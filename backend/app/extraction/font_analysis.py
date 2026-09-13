"""
font_analysis.py
================
SAFEMETRIC Font Size & Label Readability Analysis Engine.

Statutory Basis:
----------------
Rule 7 of the Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E)):
- Rule 7(2): "The height of any numeral in the declaration required under these
  rules, on the principal display panel shall not be less than,-
  (i) as shown in Table-I, if the net quantity is declared in terms of weight or volume;
  (ii) as shown in Table-II, if the net quantity is declared in terms of length, area or number."
- Rule 7(3): "The height of letters in the declaration shall not be less than 1 mm height
  and when blown, formed, molded, embossed or perforated, the height of letters shall not
  be less than 2 mm. Provided that the width of the letter or numeral shall not be less than
  one third of its height, except in the case of numeral '1' and letters (i), (I) and (l)."

Table-I: Minimum height of numeral (Weight / Volume):
- Upto 200 g/ml: Normal case 1.0 mm (Blown/Moulded 2.0 mm)
- Above 200 g/ml and upto 500 g/ml: Normal case 2.0 mm (Blown/Moulded 4.0 mm)
- Above 500 g/ml: Normal case 4.0 mm (Blown/Moulded 6.0 mm)

Table-II: Minimum height of numeral (Length, Area, Number, or Area of PDP):
- Upto 100 cm²: Normal case 1.0 mm (Blown/Moulded 2.0 mm)
- Above 100 cm² and upto 500 cm²: Normal case 2.0 mm (Blown/Moulded 4.0 mm)
- Above 500 cm² and upto 2500 cm²: Normal case 4.0 mm (Blown/Moulded 6.0 mm)
- Above 2500 cm²: Normal case 6.0 mm (Blown/Moulded 6.0 mm)

Generic Product Handling:
--------------------------
This module is 100% generic across all packaged commodity types and packaging formats.
Zero brand-specific assumptions or hardcoded product rules are utilized.
"""

import math
from typing import Dict, Any, List, Optional, Tuple


class FontAnalysisEngine:
    """
    Computes character heights in physical millimeters from optical bounding boxes,
    determines pixel-to-millimeter scaling, and audits compliance against Rule 7.
    """

    CAP_HEIGHT_RATIO = 0.82  # Typical ratio of numeral/capital height to line bounding box height

    def compute_box_height_px(self, box: Optional[List[List[float]]]) -> float:
        """
        Calculates line height in pixels from a 4-point polygon [[x1,y1], [x2,y2], [x3,y3], [x4,y4]].
        Uses average of left edge height and right edge height.
        """
        if not box or len(box) < 4:
            return 0.0

        try:
            p0, p1, p2, p3 = box[0], box[1], box[2], box[3]
            # Height of left edge (p0 -> p3)
            h_left = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
            # Height of right edge (p1 -> p2)
            h_right = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            # Average height
            avg_h = (h_left + h_right) / 2.0
            return round(avg_h, 2)
        except Exception:
            return 0.0

    def resolve_pixel_to_mm_scale(
        self,
        image_width_px: int,
        image_height_px: int,
        package_length_mm: Optional[float] = None,
        package_width_mm: Optional[float] = None,
        net_quantity_g_or_ml: Optional[float] = None
    ) -> Tuple[float, str, float, str]:
        """
        Establishes pixel-to-millimeter ratio.

        Returns:
            (pixel_to_mm, estimation_method, confidence, limitations_text)
        """
        # 1. User-calibrated physical package dimensions (Highest Confidence)
        if package_width_mm and package_width_mm > 0 and image_width_px > 0:
            scale_w = package_width_mm / float(image_width_px)
            if package_length_mm and package_length_mm > 0 and image_height_px > 0:
                scale_h = package_length_mm / float(image_height_px)
                px_to_mm = (scale_w + scale_h) / 2.0
            else:
                px_to_mm = scale_w

            return (
                round(px_to_mm, 4),
                "user_calibrated_package_dimensions",
                0.95,
                "Pixel-to-millimeter scale calibrated directly from user-provided physical package dimensions."
            )

        if package_length_mm and package_length_mm > 0 and image_height_px > 0:
            scale_h = package_length_mm / float(image_height_px)
            return (
                round(scale_h, 4),
                "user_calibrated_package_dimensions",
                0.95,
                "Pixel-to-millimeter scale calibrated directly from user-provided physical package length/height."
            )

        # 2. Statistical packaging dimension heuristic (Draft Estimate - Needs Review if borderline)
        # Sourced from standard retail FMCG packaging dimensions corresponding to net contents:
        # - Small pouch/bottle (<=200g/ml): typically ~140mm-170mm vertical height
        # - Medium pouch/carton (200g-500g/ml): typically ~200mm-250mm vertical height
        # - Large pack (>500g/ml): typically ~280mm-350mm vertical height
        est_height_mm = 220.0
        if net_quantity_g_or_ml:
            if net_quantity_g_or_ml <= 200.0:
                est_height_mm = 160.0
            elif net_quantity_g_or_ml <= 500.0:
                est_height_mm = 230.0
            else:
                est_height_mm = 300.0

        if image_height_px > 0:
            px_to_mm = est_height_mm / float(image_height_px)
        else:
            px_to_mm = 0.20  # Standard fallback: ~5 pixels per mm (~127 DPI)

        limitations = (
            "ESTIMATED SCALE: User physical package dimensions were not provided. "
            "Character height computed using statistical retail packaging tier heuristic. "
            "For definitive legal enforcement under Rule 7, physical micro-caliper verification is required."
        )

        return (
            round(px_to_mm, 4),
            "statistical_package_tier_heuristic",
            0.60,
            limitations
        )

    def get_statutory_minimum_height_mm(
        self,
        field_name: str,
        net_quantity_g_or_ml: Optional[float] = None,
        is_blown_or_embossed: bool = False
    ) -> Tuple[float, str]:
        """
        Retrieves legally required minimum character height under Rule 7 of PCR 2011.

        Table-I: Minimum height of numeral:
        - Upto 200 g/ml: 1.0 mm (blown/moulded: 2.0 mm)
        - Above 200 g/ml and upto 500 g/ml: 2.0 mm (blown/moulded: 4.0 mm)
        - Above 500 g/ml: 4.0 mm (blown/moulded: 6.0 mm)

        Rule 7(3): General letters in declarations shall not be less than 1.0 mm (2.0 mm blown).
        """
        f = field_name.lower().strip()

        # Numerals for net quantity and MRP governed by Rule 7(2) Table-I
        if f in ("net_quantity", "mrp", "retail_sale_price"):
            qty = net_quantity_g_or_ml or 250.0  # Default to middle tier if unknown

            if qty <= 200.0:
                min_h = 2.0 if is_blown_or_embossed else 1.0
                tier_desc = "Net quantity <= 200 g/ml (Rule 7(2) Table-I)"
            elif qty <= 500.0:
                min_h = 4.0 if is_blown_or_embossed else 2.0
                tier_desc = "Net quantity 200g - 500g/ml (Rule 7(2) Table-I)"
            else:
                min_h = 6.0 if is_blown_or_embossed else 4.0
                tier_desc = "Net quantity > 500 g/ml (Rule 7(2) Table-I)"

            return min_h, tier_desc

        # General declarations governed by Rule 7(3)
        min_h = 2.0 if is_blown_or_embossed else 1.0
        return min_h, "General statutory declaration (Rule 7(3))"

    def analyze_declarations(
        self,
        extracted_declarations: Dict[str, Any],
        image_dimensions: Optional[Dict[str, int]] = None,
        package_length_mm: Optional[float] = None,
        package_width_mm: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Performs full font size and character height compliance analysis
        for all extracted declaration fields.
        """
        dims = image_dimensions or {}
        img_w = dims.get("width") or 1000
        img_h = dims.get("height") or 1000

        # Extract net quantity magnitude if available
        net_qty_num = None
        net_info = extracted_declarations.get("net_quantity") or {}
        if isinstance(net_info, dict):
            net_qty_num = net_info.get("numeric_value")

        # Resolve scale
        px_to_mm, method, scale_conf, limitations = self.resolve_pixel_to_mm_scale(
            image_width_px=img_w,
            image_height_px=img_h,
            package_length_mm=package_length_mm,
            package_width_mm=package_width_mm,
            net_quantity_g_or_ml=net_qty_num
        )

        target_fields = [
            ("net_quantity", "Net Quantity"),
            ("mrp", "Maximum Retail Price (MRP)"),
            ("product_name", "Product Name"),
            ("generic_name", "Generic Commodity Name"),
            ("manufacturer", "Manufacturer Identity"),
            ("consumer_care", "Consumer Care Cell"),
            ("manufacturing_date", "Date of Packaging/Mfg")
        ]

        field_results: Dict[str, Any] = {}
        all_passed = True
        has_failure = False
        requires_review = False

        for f_key, f_label in target_fields:
            f_data = extracted_declarations.get(f_key)
            if not f_data or not isinstance(f_data, dict):
                continue

            val = f_data.get("value")
            box = f_data.get("bounding_box")

            if not val or not box:
                # Field missing or lacks bounding box — cannot verify character height optically
                field_results[f_key] = {
                    "field_label": f_label,
                    "extracted_value": val,
                    "status": "NOT_VERIFIABLE" if not val else "NEEDS_REVIEW",
                    "char_height_px": None,
                    "char_height_mm": None,
                    "min_required_mm": None,
                    "threshold_citation": None,
                    "explanation": "No bounding box coordinates detected for optical font size measurement."
                }
                if val:
                    requires_review = True
                continue

            # Compute box height and character height
            box_h_px = self.compute_box_height_px(box)
            char_h_px = round(box_h_px * self.CAP_HEIGHT_RATIO, 2)
            char_h_mm = round(char_h_px * px_to_mm, 2)

            min_req_mm, tier_info = self.get_statutory_minimum_height_mm(
                field_name=f_key,
                net_quantity_g_or_ml=net_qty_num,
                is_blown_or_embossed=False
            )

            # Evaluate compliance
            # If scale was an uncalibrated estimate (confidence < 0.8), borderlines route to NEEDS_REVIEW
            if char_h_mm >= min_req_mm:
                if scale_conf >= 0.80:
                    status = "PASS"
                    explanation = f"Character height ({char_h_mm} mm) satisfies statutory minimum ({min_req_mm} mm) under {tier_info}."
                else:
                    status = "PASS" if char_h_mm >= (min_req_mm * 1.15) else "NEEDS_REVIEW"
                    explanation = (
                        f"Estimated character height is {char_h_mm} mm (min required: {min_req_mm} mm). "
                        f"Scale based on {method} ({int(scale_conf*100)}% confidence)."
                    )
            else:
                # Below minimum
                if scale_conf >= 0.80:
                    status = "FAIL"
                    explanation = f"Character height ({char_h_mm} mm) violates statutory minimum of {min_req_mm} mm under {tier_info}."
                    has_failure = True
                    all_passed = False
                else:
                    # Borderline/estimated scale routes to NEEDS_REVIEW
                    status = "NEEDS_REVIEW"
                    explanation = (
                        f"Estimated character height ({char_h_mm} mm) is below statutory minimum ({min_req_mm} mm). "
                        f"Physical verification required under Rule 7 due to estimated scale."
                    )
                    requires_review = True
                    all_passed = False

            field_results[f_key] = {
                "field_label": f_label,
                "extracted_value": val,
                "status": status,
                "char_height_px": char_h_px,
                "box_height_px": box_h_px,
                "char_height_mm": char_h_mm,
                "min_required_mm": min_req_mm,
                "threshold_citation": tier_info,
                "explanation": explanation
            }

        # Overall Status Determination
        if has_failure:
            overall_status = "FAIL"
        elif requires_review or scale_conf < 0.80:
            overall_status = "NEEDS_REVIEW"
        elif all_passed and len(field_results) > 0:
            overall_status = "PASS"
        else:
            overall_status = "NEEDS_REVIEW"

        return {
            "overall_status": overall_status,
            "estimation_method": method,
            "confidence": scale_conf,
            "pixel_to_mm_ratio": px_to_mm,
            "limitations": limitations,
            "package_length_mm_provided": package_length_mm,
            "package_width_mm_provided": package_width_mm,
            "fields": field_results
        }


font_analysis_engine = FontAnalysisEngine()
