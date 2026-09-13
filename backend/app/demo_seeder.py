import os
import datetime
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.inspection import Inspection
from app.models.field import InspectionField
from app.models.report import Report
from app.models.rule import Rule
from app.auth.security import hash_password
from app.rules.rule_engine import rule_engine
from app.reports.pdf_generator import generate_pdf_report

def create_sample_label_images(demo_dir: str):
    """Generates realistic visual product label images for demonstration and field testing."""
    os.makedirs(demo_dir, exist_ok=True)

    # 1. Compliant Label: SafeRice Premium
    img1 = Image.new('RGB', (800, 1000), color='#FBFBFB')
    draw1 = ImageDraw.Draw(img1)
    
    # Outer green security border
    draw1.rectangle([(20, 20), (780, 980)], outline='#15803D', width=4)
    draw1.rectangle([(30, 30), (770, 970)], outline='#86EFAC', width=2)
    
    # Header Banner
    draw1.rectangle([(35, 35), (765, 120)], fill='#14532D')
    draw1.text((220, 50), "SafeRice Premium", fill='#FFFFFF')
    draw1.text((250, 85), "TRADITIONAL AGED BASMATI RICE", fill='#BBF7D0')
    
    # Declarations Box
    draw1.rectangle([(60, 150), (740, 940)], outline='#CBD5E1', width=2, fill='#F8FAFC')
    
    label_lines1 = [
        "STATUTORY LEGAL METROLOGY DECLARATIONS",
        "--------------------------------------------------",
        "Commodity: Packaged Basmati Rice",
        "Net Quantity: 500 g",
        "Maximum Retail Price (MRP): Rs. 120 (Incl. of all taxes)",
        "Month & Year of Manufacture: 08/2026",
        "Best Before: 06/2027 (10 Months from Packaging)",
        "Batch / Lot No: BATCH-SR-2026-08A",
        "Country of Origin: India",
        "",
        "Manufactured & Packed By:",
        "Safe Foods Pvt Ltd",
        "Address: Plot No. 42, Food Park, Phase-1,",
        "Sonipat, Haryana - 131001",
        "",
        "Consumer Care Cell:",
        "Toll-Free Helpline: 1800-123-4567",
        "Email: customercare@safefoods.in",
        "For grievances contact: Executive - Consumer Service at above address"
    ]
    
    y = 170
    for line in label_lines1:
        if line.startswith("STATUTORY"):
            draw1.text((120, y), line, fill='#0F2744')
        elif line.startswith("Manufactured") or line.startswith("Consumer Care"):
            draw1.text((80, y), line, fill='#1E40AF')
        else:
            draw1.text((80, y), line, fill='#1E293B')
        y += 36

    img1.save(os.path.join(demo_dir, "sample_saferice.png"))

    # 2. Non-Compliant Label: Crispy Delight
    img2 = Image.new('RGB', (800, 1000), color='#FFFBEB')
    draw2 = ImageDraw.Draw(img2)
    
    draw2.rectangle([(20, 20), (780, 980)], outline='#B45309', width=4)
    draw2.rectangle([(35, 35), (765, 120)], fill='#78350F')
    draw2.text((220, 50), "Crispy Delight Wafers", fill='#FFFFFF')
    draw2.text((260, 85), "SALTED POTATO CHIPS", fill='#FDE68A')
    
    label_lines2 = [
        "PACKAGED SNACK DECLARATION",
        "--------------------------------------------------",
        "Product: Crispy Delight Potato Wafers",
        "Net Wt: Approx 200g  [VIOLATION: Qualifiers prohibited]",
        "MRP: 50              [VIOLATION: Currency & Taxes missing]",
        "Mfg: 05/2026",
        "Best Before 4 months from packaging",
        "Manufactured by: Delight Snacks & Co",
        "Address: Industrial Area, Pune, Maharashtra",
        "",
        "[VIOLATION: Consumer Care Details MISSING]",
        "[VIOLATION: Country of Origin MISSING]"
    ]
    
    y = 180
    for line in label_lines2:
        if "[VIOLATION" in line:
            draw2.text((80, y), line, fill='#DC2626')
        else:
            draw2.text((80, y), line, fill='#1E293B')
        y += 44

    img2.save(os.path.join(demo_dir, "sample_wafer.png"))

    # 3. Review Required Label: Olive Oil
    img3 = Image.new('RGB', (800, 1000), color='#F0FDF4')
    draw3 = ImageDraw.Draw(img3)
    draw3.rectangle([(20, 20), (780, 980)], outline='#047857', width=4)
    draw3.rectangle([(35, 35), (765, 120)], fill='#064E3B')
    draw3.text((200, 50), "Mediterranean Olive Oil", fill='#FFFFFF')
    draw3.text((270, 85), "EXTRA VIRGIN COLD PRESSED", fill='#A7F3D0')
    
    label_lines3 = [
        "IMPORT COMMODITY DECLARATIONS",
        "--------------------------------------------------",
        "Volume: 1 Litre",
        "MRP: Rs. 950 (Incl. of all taxes)",
        "Pkd: 01/2026",
        "Use By: 12/2027",
        "Country of Origin: Spain",
        "Imported and Distributed by: Global Gourmet Logistics",
        "Office address obscured / unreadable",
        "Customer Care: info@globalgourmet.eu",
        "",
        "[FLAG: Address illegibility requires visual review]"
    ]
    
    y = 180
    for line in label_lines3:
        if "[FLAG" in line:
            draw3.text((80, y), line, fill='#D97706')
        else:
            draw3.text((80, y), line, fill='#1E293B')
        y += 44

    img3.save(os.path.join(demo_dir, "sample_oil.png"))


def seed_database(db: Session):
    """Seeds default Legal Metrology rules, default admin inspector, and demo inspections."""
    # 1. Seed Rules
    rules_metadata = rule_engine.get_all_rules_metadata()
    for rm in rules_metadata:
        existing = db.query(Rule).filter(Rule.rule_id == rm["rule_id"]).first()
        if not existing:
            r = Rule(
                rule_id=rm["rule_id"],
                field=rm["field"],
                description=rm["description"],
                required=rm["required"],
                severity=rm["severity"],
                active=True,
                reference=rm["reference"]
            )
            db.add(r)
    db.commit()

    # 2. Seed Officer User
    demo_email = "officer@safemetric.gov.in"
    officer = db.query(User).filter(User.email == demo_email).first()
    if not officer:
        officer = User(
            name="Inspector Rajesh Kumar",
            email=demo_email,
            password_hash=hash_password("password123"),
            role="Senior Legal Metrology Inspector",
            organization="Department of Consumer Affairs, Delhi Zone",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=14)
        )
        db.add(officer)
        db.commit()
        db.refresh(officer)

    # 3. Seed Sample Images
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    demo_dir = os.path.join(backend_root, "demo_samples")
    uploads_dir = os.path.join(backend_root, "uploads")
    reports_dir = os.path.join(backend_root, "reports")
    os.makedirs(demo_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    create_sample_label_images(demo_dir)

    # 4. Seed 2 initial inspections if database has no inspections yet
    existing_inspections = db.query(Inspection).filter(Inspection.user_id == officer.id).count()
    if existing_inspections == 0:
        # Seed Demo 1: Compliant SafeRice Premium
        rice_path = os.path.join(demo_dir, "sample_saferice.png")
        rice_extracted = {
            "product_name": {"value": "SafeRice Premium Basmati", "confidence": 98.5, "status": "Found"},
            "net_quantity": {"value": "500 g", "confidence": 98.1, "status": "Found"},
            "mrp": {"value": "₹ 120 (Incl. of all taxes)", "confidence": 97.8, "status": "Found"},
            "manufacturing_date": {"value": "08/2026", "confidence": 96.5, "status": "Found"},
            "best_before": {"value": "06/2027", "confidence": 97.0, "status": "Found"},
            "manufacturer_name": {"value": "Safe Foods Pvt Ltd", "confidence": 96.8, "status": "Found"},
            "manufacturer_packer_importer": {"value": "Manufactured & Packed By", "confidence": 96.8, "status": "Found"},
            "manufacturer_address": {"value": "Plot No. 42, Food Park, Phase-1, Sonipat, Haryana - 131001", "confidence": 95.4, "status": "Found"},
            "consumer_care": {"value": "Tel: 1800-123-4567 | Email: customercare@safefoods.in", "confidence": 98.7, "status": "Found"},
            "country_of_origin": {"value": "India", "confidence": 98.4, "status": "Found"},
            "batch_number": {"value": "BATCH-SR-2026-08A", "confidence": 96.9, "status": "Found"}
        }
        
        insp1 = Inspection(
            user_id=officer.id,
            product_name="SafeRice Premium Basmati",
            image_path=rice_path,
            inspection_date=datetime.datetime.utcnow() - datetime.timedelta(days=1),
            compliance_status="COMPLIANT",
            compliance_score=100.0,
            raw_ocr_text="SafeRice Premium\nNet Quantity: 500 g\nMRP: Rs. 120 (Incl. of all taxes)\nMfg Date: 08/2026\nBest Before: 06/2027\nManufactured & Packed By: Safe Foods Pvt Ltd\nAddress: Plot No. 42, Food Park, Phase-1, Sonipat, Haryana - 131001\nConsumer Care Cell: 1800-123-4567\nCountry of Origin: India\nBatch No: BATCH-SR-2026-08A",
            extracted_data=rice_extracted,
            violations=[],
            quality_score=98.0,
            quality_notes="Excellent contrast and sharp label focus.",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
        )
        db.add(insp1)
        db.commit()
        db.refresh(insp1)

        # Fields
        for fn, fv in rice_extracted.items():
            db.add(InspectionField(
                inspection_id=insp1.id,
                field_name=fn,
                extracted_value=fv["value"],
                confidence=fv["confidence"],
                status=fv["status"]
            ))

        pdf1 = os.path.join(reports_dir, f"SafeMetric_Report_INS_{insp1.id}.pdf")
        generate_pdf_report(
            inspection_id=insp1.id,
            inspector_name=officer.name,
            product_name=insp1.product_name,
            compliance_status="COMPLIANT",
            compliance_score=100.0,
            extracted_data=rice_extracted,
            violations=[],
            avg_confidence=97.4,
            image_path=rice_path,
            output_pdf_path=pdf1
        )
        db.add(Report(inspection_id=insp1.id, report_path=pdf1))

        # Seed Demo 2: Non-Compliant Crispy Delight
        wafer_path = os.path.join(demo_dir, "sample_wafer.png")
        wafer_extracted = {
            "product_name": {"value": "Crispy Delight Wafers", "confidence": 96.0, "status": "Found"},
            "net_quantity": {"value": "Approx 200g", "confidence": 93.0, "status": "Found"},
            "mrp": {"value": "50", "confidence": 94.5, "status": "Found"},
            "manufacturing_date": {"value": "05/2026", "confidence": 91.8, "status": "Found"},
            "best_before": {"value": "4 months from packaging", "confidence": 88.0, "status": "Found"},
            "manufacturer_name": {"value": "Delight Snacks & Co", "confidence": 92.0, "status": "Found"},
            "manufacturer_packer_importer": {"value": "Manufactured by", "confidence": 92.0, "status": "Found"},
            "manufacturer_address": {"value": "Industrial Area, Pune, Maharashtra", "confidence": 89.5, "status": "Found"},
            "consumer_care": {"value": "", "confidence": 0.0, "status": "Missing"},
            "country_of_origin": {"value": "", "confidence": 0.0, "status": "Missing"},
            "batch_number": {"value": "", "confidence": 0.0, "status": "Missing"}
        }
        
        wafer_eval = rule_engine.evaluate(wafer_extracted)

        insp2 = Inspection(
            user_id=officer.id,
            product_name="Crispy Delight Wafers",
            image_path=wafer_path,
            inspection_date=datetime.datetime.utcnow() - datetime.timedelta(hours=5),
            compliance_status=wafer_eval["compliance_status"],
            compliance_score=wafer_eval["compliance_score"],
            raw_ocr_text="Crispy Delight Potato Wafers\nNet Wt: Approx 200g\nMRP: 50\nManufactured by: Delight Snacks & Co\nIndustrial Area, Pune, Maharashtra\nMfg: 05/2026\nBest Before 4 months from packaging",
            extracted_data=wafer_extracted,
            violations=wafer_eval["violations"],
            quality_score=92.0,
            quality_notes="Good resolution; some glare on packaging corner.",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=5)
        )
        db.add(insp2)
        db.commit()
        db.refresh(insp2)

        for fn, fv in wafer_extracted.items():
            db.add(InspectionField(
                inspection_id=insp2.id,
                field_name=fn,
                extracted_value=fv["value"],
                confidence=fv["confidence"],
                status=fv["status"]
            ))

        pdf2 = os.path.join(reports_dir, f"SafeMetric_Report_INS_{insp2.id}.pdf")
        generate_pdf_report(
            inspection_id=insp2.id,
            inspector_name=officer.name,
            product_name=insp2.product_name,
            compliance_status=wafer_eval["compliance_status"],
            compliance_score=wafer_eval["compliance_score"],
            extracted_data=wafer_extracted,
            violations=wafer_eval["violations"],
            avg_confidence=92.1,
            image_path=wafer_path,
            output_pdf_path=pdf2
        )
        db.add(Report(inspection_id=insp2.id, report_path=pdf2))
        db.commit()
