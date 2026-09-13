import re
from typing import Dict, Any, Tuple, Optional
from app.rules.base_rules import BaseRule

class MRPValidationRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="PCR-2011-R6-1-E",
            field="mrp",
            description="Maximum Retail Price (MRP) must be clearly stated in Indian Rupees inclusive of all taxes.",
            required=True,
            applicability="All Packaged Commodities",
            severity="HIGH",
            reference="Rule 6(1)(e), Legal Metrology (Packaged Commodities) Rules, 2011"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        field_info = extracted_data.get("mrp", {})
        val = str(field_info.get("value", "")).strip()
        raw = str(field_info.get("raw", "")).strip()

        if not val or field_info.get("status") == "Missing":
            return (
                False,
                "Maximum Retail Price (MRP) declaration is completely missing.",
                "Verify packaging. Absence of MRP is a non-compoundable statutory violation under Section 36(1) of Legal Metrology Act, 2009."
            )

        # Check for currency symbol or keyword
        has_currency = field_info.get("has_currency", False) or bool(re.search(r'(?:₹|rs\.?|inr)', val + " " + raw, re.IGNORECASE))
        if not has_currency:
            return (
                False,
                "MRP is printed without currency designation (₹ / Rs.).",
                "Ensure price is accompanied by the official Rupee symbol '₹' or 'Rs.' as required under Rule 6(1)(e)."
            )

        # Check for taxes statement if possible
        has_tax = field_info.get("has_tax", False) or bool(re.search(r'(?:incl|inclusive|tax|all\s*taxes)', val + " " + raw, re.IGNORECASE))
        if not has_tax:
            return (
                False,
                "MRP does not explicitly state '(Inclusive of all taxes)' or 'Incl. of all taxes'.",
                "Verify whether 'Incl. of all taxes' appears on an adjacent label segment."
            )

        return (True, None, None)


class NetQuantityRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="PCR-2011-R6-1-C",
            field="net_quantity",
            description="Net Quantity must be declared in standard metric units (g, kg, ml, l, or numbers).",
            required=True,
            applicability="All Packaged Commodities",
            severity="HIGH",
            reference="Rule 6(1)(c) & Rule 11, Legal Metrology (Packaged Commodities) Rules, 2011"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        field_info = extracted_data.get("net_quantity", {})
        val = str(field_info.get("value", "")).strip().lower()

        if not val or field_info.get("status") == "Missing":
            return (
                False,
                "Net quantity declaration was not detected on the package.",
                "Mandatory declaration. Check principal display panel for net weight, volume or unit count."
            )

        # Check for non-standard misleading words like 'approx', 'about', 'when packed'
        if any(w in val for w in ["approx", "about", "when packed", "approximate"]):
            return (
                False,
                f"Net quantity uses non-compliant ambiguous phrasing ('{val}'). Qualifiers like 'approx' are prohibited under Rule 12.",
                "Issue regulatory advisory. Rule 12 strictly prohibits misleading expressions like 'approximate' or 'when packed'."
            )

        # Check for metric unit
        has_metric = bool(re.search(r'\b(g|gm|gms|kg|kilogram|ml|l|ltr|litre|litres|n|units|pieces)\b', val))
        if not has_metric:
            return (
                False,
                f"Net quantity '{val}' does not conform to standard metric units of weight or measure.",
                "Verify compliance with Second Schedule of Legal Metrology (Packaged Commodities) Rules, 2011."
            )

        return (True, None, None)


class ManufacturerIdentityRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="PCR-2011-R6-1-A",
            field="manufacturer_name",
            description="Name and role (Manufacturer, Packer, or Importer) must be prominently declared.",
            required=True,
            applicability="All Packaged Commodities",
            severity="HIGH",
            reference="Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        field_info = extracted_data.get("manufacturer_name", {})
        val = str(field_info.get("value", "")).strip()

        if not val or field_info.get("status") == "Missing":
            return (
                False,
                "Manufacturer / Packer / Importer name is missing from the packaging.",
                "Statutory requirement. Package must declare the identity of the manufacturer or packer."
            )

        role_info = extracted_data.get("manufacturer_packer_importer", {})
        role = str(role_info.get("value", "")).strip()
        if not role:
            return (
                False,
                "Clear role qualifier ('Manufactured by', 'Packed by', or 'Imported by') is missing.",
                "Verify whether the entity is identified specifically as manufacturer, packer, or importer."
            )

        return (True, None, None)


class ManufacturerAddressRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="PCR-2011-R6-1-A-ADDR",
            field="manufacturer_address",
            description="Complete postal address of the manufacturer/packer/importer must be displayed.",
            required=True,
            applicability="All Packaged Commodities",
            severity="HIGH",
            reference="Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        field_info = extracted_data.get("manufacturer_address", {})
        val = str(field_info.get("value", "")).strip()
        status = field_info.get("status", "")

        if not val or status == "Missing":
            return (
                False,
                "Complete postal address of the manufacturer or packer is missing.",
                "Package must specify physical factory/registered address under Rule 6(1)(a)."
            )

        if status == "Low Confidence" or "obscured" in val.lower() or "unreadable" in val.lower():
            return (
                False,
                "Manufacturer address is partially obscured, low-contrast, or unreadable.",
                "Physical inspection required to determine if the address meets minimum font and contrast standards."
            )

        return (True, None, None)


class ConsumerCareRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="PCR-2011-R6-1-N",
            field="consumer_care",
            description="Consumer Care details (Name, Address, Telephone, and Email) must be provided for consumer grievance.",
            required=True,
            applicability="All Packaged Commodities",
            severity="HIGH",
            reference="Rule 6(1)(n), Legal Metrology (Packaged Commodities) Rules, 2011"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        field_info = extracted_data.get("consumer_care", {})
        val = str(field_info.get("value", "")).strip()

        if not val or field_info.get("status") == "Missing":
            return (
                False,
                "Consumer care helpline or grievance address is missing.",
                "Mandatory consumer grievance mechanism under Rule 6(1)(n). Verify package manually."
            )

        # Check if at least telephone or email is present
        has_phone = bool(re.search(r'(?:[0-9]{3,4}[-\s]?[0-9]{3}[-\s]?[0-9]{3,4}|[0-9]{10,11}|tel)', val, re.IGNORECASE))
        has_email = bool(re.search(r'@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', val))

        if not (has_phone or has_email):
            return (
                False,
                "Consumer care declaration lacks valid direct contact points (telephone or email address).",
                "Ensure telephone number and email address are provided in addition to grievance address."
            )

        return (True, None, None)


class ManufacturingDateRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="PCR-2011-R6-1-D",
            field="manufacturing_date",
            description="Month and year of manufacture or pre-packing must be stated.",
            required=True,
            applicability="All Packaged Commodities",
            severity="MEDIUM",
            reference="Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        mfg_info = extracted_data.get("manufacturing_date", {})
        pkd_info = extracted_data.get("packing_date", {})

        mfg_val = str(mfg_info.get("value", "")).strip()
        pkd_val = str(pkd_info.get("value", "")).strip()

        if not mfg_val and not pkd_val:
            return (
                False,
                "Neither Manufacturing Date (Mfg) nor Packing Date (PKD) was detected.",
                "Verify packaging. Rule 6(1)(d) mandates month and year of manufacture or packing."
            )

        return (True, None, None)


class BestBeforeRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="PCR-2011-R6-1-D-PROVISO",
            field="best_before",
            description="Best Before / Use By / Expiry date declaration for commodities which can become unfit for human consumption.",
            required=False,
            applicability="Food & Perishable Products",
            severity="MEDIUM",
            reference="Rule 6(1)(d) proviso, Legal Metrology (Packaged Commodities) Rules, 2011"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        bb_info = extracted_data.get("best_before", {})
        use_info = extracted_data.get("use_by", {})

        bb_val = str(bb_info.get("value", "")).strip()
        use_val = str(use_info.get("value", "")).strip()

        if not bb_val and not use_val:
            return (
                False,
                "Best Before or Use By date was not detected (mandatory for food and perishable commodities).",
                "If commodity is non-food/non-perishable, exemption applies. If food commodity, manual verification required."
            )

        return (True, None, None)


class CountryOfOriginRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="PCR-2011-R6-1-AB",
            field="country_of_origin",
            description="Country of origin or manufacture must be declared on the package.",
            required=True,
            applicability="All Packaged Commodities",
            severity="MEDIUM",
            reference="Rule 6(1)(ab), Legal Metrology (Packaged Commodities) Rules, 2011"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        field_info = extracted_data.get("country_of_origin", {})
        val = str(field_info.get("value", "")).strip()

        if not val or field_info.get("status") == "Missing":
            return (
                False,
                "Country of Origin declaration ('Made in India' / 'Country of Origin') was not detected.",
                "Mandatory declaration under Rule 6(1)(ab). Verify country declaration on container."
            )

        return (True, None, None)


class GenericNameRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="PCR-2011-R6-1-B",
            field="generic_name",
            description="Generic or common name of the commodity contained in the package must be prominently stated.",
            required=True,
            applicability="All Packaged Commodities",
            severity="HIGH",
            reference="Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        field_info = extracted_data.get("generic_name", {})
        val = str(field_info.get("value", "")).strip()

        if not val or field_info.get("status") == "Missing":
            # If product_name itself is detected and informative, accept it
            p_name = extracted_data.get("product_name", {}).get("value", "")
            if p_name and p_name != "Packaged Commodity":
                return (True, None, None)
            return (
                False,
                "Generic or common name of the commodity is missing from the packaging.",
                "Rule 6(1)(b) requires the common or generic name to inform consumers of the nature of the goods."
            )

        return (True, None, None)


class UnitSalePriceRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="PCR-2011-R6-1-EA",
            field="unit_sale_price",
            description="Unit Sale Price (USP) in Rupees per unit weight/measure/count must be declared for multi-quantity commodities.",
            required=False,
            applicability="All Retail Packaged Commodities exceeding 1 unit/g/ml",
            severity="MEDIUM",
            reference="Rule 6(1)(ea) & Rule 6(11), Legal Metrology (Packaged Commodities) Rules, 2011"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        field_info = extracted_data.get("unit_sale_price", {})
        val = str(field_info.get("value", "")).strip()

        if not val or field_info.get("status") == "Missing":
            net_qty = extracted_data.get("net_quantity", {})
            qty_num = net_qty.get("numeric_value", 0.0)
            if qty_num > 1.0:
                return (
                    False,
                    "Unit Sale Price (USP) is not declared on the retail package.",
                    "Mandatory under Rule 6(1)(ea) for pre-packaged commodities containing more than 1 unit/g/ml."
                )

        return (True, None, None)

