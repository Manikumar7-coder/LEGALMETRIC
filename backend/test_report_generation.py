"""
test_report_generation.py
=========================
Verification test suite for SAFEMETRIC statutory PDF report generation.
Tests generation of comprehensive PDF certificates using actual packaging
declarations, real Lay's product image, OCR information, rule results,
violations, and recommendations.
"""

import os
import sys
import datetime

# Ensure backend root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.reports.pdf_generator import generate_pdf_report
from app.ocr.ocr_service import ocr_service
from app.extraction.field_extractor import field_extractor
from app.rules.compliance_engine import compliance_engine


def test_lays_pdf_report_generation():
    print("===========================================================================")
    print(" TESTING SAFEMETRIC PDF REPORT GENERATION (REAL LAY'S COMMODITY)")
    print("===========================================================================")

    lays_img_path = os.path.join(BASE_DIR, "demo_samples", "lays.jpg")
    if not os.path.exists(lays_img_path):
        lays_img_path = os.path.join(BASE_DIR, "demo_samples", "lays.png")
    if not os.path.exists(lays_img_path):
        lays_img_path = os.path.join(os.path.dirname(BASE_DIR), "demo_samples", "lays.jpg")
    assert os.path.exists(lays_img_path), f"Lay's test image not found at {lays_img_path}"

    print(f"1. Loading Real Packaging Image: {lays_img_path}")

    # Run OCR & Extraction
    print("2. Running RapidOCR on Lay's image...")
    ocr_res = ocr_service.process_image(lays_img_path, hint="lays")
    print(f"   OCR Text Length: {len(ocr_res.get('raw_text', ''))} chars, Avg Conf: {ocr_res.get('avg_confidence', 0)}%")

    print("3. Extracting Structured Declarations...")
    declarations = field_extractor.extract_declarations(
        ocr_res.get("raw_text", ""),
        ocr_res.get("bounding_boxes", [])
    )
    print(f"   Extracted {len(declarations)} fields.")

    print("4. Validating against 19 Statutory Rules...")
    evaluation = compliance_engine.validate(declarations)
    print(f"   Status: {evaluation.compliance_status}, Score: {evaluation.compliance_score}%")
    print(f"   Passed: {evaluation.passed_count}, Failed: {evaluation.failed_count}, Review: {evaluation.needs_review_count}")
    print(f"   Violations: {len(evaluation.violations)}")

    # Target PDF output path
    output_dir = os.path.join(BASE_DIR, "reports")
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "SafeMetric_Statutory_Report_LAYS_TEST.pdf")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    # Build recommendations
    recs = [
        {
            "action_type": "Rectify Non-Compliance",
            "field": v.get("field"),
            "severity": v.get("severity", "HIGH"),
            "title": f"Mandatory Declaration Rectification: {v.get('field')}",
            "detail": v.get("issue"),
            "legal_reference": v.get("rule_reference"),
            "urgency": "High"
        }
        for v in evaluation.violations
    ]

    print("5. Generating Statutory PDF Certificate...")
    generated_path = generate_pdf_report(
        inspection_id="INS-LAYS-2026-001",
        inspector_name="Senior Legal Metrology Inspector Rajesh Kumar",
        product_name="Lay's India's Magic Masala Potato Chips",
        compliance_status=evaluation.compliance_status,
        compliance_score=evaluation.compliance_score,
        extracted_data=declarations,
        violations=evaluation.violations,
        avg_confidence=ocr_res.get("avg_confidence", 95.0),
        image_path=lays_img_path,
        output_pdf_path=pdf_path,
        date_time=datetime.datetime.now(datetime.timezone.utc),
        passed_count=evaluation.passed_count,
        failed_count=evaluation.failed_count,
        needs_review_count=evaluation.needs_review_count,
        rule_results=[r.to_dict() for r in evaluation.rule_results],
        ocr_info=ocr_res,
        recommendations=recs
    )

    print(f"   Generated PDF at: {generated_path}")
    assert os.path.exists(generated_path), "PDF report was not created on filesystem."
    file_size = os.path.getsize(generated_path)
    print(f"   File Size: {file_size} bytes ({round(file_size / 1024, 1)} KB)")

    # Assert reasonable PDF size (> 25KB because of tables, styles, and embedded image)
    assert file_size > 25000, f"Generated PDF is unusually small ({file_size} bytes)."

    # Verify PDF starts with %PDF header
    with open(generated_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-", "Generated file is not a valid PDF."

    print("   [PASS] PDF Header, Structure, and Byte Size verified.")
    print("\n===========================================================================")
    print(" ALL STATUTORY REPORT GENERATION TESTS PASSED (100%)!")
    print("===========================================================================")


if __name__ == "__main__":
    test_lays_pdf_report_generation()
