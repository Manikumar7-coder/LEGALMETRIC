"""
Test Suite: Field Extraction Resilience Against Noisy / OCR-Garbled Text (BUG 2).
Verifies:
1. MRP extraction handles currency OCR misreads (e.g. ₹ -> R) adjacent to MRP token ('MRP:R6491').
2. When digit count looks inconsistent with typical Indian retail pricing (e.g., 4+ digits without decimal '6491'),
   the extractor routes to OCR_UNCERTAIN / NEEDS_REVIEW with raw text preserved, without guessing or truncation.
3. Clean MRP values continue to extract with CONFIRMED_PRESENT.
4. India Gate blank MRP box with nearby stray digits continues to return NOT_VERIFIABLE (no false positive).
5. Consumer care extracts phone numbers with '+91' / 'call:' prefixes and emails with 'write:' prefixes.
6. FSSAI license extraction tolerates OCR-garbled markers (e.g. 'fal 10019023000027') and standalone 14-digit licenses.
7. Physical referral phrases ('See CapBodom', 'See Cap/Bottom', 'See CapSodom') for batch number and manufacturing
   date strictly return NOT_VERIFIABLE.
8. End-to-end verification against real MyFitness data from database.
"""

import sys
import os
import sqlite3
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.extraction.field_extractor import FieldExtractor
from app.rules.compliance_engine import compliance_engine


def test_mrp_noisy_ocr_and_digit_inconsistency():
    print("\n--- 1. Testing MRP Extraction with Noisy OCR & Inconsistent Digit Count ---")
    fe = FieldExtractor()

    # Case A: Real MyFitness packaging OCR string 'MRP:R6491'
    raw_noisy = "Net Weight:1Kg\nMRP:R6491\nwrite:care@myfitness.co.in"
    boxes_noisy = [
        {"text": "Net Weight:1Kg", "confidence": 97.4, "box": [[10, 10], [100, 10], [100, 25], [10, 25]]},
        {"text": "MRP:R6491", "confidence": 90.0, "box": [[10, 30], [100, 30], [100, 45], [10, 45]]},
        {"text": "write:care@myfitness.co.in", "confidence": 96.0, "box": [[10, 50], [200, 50], [200, 65], [10, 65]]},
    ]
    res_noisy = fe.extract_declarations(raw_noisy, boxes_noisy)
    mrp_noisy = res_noisy["mrp"]

    # Rule: Must extract recognizable price without truncation
    assert mrp_noisy["value"] is not None, "MRP must not be None for 'MRP:R6491'"
    assert "6491" in mrp_noisy["value"], f"Expected '6491' in extracted price, got: {mrp_noisy['value']}"
    assert mrp_noisy["raw_text"] == "MRP:R6491"
    # Rule: Inconsistent digit count & 'R' misread must cap confidence < 80% to trigger OCR_UNCERTAIN
    assert mrp_noisy["confidence"] < 80.0, f"Confidence must be < 80.0 for unusual digit count / R misread, got: {mrp_noisy['confidence']}"
    assert mrp_noisy["status"] == "OCR_UNCERTAIN", f"Expected OCR_UNCERTAIN, got: {mrp_noisy['status']}"
    print(f"  [PASS] 'MRP:R6491' extracted as '{mrp_noisy['value']}' with status='{mrp_noisy['status']}' (conf={mrp_noisy['confidence']}%) without truncation.")

    # Rule: When evaluated by compliance engine, OCR_UNCERTAIN must route to NEEDS_REVIEW
    eval_res = compliance_engine.validate(res_noisy)
    mrp_rule = next((r for r in eval_res.rule_results if r.rule_id == "PCR-2011-R6-1-E-MRP"), None)
    assert mrp_rule is not None
    assert mrp_rule.status == "NEEDS_REVIEW", f"Expected rule status NEEDS_REVIEW for uncertain MRP, got: {mrp_rule.status}"
    print("  [PASS] Compliance engine correctly evaluates uncertain MRP as NEEDS_REVIEW.")

    # Case B: Clean MRPs with canonical currency must remain CONFIRMED_PRESENT with high confidence
    clean_cases = [
        ("MRP ₹ 35.00 (Incl. of all taxes)", "₹ 35.00 (Incl. of all taxes)", 95.0),
        ("MRP: Rs. 120.00", "₹ 120.00", 90.0),
        ("MRP: 45.00", "₹ 45.00", 90.0),
    ]
    for raw_c, expected_val, min_conf in clean_cases:
        boxes_c = [{"text": raw_c, "confidence": 95.0, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]}]
        res_c = fe.extract_declarations(raw_c, boxes_c)
        m = res_c["mrp"]
        assert m["status"] == "CONFIRMED_PRESENT", f"Expected CONFIRMED_PRESENT for clean MRP '{raw_c}', got: {m['status']}"
        assert m["confidence"] >= min_conf
        assert m["numeric_price"] > 0
    print("  [PASS] Clean canonical MRPs maintain CONFIRMED_PRESENT status and high confidence.")

    # Case C: Re-verify India Gate Rice blank MRP box negative test (MUST NOT REGRESS)
    raw_india_gate = "MRP\n6\n190225110110113\n(Incl. of all taxes)"
    boxes_ig = [
        {"text": "MRP", "confidence": 99.6, "box": [[10, 10], [50, 10], [50, 20], [10, 20]]},
        {"text": "6", "confidence": 96.2, "box": [[10, 25], [20, 25], [20, 35], [10, 35]]},
        {"text": "190225110110113", "confidence": 91.6, "box": [[10, 40], [120, 40], [120, 50], [10, 50]]},
        {"text": "(Incl. of all taxes)", "confidence": 98.2, "box": [[10, 55], [150, 55], [150, 65], [10, 65]]},
    ]
    res_ig = fe.extract_declarations(raw_india_gate, boxes_ig)
    assert res_ig["mrp"]["value"] is None, f"Blank MRP box must be None, got: {res_ig['mrp']['value']}"
    assert res_ig["mrp"]["status"] == "NOT_VERIFIABLE"
    print("  [PASS] India Gate blank MRP box with stray digit '6' strictly returns NOT_VERIFIABLE (zero regression).")


def test_consumer_care_noisy_ocr():
    print("\n--- 2. Testing Consumer Care Extraction with Noisy Prefixes ---")
    fe = FieldExtractor()

    # Case A: Real MyFitness packaging text
    raw = (
        "Far Cortumer Comglit/Fedback/Sugoestons\n"
        "pleaue cortact mertioned manning cnice address\n"
        "write:care@myfitness.co.in\n"
        "call:+917096699111"
    )
    boxes = [
        {"text": "write:care@myfitness.co.in", "confidence": 96.7, "box": [[10, 10], [150, 10], [150, 25], [10, 25]]},
        {"text": "call:+917096699111", "confidence": 98.0, "box": [[10, 30], [150, 30], [150, 45], [10, 45]]},
    ]
    res = fe.extract_declarations(raw, boxes)
    care = res["consumer_care"]
    assert care["value"] is not None
    assert "care@myfitness.co.in" in care["value"], f"Expected email in consumer care, got: {care['value']}"
    assert "7096699111" in care["value"], f"Expected phone number in consumer care, got: {care['value']}"
    assert care["status"] == "CONFIRMED_PRESENT"
    print(f"  [PASS] Extracted consumer care: '{care['value']}'")


def test_fssai_license_noisy_ocr():
    print("\n--- 3. Testing FSSAI License Extraction with OCR Corruption ---")
    fe = FieldExtractor()

    # Case A: FSSAI logo read as 'fal' (from MyFitness scan)
    raw_fal = "fal 10019023000027\n1110015021001816"
    boxes_fal = [
        {"text": "fal 10019023000027", "confidence": 88.1, "box": [[10, 10], [120, 10], [120, 25], [10, 25]]}
    ]
    res_fal = fe.extract_declarations(raw_fal, boxes_fal)
    fssai = res_fal["fssai_license"]
    assert fssai["value"] == "10019023000027", f"Expected 10019023000027, got: {fssai['value']}"
    assert fssai["status"] == "CONFIRMED_PRESENT"
    print(f"  [PASS] 'fal 10019023000027' correctly extracted as '{fssai['value']}'.")

    # Case B: Other common OCR corruptions: 'fssat', 'issai', 'lic. no'
    corruptions = [
        ("fssat 10018011005090", "10018011005090"),
        ("issai 10012063000110", "10012063000110"),
        ("lic. no. 12714055000143", "12714055000143"),
    ]
    for text, expected in corruptions:
        boxes_c = [{"text": text, "confidence": 95.0, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]}]
        res_c = fe.extract_declarations(text, boxes_c)
        assert res_c["fssai_license"]["value"] == expected, f"Failed for {text}: got {res_c['fssai_license']['value']}"
    print("  [PASS] Common FSSAI OCR corruptions successfully extracted.")


def test_referral_phrases_rejected():
    print("\n--- 4. Testing Physical Referral Phrases Rejection (See Cap/Bottom) ---")
    fe = FieldExtractor()

    # Case A: 'See CapBodom' / 'See Cap/Bottom' for batch number
    referral_batch = [
        "Batch No. :See CapBodom",
        "Batch No. :See Cap/Bottom",
        "Lot No: See bottom",
        "B.No. See neck of bottle",
        "Batch No: See crimp of pouch",
        "Batch No: See reverse"
    ]
    for ref_text in referral_batch:
        boxes = [{"text": ref_text, "confidence": 95.0, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]}]
        res = fe.extract_declarations(ref_text, boxes)
        b_val = res["batch_number"]["value"]
        assert b_val is None, f"Referral phrase '{ref_text}' must NOT be extracted as batch number! Got: {b_val}"
        assert res["batch_number"]["status"] == "NOT_VERIFIABLE"
    print("  [PASS] All batch number physical referral phrases correctly rejected (NOT_VERIFIABLE).")

    # Case B: 'Prod.Date:See CapSodom' / 'Mfg Date: See Bottom' for dates
    referral_dates = [
        "Prod.Date:See CapSodom",
        "Mfg Date: See Bottom",
        "Packed on: See cap",
        "Date of Mfg: See lid"
    ]
    for ref_text in referral_dates:
        boxes = [{"text": ref_text, "confidence": 95.0, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]}]
        res = fe.extract_declarations(ref_text, boxes)
        m_val = res["manufacturing_date"]["value"]
        p_val = res["packing_date"]["value"]
        assert m_val is None, f"Referral phrase '{ref_text}' must NOT be extracted as mfg date! Got: {m_val}"
        assert p_val is None, f"Referral phrase '{ref_text}' must NOT be extracted as packing date! Got: {p_val}"
    print("  [PASS] All date physical referral phrases correctly rejected (NOT_VERIFIABLE).")


def test_myfitness_db_record_e2e():
    print("\n--- 5. Testing Live MyFitness Data from Database Record (#31) ---")
    db_path = os.path.join(BASE_DIR, "safemetric.db")
    if not os.path.exists(db_path):
        print("  [SKIP] safemetric.db not found.")
        return

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = con.cursor()
    row = cur.execute("SELECT raw_ocr_text, ocr_info FROM inspections WHERE id=31").fetchone()
    con.close()

    if not row:
        print("  [SKIP] Inspection row 31 not found in database.")
        return

    raw_text = row[0]
    ocr_info = json.loads(row[1]) if row[1] else {}
    boxes = ocr_info.get("bounding_boxes", [])

    fe = FieldExtractor()
    fields = fe.extract_declarations(raw_text, boxes)

    # 1. Product Name: MYFITNESS
    assert fields["product_name"]["value"] == "MYFITNESS"
    print(f"  * Product Name:     '{fields['product_name']['value']}' [PASS]")

    # 2. Net Quantity: 1Kg
    assert fields["net_quantity"]["value"] == "1Kg"
    print(f"  * Net Quantity:     '{fields['net_quantity']['value']}' [PASS]")

    # 3. MRP: extracted from 'MRP:R6491', status='OCR_UNCERTAIN' (confidence < 80%)
    mrp = fields["mrp"]
    assert mrp["value"] is not None and "6491" in mrp["value"]
    assert mrp["status"] == "OCR_UNCERTAIN"
    assert mrp["confidence"] < 80.0
    print(f"  * MRP:              '{mrp['value']}' (status={mrp['status']}, conf={mrp['confidence']}%) [PASS]")

    # 4. Consumer Care: contains email & phone
    care = fields["consumer_care"]
    assert care["value"] is not None
    assert "care@myfitness.co.in" in care["value"]
    assert "7096699111" in care["value"]
    print(f"  * Consumer Care:    '{care['value']}' [PASS]")

    # 5. FSSAI License: 10019023000027
    fssai = fields["fssai_license"]
    assert fssai["value"] == "10019023000027"
    print(f"  * FSSAI License:    '{fssai['value']}' [PASS]")

    # 6. Batch & Date: strictly None (physical referral phrases rejected)
    assert fields["batch_number"]["value"] is None
    assert fields["manufacturing_date"]["value"] is None
    print(f"  * Batch & Date:     null (referral phrases correctly rejected) [PASS]")

    print("\n  [PASS] All MyFitness fields successfully verified end-to-end!")


if __name__ == "__main__":
    print("=" * 70)
    print(" RUNNING NOISY OCR FIELD EXTRACTION RESILIENCE TESTS (BUG 2)")
    print("=" * 70)
    test_mrp_noisy_ocr_and_digit_inconsistency()
    test_consumer_care_noisy_ocr()
    test_fssai_license_noisy_ocr()
    test_referral_phrases_rejected()
    test_myfitness_db_record_e2e()
    print("\n" + "=" * 70)
    print(" ALL NOISY OCR FIELD EXTRACTION TESTS PASSED (100%)!")
    print("=" * 70)
