"""
inspection_persistence.py
=========================
Statutory Inspection Persistence Service.

Saves and retrieves self-contained inspection records representing uploaded
commodity packaging image analyses under the Legal Metrology Act, 2009 and
Legal Metrology (Packaged Commodities) Rules, 2011.

Persists the 9 statutory inspection components:
1. inspection_id
2. uploaded image reference (image_path / image_reference)
3. date/time (created_at / inspection_date)
4. extracted declarations (extracted_data)
5. OCR information (ocr_info / raw_ocr_text)
6. rule results (evaluated statutory rules)
7. violations (detected non-compliances)
8. compliance status (Compliant, Partially Compliant, Non-Compliant, Needs Review)
9. compliance score (calibrated 0.0 - 100.0%)

Uses the project's existing database architecture (SQLAlchemy + SQLite).
Strictly does NOT create a separate product database:
An inspection is a self-contained record of an uploaded image analysis.
"""

import os
import uuid
import datetime
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.inspection import Inspection
from app.models.field import InspectionField
from app.database import ensure_database_schema


class InspectionPersistenceService:
    """
    Service responsible for persisting and retrieving self-contained
    inspection records in the SafeMetric SQLite database.
    """

    def __init__(self):
        # Ensure schema migrations are applied
        try:
            ensure_database_schema()
        except Exception as e:
            print(f"[InspectionPersistenceService Init Notice] {e}")

    def save_inspection(
        self,
        db: Session,
        uploaded_image_reference: str,
        extracted_declarations: Dict[str, Any],
        ocr_information: Dict[str, Any],
        rule_results: List[Dict[str, Any]],
        violations: List[Dict[str, Any]],
        compliance_status: str,
        compliance_score: float,
        inspection_id: Optional[str] = None,
        date_time: Optional[Union[datetime.datetime, str]] = None,
        user_id: Optional[int] = None,
        product_name: Optional[str] = None,
        quality_score: float = 100.0,
        quality_notes: str = ""
    ) -> Inspection:
        """
        Saves a self-contained packaging label inspection record to the database.

        Parameters:
        -----------
        db : Session
            Active SQLAlchemy database session.
        uploaded_image_reference : str
            File system path or URI reference to the uploaded product package image.
        extracted_declarations : Dict[str, Any]
            Structured field declarations extracted from the packaging image.
        ocr_information : Dict[str, Any]
            Full OCR output including raw text, bounding boxes, and confidences.
        rule_results : List[Dict[str, Any]]
            Evaluated statutory rule outcomes under PCR, 2011 and LMA, 2009.
        violations : List[Dict[str, Any]]
            Detected legal violations and statutory infractions.
        compliance_status : str
            Overall statutory compliance verdict (e.g. Compliant, Non-Compliant).
        compliance_score : float
            Deterministic compliance score (0.0 - 100.0%).
        inspection_id : Optional[str]
            Statutory inspection identifier. If omitted, generates unique 'INS-<hex>'.
        date_time : Optional[Union[datetime.datetime, str]]
            Audit timestamp. Defaults to UTC now.
        user_id : Optional[int]
            Inspecting officer's user ID (optional).
        product_name : Optional[str]
            Commodity common name or generic designation.
        quality_score : float
            Image quality rating (0-100).
        quality_notes : str
            Image quality diagnostic observations.

        Returns:
        --------
        Inspection
            Persisted SQLAlchemy Inspection model instance.
        """
        if not uploaded_image_reference:
            raise ValueError("Uploaded image reference is mandatory for inspection persistence.")

        # 1. Parse or assign date/time
        if date_time is None:
            dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        elif isinstance(date_time, str):
            try:
                dt = datetime.datetime.fromisoformat(date_time)
            except Exception:
                dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        elif isinstance(date_time, datetime.datetime):
            dt = date_time
        else:
            dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

        # 2. Resolve user_id for existing database NOT NULL constraint
        if user_id is None:
            try:
                from app.models.user import User
                first_user = db.query(User).first()
                user_id = first_user.id if first_user else 1
            except Exception:
                user_id = 1

        # 3. Assign or generate inspection ID
        if not inspection_id:
            assigned_id = f"INS-{uuid.uuid4().hex[:8].upper()}"
        else:
            assigned_id = str(inspection_id).strip()

        # 3. Resolve Product Name
        if not product_name:
            if isinstance(extracted_declarations, dict):
                p_val = extracted_declarations.get("product_name")
                if isinstance(p_val, dict):
                    product_name = p_val.get("value")
                elif isinstance(p_val, str):
                    product_name = p_val
            if not product_name:
                product_name = "Packaged Commodity"

        # 4. Resolve OCR text
        raw_ocr_text = ""
        if isinstance(ocr_information, dict):
            raw_ocr_text = ocr_information.get("raw_text") or ocr_information.get("text") or ""
        elif isinstance(ocr_information, str):
            raw_ocr_text = ocr_information
            ocr_information = {"raw_text": raw_ocr_text, "bounding_boxes": []}

        # 5. Normalize rules & violations lists
        norm_rule_results = [
            r if isinstance(r, dict) else (r.to_dict() if hasattr(r, "to_dict") else str(r))
            for r in (rule_results or [])
        ]
        norm_violations = [
            v if isinstance(v, dict) else (v.to_dict() if hasattr(v, "to_dict") else str(v))
            for v in (violations or [])
        ]

        # 6. Instantiate Inspection model
        inspection = Inspection(
            inspection_id=assigned_id,
            user_id=user_id,
            product_name=str(product_name),
            image_path=str(uploaded_image_reference),
            inspection_date=dt,
            compliance_status=str(compliance_status),
            compliance_score=round(float(compliance_score), 1),
            raw_ocr_text=raw_ocr_text,
            ocr_info=ocr_information or {},
            extracted_data=extracted_declarations or {},
            rule_results=norm_rule_results,
            violations=norm_violations,
            quality_score=float(quality_score),
            quality_notes=str(quality_notes),
            created_at=dt
        )

        db.add(inspection)
        db.commit()
        db.refresh(inspection)

        # 7. Optionally record InspectionField child rows if extracted declarations present
        if isinstance(extracted_declarations, dict):
            for field_name, field_dict in extracted_declarations.items():
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
            db.commit()
            db.refresh(inspection)

        return inspection

    def get_inspection(
        self,
        db: Session,
        inspection_id: Union[str, int]
    ) -> Optional[Inspection]:
        """
        Retrieves a persisted inspection by string inspection_id or integer primary key.

        Parameters:
        -----------
        db : Session
            Active SQLAlchemy database session.
        inspection_id : Union[str, int]
            Identifier to search (e.g. 'INS-ABCD1234', '1', or 1).

        Returns:
        --------
        Optional[Inspection]
            Matching Inspection model instance, or None if not found.
        """
        if inspection_id is None:
            return None

        # Check by string inspection_id first
        str_id = str(inspection_id).strip()
        query = db.query(Inspection).filter(Inspection.inspection_id == str_id)
        match = query.first()
        if match:
            return match

        # Check by integer ID if numeric
        try:
            int_id = int(str_id)
            match = db.query(Inspection).filter(Inspection.id == int_id).first()
            if match:
                return match
        except ValueError:
            pass

        return None

    def get_inspection_payload(
        self,
        db: Session,
        inspection_id: Union[str, int]
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves a persisted inspection and formats it as a dictionary containing
        the 9 statutory components.

        Returns:
        --------
        Optional[Dict[str, Any]]
            Dictionary containing:
            - inspection_id
            - uploaded_image_reference
            - date_time
            - extracted_declarations
            - OCR information
            - rule results
            - violations
            - compliance status
            - compliance score
        """
        inspection = self.get_inspection(db, inspection_id)
        if not inspection:
            return None

        return inspection.to_persistence_dict()

    def list_inspections(
        self,
        db: Session,
        user_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Inspection]:
        """
        Lists persisted inspections ordered by newest first.
        """
        query = db.query(Inspection)
        if user_id is not None:
            query = query.filter(Inspection.user_id == user_id)
        return query.order_by(Inspection.created_at.desc()).limit(limit).all()

    def delete_inspection(
        self,
        db: Session,
        inspection_id: Union[str, int]
    ) -> bool:
        """
        Deletes an inspection record from persistence.
        """
        inspection = self.get_inspection(db, inspection_id)
        if not inspection:
            return False

        db.delete(inspection)
        db.commit()
        return True


# Global Singleton Instance
inspection_persistence_service = InspectionPersistenceService()
