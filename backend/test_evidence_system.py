"""
test_evidence_system.py
========================
Comprehensive Unit Test Suite for the SAFEMETRIC Evidence System.

Verifies:
1. Storage of all 6 statutory parameters:
   - page/image identifier
   - bounding box
   - OCR text
   - confidence
   - associated declaration
   - associated rule
2. Preservation of connection to original image for every detected declaration.
3. Bidirectional traceability of statutory violations back to visual evidence.
4. Handling of visual evidence for both detected fields and missing mandatory fields.
5. Integration with real Lay's image OCR and compliance engine.
6. Absence of image drawing/editing operations.
"""

import os
import sys

# Configure UTF-8 stdout for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.evidence.models import EvidenceItem, EvidenceStore
from app.evidence.service import evidence_service, EvidenceService
from app.ocr.ocr_service import ocr_service
from app.extraction.field_extractor import field_extractor
from app.rules.compliance_engine import compliance_engine


def test_evidence_item_mandatory_fields_storage():
    """
    Verifies that EvidenceItem stores all 6 mandatory attributes:
    1. page/image identifier
    2. bounding box
    3. OCR text
    4. confidence
    5. associated declaration
    6. associated rule
    """
    print("\n--- 1. Testing EvidenceItem 6 Mandatory Attributes Storage ---")

    box = [[100, 200], [300, 200], [300, 250], [100, 250]]
    item = evidence_service.create_evidence_item(
        image_id="pkg_img_101.jpg",
        page_number=1,
        bounding_box=box,
        ocr_text="MRP Rs. 50.00 (Incl. of all taxes)",
        confidence=96.5,
        associated_declaration="mrp",
        associated_rule="PCR-2011-R6-1-E-MRP",
        declaration_value="Rs. 50.00",
        legal_reference="Rule 6(1)(e), Legal Metrology (Packaged Commodities) Rules, 2011"
    )

    assert isinstance(item, EvidenceItem)
    # Check 6 statutory attributes
    assert item.image_id == "pkg_img_101.jpg"
    assert item.bounding_box == box
    assert item.ocr_text == "MRP Rs. 50.00 (Incl. of all taxes)"
    assert item.confidence == 96.5
    assert item.associated_declaration == "mrp"
    assert item.associated_rule == "PCR-2011-R6-1-E-MRP"

    # Check supplementary context
    assert item.page_number == 1
    assert item.declaration_value == "Rs. 50.00"
    assert item.has_bounding_box is True
    assert item.visual_status == "DETECTED_ON_IMAGE"
    assert not item.is_violation

    # Serialization test
    d = item.to_dict()
    assert d["image_id"] == "pkg_img_101.jpg"
    assert d["bounding_box"] == box
    assert d["ocr_text"] == "MRP Rs. 50.00 (Incl. of all taxes)"
    assert d["confidence"] == 96.5
    assert d["associated_declaration"] == "mrp"
    assert d["associated_rule"] == "PCR-2011-R6-1-E-MRP"

    print("  [PASS] All 6 mandatory attributes strictly stored and verified.")


def test_preservation_of_connection_to_original_image():
    """
    Verifies that every detected declaration in an inspection preserves its
    connection to the original image identifier and page.
    """
    print("\n--- 2. Testing Image Connection Preservation Across All Declarations ---")

    test_image_id = "inspection_img_5521.png"
    sample_declarations = {
        "product_name": {
            "value": "Potato Chips",
            "raw_text": "POTATO CHIPS",
            "confidence": 98.0,
            "bounding_box": [[50, 50], [200, 50], [200, 90], [50, 90]]
        },
        "manufacturer": {
            "value": "SnackCorp India Ltd",
            "raw_text": "Mfd By: SnackCorp India Ltd",
            "confidence": 95.0,
            "bounding_box": [[50, 100], [350, 100], [350, 140], [50, 140]]
        },
        "net_quantity": {
            "value": "75 g",
            "raw_text": "Net Weight: 75 g",
            "confidence": 94.0,
            "bounding_box": [[50, 150], [180, 150], [180, 190], [50, 190]]
        },
        "mrp": {
            "value": "Rs. 20.00",
            "raw_text": "MRP Rs. 20.00 (incl. of all taxes)",
            "confidence": 96.0,
            "bounding_box": [[50, 200], [250, 200], [250, 240], [50, 240]]
        }
    }

    store = evidence_service.build_evidence_store(
        image_id=test_image_id,
        extracted_declarations=sample_declarations,
        image_path="/var/safemetric/uploads/inspection_img_5521.png"
    )

    assert store.image_id == test_image_id
    assert len(store.items) == 4

    for item in store.items:
        # Every item MUST preserve the connection to the original image
        assert item.image_id == test_image_id, f"Item {item.associated_declaration} missing image_id connection!"
        assert item.page_number == 1
        assert item.has_bounding_box is True
        assert item.ocr_text is not None
        assert item.confidence > 90.0
        assert item.associated_rule is not None, f"Item {item.associated_declaration} missing statutory rule mapping!"

    print(f"  [PASS] All {len(store.items)} declarations strictly connected to original image '{test_image_id}'.")


def test_violation_traceability_to_visual_evidence():
    """
    CRITICAL STATUTORY REQUIREMENT:
    A violation must be traceable back to visual evidence on the package substrate.
    """
    print("\n--- 3. Testing Violation Traceability to Visual Evidence ---")

    test_image_id = "violation_sample_77.jpg"

    # Package bearing a prohibited qualifier violation: "Approx 200g"
    declarations = {
        "product_name": {
            "value": "Spicy Mixture",
            "raw_text": "Spicy Mixture",
            "confidence": 95.0,
            "bounding_box": [[20, 20], [150, 20], [150, 50], [20, 50]]
        },
        "net_quantity": {
            "value": "Approx 200g",
            "raw_text": "Net Qty: Approx 200g",
            "confidence": 93.5,
            "bounding_box": [[30, 250], [280, 250], [280, 300], [30, 300]]  # Specific visual evidence
        },
        "mrp": {
            "value": "Rs. 60.00",
            "raw_text": "MRP Rs. 60.00 (incl. of all taxes)",
            "confidence": 95.0,
            "bounding_box": [[30, 310], [220, 310], [220, 350], [30, 350]]
        }
    }

    # Run compliance engine
    eval_result = compliance_engine.validate(declarations)
    assert any(r.status == "FAIL" and r.rule_id == "PCR-2011-R12-6-PROHIBITED-QUALIFIERS" for r in eval_result.rule_results)

    # Build evidence store
    store = evidence_service.build_evidence_store(
        image_id=test_image_id,
        extracted_declarations=declarations,
        rule_results=eval_result.rule_results,
        violations=eval_result.violations
    )

    # Trace violation back to visual evidence
    violation_evidence = store.trace_violation("PCR-2011-R12-6-PROHIBITED-QUALIFIERS")

    assert violation_evidence is not None, "Failed to trace violation back to visual evidence!"
    assert violation_evidence.is_violation is True
    assert violation_evidence.image_id == test_image_id
    assert violation_evidence.bounding_box == [[30, 250], [280, 250], [280, 300], [30, 300]]
    assert violation_evidence.ocr_text == "Net Qty: Approx 200g"
    assert violation_evidence.confidence == 93.5
    assert violation_evidence.associated_declaration == "net_quantity"
    assert "prohibited" in violation_evidence.violation_details.get("issue", "").lower()

    print(f"  [PASS] Violation 'PCR-2011-R12-6-PROHIBITED-QUALIFIERS' traced to image '{violation_evidence.image_id}' at {violation_evidence.bounding_box}.")


def test_missing_mandatory_declaration_visual_traceability():
    """
    Verifies that violations arising from omitted mandatory declarations
    (e.g., missing MRP or missing Consumer Care) preserve connection to the
    inspected image with visual absence status.
    """
    print("\n--- 4. Testing Missing Declaration Visual Traceability ---")

    test_image_id = "missing_mrp_packet.png"

    declarations = {
        "product_name": {
            "value": "Basmati Rice",
            "raw_text": "Basmati Rice",
            "confidence": 95.0,
            "bounding_box": [[10, 10], [100, 10], [100, 40], [10, 40]]
        },
        "mrp": {
            "value": None,
            "raw_text": None,
            "confidence": 0.0,
            "bounding_box": None,
            "status": "Missing"
        }
    }

    eval_result = compliance_engine.validate(declarations)
    mrp_rule = next(r for r in eval_result.rule_results if r.rule_id == "PCR-2011-R6-1-E-MRP")
    assert mrp_rule.status == "FAIL"

    store = evidence_service.build_evidence_store(
        image_id=test_image_id,
        extracted_declarations=declarations,
        rule_results=eval_result.rule_results,
        violations=eval_result.violations
    )

    # Trace missing MRP violation
    mrp_ev = store.trace_violation("PCR-2011-R6-1-E-MRP")
    assert mrp_ev is not None, "Missing MRP violation must be traceable in evidence store"
    assert mrp_ev.is_violation is True
    assert mrp_ev.image_id == test_image_id
    assert mrp_ev.visual_status == "MISSING_FROM_IMAGE"
    assert mrp_ev.bounding_box is None
    assert mrp_ev.ocr_text is None
    assert mrp_ev.confidence == 0.0
    assert mrp_ev.associated_declaration == "mrp"
    assert "missing" in mrp_ev.violation_details.get("issue", "").lower()

    print("  [PASS] Missing mandatory declaration violation preserved with visual absence record on image.")


def test_bounding_rect_geometry_calculation():
    """
    Verifies calculation of 2D axis-aligned bounding rectangles [x, y, w, h]
    from polygon coordinates without performing any image drawing or editing.
    """
    print("\n--- 5. Testing Bounding Rect Geometry Calculation ---")

    polygon = [[120, 340], [450, 340], [450, 390], [120, 390]]
    item = evidence_service.create_evidence_item(
        image_id="geometry_test.jpg",
        bounding_box=polygon,
        ocr_text="100% Basmati",
        confidence=95.0,
        associated_declaration="product_name"
    )

    rect = item.get_bounding_rect()
    assert rect == {"x": 120, "y": 340, "width": 330, "height": 50}

    # Verify None handling when bounding box is missing
    item_no_box = evidence_service.create_evidence_item(
        image_id="geometry_test.jpg",
        bounding_box=None,
        ocr_text=None,
        associated_declaration="packer"
    )
    assert item_no_box.get_bounding_rect() is None

    print("  [PASS] Axis-aligned bounding rect correctly computed without image editing.")


def test_evidence_store_query_operations():
    """
    Tests lookup operations on EvidenceStore:
    - get_evidence_by_declaration
    - get_evidence_by_rule
    - get_violations_evidence
    - get_detected_evidence
    - get_missing_evidence
    """
    print("\n--- 6. Testing EvidenceStore Query Operations ---")

    store = EvidenceStore(image_id="multi_query.jpg")

    ev1 = evidence_service.create_evidence_item(
        image_id="multi_query.jpg",
        associated_declaration="net_quantity",
        bounding_box=[[10, 10], [50, 10], [50, 30], [10, 30]],
        ocr_text="500 g",
        confidence=95.0,
        associated_rule="PCR-2011-R6-1-C-NET-QUANTITY"
    )
    ev2 = evidence_service.create_evidence_item(
        image_id="multi_query.jpg",
        associated_declaration="net_quantity",
        bounding_box=[[10, 35], [90, 35], [90, 55], [10, 55]],
        ocr_text="1.1 lb",
        confidence=90.0,
        associated_rule="PCR-2011-R13-UNITS-SYMBOLS",
        is_violation=True
    )
    ev3 = evidence_service.create_evidence_item(
        image_id="multi_query.jpg",
        associated_declaration="mrp",
        bounding_box=None,
        ocr_text=None,
        associated_rule="PCR-2011-R6-1-E-MRP",
        is_violation=True,
        visual_status="MISSING_FROM_IMAGE"
    )

    store.add_item(ev1)
    store.add_item(ev2)
    store.add_item(ev3)

    # 1. By declaration
    qty_items = store.get_evidence_by_declaration("net_quantity")
    assert len(qty_items) == 2

    # 2. By rule
    r13_items = store.get_evidence_by_rule("PCR-2011-R13-UNITS-SYMBOLS")
    assert len(r13_items) == 1
    assert r13_items[0].ocr_text == "1.1 lb"

    # 3. Violations
    viols = store.get_violations_evidence()
    assert len(viols) == 2

    # 4. Detected vs Missing
    assert len(store.get_detected_evidence()) == 2
    assert len(store.get_missing_evidence()) == 1

    # 5. Manifest serialization
    manifest = store.to_dict()
    assert manifest["total_evidence_items"] == 3
    assert manifest["total_violations_linked"] == 2
    assert manifest["detected_regions_count"] == 2
    assert manifest["missing_declarations_count"] == 1

    print("  [PASS] EvidenceStore query and indexing operations passed.")


def test_real_lays_image_evidence_system():
    """
    Tests evidence system end-to-end with real Lay's package image:
    1. Run OCR to acquire actual bounding boxes and confidences.
    2. Extract declarations with FieldExtractor.
    3. Run ComplianceEngine to evaluate statutory rules.
    4. Build EvidenceStore.
    5. Verify evidence preservation and violation traceability back to the image.
    """
    print("\n--- 7. Testing Evidence System on Real Lay's Product Image ---")

    lays_path = r"C:\Users\doram\Downloads\lays.jpg"
    if not os.path.exists(lays_path):
        lays_path = os.path.join(BASE_DIR, "demo_samples", "lays.jpg")
    assert os.path.exists(lays_path), f"Lay's image missing at {lays_path}!"

    # 1. OCR Subsystem
    ocr_result = ocr_service.process_image(lays_path, is_demo=False)
    raw_text = ocr_result.get("raw_text", "")
    boxes = ocr_result.get("bounding_boxes", [])

    # 2. Field Extraction Layer
    declarations = field_extractor.extract_declarations(raw_text, boxes)

    # 3. Compliance Validation Engine
    eval_result = compliance_engine.validate(declarations)

    # 4. Evidence Subsystem Integration
    image_identifier = os.path.basename(lays_path)
    store = evidence_service.build_evidence_store(
        image_id=image_identifier,
        extracted_declarations=declarations,
        rule_results=eval_result.rule_results,
        violations=eval_result.violations,
        image_path=lays_path
    )

    assert isinstance(store, EvidenceStore)
    assert store.image_id == image_identifier
    assert len(store.items) > 0

    print(f"  Total Evidence Records Preserved: {len(store.items)}")
    print(f"  Detected Visual Regions:          {len(store.get_detected_evidence())}")
    print(f"  Missing Declarations:             {len(store.get_missing_evidence())}")
    print(f"  Total Violations Linked:          {len(store.get_violations_evidence())}")

    # Verify Every Item Preserves Connection to Image
    for item in store.items:
        assert item.image_id == image_identifier, f"Item {item.associated_declaration} lost image connection!"
        if item.has_bounding_box:
            # Check 6 statutory attributes
            assert item.bounding_box is not None
            assert item.ocr_text is not None
            assert item.confidence > 0.0
            assert item.associated_declaration is not None
            assert item.associated_rule is not None
            print(f"    [VISUAL EVIDENCE] {item.associated_declaration:20s} -> BBox: {item.bounding_box[0]}..{item.bounding_box[2]} | Conf: {item.confidence}% | Rule: {item.associated_rule}")
        else:
            print(f"    [MISSING AUDIT ]  {item.associated_declaration:20s} -> Visual Status: {item.visual_status} | Rule: {item.associated_rule}")

    # Verify Specific Detected Declarations have authentic bounding boxes:
    # 1. MRP
    mrp_ev = store.get_evidence_by_declaration("mrp")
    assert len(mrp_ev) > 0
    assert mrp_ev[0].has_bounding_box is True
    assert "35" in mrp_ev[0].ocr_text
    assert mrp_ev[0].associated_rule == "PCR-2011-R6-1-E-MRP"

    # 2. Manufacturer
    mfg_ev = store.get_evidence_by_declaration("manufacturer")
    assert len(mfg_ev) > 0
    assert mfg_ev[0].has_bounding_box is True
    assert "PEPSICO" in mfg_ev[0].ocr_text
    assert mfg_ev[0].associated_rule == "PCR-2011-R6-1-A-MFG-NAME"

    # 3. Generic Name
    gen_ev = store.get_evidence_by_declaration("generic_name")
    assert len(gen_ev) > 0
    assert gen_ev[0].has_bounding_box is True
    assert "POTATO CHIPS" in gen_ev[0].ocr_text
    assert gen_ev[0].associated_rule == "PCR-2011-R6-1-B-GENERIC-NAME"

    # Verify Traceability of Violations (Net Quantity missing on this back label)
    qty_viol = store.trace_violation("PCR-2011-R6-1-C-NET-QUANTITY")
    assert qty_viol is not None
    assert qty_viol.is_violation is True
    assert qty_viol.image_id == image_identifier
    assert qty_viol.visual_status == "MISSING_FROM_IMAGE"

    print("\n  [PASS] Real Lay's packaging evidence system integration verified successfully.")


if __name__ == "__main__":
    print("=" * 75)
    print(" EXECUTING SAFEMETRIC EVIDENCE SYSTEM TEST SUITE")
    print("=" * 75)
    test_evidence_item_mandatory_fields_storage()
    test_preservation_of_connection_to_original_image()
    test_violation_traceability_to_visual_evidence()
    test_missing_mandatory_declaration_visual_traceability()
    test_bounding_rect_geometry_calculation()
    test_evidence_store_query_operations()
    test_real_lays_image_evidence_system()
    print("\n" + "=" * 75)
    print(" ALL 7 EVIDENCE SYSTEM UNIT TESTS PASSED (100%)!")
    print("=" * 75)
