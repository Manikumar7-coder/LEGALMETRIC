"""
report_exporter.py
==================
SAFEMETRIC Multi-Format Report Exporter (DOCX & CSV).

Generates editable compliance inspection reports for Legal Metrology officers:
- DOCX: Formatted Word document matching the PDF statutory layout, allowing
  enforcement officers to draft notices, compoundment requests, and inspection notes.
- CSV: Flat tabular export suited for spreadsheet analysis, audit queries,
  and department-level aggregation.

Statutory Compliance:
- Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E))
- Legal Metrology Act, 2009 (Act No. 1 of 2010)
"""

import os
import csv
import datetime
from typing import Dict, Any, List, Optional

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls


def _set_cell_background(cell, hex_color: str):
    """Sets table cell background color using OXML."""
    try:
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
        cell._tc.get_or_add_tcPr().append(shd)
    except Exception:
        pass


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets internal cell margins (in dxa: 20 dxa = 1 pt)."""
    try:
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(
            f'<w:tcMar {nsdecls("w")}>'
            f'<w:top w:w="{top}" w:type="dxa"/>'
            f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
            f'<w:left w:w="{left}" w:type="dxa"/>'
            f'<w:right w:w="{right}" w:type="dxa"/>'
            f'</w:tcMar>'
        )
        tcPr.append(tcMar)
    except Exception:
        pass


def export_report_docx(
    inspection_data: Dict[str, Any],
    output_path: str,
    inspector_name: Optional[str] = None
) -> str:
    """
    Generates an editable Microsoft Word (.docx) inspection report.
    """
    doc = Document()

    # Set 0.75-inch page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Color definitions
    NAVY = RGBColor(15, 39, 68)       # #0F2744
    GREEN = RGBColor(5, 150, 105)     # #059669
    RED = RGBColor(220, 38, 38)       # #DC2626
    AMBER = RGBColor(217, 119, 6)     # #D97706
    GRAY = RGBColor(100, 116, 139)    # #64748B
    DARK = RGBColor(30, 41, 59)       # #1E293B

    # Header / Title Block
    p_header = doc.add_paragraph()
    p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p_header.add_run("GOVERNMENT OF INDIA\n")
    r1.font.size = Pt(10)
    r1.font.bold = True
    r1.font.color.rgb = GRAY

    r2 = p_header.add_run("MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION\nDEPARTMENT OF CONSUMER AFFAIRS — LEGAL METROLOGY DIVISION\n")
    r2.font.size = Pt(9)
    r2.font.color.rgb = GRAY

    r3 = p_header.add_run("STATUTORY PACKAGING COMPLIANCE INSPECTION REPORT\n")
    r3.font.size = Pt(15)
    r3.font.bold = True
    r3.font.color.rgb = NAVY

    r4 = p_header.add_run("Legal Metrology (Packaged Commodities) Rules, 2011 & Legal Metrology Act, 2009\n")
    r4.font.size = Pt(9)
    r4.font.italic = True
    r4.font.color.rgb = GRAY

    # Metadata Summary Table
    t_meta = doc.add_table(rows=3, cols=2)
    t_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_meta.autofit = False

    insp_id = str(inspection_data.get("inspection_id") or inspection_data.get("id") or "N/A")
    prod_name = str(inspection_data.get("product_name") or "Packaged Commodity")
    created_at = inspection_data.get("created_at") or inspection_data.get("inspection_date") or datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    officer = inspector_name or inspection_data.get("inspector_name") or "Legal Metrology Officer"
    comp_status = str(inspection_data.get("compliance_status") or "REVIEW REQUIRED")
    comp_score = inspection_data.get("compliance_score", 0.0)

    meta_cells = [
        ("Inspection Reference:", insp_id, "Product Name:", prod_name),
        ("Inspection Date / Time:", str(created_at)[:19], "Inspecting Officer:", officer),
        ("Compliance Determination:", comp_status, "Compliance Score:", f"{comp_score}%")
    ]

    for row_idx, (k1, v1, k2, v2) in enumerate(meta_cells):
        row = t_meta.rows[row_idx]
        c0, c1 = row.cells[0], row.cells[1]
        
        # Left column
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(2)
        r = p0.add_run(f"{k1} ")
        r.font.bold = True
        r.font.size = Pt(9.5)
        p0.add_run(f"{v1}").font.size = Pt(9.5)

        # Right column
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(2)
        r = p1.add_run(f"{k2} ")
        r.font.bold = True
        r.font.size = Pt(9.5)
        r_val = p1.add_run(f"{v2}")
        r_val.font.size = Pt(9.5)
        if "Determination" in k2 or "Status" in k1:
            r_val.font.bold = True
            if "COMPLIANT" in str(v2).upper() and "NON" not in str(v2).upper() and "REVIEW" not in str(v2).upper():
                r_val.font.color.rgb = GREEN
            elif "NON" in str(v2).upper() or "FAIL" in str(v2).upper():
                r_val.font.color.rgb = RED
            else:
                r_val.font.color.rgb = AMBER

        _set_cell_background(c0, "F8FAFC")
        _set_cell_background(c1, "F8FAFC")
        _set_cell_margins(c0, top=60, bottom=60, left=100, right=100)
        _set_cell_margins(c1, top=60, bottom=60, left=100, right=100)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 1. Executive Summary Table
    h1 = doc.add_paragraph()
    r = h1.add_run("1. Executive Compliance Summary")
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = NAVY
    h1.paragraph_format.space_after = Pt(4)

    rule_results = inspection_data.get("rule_results") or []
    passed_n = sum(1 for r in rule_results if (r.get("status") if isinstance(r, dict) else getattr(r, "status", "")) == "PASS")
    failed_n = sum(1 for r in rule_results if (r.get("status") if isinstance(r, dict) else getattr(r, "status", "")) == "FAIL")
    review_n = sum(1 for r in rule_results if (r.get("status") if isinstance(r, dict) else getattr(r, "status", "")) == "NEEDS_REVIEW")
    na_n = sum(1 for r in rule_results if (r.get("status") if isinstance(r, dict) else getattr(r, "status", "")) == "NOT_APPLICABLE")

    t_exec = doc.add_table(rows=2, cols=5)
    t_exec.alignment = WD_TABLE_ALIGNMENT.CENTER
    exec_headers = ["Total Rules", "Passed Checks", "Failed Infractions", "Review Required", "Not Applicable"]
    exec_vals = [str(len(rule_results)), str(passed_n), str(failed_n), str(review_n), str(na_n)]

    for i, title in enumerate(exec_headers):
        c = t_exec.rows[0].cells[i]
        c.paragraphs[0].paragraph_format.space_after = Pt(2)
        run = c.paragraphs[0].add_run(title)
        run.font.bold = True
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
        _set_cell_background(c, "0F2744")
        _set_cell_margins(c, top=80, bottom=80, left=80, right=80)

    for i, val in enumerate(exec_vals):
        c = t_exec.rows[1].cells[i]
        c.paragraphs[0].paragraph_format.space_after = Pt(2)
        run = c.paragraphs[0].add_run(val)
        run.font.bold = True
        run.font.size = Pt(11)
        if i == 1:
            run.font.color.rgb = GREEN
        elif i == 2:
            run.font.color.rgb = RED if failed_n > 0 else GRAY
        elif i == 3:
            run.font.color.rgb = AMBER if review_n > 0 else GRAY
        _set_cell_background(c, "FFFFFF")
        _set_cell_margins(c, top=80, bottom=80, left=80, right=80)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 2. Mandatory Declarations Audit Table
    h2 = doc.add_paragraph()
    r = h2.add_run("2. Mandatory Declarations Audit (Rule 6, PCR 2011)")
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = NAVY
    h2.paragraph_format.space_after = Pt(4)

    ext_data = inspection_data.get("extracted_data") or {}
    fields_list = []
    if isinstance(ext_data, dict):
        for k, v in ext_data.items():
            if k.startswith("_") or k in ("font_analysis", "placement_analysis", "dimensions"):
                continue
            if isinstance(v, dict):
                fields_list.append((k, v))

    t_decl = doc.add_table(rows=len(fields_list) + 1, cols=4)
    t_decl.alignment = WD_TABLE_ALIGNMENT.CENTER
    decl_headers = ["Statutory Field", "Extracted Value", "Confidence", "Status"]

    for i, title in enumerate(decl_headers):
        c = t_decl.rows[0].cells[i]
        run = c.paragraphs[0].add_run(title)
        run.font.bold = True
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
        _set_cell_background(c, "0F2744")
        _set_cell_margins(c, top=80, bottom=80, left=80, right=80)

    for row_idx, (f_name, f_dict) in enumerate(fields_list, start=1):
        row = t_decl.rows[row_idx]
        val = str(f_dict.get("value") or "Missing")
        conf = f"{float(f_dict.get('confidence', 0.0)):.1f}%"
        stat = str(f_dict.get("status") or "Unknown")

        row.cells[0].paragraphs[0].add_run(f_name.replace("_", " ").title()).font.size = Pt(8.5)
        row.cells[1].paragraphs[0].add_run(val[:80] + ("..." if len(val) > 80 else "")).font.size = Pt(8.5)
        row.cells[2].paragraphs[0].add_run(conf).font.size = Pt(8.5)

        r_st = row.cells[3].paragraphs[0].add_run(stat)
        r_st.font.bold = True
        r_st.font.size = Pt(8.5)
        if stat in ("Found", "PASS"):
            r_st.font.color.rgb = GREEN
        elif stat in ("Missing", "FAIL"):
            r_st.font.color.rgb = RED
        else:
            r_st.font.color.rgb = AMBER

        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for c in row.cells:
            _set_cell_background(c, bg)
            _set_cell_margins(c, top=60, bottom=60, left=80, right=80)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 3. Font Size & Readability Analysis (Rule 7, PCR 2011)
    font_res = ext_data.get("font_analysis") if isinstance(ext_data, dict) else None
    if font_res and isinstance(font_res, dict):
        h3 = doc.add_paragraph()
        r = h3.add_run("3. Font Size & Label Readability Analysis (Rule 7, PCR 2011)")
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = NAVY
        h3.paragraph_format.space_after = Pt(4)

        font_fields = font_res.get("fields", {})
        t_font = doc.add_table(rows=len(font_fields) + 1, cols=5)
        t_font.alignment = WD_TABLE_ALIGNMENT.CENTER
        font_headers = ["Declaration", "Measured Height", "Rule 7 Min", "Scale / Method", "Verdict"]

        for i, title in enumerate(font_headers):
            c = t_font.rows[0].cells[i]
            run = c.paragraphs[0].add_run(title)
            run.font.bold = True
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(255, 255, 255)
            _set_cell_background(c, "0F2744")
            _set_cell_margins(c, top=80, bottom=80, left=80, right=80)

        method = str(font_res.get("estimation_method", "Statistical Heuristic"))[:18]
        conf_val = int(font_res.get("confidence", 0.6) * 100)

        for row_idx, (fk, fv) in enumerate(font_fields.items(), start=1):
            row = t_font.rows[row_idx]
            lbl = fv.get("field_label") or fk
            h_mm = f"{fv.get('char_height_mm'):.1f} mm" if fv.get("char_height_mm") is not None else "N/A"
            req_mm = f"{fv.get('min_required_mm'):.1f} mm" if fv.get("min_required_mm") is not None else "1.0 mm"
            st = str(fv.get("status") or "NEEDS_REVIEW")

            row.cells[0].paragraphs[0].add_run(lbl).font.size = Pt(8.5)
            row.cells[1].paragraphs[0].add_run(h_mm).font.size = Pt(8.5)
            row.cells[2].paragraphs[0].add_run(req_mm).font.size = Pt(8.5)
            row.cells[3].paragraphs[0].add_run(f"{conf_val}% ({method})").font.size = Pt(8.5)

            r_st = row.cells[4].paragraphs[0].add_run(st)
            r_st.font.bold = True
            r_st.font.size = Pt(8.5)
            if st == "PASS":
                r_st.font.color.rgb = GREEN
            elif st == "FAIL":
                r_st.font.color.rgb = RED
            else:
                r_st.font.color.rgb = AMBER

            bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
            for c in row.cells:
                _set_cell_background(c, bg)
                _set_cell_margins(c, top=60, bottom=60, left=80, right=80)

        if font_res.get("limitations"):
            p_lim = doc.add_paragraph()
            p_lim.paragraph_format.space_before = Pt(2)
            p_lim.paragraph_format.space_after = Pt(4)
            r = p_lim.add_run(f"Technical Notice: {font_res.get('limitations')}")
            r.font.size = Pt(8)
            r.font.italic = True
            r.font.color.rgb = GRAY

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 4. Declaration Placement & Grouping (Rule 8, PCR 2011)
    placement_res = ext_data.get("placement_analysis") if isinstance(ext_data, dict) else None
    if placement_res and isinstance(placement_res, dict):
        h4 = doc.add_paragraph()
        r = h4.add_run("4. Declaration Placement & Grouping (Rule 8, PCR 2011)")
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = NAVY
        h4.paragraph_format.space_after = Pt(4)

        grp = placement_res.get("grouping", {})
        cs = placement_res.get("clear_space", {})

        t_plc = doc.add_table(rows=3, cols=4)
        t_plc.alignment = WD_TABLE_ALIGNMENT.CENTER
        plc_headers = ["Rule 8 Dimension", "Statutory Standard", "Inspection Finding", "Verdict"]

        for i, title in enumerate(plc_headers):
            c = t_plc.rows[0].cells[i]
            run = c.paragraphs[0].add_run(title)
            run.font.bold = True
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(255, 255, 255)
            _set_cell_background(c, "0F2744")
            _set_cell_margins(c, top=80, bottom=80, left=80, right=80)

        # Row 1: PDP Grouping
        row1 = t_plc.rows[1]
        row1.cells[0].paragraphs[0].add_run("PDP Spatial Grouping\n(Rule 8(1) & 8(2))").font.size = Pt(8.5)
        row1.cells[1].paragraphs[0].add_run("Core declarations must appear grouped on Principal Display Panel").font.size = Pt(8.5)
        row1.cells[2].paragraphs[0].add_run(grp.get("explanation", "Evaluated from declaration coordinates")[:110]).font.size = Pt(8.5)
        r_grp = row1.cells[3].paragraphs[0].add_run(grp.get("status", "NEEDS_REVIEW"))
        r_grp.font.bold = True
        r_grp.font.size = Pt(8.5)
        r_grp.font.color.rgb = GREEN if grp.get("status") == "PASS" else (RED if grp.get("status") == "FAIL" else AMBER)
        for c in row1.cells:
            _set_cell_background(c, "FFFFFF")
            _set_cell_margins(c, top=60, bottom=60, left=80, right=80)

        # Row 2: Clear Space
        row2 = t_plc.rows[2]
        row2.cells[0].paragraphs[0].add_run("Net Qty Clear Space\n(Rule 8(1) Proviso)").font.size = Pt(8.5)
        row2.cells[1].paragraphs[0].add_run("Free from print: 1x numeral height above/below, 2x left/right").font.size = Pt(8.5)
        row2.cells[2].paragraphs[0].add_run(cs.get("explanation", "Clear zone audit surrounding net quantity")[:110]).font.size = Pt(8.5)
        r_cs = row2.cells[3].paragraphs[0].add_run(cs.get("status", "NEEDS_REVIEW"))
        r_cs.font.bold = True
        r_cs.font.size = Pt(8.5)
        r_cs.font.color.rgb = GREEN if cs.get("status") == "PASS" else (RED if cs.get("status") == "FAIL" else AMBER)
        for c in row2.cells:
            _set_cell_background(c, "F8FAFC")
            _set_cell_margins(c, top=60, bottom=60, left=80, right=80)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 5. Statutory Violations & Non-Compliance Infractions
    violations = inspection_data.get("violations") or []
    h5 = doc.add_paragraph()
    r = h5.add_run("5. Statutory Violations & Non-Compliance Infractions")
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = NAVY
    h5.paragraph_format.space_after = Pt(4)

    if violations:
        t_viol = doc.add_table(rows=len(violations) + 1, cols=4)
        t_viol.alignment = WD_TABLE_ALIGNMENT.CENTER
        viol_headers = ["#", "Field / Subject", "Violation & Legal Citation", "Severity"]

        for i, title in enumerate(viol_headers):
            c = t_viol.rows[0].cells[i]
            run = c.paragraphs[0].add_run(title)
            run.font.bold = True
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(255, 255, 255)
            _set_cell_background(c, "0F2744")
            _set_cell_margins(c, top=80, bottom=80, left=80, right=80)

        for idx, v in enumerate(violations, start=1):
            row = t_viol.rows[idx]
            fld = v.get("field") or "Packaging"
            iss = v.get("issue") or "Statutory infraction identified"
            cit = v.get("rule_reference") or v.get("rule_id") or "PCR, 2011"
            sev = v.get("severity") or "HIGH"

            row.cells[0].paragraphs[0].add_run(str(idx)).font.size = Pt(8.5)
            row.cells[1].paragraphs[0].add_run(fld).font.size = Pt(8.5)
            
            p_desc = row.cells[2].paragraphs[0]
            p_desc.add_run(f"{iss}\n").font.size = Pt(8.5)
            r_cit = p_desc.add_run(f"Citation: {cit}")
            r_cit.font.bold = True
            r_cit.font.size = Pt(8)
            r_cit.font.color.rgb = RGBColor(30, 64, 175)

            r_sev = row.cells[3].paragraphs[0].add_run(sev)
            r_sev.font.bold = True
            r_sev.font.size = Pt(8.5)
            r_sev.font.color.rgb = RED if sev in ("HIGH", "CRITICAL") else AMBER

            bg = "FFFFFF" if idx % 2 != 0 else "F8FAFC"
            for c in row.cells:
                _set_cell_background(c, bg)
                _set_cell_margins(c, top=60, bottom=60, left=80, right=80)
    else:
        p_noviol = doc.add_paragraph()
        r = p_noviol.add_run("No statutory violations or legal infractions identified in evaluated declarations.")
        r.font.size = Pt(9.5)
        r.font.color.rgb = GREEN

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 6. Officer Sign-off & Enforcement Notice Block
    p_sign = doc.add_paragraph()
    p_sign.paragraph_format.space_before = Pt(8)
    p_sign.paragraph_format.space_after = Pt(2)
    r = p_sign.add_run("6. Officer Verification & Sign-off Block")
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = NAVY

    t_sign = doc.add_table(rows=2, cols=2)
    t_sign.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_sign.rows[0].cells[0].paragraphs[0].add_run(f"Inspecting Officer: {officer}\nDesignation: Legal Metrology Inspector\nDepartment: Consumer Affairs").font.size = Pt(9)
    t_sign.rows[0].cells[1].paragraphs[0].add_run("Official Stamp & Signature:\n\n__________________________________").font.size = Pt(9)
    t_sign.rows[1].cells[0].paragraphs[0].add_run(f"Report Generated: {str(created_at)[:19]}").font.size = Pt(8.5)
    t_sign.rows[1].cells[1].paragraphs[0].add_run("Action Proposed: [ ] Notice Issued  [ ] Compounding  [ ] Cleared").font.size = Pt(8.5)

    for row in t_sign.rows:
        for c in row.cells:
            _set_cell_background(c, "F8FAFC")
            _set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    # 7. Statutory Disclaimer
    p_disc = doc.add_paragraph()
    p_disc.paragraph_format.space_before = Pt(10)
    r = p_disc.add_run(
        "STATUTORY NOTICE: SafeMetric provides automated optical compliance assistance under the Legal Metrology "
        "Act, 2009 and the Legal Metrology (Packaged Commodities) Rules, 2011. Final statutory notice issuance, compounding, "
        "or seizure remains strictly subject to designated Legal Metrology officer verification under Section 15 of the Act."
    )
    r.font.size = Pt(7.5)
    r.font.italic = True
    r.font.color.rgb = GRAY

    doc.save(output_path)
    return output_path


def export_report_csv(
    inspection_data: Dict[str, Any],
    output_path: str,
    inspector_name: Optional[str] = None
) -> str:
    """
    Generates a flat tabular CSV audit export suitable for spreadsheet analysis.
    One row per statutory declaration field evaluated.
    """
    insp_id = str(inspection_data.get("inspection_id") or inspection_data.get("id") or "N/A")
    prod_name = str(inspection_data.get("product_name") or "Packaged Commodity")
    created_at = str(inspection_data.get("created_at") or inspection_data.get("inspection_date") or datetime.datetime.utcnow())[:19]
    officer = inspector_name or inspection_data.get("inspector_name") or "Legal Metrology Officer"
    comp_status = str(inspection_data.get("compliance_status") or "REVIEW REQUIRED")
    comp_score = float(inspection_data.get("compliance_score", 0.0))

    ext_data = inspection_data.get("extracted_data") or {}
    font_data = ext_data.get("font_analysis") or {}
    font_fields = font_data.get("fields") or {}
    placement_data = ext_data.get("placement_analysis") or {}
    grp_status = placement_data.get("grouping", {}).get("status", "N/A")
    cs_status = placement_data.get("clear_space", {}).get("status", "N/A")

    violations = inspection_data.get("violations") or []
    viol_count = len(violations)
    viol_summary = "; ".join(f"{v.get('field')}: {v.get('issue')}" for v in violations if isinstance(v, dict)) if violations else "None"

    headers = [
        "inspection_id",
        "inspection_timestamp",
        "inspector_name",
        "product_name",
        "overall_compliance_status",
        "overall_compliance_score",
        "field_name",
        "extracted_value",
        "optical_confidence",
        "field_status",
        "font_char_height_mm",
        "font_min_required_mm",
        "font_status",
        "pdp_grouping_status",
        "clear_space_status",
        "total_violations_count",
        "violations_summary"
    ]

    rows = []
    # Collect fields
    fields_list = []
    if isinstance(ext_data, dict):
        for k, v in ext_data.items():
            if k.startswith("_") or k in ("font_analysis", "placement_analysis", "dimensions"):
                continue
            if isinstance(v, dict):
                fields_list.append((k, v))

    if not fields_list:
        # Single row if no extracted fields
        rows.append([
            insp_id, created_at, officer, prod_name, comp_status, comp_score,
            "None", "None", 0.0, "Missing",
            None, None, "N/A",
            grp_status, cs_status, viol_count, viol_summary
        ])
    else:
        for f_name, f_dict in fields_list:
            val = str(f_dict.get("value") or "")
            conf = float(f_dict.get("confidence", 0.0))
            stat = str(f_dict.get("status") or "Unknown")

            f_font = font_fields.get(f_name) or {}
            font_h = f_font.get("char_height_mm")
            font_req = f_font.get("min_required_mm")
            font_st = f_font.get("status", "N/A")

            rows.append([
                insp_id,
                created_at,
                officer,
                prod_name,
                comp_status,
                comp_score,
                f_name,
                val,
                conf,
                stat,
                font_h,
                font_req,
                font_st,
                grp_status,
                cs_status,
                viol_count,
                viol_summary
            ])

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    return output_path
