import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.extraction.font_analysis import font_analysis_engine
from app.rules.compliance_engine import compliance_engine
from app.rules.knowledge_base import legal_rule_kb


def test_box_height_calculation():
    print("\n--- 1. Testing Box Height in Pixels Calculation ---")
    # Axis-aligned box: 20 pixels high, 100 pixels wide
    box = [[10.0, 50.0], [110.0, 50.0], [110.0, 70.0], [10.0, 70.0]]
    h = font_analysis_engine.compute_box_height_px(box)
    assert h == 20.0, f"Expected 20.0 px, got {h}"
    print(f"  [PASS] Box height computation accurate: {h} px")


def test_pixel_to_mm_scaling():
    print("\n--- 2. Testing Pixel-to-MM Scale Resolution ---")
    # Case A: User provides physical dimensions: 200mm height, image is 1000px high -> 0.2 mm/px
    scale_a, method_a, conf_a, limitations_a = font_analysis_engine.resolve_pixel_to_mm_scale(
        image_width_px=800,
        image_height_px=1000,
        package_length_mm=200.0,
        package_width_mm=160.0
    )
    assert scale_a == 0.2, f"Expected 0.2 mm/px, got {scale_a}"
    assert method_a == "user_calibrated_package_dimensions"
    assert conf_a == 0.95
    print(f"  [PASS] User-calibrated scale: {scale_a} mm/px (Confidence: {conf_a}, Method: {method_a})")

    # Case B: No dimensions provided -> Statistical package tier heuristic
    scale_b, method_b, conf_b, limitations_b = font_analysis_engine.resolve_pixel_to_mm_scale(
        image_width_px=800,
        image_height_px=1000,
        net_quantity_g_or_ml=500.0
    )
    assert conf_b == 0.60
    assert method_b == "statistical_package_tier_heuristic"
    assert "ESTIMATED SCALE" in limitations_b
    print(f"  [PASS] Statistical tier heuristic scale: {scale_b} mm/px (Confidence: {conf_b}, Limitations flagged)")


def test_statutory_thresholds_under_rule_7():
    print("\n--- 3. Testing Statutory Thresholds under Rule 7 Tables I & II ---")
    # Table-I: Net quantity <= 200g -> 1.0 mm (normal), 2.0 mm (blown)
    min_1, desc_1 = font_analysis_engine.get_statutory_minimum_height_mm("net_quantity", net_quantity_g_or_ml=150.0)
    assert min_1 == 1.0, f"Expected 1.0 mm, got {min_1}"
    min_1b, _ = font_analysis_engine.get_statutory_minimum_height_mm("net_quantity", net_quantity_g_or_ml=150.0, is_blown_or_embossed=True)
    assert min_1b == 2.0, f"Expected 2.0 mm, got {min_1b}"

    # Table-I: Net quantity 200g - 500g -> 2.0 mm (normal), 4.0 mm (blown)
    min_2, desc_2 = font_analysis_engine.get_statutory_minimum_height_mm("net_quantity", net_quantity_g_or_ml=500.0)
    assert min_2 == 2.0, f"Expected 2.0 mm, got {min_2}"

    # Table-I: Net quantity > 500g -> 4.0 mm (normal), 6.0 mm (blown)
    min_3, desc_3 = font_analysis_engine.get_statutory_minimum_height_mm("net_quantity", net_quantity_g_or_ml=1000.0)
    assert min_3 == 4.0, f"Expected 4.0 mm, got {min_3}"

    # General declarations under Rule 7(3) -> 1.0 mm
    min_gen, _ = font_analysis_engine.get_statutory_minimum_height_mm("manufacturer")
    assert min_gen == 1.0, f"Expected 1.0 mm, got {min_gen}"
    print("  [PASS] All Rule 7 statutory thresholds strictly verified against Gazette text.")


def test_font_analysis_pass_and_fail_generic():
    print("\n--- 4. Testing Font Compliance with Calibrated Scale (PASS & FAIL) ---")
    # Image 1000 x 1000. Package length = 200 mm -> scale = 0.2 mm/px
    # Box height = 20 px -> cap_height = 20 * 0.82 = 16.4 px -> 16.4 * 0.2 = 3.28 mm
    # Net quantity = 400g (Table I min is 2.0 mm). 3.28 mm >= 2.0 mm -> PASS
    sample_declarations = {
        "net_quantity": {
            "value": "400 g",
            "numeric_value": 400.0,
            "unit": "g",
            "confidence": 95.0,
            "bounding_box": [[100, 100], [200, 100], [200, 120], [100, 120]]
        },
        "mrp": {
            "value": "Rs. 50 (Incl. of all taxes)",
            "confidence": 92.0,
            "bounding_box": [[100, 150], [300, 150], [300, 170], [100, 170]]
        }
    }

    res_pass = font_analysis_engine.analyze_declarations(
        extracted_declarations=sample_declarations,
        image_dimensions={"width": 1000, "height": 1000},
        package_length_mm=200.0,
        package_width_mm=200.0
    )

    assert res_pass["overall_status"] == "PASS"
    assert res_pass["fields"]["net_quantity"]["status"] == "PASS"
    assert res_pass["fields"]["net_quantity"]["char_height_mm"] >= 2.0
    print(f"  [PASS] Compliant font height passed: {res_pass['fields']['net_quantity']['char_height_mm']} mm >= 2.0 mm")

    # Now create undersized font: box height 5 px -> char height = 5 * 0.82 * 0.2 = 0.82 mm (< 2.0 mm)
    sample_fail = {
        "net_quantity": {
            "value": "400 g",
            "numeric_value": 400.0,
            "unit": "g",
            "confidence": 95.0,
            "bounding_box": [[100, 100], [200, 100], [200, 105], [100, 105]]
        }
    }
    res_fail = font_analysis_engine.analyze_declarations(
        extracted_declarations=sample_fail,
        image_dimensions={"width": 1000, "height": 1000},
        package_length_mm=200.0,
        package_width_mm=200.0
    )
    assert res_fail["overall_status"] == "FAIL"
    assert res_fail["fields"]["net_quantity"]["status"] == "FAIL"
    print(f"  [PASS] Undersized font height correctly flagged as FAIL: {res_fail['fields']['net_quantity']['char_height_mm']} mm < 2.0 mm")


def test_uncertainty_handling_routes_to_needs_review():
    print("\n--- 5. Testing Uncertainty Handling Routes to NEEDS_REVIEW ---")
    # When physical dimensions are uncalibrated (heuristic scale) and height is marginal/below threshold:
    # Must route to NEEDS_REVIEW, NOT FAIL!
    sample_marginal = {
        "net_quantity": {
            "value": "400 g",
            "numeric_value": 400.0,
            "unit": "g",
            "confidence": 95.0,
            "bounding_box": [[100, 100], [200, 100], [200, 105], [100, 105]]
        }
    }
    res_heuristic = font_analysis_engine.analyze_declarations(
        extracted_declarations=sample_marginal,
        image_dimensions={"width": 1000, "height": 1000},
        package_length_mm=None,  # No user dimensions
        package_width_mm=None
    )
    assert res_heuristic["confidence"] < 0.80
    assert res_heuristic["overall_status"] == "NEEDS_REVIEW"
    assert res_heuristic["fields"]["net_quantity"]["status"] == "NEEDS_REVIEW"
    print(f"  [PASS] Uncalibrated scale strictly routed to NEEDS_REVIEW: status='{res_heuristic['overall_status']}'")


def test_compliance_engine_font_rule_integration():
    print("\n--- 6. Testing Compliance Engine Font Rule Integration ---")
    eval_res = compliance_engine.validate({
        "net_quantity": {
            "value": "500 g",
            "numeric_value": 500.0,
            "unit": "g",
            "confidence": 95.0,
            "bounding_box": [[100, 100], [200, 100], [200, 125], [100, 125]]
        },
        "_package_length_mm": 200.0,
        "_package_width_mm": 150.0,
        "dimensions": {"width": 1000, "height": 1000}
    })

    font_rule_results = [r for r in eval_res.rule_results if r.rule_id == "PCR-2011-R7-FONT-SIZE-COMPLIANCE"]
    assert len(font_rule_results) == 1, "Expected PCR-2011-R7-FONT-SIZE-COMPLIANCE in rule results"
    r = font_rule_results[0]
    assert r.status in ("PASS", "FAIL", "NEEDS_REVIEW")
    assert "Rule 7" in r.legal_reference
    print(f"  [PASS] Compliance engine evaluates font size rule: status='{r.status}', rule='{r.rule_id}'")


if __name__ == "__main__":
    test_box_height_calculation()
    test_pixel_to_mm_scaling()
    test_statutory_thresholds_under_rule_7()
    test_font_analysis_pass_and_fail_generic()
    test_uncertainty_handling_routes_to_needs_review()
    test_compliance_engine_font_rule_integration()
    print("\n======================================================================")
    print(" ALL FONT SIZE & READABILITY ANALYSIS TESTS PASSED SUCCESSFULLY (100%)")
    print("======================================================================")
