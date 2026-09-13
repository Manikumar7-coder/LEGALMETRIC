import os
import uuid
import shutil
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from app.database import get_db
from app.models.user import User
from app.models.inspection import Inspection
from app.models.field import InspectionField
from app.models.report import Report
from app.auth.jwt_handler import get_current_user, require_admin, normalize_role
from app.services.inspection_service import inspection_service
from app.ocr.ocr_service import ocr_service

router = APIRouter(prefix="/api/inspections", tags=["Inspections"])


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_SIZE = 15 * 1024 * 1024 # 15MB

ALLOWED_UPLOAD_FORMATS = {".png", ".jpg", ".jpeg"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024 # 10MB

@router.post("/upload")
async def upload_inspection_image(
    file: Optional[UploadFile] = File(None),
    product_name: Optional[str] = Form(None),
    package_length_mm: Optional[float] = Form(None),
    package_width_mm: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step: Product Image Upload.
    Validates uploaded commodity label image (JPG, JPEG, PNG, max 10MB),
    verifies image integrity and dimensions, and stores the image as primary inspection input.
    No OCR or legal validation is performed in this step.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Missing product image file. Please upload an image."
        )

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_UPLOAD_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Only JPG, JPEG, and PNG images are supported."
        )

    # Read content to validate size and image validity
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({round(file_size / (1024 * 1024), 2)} MB) exceeds the maximum allowed limit of 10 MB."
        )

    # Verify image integrity and dimensions using PIL
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(content))
        img.verify()
        # Re-open to read dimensions after verify()
        img = Image.open(io.BytesIO(content))
        width, height = img.size
        img_format = img.format or ext.replace(".", "").upper()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or corrupted image file: {str(e)}"
        )

    # Save to uploads directory
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    unique_filename = f"commodity_{uuid.uuid4().hex[:12]}{ext}"
    saved_path = os.path.join(upload_dir, unique_filename)

    with open(saved_path, "wb") as f:
        f.write(content)

    # Product name: use explicit user-provided name, or a neutral placeholder.
    # The actual OCR-extracted product name is resolved later by analyze_and_record.
    # NEVER derive product name from the uploaded filename.
    p_name = (product_name or "").strip() or "Packaged Commodity (Pending Inspection)"
    import datetime
    unique_ins_id = f"INS-{uuid.uuid4().hex[:8].upper()}"
    inspection = Inspection(
        inspection_id=unique_ins_id,
        user_id=current_user.id,
        product_name=p_name,
        image_path=saved_path,
        inspection_date=datetime.datetime.utcnow(),
        compliance_status="PENDING_INSPECTION",
        compliance_score=0.0,
        raw_ocr_text="",
        ocr_info={},
        extracted_data={
            "filename": file.filename,
            "saved_filename": unique_filename,
            "dimensions": {"width": width, "height": height},
            "file_size_bytes": file_size,
            "format": img_format,
            "upload_timestamp": datetime.datetime.utcnow().isoformat(),
            "package_length_mm": package_length_mm,
            "package_width_mm": package_width_mm
        },
        rule_results=[],
        violations=[],
        quality_score=100.0,
        quality_notes=f"Image verified ({width}x{height} px, {img_format}). Ready for Legal Metrology audit.",
        created_at=datetime.datetime.utcnow()
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    return {
        "id": inspection.id,
        "inspection_id": inspection.inspection_id,
        "uploaded_image_reference": inspection.image_path,
        "product_name": inspection.product_name,
        "image_url": f"/api/inspections/{inspection.id}/image",
        "filename": unique_filename,
        "original_filename": file.filename,
        "size_bytes": file_size,
        "size_formatted": f"{round(file_size / 1024, 1)} KB" if file_size < 1024*1024 else f"{round(file_size / (1024*1024), 2)} MB",
        "dimensions": {"width": width, "height": height},
        "format": img_format,
        "compliance_status": inspection.compliance_status,
        "created_at": inspection.created_at,
        "message": "Product package image uploaded and verified successfully."
    }


@router.post("/{inspection_id}/ocr")
def run_inspection_ocr(
    inspection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes pure OCR on the uploaded product package image for the specified inspection ID.
    Returns:
    - extracted text
    - detected text regions / bounding boxes
    - confidence scores and summary
    - preserved low-confidence regions for officer review
    - limitations diagnostic notes
    Does NOT make legal compliance decisions.
    Does NOT guess missing text.
    Preserves original image and preprocessed image.
    """
    inspection = db.query(Inspection).filter(
        Inspection.id == inspection_id,
        Inspection.user_id == current_user.id
    ).first()

    if not inspection:
        raise HTTPException(status_code=404, detail=f"Inspection #{inspection_id} not found.")

    if not inspection.image_path or not os.path.exists(inspection.image_path):
        raise HTTPException(status_code=400, detail="Commodity image file for this inspection is missing.")

    ocr_result = ocr_service.process_image(
        image_path=inspection.image_path,
        hint=inspection.product_name,
        is_demo=False
    )

    inspection.raw_ocr_text = ocr_result.get("raw_text", "")
    
    # Store rich OCR metadata in extracted_data
    if not isinstance(inspection.extracted_data, dict):
        inspection.extracted_data = {}

    inspection.extracted_data["_bounding_boxes"] = ocr_result.get("bounding_boxes", [])
    inspection.extracted_data["confidence_summary"] = ocr_result.get("confidence_summary", {})
    inspection.extracted_data["low_confidence_regions"] = ocr_result.get("low_confidence_regions", [])
    inspection.extracted_data["preprocessed_path"] = ocr_result.get("preprocessed_image_path")
    inspection.extracted_data["ocr_limitations"] = ocr_result.get("limitations", [])
    inspection.compliance_status = "OCR_COMPLETED"

    db.commit()
    db.refresh(inspection)

    return {
        "inspection_id": inspection.id,
        "product_name": inspection.product_name,
        "compliance_status": inspection.compliance_status,
        "raw_text": ocr_result.get("raw_text", ""),
        "text_lines": ocr_result.get("text_lines", []),
        "bounding_boxes": ocr_result.get("bounding_boxes", []),
        "confidence_summary": ocr_result.get("confidence_summary", {}),
        "low_confidence_regions": ocr_result.get("low_confidence_regions", []),
        "low_confidence_review_required": ocr_result.get("low_confidence_review_required", False),
        "original_image_path": ocr_result.get("original_image_path"),
        "preprocessed_image_path": ocr_result.get("preprocessed_image_path"),
        "engine": ocr_result.get("engine"),
        "limitations": ocr_result.get("limitations", [])
    }


@router.post("/analyze")
async def analyze_inspection(
    file: Optional[UploadFile] = File(None),
    demo_sample: Optional[str] = Form(None),
    product_name: Optional[str] = Form(None),
    package_length_mm: Optional[float] = Form(None),
    package_width_mm: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    saved_image_path = ""
    hint = demo_sample or ""

    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Allowed formats: PNG, JPG, JPEG, WEBP."
            )

        unique_filename = f"scan_{uuid.uuid4().hex[:10]}{ext}"
        saved_image_path = os.path.join(upload_dir, unique_filename)

        with open(saved_image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # File size check (max 15MB)
        file_size = os.path.getsize(saved_image_path)
        if file_size > MAX_FILE_SIZE:
            if os.path.exists(saved_image_path):
                os.remove(saved_image_path)
            raise HTTPException(status_code=400, detail="Image size exceeds maximum limit of 15MB.")

        # MIME magic bytes & image integrity verification
        try:
            from PIL import Image
            with Image.open(saved_image_path) as img:
                img.verify()
        except Exception as e:
            if os.path.exists(saved_image_path):
                os.remove(saved_image_path)
            raise HTTPException(status_code=400, detail=f"Invalid or corrupted image payload: {str(e)}")
            
    elif demo_sample:
        # Sanitize against path traversal: allow only alphanumeric, dashes, underscores
        safe_demo = "".join(c for c in demo_sample if c.isalnum() or c in ("-", "_")).strip()
        demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo_samples")
        os.makedirs(demo_dir, exist_ok=True)
        
        sample_filename = f"sample_{safe_demo}.png"
        sample_path = os.path.join(demo_dir, sample_filename)
        
        if not os.path.exists(sample_path):
            alt_sample_path = os.path.join(os.path.dirname(demo_dir), "demo_samples", sample_filename)
            if os.path.exists(alt_sample_path):
                sample_path = alt_sample_path

        if not os.path.exists(sample_path):
            saved_image_path = os.path.join(upload_dir, f"demo_{safe_demo}_{uuid.uuid4().hex[:6]}.png")
            with open(saved_image_path, "wb") as f:
                f.write(b"DEMO_LABEL_IMAGE")
        else:
            saved_image_path = sample_path
    else:
        raise HTTPException(
            status_code=400,
            detail="No product label image provided. Please capture with camera, upload a file, or choose a demo sample."
        )

    # Execute end-to-end inspection
    try:
        inspection = inspection_service.analyze_and_record(
            db=db,
            user=current_user,
            image_path=saved_image_path,
            hint=demo_sample or "",
            product_name_override=product_name,
            is_demo=bool(demo_sample),
            package_length_mm=package_length_mm,
            package_width_mm=package_width_mm
        )
    except Exception as e:
        print(f"[Inspection Execution Error] {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process inspection: {str(e)}")

    rel_img_url = f"/api/inspections/{inspection.id}/image"
    return build_inspection_payload(inspection=inspection, db=db, rel_img_url=rel_img_url)


def normalize_status(raw_status: str) -> str:
    s = (raw_status or "").upper().strip()
    if "NON" in s:
        return "Non-Compliant"
    elif "PARTIAL" in s:
        return "Partially Compliant"
    elif "REVIEW" in s or "NEEDS" in s:
        return "Needs Review"
    elif "COMPLIANT" in s:
        return "Compliant"
    return "Needs Review"


def build_inspection_payload(inspection: Inspection, db: Session, rel_img_url: Optional[str] = None) -> Dict[str, Any]:
    if not rel_img_url:
        rel_img_url = f"/api/inspections/{inspection.id}/image"

    fields_list = [
        {
            "field_name": f.field_name,
            "extracted_value": f.extracted_value,
            "confidence": f.confidence,
            "status": f.status
        }
        for f in inspection.fields
    ]

    report = db.query(Report).filter(Report.inspection_id == inspection.id).first()

    bboxes = []
    if isinstance(inspection.extracted_data, dict):
        bboxes = inspection.extracted_data.get("_bounding_boxes", [])

    compliance_eval = None
    if isinstance(inspection.extracted_data, dict) and inspection.extracted_data:
        try:
            from app.rules.compliance_engine import compliance_engine
            compliance_eval = compliance_engine.validate(inspection.extracted_data)
        except Exception as e:
            print(f"[Compliance Engine Error] {e}")

    if compliance_eval:
        compliance_status_raw = compliance_eval.compliance_status
        compliance_score = compliance_eval.compliance_score
        passed_count = compliance_eval.passed_count
        failed_count = compliance_eval.failed_count
        needs_review_count = compliance_eval.needs_review_count
        not_applicable_count = compliance_eval.not_applicable_count
        total_rules_evaluated = compliance_eval.total_rules_evaluated
        violations = compliance_eval.violations
        rule_results = [r.to_dict() for r in compliance_eval.rule_results]
    else:
        compliance_status_raw = inspection.compliance_status
        compliance_score = inspection.compliance_score
        violations = inspection.violations or []
        failed_count = len(violations)
        passed_count = max(0, len(fields_list) - failed_count)
        needs_review_count = sum(1 for f in fields_list if f.get("status") == "Low Confidence")
        not_applicable_count = 0
        total_rules_evaluated = len(fields_list)
        rule_results = []

    # Normalized clear status label
    status_label = normalize_status(compliance_status_raw)

    # Build actionable recommendations
    recommendations = []
    if violations:
        for v in violations:
            recommendations.append({
                "action_type": "Rectify Violation" if v.get("severity") in ("CRITICAL", "HIGH") else "Corrective Review",
                "field": v.get("field"),
                "severity": v.get("severity", "HIGH"),
                "title": f"Rectify {v.get('field')} Non-Compliance",
                "detail": v.get("recommendation") or v.get("issue"),
                "legal_reference": v.get("rule_reference") or v.get("rule_id"),
                "urgency": "Immediate" if v.get("severity") == "CRITICAL" else ("High" if v.get("severity") == "HIGH" else "Moderate")
            })
    if needs_review_count > 0:
        recommendations.append({
            "action_type": "Physical Verification",
            "field": "Optical / Contrast Legibility",
            "severity": "MEDIUM",
            "title": "Perform Physical Inspection for Legibility / Contrast",
            "detail": "One or more package declarations showed lower optical contrast or legibility. A designated inspector should physically verify numeral height and color contrast under Rule 9(1) on the retail package.",
            "legal_reference": "Rule 9(1), Legal Metrology (Packaged Commodities) Rules, 2011",
            "urgency": "Moderate"
        })
    if not violations and needs_review_count == 0:
        recommendations.append({
            "action_type": "Statutory Clearance",
            "field": "Packaging Compliance",
            "severity": "LOW",
            "title": "Commodity Fully Compliant with Metrology Standards",
            "detail": "All mandatory declarations required under the Legal Metrology Act, 2009 and Packaged Commodities Rules, 2011 have been verified. Commodity is cleared for retail distribution.",
            "legal_reference": "Section 18(1), Legal Metrology Act, 2009",
            "urgency": "None"
        })

    # Structured legal references evaluated
    legal_references = []
    if rule_results:
        for r in rule_results:
            legal_references.append({
                "rule_id": r.get("rule_id"),
                "legal_reference": r.get("legal_reference"),
                "status": r.get("status"),
                "requirement": r.get("expected_requirement"),
                "explanation": r.get("explanation"),
                "detected_value": r.get("detected_value")
            })

    # Build evidence store manifest
    evidence_manifest = None
    if isinstance(inspection.extracted_data, dict):
        try:
            from app.evidence import evidence_service
            img_id = os.path.basename(inspection.image_path) if inspection.image_path else f"ins_{inspection.id}"
            ev_store = evidence_service.build_evidence_store(
                image_id=img_id,
                extracted_declarations=inspection.extracted_data,
                rule_results=compliance_eval.rule_results if compliance_eval else None,
                violations=violations,
                inspection_id=str(inspection.id),
                image_path=inspection.image_path
            )
            evidence_manifest = ev_store.to_dict()
        except Exception as e:
            print(f"[Evidence Store Build Error] {e}")

    score_breakdown = None
    if compliance_eval and getattr(compliance_eval, "score_breakdown", None):
        score_breakdown = compliance_eval.score_breakdown.to_dict()

    return {
        "id": inspection.id,
        "inspection_id": inspection.inspection_id or f"INS-{inspection.id}",
        "uploaded_image_reference": inspection.image_path,
        "date_time": (inspection.created_at or inspection.inspection_date).isoformat() if (inspection.created_at or inspection.inspection_date) else None,
        "extracted_declarations": inspection.extracted_data or {},
        "ocr_information": inspection.ocr_info or {"raw_text": inspection.raw_ocr_text or "", "bounding_boxes": bboxes},
        "user_id": inspection.user_id,
        "product_name": inspection.product_name,
        "image_url": rel_img_url,
        "inspection_date": inspection.inspection_date,
        "compliance_status": inspection.compliance_status,
        "status": status_label,
        "normalized_status": status_label,
        "compliance_score": compliance_score,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "needs_review_count": needs_review_count,
        "not_applicable_count": not_applicable_count,
        "total_rules_evaluated": total_rules_evaluated,
        "raw_ocr_text": inspection.raw_ocr_text,
        "extracted_data": inspection.extracted_data,
        "violations": violations,
        "rule_results": rule_results,
        "legal_references": legal_references,
        "recommendations": recommendations,
        "score_breakdown": score_breakdown,
        "fields": fields_list,
        "bounding_boxes": bboxes,
        "evidence": evidence_manifest,
        "font_analysis": (inspection.extracted_data or {}).get("font_analysis") if isinstance(inspection.extracted_data, dict) else None,
        "placement_analysis": (inspection.extracted_data or {}).get("placement_analysis") if isinstance(inspection.extracted_data, dict) else None,
        "quality_score": inspection.quality_score,
        "quality_notes": inspection.quality_notes,
        "has_report": report is not None,
        "report_id": report.id if report else None,
        "created_at": inspection.created_at
    }


@router.get("")
def list_inspections(
    response: Response,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(50, ge=1, le=100),
    sort_by: Optional[str] = "newest", # newest, oldest, score
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import datetime
    # Role-based authorization: Admins and Supervisors can view all records across the department
    # Field Inspectors view their own inspections
    user_role = normalize_role(current_user.role)
    if user_role in ("Admin", "Supervisor"):
        query = db.query(Inspection)
    else:
        query = db.query(Inspection).filter(Inspection.user_id == current_user.id)

    if isinstance(status_filter, str) and status_filter.upper() != "ALL":
        sf = status_filter.upper()
        if sf in ("REVIEW REQUIRED", "NEEDS REVIEW", "REVIEW"):
            query = query.filter(or_(
                Inspection.compliance_status.ilike("%REVIEW%"),
                Inspection.compliance_status.ilike("%NEEDS%")
            ))
        elif sf in ("PARTIALLY COMPLIANT", "PARTIAL"):
            query = query.filter(Inspection.compliance_status.ilike("%PARTIAL%"))
        elif sf in ("NON-COMPLIANT", "NON COMPLIANT", "FAIL"):
            query = query.filter(Inspection.compliance_status.ilike("%NON%"))
        elif sf in ("COMPLIANT", "PASS"):
            query = query.filter(
                Inspection.compliance_status.ilike("%COMPLIANT%"),
                ~Inspection.compliance_status.ilike("%NON%"),
                ~Inspection.compliance_status.ilike("%PARTIAL%")
            )
        else:
            query = query.filter(Inspection.compliance_status.ilike(f"%{sf}%"))

    if search:
        s = search.strip()
        query = query.filter(
            or_(
                Inspection.product_name.ilike(f"%{s}%"),
                Inspection.inspection_id.ilike(f"%{s}%"),
                cast(Inspection.id, String).ilike(f"%{s}%")
            )
        )

    if from_date:
        try:
            f_d = datetime.date.fromisoformat(from_date)
            f_dt = datetime.datetime.combine(f_d, datetime.time.min)
            query = query.filter(Inspection.created_at >= f_dt)
        except Exception:
            pass

    if to_date:
        try:
            t_d = datetime.date.fromisoformat(to_date)
            t_dt = datetime.datetime.combine(t_d, datetime.time.max)
            query = query.filter(Inspection.created_at <= t_dt)
        except Exception:
            pass

    total_count = query.count()
    cur_page = page if isinstance(page, int) else 1
    cur_page_size = page_size if isinstance(page_size, int) else 50

    if response and hasattr(response, "headers"):
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["X-Page"] = str(cur_page)
        response.headers["X-Page-Size"] = str(cur_page_size)

    if sort_by == "oldest":
        query = query.order_by(Inspection.created_at.asc())
    elif sort_by == "score":
        query = query.order_by(Inspection.compliance_score.desc())
    else:
        query = query.order_by(Inspection.created_at.desc())

    offset = (cur_page - 1) * cur_page_size
    inspections = query.offset(offset).limit(cur_page_size).all()

    return [
        {
            "id": i.id,
            "inspection_id": i.inspection_id or f"INS-{i.id}",
            "user_id": i.user_id,
            "product_name": i.product_name,
            "uploaded_image_reference": i.image_path,
            "image_url": f"/api/inspections/{i.id}/image",
            "inspection_date": i.inspection_date,
            "date_time": (i.created_at or i.inspection_date).isoformat() if (i.created_at or i.inspection_date) else None,
            "compliance_status": i.compliance_status,
            "status": normalize_status(i.compliance_status),
            "compliance_score": i.compliance_score,
            "violations_count": len(i.violations) if i.violations else 0,
            "violations": i.violations or [],
            "rule_results_count": len(i.rule_results) if i.rule_results else 0,
            "created_at": i.created_at
        }
        for i in inspections
    ]


@router.get("/{inspection_id}")
def get_inspection(
    inspection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.inspection_persistence import inspection_persistence_service
    inspection = inspection_persistence_service.get_inspection(db, inspection_id)

    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    user_role = normalize_role(current_user.role)
    if user_role not in ("Admin", "Supervisor") and inspection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to view this inspection record."
        )

    return build_inspection_payload(inspection=inspection, db=db)


@router.get("/{inspection_id}/image")
def get_inspection_image(
    inspection_id: int,
    db: Session = Depends(get_db)
):
    from fastapi.responses import FileResponse
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection or not inspection.image_path or not os.path.exists(inspection.image_path):
        raise HTTPException(status_code=404, detail="Image not found on filesystem.")
    
    real_path = os.path.abspath(inspection.image_path)
    if not os.path.isfile(real_path):
        raise HTTPException(status_code=404, detail="Image not found.")

    # Path traversal protection: Ensure path is within allowed directories
    base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    if not real_path.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Access to the specified image path is forbidden.")

    return FileResponse(real_path)


@router.get("/{inspection_id}/debug/ocr")
def get_inspection_ocr_debug(
    inspection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Development/audit endpoint: Returns raw OCR debug information for an inspection.
    Includes: source image path, SHA-256 hash, raw OCR text, bounding boxes, 
    avg confidence, and extracted fields.
    This is essential for distinguishing OCR problems from extraction problems from compliance problems.
    """
    import hashlib

    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found.")
    user_role = normalize_role(current_user.role)
    if user_role not in ("Admin", "Supervisor") and inspection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied: You are not authorized to view this debug information.")

    image_path = inspection.image_path
    img_hash = None
    image_exists = False
    if image_path:
        image_exists = os.path.exists(image_path)
        if image_exists:
            with open(image_path, 'rb') as f:
                img_hash = hashlib.sha256(f.read()).hexdigest()[:16]

    # Extract stored bounding boxes from ocr_info or extracted_data
    ocr_info = inspection.ocr_info or {}
    extracted_data = inspection.extracted_data or {}
    stored_boxes = ocr_info.get("bounding_boxes") or extracted_data.get("_bounding_boxes") or []

    # Only return non-internal extracted fields
    extracted_fields = {
        k: v for k, v in extracted_data.items()
        if not k.startswith("_") and k not in (
            "filename", "saved_filename", "dimensions", "file_size_bytes",
            "format", "upload_timestamp", "preprocessed_path",
            "confidence_summary", "low_confidence_regions", "ocr_limitations"
        )
    }

    return {
        "inspection_id": inspection.id,
        "inspection_ref": inspection.inspection_id,
        "image_path": image_path,
        "image_exists": image_exists,
        "image_sha256_prefix": img_hash,
        "raw_ocr_text": inspection.raw_ocr_text or "",
        "ocr_char_count": len(inspection.raw_ocr_text or ""),
        "bounding_box_count": len(stored_boxes),
        "bounding_boxes": stored_boxes[:50],  # Return first 50 to avoid huge response
        "ocr_engine": ocr_info.get("engine"),
        "avg_confidence": ocr_info.get("avg_confidence"),
        "extracted_fields": extracted_fields,
        "product_name": inspection.product_name,
        "compliance_status": inspection.compliance_status,
        "compliance_score": inspection.compliance_score,
    }


@router.delete("/{inspection_id}")
def delete_inspection(
    inspection_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    from app.services.inspection_persistence import inspection_persistence_service
    inspection = inspection_persistence_service.get_inspection(db, inspection_id)

    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    db.delete(inspection)
    db.commit()
    return {"message": f"Inspection #{inspection_id} successfully deleted."}
