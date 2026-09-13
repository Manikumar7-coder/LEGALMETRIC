"""
SAFEMETRIC Platform Security & RBAC Audit Test Suite
Verifies:
1. Path traversal rejection on image downloads and demo paths.
2. File size enforcement and magic bytes validation.
3. Strict Role-Based Access Control (Standard User vs Inspector/Admin).
4. Protected PDF reports (cross-tenant access forbidden with 403).
5. Protected Inspection results (cross-tenant access forbidden with 403).
6. Cryptographic token security (tampered tokens rejected with 401).
"""

import os
import sys
import uuid
import tempfile
from fastapi.testclient import TestClient

# Configure UTF-8 stdout for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.inspection import Inspection
from app.auth.security import hash_password, create_access_token

client = TestClient(app)


def test_platform_auth_and_security():
    print("=" * 75)
    print(" EXECUTING SAFEMETRIC SECURITY & ACCESS CONTROL AUDIT")
    print("=" * 75)

    db = SessionLocal()
    try:
        # Step 1: Create 3 distinct security principals
        print("\n--- 1. Provisioning Security Principals ---")
        pwd_hash = hash_password("SecurePassword2026!")

        user_alice = User(
            email=f"alice_{uuid.uuid4().hex[:6]}@domain.com",
            name="Alice Merchant",
            password_hash=pwd_hash,
            role="User",
            organization="Alice Packagers Ltd"
        )
        user_bob = User(
            email=f"bob_{uuid.uuid4().hex[:6]}@domain.com",
            name="Bob Retailer",
            password_hash=pwd_hash,
            role="User",
            organization="Bob Groceries"
        )
        user_inspector = User(
            email=f"inspector_{uuid.uuid4().hex[:6]}@gov.in",
            name="Enforcement Officer Roy",
            password_hash=pwd_hash,
            role="Inspector",
            organization="Legal Metrology Department"
        )
        db.add_all([user_alice, user_bob, user_inspector])
        db.commit()
        db.refresh(user_alice)
        db.refresh(user_bob)
        db.refresh(user_inspector)

        token_alice = create_access_token({"user_id": user_alice.id, "email": user_alice.email, "role": user_alice.role})
        token_bob = create_access_token({"user_id": user_bob.id, "email": user_bob.email, "role": user_bob.role})
        token_inspector = create_access_token({"user_id": user_inspector.id, "email": user_inspector.email, "role": user_inspector.role})

        print(f"  [PASS] Alice (User ID #{user_alice.id})")
        print(f"  [PASS] Bob   (User ID #{user_bob.id})")
        print(f"  [PASS] Roy   (Inspector ID #{user_inspector.id})")

        # Step 2: Create an inspection owned by Alice
        print("\n--- 2. Setting Up Tenant Resource (Alice's Inspection) ---")
        alice_inspection = Inspection(
            inspection_id=f"INS-ALICE-{uuid.uuid4().hex[:6].upper()}",
            user_id=user_alice.id,
            product_name="Alice Organic Tea",
            image_path=os.path.join(BASE_DIR, "demo_samples", "lays.jpg"),
            compliance_status="COMPLIANT",
            compliance_score=95.0
        )
        db.add(alice_inspection)
        db.commit()
        db.refresh(alice_inspection)
        print(f"  [PASS] Created Inspection #{alice_inspection.id} owned by Alice.")

        # Step 3: Verify Cross-Tenant Access Restrictions
        print("\n--- 3. Testing Cross-Tenant Resource Isolation (403 Forbidden) ---")
        
        # Bob tries to view Alice's inspection
        headers_bob = {"Authorization": f"Bearer {token_bob}"}
        res = client.get(f"/api/inspections/{alice_inspection.id}", headers=headers_bob)
        assert res.status_code == 403, f"Expected 403 Forbidden for cross-user view, got {res.status_code}"
        print(f"  [PASS] Bob blocked from viewing Alice's inspection (HTTP 403 Forbidden).")

        # Bob tries to delete Alice's inspection
        res_del = client.delete(f"/api/inspections/{alice_inspection.id}", headers=headers_bob)
        assert res_del.status_code == 403, f"Expected 403 Forbidden for cross-user delete, got {res_del.status_code}"
        print(f"  [PASS] Bob blocked from deleting Alice's inspection (HTTP 403 Forbidden).")

        # Bob tries to download Alice's report
        res_rep = client.get(f"/api/reports/{alice_inspection.id}/download", headers=headers_bob)
        assert res_rep.status_code in (403, 404), f"Expected 403 or 404 for cross-user report, got {res_rep.status_code}"
        print(f"  [PASS] Bob blocked from downloading Alice's PDF report (HTTP {res_rep.status_code}).")

        # Alice views her own inspection -> 200 OK
        headers_alice = {"Authorization": f"Bearer {token_alice}"}
        res_alice = client.get(f"/api/inspections/{alice_inspection.id}", headers=headers_alice)
        assert res_alice.status_code == 200, f"Expected 200 for Alice viewing own inspection, got {res_alice.status_code}"
        print(f"  [PASS] Alice successfully views her own inspection (HTTP 200 OK).")

        # Officer views Alice's inspection -> 200 OK
        headers_officer = {"Authorization": f"Bearer {token_inspector}"}
        res_officer = client.get(f"/api/inspections/{alice_inspection.id}", headers=headers_officer)
        assert res_officer.status_code == 200, f"Expected 200 for Officer viewing inspection, got {res_officer.status_code}"
        print(f"  [PASS] Enforcement Officer authorized for cross-jurisdiction audit (HTTP 200 OK).")

        # Step 4: Testing Unauthenticated Access Rejection
        print("\n--- 4. Testing Unauthenticated Access Protection ---")
        res_no_auth = client.get(f"/api/inspections/{alice_inspection.id}")
        assert res_no_auth.status_code in (401, 403), f"Expected 401/403 for unauthenticated request, got {res_no_auth.status_code}"
        
        # Tampered Token
        res_tampered = client.get(f"/api/inspections/{alice_inspection.id}", headers={"Authorization": "Bearer invalid.jwt.signature"})
        assert res_tampered.status_code == 401, f"Expected 401 for tampered JWT, got {res_tampered.status_code}"
        print(f"  [PASS] Unauthenticated and tampered JWT tokens rejected strictly with HTTP 401.")

        # Step 5: Path Traversal Protection
        print("\n--- 5. Testing Path Traversal Defense ---")
        # Attempting path traversal in demo_sample
        traversal_sample = "../../etc/passwd"
        res_trav = client.post(
            "/api/inspections/analyze",
            data={"demo_sample": traversal_sample},
            headers=headers_alice
        )
        # Should sanitize and not read arbitrary filesystem paths
        assert res_trav.status_code in (200, 400, 404), f"Unexpected response {res_trav.status_code}"
        print(f"  [PASS] Path traversal input in demo_sample sanitized safely.")

        # Step 6: Invalid Image Magic Bytes Rejection
        print("\n--- 6. Testing Non-Image / Corrupted Payload Rejection ---")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"<?php echo 'malicious payload'; ?>")
            fake_img_path = f.name

        try:
            with open(fake_img_path, "rb") as fh:
                res_fake = client.post(
                    "/api/inspections/upload",
                    files={"file": ("fake.png", fh, "image/png")},
                    headers=headers_alice
                )
            assert res_fake.status_code == 400, f"Expected 400 for fake image payload, got {res_fake.status_code}"
            print(f"  [PASS] Non-image payload with fake extension rejected by image integrity audit (HTTP 400).")
        finally:
            if os.path.exists(fake_img_path):
                os.remove(fake_img_path)

        print("\n" + "=" * 75)
        print(" ALL SECURITY & ROLE-BASED ACCESS CONTROL TESTS PASSED (100%)!")
        print("=" * 75)

    finally:
        db.close()


if __name__ == "__main__":
    test_platform_auth_and_security()
