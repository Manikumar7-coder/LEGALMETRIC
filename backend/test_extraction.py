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


def test_declaration_extraction_pipeline():
    print("=" * 70)
    print(" TESTING SAFEMETRIC DECLARATION EXTRACTION LAYER (LAY'S IMAGE)")
    print("=" * 70)

    # 1. Target Image
    lays_path = r"C:\Users\doram\Downloads\lays.jpg"
    if not os.path.exists(lays_path):
        lays_path = os.path.join(BASE_DIR, "demo_samples", "lays.jpg")
    assert os.path.exists(lays_path), f"Lay's image missing at {lays_path}!"
    print(f"\n[Target Image]: {lays_path}")

    # 2. Run OCR Subsystem
    print("\n--- 1. Running OCR Subsystem ---")
    ocr_result = ocr_service.process_image(lays_path, is_demo=False)
    raw_text = ocr_result.get("raw_text", "")
    boxes = ocr_result.get("bounding_boxes", [])
    assert len(boxes) > 0, "OCR produced 0 bounding boxes!"
    print(f"  OCR extracted {len(boxes)} text regions (avg confidence: {ocr_result.get('avg_confidence')}%)")

    # 3. Run Field Extraction Layer
    print("\n--- 2. Converting OCR Output to Structured Fields ---")
    fields = field_extractor.extract_declarations(raw_text, boxes)

    supported_field_keys = [
        "product_name",
        "manufacturer",
        "packer",
        "importer",
        "net_quantity",
        "mrp",
        "MRP",
        "manufacturing_date",
        "packing_date",
        "batch_number",
        "best_before",
        "consumer_care",
        "address",
        "ingredients",
        "fssai_license",
        "country_of_origin",
        "generic_name",
        "nutrition_info"
    ]

    print(f"  Total Extracted Field Keys: {len(fields)}")
    for key in supported_field_keys:
        assert key in fields, f"Required field '{key}' missing from extraction output!"

    # -----------------------------------------------------------------
    # Step 3: Canonical Field Schema Verification
    # -----------------------------------------------------------------
    print("\n--- 3. Verifying Field Schema Structure (value, raw_text, confidence, bounding_box) ---")
    for key, f in fields.items():
        assert "value" in f, f"Field '{key}' missing 'value' key!"
        assert "raw_text" in f, f"Field '{key}' missing 'raw_text' key!"
        assert "confidence" in f, f"Field '{key}' missing 'confidence' key!"
        assert "bounding_box" in f, f"Field '{key}' missing 'bounding_box' key!"

        val = f["value"]
        raw = f["raw_text"]
        conf = f["confidence"]
        box = f["bounding_box"]

        if val is None:
            # Strictly verify null representation for missing fields
            assert raw is None, f"Missing field '{key}' must have raw_text=None, got '{raw}'!"
            assert conf == 0.0, f"Missing field '{key}' must have confidence=0.0, got '{conf}'!"
            assert box is None, f"Missing field '{key}' must have bounding_box=None, got '{box}'!"
            print(f"  [MISSING/NULL] {key:22s} -> value: null | raw: null | conf: 0.0 | box: null")
        else:
            assert isinstance(val, str) and len(val.strip()) > 0, f"Field '{key}' value should be non-empty string!"
            assert raw is not None, f"Present field '{key}' must have source OCR raw_text!"
            assert conf > 0.0, f"Present field '{key}' must have non-zero confidence!"
            if box is not None:
                assert len(box) == 4, f"Field '{key}' bounding_box must have 4 coordinate points!"
            disp_val = (val[:40] + "...") if len(val) > 40 else val
            print(f"  [FOUND]        {key:22s} -> '{disp_val}' (conf: {conf}%, has_box: {bool(box)})")

    print("\n  [PASS] Every field strictly conforms to the canonical schema.")

    # -----------------------------------------------------------------
    # Step 4: Verification of Specific Extracted Values on Lay's Package
    # -----------------------------------------------------------------
    print("\n--- 4. Verifying Lay's Specific Declarations ---")

    # A. Product Name
    prod = fields["product_name"]
    assert prod["value"] in ("POTATO CHIPS", "Lay's Spanish Tomato Tango!"), f"Unexpected product name: {prod['value']}"
    assert prod["bounding_box"] is not None, "Product name missing bounding box!"
    print(f"  * Product Name:        {prod['value']} [Box: {prod['bounding_box']}]")

    # B. Manufacturer
    mfg = fields["manufacturer"]
    assert "pepsico" in mfg["value"].lower(), f"Expected PepsiCo in manufacturer, got: {mfg['value']}"
    assert mfg["bounding_box"] is not None, "Manufacturer missing bounding box!"
    print(f"  * Manufacturer:        {mfg['value']} (conf: {mfg['confidence']}%)")

    # C. Missing Fields (Packer, Importer) - MUST BE NULL / NOT INVENTED
    packer = fields["packer"]
    assert packer["value"] is None, "Packer must be None (not separately declared on Lay's)!"
    print(f"  * Packer:              null (correctly null, not invented)")

    importer = fields["importer"]
    assert importer["value"] is None, "Importer must be None (Lay's is domestic, not imported)!"
    print(f"  * Importer:            null (correctly null, not invented)")

    # D. Maximum Retail Price (MRP)
    mrp = fields["mrp"]
    assert "35" in mrp["value"], f"Expected MRP 35 in value, got: {mrp['value']}"
    assert mrp["bounding_box"] is not None, "MRP missing bounding box!"
    print(f"  * MRP:                 {mrp['value']} (conf: {mrp['confidence']}%) [Box: {mrp['bounding_box']}]")

    # E. Best Before
    bb = fields["best_before"]
    assert "month" in bb["value"].lower(), f"Expected months in best_before, got: {bb['value']}"
    assert bb["bounding_box"] is not None, "Best before missing bounding box!"
    print(f"  * Best Before:         {bb['value']} (conf: {bb['confidence']}%)")

    # F. Consumer Care Cell
    care = fields["consumer_care"]
    assert "1800224020" in care["value"] or "pepsico.com" in care["value"].lower(), f"Expected phone/email in consumer care, got: {care['value']}"
    assert care["bounding_box"] is not None, "Consumer care missing bounding box!"
    print(f"  * Consumer Care:       {care['value']} (conf: {care['confidence']}%)")

    # G. Address
    addr = fields["address"]
    assert any(k in addr["value"].lower() for k in ["gurugram", "haryana", "india", "punjab"]), f"Expected address, got: {addr['value']}"
    print(f"  * Address:             {addr['value'][:50]}... (conf: {addr['confidence']}%)")

    # H. Ingredients
    ing = fields["ingredients"]
    assert "potato" in ing["value"].lower(), f"Expected Potato in ingredients, got: {ing['value']}"
    assert ing["bounding_box"] is not None, "Ingredients missing bounding box!"
    print(f"  * Ingredients:         {ing['value'][:50]}... (conf: {ing['confidence']}%)")

    # I. Other Declarations: FSSAI License & Country of Origin & Nutrition Info
    fssai = fields["fssai_license"]
    assert fssai["value"] is not None and len(fssai["value"]) == 14, f"Expected 14-digit FSSAI license, got: {fssai['value']}"
    print(f"  * FSSAI License:       {fssai['value']} (conf: {fssai['confidence']}%)")

    origin = fields["country_of_origin"]
    assert origin["value"] == "India", f"Expected India as country of origin, got: {origin['value']}"
    print(f"  * Country of Origin:   {origin['value']} (conf: {origin['confidence']}%)")

    nut = fields["nutrition_info"]
    assert "543" in nut["value"] and "7.1" in nut["value"], f"Expected nutrition numbers, got: {nut['value']}"
    print(f"  * Nutrition Info:      {nut['value']}")

    # -----------------------------------------------------------------
    # Step 5: Strict Compliance Boundary Verification
    # -----------------------------------------------------------------
    print("\n--- 5. Verifying Compliance Boundary (No Legal Decisions Made) ---")
    for key, f in fields.items():
        assert "compliance_status" not in f, f"Field '{key}' contains illegal compliance_status!"
        assert "is_compliant" not in f, f"Field '{key}' contains illegal is_compliant!"
        assert "violation" not in f, f"Field '{key}' contains illegal violation!"
        assert "violations" not in f, f"Field '{key}' contains illegal violations!"

    assert "compliance_score" not in fields, "Compliance score must not be computed in extraction layer!"
    assert "compliance_status" not in fields, "Compliance status must not be computed in extraction layer!"
    assert "violations" not in fields, "Violations must not be computed in extraction layer!"
    print("  [PASS] Zero legal compliance decisions or rule evaluations executed.")

    print("\n" + "=" * 70)
    print(" ALL DECLARATION EXTRACTION LAYER TESTS PASSED (100%)!")
    print("=" * 70)


if __name__ == "__main__":
    test_declaration_extraction_pipeline()
