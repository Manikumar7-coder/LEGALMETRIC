import sys
import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.inspection import Inspection
from app.models.report import Report
from app.auth.security import create_access_token

client = TestClient(app)
db = SessionLocal()

print("=" * 70)
print(" RUNNING REPORT DOWNLOAD RBAC VERIFICATION SUITE")
print("=" * 70)

# Identify MYFITNESS inspection (ID #31)
insp_31 = db.query(Inspection).filter(Inspection.id == 31).first()
if not insp_31:
    print("[FAIL] Could not find Inspection #31 (MYFITNESS) in database.")
    sys.exit(1)

owner_id = insp_31.user_id
owner = db.query(User).filter(User.id == owner_id).first()
print(f"Target Inspection: #{insp_31.id} ('{insp_31.product_name}'), Owner: ID={owner.id}, Name='{owner.name}', Role='{owner.role}'")

# Identify another inspector who does NOT own #31
other_inspector = (
    db.query(User)
    .filter(User.role.in_(["Inspector", "Enforcement Officer"]))
    .filter(User.id != owner_id)
    .first()
)
print(f"Non-owner Inspector: ID={other_inspector.id}, Name='{other_inspector.name}', Role='{other_inspector.role}'")

# Identify Admin and Supervisor
admin_user = db.query(User).filter(User.role == "Admin").first()
supervisor_user = db.query(User).filter(User.role == "Supervisor").first()
print(f"Admin User: ID={admin_user.id}, Role='{admin_user.role}'")
print(f"Supervisor User: ID={supervisor_user.id}, Role='{supervisor_user.role}'")

owner_token = create_access_token({"user_id": owner.id, "email": owner.email, "role": owner.role})
other_token = create_access_token({"user_id": other_inspector.id, "email": other_inspector.email, "role": other_inspector.role})
admin_token = create_access_token({"user_id": admin_user.id, "email": admin_user.email, "role": admin_user.role})
supervisor_token = create_access_token({"user_id": supervisor_user.id, "email": supervisor_user.email, "role": supervisor_user.role})

print("\n--- 1. Testing Owner Downloads (PDF, DOCX, CSV) ---")
for fmt in ["pdf", "docx", "csv"]:
    # Test via query param (?token=...)
    res_query = client.get(f"/api/reports/{insp_31.id}/download?format={fmt}&token={owner_token}")
    assert res_query.status_code == 200, f"Owner query download failed for format {fmt}: {res_query.status_code}, {res_query.text}"
    print(f"  [PASS] Owner download ({fmt.upper()}) via ?token=: HTTP 200 OK (Content-Type: {res_query.headers.get('content-type')})")

    # Test via Bearer header
    res_bearer = client.get(f"/api/reports/{insp_31.id}/download?format={fmt}", headers={"Authorization": f"Bearer {owner_token}"})
    assert res_bearer.status_code == 200, f"Owner Bearer download failed for format {fmt}: {res_bearer.status_code}, {res_bearer.text}"
    print(f"  [PASS] Owner download ({fmt.upper()}) via Bearer header: HTTP 200 OK")

print("\n--- 2. Testing Non-Owner Inspector Blocked (403 Forbidden) ---")
for fmt in ["pdf", "docx", "csv"]:
    # Test via query param
    res_query = client.get(f"/api/reports/{insp_31.id}/download?format={fmt}&token={other_token}")
    assert res_query.status_code == 403, f"Non-owner was not blocked for {fmt}: {res_query.status_code}"
    assert "Access denied" in res_query.json().get("detail", ""), f"Unexpected error detail: {res_query.text}"
    print(f"  [PASS] Non-owner Inspector blocked ({fmt.upper()}) via ?token=: HTTP 403 Forbidden")

    # Test via Bearer header
    res_bearer = client.get(f"/api/reports/{insp_31.id}/download?format={fmt}", headers={"Authorization": f"Bearer {other_token}"})
    assert res_bearer.status_code == 403, f"Non-owner was not blocked for {fmt}: {res_bearer.status_code}"
    print(f"  [PASS] Non-owner Inspector blocked ({fmt.upper()}) via Bearer: HTTP 403 Forbidden")

print("\n--- 3. Testing Admin & Supervisor Downloads (Allowed Any Report) ---")
for role_name, token in [("Admin", admin_token), ("Supervisor", supervisor_token)]:
    for fmt in ["pdf", "docx", "csv"]:
        res = client.get(f"/api/reports/{insp_31.id}/download?format={fmt}&token={token}")
        assert res.status_code == 200, f"{role_name} download failed for format {fmt}: {res.status_code}, {res.text}"
        print(f"  [PASS] {role_name} download ({fmt.upper()}): HTTP 200 OK")

print("\n--- 4. Testing Unauthenticated Request Rejected (401 Unauthorized) ---")
res_unauth = client.get(f"/api/reports/{insp_31.id}/download?format=pdf")
assert res_unauth.status_code == 401, f"Unauthenticated request was not 401: {res_unauth.status_code}"
print("  [PASS] Unauthenticated download request correctly rejected: HTTP 401 Unauthorized")

print("\n--- 5. Testing get_report Endpoint RBAC ---")
# Owner can view
res_owner_view = client.get(f"/api/reports/{insp_31.id}", headers={"Authorization": f"Bearer {owner_token}"})
assert res_owner_view.status_code == 200, f"Owner view failed: {res_owner_view.status_code}"
print("  [PASS] Owner can view report metadata: HTTP 200 OK")

# Non-owner blocked
res_other_view = client.get(f"/api/reports/{insp_31.id}", headers={"Authorization": f"Bearer {other_token}"})
assert res_other_view.status_code == 403, f"Non-owner view not blocked: {res_other_view.status_code}"
print("  [PASS] Non-owner Inspector blocked from report metadata: HTTP 403 Forbidden")

# Admin can view
res_admin_view = client.get(f"/api/reports/{insp_31.id}", headers={"Authorization": f"Bearer {admin_token}"})
assert res_admin_view.status_code == 200, f"Admin view failed: {res_admin_view.status_code}"
print("  [PASS] Admin can view report metadata: HTTP 200 OK")

# Supervisor can view
res_sup_view = client.get(f"/api/reports/{insp_31.id}", headers={"Authorization": f"Bearer {supervisor_token}"})
assert res_sup_view.status_code == 200, f"Supervisor view failed: {res_sup_view.status_code}"
print("  [PASS] Supervisor can view report metadata: HTTP 200 OK")

print("\n" + "=" * 70)
print(" ALL REPORT DOWNLOAD RBAC VERIFICATION TESTS PASSED (100%)!")
print("=" * 70)

db.close()
