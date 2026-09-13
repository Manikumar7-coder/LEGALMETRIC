from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.inspection import Inspection
from app.auth.jwt_handler import get_current_user, normalize_role

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Role-based query: Admins and Supervisors access departmental analytics; Field Inspectors access their own
    user_role = normalize_role(current_user.role)
    if user_role in ("Admin", "Supervisor"):
        inspections = db.query(Inspection).order_by(Inspection.created_at.desc()).all()
    else:
        inspections = (
            db.query(Inspection)
            .filter(Inspection.user_id == current_user.id)
            .order_by(Inspection.created_at.desc())
            .all()
        )

    total = len(inspections)

    compliant = 0
    partially_compliant = 0
    non_compliant = 0
    needs_review = 0

    for i in inspections:
        st = (i.compliance_status or "").upper()
        if "NON" in st:
            non_compliant += 1
        elif "PARTIAL" in st:
            partially_compliant += 1
        elif "REVIEW" in st or "NEEDS" in st:
            needs_review += 1
        elif "COMPLIANT" in st:
            compliant += 1
        else:
            needs_review += 1

    compliance_pct = round((compliant / total * 100), 1) if total > 0 else 0.0
    avg_score = round(sum((i.compliance_score or 0.0) for i in inspections) / total, 1) if total > 0 else 0.0

    # Recent inspections (up to 8)
    recent = [
        {
            "id": i.id,
            "inspection_id": i.inspection_id or f"INS-{i.id}",
            "product_name": i.product_name,
            "image_url": f"/api/inspections/{i.id}/image",
            "compliance_status": i.compliance_status,
            "compliance_score": i.compliance_score,
            "inspection_date": i.inspection_date,
            "created_at": i.created_at,
            "violations_count": len(i.violations) if i.violations else 0
        }
        for i in inspections[:8]
    ]

    # Category breakdown of violations
    violations_map = {}
    for i in inspections:
        if i.violations and isinstance(i.violations, list):
            for v in i.violations:
                if isinstance(v, dict):
                    f_name = v.get("field") or "General Packaging"
                else:
                    f_name = "General Packaging"
                violations_map[f_name] = violations_map.get(f_name, 0) + 1

    # Sorted list of common violations
    common_violations = sorted(
        [{"category": k, "count": v} for k, v in violations_map.items()],
        key=lambda x: x["count"],
        reverse=True
    )

    # Real chronological trend data
    date_map = {}
    for i in reversed(inspections[:14]):
        if i.created_at:
            d_str = i.created_at.strftime("%d %b")
            if d_str not in date_map:
                date_map[d_str] = {"date": d_str, "total": 0, "compliant": 0, "non_compliant": 0}
            date_map[d_str]["total"] += 1
            st = (i.compliance_status or "").upper()
            if "COMPLIANT" in st and "NON" not in st and "PARTIAL" not in st:
                date_map[d_str]["compliant"] += 1
            else:
                date_map[d_str]["non_compliant"] += 1

    trend_data = list(date_map.values())

    return {
        "total_inspections": total,
        "compliant_count": compliant,
        "partially_compliant_count": partially_compliant,
        "non_compliant_count": non_compliant,
        "needs_review_count": needs_review,
        "review_required_count": needs_review + partially_compliant, # Backwards compatibility
        "average_compliance_score": avg_score,
        "compliance_percentage": compliance_pct,
        "recent_inspections": recent,
        "trend_data": trend_data,
        "violations_breakdown": violations_map,
        "common_violations": common_violations
    }
