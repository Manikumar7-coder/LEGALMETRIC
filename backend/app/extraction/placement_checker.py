"""
placement_checker.py
====================
SAFEMETRIC Declaration Placement & Grouping Analysis Engine.

Statutory Basis:
----------------
Rule 8 of the Legal Metrology (Packaged Commodities) Rules, 2011 (G.S.R. 202(E)):
- Rule 8(1): "Every declaration required to be made under these rules shall appear
  on the principal display panel."
- Rule 8(1) Proviso:
  "Provided that the area surrounding the quantity declaration shall be free from
   printed information:
   (a) above and below by a space equal to at least the height of the numeral in
       the declaration, and
   (b) to the left and right by a space at least twice the height of numeral in the
       declaration."
- Rule 8(2): Grouping requirement on principal display panel for mandatory
  declarations (Net quantity, Retail sale price, Date of manufacture/packing,
  Manufacturer/Packer identity).

Generic Product Handling:
--------------------------
This module is 100% generic across all packaged commodity types and packaging formats.
Zero brand-specific assumptions or hardcoded product rules are utilized.
"""

import math
from typing import Dict, Any, List, Optional, Tuple


class PlacementChecker:
    """
    Audits declaration placement and grouping against Rule 8(1) and 8(2)
    of the Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    CORE_FIELDS = [
        ("net_quantity", "Net Quantity"),
        ("mrp", "Maximum Retail Price (MRP)"),
        ("manufacturer", "Manufacturer / Packer"),
        ("consumer_care", "Consumer Care Details"),
        ("manufacturing_date", "Date of Manufacture/Packing")
    ]

    @staticmethod
    def _to_rect(box: Any) -> Optional[Tuple[float, float, float, float]]:
        """
        Converts any polygon or bounding box format to (x_min, y_min, x_max, y_max).
        Supports:
        - 4-point polygon: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        - 4-element list/tuple: [x_min, y_min, x_max, y_max]
        - Dict with keys: {"x_min", "y_min", "x_max", "y_max"} or {"x", "y", "w", "h"}
        """
        if not box:
            return None

        try:
            if isinstance(box, (list, tuple)):
                if len(box) == 4 and all(isinstance(pt, (list, tuple)) and len(pt) >= 2 for pt in box):
                    xs = [pt[0] for pt in box]
                    ys = [pt[1] for pt in box]
                    return float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))
                elif len(box) == 4 and all(isinstance(val, (int, float)) for val in box):
                    return float(box[0]), float(box[1]), float(box[2]), float(box[3])
            elif isinstance(box, dict):
                if "x_min" in box and "y_min" in box and "x_max" in box and "y_max" in box:
                    return float(box["x_min"]), float(box["y_min"]), float(box["x_max"]), float(box["y_max"])
                if "x" in box and "y" in box and "w" in box and "h" in box:
                    return float(box["x"]), float(box["y"]), float(box["x"] + box["w"]), float(box["y"] + box["h"])
        except Exception:
            return None

        return None

    def analyze_placement(
        self,
        extracted_declarations: Dict[str, Any],
        all_detections: Optional[List[Dict[str, Any]]] = None,
        image_dimensions: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Performs comprehensive Rule 8 placement analysis:
        1. Spatial grouping of core declarations on the Principal Display Panel (Rule 8(1), 8(2)).
        2. Clear space area surrounding the net quantity numeral (Rule 8(1) proviso).
        """
        limitations = []

        # -------------------------------------------------------------
        # 1. Evaluate Declaration Grouping on PDP
        # -------------------------------------------------------------
        detected_core_boxes = {}
        for f_key, f_label in self.CORE_FIELDS:
            f_data = extracted_declarations.get(f_key)
            if not f_data and f_key == "manufacturer":
                f_data = extracted_declarations.get("manufacturer_name")
            if not f_data and f_key == "manufacturing_date":
                f_data = extracted_declarations.get("date")

            if f_data and isinstance(f_data, dict):
                rect = self._to_rect(f_data.get("bounding_box"))
                if rect:
                    detected_core_boxes[f_key] = {
                        "label": f_label,
                        "rect": rect,
                        "value": f_data.get("value")
                    }

        grouping_result = self._evaluate_grouping(detected_core_boxes, image_dimensions)

        # -------------------------------------------------------------
        # 2. Evaluate Clear Space Around Net Quantity (Rule 8(1) Proviso)
        # -------------------------------------------------------------
        qty_data = extracted_declarations.get("net_quantity")
        qty_rect = self._to_rect(qty_data.get("bounding_box")) if isinstance(qty_data, dict) else None

        clear_space_result = self._evaluate_clear_space(
            qty_rect=qty_rect,
            qty_value=qty_data.get("value") if isinstance(qty_data, dict) else None,
            all_detections=all_detections,
            image_dimensions=image_dimensions
        )

        # -------------------------------------------------------------
        # 3. Overall Determination
        # -------------------------------------------------------------
        # If either sub-check fails -> FAIL
        # If both pass -> PASS
        # If uncertainty or missing boxes -> NEEDS_REVIEW
        if grouping_result["status"] == "FAIL" or clear_space_result["status"] == "FAIL":
            overall_status = "FAIL"
            explanation = (
                f"Rule 8 placement violation detected: "
                f"{grouping_result.get('explanation') if grouping_result['status'] == 'FAIL' else clear_space_result.get('explanation')}"
            )
        elif grouping_result["status"] == "NEEDS_REVIEW" or clear_space_result["status"] == "NEEDS_REVIEW":
            overall_status = "NEEDS_REVIEW"
            reasons = []
            if grouping_result["status"] == "NEEDS_REVIEW":
                reasons.append(grouping_result["explanation"])
            if clear_space_result["status"] == "NEEDS_REVIEW":
                reasons.append(clear_space_result["explanation"])
            explanation = " | ".join(reasons)
        else:
            overall_status = "PASS"
            explanation = (
                "Core statutory declarations appear grouped on the Principal Display Panel, "
                "and the net quantity declaration complies with the statutory clear space requirement."
            )

        if grouping_result.get("limitation"):
            limitations.append(grouping_result["limitation"])
        if clear_space_result.get("limitation"):
            limitations.append(clear_space_result["limitation"])

        return {
            "status": overall_status,
            "explanation": explanation,
            "legal_reference": "Rule 8(1) & 8(2), Legal Metrology (Packaged Commodities) Rules, 2011",
            "grouping": grouping_result,
            "clear_space": clear_space_result,
            "limitations": limitations
        }

    def _evaluate_grouping(
        self,
        detected_core_boxes: Dict[str, Dict[str, Any]],
        image_dimensions: Optional[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        Evaluates spatial grouping of core declarations on the Principal Display Panel.
        """
        num_boxes = len(detected_core_boxes)
        fields_analyzed = list(detected_core_boxes.keys())

        if num_boxes < 2:
            return {
                "status": "NEEDS_REVIEW",
                "fields_analyzed": fields_analyzed,
                "cluster_bbox": None,
                "cluster_span_ratio": None,
                "explanation": (
                    f"Only {num_boxes} mandatory declaration bounding box(es) detected optically. "
                    "At least 2 core declaration coordinates are required to evaluate spatial grouping."
                ),
                "limitation": "Insufficient optical coordinates to determine PDP grouping."
            }

        all_rects = [d["rect"] for d in detected_core_boxes.values()]
        c_xmin = min(r[0] for r in all_rects)
        c_ymin = min(r[1] for r in all_rects)
        c_xmax = max(r[2] for r in all_rects)
        c_ymax = max(r[3] for r in all_rects)
        cluster_bbox = [round(c_xmin, 1), round(c_ymin, 1), round(c_xmax, 1), round(c_ymax, 1)]

        cluster_w = c_xmax - c_xmin
        cluster_h = c_ymax - c_ymin

        # Safely extract image dimensions whether passed as dict or tuple/list
        img_w = None
        img_h = None
        if isinstance(image_dimensions, dict):
            img_w = image_dimensions.get("width") or image_dimensions.get("image_width")
            img_h = image_dimensions.get("height") or image_dimensions.get("image_height")
        elif isinstance(image_dimensions, (list, tuple)) and len(image_dimensions) >= 2:
            img_w, img_h = image_dimensions[0], image_dimensions[1]

        if img_w and img_h and img_w > 0 and img_h > 0:
            span_ratio_w = cluster_w / float(img_w)
            span_ratio_h = cluster_h / float(img_h)
            span_ratio = round(max(span_ratio_w, span_ratio_h), 2)
        else:
            span_ratio = None

        # If bounding boxes are extremely scattered across opposing edges of the image
        # with span_ratio > 0.92, flag for manual review
        if span_ratio is not None and span_ratio > 0.92:
            return {
                "status": "NEEDS_REVIEW",
                "fields_analyzed": fields_analyzed,
                "cluster_bbox": cluster_bbox,
                "cluster_span_ratio": span_ratio,
                "explanation": (
                    f"Core declarations are dispersed widely across the captured surface (span ratio: {span_ratio}). "
                    "Physical verification recommended to confirm grouping on the Principal Display Panel."
                ),
                "limitation": "Declarations widely distributed across the captured field of view."
            }

        return {
            "status": "PASS",
            "fields_analyzed": fields_analyzed,
            "cluster_bbox": cluster_bbox,
            "cluster_span_ratio": span_ratio,
            "explanation": (
                f"{num_boxes} core declarations ({', '.join(fields_analyzed)}) are grouped within "
                f"a cohesive bounding cluster on the packaging panel in accordance with Rule 8(1)."
            ),
            "limitation": None
        }

    def _evaluate_clear_space(
        self,
        qty_rect: Optional[Tuple[float, float, float, float]],
        qty_value: Optional[str],
        all_detections: Optional[List[Dict[str, Any]]],
        image_dimensions: Optional[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        Evaluates clear space surrounding the net quantity numeral under Rule 8(1) Proviso:
        - Vertically: At least 1x height of numeral above and below.
        - Horizontally: At least 2x height of numeral left and right.
        """
        if not qty_rect:
            return {
                "status": "NEEDS_REVIEW",
                "net_quantity_bbox": None,
                "numeral_height_px": None,
                "required_vertical_clearance_px": None,
                "required_horizontal_clearance_px": None,
                "clear_zone": None,
                "intrusions_detected": [],
                "explanation": (
                    "Net quantity bounding box not detected. Clear space zone under Rule 8(1) "
                    "cannot be audited optically and requires manual inspection."
                ),
                "limitation": "Optical bounding box for net quantity was unavailable."
            }

        qx_min, qy_min, qx_max, qy_max = qty_rect
        h = max(1.0, qy_max - qy_min)
        w = max(1.0, qx_max - qx_min)

        # Statutory Clear Space Proviso:
        # (a) above and below: 1x height
        # (b) to left and right: 2x height
        vert_clearance = h
        horiz_clearance = 2.0 * h

        cz_xmin = max(0.0, qx_min - horiz_clearance)
        cz_ymin = max(0.0, qy_min - vert_clearance)
        cz_xmax = qx_max + horiz_clearance
        cz_ymax = qy_max + vert_clearance

        clear_zone = [round(cz_xmin, 1), round(cz_ymin, 1), round(cz_xmax, 1), round(cz_ymax, 1)]

        if not all_detections:
            return {
                "status": "NEEDS_REVIEW",
                "net_quantity_bbox": [round(qx_min, 1), round(qy_min, 1), round(qx_max, 1), round(qy_max, 1)],
                "numeral_height_px": round(h, 1),
                "required_vertical_clearance_px": round(vert_clearance, 1),
                "required_horizontal_clearance_px": round(horiz_clearance, 1),
                "clear_zone": clear_zone,
                "intrusions_detected": [],
                "explanation": (
                    "Surrounding OCR detections list unavailable; clear space around net quantity "
                    "cannot be automatically audited and requires physical verification."
                ),
                "limitation": "Surrounding OCR bounding boxes were not provided."
            }

        # Check for intruding text boxes in clear zone
        intrusions = []
        for det in all_detections:
            det_box = det.get("box") or det.get("bounding_box")
            det_rect = self._to_rect(det_box)
            if not det_rect:
                continue

            dx_min, dy_min, dx_max, dy_max = det_rect
            det_text = str(det.get("text", "")).strip()

            # Skip the net quantity box itself (or nearly identical box)
            center_x_diff = abs(((dx_min + dx_max) / 2.0) - ((qx_min + qx_max) / 2.0))
            center_y_diff = abs(((dy_min + dy_max) / 2.0) - ((qy_min + qy_max) / 2.0))
            if center_x_diff < 5.0 and center_y_diff < 5.0:
                continue

            # Skip if text is part of net quantity itself (e.g. unit 'g', 'ml', or quantity value)
            if qty_value and det_text and (det_text in qty_value or qty_value in det_text):
                continue

            # Calculate intersection between det_rect and clear_zone
            inter_xmin = max(cz_xmin, dx_min)
            inter_ymin = max(cz_ymin, dy_min)
            inter_xmax = min(cz_xmax, dx_max)
            inter_ymax = min(cz_ymax, dy_max)

            if inter_xmax > inter_xmin and inter_ymax > inter_ymin:
                inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
                det_area = max(1.0, (dx_max - dx_min) * (dy_max - dy_min))
                overlap_ratio = inter_area / det_area

                # If candidate box intrudes into clear zone by more than 20% of its area
                # AND is outside the quantity bounding box
                qty_inter_x = max(qx_min, dx_min)
                qty_inter_y = max(qy_min, dy_min)
                qty_inter_xmax = min(qx_max, dx_max)
                qty_inter_ymax = min(qy_max, dy_max)
                qty_overlap_area = max(0.0, qty_inter_xmax - qty_inter_x) * max(0.0, qty_inter_ymax - qty_inter_y)

                # Clear-zone intrusion is area overlapping clear zone minus any overlap with net qty itself
                intrusion_area = inter_area - qty_overlap_area
                if intrusion_area > 0.2 * det_area:
                    intrusions.append({
                        "text": det_text,
                        "box": [round(dx_min, 1), round(dy_min, 1), round(dx_max, 1), round(dy_max, 1)],
                        "overlap_ratio": round(overlap_ratio, 2)
                    })

        if intrusions:
            return {
                "status": "FAIL",
                "net_quantity_bbox": [round(qx_min, 1), round(qy_min, 1), round(qx_max, 1), round(qy_max, 1)],
                "numeral_height_px": round(h, 1),
                "required_vertical_clearance_px": round(vert_clearance, 1),
                "required_horizontal_clearance_px": round(horiz_clearance, 1),
                "clear_zone": clear_zone,
                "intrusions_detected": intrusions,
                "explanation": (
                    f"Printed information encroaches into the statutory clear space surrounding "
                    f"the net quantity numeral in violation of Rule 8(1) Proviso. "
                    f"Detected {len(intrusions)} encroaching text element(s) (e.g. '{intrusions[0]['text']}')."
                ),
                "limitation": None
            }

        return {
            "status": "PASS",
            "net_quantity_bbox": [round(qx_min, 1), round(qy_min, 1), round(qx_max, 1), round(qy_max, 1)],
            "numeral_height_px": round(h, 1),
            "required_vertical_clearance_px": round(vert_clearance, 1),
            "required_horizontal_clearance_px": round(horiz_clearance, 1),
            "clear_zone": clear_zone,
            "intrusions_detected": [],
            "explanation": (
                "Statutory clear space surrounding the net quantity numeral is free from "
                "encroaching printed information (>= 1x numeral height above/below, "
                ">= 2x numeral height left/right) compliant with Rule 8(1) Proviso."
            ),
            "limitation": None
        }


placement_checker = PlacementChecker()
