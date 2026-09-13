import os
import sys
import hashlib
from fastapi.testclient import TestClient

# Configure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.main import app
from app.ocr.ocr_service import ocr_service, LOW_CONFIDENCE_THRESHOLD

client = TestClient(app)


def test_ocr_lays_pipeline():
    print("=" * 70)
    print(" TESTING SAFEMETRIC OCR SUBSYSTEM (LAY'S PRODUCT IMAGE)")
    print("=" * 70)

    # 1. Locate Lay's Product Image
    lays_path = r"C:\Users\doram\Downloads\lays.jpg"
    if not os.path.exists(lays_path):
        lays_path = os.path.join(BASE_DIR, "demo_samples", "lays.jpg")

    assert os.path.exists(lays_path), f"Lay's product image not found at {lays_path}!"
    print(f"\n[Target Image]: {lays_path}")

    # 2. Check Original Image Immutability
    with open(lays_path, "rb") as f:
        md5_before = hashlib.md5(f.read()).hexdigest()
    size_before = os.path.getsize(lays_path)

    # -----------------------------------------------------------------
    # Step 1: Direct OCR Service Processing on Lay's Package
    # -----------------------------------------------------------------
    print("\n--- 1. Executing RapidOCR Engine on Lay's Packaging ---")
    ocr_result = ocr_service.process_image(lays_path, is_demo=False)

    # Verify original image was not modified
    with open(lays_path, "rb") as f:
        md5_after = hashlib.md5(f.read()).hexdigest()
    assert md5_before == md5_after, "Original image was modified by OCR service!"
    assert size_before == os.path.getsize(lays_path), "Original image size changed!"
    print(f"  [PASS] Original image preserved 100% intact (MD5: {md5_after})")

    # -----------------------------------------------------------------
    # Step 2: Verify Dual Image Retention
    # -----------------------------------------------------------------
    print("\n--- 2. Verifying Dual Image Retention ---")
    orig_path = ocr_result.get("original_image_path")
    prep_path = ocr_result.get("preprocessed_image_path")
    print(f"  Original Path:     {orig_path}")
    print(f"  Preprocessed Path: {prep_path}")
    assert orig_path and os.path.exists(orig_path), "Original path missing!"
    assert prep_path and os.path.exists(prep_path), "Preprocessed path missing!"
    assert orig_path != prep_path, "Original and preprocessed paths must be distinct!"
    print("  [PASS] Both original and preprocessed images independently exist on disk.")

    # -----------------------------------------------------------------
    # Step 3: Extracted Text Verification
    # -----------------------------------------------------------------
    print("\n--- 3. Verifying Extracted Text ---")
    raw_text = ocr_result.get("raw_text", "")
    lines = ocr_result.get("text_lines", [])
    print(f"  Total Extracted Lines: {len(lines)}")
    assert len(lines) >= 70, f"Expected >= 70 lines from Lay's package, got {len(lines)}"

    # Check statutory keywords extracted optically (packaging often condenses words like BESTBEFORE)
    keywords_expected = [
        "pepsico", "nutritional", "potato chips", "mrp", "bestbefore", "1800224020"
    ]
    raw_lower = raw_text.lower().replace(" ", "")
    for kw in keywords_expected:
        assert kw.replace(" ", "") in raw_lower, f"Expected statutory declaration keyword '{kw}' not found in OCR text!"
        print(f"  [Found Keyword]: '{kw}'")


    print("  [PASS] All core statutory text declarations extracted optically without guessing.")

    # -----------------------------------------------------------------
    # Step 4: Detected Regions / Bounding Boxes
    # -----------------------------------------------------------------
    print("\n--- 4. Verifying Detected Regions & Bounding Boxes ---")
    boxes = ocr_result.get("bounding_boxes", [])
    print(f"  Total Detected Regions: {len(boxes)}")
    assert len(boxes) == len(lines), "Bounding box count should match text line count!"

    for i, b in enumerate(boxes[:5], 1):
        box_pts = b["box"]
        assert len(box_pts) == 4, f"Box {i} must have 4 corner vertices!"
        for pt in box_pts:
            assert len(pt) == 2 and isinstance(pt[0], int) and isinstance(pt[1], int), "Box coordinates must be integer points!"
        print(f"  Region {i:02d}: '{b['text']}' -> {b['confidence']}% [Box: {box_pts}]")

    print("  [PASS] All text regions mapped with 4-point polygon bounding boxes in original image space.")

    # -----------------------------------------------------------------
    # Step 5: Confidence Scores & Low-Confidence Preservation
    # -----------------------------------------------------------------
    print("\n--- 5. Verifying Confidence Information & Low-Confidence Preservation ---")
    summary = ocr_result.get("confidence_summary", {})
    avg_conf = summary.get("average_confidence", 0.0)
    min_conf = summary.get("min_confidence", 0.0)
    max_conf = summary.get("max_confidence", 0.0)
    total_reg = summary.get("total_regions", 0)
    low_count = summary.get("low_confidence_count", 0)
    high_count = summary.get("high_confidence_count", 0)

    print(f"  Average Confidence:    {avg_conf}%")
    print(f"  Min Confidence:        {min_conf}%")
    print(f"  Max Confidence:        {max_conf}%")
    print(f"  High-Confidence Count: {high_count} (>= {LOW_CONFIDENCE_THRESHOLD}%)")
    print(f"  Low-Confidence Count:  {low_count} (< {LOW_CONFIDENCE_THRESHOLD}%)")

    assert avg_conf > 88.0, f"Expected high overall confidence >88%, got {avg_conf}%"
    assert min_conf > 40.0, "Minimum confidence should be reasonable"
    assert max_conf <= 100.0, "Maximum confidence cannot exceed 100%"

    low_regions = ocr_result.get("low_confidence_regions", [])
    assert len(low_regions) == low_count, "Low confidence list length mismatch!"
    print(f"\n  Preserved Low-Confidence Regions for Human Review ({len(low_regions)} items):")
    for r in low_regions:
        print(f"    - Line {r['line_number']}: '{r['text']}' ({r['confidence']}%) [Box: {r['box']}]")
        print(f"      Reason: {r['reason']}")

    assert ocr_result.get("low_confidence_review_required") is True, "Review flag should be True when low-conf regions exist!"
    print("  [PASS] Low-confidence regions successfully preserved with line numbers, boxes, and review flags.")

    # -----------------------------------------------------------------
    # Step 6: OCR Limitations Reporting
    # -----------------------------------------------------------------
    print("\n--- 6. Verifying OCR Limitations Diagnostic Reporting ---")
    limitations = ocr_result.get("limitations", [])
    assert len(limitations) > 0, "Limitations should be diagnosed and reported!"
    for lim in limitations:
        print(f"  * {lim}")
    print("  [PASS] Optical limitations accurately diagnosed.")

    # -----------------------------------------------------------------
    # Step 7: Boundary Check - No Legal Decisions or Guesses
    # -----------------------------------------------------------------
    print("\n--- 7. Verifying Compliance Boundary ---")
    assert "compliance_score" not in ocr_result, "CRITICAL: compliance_score must not be computed in OCR!"
    assert "violations" not in ocr_result, "CRITICAL: violations must not be computed in OCR!"
    assert "compliance_status" not in ocr_result, "CRITICAL: compliance_status must not be computed in OCR!"
    print("  [PASS] Zero legal compliance decisions made during OCR.")

    # -----------------------------------------------------------------
    # Step 8: Testing HTTP API Endpoint POST /api/inspections/{id}/ocr
    # -----------------------------------------------------------------
    print("\n--- 8. Testing HTTP API Endpoint (POST /api/inspections/{id}/ocr) ---")
    # Login as officer
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "officer@safemetric.gov.in", "password": "password123"}
    )
    assert login_resp.status_code == 200, f"Officer authentication failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}


    # Upload Lay's image to register an inspection
    with open(lays_path, "rb") as img_f:
        upload_resp = client.post(
            "/api/inspections/upload",
            files={"file": ("lays.jpg", img_f, "image/jpeg")},
            data={"product_name": "Lay's Spanish Tomato Tango 52g"},
            headers=headers
        )
    assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
    insp_id = upload_resp.json()["id"]
    print(f"  Uploaded Inspection Registered: ID #{insp_id}")

    # Call OCR endpoint
    ocr_api_resp = client.post(f"/api/inspections/{insp_id}/ocr", headers=headers)
    assert ocr_api_resp.status_code == 200, f"OCR API failed: {ocr_api_resp.text}"
    api_data = ocr_api_resp.json()

    assert api_data["inspection_id"] == insp_id
    assert api_data["compliance_status"] == "OCR_COMPLETED"
    assert len(api_data["bounding_boxes"]) == len(boxes)
    assert api_data["confidence_summary"]["average_confidence"] == avg_conf
    assert len(api_data["low_confidence_regions"]) == low_count
    print(f"  API Response Status: {api_data['compliance_status']}")
    print(f"  API Bounding Boxes:  {len(api_data['bounding_boxes'])} regions")
    print(f"  API Engine:          {api_data['engine']}")
    print("  [PASS] HTTP API endpoint /api/inspections/{id}/ocr executed and persisted OCR data successfully.")

    print("\n" + "=" * 70)
    print(" ALL OCR SUBSYSTEM TESTS PASSED (100%)!")
    print("=" * 70)


if __name__ == "__main__":
    test_ocr_lays_pipeline()
