import os
import sys

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app

def test_all():
    # Use context manager so FastAPI lifespan is triggered
    with TestClient(app) as client:
        print("--- 1. Testing Root & Health ---")
        res = client.get("/")
        assert res.status_code == 200, f"Root failed: {res.text}"
        print("Root OK:", res.json()["system"])

        res = client.get("/api/health")
        assert res.status_code == 200
        print("Health OK:", res.json())

        print("\n--- 2. Testing Authentication ---")
        # Login with seeded officer
        res = client.post("/api/auth/login", json={
            "email": "officer@safemetric.gov.in",
            "password": "password123"
        })
        assert res.status_code == 200, f"Login failed: {res.text}"
        token_data = res.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login OK. Officer:", token_data["user"]["name"])

        # Test /api/auth/me
        res = client.get("/api/auth/me", headers=headers)
        assert res.status_code == 200
        print("Auth Me OK:", res.json()["email"])

        print("\n--- 3. Testing Rules Endpoint ---")
        res = client.get("/api/rules")
        assert res.status_code == 200
        rules = res.json()
        assert len(rules) >= 8
        print(f"Rules OK: {len(rules)} statutory rules configured.")

        print("\n--- 4. Testing Dashboard Stats ---")
        res = client.get("/api/dashboard/stats", headers=headers)
        assert res.status_code == 200
        stats = res.json()
        print("Dashboard Stats OK:", {
            "total": stats["total_inspections"],
            "compliant": stats["compliant_count"],
            "non_compliant": stats["non_compliant_count"],
            "score_pct": stats["compliance_percentage"]
        })

        print("\n--- 5. Testing Profile Endpoint ---")
        res = client.get("/api/profile", headers=headers)
        assert res.status_code == 200
        print("Profile OK:", res.json()["role"])

        print("\n--- 6. Testing Inspection Analysis (Compliant Demo) ---")
        res = client.post(
            "/api/inspections/analyze",
            data={"demo_sample": "saferice", "product_name": "SafeRice Basmati Test"},
            headers=headers
        )
        assert res.status_code == 200, f"Analysis failed: {res.text}"
        rice_res = res.json()
        print("SafeRice Analysis OK:")
        print("  Status:", rice_res["compliance_status"])
        print("  Score:", rice_res["compliance_score"], "%")
        print("  Violations:", len(rice_res["violations"]))
        assert rice_res["compliance_status"] == "COMPLIANT"

        print("\n--- 7. Testing Inspection Analysis (Non-Compliant Demo) ---")
        res = client.post(
            "/api/inspections/analyze",
            data={"demo_sample": "wafer", "product_name": "Crispy Delight Test"},
            headers=headers
        )
        assert res.status_code == 200, f"Analysis failed: {res.text}"
        wafer_res = res.json()
        print("Crispy Delight Analysis OK:")
        print("  Status:", wafer_res["compliance_status"])
        print("  Score:", wafer_res["compliance_score"], "%")
        print("  Violations Count:", len(wafer_res["violations"]))
        assert wafer_res["compliance_status"] == "NON-COMPLIANT"

        print("\n--- 8. Testing Reports Listing & Download ---")
        res = client.get("/api/reports", headers=headers)
        assert res.status_code == 200
        reports = res.json()
        assert len(reports) > 0
        print(f"Reports Listing OK: {len(reports)} reports found.")

        first_insp_id = reports[0]["inspection_id"]
        pdf_res = client.get(f"/api/reports/{first_insp_id}/download")
        assert pdf_res.status_code == 200
        assert pdf_res.headers.get("content-type") == "application/pdf"
        assert len(pdf_res.content) > 1000
        print(f"PDF Download OK: received {len(pdf_res.content)} bytes of valid PDF.")

        print("\n--- 9. Testing Real File Upload & Dynamic RapidOCR Inference ---")
        sample_img_path = os.path.join(backend_dir, "..", "demo_samples", "sample_saferice.png")
        if os.path.exists(sample_img_path):
            with open(sample_img_path, "rb") as f_img:
                res = client.post(
                    "/api/inspections/analyze",
                    files={"file": ("test_commodity_label.png", f_img, "image/png")},
                    data={"product_name": "Dynamic Scanned Commodity"},
                    headers=headers
                )
            assert res.status_code == 200, f"Upload analysis failed: {res.text}"
            upload_res = res.json()
            print("Dynamic Upload Analysis OK:")
            print("  Status:", upload_res["compliance_status"])
            print("  Score:", upload_res["compliance_score"], "%")
            print("  Detected Fields:", len(upload_res["fields"]))
            print("  Bounding Boxes Count:", len(upload_res.get("bounding_boxes", [])))
            assert len(upload_res["fields"]) > 0

        print("\n--- 10. Testing Unit Sale Price (USP) & Generic Name Validation ---")
        from app.extraction.field_extractor import field_extractor
        from app.rules.rule_engine import rule_engine
        
        sample_pcr_text = (
            "Kavita Refined Sunflower Oil\n"
            "Commodity: Edible Vegetable Oil\n"
            "Net Quantity: 1 Litre\n"
            "MRP: Rs. 140 (Incl. of all taxes)\n"
            "Unit Sale Price: Rs. 140.00 / l\n"
            "Mfg Date: 09/2026\n"
            "Best Before: 09/2027\n"
            "Manufactured by: Kavita Oils Ltd\n"
            "Address: Industrial Estate, Surat, Gujarat - 395001\n"
            "Consumer Care Cell: 1800-999-8888\n"
            "Country of Origin: India"
        )
        ext = field_extractor.extract_declarations(sample_pcr_text)
        assert ext["generic_name"]["status"] == "Found"
        assert ext["unit_sale_price"]["status"] == "Found"
        eval_res = rule_engine.evaluate(ext)
        print("  USP & Generic Name Evaluated:")
        print("  Status:", eval_res["compliance_status"])
        print("  Score:", eval_res["compliance_score"], "%")
        assert eval_res["compliance_score"] >= 80.0

        print("\n==========================================")
        print("ALL 10 BACKEND COMPONENT TESTS PASSED 100%!")
        print("==========================================")

if __name__ == "__main__":
    test_all()
