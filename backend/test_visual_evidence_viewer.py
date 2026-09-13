"""
test_visual_evidence_viewer.py
===============================
Statutory Verification of the Visual Evidence Viewer Data Pipeline on Lay's Product Image.

Verifies:
1. Original uploaded image URL and preservation of unmodified image.
2. Complete detection and delivery of OCR text bounding boxes.
3. Highlighting and tagging of statutory violation regions.
4. Bidirectional selection of violations and their associated image regions.
5. Verbatim OCR text and optical confidence score exposure.
6. Zero image file pixel modifications.
7. Verification on real Lay's chips packaging image.
"""

import os
import sys

# Configure UTF-8 stdout for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.ocr.ocr_service import ocr_service
from app.extraction.field_extractor import field_extractor
from app.rules.compliance_engine import compliance_engine
from app.evidence.service import evidence_service
from app.evidence.models import EvidenceStore, EvidenceItem


def test_visual_evidence_viewer_data_contract():
    print("=" * 75)
    print(" TESTING VISUAL EVIDENCE VIEWER DATA PIPELINE (LAY'S IMAGE)")
    print("=" * 75)

    lays_path = r"C:\Users\doram\Downloads\lays.jpg"
    if not os.path.exists(lays_path):
        lays_path = os.path.join(BASE_DIR, "demo_samples", "lays.jpg")
    assert os.path.exists(lays_path), f"Lay's image missing at {lays_path}!"

    original_size = os.path.getsize(lays_path)
    original_mtime = os.path.getmtime(lays_path)
    print(f"\n[1. Original Image Input]: {lays_path} ({original_size} bytes)")

    # 1. OCR Subsystem
    print("\n--- 1. Executing OCR & Extracting Bounding Boxes ---")
    ocr_result = ocr_service.process_image(lays_path, is_demo=False)
    boxes = ocr_result.get("bounding_boxes", [])
    raw_text = ocr_result.get("raw_text", "")
    assert len(boxes) > 0, "OCR produced 0 bounding boxes"
    print(f"  OCR extracted {len(boxes)} text regions with polygon coordinates.")

    # 2. Field Extraction
    print("\n--- 2. Extracting Structured Declarations ---")
    declarations = field_extractor.extract_declarations(raw_text, boxes)
    assert len(declarations) > 0

    # 3. Compliance Validation Engine
    print("\n--- 3. Running Statutory Compliance Validation ---")
    evaluation = compliance_engine.validate(declarations)
    print(f"  Compliance Status: {evaluation.compliance_status}")
    print(f"  Total Violations:  {len(evaluation.violations)}")

    # 4. Evidence Subsystem Linking
    print("\n--- 4. Building Visual Evidence Store Manifest ---")
    image_identifier = os.path.basename(lays_path)
    store = evidence_service.build_evidence_store(
        image_id=image_identifier,
        extracted_declarations=declarations,
        rule_results=evaluation.rule_results,
        violations=evaluation.violations,
        image_path=lays_path
    )

    manifest = store.to_dict()
    assert manifest["image_id"] == image_identifier
    assert manifest["total_evidence_items"] > 0
    print(f"  Total Evidence Items: {manifest['total_evidence_items']}")
    print(f"  Detected Regions:     {manifest['detected_regions_count']}")
    print(f"  Missing Declarations: {manifest['missing_declarations_count']}")
    print(f"  Violations Linked:    {manifest['total_violations_linked']}")

    # 5. Requirement Verification: Display detected text regions with OCR text & confidence
    print("\n--- 5. Verifying Detected Text Regions, OCR Text & Optical Confidence ---")
    detected_items = store.get_detected_evidence()
    assert len(detected_items) > 0, "No detected visual regions found!"

    for item in detected_items:
        # Verify 6 statutory attributes
        assert item.image_id == image_identifier
        assert item.bounding_box is not None and len(item.bounding_box) >= 4
        assert item.ocr_text is not None and len(item.ocr_text) > 0
        assert item.confidence > 0.0
        assert item.associated_declaration is not None
        assert item.associated_rule is not None

        rect = item.get_bounding_rect()
        assert rect is not None
        assert rect["width"] > 0 and rect["height"] > 0

    print(f"  [PASS] All {len(detected_items)} detected regions contain valid bounding boxes, OCR text, and optical confidence.")

    # 6. Requirement Verification: Highlight regions associated with violations
    print("\n--- 6. Verifying Highlighting of Violation Regions ---")
    violations_evidence = store.get_violations_evidence()
    assert len(violations_evidence) > 0, "Expected violations on Lay's back-panel crop!"

    for v_ev in violations_evidence:
        assert v_ev.is_violation is True
        assert v_ev.associated_rule is not None
        assert v_ev.violation_details is not None
        assert "issue" in v_ev.violation_details

        if v_ev.has_bounding_box:
            print(f"  [VIOLATION REGION HIGHLIGHTED]: {v_ev.associated_declaration:20s} at {v_ev.bounding_box[0]}..{v_ev.bounding_box[2]} | Conf: {v_ev.confidence}% | Rule: {v_ev.associated_rule}")
        else:
            print(f"  [MISSING MANDATORY AUDIT     ]: {v_ev.associated_declaration:20s} | Status: {v_ev.visual_status} | Rule: {v_ev.associated_rule}")

    print("  [PASS] Violation regions and missing mandatory declarations accurately tagged and highlighted.")

    # 7. Requirement Verification: Allow selecting a violation and viewing its related image region
    print("\n--- 7. Verifying Violation Selection & Bidirectional Region Traceability ---")
    # Test selecting Net Quantity violation
    net_qty_ev = store.trace_violation("PCR-2011-R6-1-C-NET-QUANTITY")
    assert net_qty_ev is not None
    assert net_qty_ev.is_violation is True
    assert net_qty_ev.visual_status == "MISSING_FROM_IMAGE"
    assert net_qty_ev.image_id == image_identifier

    # Test selecting Mfg Date violation
    mfg_date_ev = store.trace_violation("PCR-2011-R6-1-D-DATE")
    assert mfg_date_ev is not None
    assert mfg_date_ev.is_violation is True
    assert mfg_date_ev.visual_status == "MISSING_FROM_IMAGE"

    # Test selecting a present declaration (MRP)
    mrp_items = store.get_evidence_by_declaration("mrp")
    assert len(mrp_items) > 0
    mrp_ev = mrp_items[0]
    assert mrp_ev.has_bounding_box is True
    assert "35" in mrp_ev.ocr_text
    assert mrp_ev.confidence == 91.2
    assert mrp_ev.associated_rule == "PCR-2011-R6-1-E-MRP"
    print(f"  [SELECTED REGION]: 'mrp' -> OCR Text: '{mrp_ev.ocr_text}' | Confidence: {mrp_ev.confidence}% | Rule: {mrp_ev.associated_rule}")

    print("  [PASS] Violation selection and related image region query verified.")

    # 8. Requirement Verification: Do not modify the original image file
    print("\n--- 8. Verifying Original Image Integrity (Zero File Modification) ---")
    current_size = os.path.getsize(lays_path)
    current_mtime = os.path.getmtime(lays_path)
    assert current_size == original_size, "Original image size was modified!"
    assert current_mtime == original_mtime, "Original image timestamp was modified!"
    print(f"  [PASS] Original image file remained 100% untouched ({current_size} bytes).")

    print("\n" + "=" * 75)
    print(" ALL VISUAL EVIDENCE VIEWER PIPELINE TESTS PASSED (100%)!")
    print("=" * 75)


if __name__ == "__main__":
    test_visual_evidence_viewer_data_contract()
