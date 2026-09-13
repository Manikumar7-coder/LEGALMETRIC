import os
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.inspection import Inspection
from app.models.field import InspectionField
from app.models.report import Report
from app.services.quality_service import analyze_image_quality
from app.ocr.ocr_service import ocr_service
from app.extraction.field_extractor import field_extractor
from app.rules.compliance_engine import compliance_engine
from app.reports.pdf_generator import generate_pdf_report

class InspectionService:
    def analyze_and_record(
        self,
        db: Session,
        user: User,
        image_path: str,
        hint: str = "",
        product_name_override: Optional[str] = None,
        is_demo: bool = False,
        package_length_mm: Optional[float] = None,
        package_width_mm: Optional[float] = None
    ) -> Inspection:
        """
        End-to-end regulatory inspection analysis:
        Image Quality Check -> OpenCV Preprocessing -> OCR -> Extraction -> Font Analysis -> Rules Engine -> DB Save -> PDF Generate
        """
        # 1. Quality Analysis
        quality_res = analyze_image_quality(image_path)
        quality_score = quality_res.get("quality_score", 100.0)
        quality_notes = "; ".join(quality_res.get("warnings", [])) or "Good Quality"

        # 2. OCR Processing
        ocr_result = ocr_service.process_image(image_path, hint=hint, is_demo=is_demo)
        raw_ocr_text = ocr_result.get("raw_text", "")
        avg_confidence = ocr_result.get("avg_confidence", 95.0)
        bounding_boxes = ocr_result.get("bounding_boxes", [])

        # Get image dimensions for optical scaling
        img_dims = None
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                img_dims = {"width": img.width, "height": img.height}
        except Exception:
            pass

        # 3. Field Extraction
        extracted_data = field_extractor.extract_declarations(raw_ocr_text, bounding_boxes)
        if bounding_boxes:
            extracted_data["_bounding_boxes"] = bounding_boxes
        if img_dims:
            extracted_data["dimensions"] = img_dims

        # 3b. Font Size & Readability Analysis (Rule 7)
        from app.extraction.font_analysis import font_analysis_engine
        font_res = font_analysis_engine.analyze_declarations(
            extracted_declarations=extracted_data,
            image_dimensions=img_dims,
            package_length_mm=package_length_mm,
            package_width_mm=package_width_mm
        )
        extracted_data["font_analysis"] = font_res

        # 3c. Declaration Placement & Grouping Analysis (Rule 8)
        from app.extraction.placement_checker import placement_checker
        placement_res = placement_checker.analyze_placement(
            extracted_declarations=extracted_data,
            all_detections=bounding_boxes,
            image_dimensions=img_dims
        )
        extracted_data["placement_analysis"] = placement_res

        # 4. Product Name Resolution
        #    Priority: OCR-extracted name > explicit user override > descriptive fallback.
        #    NEVER use uploaded filename as product name.
        detected_name = extracted_data.get("product_name", {}).get("value")
        user_override = (product_name_override or "").strip()
        if detected_name:
            product_name = detected_name
        elif user_override:
            product_name = user_override
        else:
            product_name = "Product name could not be determined from image"

        # 5. Statutory Compliance Engine Evaluation
        evaluation = compliance_engine.validate(extracted_data)
        compliance_status = evaluation.compliance_status
        compliance_score = evaluation.compliance_score
        violations = evaluation.violations

        # 6. Database record creation
        import uuid
        norm_rules = [r.to_dict() if hasattr(r, "to_dict") else r for r in (evaluation.rule_results or [])]
        inspection = Inspection(
            inspection_id=f"INS-{uuid.uuid4().hex[:8].upper()}",
            user_id=user.id,
            product_name=product_name,
            image_path=image_path,
            inspection_date=datetime.datetime.utcnow(),
            compliance_status=compliance_status,
            compliance_score=compliance_score,
            raw_ocr_text=raw_ocr_text,
            ocr_info=ocr_result or {},
            extracted_data=extracted_data,
            rule_results=norm_rules,
            violations=violations,
            quality_score=quality_score,
            quality_notes=quality_notes,
            created_at=datetime.datetime.utcnow()
        )
        db.add(inspection)
        db.commit()
        db.refresh(inspection)

        # 7. Record Inspection Fields in DB
        for field_name, field_dict in extracted_data.items():
            if field_name.startswith("_") or not isinstance(field_dict, dict):
                continue
            val = str(field_dict.get("value", ""))
            conf = float(field_dict.get("confidence", 0.0))
            stat = str(field_dict.get("status", "Missing"))
            
            db_field = InspectionField(
                inspection_id=inspection.id,
                field_name=field_name,
                extracted_value=val,
                confidence=conf,
                status=stat
            )
            db.add(db_field)

        # 8. Generate PDF Report immediately
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        pdf_path = os.path.join(reports_dir, f"SafeMetric_Report_INS_{inspection.id}.pdf")

        generate_pdf_report(
            inspection_id=inspection.id,
            inspector_name=user.name,
            product_name=product_name,
            compliance_status=compliance_status,
            compliance_score=compliance_score,
            extracted_data=extracted_data,
            violations=violations,
            avg_confidence=avg_confidence,
            image_path=image_path,
            output_pdf_path=pdf_path
        )

        report_rec = Report(
            inspection_id=inspection.id,
            report_path=pdf_path,
            created_at=datetime.datetime.utcnow()
        )
        db.add(report_rec)
        db.commit()
        db.refresh(inspection)

        return inspection


inspection_service = InspectionService()
