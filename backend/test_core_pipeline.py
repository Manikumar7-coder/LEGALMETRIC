"""
SAFEMETRIC Core Pipeline Test
Tests the complete pipeline: image upload -> unique image storage -> OCR -> extraction 
-> compliance -> DB persistence -> API retrieval.
Also verifies Inspection A/B isolation (no cross-contamination between uploads).

Run: python test_core_pipeline.py
"""
import os
import sys
import io
import hashlib

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
DEFAULT_EMAIL = 'officer@safemetric.gov.in'
DEFAULT_PASSWORD = 'password123'

PASS_COUNT = 0
FAIL_COUNT = 0


def check(label: str, condition: bool, detail: str = ""):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  [PASS] {label}")
    else:
        FAIL_COUNT += 1
        print(f"  [FAIL] {label} {detail}")


def login():
    res = client.post('/api/auth/login', json={'email': DEFAULT_EMAIL, 'password': DEFAULT_PASSWORD})
    assert res.status_code == 200, f'Login failed: {res.status_code} {res.text}'
    return {'Authorization': 'Bearer ' + res.json()['access_token']}


def make_test_image(label: str, color=(200, 255, 200)) -> bytes:
    """Creates a unique synthetic test image with visible text drawn on it."""
    img = Image.new('RGB', (700, 500), color=color)
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), label, fill=(0, 0, 0))
    draw.text((30, 80), 'Net Quantity: 200 g', fill=(0, 0, 0))
    draw.text((30, 130), 'MRP: Rs. 50 (Incl. of all taxes)', fill=(0, 0, 0))
    draw.text((30, 180), f'Manufactured By: {label} Foods Pvt Ltd', fill=(0, 0, 0))
    draw.text((30, 230), 'Country of Origin: India', fill=(0, 0, 0))
    draw.text((30, 280), 'Best Before: 06/2027', fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def sha256_prefix(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def test_core_pipeline():
    print('=' * 75)
    print(' SAFEMETRIC CORE PIPELINE TEST')
    print('=' * 75)

    headers = login()

    # --- 0. Verify empty history (no demo data) ---
    print('\n--- 0. Verifying History is Empty (No Demo Data) ---')
    hist = client.get('/api/inspections', headers=headers)
    check("History endpoint returns 200", hist.status_code == 200)
    all_inspections = hist.json()
    # Count only demo/sample inspections (not test ones from previous runs)
    demo_names = ['SafeRice Premium', 'Crispy Delight', 'sample_saferice', 'sample_wafer']
    demo_records = [i for i in all_inspections if any(d in (i.get('product_name') or '') for d in demo_names)]
    check(f"No demo SafeRice/CrispyDelight records in history", len(demo_records) == 0,
          f"(found {len(demo_records)} demo records)")

    # --- 1. Create two unique test images ---
    print('\n--- 1. Creating Two Unique Test Images ---')
    img_a_bytes = make_test_image('AlphaTest', color=(220, 255, 220))
    img_b_bytes = make_test_image('BetaTest', color=(220, 220, 255))
    hash_a = sha256_prefix(img_a_bytes)
    hash_b = sha256_prefix(img_b_bytes)
    check("Image A and B are different bytes", hash_a != hash_b)
    print(f'    Image A: {hash_a}')
    print(f'    Image B: {hash_b}')

    # --- 2. Upload Image A ---
    print('\n--- 2. Uploading Image A ---')
    res_a = client.post(
        '/api/inspections/analyze',
        files={'file': ('product_a.png', img_a_bytes, 'image/png')},
        headers=headers
    )
    check("Image A upload returns 200", res_a.status_code == 200, res_a.text[:200])
    insp_a = res_a.json()
    id_a = insp_a.get('id')
    path_a = insp_a.get('uploaded_image_reference') or insp_a.get('image_path', '')
    check("Inspection A has an ID", id_a is not None)
    check("Inspection A has a stored image path", bool(path_a))
    print(f'    Inspection A: id={id_a}, image={path_a}')

    # --- 3. Upload Image B ---
    print('\n--- 3. Uploading Image B ---')
    res_b = client.post(
        '/api/inspections/analyze',
        files={'file': ('product_b.png', img_b_bytes, 'image/png')},
        headers=headers
    )
    check("Image B upload returns 200", res_b.status_code == 200, res_b.text[:200])
    insp_b = res_b.json()
    id_b = insp_b.get('id')
    path_b = insp_b.get('uploaded_image_reference') or insp_b.get('image_path', '')
    check("Inspection B has a unique ID", id_b is not None and id_b != id_a)
    check("Inspection B has a unique stored image path", path_b != path_a)
    print(f'    Inspection B: id={id_b}, image={path_b}')

    # --- 4. Verify images on disk ---
    print('\n--- 4. Verifying Image Files On Disk ---')
    check("Image A file exists on disk", os.path.exists(path_a))
    if os.path.exists(path_a):
        with open(path_a, 'rb') as f:
            stored_hash_a = sha256_prefix(f.read())
        check(f"Image A disk hash matches upload ({stored_hash_a})", stored_hash_a == hash_a)

    check("Image B file exists on disk", os.path.exists(path_b))
    if os.path.exists(path_b):
        with open(path_b, 'rb') as f:
            stored_hash_b = sha256_prefix(f.read())
        check(f"Image B disk hash matches upload ({stored_hash_b})", stored_hash_b == hash_b)

    # --- 5. Verify OCR debug endpoint ---
    print('\n--- 5. Verifying OCR Debug Endpoint ---')
    debug_a = client.get(f'/api/inspections/{id_a}/debug/ocr', headers=headers)
    check("Debug endpoint A returns 200", debug_a.status_code == 200, debug_a.text[:200])
    if debug_a.status_code == 200:
        da = debug_a.json()
        check("Debug A image_path matches stored path", da.get('image_path') == path_a)
        check("Debug A image_sha256_prefix matches upload", da.get('image_sha256_prefix') == hash_a)
        check("Debug A raw_ocr_text is non-empty (OCR ran)", len(da.get('raw_ocr_text', '')) > 0,
              f"(got {len(da.get('raw_ocr_text', ''))} chars)")
        print(f"    OCR text A ({da.get('ocr_char_count', 0)} chars): {da.get('raw_ocr_text', '')[:80]}...")

    debug_b = client.get(f'/api/inspections/{id_b}/debug/ocr', headers=headers)
    check("Debug endpoint B returns 200", debug_b.status_code == 200, debug_b.text[:200])
    if debug_b.status_code == 200:
        db_data = debug_b.json()
        check("Debug B image_path matches stored path", db_data.get('image_path') == path_b)
        check("Debug B image_sha256_prefix matches upload", db_data.get('image_sha256_prefix') == hash_b)
        check("A and B have different image hashes in debug (no cross-contamination)",
              da.get('image_sha256_prefix') != db_data.get('image_sha256_prefix'))
        print(f"    OCR text B ({db_data.get('ocr_char_count', 0)} chars): {db_data.get('raw_ocr_text', '')[:80]}...")

    # --- 6. Verify compliance was computed ---
    print('\n--- 6. Verifying Compliance Results ---')
    check("Inspection A has a compliance status", bool(insp_a.get('status')))
    check("Inspection B has a compliance status", bool(insp_b.get('status')))
    print(f'    A status: {insp_a.get("status")}, score: {insp_a.get("compliance_score")}')
    print(f'    B status: {insp_b.get("status")}, score: {insp_b.get("compliance_score")}')

    # --- 7. Re-fetch inspection A after B exists ---
    print('\n--- 7. Re-fetching Inspection A After B Exists (Persistence Check) ---')
    refetch_a = client.get(f'/api/inspections/{id_a}', headers=headers)
    check("Re-fetch A returns 200", refetch_a.status_code == 200)
    if refetch_a.status_code == 200:
        ra = refetch_a.json()
        check("Re-fetched A has same ID", ra.get('id') == id_a)
        fetched_path = ra.get('uploaded_image_reference') or ra.get('image_path', '')
        check("Re-fetched A still has same image path", fetched_path == path_a)

    # --- 8. History contains both new inspections ---
    print('\n--- 8. Verifying History Contains Both Inspections ---')
    hist2 = client.get('/api/inspections', headers=headers)
    check("History returns 200", hist2.status_code == 200)
    if hist2.status_code == 200:
        hist_ids = [i['id'] for i in hist2.json()]
        check(f"History contains inspection A (id={id_a})", id_a in hist_ids)
        check(f"History contains inspection B (id={id_b})", id_b in hist_ids)

    # --- 9. Dashboard statistics are real (not hardcoded) ---
    print('\n--- 9. Verifying Dashboard Stats Are From Real Data ---')
    dash = client.get('/api/dashboard/stats', headers=headers)
    check("Dashboard stats returns 200", dash.status_code == 200)
    if dash.status_code == 200:
        stats = dash.json()
        total = stats.get('total_inspections', -1)
        check(f"Dashboard total_inspections >= 2 (real data)", total >= 2,
              f"(got {total})")
        print(f"    total_inspections={total}, compliant={stats.get('compliant_count')}, "
              f"needs_review={stats.get('needs_review_count')}")

    # --- 10. OCR result isolation (different OCR texts for different images) ---
    print('\n--- 10. Verifying OCR Text Isolation Between Inspections ---')
    if debug_a.status_code == 200 and debug_b.status_code == 200:
        text_a = debug_a.json().get('raw_ocr_text', '')
        text_b = debug_b.json().get('raw_ocr_text', '')
        check("Inspection A and B have different OCR text", text_a != text_b,
              "(OCR text should differ since images are different)")

    # Summary
    print()
    print('=' * 75)
    total_tests = PASS_COUNT + FAIL_COUNT
    print(f' RESULTS: {PASS_COUNT}/{total_tests} PASSED, {FAIL_COUNT} FAILED')
    if FAIL_COUNT == 0:
        print(' ALL CORE PIPELINE TESTS PASSED!')
    else:
        print(f' WARNING: {FAIL_COUNT} test(s) failed — review output above.')
    print('=' * 75)
    return FAIL_COUNT == 0


if __name__ == '__main__':
    success = test_core_pipeline()
    sys.exit(0 if success else 1)
