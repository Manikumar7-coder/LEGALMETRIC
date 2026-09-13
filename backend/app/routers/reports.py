import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.inspection import Inspection
from app.models.report import Report
from app.auth.jwt_handler import get_current_user, security, normalize_role
from app.auth.security import decode_access_token

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("")
def list_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_role = normalize_role(current_user.role)
    query = db.query(Report).join(Inspection, Report.inspection_id == Inspection.id)
    if user_role not in ("Admin", "Supervisor"):
        query = query.filter(Inspection.user_id == current_user.id)

    reports = query.order_by(Report.created_at.desc()).all()

    result = []
    for r in reports:
        insp = r.inspection
        result.append({
            "report_id": r.id,
            "inspection_id": r.inspection_id,
            "product_name": insp.product_name if insp else "Packaged Commodity",
            "compliance_status": insp.compliance_status if insp else "UNKNOWN",
            "compliance_score": insp.compliance_score if insp else 0.0,
            "created_at": r.created_at,
            "download_url": f"/api/reports/{r.inspection_id}/download"
        })
    return result

@router.get("/{inspection_id}")
def get_report(
    inspection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = (
        db.query(Report)
        .join(Inspection, Report.inspection_id == Inspection.id)
        .filter(Report.inspection_id == inspection_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found for this inspection.")

    insp = report.inspection
    user_role = normalize_role(current_user.role)
    is_admin_or_sup = user_role in ("Admin", "Supervisor")
    is_owner = (
        insp is not None
        and insp.user_id is not None
        and current_user.id is not None
        and str(insp.user_id).strip() == str(current_user.id).strip()
    )
    if not is_admin_or_sup and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to view this report."
        )

    return {
        "report_id": report.id,
        "inspection_id": report.inspection_id,
        "product_name": insp.product_name if insp else "Packaged Commodity",
        "compliance_status": insp.compliance_status if insp else "UNKNOWN",
        "compliance_score": insp.compliance_score if insp else 0.0,
        "created_at": report.created_at,
        "download_url": f"/api/reports/{inspection_id}/download"
    }

@router.get("/{inspection_id}/download")
def download_report(
    inspection_id: int,
    format: str = Query("pdf", pattern="^(pdf|docx|csv)$"),
    token: Optional[str] = Query(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    user = None
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token

    if raw_token:
        payload = decode_access_token(raw_token)
        if payload and isinstance(payload, dict):
            uid = payload.get("user_id")
            email = payload.get("email") or payload.get("sub")
            if uid is not None:
                try:
                    user = db.query(User).filter(User.id == int(uid)).first()
                except (ValueError, TypeError):
                    pass
            if not user and email:
                user = db.query(User).filter(User.email == str(email).lower().strip()).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to download inspection report."
        )

    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    user_role = normalize_role(user.role)
    is_admin_or_sup = user_role in ("Admin", "Supervisor")
    is_owner = (
        inspection.user_id is not None
        and user.id is not None
        and str(inspection.user_id).strip() == str(user.id).strip()
    )
    if not is_admin_or_sup and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to download this inspection report."
        )

    reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    insp_dict = {
        "inspection_id": inspection.inspection_id,
        "id": inspection.id,
        "product_name": inspection.product_name,
        "created_at": inspection.created_at,
        "compliance_status": inspection.compliance_status,
        "compliance_score": inspection.compliance_score,
        "extracted_data": inspection.extracted_data or {},
        "rule_results": inspection.rule_results or [],
        "violations": inspection.violations or [],
        "inspector_name": user.name if user else "Legal Metrology Officer"
    }

    fmt = format.lower()
    if fmt == "docx":
        from app.reports.report_exporter import export_report_docx
        docx_path = os.path.join(reports_dir, f"SafeMetric_Report_INS_{inspection.id}.docx")
        export_report_docx(
            inspection_data=insp_dict,
            output_path=docx_path,
            inspector_name=user.name if user else "Legal Metrology Officer"
        )
        return FileResponse(
            path=docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"SafeMetric_Inspection_Report_{inspection.inspection_id}.docx"
        )

    elif fmt == "csv":
        from app.reports.report_exporter import export_report_csv
        csv_path = os.path.join(reports_dir, f"SafeMetric_Report_INS_{inspection.id}.csv")
        export_report_csv(
            inspection_data=insp_dict,
            output_path=csv_path,
            inspector_name=user.name if user else "Legal Metrology Officer"
        )
        return FileResponse(
            path=csv_path,
            media_type="text/csv",
            filename=f"SafeMetric_Inspection_Report_{inspection.inspection_id}.csv"
        )

    else:
        # Default: PDF
        report = db.query(Report).filter(Report.inspection_id == inspection_id).first()
        pdf_path = report.report_path if report and os.path.exists(report.report_path) else None

        if not pdf_path or not os.path.exists(pdf_path):
            from app.reports.pdf_generator import generate_pdf_report
            pdf_path = os.path.join(reports_dir, f"SafeMetric_Report_INS_{inspection.id}.pdf")
            generate_pdf_report(
                inspection_id=inspection.id,
                inspector_name=user.name if user else "Legal Metrology Officer",
                product_name=inspection.product_name,
                compliance_status=inspection.compliance_status,
                compliance_score=inspection.compliance_score,
                extracted_data=inspection.extracted_data or {},
                violations=inspection.violations or [],
                output_path=pdf_path
            )

        filename = f"SafeMetric_Inspection_Report_{inspection.inspection_id}.pdf"
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=filename
        )
