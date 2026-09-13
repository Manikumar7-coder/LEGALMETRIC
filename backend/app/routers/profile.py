from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.inspection import Inspection
from app.schemas.user import UserResponse, UserUpdate
from app.auth.security import hash_password
from app.auth.jwt_handler import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Profile"])

@router.get("", response_model=dict)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Calculate user-specific inspection stats
    inspections = db.query(Inspection).filter(Inspection.user_id == current_user.id).all()
    total = len(inspections)
    compliant = sum(1 for i in inspections if i.compliance_status == "COMPLIANT")
    non_compliant = sum(1 for i in inspections if i.compliance_status == "NON-COMPLIANT")
    review_required = sum(1 for i in inspections if i.compliance_status in ("REVIEW REQUIRED", "PARTIALLY COMPLIANT"))

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "organization": current_user.organization,
        "created_at": current_user.created_at,
        "stats": {
            "total_inspections": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "review_required": review_required
        }
    }

@router.put("", response_model=dict)
def update_profile(
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.name:
        current_user.name = req.name.strip()
    if req.role:
        current_user.role = req.role.strip()
    if req.organization:
        current_user.organization = req.organization.strip()
    if req.new_password:
        if len(req.new_password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")
        current_user.password_hash = hash_password(req.new_password)

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile updated successfully.",
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "organization": current_user.organization
        }
    }


settings_router = APIRouter(prefix="/api/settings", tags=["Settings"])

@settings_router.get("", response_model=dict)
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import os
    return {
        "inspector_id": current_user.id,
        "inspector_name": current_user.name,
        "department": current_user.organization,
        "rules_edition": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "statutory_act": "Legal Metrology Act, 2009",
        "demo_mode": os.getenv("DEMO_MODE", "true"),
        "ocr_engine": "RapidOCR ONNX (PP-OCRv4)",
        "active_rules_count": 12,
        "min_confidence_warning_threshold": 70.0,
        "pdf_export_enabled": True
    }

