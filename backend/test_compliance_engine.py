import os
import sys

# Configure UTF-8 stdout for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.rules.compliance_engine import (
    compliance_engine,
    ComplianceEngine,
    RuleValidationResult,
    ComplianceEvaluation
)
from app.ocr.ocr_service import ocr_service
from app.extraction.field_extractor import field_extractor


def test_compliance_engine_contract_and_schema():
    """
    Verifies that every rule validation result adheres strictly to the required schema:
    - rule_id
    - legal_reference
    - status in {PASS, FAIL, NEEDS_REVIEW, NOT_APPLICABLE}
    - explanation
    - detected_value
    - expected_requirement
    - evidence_reference
    """
    print("\n--- 1. Testing Compliance Engine Contract & Schema Output ---")
    evaluation = compliance_engine.validate({})

    assert isinstance(evaluation, ComplianceEvaluation)
    assert len(evaluation.rule_results) >= 19, f"Expected at least 19 rules evaluated, got {len(evaluation.rule_results)}"
    assert evaluation.total_rules_evaluated >= 19

    valid_statuses = {"PASS", "FAIL", "NEEDS_REVIEW", "NOT_APPLICABLE"}

    for res in evaluation.rule_results:
        assert isinstance(res, RuleValidationResult)
        assert res.rule_id, "Rule ID missing"
        assert res.legal_reference, f"Legal reference missing for {res.rule_id}"
        assert res.status in valid_statuses, f"Invalid status '{res.status}' in {res.rule_id}"
        assert res.explanation and len(res.explanation) > 5, f"Explanation insufficient for {res.rule_id}"
        assert res.expected_requirement and len(res.expected_requirement) > 5, f"Expected requirement missing for {res.rule_id}"
        assert isinstance(res.evidence_reference, dict), f"Evidence reference must be a dict for {res.rule_id}"

    # Verify to_dict serialization
    d = evaluation.to_dict()
    assert "compliance_status" in d
    assert "compliance_score" in d
    assert "rule_results" in d
    assert "violations" in d
    assert len(d["rule_results"]) >= 19
    print(f"  [PASS] Engine output strictly conforms to the statutory 7-field schema across all {len(d['rule_results'])} rules.")


def test_status_coverage_all_four_verdicts():
    """
    Verifies that the engine can produce all four statutory statuses:
    PASS, FAIL, NEEDS_REVIEW, NOT_APPLICABLE.
    """
    print("\n--- 2. Testing All Four Statutory Verdicts (PASS, FAIL, NEEDS_REVIEW, NOT_APPLICABLE) ---")

    # Construct test sample with diverse statuses:
    mock_data = {
        "product_name": {"value": "SafeRice Basmati", "raw_text": "SafeRice Basmati", "confidence": 95.0, "bounding_box": [[10, 10], [50, 10], [50, 20], [10, 20]]},
        "generic_name": {"value": "Basmati Rice", "raw_text": "Basmati Rice", "confidence": 95.0, "bounding_box": None},
        "manufacturer": {"value": "Safe Foods Ltd", "raw_text": "Mfd By: Safe Foods Ltd", "confidence": 95.0, "bounding_box": None},
        "address": {"value": "Plot 42, Industrial Area, Sector 5, New Delhi 110001", "raw_text": "Plot 42, Ind Area, Delhi 110001", "confidence": 92.0, "bounding_box": None},
        "net_quantity": {"value": "500 g", "numeric_value": 500.0, "unit": "g", "raw_text": "Net Weight: 500 g", "confidence": 95.0, "bounding_box": None},
        "mrp": {"value": "Rs. 120.00", "raw_text": "MRP Rs. 120.00 (incl. of all taxes)", "confidence": 94.0, "bounding_box": None, "has_currency": True, "has_tax": True},
        "unit_sale_price": {"value": "Rs. 0.24 / g", "raw_text": "USP Rs. 0.24 / g", "confidence": 92.0, "bounding_box": None},
        "manufacturing_date": {"value": "08/2026", "raw_text": "Mfg: 08/2026", "confidence": 95.0, "bounding_box": None},
        "consumer_care": {"value": "Call 1800-11-2233 or care@safefoods.com", "raw_text": "Care: 1800-11-2233", "confidence": 95.0, "bounding_box": None},
        "country_of_origin": {"value": "India", "raw_text": "Country of Origin: India", "confidence": 95.0, "bounding_box": None}
    }

    evaluation = compliance_engine.validate(mock_data)

    statuses_found = {r.status for r in evaluation.rule_results}
    print(f"  Detected statuses in evaluated sample: {statuses_found}")

    assert "PASS" in statuses_found, "PASS status missing"
    assert "NOT_APPLICABLE" in statuses_found, "NOT_APPLICABLE status missing (e.g. Third Schedule or Physical Advisory)"

    # Now verify FAIL status using invalid declarations:
    fail_data = {
        "product_name": {"value": "Crunchy Chips", "confidence": 95.0},
        "net_quantity": {"value": "Approx 100g", "raw_text": "Approx 100g", "confidence": 95.0},  # Banned qualifier
        "mrp": {"value": "100.00", "raw_text": "100.00", "confidence": 95.0},  # Missing currency and taxes clause
    }
    eval_fail = compliance_engine.validate(fail_data)
    fail_statuses = {r.status for r in eval_fail.rule_results}
    assert "FAIL" in fail_statuses, "FAIL status missing"

    # Now verify NEEDS_REVIEW status using low confidence:
    review_data = {
        "product_name": {"value": "Crunchy Chips", "confidence": 95.0},
        "net_quantity": {"value": "100 g", "raw_text": "100 g", "confidence": 62.0},  # Low confidence < 80%
    }
    eval_review = compliance_engine.validate(review_data)
    review_statuses = {r.status for r in eval_review.rule_results}
    assert "NEEDS_REVIEW" in review_statuses, "NEEDS_REVIEW status missing"

    print("  [PASS] All four statutory statuses verified (PASS, FAIL, NEEDS_REVIEW, NOT_APPLICABLE).")


def test_ocr_uncertainty_is_never_treated_as_violation():
    """
    CRITICAL STATUTORY REQUIREMENT:
    Optical recognition uncertainty (<80% confidence or 'Low Confidence' status)
    must strictly route to NEEDS_REVIEW, NEVER FAIL.
    """
    print("\n--- 3. Testing OCR Uncertainty Handling (<80% -> NEEDS_REVIEW, NOT FAIL) ---")

    # Case A: Net quantity with 65% OCR confidence
    data_low_qty = {
        "product_name": {"value": "Lay's Chips", "confidence": 95.0},
        "net_quantity": {"value": "50 g", "raw_text": "50 g", "confidence": 65.0, "status": "Low Confidence"},
        "mrp": {"value": "Rs. 20.00", "raw_text": "Rs. 20.00 incl. of all taxes", "confidence": 95.0, "has_currency": True, "has_tax": True}
    }
    eval_a = compliance_engine.validate(data_low_qty)
    qty_rule = next(r for r in eval_a.rule_results if r.rule_id == "PCR-2011-R6-1-C-NET-QUANTITY")
    assert qty_rule.status == "NEEDS_REVIEW", f"Expected NEEDS_REVIEW for low confidence quantity, got {qty_rule.status}"
    assert qty_rule.status != "FAIL", "OCR uncertainty was incorrectly treated as a violation!"
    assert "65.0%" in qty_rule.explanation

    # Case B: MRP with 72% OCR confidence
    data_low_mrp = {
        "product_name": {"value": "Lay's Chips", "confidence": 95.0},
        "net_quantity": {"value": "50 g", "raw_text": "50 g", "confidence": 95.0},
        "mrp": {"value": "Rs. 20.00", "raw_text": "Rs. 20.00 incl. of all taxes", "confidence": 72.0, "has_currency": True, "has_tax": True}
    }
    eval_b = compliance_engine.validate(data_low_mrp)
    mrp_rule = next(r for r in eval_b.rule_results if r.rule_id == "PCR-2011-R6-1-E-MRP")
    assert mrp_rule.status == "NEEDS_REVIEW", f"Expected NEEDS_REVIEW for low confidence MRP, got {mrp_rule.status}"
    assert mrp_rule.status != "FAIL", "OCR uncertainty on MRP was incorrectly treated as FAIL!"

    # Case C: Manufacturer name with 55% confidence
    data_low_mfg = {
        "manufacturer": {"value": "PepsiCo India", "raw_text": "Mfd By PepsiCo", "confidence": 55.0}
    }
    eval_c = compliance_engine.validate(data_low_mfg)
    mfg_rule = next(r for r in eval_c.rule_results if r.rule_id == "PCR-2011-R6-1-A-MFG-NAME")
    assert mfg_rule.status == "NEEDS_REVIEW"
    assert mfg_rule.status != "FAIL"

    # Case D: Overall package legibility with low optical contrast (<80%)
    data_low_contrast = {
        "product_name": {"value": "Test Product", "confidence": 60.0},
        "net_quantity": {"value": "100 g", "confidence": 62.0},
        "mrp": {"value": "Rs. 50", "confidence": 58.0}
    }
    eval_d = compliance_engine.validate(data_low_contrast)
    leg_rule = next(r for r in eval_d.rule_results if r.rule_id == "PCR-2011-R9-LEGIBILITY-CONTRAST-LANG")
    assert leg_rule.status == "NEEDS_REVIEW"
    assert "contrast" in leg_rule.explanation.lower()

    print("  [PASS] Optical uncertainty strictly routes to NEEDS_REVIEW across all rules. No false violations generated.")


def test_missing_values_are_not_invented():
    """
    CRITICAL NO-HALLUCINATION REQUIREMENT:
    Missing values must remain None/null. Missing mandatory declarations must
    fail deterministically without fabricating placeholder values.
    """
    print("\n--- 4. Testing Strict Null Handling & No Hallucination ---")

    empty_data = {
        "product_name": {"value": None, "confidence": 0.0, "raw_text": None, "bounding_box": None},
        "mrp": {"value": None, "confidence": 0.0, "raw_text": None, "bounding_box": None},
        "net_quantity": {"value": None, "confidence": 0.0, "raw_text": None, "bounding_box": None},
        "consumer_care": {"value": None, "confidence": 0.0, "raw_text": None, "bounding_box": None}
    }

    eval_empty = compliance_engine.validate(empty_data)

    mrp_res = next(r for r in eval_empty.rule_results if r.rule_id == "PCR-2011-R6-1-E-MRP")
    assert mrp_res.status == "FAIL"
    assert mrp_res.detected_value is None, f"Detected value must be None, got {mrp_res.detected_value}"
    assert "missing" in mrp_res.explanation.lower()

    qty_res = next(r for r in eval_empty.rule_results if r.rule_id == "PCR-2011-R6-1-C-NET-QUANTITY")
    assert qty_res.status == "FAIL"
    assert qty_res.detected_value is None

    care_res = next(r for r in eval_empty.rule_results if r.rule_id == "PCR-2011-R6-2-CONSUMER-CARE")
    assert care_res.status == "FAIL"
    assert care_res.detected_value is None

    # For dependent rules (qualifiers and units), missing net_quantity must be NOT_APPLICABLE
    qual_res = next(r for r in eval_empty.rule_results if r.rule_id == "PCR-2011-R12-6-PROHIBITED-QUALIFIERS")
    assert qual_res.status == "NOT_APPLICABLE"
    assert qual_res.detected_value is None

    print("  [PASS] Missing values strictly preserved as None. No hallucination detected.")


def test_prohibited_qualifiers_rule_12_6():
    """
    Rule 12(6): Prohibits ambiguous qualifiers ('approx', 'about', 'minimum', 'average').
    """
    print("\n--- 5. Testing Rule 12(6): Prohibited Qualifiers ---")

    banned_samples = [
        "Approx 200g",
        "about 100g",
        "minimum 500g",
        "not less than 250g",
        "average 100g"
    ]

    for sample in banned_samples:
        data = {
            "product_name": {"value": "Snack Food", "confidence": 95.0},
            "net_quantity": {"value": sample, "raw_text": sample, "confidence": 95.0}
        }
        res = compliance_engine.validate(data)
        rule_res = next(r for r in res.rule_results if r.rule_id == "PCR-2011-R12-6-PROHIBITED-QUALIFIERS")
        assert rule_res.status == "FAIL", f"Expected FAIL for '{sample}', got {rule_res.status}"
        assert "prohibited" in rule_res.explanation.lower()

    # Compliant sample
    compliant_data = {
        "product_name": {"value": "Snack Food", "confidence": 95.0},
        "net_quantity": {"value": "200 g", "raw_text": "Net Qty: 200 g", "confidence": 95.0}
    }
    comp_res = compliance_engine.validate(compliant_data)
    comp_rule = next(r for r in comp_res.rule_results if r.rule_id == "PCR-2011-R12-6-PROHIBITED-QUALIFIERS")
    assert comp_rule.status == "PASS"

    print("  [PASS] Rule 12(6) strictly catches all banned qualifiers ('approx', 'about', etc.).")


def test_units_and_symbols_rule_13():
    """
    Rule 13: Measurement units must conform to SI standards. Collective counts (dozen, gross) prohibited.
    """
    print("\n--- 6. Testing Rule 13: Units and Symbology Standards ---")

    # Non-metric collective count: 1 Dozen
    banned_data = {
        "product_name": {"value": "Bakery Muffins", "confidence": 95.0},
        "net_quantity": {"value": "1 Dozen", "raw_text": "Contents: 1 Dozen", "confidence": 95.0}
    }
    eval_banned = compliance_engine.validate(banned_data)
    rule_res = next(r for r in eval_banned.rule_results if r.rule_id == "PCR-2011-R13-UNITS-SYMBOLS")
    assert rule_res.status == "FAIL"
    assert "non-metric collective count" in rule_res.explanation.lower()

    # Valid metric units: 500 g
    metric_data = {
        "product_name": {"value": "Atta", "confidence": 95.0},
        "net_quantity": {"value": "500 g", "raw_text": "Net Weight: 500 g", "confidence": 95.0}
    }
    eval_metric = compliance_engine.validate(metric_data)
    rule_metric = next(r for r in eval_metric.rule_results if r.rule_id == "PCR-2011-R13-UNITS-SYMBOLS")
    assert rule_metric.status == "PASS"

    print("  [PASS] Rule 13 correctly validates SI units and rejects collective non-metric counts.")


def test_second_schedule_standard_pack_sizes():
    """
    Rule 5 & Second Schedule: Standard pack sizes for scheduled commodities (Rice, Atta, Biscuits, Soap, Oil).
    """
    print("\n--- 7. Testing Rule 5: Second Schedule Standard Packaging Quantities ---")

    # Case A: Scheduled commodity (Basmati Rice) in non-standard pack size without disclaimer -> FAIL
    rice_non_standard = {
        "product_name": {"value": "Royal Basmati Rice", "confidence": 95.0},
        "generic_name": {"value": "Rice", "confidence": 95.0},
        "net_quantity": {"value": "340 g", "raw_text": "Net Qty: 340 g", "confidence": 95.0}
    }
    eval_ns = compliance_engine.validate(rice_non_standard)
    sched2_res = next(r for r in eval_ns.rule_results if r.rule_id == "PCR-2011-R5-SECOND-SCHEDULE")
    assert sched2_res.status == "FAIL"
    assert "non-standard pack size" in sched2_res.explanation.lower()

    # Case B: Scheduled commodity (Basmati Rice) in standard pack size 500 g -> PASS
    rice_standard = {
        "product_name": {"value": "Royal Basmati Rice", "confidence": 95.0},
        "generic_name": {"value": "Rice", "confidence": 95.0},
        "net_quantity": {"value": "500 g", "raw_text": "Net Qty: 500 g", "confidence": 95.0}
    }
    eval_s = compliance_engine.validate(rice_standard)
    sched2_s = next(r for r in eval_s.rule_results if r.rule_id == "PCR-2011-R5-SECOND-SCHEDULE")
    assert sched2_s.status == "PASS"

    # Case C: Scheduled commodity in non-standard pack size WITH mandatory statutory disclaimer -> PASS
    rice_with_disclaimer = {
        "product_name": {"value": "Royal Basmati Rice", "confidence": 95.0},
        "generic_name": {"value": "Rice", "confidence": 95.0},
        "net_quantity": {"value": "340 g", "raw_text": "Net Qty: 340 g - Not a standard pack size under Legal Metrology Rules", "confidence": 95.0}
    }
    eval_disc = compliance_engine.validate(rice_with_disclaimer)
    sched2_disc = next(r for r in eval_disc.rule_results if r.rule_id == "PCR-2011-R5-SECOND-SCHEDULE")
    assert sched2_disc.status == "PASS"
    assert "statutory disclaimer" in sched2_disc.explanation.lower()

    # Case D: Non-scheduled commodity (Potato Chips) -> NOT_APPLICABLE
    chips_data = {
        "product_name": {"value": "Lay's Potato Chips", "confidence": 95.0},
        "generic_name": {"value": "Potato Chips", "confidence": 95.0},
        "net_quantity": {"value": "48 g", "raw_text": "Net Qty: 48 g", "confidence": 95.0}
    }
    eval_chips = compliance_engine.validate(chips_data)
    sched2_chips = next(r for r in eval_chips.rule_results if r.rule_id == "PCR-2011-R5-SECOND-SCHEDULE")
    assert sched2_chips.status == "NOT_APPLICABLE"

    print("  [PASS] Second Schedule logic verified for standard, non-standard, and disclaimed packages.")


def test_third_schedule_when_packed_exemption():
    """
    Rule 11(4) & Third Schedule: 'When Packed' qualification strictly limited to soaps, lotions, creams.
    """
    print("\n--- 8. Testing Third Schedule: 'When Packed' Exemption ---")

    # Case A: Toilet Soap with 'when packed' -> PASS
    soap_data = {
        "product_name": {"value": "Luxury Bathing Soap", "confidence": 95.0},
        "generic_name": {"value": "Toilet Soap", "confidence": 95.0},
        "net_quantity": {"value": "125 g when packed", "raw_text": "Net Wt: 125 g when packed", "confidence": 95.0}
    }
    eval_soap = compliance_engine.validate(soap_data)
    sched3_soap = next(r for r in eval_soap.rule_results if r.rule_id == "PCR-2011-THIRD-SCHEDULE-WHEN-PACKED")
    assert sched3_soap.status == "PASS"

    # Case B: Potato Chips with 'when packed' -> FAIL
    chips_when_packed = {
        "product_name": {"value": "Crispy Chips", "confidence": 95.0},
        "generic_name": {"value": "Potato Chips", "confidence": 95.0},
        "net_quantity": {"value": "50 g when packed", "raw_text": "Net Wt: 50 g when packed", "confidence": 95.0}
    }
    eval_chips = compliance_engine.validate(chips_when_packed)
    sched3_chips = next(r for r in eval_chips.rule_results if r.rule_id == "PCR-2011-THIRD-SCHEDULE-WHEN-PACKED")
    assert sched3_chips.status == "FAIL"
    assert "restricted to soaps, lotions, and creams" in sched3_chips.explanation.lower()

    # Case C: Product without 'when packed' -> NOT_APPLICABLE
    normal_data = {
        "product_name": {"value": "Bathing Soap", "confidence": 95.0},
        "net_quantity": {"value": "125 g", "raw_text": "Net Wt: 125 g", "confidence": 95.0}
    }
    eval_norm = compliance_engine.validate(normal_data)
    sched3_norm = next(r for r in eval_norm.rule_results if r.rule_id == "PCR-2011-THIRD-SCHEDULE-WHEN-PACKED")
    assert sched3_norm.status == "NOT_APPLICABLE"

    print("  [PASS] Third Schedule strictly restricts 'when packed' to statutory commodities.")


def test_de_minimis_statutory_exemptions_rule_26():
    """
    Rule 26(a): Small packages containing 10g / 10ml or less are statutorily exempt.
    """
    print("\n--- 9. Testing Rule 26: De-Minimis Package Exemptions ---")

    # Case A: Small package <= 10g -> PASS under exemption
    small_pkg = {
        "product_name": {"value": "Hotel Shampoo Sachet", "confidence": 95.0},
        "net_quantity": {"value": "6 ml", "numeric_value": 6.0, "unit": "ml", "confidence": 95.0}
    }
    eval_small = compliance_engine.validate(small_pkg)
    ex_rule = next(r for r in eval_small.rule_results if r.rule_id == "PCR-2011-R26-STATUTORY-EXEMPTIONS")
    assert ex_rule.status == "PASS"
    assert "de-minimis exemption" in ex_rule.explanation.lower()

    # Case B: Standard 100g package -> NOT_APPLICABLE
    std_pkg = {
        "product_name": {"value": "Biscuits", "confidence": 95.0},
        "net_quantity": {"value": "100 g", "numeric_value": 100.0, "unit": "g", "confidence": 95.0}
    }
    eval_std = compliance_engine.validate(std_pkg)
    ex_std = next(r for r in eval_std.rule_results if r.rule_id == "PCR-2011-R26-STATUTORY-EXEMPTIONS")
    assert ex_std.status == "NOT_APPLICABLE"

    print("  [PASS] Rule 26 de-minimis package exemptions verified.")


def test_real_lays_image_compliance_evaluation():
    """
    Tests compliance evaluation on actual extracted declarations from the Lay's package image.
    Net Quantity and Manufacturing Date should now be NEEDS_REVIEW (not FAIL)
    because the Lay's rear image shows other core declarations, indicating
    partial surface capture.
    """
    print("\n--- 10. Testing Full Pipeline on Real Lay's Product Declarations ---")

    lays_path = r"C:\Users\doram\Downloads\lays.jpg"
    if not os.path.exists(lays_path):
        lays_path = os.path.join(BASE_DIR, "demo_samples", "lays.jpg")
    assert os.path.exists(lays_path), f"Lay's image missing at {lays_path}!"

    ocr_result = ocr_service.process_image(lays_path, is_demo=False)
    raw_text = ocr_result.get("raw_text", "")
    boxes = ocr_result.get("bounding_boxes", [])

    fields = field_extractor.extract_declarations(raw_text, boxes)
    assert len(fields) > 0

    evaluation = compliance_engine.validate(fields)

    assert isinstance(evaluation, ComplianceEvaluation)
    assert evaluation.total_rules_evaluated >= 19
    assert evaluation.compliance_score >= 0.0

    print(f"  Lay's Package Overall Compliance Status: {evaluation.compliance_status}")
    print(f"  Lay's Compliance Score:                  {evaluation.compliance_score}%")
    print(f"  Rules Passed:                            {evaluation.passed_count}")
    print(f"  Rules Failed:                            {evaluation.failed_count}")
    print(f"  Rules Needing Review:                    {evaluation.needs_review_count}")
    print(f"  Rules Not Applicable:                    {evaluation.not_applicable_count}")

    # Inspect individual rule outcomes
    for r in evaluation.rule_results:
        print(f"    [{r.status:14s}] {r.rule_id:38s} | Det: {str(r.detected_value)[:30]}")

    # Section 18 Core Declarations check
    r_sec18 = next(r for r in evaluation.rule_results if r.rule_id == "LMA-2009-SEC-18-MANDATORY")
    assert r_sec18.status == "PASS"

    # Net Quantity: should now be NEEDS_REVIEW (partial surface capture)
    r_net_qty = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R6-1-C-NET-QUANTITY")
    assert r_net_qty.status in ("PASS", "NEEDS_REVIEW"), (
        f"Expected PASS or NEEDS_REVIEW for net quantity on partial image, got {r_net_qty.status}"
    )

    # Manufacturing Date: should now be NEEDS_REVIEW (partial surface capture)
    r_date = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R6-1-D-DATE")
    assert r_date.status in ("PASS", "NEEDS_REVIEW"), (
        f"Expected PASS or NEEDS_REVIEW for mfg date on partial image, got {r_date.status}"
    )

    # No HIGH/CRITICAL FAIL should remain → status should NOT be NON-COMPLIANT
    # unless there are other genuine violations
    print(f"\n  Net Quantity Rule:       {r_net_qty.status}")
    print(f"  Manufacturing Date Rule: {r_date.status}")

    # Rule 12(6) Prohibited Qualifiers check (PASS if net quantity present and clean, NOT_APPLICABLE if net quantity absent)
    r_qual = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R12-6-PROHIBITED-QUALIFIERS")
    assert r_qual.status in ("PASS", "NOT_APPLICABLE")

    # Legibility check
    r_leg = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R9-LEGIBILITY-CONTRAST-LANG")
    assert r_leg.status in ("PASS", "NEEDS_REVIEW")

    print("\n  [PASS] Real Lay's packaging compliance evaluation completed successfully.")


def test_detection_state_a_clearly_present_passes():
    """
    Detection State A: DECLARATION_CONFIRMED_PRESENT
    When OCR successfully detects the declaration → PASS.
    """
    print("\n--- 11. Testing Detection State A: Clearly Present → PASS ---")

    data = {
        "product_name": {"value": "Lay's Classic", "confidence": 95.0, "raw_text": "Lay's Classic"},
        "manufacturer": {"value": "PepsiCo India", "confidence": 94.0, "raw_text": "Mfg By: PepsiCo"},
        "net_quantity": {"value": "52 g", "raw_text": "Net Qty: 52 g", "confidence": 93.0},
        "mrp": {"value": "Rs. 20.00", "raw_text": "MRP Rs. 20.00 (incl. taxes)", "confidence": 95.0, "has_currency": True, "has_tax": True},
        "manufacturing_date": {"value": "07/2026", "raw_text": "Mfg: 07/2026", "confidence": 92.0},
        "consumer_care": {"value": "1800-11-2233", "raw_text": "Care: 1800-11-2233", "confidence": 95.0},
    }

    evaluation = compliance_engine.validate(data)

    r_qty = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R6-1-C-NET-QUANTITY")
    assert r_qty.status == "PASS", f"Expected PASS for clearly detected net quantity, got {r_qty.status}"

    r_date = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R6-1-D-DATE")
    assert r_date.status == "PASS", f"Expected PASS for clearly detected mfg date, got {r_date.status}"

    print("  [PASS] Clearly present declarations correctly produce PASS.")


def test_detection_state_b_outside_captured_surface_needs_review():
    """
    Detection State B: DECLARATION_NOT_VERIFIABLE
    When OCR detects substantial OTHER core declarations but a specific
    field is absent (likely on another package surface) → NEEDS_REVIEW.
    """
    print("\n--- 12. Testing Detection State B: Outside Captured Surface → NEEDS_REVIEW ---")

    # Simulates Lay's rear image: product_name, manufacturer, mrp, consumer_care detected,
    # but net_quantity and manufacturing_date are absent (likely on front/side/seal)
    data = {
        "product_name": {"value": "Lay's Classic Salted", "confidence": 95.0, "raw_text": "Lay's Classic Salted"},
        "manufacturer": {"value": "PepsiCo India Holdings Pvt Ltd", "confidence": 94.0, "raw_text": "Mfg By PepsiCo"},
        "address": {"value": "Plot 42, Sector 5, New Delhi", "confidence": 92.0, "raw_text": "Plot 42, Delhi"},
        "mrp": {"value": "₹20.00", "raw_text": "MRP ₹20.00 (incl. of all taxes)", "confidence": 95.0, "has_currency": True, "has_tax": True},
        "consumer_care": {"value": "1800-11-2233", "raw_text": "Consumer Care: 1800-11-2233", "confidence": 95.0},
        "country_of_origin": {"value": "India", "raw_text": "Country of Origin: India", "confidence": 95.0},
        # net_quantity: NOT present in this image
        # manufacturing_date: NOT present in this image
    }

    evaluation = compliance_engine.validate(data)

    r_qty = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R6-1-C-NET-QUANTITY")
    assert r_qty.status == "NEEDS_REVIEW", (
        f"Expected NEEDS_REVIEW for net quantity when other core fields are detected, got {r_qty.status}"
    )
    assert "partial surface capture" in r_qty.explanation.lower() or "unable to verify" in r_qty.explanation.lower(), (
        f"Explanation should mention partial surface capture: {r_qty.explanation}"
    )

    r_date = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R6-1-D-DATE")
    assert r_date.status == "NEEDS_REVIEW", (
        f"Expected NEEDS_REVIEW for mfg date when other core fields are detected, got {r_date.status}"
    )
    assert "partial surface capture" in r_date.explanation.lower() or "unable to verify" in r_date.explanation.lower(), (
        f"Explanation should mention partial surface capture: {r_date.explanation}"
    )

    print(f"  Net Quantity:       {r_qty.status} — {r_qty.explanation[:80]}...")
    print(f"  Manufacturing Date: {r_date.status} — {r_date.explanation[:80]}...")
    print("  [PASS] Missing declarations on partial surface correctly produce NEEDS_REVIEW.")


def test_detection_state_c_low_ocr_confidence_needs_review():
    """
    Detection State C: OCR_UNCERTAIN
    When OCR detects relevant text but with low confidence → NEEDS_REVIEW.
    """
    print("\n--- 13. Testing Detection State C: Low OCR Confidence → NEEDS_REVIEW ---")

    data = {
        "product_name": {"value": "Test Product", "confidence": 95.0},
        "manufacturer": {"value": "Test Corp", "confidence": 94.0},
        "net_quantity": {"value": "100 g", "raw_text": "100 g", "confidence": 55.0},  # Low confidence
        "mrp": {"value": "Rs. 50.00", "raw_text": "MRP Rs. 50.00", "confidence": 95.0, "has_currency": True, "has_tax": True},
        "manufacturing_date": {"value": "06/2026", "raw_text": "Mfg: 06/2026", "confidence": 45.0},  # Low confidence
        "consumer_care": {"value": "1800-000-111", "confidence": 95.0},
    }

    evaluation = compliance_engine.validate(data)

    r_qty = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R6-1-C-NET-QUANTITY")
    assert r_qty.status == "NEEDS_REVIEW", f"Expected NEEDS_REVIEW for low confidence net quantity, got {r_qty.status}"
    assert "55.0%" in r_qty.explanation

    r_date = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R6-1-D-DATE")
    assert r_date.status == "NEEDS_REVIEW", f"Expected NEEDS_REVIEW for low confidence mfg date, got {r_date.status}"
    assert "45.0%" in r_date.explanation

    print(f"  Net Quantity:       {r_qty.status} (55.0% confidence)")
    print(f"  Manufacturing Date: {r_date.status} (45.0% confidence)")
    print("  [PASS] Low OCR confidence correctly produces NEEDS_REVIEW.")


def test_detection_state_d_clearly_absent_fails():
    """
    Detection State D: DECLARATION_CONFIRMED_ABSENT
    When the package shows NO other core declarations (0-1 core fields),
    the package may genuinely lack the declaration → FAIL.
    """
    print("\n--- 14. Testing Detection State D: Clearly Absent → FAIL ---")

    # Only product_name is present — not enough evidence that the image
    # shows substantial label content. Missing fields are likely genuinely absent.
    data = {
        "product_name": {"value": "Unlabeled Product", "confidence": 90.0, "raw_text": "Unlabeled Product"},
        # No manufacturer, no mrp, no consumer_care, no net_quantity, no mfg date
    }

    evaluation = compliance_engine.validate(data)

    r_qty = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R6-1-C-NET-QUANTITY")
    assert r_qty.status == "FAIL", (
        f"Expected FAIL for net quantity when no other core fields detected, got {r_qty.status}"
    )

    r_date = next(r for r in evaluation.rule_results if r.rule_id == "PCR-2011-R6-1-D-DATE")
    assert r_date.status == "FAIL", (
        f"Expected FAIL for mfg date when no other core fields detected, got {r_date.status}"
    )

    # Also verify the empty package case from test 4 still works
    empty_data = {
        "product_name": {"value": None, "confidence": 0.0, "raw_text": None, "bounding_box": None},
        "mrp": {"value": None, "confidence": 0.0, "raw_text": None, "bounding_box": None},
        "net_quantity": {"value": None, "confidence": 0.0, "raw_text": None, "bounding_box": None},
        "consumer_care": {"value": None, "confidence": 0.0, "raw_text": None, "bounding_box": None}
    }

    eval_empty = compliance_engine.validate(empty_data)
    qty_res = next(r for r in eval_empty.rule_results if r.rule_id == "PCR-2011-R6-1-C-NET-QUANTITY")
    assert qty_res.status == "FAIL", f"Expected FAIL for completely empty package, got {qty_res.status}"

    print("  [PASS] Genuinely absent declarations (no other core fields) correctly produce FAIL.")


if __name__ == "__main__":
    print("=" * 75)
    print(" EXECUTING SAFEMETRIC COMPLIANCE-VALIDATION ENGINE TEST SUITE")
    print("=" * 75)
    test_compliance_engine_contract_and_schema()
    test_status_coverage_all_four_verdicts()
    test_ocr_uncertainty_is_never_treated_as_violation()
    test_missing_values_are_not_invented()
    test_prohibited_qualifiers_rule_12_6()
    test_units_and_symbols_rule_13()
    test_second_schedule_standard_pack_sizes()
    test_third_schedule_when_packed_exemption()
    test_de_minimis_statutory_exemptions_rule_26()
    test_real_lays_image_compliance_evaluation()
    test_detection_state_a_clearly_present_passes()
    test_detection_state_b_outside_captured_surface_needs_review()
    test_detection_state_c_low_ocr_confidence_needs_review()
    test_detection_state_d_clearly_absent_fails()
    print("\n" + "=" * 75)
    print(" ALL 14 COMPLIANCE-VALIDATION ENGINE UNIT TESTS PASSED (100%)!")
    print("=" * 75)

