"""
SAFEMETRIC Legal-Rule Knowledge Base
Authoritative, structured representation of statutory requirements under:
1. Legal Metrology Act, 2009 (Act No. 1 of 2010)
2. Legal Metrology (Packaged Commodities) Rules, 2011 (GSR 202(E) as amended)

Design Principles:
- Strictly sourced from verified legal documents (Act sections, Rules, Schedules).
- Zero hallucinated or invented legal requirements.
- Clean separation from UI code.
- Clear distinction between Act provisions, Rules provisions, commodity-specific rules,
  and physical-measurement boundaries.
- Every rule contains at minimum:
    rule_id, legal_reference, requirement, applicable_conditions,
    field_to_check, validation_type, violation_message, evidence_requirement.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional


@dataclass
class LegalRuleSpecification:
    """
    Standardized specification for a Legal Metrology statutory rule.
    """
    rule_id: str
    legal_reference: str
    requirement: str
    applicable_conditions: str
    field_to_check: str
    validation_type: str
    violation_message: str
    evidence_requirement: str
    
    # Classification & Enforcement Metadata
    provision_type: str = "RULES_PROVISION"  # ACT_PROVISION, RULES_PROVISION, COMMODITY_SPECIFIC, PHYSICAL_BOUNDARY
    severity: str = "HIGH"                  # CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL
    required: bool = True
    punitive_reference: str = "Rule 32(2), Legal Metrology (Packaged Commodities) Rules, 2011"
    image_verifiable: bool = True
    applicable_commodities: Optional[List[str]] = None
    exempt_commodities: Optional[List[str]] = None
    statutory_exceptions: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes rule specification to canonical dictionary."""
        d = asdict(self)
        # Aliases for backward compatibility with existing engine/UI consumers
        d["field"] = self.field_to_check
        d["description"] = self.requirement
        d["reference"] = self.legal_reference
        d["applicability"] = self.applicable_conditions
        return d


# =============================================================================
# VERIFIED LEGAL RULE SPECIFICATIONS
# =============================================================================

LEGAL_RULE_KNOWLEDGE_BASE: List[LegalRuleSpecification] = [
    # -------------------------------------------------------------------------
    # 1. ACT PROVISIONS: Section 18(1) - Mandatory Statutory Declarations
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="LMA-2009-SEC-18-MANDATORY",
        legal_reference="Section 18(1), Legal Metrology Act, 2009 read with Rule 4, Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="No person shall manufacture, pack, sell, import, distribute, deliver, offer, expose or possess for sale any pre-packaged commodity unless the package bears thereon such declarations and particulars as prescribed.",
        applicable_conditions="All pre-packaged commodities intended for retail sale, distribution, or delivery in India.",
        field_to_check="principal_display_panel",
        validation_type="MANDATORY_BUNDLE_PRESENCE",
        violation_message="Pre-packaged commodity completely lacks statutory declarations or is missing the mandatory principal display panel declarations required under Section 18(1) of the Legal Metrology Act, 2009.",
        evidence_requirement="Principal display panel image crop demonstrating total omission or systemic absence of prescribed statutory particulars.",
        provision_type="ACT_PROVISION",
        severity="CRITICAL",
        punitive_reference="Section 36(1), Legal Metrology Act, 2009 (Fine up to ₹25,000 for first offence, ₹50,000 for second offence, and up to ₹1,00,000 or 1 year imprisonment for subsequent offences).",
        image_verifiable=True,
        statutory_exceptions=[
            "Rule 3(a): Packages containing quantity more than 25 kg or 25 litre (except cement and fertilizer sold in bags up to 50 kg)",
            "Rule 3(b): Packaged commodities meant exclusively for industrial or institutional consumers",
            "Rule 4 Explanation: Packages remaining within manufacturer's premises prior to dispatch for retail destination"
        ]
    ),

    # -------------------------------------------------------------------------
    # 2. ACT PROVISIONS: Section 36(1) & 49 - Corporate Liability & Deemed Manufacturer
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="LMA-2009-SEC-36-DEEMED-MFG",
        legal_reference="Section 36(1) & Section 49, Legal Metrology Act, 2009 read with Rule 6(1) Explanation I & II",
        requirement="Pre-packaged commodities must conform to statutory standards. If a company name appears without 'manufactured by' or 'packed by', or if a brand owner markets the product, liability as deemed manufacturer attaches.",
        applicable_conditions="All retail packaged goods bearing corporate marketer or un-qualified brand owner details.",
        field_to_check="manufacturer_name",
        validation_type="CORPORATE_LIABILITY_ROLE",
        violation_message="Deemed manufacturer liability established under Section 49 of the Act. Omission of explicit manufacturer/packer credentials subjects marketer to primary statutory liability.",
        evidence_requirement="Bounding box of marketer/brand owner text and verification of absence of separate manufacturer identification.",
        provision_type="ACT_PROVISION",
        severity="HIGH",
        punitive_reference="Section 36(1) and Section 49(1)-(2), Legal Metrology Act, 2009.",
        image_verifiable=True
    ),

    # -------------------------------------------------------------------------
    # 3. RULES PROVISIONS: Rule 6(1)(a) & Rule 10 - Manufacturer / Packer / Importer Name
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R6-1-A-MFG-NAME",
        legal_reference="Rule 6(1)(a) & Rule 10(1)-(2), Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="The name of the manufacturer, or where manufacturer is not the packer, the names of both manufacturer and packer, or for imported goods the importer, must be prominently declared with clear role qualifier ('Manufactured by', 'Packed by', 'Imported by').",
        applicable_conditions="All retail packages.",
        field_to_check="manufacturer_name",
        validation_type="PRESENCE_AND_ROLE",
        violation_message="Manufacturer / Packer / Importer name or mandatory role qualifier ('Manufactured by', 'Packed by', 'Imported by') is missing from the package label.",
        evidence_requirement="Bounding box of manufacturer declaration area confirming absence of entity name or role qualifier.",
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), PCR 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=True,
        statutory_exceptions=[
            "Explanation III to Rule 6(1): For food articles, governed instead by food safety regulations (PFA / FSSAI)",
            "Rule 10(1) First Proviso: Packages having capacity 5 cubic cm or less may use registered mark/inscription",
            "Rule 28: Registered shorter address permissible upon approval by Director/Controller"
        ]
    ),

    # -------------------------------------------------------------------------
    # 4. RULES PROVISIONS: Rule 6(1)(a) & Rule 10 - Complete Postal Address
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R6-1-A-ADDR",
        legal_reference="Rule 6(1)(a) & Rule 10(1), Explanation, Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="Complete postal address where the factory is situated, including street, premises number, city, state, and Postal Index Number (PIN) code must be declared so a consumer can locate the manufacturer/packer/importer.",
        applicable_conditions="All retail packages.",
        field_to_check="manufacturer_address",
        validation_type="POSTAL_ADDRESS_COMPLETENESS",
        violation_message="Complete postal address of the manufacturer or packer is missing or lacks essential physical locating particulars (city, state, or PIN code).",
        evidence_requirement="Bounding box of address text block highlighting absence of city, state, or 6-digit PIN code.",
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), PCR 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=True,
        statutory_exceptions=[
            "Rule 10(1) First Proviso: Packages of capacity 5 cubic cm or less may use registered mark",
            "Rule 28: Registered shorter address permissible if approved by Controller"
        ]
    ),

    # -------------------------------------------------------------------------
    # 5. RULES PROVISIONS: Rule 6(1)(b) - Generic or Common Name of Commodity
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R6-1-B-GENERIC-NAME",
        legal_reference="Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="The common or generic name of the commodity contained in the package must be prominently stated. For multi-product packages, the name and quantity of each product must be declared.",
        applicable_conditions="All retail pre-packaged commodities.",
        field_to_check="generic_name",
        validation_type="COMMODITY_DESCRIPTOR",
        violation_message="Generic or common name of the commodity contained in the package is missing, obscuring the true nature of the goods from consumers.",
        evidence_requirement="Principal display panel image crop demonstrating brand identity without generic commodity descriptor.",
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), PCR 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=True
    ),

    # -------------------------------------------------------------------------
    # 6. RULES PROVISIONS: Rule 6(1)(c) & Rule 11, 12 - Net Quantity
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R6-1-C-NET-QUANTITY",
        legal_reference="Rule 6(1)(c), Rule 11(1), and Rule 12(1)-(3), Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="Net quantity of the commodity contained in the package must be declared in standard units of weight, measure, or count (excluding wrapper and packaging materials). Mass for solids, volume for liquids, count for items sold by number.",
        applicable_conditions="All retail packages.",
        field_to_check="net_quantity",
        validation_type="METRIC_MAGNITUDE_UNIT",
        violation_message="Net quantity declaration is missing, does not use standard metric units of weight or measure, or misapplies physical state dimensions.",
        evidence_requirement="Bounding box of Net Quantity area showing absence of quantity or non-standard measurement units.",
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), PCR 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=True,
        statutory_exceptions=[
            "Rule 26(a): Packages containing net weight/measure of 10 g or 10 ml or less (except 10g-20g must declare MRP and net quantity)",
            "Fourth Schedule: Specified commodities permitted declaration in weight or volume (curd, edible oil, ice cream)"
        ]
    ),

    # -------------------------------------------------------------------------
    # 7. RULES PROVISIONS: Rule 12(6) - Prohibition of Misleading Qualifiers
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R12-6-PROHIBITED-QUALIFIERS",
        legal_reference="Rule 12(6), Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="The declaration of quantity shall not contain any word or expression which tends to create an exaggerated, misleading, or inadequate impression, including 'minimum', 'not less than', 'average', 'about', or 'approximately'.",
        applicable_conditions="All retail pre-packaged commodities.",
        field_to_check="net_quantity",
        validation_type="PROHIBITED_SUBSTRING",
        violation_message="Net quantity declaration contains prohibited ambiguous qualifying expression ('approx', 'about', 'minimum', 'not less than') in direct violation of Rule 12(6).",
        evidence_requirement="Bounding box highlighting the prohibited qualifier adjacent to the net quantity numeral.",
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), PCR 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=True,
        statutory_exceptions=[
            "Third Schedule: Commodities subject to environmental evaporation (soaps, lotions, creams) legally permitted to use 'when packed'"
        ]
    ),

    # -------------------------------------------------------------------------
    # 8. RULES PROVISIONS: Rule 13(1)-(5) - Standard SI Units & Count Symbols
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R13-UNITS-SYMBOLS",
        legal_reference="Rule 13(1)-(5), Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="Only International System (SI) units permitted. Sub-multiples below 1 kg must use gram (g); below 1 L use millilitre (ml). Prohibits non-metric counts: 'dozen', 'score', 'gross'. Items sold by number must use symbol 'N' or 'U'.",
        applicable_conditions="All retail packaged commodities declared by weight, measure, or count.",
        field_to_check="net_quantity",
        validation_type="SI_UNIT_HIERARCHY",
        violation_message="Net quantity uses non-metric unit, prohibited collective count ('dozen', 'gross'), or fails to use statutory count symbol ('N' or 'U').",
        evidence_requirement="Bounding box of unit designation showing non-SI unit or prohibited collective count.",
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), PCR 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=True
    ),

    # -------------------------------------------------------------------------
    # 9. RULES PROVISIONS: Rule 6(1)(d) - Month & Year of Manufacture / Packing / Import
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R6-1-D-DATE",
        legal_reference="Rule 6(1)(d) & Rule 6(1)(g) Provisos (A)-(B), Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="The month and year in which the commodity was manufactured, pre-packed, or imported must be stated on the package (may use rubber stamp without overwriting).",
        applicable_conditions="All retail pre-packaged commodities.",
        field_to_check="manufacturing_date",
        validation_type="MONTH_YEAR_FORMAT",
        violation_message="Neither Manufacturing Date (Mfg) nor Pre-packing Date (PKD) containing month and year was detected on the package.",
        evidence_requirement="Principal display panel or packaging seal crop showing absence of valid month and year date marking.",
        provision_type="RULES_PROVISION",
        severity="MEDIUM",
        punitive_reference="Rule 32(2), PCR 2011.",
        image_verifiable=True,
        statutory_exceptions=[
            "Proviso 1 to Rule 6(1)(d): For food articles, governed by food safety laws (PFA/FSSAI)",
            "Proviso 2: Packages containing certified seeds under Seeds Act, 1966 exempt",
            "Proviso 4: Packages containing cosmetics governed by Drugs and Cosmetics Rules, 1945",
            "Rule 6(1)(g) Proviso (A): Bidis, incense sticks (agarbatti), and domestic LPG cylinders exempt",
            "Rule 6(1)(g) Proviso (B): One-month packaging material inventory grace period permitted (except food <= 90 days shelf-life)"
        ]
    ),

    # -------------------------------------------------------------------------
    # 10. RULES PROVISIONS: Rule 6(1)(e) - Maximum Retail Price (MRP) & Tax Inclusivity
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R6-1-E-MRP",
        legal_reference="Rule 6(1)(e), Rule 2(m), PCR 2011 and Section 18, Legal Metrology Act, 2009",
        requirement="Retail sale price must be clearly declared as Maximum Retail Price in Indian Rupees inclusive of all taxes, formatted strictly as 'Maximum or Max. retail price Rs. ... (inclusive of all taxes)' or 'MRP Rs./₹ ... (incl. of all taxes)'.",
        applicable_conditions="All retail pre-packaged commodities.",
        field_to_check="mrp",
        validation_type="PRICE_CURRENCY_TAX",
        violation_message="Maximum Retail Price (MRP) is completely missing, omits Indian Rupee symbol/word (₹ / Rs.), or omits mandatory phrase '(inclusive of all taxes)'.",
        evidence_requirement="Bounding box of price declaration showing absence of currency, omission of tax phrase, or bare numeral.",
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), PCR 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=True,
        statutory_exceptions=[
            "Rule 6(1)(g) Proviso (C): Bidis and domestic LPG cylinders under Administrative Price Mechanism exempt",
            "Rule 6(1)(e) Proviso: Alcoholic beverages governed by State Excise laws",
            "Rule 8(2): Returnable glass soft drink bottles may use simplified 'MRP Rs. ...' on crown cap or bottle"
        ]
    ),

    # -------------------------------------------------------------------------
    # 11. RULES PROVISIONS: Rule 6(1)(ea) & 6(11) - Unit Sale Price (USP)
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R6-1-EA-USP",
        legal_reference="Rule 6(1)(ea) & Rule 6(11), Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="Pre-packaged commodities containing net quantity exceeding 1 unit, 1 g, 1 kg, 1 ml, or 1 l must declare Unit Sale Price (USP) in Rupees per unit weight/measure/item.",
        applicable_conditions="Retail pre-packaged commodities containing more than 1 unit/g/kg/ml/l.",
        field_to_check="unit_sale_price",
        validation_type="UNIT_SALE_PRICE_CONSISTENCY",
        violation_message="Unit Sale Price (USP) is missing on package containing multi-quantity units, or does not mathematically correlate with declared MRP and net quantity.",
        evidence_requirement="Bounding box of price panel showing absence of per-unit price alongside MRP.",
        provision_type="RULES_PROVISION",
        severity="MEDIUM",
        punitive_reference="Rule 32(2), PCR 2011.",
        image_verifiable=True,
        statutory_exceptions=[
            "Not required if net quantity is exactly equal to 1 g, 1 ml, 1 kg, 1 l, or 1 number"
        ]
    ),

    # -------------------------------------------------------------------------
    # 12. RULES PROVISIONS: Rule 6(1)(ab) - Country of Origin
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R6-1-AB-COUNTRY-ORIGIN",
        legal_reference="Rule 6(1)(ab) & Rule 10(1) Second Proviso, Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="The name of the country of origin or manufacture must be declared on every imported and domestic package. If made abroad and packed in India, both country of manufacture and Indian packer must be stated.",
        applicable_conditions="All retail pre-packaged commodities.",
        field_to_check="country_of_origin",
        validation_type="COUNTRY_DECLARATION",
        violation_message="Country of Origin declaration ('Made in India' / 'Country of Origin') was not detected on the packaging.",
        evidence_requirement="Bounding box of declarations panel demonstrating absence of origin country.",
        provision_type="RULES_PROVISION",
        severity="MEDIUM",
        punitive_reference="Rule 32(2), PCR 2011.",
        image_verifiable=True,
        statutory_exceptions=[
            "Satisfied if manufacturer address clearly contains country name in factory address (e.g., 'Haryana, India')"
        ]
    ),

    # -------------------------------------------------------------------------
    # 13. RULES PROVISIONS: Rule 6(2) - Consumer Grievance Care Cell
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R6-2-CONSUMER-CARE",
        legal_reference="Rule 6(2), Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="Every package must bear the name, address, telephone number, and email address (if available) of the person or office that can be contacted in case of consumer complaints.",
        applicable_conditions="All retail pre-packaged commodities.",
        field_to_check="consumer_care",
        validation_type="GRIEVANCE_CONTACT_POINTS",
        violation_message="Mandatory consumer grievance mechanism under Rule 6(2) is missing or lacks direct contact points (telephone helpline or email address).",
        evidence_requirement="Bounding box of consumer care panel showing absence of telephone number, helpline, or email address.",
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), PCR 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=True
    ),

    # -------------------------------------------------------------------------
    # 14. RULES PROVISIONS: Rule 6(3) & 6(4) - Restriction on Individual Stickers
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R6-3-STICKER-RESTRICTION",
        legal_reference="Rule 6(3) & Rule 6(4), Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="It is prohibited to affix individual stickers on packages for altering or making declarations required under the rules. Sticker permitted solely for reducing MRP without obscuring original manufacturer declaration.",
        applicable_conditions="All pre-packaged commodities.",
        field_to_check="label_surface_stickers",
        validation_type="STICKER_OVERLAY_INSPECTION",
        violation_message="Individual sticker affixed on package altering statutory declaration (Net Qty, Date, or Manufacturer) in direct contravention of Rule 6(3).",
        evidence_requirement="Image crop demonstrating physical sticker affixed over pre-printed packaging surface.",
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), PCR 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=False,  # Definitive verification requires tactile/physical review
        statutory_exceptions=[
            "Proviso to Rule 6(3): Sticker permitted solely for reducing MRP (downward price revision) without covering manufacturer's original declaration",
            "Rule 6(4): Stickers permitted for declarations other than statutory declarations (e.g., internal retail inventory barcode)"
        ]
    ),

    # -------------------------------------------------------------------------
    # 15. COMMODITY-SPECIFIC: Rule 5 & Second Schedule - Standard Pack Sizes
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R5-SECOND-SCHEDULE",
        legal_reference="Rule 5 read with Second Schedule, Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="Commodities specified in Second Schedule (Biscuits, Soaps, Edible Oil, Tea, Rice, Atta) must be packed in prescribed standard quantities, or prominently declare 'Not a standard pack size under the Legal Metrology (Packaged Commodities) Rules, 2011'.",
        applicable_conditions="Commodities listed in the Second Schedule of the Rules.",
        field_to_check="net_quantity",
        validation_type="SCHEDULE_QUANTITY_MATCH",
        violation_message="Second Schedule scheduled commodity packed in non-standard pack size without the mandatory label declaration 'Not a standard pack size under the Legal Metrology (Packaged Commodities) Rules, 2011'.",
        evidence_requirement="Net quantity crop and full label crop confirming omission of mandatory non-standard pack size disclaimer.",
        provision_type="COMMODITY_SPECIFIC",
        severity="MEDIUM",
        punitive_reference="Rule 32(2), PCR 2011.",
        image_verifiable=True,
        applicable_commodities=[
            "Biscuits", "Laundry Soap", "Non-soapy detergent", "Toilet Soap",
            "Edible Oil", "Vanaspati", "Ghee", "Rice", "Atta", "Flour",
            "Tea", "Coffee", "Milk Powder", "Cement", "Paint"
        ],
        statutory_exceptions=[
            "Non-scheduled commodities (e.g. Potato Chips / Extruded Snacks) are not restricted by Second Schedule pack sizes"
        ]
    ),

    # -------------------------------------------------------------------------
    # 16. COMMODITY-SPECIFIC: Rule 11(4) & Third Schedule - 'When Packed' Exemption
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-THIRD-SCHEDULE-WHEN-PACKED",
        legal_reference="Rule 11(4) read with Third Schedule, Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="'When packed' net quantity qualification is restricted strictly to commodities subject to significant environmental moisture loss specified in Third Schedule (all kinds of soaps, lotions, creams). Prohibited on all other commodities.",
        applicable_conditions="Commodities declaring 'when packed' on label.",
        field_to_check="net_quantity",
        validation_type="SCHEDULE_EXEMPTION_MEMBERSHIP",
        violation_message="'When packed' qualification used on a commodity not listed in Third Schedule, in contravention of Rule 11(2) and Rule 11(4).",
        evidence_requirement="Bounding box of 'when packed' expression and commodity generic name verification.",
        provision_type="COMMODITY_SPECIFIC",
        severity="HIGH",
        punitive_reference="Rule 32(2), PCR 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=True,
        applicable_commodities=["Toilet Soap", "Laundry Soap", "Soap", "Lotion", "Cream (other than cream of milk)"]
    ),

    # -------------------------------------------------------------------------
    # 17. RULES PROVISIONS: Rule 9(1) & 9(4) - Legibility, Contrast & Language
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R9-LEGIBILITY-CONTRAST-LANG",
        legal_reference="Rule 9(1) & Rule 9(4), Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="Declarations must be legible, prominent, in Hindi (Devanagari) or English, with retail sale price and net quantity numerals in a color that conspicuously contrasts with the label background. No reading through liquid commodity.",
        applicable_conditions="All retail pre-packaged commodities.",
        field_to_check="general_legibility",
        validation_type="SCRIPT_AND_CONTRAST",
        violation_message="Mandatory declarations lack required prominence, legibility, permissible script (English or Hindi in Devanagari), or conspicuous color contrast for MRP/quantity numerals.",
        evidence_requirement="OCR text recognition metrics and numeral bounding box color histogram analysis.",
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), PCR 2011 & Section 18, Legal Metrology Act, 2009.",
        image_verifiable=True,
        statutory_exceptions=[
            "Rule 9(1) Proviso (a): Contrasting color not required if label info is blown, formed or moulded on glass or plastic surfaces"
        ]
    ),

    # -------------------------------------------------------------------------
    # 18. EXEMPTIONS: Rule 26 & Rule 3 - Statutory De-Minimis & Institutional Exemptions
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R26-STATUTORY-EXEMPTIONS",
        legal_reference="Rule 26 & Rule 3, Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement="Statutory exemption from Chapter II labeling rules applies to: packages <= 10 g/ml; fast food packed by hotels/restaurants; DPCO scheduled formulations; agricultural produce > 50 kg; packages > 25 kg/L; and institutional consumers.",
        applicable_conditions="Packages meeting statutory threshold criteria.",
        field_to_check="statutory_exemption",
        validation_type="EXEMPTION_QUALIFICATION",
        violation_message="N/A - Statutory Exemption Clause.",
        evidence_requirement="Package net weight/measure verification or institutional consumer invoice/marking.",
        provision_type="RULES_PROVISION",
        severity="INFORMATIONAL",
        punitive_reference="N/A",
        image_verifiable=True,
        statutory_exceptions=[
            "Packages of 10 g to 20 g or 10 ml to 20 ml must still declare Maximum Retail Price (MRP) and Net Quantity"
        ]
    ),

    # -------------------------------------------------------------------------
    # 19. PHYSICAL BOUNDARY: Rule 7 (Numeral Height) & First Schedule (MPE)
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R7-PHYSICAL-MEASUREMENT",
        legal_reference="Rule 7 (Numeral Height Tables I & II) & First Schedule (Maximum Permissible Error), PCR 2011",
        requirement="Absolute numeral height in physical millimeters (1 mm - 6 mm based on net quantity/area) and net contents error within Maximum Permissible Error (MPE) limits require calibrated physical measurement tools.",
        applicable_conditions="All retail packages.",
        field_to_check="physical_verification",
        validation_type="PHYSICAL_MEASUREMENT_ROUTING",
        violation_message="Physical numeral height in millimeters and net contents weight compliance with Maximum Permissible Error (MPE) cannot be definitively validated on uncalibrated 2D photos and require physical officer verification.",
        evidence_requirement="Physical micro-ruler measurement or certified gravimetric scale testing certificate.",
        provision_type="PHYSICAL_BOUNDARY",
        severity="INFORMATIONAL",
        punitive_reference="Section 36(2), Legal Metrology Act, 2009 (Deficiency exceeding MPE punishable with fine ₹10,000 - ₹50,000).",
        image_verifiable=False
    ),

    # -------------------------------------------------------------------------
    # 20. RULES PROVISIONS: Rule 7(1)-(3) & Tables I & II - Character / Font Height
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R7-FONT-SIZE-COMPLIANCE",
        legal_reference="Rule 7(1)-(3) read with Tables I & II, Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement=(
            "The height of any numeral in the declaration required under these rules on the principal display panel "
            "shall not be less than as shown in Table-I (1 mm for net qty <=200g/ml; 2 mm for 200g-500g/ml; 4 mm for >500g/ml; "
            "double when blown/formed/moulded) or Table-II for length/area/number/PDP area. Under Rule 7(3), the height of "
            "letters in declarations shall not be less than 1 mm (2 mm when blown/formed/moulded/embossed)."
        ),
        applicable_conditions="All pre-packaged commodities sold in retail packages.",
        field_to_check="font_size",
        validation_type="FONT_SIZE_COMPLIANCE",
        violation_message="Character height of statutory declarations (notably net quantity or retail sale price) falls below the mandatory minimum height in millimeters prescribed under Rule 7 Tables I & II.",
        evidence_requirement="Optical bounding box dimensions, calibrated pixel-to-millimeter scale factor, and character height measurement in millimeters.",
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), Legal Metrology (Packaged Commodities) Rules, 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=True,
        statutory_exceptions=[
            "Rule 7(1): Packages having capacity 5 cubic cm or less may use card or tape firmly affixed",
            "Rule 7(4): Sub-rules (2) to (3) shall not apply if information is required under any other law for the time being in force"
        ]
    ),

    # -------------------------------------------------------------------------
    # 21. RULES PROVISIONS: Rule 8(1)-(2) - Declaration Placement & Clear Space
    # -------------------------------------------------------------------------
    LegalRuleSpecification(
        rule_id="PCR-2011-R8-DECLARATION-PLACEMENT",
        legal_reference="Rule 8(1) & 8(2), Legal Metrology (Packaged Commodities) Rules, 2011",
        requirement=(
            "Every declaration required under these rules shall appear on the principal display panel and be grouped "
            "together. Under the proviso to Rule 8(1), the area surrounding the quantity declaration shall be free from "
            "printed information: (a) above and below by a space equal to at least the height of the numeral in the declaration, "
            "and (b) to the left and right by a space at least twice the height of numeral in the declaration."
        ),
        applicable_conditions="All pre-packaged commodities sold in retail packages.",
        field_to_check="declaration_placement",
        validation_type="PLACEMENT_COMPLIANCE",
        violation_message=(
            "Statutory declarations fail to appear grouped on the Principal Display Panel, or printed information "
            "encroaches into the statutory clear space surrounding the net quantity numeral in violation of Rule 8(1)."
        ),
        evidence_requirement=(
            "Spatial bounding boxes of core declarations, cluster coordinates on the Principal Display Panel, "
            "and clear space boundary coordinates surrounding the net quantity numeral."
        ),
        provision_type="RULES_PROVISION",
        severity="HIGH",
        punitive_reference="Rule 32(2), Legal Metrology (Packaged Commodities) Rules, 2011 & Section 36(1), Legal Metrology Act, 2009.",
        image_verifiable=True,
        statutory_exceptions=[
            "Rule 8(2): Returnable glass bottles for soft drinks or fruit beverages may indicate retail sale price on crown cap or bottle."
        ]
    )
]


# =============================================================================
# KNOWLEDGE BASE QUERY & LOOKUP SERVICE
# =============================================================================

class LegalRuleKnowledgeBase:
    """
    Query interface and repository manager for the Legal Metrology Rule Knowledge Base.
    """
    def __init__(self, rules: Optional[List[LegalRuleSpecification]] = None):
        self._rules: List[LegalRuleSpecification] = rules or LEGAL_RULE_KNOWLEDGE_BASE
        self._rules_by_id: Dict[str, LegalRuleSpecification] = {r.rule_id: r for r in self._rules}

    def get_all_rules(self) -> List[LegalRuleSpecification]:
        """Returns all configured statutory rules."""
        return list(self._rules)

    def get_rule_by_id(self, rule_id: str) -> Optional[LegalRuleSpecification]:
        """Looks up a statutory rule specification by its canonical ID."""
        return self._rules_by_id.get(rule_id)

    def get_rules_by_field(self, field_name: str) -> List[LegalRuleSpecification]:
        """Filters rules targeting a specific declaration field."""
        return [r for r in self._rules if r.field_to_check == field_name]

    def get_rules_by_provision_type(self, provision_type: str) -> List[LegalRuleSpecification]:
        """
        Filters rules by statutory taxonomy:
        - ACT_PROVISION
        - RULES_PROVISION
        - COMMODITY_SPECIFIC
        - PHYSICAL_BOUNDARY
        """
        return [r for r in self._rules if r.provision_type == provision_type]

    def get_image_verifiable_rules(self) -> List[LegalRuleSpecification]:
        """Returns rules that can be reliably evaluated from optical label images."""
        return [r for r in self._rules if r.image_verifiable]

    def get_rules_for_commodity(self, commodity_name: str) -> List[LegalRuleSpecification]:
        """
        Resolves applicable statutory rules for a specific commodity class
        (e.g., handles Second Schedule standard pack sizes or Third Schedule 'when packed').
        """
        c_lower = commodity_name.lower().strip()
        applicable = []

        for r in self._rules:
            # Common rules apply to all commodities
            if r.provision_type in ("ACT_PROVISION", "RULES_PROVISION", "PHYSICAL_BOUNDARY"):
                # Check for food-specific deferrals
                if "food" in c_lower or "chips" in c_lower or "rice" in c_lower:
                    if r.rule_id in ("PCR-2011-THIRD-SCHEDULE-WHEN-PACKED",):
                        continue
                applicable.append(r)
                continue

            # Commodity-specific rules
            if r.provision_type == "COMMODITY_SPECIFIC":
                if r.applicable_commodities:
                    if any(target.lower() in c_lower for target in r.applicable_commodities):
                        applicable.append(r)

        return applicable

    def export_specifications(self) -> List[Dict[str, Any]]:
        """Exports all rule specifications for API endpoints and documentation."""
        return [r.to_dict() for r in self._rules]


# Global Knowledge Base Singleton
legal_rule_kb = LegalRuleKnowledgeBase()
