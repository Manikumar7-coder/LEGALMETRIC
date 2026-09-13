"""
test_placement_checker.py
=========================
Unit test suite for SAFEMETRIC Rule 8 Placement & Grouping Analysis Engine.

Statutory Verification:
- Rule 8(1) & 8(2) of Legal Metrology (Packaged Commodities) Rules, 2011.
- Proviso to Rule 8(1): Clear space zone surrounding net quantity:
  * 1x height of numeral vertically (above & below)
  * 2x height of numeral horizontally (left & right)
- PDP Grouping of core declarations
- Uncertainty routing to NEEDS_REVIEW when coordinates are absent or < 2 declarations.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.extraction.placement_checker import placement_checker, PlacementChecker
from app.rules.compliance_engine import compliance_engine


def test_box_normalization():
    """Test _to_rect with various coordinate formats."""
    print("\n--- 1. Testing Bounding Box Normalization ---")

    # 4-point polygon
    poly = [[10, 20], [100, 20], [100, 50], [10, 50]]
    rect1 = PlacementChecker._to_rect(poly)
    assert rect1 == (10.0, 20.0, 100.0, 50.0), f"Expected (10, 20, 100, 50), got {rect1}"

    # 4-element list
    bbox = [15, 25, 115, 65]
    rect2 = PlacementChecker._to_rect(bbox)
    assert rect2 == (15.0, 25.0, 115.0, 65.0), f"Expected (15, 25, 115, 65), got {rect2}"

    # Dict format
    d = {"x_min": 5, "y_min": 10, "x_max": 80, "y_max": 40}
    rect3 = PlacementChecker._to_rect(d)
    assert rect3 == (5.0, 10.0, 80.0, 40.0), f"Expected (5, 10, 80, 40), got {rect3}"

    # None / empty handling
    assert PlacementChecker._to_rect(None) is None
    assert PlacementChecker._to_rect([]) is None

    print("  [PASS] All bounding box formats normalized accurately.")


def test_pdp_grouping_pass():
    """Test cohesive grouping on PDP returns PASS."""
    print("\n--- 2. Testing PDP Declaration Grouping (PASS) ---")

    declarations = {
        "product_name": {
            "value": "Potato Chips",
            "bounding_box": [[100, 100], [400, 100], [400, 150], [100, 150]]
        },
        "net_quantity": {
            "value": "100 g",
            "bounding_box": [[100, 200], [250, 200], [250, 240], [100, 240]]
        },
        "mrp": {
            "value": "Rs. 20.00",
            "bounding_box": [[100, 260], [300, 260], [300, 290], [100, 290]]
        },
        "manufacturer": {
            "value": "Snack Co Ltd",
            "bounding_box": [[100, 310], [450, 310], [450, 350], [100, 350]]
        }
    }

    res = placement_checker.analyze_placement(
        extracted_declarations=declarations,
        image_dimensions=(1000, 1000)
    )

    assert res["grouping"]["status"] == "PASS"
    assert len(res["grouping"]["fields_analyzed"]) >= 3
    print(f"  [PASS] Grouping status: {res['grouping']['status']}, fields: {res['grouping']['fields_analyzed']}")


def test_pdp_grouping_insufficient_boxes_needs_review():
    """Test < 2 boxes routes to NEEDS_REVIEW (never FAIL)."""
    print("\n--- 3. Testing PDP Grouping with Insufficient Boxes (NEEDS_REVIEW) ---")

    declarations = {
        "product_name": {
            "value": "Snack Item",
            "bounding_box": None  # No box
        },
        "net_quantity": {
            "value": "50 g",
            "bounding_box": [[100, 200], [250, 200], [250, 240], [100, 240]]
        }
        # Only 1 core field with box
    }

    res = placement_checker.analyze_placement(
        extracted_declarations=declarations,
        image_dimensions=(1000, 1000)
    )

    assert res["grouping"]["status"] == "NEEDS_REVIEW"
    assert "insufficient" in res["grouping"]["limitation"].lower() or "coordinates" in res["grouping"]["explanation"].lower()
    print("  [PASS] Insufficient coordinates strictly route to NEEDS_REVIEW, avoiding false violation.")


def test_clear_space_pass():
    """Test clear space when no intruding text exists within 1x vertical / 2x horizontal."""
    print("\n--- 4. Testing Net Quantity Clear Space (PASS) ---")

    # Net quantity box: [200, 300, 300, 330] -> height = 30px
    # Clear space zone:
    # vert clearance = 30px -> ymin = 270, ymax = 360
    # horiz clearance = 60px -> xmin = 140, xmax = 360
    declarations = {
        "net_quantity": {
            "value": "75 g",
            "bounding_box": [200, 300, 300, 330]
        },
        "mrp": {
            "value": "Rs. 40.00",
            "bounding_box": [200, 450, 350, 480]  # Far below y=360
        }
    }

    all_detections = [
        {"box": [200, 300, 300, 330], "text": "75 g"},        # Self
        {"box": [200, 450, 350, 480], "text": "MRP Rs. 40.00"}, # Outside clear zone
        {"box": [50, 100, 400, 150], "text": "Brand Headline"}  # Far above
    ]

    res = placement_checker.analyze_placement(
        extracted_declarations=declarations,
        all_detections=all_detections,
        image_dimensions=(800, 1000)
    )

    cs = res["clear_space"]
    assert cs["status"] == "PASS"
    assert cs["numeral_height_px"] == 30.0
    assert cs["required_vertical_clearance_px"] == 30.0
    assert cs["required_horizontal_clearance_px"] == 60.0
    assert len(cs["intrusions_detected"]) == 0
    print("  [PASS] Clean clearance around net quantity correctly returns PASS.")


def test_clear_space_fail_with_intrusion():
    """Test clear space detection when printed information encroaches (FAIL under Rule 8(1))."""
    print("\n--- 5. Testing Net Quantity Clear Space Intrusion (FAIL) ---")

    # Net quantity box: [200, 300, 300, 330] -> height = 30px
    # Clear space zone: x in [140, 360], y in [270, 360]
    declarations = {
        "net_quantity": {
            "value": "75 g",
            "bounding_box": [200, 300, 300, 330]
        },
        "mrp": {
            "value": "Rs. 40.00",
            "bounding_box": [200, 335, 300, 355]  # Intruding directly below net quantity (y=335 < y=360)!
        }
    }

    all_detections = [
        {"box": [200, 300, 300, 330], "text": "75 g"},
        {"box": [200, 335, 300, 355], "text": "MRP Rs. 40.00"} # Encroaching text
    ]

    res = placement_checker.analyze_placement(
        extracted_declarations=declarations,
        all_detections=all_detections,
        image_dimensions=(800, 1000)
    )

    cs = res["clear_space"]
    assert cs["status"] == "FAIL"
    assert len(cs["intrusions_detected"]) > 0
    assert cs["intrusions_detected"][0]["text"] == "MRP Rs. 40.00"
    assert res["status"] == "FAIL"
    print(f"  [PASS] Encroaching text correctly flagged as FAIL: {cs['explanation']}")


def test_compliance_engine_rule_8_integration():
    """Test full compliance engine evaluation of PCR-2011-R8-DECLARATION-PLACEMENT."""
    print("\n--- 6. Testing Compliance Engine Rule 8 Integration ---")

    sample_data = {
        "product_name": {"value": "Wheat Flour", "bounding_box": [50, 50, 400, 100], "confidence": 95.0},
        "net_quantity": {"value": "1 kg", "bounding_box": [50, 150, 200, 190], "confidence": 96.0},
        "mrp": {"value": "Rs. 60.00", "bounding_box": [50, 300, 250, 330], "confidence": 95.0, "has_currency": True, "has_tax": True},
        "manufacturer": {"value": "Agro Millers Pvt Ltd", "bounding_box": [50, 360, 450, 400], "confidence": 92.0},
        "consumer_care": {"value": "1800-200-3000", "bounding_box": [50, 420, 350, 450], "confidence": 94.0},
        "country_of_origin": {"value": "India", "confidence": 95.0},
        "manufacturing_date": {"value": "01/2026", "confidence": 95.0}
    }

    eval_result = compliance_engine.validate(sample_data)

    r8 = next((r for r in eval_result.rule_results if r.rule_id == "PCR-2011-R8-DECLARATION-PLACEMENT"), None)
    assert r8 is not None, "Rule PCR-2011-R8-DECLARATION-PLACEMENT was not evaluated!"
    assert r8.status in ("PASS", "NEEDS_REVIEW", "FAIL")
    assert "Rule 8" in r8.legal_reference
    assert isinstance(r8.evidence_reference, dict)
    assert "grouping" in r8.evidence_reference
    assert "clear_space" in r8.evidence_reference
    print(f"  [PASS] Compliance engine Rule 8 evaluation: {r8.status} — {r8.explanation[:80]}...")


if __name__ == "__main__":
    test_box_normalization()
    test_pdp_grouping_pass()
    test_pdp_grouping_insufficient_boxes_needs_review()
    test_clear_space_pass()
    test_clear_space_fail_with_intrusion()
    test_compliance_engine_rule_8_integration()
    print("\n" + "=" * 70)
    print(" ALL RULE 8 PLACEMENT & GROUPING TESTS PASSED (100%)!")
    print("=" * 70)
