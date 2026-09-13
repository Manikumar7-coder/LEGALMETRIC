import re
from typing import Dict, Any, List, Optional, Tuple
from app.extraction.normalizer import normalize_text, clean_value


class FieldExtractor:
    """
    Statutory Declaration Extraction Layer for Legal Metrology Packaged Commodities.
    
    Converts raw OCR text and bounding boxes into structured declarations:
    - product_name
    - manufacturer
    - packer
    - importer
    - net_quantity
    - MRP
    - manufacturing_date
    - packing_date
    - batch_number
    - best_before
    - consumer_care
    - address
    - ingredients
    - other relevant declarations (FSSAI license, country of origin, unit sale price, nutrition info)
    
    Strict Design Rules:
    1. For every field, stores: value, raw_text, confidence, bounding_box.
    2. Missing values strictly remain None / null. No values are invented.
    3. Does NOT make legal compliance decisions (no compliance status or scores assigned).
    4. Does NOT guess missing text.
    """

    def extract_declarations(
        self,
        raw_text: str,
        bounding_boxes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Parses OCR text and bounding box metadata into a structured statutory dictionary.
        """
        if not raw_text:
            raw_text = ""

        boxes = bounding_boxes or []
        normalized = normalize_text(raw_text)
        lines = [l.strip() for l in normalized.splitlines() if l.strip()]

        extracted: Dict[str, Any] = {}

        # 1. Product Name / Title
        prod_data = self._extract_product_name(lines, boxes)
        extracted["product_name"] = prod_data

        # 2. Manufacturer Identity
        mfg_data = self._extract_manufacturer(raw_text, lines, boxes)
        extracted["manufacturer"] = mfg_data
        extracted["manufacturer_name"] = mfg_data  # backward-compatible alias

        # 3. Packer Identity (explicit packer line when separated from manufacturer)
        packer_data = self._extract_packer(raw_text, lines, boxes)
        extracted["packer"] = packer_data

        # 4. Importer Identity (for imported packaged goods)
        importer_data = self._extract_importer(raw_text, lines, boxes)
        extracted["importer"] = importer_data

        # 5. Net Quantity
        net_qty_data = self._extract_net_quantity(raw_text, lines, boxes)
        extracted["net_quantity"] = net_qty_data

        # 6. Maximum Retail Price (MRP)
        mrp_data = self._extract_mrp(raw_text, lines, boxes)
        extracted["mrp"] = mrp_data
        extracted["MRP"] = mrp_data  # uppercase alias as specified

        # 7. Manufacturing Date
        mfg_date_data = self._extract_manufacturing_date(raw_text, lines, boxes)
        extracted["manufacturing_date"] = mfg_date_data

        # 8. Packing Date
        pkd_date_data = self._extract_packing_date(raw_text, lines, boxes)
        extracted["packing_date"] = pkd_date_data

        # 9. Batch / Lot Number
        batch_data = self._extract_batch_number(raw_text, lines, boxes)
        extracted["batch_number"] = batch_data

        # 10. Best Before / Expiry Indication
        bb_data = self._extract_best_before(raw_text, lines, boxes)
        extracted["best_before"] = bb_data
        extracted["use_by"] = bb_data  # fallback alias

        # 11. Consumer Care Cell (Phone, Email, Address, Helpline)
        care_data = self._extract_consumer_care(raw_text, lines, boxes)
        extracted["consumer_care"] = care_data

        # 12. Complete Address (Postal / Factory / Registered office)
        addr_data = self._extract_address(raw_text, lines, boxes)
        extracted["address"] = addr_data
        extracted["manufacturer_address"] = addr_data  # backward-compatible alias

        # 13. Ingredients List
        ing_data = self._extract_ingredients(raw_text, lines, boxes)
        extracted["ingredients"] = ing_data

        # 14. Other Relevant Declarations:
        # 14a. FSSAI License Number(s)
        fssai_data = self._extract_fssai_license(raw_text, lines, boxes)
        extracted["fssai_license"] = fssai_data

        # 14b. Country of Origin
        country_data = self._extract_country_of_origin(raw_text, lines, boxes)
        extracted["country_of_origin"] = country_data

        # 14c. Generic / Common Name of Commodity
        generic_data = self._extract_generic_name(raw_text, lines, boxes)
        extracted["generic_name"] = generic_data

        # 14d. Unit Sale Price (USP)
        usp_data = self._extract_unit_sale_price(raw_text, lines, boxes, mrp_data, net_qty_data)
        extracted["unit_sale_price"] = usp_data

        # 14e. Nutrition Information Summary
        nut_data = self._extract_nutrition_info(raw_text, lines, boxes)
        extracted["nutrition_info"] = nut_data

        # Backward-compatible role indicator for ManufacturerIdentityRule
        role = mfg_data.get("role") or packer_data.get("role") or importer_data.get("role")
        mfg_box = mfg_data.get("bounding_box") or packer_data.get("bounding_box") or importer_data.get("bounding_box")
        if role:
            extracted["manufacturer_packer_importer"] = self._make_field(role, raw_text=role, confidence=mfg_data.get("confidence", 95.0), bounding_box=mfg_box)
        elif mfg_data.get("value"):
            extracted["manufacturer_packer_importer"] = self._make_field("Manufactured By", raw_text="Manufactured By", confidence=mfg_data.get("confidence", 90.0), bounding_box=mfg_box)
        else:
            extracted["manufacturer_packer_importer"] = self._make_field(None)

        return extracted

    # -------------------------------------------------------------------------
    # Helper Utilities
    # -------------------------------------------------------------------------
    def _make_field(
        self,
        value: Optional[Any],
        raw_text: Optional[str] = None,
        confidence: float = 0.0,
        bounding_box: Optional[List[List[int]]] = None,
        **extra_metadata
    ) -> Dict[str, Any]:
        """
        Creates canonical field representation with strict null handling.
        Does NOT invent values or perform legal compliance checks.
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            res = {
                "value": None,
                "raw_text": None,
                "confidence": 0.0,
                "bounding_box": None,
                "status": "NOT_VERIFIABLE"
            }
            res.update(extra_metadata)
            return res

        cleaned_str = clean_value(str(value)) if isinstance(value, str) else str(value)
        conf_val = round(float(confidence), 1) if confidence > 0 else 90.0

        # Mirror the OCR engine's LOW_CONFIDENCE_THRESHOLD (80.0%) for consistent status mapping
        status = "CONFIRMED_PRESENT"
        if conf_val < 80.0:
            status = "OCR_UNCERTAIN"

        res = {
            "value": cleaned_str,
            "raw_text": raw_text if raw_text else cleaned_str,
            "raw": raw_text if raw_text else cleaned_str,
            "confidence": conf_val,
            "bounding_box": bounding_box,
            "status": status
        }
        res.update(extra_metadata)
        return res

    def _find_box(
        self,
        pattern: str,
        boxes: List[Dict[str, Any]]
    ) -> Tuple[Optional[str], float, Optional[List[List[int]]]]:
        """Finds the first bounding box matching a regex pattern."""
        for b in boxes:
            text = b.get("text", "")
            if re.search(pattern, text, re.IGNORECASE):
                return text, float(b.get("confidence", 90.0)), b.get("box")
        return None, 0.0, None

    # -------------------------------------------------------------------------
    # Field Extractors
    # -------------------------------------------------------------------------
    def _extract_product_name(self, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generic product/brand name extractor using a tiered approach.
        Tier 1: Short box (1-3 words) that matches a proper-noun/brand pattern — title-case or ALL-CAPS,
                no digits, no statutory/marketing keywords, confidence >= 70%.
        Tier 2: Explicit commodity type designations (e.g. 'Potato Chips', 'Instant Noodles').
        Tier 3: First short box with no statutory/numeric content.
        Tier 4: NOT_VERIFIABLE.

        Does NOT use any hardcoded brand/product names.
        Does NOT pick up slogans, marketing phrases, or statutory declaration headers.
        """
        # Statutory, marketing, and nutritional phrases to always skip
        SKIP_PATTERNS = re.compile(
            r'(?:taste|delicious|protein|chicken|bowl|source\s+of|expert|'
            r'nutritio|ingredi|mrp|mfd\.?|net\s*(?:qty|wt|weight|quantity)|'
            r'batch|expiry|fssai|lic\.?\s*no|care|toll|free|www\.|@|helpline|'
            r'customer|consumer|manufactured|packed|imported|marketed|distributed|'
            r'incl|taxes|best\s*before|use\s*by|\d{4,}|content|energy|per\s*\d|'
            r'carbohydrate|crbohydrate|fat|cholesterol|sodium|sugar|sugars|'
            r'saturat|trans\s*fat|serving|facts|typical\s*values)',
            re.IGNORECASE
        )
        # A valid brand name: starts with uppercase letter, only letters/apostrophe/hyphen/dot/space
        BRAND_PATTERN = re.compile(r"^[A-Z][A-Za-z\u2019\'\-\.\s]{1,35}$")

        # Tier 1: Short high-confidence proper-noun box (1-3 words)
        for b in boxes:
            t = b.get("text", "").strip()
            words = t.split()
            if len(words) < 1 or len(words) > 3:
                continue
            if len(t) < 2 or len(t) > 45:
                continue
            if SKIP_PATTERNS.search(t):
                continue
            if BRAND_PATTERN.match(t) and b.get("confidence", 0) >= 70.0:
                return self._make_field(
                    t, raw_text=t,
                    confidence=b.get("confidence", 90.0),
                    bounding_box=b.get("box")
                )

        # Tier 2: Explicit commodity type designations (exact short match)
        COMMODITY_TYPES = re.compile(
            r'^(?:potato\s*chips|basmati\s*rice|potato\s*wafers|instant\s*noodles|'
            r'bathing\s*bar|beauty\s*bar|olive\s*oil|refined\s*oil|wheat\s*flour|'
            r'refined\s*wheat\s*flour|biscuits?|tea\s*bags?|green\s*tea|'
            r'mineral\s*water|drinking\s*water|pure\s*ghee|cow\s*ghee|'
            r'table\s*salt|iodised\s*salt)$',
            re.IGNORECASE
        )
        for b in boxes:
            t = b.get("text", "").strip()
            if COMMODITY_TYPES.match(t):
                return self._make_field(
                    t, raw_text=t,
                    confidence=b.get("confidence", 90.0),
                    bounding_box=b.get("box")
                )

        # Tier 3: Fallback — first short box with no statutory/numeric/marketing/nutritional content
        FALLBACK_SKIP = re.compile(
            r'(?:\d{3,}|ingredi|net\s*wt|mrp|mfd|batch|fssai|manufactured|'
            r'packed|imported|care|consumer|customer|www\.|@|per\s+\d|'
            r'nutritio|energy|protein|carbohydrate|crbohydrate|fat|sodium|sugar)',
            re.IGNORECASE
        )
        for b in boxes:
            t = b.get("text", "").strip()
            words = t.split()
            if len(words) < 1 or len(words) > 4:
                continue
            if len(t) < 2:
                continue
            if FALLBACK_SKIP.search(t):
                continue
            # Must start with a letter (not a digit or symbol)
            if not t[0].isalpha():
                continue
            return self._make_field(
                t, raw_text=t,
                confidence=b.get("confidence", 80.0),
                bounding_box=b.get("box")
            )

        # Tier 4: Not extractable from this image
        return self._make_field(None)


    def _clean_company_name(self, name: str) -> str:
        """
        Cleans corporate entity names and separates words merged during OCR concatenation.
        e.g., 'KRBLLimited' -> 'KRBL Limited', 'HOLDINGSPVT.LTD' -> 'HOLDINGS PVT. LTD'
        """
        if not name:
            return ""
        s = name.strip()
        # Separate merged corporate suffixes (Limited, Ltd, Pvt, Private, LLP, Holdings)
        s = re.sub(r'([A-Za-z0-9])(Pvt|Private|Holdings)\b', r'\1 \2', s, flags=re.IGNORECASE)
        s = re.sub(r'([A-Za-z0-9])(Limited|Ltd|LLP)\b', r'\1 \2', s, flags=re.IGNORECASE)
        s = re.sub(r'(PVT)\s*(LTD)', r'\1 \2', s, flags=re.IGNORECASE)
        s = re.sub(r'(HOLDINGS)\s*(PVT)', r'\1 \2', s, flags=re.IGNORECASE)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def _extract_manufacturer(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule 6(1)(a): Manufacturer Identity."""
        # 1. Search in bounding boxes for Mfd By / Manufactured By
        for b in boxes:
            t = b.get("text", "").strip()
            if re.search(r'(?:mfd\.?\s*by|manufactured\s*(?:&|and)?\s*(?:packed)?\s*by)[\s.:]*', t, re.IGNORECASE):
                val = re.sub(r'^(?:mfd\.?\s*by|manufactured\s*(?:&|and)?\s*(?:packed)?\s*by)[\s.:]*', '', t, flags=re.IGNORECASE).strip()
                val = self._clean_company_name(val)
                if len(val) > 2:
                    return self._make_field(val, raw_text=t, confidence=b.get("confidence", 95.0), bounding_box=b.get("box"), role="Manufacturer")

        # 2. Search across raw text with standard prefix
        match = re.search(r'(?:mfd\.?\s*by|manufactured\s*(?:&|and)?\s*(?:packed)?\s*by)[\s.:]*([a-zA-Z0-9\s.,&]+?(?:pvt\.?\s*ltd|ltd|limited|llp|co\.?))\b', raw_text, re.IGNORECASE)
        if match:
            cand = self._clean_company_name(match.group(1).strip())
            box_text, conf, box = self._find_box(re.escape(cand[:10]), boxes)
            return self._make_field(cand, raw_text=box_text or match.group(0), confidence=conf or 90.0, bounding_box=box, role="Manufacturer")

        # 2b. Search for standalone major company names (Nestle, HUL, PepsiCo, ITC, etc.) ending in Ltd/Limited
        for line in lines:
            match_standalone = re.search(r'([A-Z][a-zA-Z0-9\s.,&é]{2,60}?(?:pvt\.?\s*ltd|ltd|limited|llp))\b', line, re.IGNORECASE)
            if match_standalone:
                cand = self._clean_company_name(match_standalone.group(1).strip())
                # Filter out generic or very short matches
                if len(cand) > 5 and not cand.lower().startswith("for "):
                    box_text, conf, box = self._find_box(re.escape(cand[:10]), boxes)
                    return self._make_field(cand, raw_text=box_text or match_standalone.group(0), confidence=conf or 85.0, bounding_box=box, role="Manufacturer")

        # 3. Look for Marketed By if manufacturer not directly found
        for b in boxes:
            t = b.get("text", "").strip()
            if re.search(r'marketed\s*by[\s.:]*', t, re.IGNORECASE):
                val = re.sub(r'^marketed\s*by[\s.:]*', '', t, flags=re.IGNORECASE).strip()
                val = self._clean_company_name(val)
                if len(val) > 2:
                    return self._make_field(val, raw_text=t, confidence=b.get("confidence", 92.0), bounding_box=b.get("box"), role="Marketed By")

        return self._make_field(None)

    def _extract_packer(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extracts separate packer declaration when explicitly declared."""
        for b in boxes:
            t = b.get("text", "").strip()
            # Only match if strictly Packed By without Manufactured By
            if re.search(r'^(?:packed\s*by|pkd\s*by)[\s.:]+', t, re.IGNORECASE) and not re.search(r'mfd|manufactured', t, re.IGNORECASE):
                val = re.sub(r'^(?:packed\s*by|pkd\s*by)[\s.:]*', '', t, flags=re.IGNORECASE).strip()
                if len(val) > 2:
                    return self._make_field(val, raw_text=t, confidence=b.get("confidence", 94.0), bounding_box=b.get("box"), role="Packer")

        return self._make_field(None)

    def _extract_importer(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extracts importer declaration for imported pre-packaged commodities."""
        for b in boxes:
            t = b.get("text", "").strip()
            if re.search(r'(?:imported\s*(?:and|&)?\s*(?:distributed)?\s*by|importer)[\s.:]+', t, re.IGNORECASE):
                val = re.sub(r'^(?:imported\s*(?:and|&)?\s*(?:distributed)?\s*by|importer)[\s.:]*', '', t, flags=re.IGNORECASE).strip()
                if len(val) > 2:
                    return self._make_field(val, raw_text=t, confidence=b.get("confidence", 92.0), bounding_box=b.get("box"), role="Importer")

        return self._make_field(None)

    def _extract_net_quantity(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule 6(1)(c) & Rule 11: Net Quantity in standard metric units."""
        def _qty_meta(val_str: str) -> Dict[str, Any]:
            num_m = re.search(r'([0-9]+(?:\.[0-9]+)?)', val_str)
            unit_m = re.search(r'([a-zA-Z]+)', val_str)
            return {
                "numeric_value": float(num_m.group(1)) if num_m else 0.0,
                "unit": unit_m.group(1).lower() if unit_m else ""
            }

        # Check bounding boxes for explicit Net Qty with numeric value
        for b in boxes:
            t = b.get("text", "").strip()
            # Avoid picking up 'Per 100g' from nutrition tables
            if "per 100" in t.lower() or "approx" in t.lower() and "g" in t.lower() and "nutri" in raw_text.lower():
                continue

            m = re.search(r'(?:net\s*(?:quantity|qty|weight|wt|volume|vol)|n\.qty)[\s.:]*([0-9]+(?:\.[0-9]+)?\s*(?:g|gm|gms|kg|ml|l|ltr|litre|n|units|pieces|9))\b', t, re.IGNORECASE)
            if m:
                val = m.group(1)
                val = re.sub(r'([0-9]+)\s*9$', r'\1g', val, flags=re.IGNORECASE)
                val = clean_value(val)
                return self._make_field(val, raw_text=t, confidence=b.get("confidence", 98.0), bounding_box=b.get("box"), **_qty_meta(val))

        # Check across raw text for Net Qty (e.g. Net Quantity: 500 g, Net Wt: 200g)
        m = re.search(r'(?:net\s*(?:quantity|qty|weight|wt|volume|vol)|n\.qty)[\s.:]*([0-9]+(?:\.[0-9]+)?\s*(?:g|gm|gms|kg|ml|l|ltr|litre|pieces|units|items|9))\b', raw_text, re.IGNORECASE)
        if m:
            val = m.group(1)
            val = re.sub(r'([0-9]+)\s*9$', r'\1g', val, flags=re.IGNORECASE)
            val = clean_value(val)
            box_text, conf, box = self._find_box(re.escape(val), boxes)
            return self._make_field(val, raw_text=box_text or m.group(0), confidence=conf or 95.0, bounding_box=box, **_qty_meta(val))

        # Check for standalone Volume: 1 Litre
        m_vol = re.search(r'(?:volume|content)[\s.:]*([0-9]+(?:\.[0-9]+)?\s*(?:litre|liter|ltr|l|ml))\b', raw_text, re.IGNORECASE)
        if m_vol:
            val = clean_value(m_vol.group(1))
            box_text, conf, box = self._find_box(re.escape(val), boxes)
            return self._make_field(val, raw_text=box_text or m_vol.group(0), confidence=conf or 94.0, bounding_box=box, **_qty_meta(val))

        # Standalone weight on non-nutrition lines (e.g. 'Approx 200g')
        for b in boxes:
            t = b.get("text", "").strip()
            if "per 100" not in t.lower() and re.search(r'(?:approx\s*)?[0-9]+(?:\.[0-9]+)?\s*(?:g|gm|kg|ml|l)\b', t, re.IGNORECASE):
                m_stand = re.search(r'((?:approx\s*)?[0-9]+(?:\.[0-9]+)?\s*(?:g|gm|kg|ml|l))\b', t, re.IGNORECASE)
                if m_stand:
                    val = clean_value(m_stand.group(1))
                    return self._make_field(val, raw_text=t, confidence=b.get("confidence", 85.0), bounding_box=b.get("box"), **_qty_meta(val))

        return self._make_field(None)

    def _extract_mrp(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Rule 6(1)(e): Maximum Retail Price (MRP).
        
        Strict extraction rules:
        1. The price numeral must be textually and spatially associated with an MRP declaration
           or an explicit currency symbol (₹, Rs, Rs., INR).
        2. A numeral must look like a genuine retail price (e.g. 10 to 99999 or has decimals like 35.00).
           Numerals >= 8 digits without decimals are barcode/FSSAI numbers and must be rejected.
        3. A stray single-digit number (e.g. 1-9) without a currency symbol or decimal places on a
           separate line (like a barcode check digit) must NEVER be extracted as MRP.
        4. If the label has a printed blank MRP box (e.g., 'MRP (Incl. of all taxes)' with no filled price),
           return NOT_VERIFIABLE without inventing or guessing a value.
        """
        def _is_valid_price(num_str: str, has_explicit_currency: bool, on_same_line: bool) -> bool:
            if not num_str:
                return False
            # Disallow barcode / license / telephone numbers (8+ digits without decimal)
            if re.match(r'^[0-9]{8,}$', num_str):
                return False
            try:
                val = float(num_str)
            except ValueError:
                return False
            if val <= 0:
                return False
            # Stray single digit without currency or without decimal: reject
            if val < 10.0 and "." not in num_str and not has_explicit_currency:
                return False
            # If not on same line, require explicit currency or decimal format (.00, .50)
            if not on_same_line and not has_explicit_currency and "." not in num_str:
                return False
            return True

        def _evaluate_price_confidence(num_str: str, raw_snippet: str, base_conf: float, is_ocr_currency_misread: bool) -> float:
            """
            Evaluates extraction confidence.
            When digit count looks inconsistent with typical Indian retail pricing
            (e.g., 4+ integer digits like 6491 without decimal) or currency is an OCR misread ('R'),
            route to NEEDS_REVIEW by capping confidence below 80% (status='OCR_UNCERTAIN').
            Never silently truncate or guess digits.
            """
            # Inconsistent digit count: >= 4 integer digits without decimal (e.g. 6491)
            is_unusual_digit_count = (len(num_str.split(".")[0]) >= 4)
            if is_ocr_currency_misread or is_unusual_digit_count:
                return min(70.0, float(base_conf))
            return max(85.0, float(base_conf))

        # 1. First search: Bounding boxes that contain both MRP pattern and an associated price
        for b in boxes:
            t = b.get("text", "").strip()
            # 1a. Check for MRP label with price on same box: e.g. "MRP:R6491", "MRP ₹ 35.00", "MRP: 35.00", "MRP Rs. 40"
            if re.search(r'\b(?:mrp|maximum\s*retail\s*price|m\.r\.p\.)\b', t, re.IGNORECASE):
                # Pattern allows optional colon/dash, optional currency (₹, Rs, INR, or OCR misread R), and digits
                m_mrp = re.search(r'\b(?:mrp|maximum\s*retail\s*price|m\.r\.p\.)[\s.:]*[:=\-]?\s*(?:rs\.?|inr|[₹Rr])?[\s.:]*([0-9]+(?:\.[0-9]{1,2})?)', t, re.IGNORECASE)
                if m_mrp:
                    num = m_mrp.group(1)
                    has_curr = bool(re.search(r'(?:₹|rs\.?|inr|[Rr])', t, re.IGNORECASE))
                    is_r_misread = bool(re.search(r'\b(?:mrp|m\.r\.p\.)[\s.:]*[:=\-]?\s*[Rr][0-9]', t, re.IGNORECASE))
                    if _is_valid_price(num, has_explicit_currency=has_curr, on_same_line=True):
                        has_tax = bool(re.search(r'(?:incl|inclusive|taxes?|inol)', t, re.IGNORECASE) or re.search(r'(?:incl|inclusive|taxes?|inol)', raw_text, re.IGNORECASE))
                        disp = f"₹ {num} (Incl. of all taxes)" if has_tax else f"₹ {num}"
                        conf = _evaluate_price_confidence(num, t, b.get("confidence", 95.0), is_r_misread)
                        return self._make_field(
                            disp,
                            raw_text=t,
                            confidence=conf,
                            bounding_box=b.get("box"),
                            numeric_price=float(num),
                            has_currency=has_curr,
                            has_tax=has_tax
                        )

            # 1b. Check for canonical currency symbol line without explicit MRP token: e.g. "₹ 35.00", "Rs. 40.00"
            if re.search(r'[₹]|(?:rs\.?|inr)\s*[0-9]+', t, re.IGNORECASE):
                curr_match = re.search(r'(?:₹|rs\.?|inr)[\s.:]*([0-9]+(?:\.[0-9]{1,2})?)', t, re.IGNORECASE)
                if curr_match and _is_valid_price(curr_match.group(1), has_explicit_currency=True, on_same_line=True):
                    num = curr_match.group(1)
                    has_tax = bool(re.search(r'(?:incl|inclusive|taxes?|inol)', t, re.IGNORECASE) or re.search(r'(?:incl|inclusive|taxes?|inol)', raw_text, re.IGNORECASE))
                    disp = f"₹ {num} (Incl. of all taxes)" if has_tax else f"₹ {num}"
                    conf = _evaluate_price_confidence(num, t, b.get("confidence", 95.0), is_ocr_currency_misread=False)
                    return self._make_field(
                        disp,
                        raw_text=t,
                        confidence=conf,
                        bounding_box=b.get("box"),
                        numeric_price=float(num),
                        has_currency=True,
                        has_tax=has_tax
                    )

        # 2. Line-by-line search in lines
        for i, line in enumerate(lines):
            line_str = line.strip()
            if re.search(r'\b(?:mrp|maximum\s*retail\s*price|m\.r\.p\.)\b', line_str, re.IGNORECASE):
                # 2a. Same line price with currency or delimiter
                m_line = re.search(r'\b(?:mrp|maximum\s*retail\s*price|m\.r\.p\.)[\s.:]*[:=\-]?\s*(?:rs\.?|inr|[₹Rr])?[\s.:]*([0-9]+(?:\.[0-9]{1,2})?)', line_str, re.IGNORECASE)
                if m_line:
                    num = m_line.group(1)
                    has_curr = bool(re.search(r'(?:₹|rs\.?|inr|[Rr])', line_str, re.IGNORECASE))
                    is_r_misread = bool(re.search(r'\b(?:mrp|m\.r\.p\.)[\s.:]*[:=\-]?\s*[Rr][0-9]', line_str, re.IGNORECASE))
                    if _is_valid_price(num, has_explicit_currency=has_curr, on_same_line=True):
                        box_text, conf, box = self._find_box(re.escape(num), boxes)
                        has_tax = bool(re.search(r'(?:incl|inclusive|taxes?|inol)', raw_text, re.IGNORECASE))
                        disp = f"₹ {num} (Incl. of all taxes)" if has_tax else f"₹ {num}"
                        final_conf = _evaluate_price_confidence(num, line_str, conf or 90.0, is_r_misread)
                        return self._make_field(
                            disp,
                            raw_text=box_text or line_str,
                            confidence=final_conf,
                            bounding_box=box,
                            numeric_price=float(num),
                            has_currency=has_curr,
                            has_tax=has_tax
                        )

                # 2b. Check immediate next line ONLY if it has an explicit currency symbol
                if i + 1 < len(lines):
                    next_l = lines[i+1].strip()
                    m_next_curr = re.search(r'^(?:rs\.?|₹|inr)[\s.:]*([0-9]+(?:\.[0-9]{1,2})?)$', next_l, re.IGNORECASE)
                    if m_next_curr and _is_valid_price(m_next_curr.group(1), has_explicit_currency=True, on_same_line=False):
                        num = m_next_curr.group(1)
                        box_text, conf, box = self._find_box(re.escape(num), boxes)
                        has_tax = bool(re.search(r'(?:incl|inclusive|taxes?|inol)', raw_text, re.IGNORECASE))
                        disp = f"₹ {num} (Incl. of all taxes)" if has_tax else f"₹ {num}"
                        final_conf = _evaluate_price_confidence(num, next_l, conf or 90.0, is_ocr_currency_misread=False)
                        return self._make_field(
                            disp,
                            raw_text=box_text or next_l,
                            confidence=final_conf,
                            bounding_box=box,
                            numeric_price=float(num),
                            has_currency=True,
                            has_tax=has_tax
                        )

        # 3. Check for standalone currency declaration anywhere on label: e.g. "₹ 35.00 (Incl. of all taxes)"
        for b in boxes:
            t = b.get("text", "").strip()
            # Must have explicit canonical currency symbol followed by price
            m_stand = re.search(r'(?:₹|rs\.?)\s*([0-9]+(?:\.[0-9]{1,2})?)\s*(?:\([^\)]*taxes?\))?', t, re.IGNORECASE)
            if m_stand:
                num = m_stand.group(1)
                if _is_valid_price(num, has_explicit_currency=True, on_same_line=True):
                    # Make sure it's not part of an address or telephone
                    if not re.search(r'(?:tel|phone|pin|fax|lic|delhi|mumbai|road)', t, re.IGNORECASE):
                        has_tax = bool(re.search(r'(?:incl|inclusive|taxes?|inol)', t, re.IGNORECASE) or re.search(r'(?:incl|inclusive|taxes?|inol)', raw_text, re.IGNORECASE))
                        disp = f"₹ {num} (Incl. of all taxes)" if has_tax else f"₹ {num}"
                        conf = _evaluate_price_confidence(num, t, b.get("confidence", 90.0), is_ocr_currency_misread=False)
                        return self._make_field(
                            disp,
                            raw_text=t,
                            confidence=conf,
                            bounding_box=b.get("box"),
                            numeric_price=float(num),
                            has_currency=True,
                            has_tax=has_tax
                        )

        # Blank MRP box or no legitimate price numeral found -> NOT_VERIFIABLE
        return self._make_field(None)

    def _extract_manufacturing_date(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule 6(1)(d): Manufacturing Date."""
        date_pattern = r'([0-9]{1,2}[\/\-\.][0-9]{4}|[0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s\.\-]+[0-9]{4})'
        for b in boxes:
            t = b.get("text", "").strip()
            if re.search(r'(?:mfg(?:\s*date)?|manufactured(?:\s*on)?|manufacturing\s*date)[\s.:]*' + date_pattern, t, re.IGNORECASE):
                m = re.search(date_pattern, t, re.IGNORECASE)
                if m:
                    val = clean_value(m.group(1))
                    return self._make_field(val, raw_text=t, confidence=b.get("confidence", 96.0), bounding_box=b.get("box"))

        m_raw = re.search(r'(?:mfg(?:\s*date)?|manufactured(?:\s*on)?|manufacturing\s*date)[\s.:]*' + date_pattern, raw_text, re.IGNORECASE)
        if m_raw:
            val = clean_value(m_raw.group(1))
            box_text, conf, box = self._find_box(re.escape(val), boxes)
            return self._make_field(val, raw_text=box_text or m_raw.group(0), confidence=conf or 94.0, bounding_box=box)

        return self._make_field(None)

    def _extract_packing_date(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule 6(1)(d): Packing Date."""
        date_pattern = r'([0-9]{1,2}[\/\-\.][0-9]{4}|[0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s\.\-]+[0-9]{4})'
        for b in boxes:
            t = b.get("text", "").strip()
            if re.search(r'(?:pkd|packed(?:\s*on)?|packing\s*date)[\s.:]*' + date_pattern, t, re.IGNORECASE):
                m = re.search(date_pattern, t, re.IGNORECASE)
                if m:
                    val = clean_value(m.group(1))
                    return self._make_field(val, raw_text=t, confidence=b.get("confidence", 95.0), bounding_box=b.get("box"))

        m_raw = re.search(r'(?:pkd|packed(?:\s*on)?|packing\s*date)[\s.:]*' + date_pattern, raw_text, re.IGNORECASE)
        if m_raw:
            val = clean_value(m_raw.group(1))
            box_text, conf, box = self._find_box(re.escape(val), boxes)
            return self._make_field(val, raw_text=box_text or m_raw.group(0), confidence=conf or 93.0, bounding_box=box)

        return self._make_field(None)

    def _extract_batch_number(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extracts batch or lot number.
        
        Strict extraction rules:
        1. Requires an explicit batch/lot context marker (e.g., 'Batch No', 'Lot No', 'B.No.').
        2. Must be on the same line or explicitly delimited, not matched across unrelated lines.
        3. Rejects recipe/cooking instruction text (e.g. '9-10 minutes', 'simmer for 9-10 mins').
        4. Rejects packaging instructions (e.g., 'read the first character of the batch no').
        5. Rejects referral words (e.g., 'see below', 'andseebelow').
        """
        # Prohibited terms indicating cooking instructions, recipe durations, units, or disclaimers
        INVALID_BATCH_WORDS = re.compile(
            r'(?:minute|min|second|sec|hour|hr|cup|water|boil|simmer|cook|heat|serve|'
            r'spoon|tbsp|tsp|temp|degree|pan|lid|flame|rinse|drain|strain|lukewarm|'
            r'\bsee\b|\bbelow\b|andseebelow|read\s*the|first\s*character|packing\s*unit|'
            r'refer|details|address|crimp|panel|above|'
            r'capbodom|capsodom|cap\/bottom|bottom|bodom|sodom|cap|neck|reverse|printed)',
            re.IGNORECASE
        )

        def _is_valid_batch_code(code: str) -> bool:
            if not code or len(code) < 2 or len(code) > 30:
                return False
            if INVALID_BATCH_WORDS.search(code):
                return False
            # Check for range of numbers (e.g. "9-10", "6-7")
            if re.match(r'^[0-9]+[\-–—][0-9]+[a-z]*$', code, re.IGNORECASE):
                return False
            # Must have at least one digit or alphanumeric token
            if not re.search(r'[A-Za-z0-9]', code):
                return False
            return True

        # Disclaimers like "For packing unit address read the first character of the batch no"
        # or physical location referrals like "See Cap/Bottom", "See CapBodom"
        DISCLAIMER_PATTERN = re.compile(
            r'(?:first\s*character|read\s*(?:the)?|refer\s*(?:to)?|'
            r'see\s*(?:batch|cap|bottom|bodom|sodom|neck|below|reverse|lid|crimp|panel|details)|for\s*packing)',
            re.IGNORECASE
        )

        # 1. Search in bounding boxes for explicit Batch / Lot declaration
        for b in boxes:
            t = b.get("text", "").strip()
            if DISCLAIMER_PATTERN.search(t):
                continue

            # e.g., "Batch No.: B1234", "Lot: 402-A", "B.No. 9021"
            m = re.search(r'\b(?:batch\s*(?:no\.?|num(?:ber)?|\/lot)?|lot\s*(?:no\.?|num(?:ber)?)?|b\.?\s*no\.?)\s*[:=\-]?\s*([A-Za-z0-9\-_/]{2,30})\b', t, re.IGNORECASE)
            if m:
                cand = clean_value(m.group(1))
                if _is_valid_batch_code(cand):
                    return self._make_field(cand, raw_text=t, confidence=b.get("confidence", 96.0), bounding_box=b.get("box"))

        # 2. Line-by-line search (restricted to same line)
        for line in lines:
            line_str = line.strip()
            if DISCLAIMER_PATTERN.search(line_str):
                continue

            m = re.search(r'\b(?:batch\s*(?:no\.?|num(?:ber)?|\/lot)?|lot\s*(?:no\.?|num(?:ber)?)?|b\.?\s*no\.?)\s*[:=\-]?\s*([A-Za-z0-9\-_/]{2,30})\b', line_str, re.IGNORECASE)
            if m:
                cand = clean_value(m.group(1))
                if _is_valid_batch_code(cand):
                    box_text, conf, box = self._find_box(re.escape(cand), boxes)
                    return self._make_field(cand, raw_text=box_text or line_str, confidence=conf or 92.0, bounding_box=box)

        return self._make_field(None)

    def _extract_best_before(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule 6(1)(da): Best Before / Expiry Indication."""
        bb_regex = r'(?:best\s*before|bestbefore|expiry|exp(?:\s*date)?|use\s*before)[\s.:]*([0-9]{1,2}[\/\-\.][0-9]{4}|[0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|(?:five|six|three|four|[0-9]+)\s*months?(?:\s*from\s*(?:packaging|pkd|mfg|manufacture))?)'
        for b in boxes:
            t = b.get("text", "").strip()
            if re.search(r'best\s*before|bestbefore|expiry|exp\s*date', t, re.IGNORECASE):
                m = re.search(bb_regex, t, re.IGNORECASE)
                if m and m.group(1):
                    val = clean_value(m.group(1))
                    # Normalize words like 'FIVE MONTHSFROM MANUFACTURE'
                    val = re.sub(r'MONTHSFROM', 'Months from', val)
                    return self._make_field(val, raw_text=t, confidence=b.get("confidence", 96.0), bounding_box=b.get("box"))

        m_raw = re.search(bb_regex, raw_text, re.IGNORECASE)
        if m_raw and m_raw.group(1):
            val = clean_value(m_raw.group(1))
            val = re.sub(r'MONTHSFROM', 'Months from', val)
            box_text, conf, box = self._find_box(r'best\s*before|bestbefore', boxes)
            return self._make_field(val, raw_text=box_text or m_raw.group(0), confidence=conf or 93.0, bounding_box=box)

        return self._make_field(None)

    def _extract_consumer_care(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule 6(1)(f): Consumer Care Cell."""
        phones: List[str] = []
        emails: List[str] = []
        src_texts: List[str] = []
        primary_box = None
        highest_conf = 0.0

        # Robust phone regex supporting:
        # 1. Toll-free numbers (1800...)
        # 2. Numbers preceded by call/tel/phone/ph/helpline/contact marker (e.g. call:+917096699111)
        # 3. 10-digit mobile numbers with optional +91 or 0 (e.g. +917096699111, 7096699111)
        # 4. Standard delimited phone numbers (e.g. 011-23456789)
        PHONE_REGEX = re.compile(
            r'(?:1800[-\s]?[0-9]{3,4}[-\s]?[0-9]{3,4}|'
            r'(?:call|tel|ph(?:one)?|mobile|helpline|contact)[\s.:]*(\+?91[\-\s]?[0-9]{10}|0?[6-9][0-9]{9})|'
            r'(?:\+91[-\s]?|0)?[6-9][0-9]{9}|'
            r'[0-9]{3,4}[-\s][0-9]{3}[-\s][0-9]{4})',
            re.IGNORECASE
        )
        EMAIL_REGEX = re.compile(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', re.IGNORECASE)

        for b in boxes:
            t = b.get("text", "").strip()
            # Extract phone
            phone_m = PHONE_REGEX.search(t)
            if phone_m:
                matched_ph = phone_m.group(1) if phone_m.lastindex and phone_m.group(1) else phone_m.group(0)
                matched_ph = re.sub(r'^(?:call|tel|phone|ph|mobile|helpline|contact)[\s.:]*', '', matched_ph, flags=re.IGNORECASE).strip()
                digits_only = re.sub(r'\D', '', matched_ph)
                if len(digits_only) >= 8 and matched_ph not in phones:
                    phones.append(matched_ph)
                    src_texts.append(t)
                    if b.get("confidence", 0) > highest_conf:
                        highest_conf = b.get("confidence", 0)
                        primary_box = b.get("box")

            # Extract email
            email_m = EMAIL_REGEX.search(t)
            if email_m:
                matched_em = email_m.group(1).strip()
                if matched_em not in emails:
                    emails.append(matched_em)
                    src_texts.append(t)
                    if b.get("confidence", 0) > highest_conf:
                        highest_conf = b.get("confidence", 0)
                        primary_box = b.get("box")

        # Fallback to raw_text if not detected from boxes
        if not phones or not emails:
            for line in raw_text.splitlines():
                line_str = line.strip()
                if not phones:
                    p_m = PHONE_REGEX.search(line_str)
                    if p_m:
                        raw_ph = p_m.group(1) if p_m.lastindex and p_m.group(1) else p_m.group(0)
                        raw_ph = re.sub(r'^(?:call|tel|phone|ph|mobile|helpline|contact)[\s.:]*', '', raw_ph, flags=re.IGNORECASE).strip()
                        digits_only = re.sub(r'\D', '', raw_ph)
                        if len(digits_only) >= 8 and raw_ph not in phones:
                            phones.append(raw_ph)
                            src_texts.append(line_str)
                if not emails:
                    e_m = EMAIL_REGEX.search(line_str)
                    if e_m:
                        raw_em = e_m.group(1).strip()
                        if raw_em not in emails:
                            emails.append(raw_em)
                            src_texts.append(line_str)

        parts = []
        if phones:
            parts.append(f"Tel: {phones[0]}")
        if emails:
            parts.append(f"Email: {emails[0]}")

        if parts:
            comb_val = " | ".join(parts)
            comb_raw = "\n".join(src_texts)
            return self._make_field(
                comb_val,
                raw_text=comb_raw,
                confidence=highest_conf or 96.0,
                bounding_box=primary_box,
                phone=phones[0] if phones else None,
                email=emails[0] if emails else None
            )

        return self._make_field(None)

    def _extract_address(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule 6(1)(a): Complete Address."""
        # Find lines containing explicit postal markers or Pin codes
        addr_lines = []
        primary_box = None
        highest_conf = 0.0

        # Try finding an address block ending in a 6-digit pin code safely
        # We find the pin code first, then grab the preceding 150 characters
        m_pin = re.search(r'(?:delhi|mumbai|gurugram|pune|surat|gujarat|haryana|maharashtra|punjab|bangalore|bengaluru|noida|chennai|hyderabad)[\s.,\-]*[0-9]{6}\b', raw_text, re.IGNORECASE)
        if m_pin:
            end_idx = m_pin.end()
            start_idx = max(0, m_pin.start() - 150)
            val = raw_text[start_idx:end_idx]
            # Trim to the last newline or safe boundary if possible
            val = re.sub(r'^.*?(?:mfd\.?\s*by|marketed\s*by|manufactured|address|consumer\s*care)[\s.:]*', '', val, flags=re.IGNORECASE | re.DOTALL).strip()
            # If it's still too long, just cut at the first newline if it's far away
            if '\n' in val:
                val = val[val.find('\n')+1:].strip()
            
            box_text, conf, box = self._find_box(re.escape(val[-10:]), boxes)
            return self._make_field(
                val,
                raw_text=m_pin.group(0),
                confidence=conf or 92.0,
                bounding_box=box
            )

        # Fallback line-based matching
        for i, b in enumerate(boxes):
            t = b.get("text", "").strip()
            if any(k in t.lower() for k in ["gurugram", "sonipat", "pune", "mumbai", "surat", "gujarat", "haryana", "maharashtra", "delhi", "punjab", "pin-", "p.o.box", "plot no", "industrial estate"]):
                addr_lines.append(t)
                if b.get("confidence", 0) > highest_conf:
                    highest_conf = b.get("confidence", 0)
                    primary_box = b.get("box")
                # Grab the previous box if it looks like part of the address (e.g. PO Box)
                if i > 0 and len(addr_lines) == 1:
                    prev_t = boxes[i-1].get("text", "").strip()
                    if len(prev_t) > 3 and not re.search(r'(mrp|net|qty|date)', prev_t, re.IGNORECASE):
                        addr_lines.insert(0, prev_t)

        if not addr_lines:
            for line in lines:
                if any(k in line.lower() for k in ["gurugram", "sonipat", "pune", "mumbai", "surat", "gujarat", "haryana", "maharashtra", "delhi", "punjab", "pin-", "p.o.box", "plot no", "industrial estate"]):
                    clean_l = re.sub(r'^address[\s.:]*', '', line, flags=re.IGNORECASE).strip()
                    if clean_l:
                        addr_lines.append(clean_l)

        if addr_lines:
            combined = " ".join(addr_lines[:4])
            return self._make_field(
                combined,
                raw_text="\n".join(addr_lines),
                confidence=highest_conf or 92.0,
                bounding_box=primary_box
            )

        return self._make_field(None)

    def _extract_ingredients(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extracts ingredients list."""
        ing_lines = []
        primary_box = None
        capturing = False

        for b in boxes:
            t = b.get("text", "").strip()
            if not capturing and re.search(r'\bingredients\b', t, re.IGNORECASE):
                capturing = True
                primary_box = b.get("box")
                ing_lines.append(t)
                continue
            if capturing:
                if any(stop_word in t.lower() for stop_word in ["contains added", "potato chips", "mfd", "marketed by", "lic.no", "net qty", "mrp", "manufactured"]):
                    capturing = False
                    break
                ing_lines.append(t)
                if len(ing_lines) >= 8:
                    break

        if ing_lines:
            comb = " ".join(ing_lines)
            cleaned = re.sub(r'^(?:.*?\b)ingredients[\s.:]*', '', comb, flags=re.IGNORECASE).strip()
            if len(cleaned) > 5:
                return self._make_field(cleaned, raw_text="\n".join(ing_lines), confidence=88.0, bounding_box=primary_box)

        # Raw text fallback
        m_raw = re.search(r'\bingredients[\s.:]*([a-zA-Z0-9\s.,&\-\(\)]{5,500}?)(?:contains\s*added|mfd|marketed|lic\.?no|net\s*qty|mrp|manufactured|$)', raw_text, re.IGNORECASE | re.DOTALL)
        if m_raw:
            cleaned = m_raw.group(1).strip()
            if len(cleaned) > 10:
                box_text, conf, box = self._find_box("ingredients", boxes)
                return self._make_field(cleaned, raw_text=m_raw.group(0), confidence=conf or 85.0, bounding_box=box)

        return self._make_field(None)

    def _extract_fssai_license(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """FSSAI / Statutory License Numbers."""
        FSSAI_PREFIX = r'(?:lic\.?\s*no\.?|lc\.?\s*no\.?|lk\.?\s*o\.?|le\.?\s*no\.?|fssai|fssat|fal|issai|fssal|issat|fssa|fsai)'
        for b in boxes:
            t = b.get("text", "").strip()
            m = re.search(FSSAI_PREFIX + r'[\s.:]*([0-9]{14})\b', t, re.IGNORECASE)
            if m:
                val = m.group(1)
                return self._make_field(val, raw_text=t, confidence=b.get("confidence", 97.0), bounding_box=b.get("box"))

        m_raw = re.search(FSSAI_PREFIX + r'[\s.:]*([0-9]{14})\b', raw_text, re.IGNORECASE)
        if m_raw:
            val = m_raw.group(1)
            box_text, conf, box = self._find_box(val, boxes)
            return self._make_field(val, raw_text=box_text or m_raw.group(0), confidence=conf or 95.0, bounding_box=box)

        # Standalone 14-digit number starting with 1 (standard FSSAI format across India)
        for b in boxes:
            t = b.get("text", "").strip()
            m_stand = re.search(r'\b(1[0-9]{13})\b', t)
            if m_stand:
                val = m_stand.group(1)
                return self._make_field(val, raw_text=t, confidence=b.get("confidence", 92.0), bounding_box=b.get("box"))

        m_raw_stand = re.search(r'\b(1[0-9]{13})\b', raw_text)
        if m_raw_stand:
            val = m_raw_stand.group(1)
            box_text, conf, box = self._find_box(val, boxes)
            return self._make_field(val, raw_text=box_text or m_raw_stand.group(0), confidence=conf or 90.0, bounding_box=box)

        return self._make_field(None)

    def _extract_country_of_origin(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule 6(1)(h): Country of Origin."""
        for b in boxes:
            t = b.get("text", "").strip()
            m = re.search(r'(?:country\s*of\s*origin|made\s*in|product\s*of)[\s.:]*([a-zA-Z\s]+)', t, re.IGNORECASE)
            if m:
                val = clean_value(m.group(1))
                return self._make_field(val, raw_text=t, confidence=b.get("confidence", 98.0), bounding_box=b.get("box"))

        m_raw = re.search(r'(?:country\s*of\s*origin|made\s*in|product\s*of)[\s.:]*([a-zA-Z\s]+)', raw_text, re.IGNORECASE)
        if m_raw:
            val = clean_value(m_raw.group(1).split("\n")[0])
            box_text, conf, box = self._find_box(re.escape(val), boxes)
            return self._make_field(val, raw_text=box_text or m_raw.group(0), confidence=conf or 95.0, bounding_box=box)

        # Look for explicit country mention in address
        if re.search(r'haryana,\s*india', raw_text, re.IGNORECASE):
            box_text, conf, box = self._find_box(r'india', boxes)
            return self._make_field("India", raw_text=box_text or "Haryana,India.", confidence=conf or 94.0, bounding_box=box)

        return self._make_field(None)

    def _extract_generic_name(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Rule 6(1)(b): Generic / Common Name of Commodity.
        
        Strict extraction rules:
        1. Must be a genuine commodity/product-type noun phrase (e.g. 'Basmati Rice', 'Potato Chips').
        2. Strictly rejects marketing FAQ headlines, questions (e.g. 'WHY AGED RICE?'), slogans,
           recipe copy, or promotional sentences.
        3. Normalizes common OCR concatenations in standard commodity terms (e.g. 'BASMATIRICE' -> 'Basmati Rice').
        4. If confidence in distinguishing a genuine generic name from marketing copy is low,
           returns NOT_VERIFIABLE rather than a confident false positive.
        """
        MARKETING_OR_QUESTION = re.compile(
            r'[\?]|'
            r'^(?:why|how|what|when|where|who|which|is|are|do|does|can|will)\b|'
            r'(?:why\s*aged|aged\s*rice|cooking\s*tips?|recipe|how\s*to|originates?\s*from|'
            r'for\s*basmati|guarantee|matured\s*for|harvest|attribute|aroma|pyramid|'
            r'pre-cooking|open\s*pan|closed\s*pan|water\s*for|rolling\s*boil|simmer|'
            r'tight\s*lid|strain\s*excess|remove\s*from|lukewarm|soak\s*the|taste|'
            r'delicious|freshness|pure|natural|hygienic|premium\s*quality)',
            re.IGNORECASE
        )

        SPECIFIC_COMMODITIES = [
            (re.compile(r'\b(?:traditional\s*)?basmati\s*rice\b', re.IGNORECASE), "Basmati Rice"),
            (re.compile(r'\bbasmatirice\b', re.IGNORECASE), "Basmati Rice"),
            (re.compile(r'\bpotato\s*chips\b', re.IGNORECASE), "Potato Chips"),
            (re.compile(r'\bpotato\s*wafers\b', re.IGNORECASE), "Potato Wafers"),
            (re.compile(r'\bbanana\s*chips\b', re.IGNORECASE), "Banana Chips"),
            (re.compile(r'\b(?:extra\s*virgin\s*)?olive\s*oil\b', re.IGNORECASE), "Olive Oil"),
            (re.compile(r'\b(?:mustard|sunflower|soybean|groundnut|coconut|rice\s*bran|sesame|til|gingelly|edible\s*vegetable)\s*oil\b', re.IGNORECASE), "Edible Vegetable Oil"),
            (re.compile(r'\brefined\s*(?:edible\s*)?oil\b', re.IGNORECASE), "Refined Edible Oil"),
            (re.compile(r'\b(?:pure\s*)?(?:cow\s*)?ghee\b', re.IGNORECASE), "Ghee"),
            (re.compile(r'\b(?:maida|refined\s*wheat\s*flour)\b', re.IGNORECASE), "Refined Wheat Flour"),
            (re.compile(r'\b(?:atta|whole\s*wheat\s*flour|wheat\s*flour)\b', re.IGNORECASE), "Wheat Flour"),
            (re.compile(r'\b(?:besan|gram\s*flour)\b', re.IGNORECASE), "Gram Flour"),
            (re.compile(r'\b(?:suji|sooji|rava|semolina)\b', re.IGNORECASE), "Semolina"),
            (re.compile(r'\b(?:arhar|toor|tur|moong|chana|urad|masoor|kabuli\s*chana|rajma)\s*(?:dal|dhal)\b', re.IGNORECASE), "Pulses / Dal"),
            (re.compile(r'\b(?:instant\s*)?noodles\b', re.IGNORECASE), "Instant Noodles"),
            (re.compile(r'\b(?:toilet\s*soap|bathing\s*bar|beauty\s*bar)\b', re.IGNORECASE), "Toilet Soap"),
            (re.compile(r'\b(?:laundry\s*soap|detergent\s*bar|detergent\s*powder)\b', re.IGNORECASE), "Detergent"),
            (re.compile(r'\bmineral\s*water\b', re.IGNORECASE), "Mineral Water"),
            (re.compile(r'\bpackaged\s*drinking\s*water\b', re.IGNORECASE), "Packaged Drinking Water"),
        ]

        GENERAL_COMMODITIES = [
            (re.compile(r'\b(?:brown|white|parboiled|raw|boiled|jeera|sona\s*masoori|idli|ponni)?\s*rice\b', re.IGNORECASE), "Rice"),
            (re.compile(r'\bbutter\b', re.IGNORECASE), "Butter"),
            (re.compile(r'\bpasta\b', re.IGNORECASE), "Pasta"),
            (re.compile(r'\bmacaroni\b', re.IGNORECASE), "Macaroni"),
            (re.compile(r'\bvermicelli\b', re.IGNORECASE), "Vermicelli"),
            (re.compile(r'\bbiscuits?\b', re.IGNORECASE), "Biscuits"),
            (re.compile(r'\bcookies\b', re.IGNORECASE), "Cookies"),
            (re.compile(r'\brusk\b', re.IGNORECASE), "Rusk"),
            (re.compile(r'\b(?:green\s*)?tea(?:\s*bags?)?\b', re.IGNORECASE), "Tea"),
            (re.compile(r'\bcoffee\b', re.IGNORECASE), "Coffee"),
            (re.compile(r'\b(?:iodised\s*|table\s*|rock\s*)?salt\b', re.IGNORECASE), "Iodised Salt"),
            (re.compile(r'\bsugar\b', re.IGNORECASE), "Sugar"),
            (re.compile(r'\btoothpaste\b', re.IGNORECASE), "Toothpaste"),
            (re.compile(r'\bshampoo\b', re.IGNORECASE), "Shampoo"),
        ]

        # 1. Check for explicit labeled declaration, e.g. "Generic Name: Basmati Rice"
        for b in boxes:
            t = b.get("text", "").strip()
            m_label = re.search(r'\b(?:generic\s*name|common\s*name|name\s*of\s*(?:the\s*)?commodity)[\s.:]+([A-Za-z\s.,\-_]{2,40})', t, re.IGNORECASE)
            if m_label:
                cand = m_label.group(1).strip()
                if not MARKETING_OR_QUESTION.search(cand):
                    return self._make_field(cand, raw_text=t, confidence=b.get("confidence", 96.0), bounding_box=b.get("box"))

        # 2. Pass 1: Check bounding boxes for specific/compound commodity names
        for b in boxes:
            t = b.get("text", "").strip()
            if MARKETING_OR_QUESTION.search(t):
                continue
            for pat, norm_name in SPECIFIC_COMMODITIES:
                if pat.search(t):
                    if len(t.split()) <= 4:
                        return self._make_field(norm_name, raw_text=t, confidence=b.get("confidence", 92.0), bounding_box=b.get("box"))

        # 3. Pass 2: Check bounding boxes for general single-word commodity names
        for b in boxes:
            t = b.get("text", "").strip()
            if MARKETING_OR_QUESTION.search(t):
                continue
            for pat, norm_name in GENERAL_COMMODITIES:
                if pat.search(t):
                    if len(t.split()) <= 4:
                        return self._make_field(norm_name, raw_text=t, confidence=b.get("confidence", 92.0), bounding_box=b.get("box"))

        # 4. Check lines for clean commodity matches
        for line in lines:
            line_str = line.strip()
            if MARKETING_OR_QUESTION.search(line_str):
                continue
            for pat, norm_name in SPECIFIC_COMMODITIES + GENERAL_COMMODITIES:
                if pat.search(line_str) and len(line_str.split()) <= 4:
                    box_text, conf, box = self._find_box(re.escape(line_str), boxes)
                    return self._make_field(norm_name, raw_text=box_text or line_str, confidence=conf or 90.0, bounding_box=box)

        return self._make_field(None)

    def _extract_unit_sale_price(
        self,
        raw_text: str,
        lines: List[str],
        boxes: List[Dict[str, Any]],
        mrp_data: Dict[str, Any],
        net_qty_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rule 6(1)(ea): Unit Sale Price (USP)."""
        for b in boxes:
            t = b.get("text", "").strip()
            m = re.search(r'(?:unit\s*sale\s*price|usp)[\s.:₹]*(?:rs\.?|inr)?[\s]*([0-9]+(?:\.[0-9]+)?[\s]*(?:\/|per)[\s]*(?:g|gm|kg|ml|l|unit|piece|item|n))\b', t, re.IGNORECASE)
            if m:
                val = f"₹ {clean_value(m.group(1))}"
                return self._make_field(val, raw_text=t, confidence=b.get("confidence", 95.0), bounding_box=b.get("box"))

        # If declared USP is missing, calculate expected USP if both MRP and Net Qty exist
        mrp_num = mrp_data.get("numeric_price", 0.0)
        net_qty_val = net_qty_data.get("value")
        if mrp_num and net_qty_val:
            num_m = re.search(r'([0-9]+(?:\.[0-9]+)?)', str(net_qty_val))
            unit_m = re.search(r'(g|gm|kg|ml|l)', str(net_qty_val), re.IGNORECASE)
            if num_m and unit_m:
                q_num = float(num_m.group(1))
                q_unit = unit_m.group(1).lower()
                if q_num > 0:
                    per_unit = round(mrp_num / q_num, 2)
                    exp = f"₹ {per_unit} / {q_unit}"
                    return self._make_field(exp, raw_text="Calculated from declared MRP and Net Qty", confidence=88.0, bounding_box=None, is_calculated=True)

        return self._make_field(None)

    def _extract_nutrition_info(self, raw_text: str, lines: List[str], boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extracts mandatory nutritional facts summary."""
        nut_elements = []
        box_match = None

        for b in boxes:
            t = b.get("text", "").strip()
            if "nutritional" in t.lower():
                box_match = b.get("box")

        # Extract energy, protein, carbohydrate, fat, sodium (handling multi-column table layout)
        energy_m = re.search(r'(?:energy|eneroy|kcal)[\s:\-]+?([0-9]{2,4})', raw_text, re.IGNORECASE)
        prot_m = re.search(r'(?:protein|proloir)[\s:\-]+?(?:g|gm|9)?[\s:\-]+?([0-9]{1,2}(?:\.[0-9]+)?)', raw_text, re.IGNORECASE)
        carb_m = re.search(r'(?:carbohydrate|crbohydrate)[\s:\-]+?(?:g|gm|9)?[\s:\-]+?([0-9]{1,2}(?:\.[0-9]+)?)', raw_text, re.IGNORECASE)
        fat_m = re.search(r'(?:total\s*fat)[\s:\-]+?(?:g|gm|9)?[\s:\-]+?([0-9]{1,2}(?:\.[0-9]+)?)', raw_text, re.IGNORECASE)
        sod_m = re.search(r'(?:sodium)[\s:\-]+?(?:mg|9)?[\s:\-]+?([0-9]{2,4})', raw_text, re.IGNORECASE)


        if energy_m:
            nut_elements.append(f"Energy: {energy_m.group(1)} kcal")
        if prot_m:
            nut_elements.append(f"Protein: {prot_m.group(1)} g")
        if carb_m:
            nut_elements.append(f"Carbohydrates: {carb_m.group(1)} g")
        if fat_m:
            nut_elements.append(f"Total Fat: {fat_m.group(1)} g")
        if sod_m:
            nut_elements.append(f"Sodium: {sod_m.group(1)} mg")

        if nut_elements:
            summary = " | ".join(nut_elements)
            return self._make_field(
                summary,
                raw_text="NUTRITIONAL INFORMATION TABLE",
                confidence=95.0,
                bounding_box=box_match
            )

        return self._make_field(None)


field_extractor = FieldExtractor()
