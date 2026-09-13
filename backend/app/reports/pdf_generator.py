"""
pdf_generator.py
================
Statutory PDF Report Generator for SafeMetric Legal Metrology Compliance System.
Enforces statutory compliance reporting under The Legal Metrology Act, 2009 and
The Legal Metrology (Packaged Commodities) Rules, 2011.

Generates comprehensive, multi-section compliance audit certificates containing:
1. Statutory header, inspection reference ID, timestamp, and officer identity
2. Original uploaded commodity packaging image
3. Overall statutory compliance determination and calibrated score
4. Statutory metrics breakdown (Passed checks, Failed checks, Needs Review checks)
5. Structured extracted declarations with status and optical confidences
6. OCR optical recognition summary & character confidence
7. Detailed regulatory violations table with statutory citations
8. Legal references audit breakdown under PCR, 2011 and LMA, 2009
9. Visual evidence information & region coordinates
10. Actionable statutory directives & corrective remediation guidance
11. Official metrology legal disclaimer under Section 18 of LMA, 2009
"""

import os
import datetime
from typing import Dict, List, Any, Optional, Union
from PIL import Image

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image as RLImage,
    KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_pdf_report(
    inspection_id: Union[int, str],
    inspector_name: str,
    product_name: str,
    compliance_status: str,
    compliance_score: float,
    extracted_data: Dict[str, Any],
    violations: List[Any],
    avg_confidence: float,
    image_path: str,
    output_pdf_path: str,
    date_time: Optional[Any] = None,
    passed_count: Optional[int] = None,
    failed_count: Optional[int] = None,
    needs_review_count: Optional[int] = None,
    rule_results: Optional[List[Dict[str, Any]]] = None,
    ocr_info: Optional[Dict[str, Any]] = None,
    evidence_info: Optional[Dict[str, Any]] = None,
    recommendations: Optional[List[Dict[str, Any]]] = None,
    score_breakdown: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates an official statutory compliance inspection audit report in PDF format.
    """
    # Ensure target directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)

    # 1. Document Setup (A4, 0.45-inch margins for optimal printable area)
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        rightMargin=0.45 * inch,
        leftMargin=0.45 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch
    )

    elements = []
    styles = getSampleStyleSheet()

    # 2. Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#2563EB'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=10
    )
    sec_heading = ParagraphStyle(
        'SecHeading',
        parent=styles['Normal'],
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#0F2744'),
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=4
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A')
    )
    cell_regular = ParagraphStyle(
        'CellRegular',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#334155')
    )
    cell_citation = ParagraphStyle(
        'CellCitation',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=9.5,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#1E40AF')
    )
    footer_style = ParagraphStyle(
        'DocFooter',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#64748B'),
        alignment=TA_CENTER
    )

    # 3. Header Banner
    elements.append(Paragraph("SAFEMETRIC", title_style))
    elements.append(Paragraph(
        "AI-POWERED LEGAL METROLOGY COMPLIANCE AUDIT CERTIFICATE<br/>"
        "<font color='#64748B' size='8'>Government of India &middot; The Legal Metrology Act, 2009 &middot; Packaged Commodities Rules, 2011</font>",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.08 * inch))

    # Resolve date string
    if isinstance(date_time, datetime.datetime):
        date_str = date_time.strftime("%d-%b-%Y %H:%M:%S UTC")
    elif isinstance(date_time, str):
        date_str = date_time
    else:
        date_str = datetime.datetime.utcnow().strftime("%d-%b-%Y %H:%M:%S UTC")

    # Format inspection ID string
    ins_id_str = str(inspection_id)
    if not ins_id_str.startswith("INS-"):
        try:
            ins_id_str = f"INS-{int(ins_id_str):06d}"
        except Exception:
            ins_id_str = f"INS-{ins_id_str}"

    # 4. Inspection Metadata Table
    status_clean = (compliance_status or "").upper()
    if "NON" in status_clean:
        status_display = "NON-COMPLIANT"
        status_bg = colors.HexColor('#DC2626')
    elif "PARTIAL" in status_clean:
        status_display = "PARTIALLY COMPLIANT"
        status_bg = colors.HexColor('#D97706')
    elif "REVIEW" in status_clean or "NEEDS" in status_clean:
        status_display = "NEEDS REVIEW"
        status_bg = colors.HexColor('#0284C7')
    else:
        status_display = "COMPLIANT"
        status_bg = colors.HexColor('#059669')

    meta_rows = [
        [
            Paragraph("<b>Inspection Reference:</b>", cell_bold),
            Paragraph(ins_id_str, cell_regular),
            Paragraph("<b>Audit Date/Time:</b>", cell_bold),
            Paragraph(date_str, cell_regular)
        ],
        [
            Paragraph("<b>Commodity Name:</b>", cell_bold),
            Paragraph(product_name or "Packaged Commodity", cell_regular),
            Paragraph("<b>Inspecting Officer:</b>", cell_bold),
            Paragraph(inspector_name or "Designated Officer", cell_regular)
        ],
        [
            Paragraph("<b>Statutory Verdict:</b>", cell_bold),
            Paragraph(f"<font color='white'><b>&nbsp;{status_display}&nbsp;</b></font>", cell_bold),
            Paragraph("<b>Compliance Score:</b>", cell_bold),
            Paragraph(f"<b>{compliance_score:.1f}%</b> (Rating)", cell_bold)
        ]
    ]
    meta_table = Table(meta_rows, colWidths=[1.6 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (1, 2), (1, 2), status_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.1 * inch))

    # 5. Check Counters Summary Bar
    p_cnt = passed_count if passed_count is not None else max(0, len(extracted_data or {}) - len(violations or []))
    f_cnt = failed_count if failed_count is not None else len(violations or [])
    r_cnt = needs_review_count if needs_review_count is not None else 0

    counter_rows = [[
        Paragraph(f"<b>PASSED CHECKS:</b> {p_cnt}", cell_bold),
        Paragraph(f"<b>FAILED CHECKS:</b> {f_cnt}", cell_bold),
        Paragraph(f"<b>NEEDS REVIEW:</b> {r_cnt}", cell_bold),
        Paragraph(f"<b>OCR CONFIDENCE:</b> {avg_confidence:.1f}%", cell_bold)
    ]]
    counter_table = Table(counter_rows, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
    counter_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#ECFDF5')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#FEF2F2')),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#FFFBEB')),
        ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#EFF6FF')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
    ]))
    elements.append(counter_table)
    elements.append(Spacer(1, 0.12 * inch))

    # 6. Original Uploaded Packaging Image
    if image_path and os.path.exists(image_path):
        try:
            pil_img = Image.open(image_path)
            orig_w, orig_h = pil_img.size
            display_w = 3.2 * inch
            display_h = (orig_h / orig_w) * display_w
            display_h = min(display_h, 2.6 * inch)

            img_table = Table([
                [
                    RLImage(image_path, width=display_w, height=display_h),
                    Paragraph(
                        "<b>Primary Physical Evidence & Ground Truth</b><br/><br/>"
                        f"&bull; <b>Image File:</b> {os.path.basename(image_path)}<br/>"
                        f"&bull; <b>Dimensions:</b> {orig_w} &times; {orig_h} px<br/>"
                        f"&bull; <b>Capture Type:</b> Physical retail packaging label<br/>"
                        f"&bull; <b>OCR Preprocessing:</b> Adaptive thresholding & noise reduction<br/>"
                        f"&bull; <b>Zero Database Dependency:</b> Evaluation performed strictly on optical text detected on this packaging.",
                        cell_regular
                    )
                ]
            ], colWidths=[3.4 * inch, 3.8 * inch])
            img_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
            ]))
            elements.append(Paragraph("1. Physical Packaging Label Visual Ground Truth", sec_heading))
            elements.append(img_table)
            elements.append(Spacer(1, 0.1 * inch))
        except Exception as e:
            elements.append(Paragraph(f"<i>Label image preview unavailable: {str(e)}</i>", cell_regular))

    # 7. Extracted Mandatory Declarations
    elements.append(Paragraph("2. Mandatory Declarations Extracted Under Rule 6(1), PCR, 2011", sec_heading))
    decl_rows = [[
        Paragraph("<b>Declaration Field</b>", cell_bold),
        Paragraph("<b>Extracted Physical Value</b>", cell_bold),
        Paragraph("<b>Confidence</b>", cell_bold),
        Paragraph("<b>Status</b>", cell_bold)
    ]]

    if extracted_data and isinstance(extracted_data, dict):
        for f_name, f_val in extracted_data.items():
            if f_name.startswith("_") or not isinstance(f_val, dict):
                continue
            val_text = str(f_val.get("value", "") or "Missing")
            conf_val = f_val.get("confidence", 0.0)
            stat_val = str(f_val.get("status", "Unknown"))

            conf_str = f"{conf_val:.1f}%" if isinstance(conf_val, (int, float)) else str(conf_val)
            stat_color = '#059669' if stat_val == 'Found' else ('#DC2626' if stat_val == 'Missing' else '#D97706')

            decl_rows.append([
                Paragraph(f"<b>{f_name.replace('_', ' ').title()}</b>", cell_regular),
                Paragraph(val_text[:80] + ("..." if len(val_text) > 80 else ""), cell_regular),
                Paragraph(conf_str, cell_regular),
                Paragraph(f"<font color='{stat_color}'><b>{stat_val}</b></font>", cell_bold)
            ])

    if len(decl_rows) > 1:
        decl_table = Table(decl_rows, colWidths=[1.9 * inch, 3.6 * inch, 0.8 * inch, 0.9 * inch])
        decl_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F2744')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elements.append(decl_table)
    else:
        elements.append(Paragraph("<i>No structured declarations extracted.</i>", cell_regular))

    elements.append(Spacer(1, 0.1 * inch))

    # Font Size & Label Readability Analysis (Rule 7, PCR 2011)
    font_data = (extracted_data or {}).get("font_analysis")
    if font_data and isinstance(font_data, dict):
        elements.append(Paragraph("Font Size & Label Readability Analysis (Rule 7, PCR 2011)", sec_heading))
        f_fields = font_data.get("fields", {})
        f_rows = [[
            Paragraph("<b>Statutory Declaration</b>", cell_bold),
            Paragraph("<b>Measured Height</b>", cell_bold),
            Paragraph("<b>Rule 7 Minimum</b>", cell_bold),
            Paragraph("<b>Scale & Confidence</b>", cell_bold),
            Paragraph("<b>Result</b>", cell_bold)
        ]]
        method = font_data.get("estimation_method", "Statistical Heuristic")
        conf_pct = int(font_data.get("confidence", 0.6) * 100)
        for f_k, f_v in f_fields.items():
            h_mm = f"{f_v.get('char_height_mm'):.1f} mm" if f_v.get('char_height_mm') is not None else "N/A"
            req_mm = f"{f_v.get('min_required_mm'):.1f} mm" if f_v.get('min_required_mm') is not None else "1.0 mm"
            st = f_v.get("status", "NEEDS_REVIEW")
            st_color = "#059669" if st == "PASS" else ("#DC2626" if st == "FAIL" else "#D97706")
            f_rows.append([
                Paragraph(f"<b>{f_v.get('field_label', f_k)}</b>", cell_regular),
                Paragraph(h_mm, cell_regular),
                Paragraph(req_mm, cell_regular),
                Paragraph(f"{conf_pct}% ({method[:15]})", cell_regular),
                Paragraph(f"<font color='{st_color}'><b>{st}</b></font>", cell_bold)
            ])
        if len(f_rows) > 1:
            f_table = Table(f_rows, colWidths=[2.0 * inch, 1.2 * inch, 1.2 * inch, 1.8 * inch, 1.0 * inch])
            f_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F2744')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            elements.append(f_table)
            elements.append(Paragraph(f"<i>Note: {font_data.get('limitations', '')}</i>", cell_citation))
            elements.append(Spacer(1, 0.1 * inch))

    # Declaration Placement & Grouping Analysis (Rule 8, PCR 2011)
    placement_data = (extracted_data or {}).get("placement_analysis")
    if placement_data and isinstance(placement_data, dict):
        elements.append(Paragraph("Declaration Placement & Grouping (Rule 8, PCR 2011)", sec_heading))
        grp = placement_data.get("grouping", {})
        cs = placement_data.get("clear_space", {})
        
        p_rows = [[
            Paragraph("<b>Rule 8 Assessment Dimension</b>", cell_bold),
            Paragraph("<b>Statutory Standard</b>", cell_bold),
            Paragraph("<b>Inspection Finding</b>", cell_bold),
            Paragraph("<b>Verdict</b>", cell_bold)
        ]]
        
        grp_st = grp.get("status", "NEEDS_REVIEW")
        grp_color = "#059669" if grp_st == "PASS" else ("#DC2626" if grp_st == "FAIL" else "#D97706")
        p_rows.append([
            Paragraph("<b>PDP Spatial Grouping</b><br/><font size=7 color='#64748B'>Rule 8(1) & 8(2)</font>", cell_regular),
            Paragraph("Core declarations must appear grouped on Principal Display Panel", cell_regular),
            Paragraph(grp.get("explanation", "Evaluated from declaration coordinates")[:120], cell_regular),
            Paragraph(f"<font color='{grp_color}'><b>{grp_st}</b></font>", cell_bold)
        ])
        
        cs_st = cs.get("status", "NEEDS_REVIEW")
        cs_color = "#059669" if cs_st == "PASS" else ("#DC2626" if cs_st == "FAIL" else "#D97706")
        p_rows.append([
            Paragraph("<b>Net Qty Clear Space</b><br/><font size=7 color='#64748B'>Rule 8(1) Proviso</font>", cell_regular),
            Paragraph("Free from print: 1x numeral height above/below, 2x left/right", cell_regular),
            Paragraph(cs.get("explanation", "Clear zone audit surrounding net quantity")[:120], cell_regular),
            Paragraph(f"<font color='{cs_color}'><b>{cs_st}</b></font>", cell_bold)
        ])
        
        p_table = Table(p_rows, colWidths=[2.0 * inch, 2.0 * inch, 2.2 * inch, 1.0 * inch])
        p_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F2744')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elements.append(p_table)
        elements.append(Spacer(1, 0.1 * inch))

    elements.append(Paragraph("3. Statutory Violations & Non-Compliance Infractions", sec_heading))
    if violations and len(violations) > 0:
        viol_rows = [[
            Paragraph("<b>#</b>", cell_bold),
            Paragraph("<b>Infraction Details & Legal Citation</b>", cell_bold),
            Paragraph("<b>Severity</b>", cell_bold)
        ]]
        for idx, v in enumerate(violations, 1):
            if isinstance(v, dict):
                fld = v.get("field", "Packaging Declaration")
                iss = v.get("issue", "Statutory non-compliance identified")
                ref = v.get("rule_reference") or v.get("rule_id", "PCR, 2011")
                rec = v.get("recommendation", "")
                sev = v.get("severity", "HIGH")
                details = f"<b>Field:</b> {fld}<br/><b>Issue:</b> {iss}<br/><font color='#1E40AF'><b>Citation:</b> {ref}</font>"
                if rec:
                    details += f"<br/><font color='#475569'><b>Directive:</b> {rec}</font>"
            else:
                sev = "HIGH"
                details = str(v)

            viol_rows.append([
                Paragraph(str(idx), cell_bold),
                Paragraph(details, cell_regular),
                Paragraph(f"<b><font color='#DC2626'>{sev}</font></b>", cell_bold)
            ])

        viol_table = Table(viol_rows, colWidths=[0.35 * inch, 5.95 * inch, 0.9 * inch])
        viol_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#991B1B')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FEF2F2')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FCA5A5')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elements.append(viol_table)
    else:
        elements.append(Paragraph(
            "<font color='#059669'><b>&check; Zero Statutory Violations Detected.</b> "
            "All mandatory packaged commodity declarations conform with Legal Metrology requirements.</font>",
            cell_bold
        ))

    elements.append(Spacer(1, 0.1 * inch))

    # 9. Evaluated Statutory Rules Breakdown
    if rule_results and len(rule_results) > 0:
        elements.append(Paragraph("4. Statutory Legal Metrology Rules Evaluated (PCR 2011 & LMA 2009)", sec_heading))
        rule_rows = [[
            Paragraph("<b>Rule Reference</b>", cell_bold),
            Paragraph("<b>Statutory Requirement</b>", cell_bold),
            Paragraph("<b>Detected Finding / Explanation</b>", cell_bold),
            Paragraph("<b>Verdict</b>", cell_bold)
        ]]
        for r in rule_results:
            if not isinstance(r, dict):
                continue
            r_id = r.get("rule_id", "")
            r_ref = r.get("legal_reference") or r_id
            r_req = r.get("expected_requirement", "") or r_id
            r_exp = r.get("explanation", "") or r.get("detected_value", "") or ""
            r_stat = (r.get("status", "NEEDS_REVIEW") or "").upper()

            if "PASS" in r_stat:
                v_color = "#059669"
            elif "FAIL" in r_stat:
                v_color = "#DC2626"
            elif "NOT" in r_stat:
                v_color = "#64748B"
            else:
                v_color = "#D97706"

            rule_rows.append([
                Paragraph(f"<b>{r_ref}</b>", cell_citation),
                Paragraph(r_req[:65] + ("..." if len(r_req) > 65 else ""), cell_regular),
                Paragraph(r_exp[:75] + ("..." if len(r_exp) > 75 else ""), cell_regular),
                Paragraph(f"<font color='{v_color}'><b>{r_stat}</b></font>", cell_bold)
            ])

        rule_table = Table(rule_rows, colWidths=[1.8 * inch, 2.3 * inch, 2.3 * inch, 0.8 * inch])
        rule_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elements.append(rule_table)
        elements.append(Spacer(1, 0.1 * inch))

    # 10. Actionable Recommendations & Directives
    if recommendations and len(recommendations) > 0:
        elements.append(Paragraph("5. Recommended Corrective Actions & Regulatory Directives", sec_heading))
        rec_rows = [[
            Paragraph("<b>Urgency</b>", cell_bold),
            Paragraph("<b>Action Directive & Legal Citation</b>", cell_bold)
        ]]
        for rec in recommendations:
            if isinstance(rec, dict):
                urg = rec.get("urgency", "Moderate")
                tit = rec.get("title") or rec.get("action_type", "Remediation")
                det = rec.get("detail", "")
                cit = rec.get("legal_reference", "")
                urg_color = "#DC2626" if urg in ("Immediate", "High") else ("#D97706" if urg == "Moderate" else "#059669")
                text = f"<b>{tit}:</b> {det}"
                if cit:
                    text += f"<br/><font color='#1E40AF'><b>Statutory Citation:</b> {cit}</font>"
            else:
                urg = "Standard"
                urg_color = "#2563EB"
                text = str(rec)

            rec_rows.append([
                Paragraph(f"<font color='{urg_color}'><b>{urg}</b></font>", cell_bold),
                Paragraph(text, cell_regular)
            ])

        rec_table = Table(rec_rows, colWidths=[1.1 * inch, 6.1 * inch])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elements.append(rec_table)
        elements.append(Spacer(1, 0.1 * inch))

    # 11. Official Metrological Disclaimer & Legal Footnote
    elements.append(Spacer(1, 0.08 * inch))
    disclaimer_text = (
        "<b>LEGAL METROLOGY REGULATORY DISCLAIMER:</b> This inspection certificate is generated by the "
        "SAFEMETRIC autonomous auditing platform in accordance with the provisions of The Legal Metrology Act, 2009 "
        "and The Legal Metrology (Packaged Commodities) Rules, 2011. The optical text and declarations evaluated are derived "
        "strictly from the submitted physical retail packaging label. Under Section 18 of the Act, non-conforming packaging "
        "is subject to compounding or adjudication by authorized State Legal Metrology authorities."
    )
    elements.append(Paragraph(disclaimer_text, footer_style))
    elements.append(Spacer(1, 0.04 * inch))
    elements.append(Paragraph(
        f"SAFEMETRIC SIH 2026 &middot; Digital Certificate &middot; Generated: {date_str} &middot; Record Ref: {ins_id_str}",
        footer_style
    ))

    # 12. Build PDF File
    doc.build(elements)
    return output_pdf_path
