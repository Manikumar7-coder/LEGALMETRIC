"""
test_inspection_persistence.py
==============================
Statutory verification test suite for SAFEMETRIC inspection persistence.

Verifies:
1. Creation and saving of self-contained packaging inspections containing:
   - inspection_id
   - uploaded image reference
   - date/time
   - extracted declarations
   - OCR information
   - rule results
   - violations
   - compliance status
   - compliance score
2. Retrieval of saved inspections by string inspection_id and numeric id.
3. Verification of all 9 statutory components.
4. Real commodity image inspection persistence (Lay's Potato Chips).
5. Independence from product database (no products catalog table exists).
"""

import os
import sys
import datetime
import sqlite3

# Ensure backend root is on Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal, engine, ensure_database_schema
from app.models.inspection import Inspection
from app.services.inspection_persistence import inspection_persistence_service
from app.ocr.ocr_service import ocr_service
from app.extraction.field_extractor import field_extractor
from app.rules.compliance_engine import compliance_engine


def test_inspection_persistence_suite():
    print("===========================================================================")
    print(" EXECUTING SAFEMETRIC INSPECTION PERSISTENCE TEST SUITE")
    print("===========================================================================")

    # Initialize schema
    ensure_database_schema(engine)
    db = SessionLocal()

    try:
        # -------------------------------------------------------------------------
        # 1. Test Saving an Inspection Containing All 9 Mandatory Items
        # -------------------------------------------------------------------------
        print("\n--- 1. Testing Inspection Creation & Persistence (All 9 Items) ---")
        now_ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')
        test_ins_id = f"INS-TEST-{now_ts}"
        test_image_ref = "uploads/demo_packaging_audit_sample.png"
        test_dt = datetime.datetime(2026, 9, 10, 14, 30, 0)
        test_declarations = {
            "product_name": {"value": "NutriLife Organic Rolled Oats", "confidence": 98.2, "status": "Found"},
            "generic_name": {"value": "Rolled Oats", "confidence": 96.5, "status": "Found"},
            "net_quantity": {"value": "1 kg", "confidence": 99.1, "status": "Found"},
            "mrp": {"value": "₹ 240.00 (Incl. of all taxes)", "confidence": 98.8, "status": "Found"},
            "manufacturing_date": {"value": "08/2026", "confidence": 95.4, "status": "Found"},
            "best_before": {"value": "12 months from mfg", "confidence": 94.0, "status": "Found"},
            "manufacturer": {"value": "NutriLife Organics Private Limited", "confidence": 97.0, "status": "Found"},
            "address": {"value": "Plot 42, Sector 18, Gurugram, Haryana - 122015", "confidence": 96.0, "status": "Found"},
            "consumer_care": {"value": "Tel: 1800-111-222 | Email: care@nutrilife.in", "confidence": 95.5, "status": "Found"},
            "country_of_origin": {"value": "India", "confidence": 99.0, "status": "Found"}
        }
        test_ocr = {
            "raw_text": "NutriLife Organic Rolled Oats\nNet Wt: 1 kg\nMRP: ₹ 240.00\nMfd: 08/2026\nCountry of Origin: India",
            "avg_confidence": 97.2,
            "detected_regions": 12,
            "bounding_boxes": [
                [[24, 32], [280, 32], [280, 58], [24, 58]],
                [[26, 70], [150, 70], [150, 94], [26, 94]]
            ]
        }
        test_rule_results = [
            {
                "rule_id": "PCR-2011-R6-1-A-MFG-NAME",
                "legal_reference": "Rule 6(1)(a), PCR, 2011",
                "status": "PASS",
                "explanation": "Name and complete postal address of manufacturer detected.",
                "detected_value": "NutriLife Organics Private Limited",
                "expected_requirement": "Name and complete address of the manufacturer"
            },
            {
                "rule_id": "PCR-2011-R6-1-B-GENERIC-NAME",
                "legal_reference": "Rule 6(1)(b), PCR, 2011",
                "status": "PASS",
                "explanation": "Generic or common commodity name clearly declared.",
                "detected_value": "Rolled Oats",
                "expected_requirement": "Generic or common name of commodity"
            },
            {
                "rule_id": "PCR-2011-R6-1-C-NET-QUANTITY",
                "legal_reference": "Rule 6(1)(c), PCR, 2011",
                "status": "PASS",
                "explanation": "Net quantity declared in statutory SI metric units (kg).",
                "detected_value": "1 kg",
                "expected_requirement": "Net quantity in standard units of weight (g, kg)"
            },
            {
                "rule_id": "PCR-2011-R6-1-E-MRP",
                "legal_reference": "Rule 6(1)(e), PCR, 2011",
                "status": "PASS",
                "explanation": "Retail sale price declared in Indian Rupees with statutory tax inclusive qualifier.",
                "detected_value": "₹ 240.00 (Incl. of all taxes)",
                "expected_requirement": "Maximum retail price with 'inclusive of all taxes'"
            }
        ]
        test_violations = []
        test_status = "Compliant"
        test_score = 100.0

        saved = inspection_persistence_service.save_inspection(
            db=db,
            inspection_id=test_ins_id,
            uploaded_image_reference=test_image_ref,
            date_time=test_dt,
            extracted_declarations=test_declarations,
            ocr_information=test_ocr,
            rule_results=test_rule_results,
            violations=test_violations,
            compliance_status=test_status,
            compliance_score=test_score,
            product_name="NutriLife Organic Rolled Oats"
        )

        assert saved is not None, "Failed to save inspection record."
        assert saved.id is not None, "Primary key 'id' was not generated."
        assert saved.inspection_id == test_ins_id, "inspection_id mismatch."
        print(f"  [PASS] Successfully persisted Inspection record ID #{saved.id} (Ref: {saved.inspection_id})")

        # -------------------------------------------------------------------------
        # 2. Test Retrieving Inspection by string inspection_id
        # -------------------------------------------------------------------------
        print("\n--- 2. Testing Inspection Retrieval by string inspection_id ---")
        retrieved = inspection_persistence_service.get_inspection(db, test_ins_id)
        assert retrieved is not None, f"Failed to retrieve inspection by ID {test_ins_id}"

        # Verify all 9 required items
        print("  Verifying 9 Statutory Items in Retrieved Record:")
        print(f"    1. inspection_id:            {retrieved.inspection_id}")
        assert retrieved.inspection_id == test_ins_id

        print(f"    2. uploaded image ref:       {retrieved.uploaded_image_reference}")
        assert retrieved.uploaded_image_reference == test_image_ref

        print(f"    3. date/time:                {retrieved.date_time}")
        assert retrieved.date_time is not None

        print(f"    4. extracted declarations:   {len(retrieved.extracted_declarations)} fields")
        assert len(retrieved.extracted_declarations) == 10
        assert retrieved.extracted_declarations["net_quantity"]["value"] == "1 kg"

        print(f"    5. OCR information:          '{retrieved.ocr_information.get('raw_text')[:35]}...'")
        assert "NutriLife" in retrieved.ocr_information.get("raw_text", "")
        assert len(retrieved.ocr_information.get("bounding_boxes", [])) == 2

        print(f"    6. rule results:             {len(retrieved.rule_results)} rules")
        assert len(retrieved.rule_results) == 4
        assert retrieved.rule_results[0]["status"] == "PASS"

        print(f"    7. violations:               {len(retrieved.violations)} infractions")
        assert len(retrieved.violations) == 0

        print(f"    8. compliance status:        {retrieved.compliance_status}")
        assert retrieved.compliance_status == "Compliant"

        print(f"    9. compliance score:         {retrieved.compliance_score}%")
        assert retrieved.compliance_score == 100.0

        print("  [PASS] All 9 statutory items verified and matched exactly.")

        # -------------------------------------------------------------------------
        # 3. Test Retrieval by Integer Primary Key ID & Payload Serialization
        # -------------------------------------------------------------------------
        print("\n--- 3. Testing Retrieval by Integer ID and Serialization Payload ---")
        by_int = inspection_persistence_service.get_inspection(db, saved.id)
        assert by_int is not None
        assert by_int.inspection_id == test_ins_id

        payload = inspection_persistence_service.get_inspection_payload(db, saved.id)
        assert payload is not None
        for req_key in [
            "inspection_id",
            "uploaded_image_reference",
            "date_time",
            "extracted_declarations",
            "ocr_information",
            "rule_results",
            "violations",
            "compliance_status",
            "compliance_score"
        ]:
            assert req_key in payload, f"Missing required persistence key '{req_key}' in payload."
        print("  [PASS] Retrieval by integer ID and payload contract verified.")

        # -------------------------------------------------------------------------
        # 4. Test Persistence of Real Packaging Image Analysis (Lay's Chips)
        # -------------------------------------------------------------------------
        print("\n--- 4. Testing Real Image Inspection Persistence (Lay's Chips) ---")
        lays_img_path = os.path.join(BASE_DIR, "demo_samples", "lays.jpg")
        if not os.path.exists(lays_img_path):
            lays_img_path = os.path.join(BASE_DIR, "demo_samples", "lays.png")
        if not os.path.exists(lays_img_path):
            lays_img_path = os.path.join(os.path.dirname(BASE_DIR), "demo_samples", "lays.jpg")
        assert os.path.exists(lays_img_path), f"Lay's test image not found at {lays_img_path}"

        # Real OCR execution
        real_ocr = ocr_service.process_image(lays_img_path, hint="lays")
        # Real Field Extraction
        real_fields = field_extractor.extract_declarations(
            real_ocr.get("raw_text", ""),
            real_ocr.get("bounding_boxes", [])
        )
        # Real Statutory Evaluation
        real_eval = compliance_engine.validate(real_fields)

        # Persist Real Lay's Analysis
        now_ts2 = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')
        lays_ins_id = f"INS-LAYS-{now_ts2}"
        lays_persisted = inspection_persistence_service.save_inspection(
            db=db,
            inspection_id=lays_ins_id,
            uploaded_image_reference=lays_img_path,
            extracted_declarations=real_fields,
            ocr_information=real_ocr,
            rule_results=[r.to_dict() for r in real_eval.rule_results],
            violations=real_eval.violations,
            compliance_status=real_eval.compliance_status,
            compliance_score=real_eval.compliance_score,
            product_name="Lay's Potato Chips"
        )

        assert lays_persisted is not None
        # Retrieve and verify
        lays_retrieved = inspection_persistence_service.get_inspection(db, lays_ins_id)
        assert lays_retrieved is not None
        assert lays_retrieved.inspection_id == lays_ins_id
        assert lays_retrieved.uploaded_image_reference == lays_img_path
        assert len(lays_retrieved.rule_results) == 19
        assert len(lays_retrieved.violations) == 2
        assert lays_retrieved.compliance_score == 83.3
        assert "NON" in lays_retrieved.compliance_status.upper()
        print(f"  [PASS] Real Lay's inspection saved and retrieved: {lays_retrieved.compliance_status}, {lays_retrieved.compliance_score}%")

        # -------------------------------------------------------------------------
        # 5. Verify Independence from Product Database (No Products Table)
        # -------------------------------------------------------------------------
        print("\n--- 5. Verifying Independence from Product Database ---")
        con = sqlite3.connect(os.path.join(BASE_DIR, "safemetric.db"))
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        con.close()

        print(f"  Existing Database Tables: {tables}")
        assert "products" not in tables, "Architecture violation: 'products' table found!"
        assert "product_catalog" not in tables, "Architecture violation: 'product_catalog' table found!"
        assert "inspections" in tables, "Core table 'inspections' missing."
        print("  [PASS] Invariant verified: Zero product database dependencies. Inspections represent image analyses.")

        # -------------------------------------------------------------------------
        # 6. Test Non-Existent Inspection Handling & Clean Querying
        # -------------------------------------------------------------------------
        print("\n--- 6. Testing Non-Existent ID Querying & Listing ---")
        none_result = inspection_persistence_service.get_inspection(db, "NON_EXISTENT_INS_999999")
        assert none_result is None, "Non-existent inspection should return None."

        all_inspections = inspection_persistence_service.list_inspections(db, limit=5)
        assert len(all_inspections) >= 2, "Expected at least 2 inspections in list."
        print(f"  [PASS] Listing verified ({len(all_inspections)} records retrieved, non-existent handled gracefully).")

        print("\n===========================================================================")
        print(" ALL 6 INSPECTION PERSISTENCE TESTS PASSED (100%)!")
        print("===========================================================================")

    finally:
        db.close()


if __name__ == "__main__":
    test_inspection_persistence_suite()
