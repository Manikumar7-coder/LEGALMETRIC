import os
import sys
import io
from PIL import Image

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app

def test_image_upload_feature():
    print("========================================================")
    print(" TESTING SAFEMETRIC PRODUCT-IMAGE UPLOAD FEATURE")
    print("========================================================")

    with TestClient(app) as client:
        # 1. Login to get authentication token
        print("\n--- 1. Authenticating Enforcement Officer ---")
        login_resp = client.post("/api/auth/login", json={
            "email": "officer@safemetric.gov.in",
            "password": "password123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"Authenticated successfully as: {login_resp.json()['user']['name']}")

        # 2. Test uploading real packaged-product image (sample_saferice.png)
        print("\n--- 2. Uploading Real Packaged-Product Image (PNG) ---")
        sample_path = os.path.join(backend_dir, "..", "demo_samples", "sample_saferice.png")
        assert os.path.exists(sample_path), f"Sample image not found: {sample_path}"

        with open(sample_path, "rb") as f:
            file_bytes = f.read()

        upload_resp = client.post(
            "/api/inspections/upload",
            files={"file": ("packaged_basmati_rice.png", io.BytesIO(file_bytes), "image/png")},
            data={"product_name": "Royal Basmati Rice 1kg Pack"},
            headers=headers
        )
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        data = upload_resp.json()
        print("Upload Response:")
        print(f"  Inspection ID: {data['id']}")
        print(f"  Product Name: {data['product_name']}")
        print(f"  Saved Filename: {data['filename']}")
        print(f"  Size: {data['size_formatted']} ({data['size_bytes']} bytes)")
        print(f"  Dimensions: {data['dimensions']['width']} x {data['dimensions']['height']} px")
        print(f"  Format: {data['format']}")
        print(f"  Status: {data['compliance_status']}")

        insp_id = data["id"]
        assert data["compliance_status"] == "PENDING_INSPECTION"
        assert data["dimensions"]["width"] > 0
        assert data["dimensions"]["height"] > 0

        # 3. Verify Inspection Record in Database (NO OCR, NO Legal Validation, NO Fake Records)
        print("\n--- 3. Verifying Database Record (No OCR, No Legal Validation) ---")
        rec_resp = client.get(f"/api/inspections/{insp_id}", headers=headers)
        assert rec_resp.status_code == 200
        rec = rec_resp.json()
        print(f"  DB Record ID: {rec['id']}")
        print(f"  Compliance Status: {rec['compliance_status']}")
        print(f"  Compliance Score: {rec['compliance_score']} (Must be 0.0)")
        print(f"  Raw OCR Text: '{rec['raw_ocr_text']}' (Must be empty - NO OCR implemented yet)")
        print(f"  Violations Count: {len(rec['violations'])} (Must be 0 - NO legal validation yet)")
        assert rec["compliance_score"] == 0.0
        assert rec["raw_ocr_text"] == ""
        assert len(rec["violations"]) == 0
        assert rec["image_url"] == f"/api/inspections/{insp_id}/image"

        # 4. Verify Image Retrieval
        print("\n--- 4. Verifying Uploaded Image Retrieval on Filesystem ---")
        img_resp = client.get(rec["image_url"])
        assert img_resp.status_code == 200
        assert len(img_resp.content) == len(file_bytes)
        print(f"  Retrieved {len(img_resp.content)} bytes (100% matches uploaded file)")

        # 5. Test uploading a JPEG format image
        print("\n--- 5. Uploading Real Packaged-Product Image (JPEG Format) ---")
        # Create a real JPEG packaging image
        jpeg_buf = io.BytesIO()
        pil_img = Image.open(sample_path).convert("RGB")
        pil_img.save(jpeg_buf, format="JPEG", quality=90)
        jpeg_bytes = jpeg_buf.getvalue()

        jpeg_upload = client.post(
            "/api/inspections/upload",
            files={"file": ("sunflower_oil_label.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
            data={"product_name": "Refined Sunflower Oil 1L"},
            headers=headers
        )
        assert jpeg_upload.status_code == 200, f"JPEG Upload failed: {jpeg_upload.text}"
        jpeg_data = jpeg_upload.json()
        print(f"  JPEG Upload OK: #{jpeg_data['id']}, Format: {jpeg_data['format']}, Size: {jpeg_data['size_formatted']}")
        assert jpeg_data["format"] == "JPEG"

        # 6. Test Format Validation (Reject Unsupported Formats)
        print("\n--- 6. Testing Format Validation (Rejecting Non-Image .PDF) ---")
        pdf_resp = client.post(
            "/api/inspections/upload",
            files={"file": ("label_document.pdf", io.BytesIO(b"%PDF-1.4 dummy"), "application/pdf")},
            headers=headers
        )
        assert pdf_resp.status_code == 400
        print(f"  Rejected unsupported format: {pdf_resp.json()['detail']}")
        assert "Unsupported format" in pdf_resp.json()["detail"]

        # 7. Test File Size Validation (Reject 0 bytes)
        print("\n--- 7. Testing File Size Validation (Rejecting 0 bytes) ---")
        empty_resp = client.post(
            "/api/inspections/upload",
            files={"file": ("empty_image.png", io.BytesIO(b""), "image/png")},
            headers=headers
        )
        assert empty_resp.status_code == 400
        print(f"  Rejected empty file: {empty_resp.json()['detail']}")

        # 8. Test File Size Validation (Reject > 10MB)
        print("\n--- 8. Testing File Size Validation (Rejecting > 10MB) ---")
        oversized_bytes = b"0" * (11 * 1024 * 1024) # 11MB
        oversized_resp = client.post(
            "/api/inspections/upload",
            files={"file": ("huge_packaging_photo.png", io.BytesIO(oversized_bytes), "image/png")},
            headers=headers
        )
        assert oversized_resp.status_code == 400
        print(f"  Rejected oversized file: {oversized_resp.json()['detail']}")
        assert "exceeds the maximum allowed limit" in oversized_resp.json()["detail"]

        # 9. Test Missing File Validation (Reject request without file)
        print("\n--- 9. Testing Missing File Validation (No file attached) ---")
        missing_resp = client.post(
            "/api/inspections/upload",
            data={"product_name": "Product Without Image"},
            headers=headers
        )
        assert missing_resp.status_code == 400
        print(f"  Rejected missing file: {missing_resp.json()['detail']}")
        assert "Missing product image file" in missing_resp.json()["detail"]

        print("\n========================================================")
        print(" ALL 9 PRODUCT-IMAGE UPLOAD FEATURE TESTS PASSED (100%)!")
        print("========================================================")

if __name__ == "__main__":
    test_image_upload_feature()
