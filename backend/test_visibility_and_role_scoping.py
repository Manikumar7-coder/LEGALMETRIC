"""
Test Suite: User-Scoped Inspection Visibility, Dashboard Stats, Report Isolation, and Role Normalization.
Verifies BUG 1 fix:
1. Normalization of legacy roles ('Enforcement Officer', 'Legal Metrology Inspector' -> 'Inspector',
   'Zonal Supervisor' -> 'Supervisor', 'Administrative Officer' -> 'Admin').
2. Scoped visibility: Inspector accounts only see their own inspections, reports, and personal dashboard stats.
3. Departmental visibility: Admin and Supervisor accounts see all records across the department.
4. Access control: Unauthorized inspection or report access by an Inspector returns 403 Forbidden.
"""

import sys
import os
import uuid
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import HTTPException, Response
from app.database import SessionLocal
from app.models.user import User
from app.models.inspection import Inspection
from app.models.report import Report
from app.auth.jwt_handler import normalize_role
from app.auth.security import hash_password
from app.routers.inspections import list_inspections, get_inspection
from app.routers.dashboard import get_dashboard_stats
from app.routers.reports import list_reports, get_report


def test_role_normalization():
    print("\n--- 1. Testing Role Normalization ---")
    assert normalize_role("Enforcement Officer") == "Inspector"
    assert normalize_role("enforcement officer") == "Inspector"
    assert normalize_role("Legal Metrology Inspector") == "Inspector"
    assert normalize_role("Field Officer") == "Inspector"
    assert normalize_role("Officer") == "Inspector"
    assert normalize_role("Inspector") == "Inspector"
    assert normalize_role("user") == "Inspector"
    assert normalize_role(None) == "Inspector"
    assert normalize_role("") == "Inspector"

    assert normalize_role("Supervisor") == "Supervisor"
    assert normalize_role("Zonal Supervisor") == "Supervisor"
    assert normalize_role("Lead Inspector") == "Supervisor"
    assert normalize_role("Chief Inspector") == "Supervisor"

    assert normalize_role("Admin") == "Admin"
    assert normalize_role("Administrator") == "Admin"
    assert normalize_role("Administrative Officer") == "Admin"
    assert normalize_role("System_Admin") == "Admin"

    print("  [PASS] All role variations correctly normalized to canonical tiers.")


def test_scoped_inspection_visibility():
    print("\n--- 2. Testing Scoped Inspection Visibility & Dashboard Stats ---")
    db = SessionLocal()
    try:
        # Create unique test users
        tag = uuid.uuid4().hex[:6]
        user_a = User(
            name=f"Inspector Alpha {tag}",
            email=f"alpha_{tag}@test.gov.in",
            password_hash=hash_password("test1234"),
            role="Enforcement Officer", # Legacy role string to test normalization
            organization="Zone A"
        )
        user_b = User(
            name=f"Inspector Beta {tag}",
            email=f"beta_{tag}@test.gov.in",
            password_hash=hash_password("test1234"),
            role="Inspector",
            organization="Zone B"
        )
        admin_user = User(
            name=f"Admin Chief {tag}",
            email=f"admin_{tag}@test.gov.in",
            password_hash=hash_password("test1234"),
            role="Admin",
            organization="Headquarters"
        )
        sup_user = User(
            name=f"Supervisor Zonal {tag}",
            email=f"sup_{tag}@test.gov.in",
            password_hash=hash_password("test1234"),
            role="Supervisor",
            organization="Headquarters"
        )
        db.add_all([user_a, user_b, admin_user, sup_user])
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)
        db.refresh(admin_user)
        db.refresh(sup_user)

        # Create inspections for User A and User B
        ins_a1 = Inspection(
            inspection_id=f"INS-A1-{tag}",
            user_id=user_a.id,
            image_path=f"uploads/test_a1_{tag}.png",
            product_name=f"Commodity Alpha 1 {tag}",
            compliance_status="COMPLIANT",
            compliance_score=95.0,
            inspection_date=datetime.datetime.utcnow()
        )
        ins_a2 = Inspection(
            inspection_id=f"INS-A2-{tag}",
            user_id=user_a.id,
            image_path=f"uploads/test_a2_{tag}.png",
            product_name=f"Commodity Alpha 2 {tag}",
            compliance_status="NON-COMPLIANT",
            compliance_score=50.0,
            inspection_date=datetime.datetime.utcnow()
        )
        ins_b1 = Inspection(
            inspection_id=f"INS-B1-{tag}",
            user_id=user_b.id,
            image_path=f"uploads/test_b1_{tag}.png",
            product_name=f"Commodity Beta 1 {tag}",
            compliance_status="REVIEW REQUIRED",
            compliance_score=75.0,
            inspection_date=datetime.datetime.utcnow()
        )
        db.add_all([ins_a1, ins_a2, ins_b1])
        db.commit()
        db.refresh(ins_a1)
        db.refresh(ins_a2)
        db.refresh(ins_b1)

        # Create reports for ins_a1 and ins_b1
        rep_a1 = Report(inspection_id=ins_a1.id, report_path="reports/test_a1.pdf")
        rep_b1 = Report(inspection_id=ins_b1.id, report_path="reports/test_b1.pdf")
        db.add_all([rep_a1, rep_b1])
        db.commit()
        db.refresh(rep_a1)
        db.refresh(rep_b1)

        # 1. Test list_inspections for User A
        resp = Response()
        res_a = list_inspections(response=resp, current_user=user_a, db=db)
        a_ids = [i["id"] for i in res_a]
        assert ins_a1.id in a_ids and ins_a2.id in a_ids, "User A must see own inspections"
        assert ins_b1.id not in a_ids, f"User A must NOT see User B's inspection! Found: {ins_b1.id} in {a_ids}"
        print("  [PASS] User A ('Enforcement Officer') only sees own inspections in list.")

        # 2. Test list_inspections for User B
        res_b = list_inspections(response=resp, current_user=user_b, db=db)
        b_ids = [i["id"] for i in res_b]
        assert ins_b1.id in b_ids, "User B must see own inspection"
        assert ins_a1.id not in b_ids and ins_a2.id not in b_ids, "User B must NOT see User A's inspections"
        print("  [PASS] User B ('Inspector') only sees own inspections in list.")

        # 3. Test list_inspections for Admin and Supervisor (see all)
        res_admin = list_inspections(response=resp, current_user=admin_user, db=db)
        admin_ids = [i["id"] for i in res_admin]
        assert ins_a1.id in admin_ids and ins_a2.id in admin_ids and ins_b1.id in admin_ids
        print("  [PASS] Admin sees all inspections department-wide.")

        res_sup = list_inspections(response=resp, current_user=sup_user, db=db)
        sup_ids = [i["id"] for i in res_sup]
        assert ins_a1.id in sup_ids and ins_a2.id in sup_ids and ins_b1.id in sup_ids
        print("  [PASS] Supervisor sees all inspections department-wide.")

        # 4. Test get_dashboard_stats isolation
        stats_a = get_dashboard_stats(current_user=user_a, db=db)
        assert stats_a["total_inspections"] >= 2
        # User A's recent inspections must not include User B's items
        recent_a_ids = [r["id"] for r in stats_a["recent_inspections"]]
        assert ins_b1.id not in recent_a_ids, "Dashboard stats for User A must not include User B's inspections"
        print("  [PASS] Dashboard stats strictly isolated for Inspector A.")

        # 5. Test inspection detail authorization (get_inspection)
        # User A accessing User A's inspection -> OK
        detail_a = get_inspection(inspection_id=str(ins_a1.id), current_user=user_a, db=db)
        assert detail_a["id"] == ins_a1.id
        print("  [PASS] User A can view own inspection detail.")

        # User A accessing User B's inspection -> 403 Forbidden
        try:
            get_inspection(inspection_id=str(ins_b1.id), current_user=user_a, db=db)
            assert False, "Inspector accessing other user's inspection must raise 403 Forbidden!"
        except HTTPException as e:
            assert e.status_code == 403, f"Expected 403, got {e.status_code}"
            print("  [PASS] Inspector A denied access to Inspector B's inspection (403 Forbidden).")

        # Admin and Supervisor accessing User B's inspection -> OK
        detail_admin = get_inspection(inspection_id=str(ins_b1.id), current_user=admin_user, db=db)
        assert detail_admin["id"] == ins_b1.id
        detail_sup = get_inspection(inspection_id=str(ins_b1.id), current_user=sup_user, db=db)
        assert detail_sup["id"] == ins_b1.id
        print("  [PASS] Admin and Supervisor can view any inspection detail.")

        # 6. Test list_reports and get_report isolation
        reps_a = list_reports(current_user=user_a, db=db)
        rep_a_ins_ids = [r["inspection_id"] for r in reps_a]
        assert ins_a1.id in rep_a_ins_ids
        assert ins_b1.id not in rep_a_ins_ids, "User A must not see User B's report in reports list"
        print("  [PASS] Reports listing strictly isolated for Inspector A.")

        # User A accessing User B's report -> 403 Forbidden
        try:
            get_report(inspection_id=ins_b1.id, current_user=user_a, db=db)
            assert False, "Inspector accessing other user's report must raise 403 Forbidden!"
        except HTTPException as e:
            assert e.status_code == 403
            print("  [PASS] Inspector A denied access to Inspector B's report (403 Forbidden).")

        # Clean up test records
        db.delete(rep_a1)
        db.delete(rep_b1)
        db.delete(ins_a1)
        db.delete(ins_a2)
        db.delete(ins_b1)
        db.delete(user_a)
        db.delete(user_b)
        db.delete(admin_user)
        db.delete(sup_user)
        db.commit()
        print("  [PASS] Test records cleaned up successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 70)
    print(" RUNNING INSPECTION VISIBILITY & ROLE SCOPING TESTS (BUG 1)")
    print("=" * 70)
    test_role_normalization()
    test_scoped_inspection_visibility()
    print("\n" + "=" * 70)
    print(" ALL VISIBILITY & ROLE SCOPING TESTS PASSED (100%)!")
    print("=" * 70)
