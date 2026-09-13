"""
compliance_engine.py
====================
SAFEMETRIC Core Compliance-Validation Engine.

Validates structured declarations extracted from an uploaded product image
against the statutory provisions of the Legal Metrology Act, 2009 and
Legal Metrology (Packaged Commodities) Rules, 2011.

Determinism & Evidence Guarantees:
1. Purely deterministic and explainable rule evaluation logic.
2. For every applicable statutory rule, outputs exactly one of:
   - PASS
   - FAIL
   - NEEDS_REVIEW
   - NOT_APPLICABLE
3. OCR Uncertainty Principle: Low optical recognition confidence (<80%) or
   ambiguous text is NEVER classified as a definite violation; it is strictly
   routed to NEEDS_REVIEW.
4. No Hallucination: Missing values strictly remain None / null; never invented.
5. Strict output format per rule:
   - rule_id
   - legal_reference
   - status
   - explanation
   - detected_value
   - expected_requirement
   - evidence_reference
"""

import re
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple

from app.rules.knowledge_base import (
    legal_rule_kb,
    LegalRuleSpecification,
    LEGAL_RULE_KNOWLEDGE_BASE
)
from app.rules.scorer import (
    compliance_scorer,
    ComplianceScoreBreakdown,
    ComplianceScorer
)

# Statutory Constants
LOW_CONFIDENCE_THRESHOLD = 80.0

SECOND_SCHEDULE_COMMODITIES = {
    "biscuits": "Biscuits",
    "biscuit": "Biscuits",
    "laundry soap": "Laundry Soap",
    "non-soapy detergent": "Non-soapy detergent cakes/bars",
    "detergent": "Non-soapy detergent cakes/bars",
    "toilet soap": "Toilet Soap",
    "bath soap": "Toilet Soap",
    "soap": "Toilet Soap",
    "edible oil": "Edible Oil",
    "vanaspati": "Vanaspati",
    "ghee": "Ghee",
    "rice": "Rice",
    "atta": "Atta",
    "flour": "Flour",
    "tea": "Tea",
    "coffee": "Coffee",
    "milk powder": "Milk Powder",
    "cement": "Cement in bags",
    "paint": "Paint varnish"
}

THIRD_SCHEDULE_EXEMPT_COMMODITIES = [
    "soap", "toilet soap", "bath soap", "laundry soap", "detergent cake",
    "lotion", "body lotion", "skin lotion",
    "cream", "skin cream", "face cream", "cold cream", "vanishing cream"
]


@dataclass
class RuleValidationResult:
    """
    Statutory evaluation result for an individual Legal Metrology rule.
    """
    rule_id: str
    legal_reference: str
    status: str  # PASS | FAIL | NEEDS_REVIEW | NOT_APPLICABLE
    explanation: str
    detected_value: Optional[Any]
    expected_requirement: str
    evidence_reference: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceEvaluation:
    """
    Complete compliance analysis payload containing rule-by-rule verdicts
    and aggregate regulatory determination.
    """
    compliance_status: str  # COMPLIANT | NON-COMPLIANT | REVIEW REQUIRED | PARTIALLY COMPLIANT
    compliance_score: float  # Percentage of applicable rules passed (0.0 - 100.0)
    rule_results: List[RuleValidationResult]
    violations: List[Dict[str, Any]]
    total_rules_evaluated: int
    passed_count: int
    failed_count: int
    needs_review_count: int
    not_applicable_count: int
    score_breakdown: Optional[ComplianceScoreBreakdown] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compliance_status": self.compliance_status,
            "compliance_score": self.compliance_score,
            "rule_results": [r.to_dict() for r in self.rule_results],
            "violations": self.violations,
            "total_rules_evaluated": self.total_rules_evaluated,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "needs_review_count": self.needs_review_count,
            "not_applicable_count": self.not_applicable_count,
            "score_breakdown": self.score_breakdown.to_dict() if self.score_breakdown else None
        }


class ComplianceEngine:
    """
    Statutory Compliance Validation Engine for Legal Metrology inspections.
    """
    def __init__(self, kb=legal_rule_kb):
        self.kb = kb

    def validate(self, extracted_declarations: Dict[str, Any]) -> ComplianceEvaluation:
        """
        Executes complete statutory compliance audit on structured declarations.
        Returns a deterministic, explainable evaluation with PASS/FAIL/NEEDS_REVIEW/NOT_APPLICABLE
        verdicts for every applicable rule.
        """
        if not extracted_declarations:
            extracted_declarations = {}

        results: List[RuleValidationResult] = []
        violations: List[Dict[str, Any]] = []

        # Resolve Commodity Category Context for Schedule routing
        prod_val = self._get_val(extracted_declarations, "product_name") or ""
        gen_val = self._get_val(extracted_declarations, "generic_name") or ""
        commodity_text = f"{prod_val} {gen_val}".lower().strip()

        # ---------------------------------------------------------------------
        # 1. Rule: LMA-2009-SEC-18-MANDATORY (Section 18(1) - Core Declarations)
        # ---------------------------------------------------------------------
        r_sec18 = self.kb.get_rule_by_id("LMA-2009-SEC-18-MANDATORY")
        res_sec18 = self._validate_section_18(extracted_declarations, r_sec18)
        results.append(res_sec18)

        # ---------------------------------------------------------------------
        # 2. Rule: LMA-2009-SEC-36-DEEMED-MFG (Section 36(1) & Section 49)
        # ---------------------------------------------------------------------
        r_sec36 = self.kb.get_rule_by_id("LMA-2009-SEC-36-DEEMED-MFG")
        res_sec36 = self._validate_deemed_manufacturer(extracted_declarations, r_sec36)
        results.append(res_sec36)

        # ---------------------------------------------------------------------
        # 3. Rule: PCR-2011-R6-1-A-MFG-NAME (Manufacturer / Packer / Importer)
        # ---------------------------------------------------------------------
        r_mfg_name = self.kb.get_rule_by_id("PCR-2011-R6-1-A-MFG-NAME")
        res_mfg_name = self._validate_manufacturer_name(extracted_declarations, r_mfg_name)
        results.append(res_mfg_name)

        # ---------------------------------------------------------------------
        # 4. Rule: PCR-2011-R6-1-A-ADDR (Complete Postal Address)
        # ---------------------------------------------------------------------
        r_mfg_addr = self.kb.get_rule_by_id("PCR-2011-R6-1-A-ADDR")
        res_mfg_addr = self._validate_manufacturer_address(extracted_declarations, r_mfg_addr)
        results.append(res_mfg_addr)

        # ---------------------------------------------------------------------
        # 4. Rule: PCR-2011-R6-1-B-GENERIC-NAME (Generic / Common Commodity Name)
        # ---------------------------------------------------------------------
        r_generic = self.kb.get_rule_by_id("PCR-2011-R6-1-B-GENERIC-NAME")
        res_generic = self._validate_generic_name(extracted_declarations, r_generic)
        results.append(res_generic)

        # ---------------------------------------------------------------------
        # 5. Rule: PCR-2011-R6-1-C-NET-QUANTITY (Net Quantity Metric Standards)
        # ---------------------------------------------------------------------
        r_net_qty = self.kb.get_rule_by_id("PCR-2011-R6-1-C-NET-QUANTITY")
        res_net_qty = self._validate_net_quantity(extracted_declarations, r_net_qty)
        results.append(res_net_qty)

        # ---------------------------------------------------------------------
        # 6. Rule: PCR-2011-R12-6-PROHIBITED-QUALIFIERS (Prohibition of 'Approx')
        # ---------------------------------------------------------------------
        r_qualifiers = self.kb.get_rule_by_id("PCR-2011-R12-6-PROHIBITED-QUALIFIERS")
        res_qualifiers = self._validate_prohibited_qualifiers(extracted_declarations, r_qualifiers, commodity_text)
        results.append(res_qualifiers)

        # ---------------------------------------------------------------------
        # 7. Rule: PCR-2011-R13-UNITS-SYMBOLS (Standard SI Units & 'N'/'U' Symbol)
        # ---------------------------------------------------------------------
        r_units = self.kb.get_rule_by_id("PCR-2011-R13-UNITS-SYMBOLS")
        res_units = self._validate_units_symbols(extracted_declarations, r_units)
        results.append(res_units)

        # ---------------------------------------------------------------------
        # 8. Rule: PCR-2011-R6-1-D-DATE (Month & Year of Manufacture/Packing)
        # ---------------------------------------------------------------------
        r_date = self.kb.get_rule_by_id("PCR-2011-R6-1-D-DATE")
        res_date = self._validate_manufacturing_date(extracted_declarations, r_date, commodity_text)
        results.append(res_date)

        # ---------------------------------------------------------------------
        # 9. Rule: PCR-2011-R6-1-E-MRP (MRP & Tax Inclusivity Declaration)
        # ---------------------------------------------------------------------
        r_mrp = self.kb.get_rule_by_id("PCR-2011-R6-1-E-MRP")
        res_mrp = self._validate_mrp(extracted_declarations, r_mrp, commodity_text)
        results.append(res_mrp)

        # ---------------------------------------------------------------------
        # 10. Rule: PCR-2011-R6-1-EA-USP (Unit Sale Price for Multi-Quantity)
        # ---------------------------------------------------------------------
        r_usp = self.kb.get_rule_by_id("PCR-2011-R6-1-EA-USP")
        res_usp = self._validate_unit_sale_price(extracted_declarations, r_usp)
        results.append(res_usp)

        # ---------------------------------------------------------------------
        # 11. Rule: PCR-2011-R6-1-AB-COUNTRY-ORIGIN (Country of Origin)
        # ---------------------------------------------------------------------
        r_country = self.kb.get_rule_by_id("PCR-2011-R6-1-AB-COUNTRY-ORIGIN")
        res_country = self._validate_country_of_origin(extracted_declarations, r_country)
        results.append(res_country)

        # ---------------------------------------------------------------------
        # 12. Rule: PCR-2011-R6-2-CONSUMER-CARE (Consumer Grievance Care Cell)
        # ---------------------------------------------------------------------
        r_care = self.kb.get_rule_by_id("PCR-2011-R6-2-CONSUMER-CARE")
        res_care = self._validate_consumer_care(extracted_declarations, r_care)
        results.append(res_care)

        # ---------------------------------------------------------------------
        # 13. Rule: PCR-2011-R6-3-STICKER-RESTRICTION (Sticker Alteration Check)
        # ---------------------------------------------------------------------
        r_sticker = self.kb.get_rule_by_id("PCR-2011-R6-3-STICKER-RESTRICTION")
        res_sticker = self._validate_sticker_restriction(extracted_declarations, r_sticker)
        results.append(res_sticker)

        # ---------------------------------------------------------------------
        # 14. Rule: PCR-2011-R5-SECOND-SCHEDULE (Standard Pack Quantities)
        # ---------------------------------------------------------------------
        r_sched2 = self.kb.get_rule_by_id("PCR-2011-R5-SECOND-SCHEDULE")
        res_sched2 = self._validate_second_schedule(extracted_declarations, r_sched2, commodity_text)
        results.append(res_sched2)

        # ---------------------------------------------------------------------
        # 15. Rule: PCR-2011-THIRD-SCHEDULE-WHEN-PACKED ('When Packed' Exemption)
        # ---------------------------------------------------------------------
        r_sched3 = self.kb.get_rule_by_id("PCR-2011-THIRD-SCHEDULE-WHEN-PACKED")
        res_sched3 = self._validate_third_schedule(extracted_declarations, r_sched3, commodity_text)
        results.append(res_sched3)

        # ---------------------------------------------------------------------
        # 16. Rule: PCR-2011-R9-LEGIBILITY-CONTRAST-LANG (Legibility, Contrast, Language)
        # ---------------------------------------------------------------------
        r_legibility = self.kb.get_rule_by_id("PCR-2011-R9-LEGIBILITY-CONTRAST-LANG")
        res_legibility = self._validate_legibility(extracted_declarations, r_legibility)
        results.append(res_legibility)

        # ---------------------------------------------------------------------
        # 17. Rule: PCR-2011-R26-STATUTORY-EXEMPTIONS (De-Minimis Exemptions)
        # ---------------------------------------------------------------------
        r_exempt = self.kb.get_rule_by_id("PCR-2011-R26-STATUTORY-EXEMPTIONS")
        res_exempt = self._validate_statutory_exemptions(extracted_declarations, r_exempt)
        results.append(res_exempt)

        # ---------------------------------------------------------------------
        # 18. Rule: PCR-2011-R7-PHYSICAL-MEASUREMENT (Physical Boundary Advisory)
        # ---------------------------------------------------------------------
        r_phys = self.kb.get_rule_by_id("PCR-2011-R7-PHYSICAL-MEASUREMENT")
        res_phys = self._validate_physical_boundary(r_phys)
        results.append(res_phys)

        # ---------------------------------------------------------------------
        # 19. Rule: PCR-2011-R7-FONT-SIZE-COMPLIANCE (Font / Character Height under Rule 7)
        # ---------------------------------------------------------------------
        r_font = self.kb.get_rule_by_id("PCR-2011-R7-FONT-SIZE-COMPLIANCE")
        if r_font:
            res_font = self._validate_font_size(extracted_declarations, r_font)
            results.append(res_font)

        # ---------------------------------------------------------------------
        # 20. Rule: PCR-2011-R8-DECLARATION-PLACEMENT (Placement & Clear Space under Rule 8)
        # ---------------------------------------------------------------------
        r_place = self.kb.get_rule_by_id("PCR-2011-R8-DECLARATION-PLACEMENT")
        if r_place:
            res_place = self._validate_declaration_placement(extracted_declarations, r_place)
            results.append(res_place)

        # ---------------------------------------------------------------------
        # Aggregation & Scoring
        # ---------------------------------------------------------------------
        passed_count = sum(1 for r in results if r.status == "PASS")
        failed_count = sum(1 for r in results if r.status == "FAIL")
        needs_review_count = sum(1 for r in results if r.status == "NEEDS_REVIEW")
        not_applicable_count = sum(1 for r in results if r.status == "NOT_APPLICABLE")

        # Compile legal violations list for enforcement notices
        for r in results:
            if r.status == "FAIL":
                spec = self.kb.get_rule_by_id(r.rule_id)
                severity = spec.severity if spec else "HIGH"
                violations.append({
                    "rule_id": r.rule_id,
                    "field": spec.field_to_check.replace("_", " ").title() if spec else r.rule_id,
                    "issue": r.explanation,
                    "severity": severity,
                    "rule_reference": r.legal_reference,
                    "recommendation": f"Statutory requirement under {r.legal_reference}. Issue statutory notice or rectify packaging.",
                    "evidence_reference": r.evidence_reference
                })

        # Calculate Compliance Score via transparent ComplianceScorer
        breakdown = compliance_scorer.calculate(results, kb=self.kb)
        score = breakdown.score

        # Compliance Status Determination
        has_critical_failure = any(
            r.status == "FAIL" and (self.kb.get_rule_by_id(r.rule_id).severity in ("CRITICAL", "HIGH") if self.kb.get_rule_by_id(r.rule_id) else True)
            for r in results
        )

        if has_critical_failure:
            compliance_status = "NON-COMPLIANT"
        elif needs_review_count > 0:
            compliance_status = "REVIEW REQUIRED"
        elif failed_count > 0:
            compliance_status = "PARTIALLY COMPLIANT"
        else:
            compliance_status = "COMPLIANT"

        return ComplianceEvaluation(
            compliance_status=compliance_status,
            compliance_score=score,
            rule_results=results,
            violations=violations,
            total_rules_evaluated=len(results),
            passed_count=passed_count,
            failed_count=failed_count,
            needs_review_count=needs_review_count,
            not_applicable_count=not_applicable_count,
            score_breakdown=breakdown
        )

    # -------------------------------------------------------------------------
    # Rule Validation Handlers
    # -------------------------------------------------------------------------

    def _validate_section_18(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Section 18(1): Checks presence of minimum statutory declaration bundle."""
        core_fields = ["product_name", "manufacturer", "net_quantity", "mrp", "consumer_care"]
        found_count = sum(1 for f in core_fields if self._get_val(data, f))

        evidence = {
            "core_fields_checked": core_fields,
            "fields_found_count": found_count
        }

        if found_count == 0:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="Pre-packaged commodity lacks mandatory statutory declarations in direct contravention of Section 18(1) of the Act.",
                detected_value="No statutory declarations found",
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # Check if optical confidence on principal display panel is low
        confidences = [self._get_conf(data, f) for f in core_fields if self._get_val(data, f)]
        avg_c = sum(confidences) / len(confidences) if confidences else 0.0

        if avg_c < LOW_CONFIDENCE_THRESHOLD and found_count < 3:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"Statutory declarations detected with low optical confidence ({round(avg_c, 1)}%). Physical inspection of packaging required.",
                detected_value=f"Found {found_count} fields (avg confidence: {round(avg_c, 1)}%)",
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation=f"Packaging bears statutory label declarations ({found_count} of 5 core statutory fields detected).",
            detected_value=f"{found_count} core fields detected",
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_deemed_manufacturer(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Section 36(1) & Section 49: Corporate Liability & Deemed Manufacturer."""
        f_info = self._get_field(data, "manufacturer") or self._get_field(data, "manufacturer_name")
        val = f_info.get("value")
        conf = float(f_info.get("confidence", 0.0))
        evidence = self._make_evidence(f_info)

        if not val:
            if f_info.get("status") == "OCR_UNCERTAIN" or (0 < conf < LOW_CONFIDENCE_THRESHOLD):
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="NEEDS_REVIEW",
                    explanation=f"Manufacturer identification detected with low optical confidence ({conf}%). Physical verification of corporate identity required.",
                    detected_value=f_info.get("raw_text"),
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="No manufacturer or corporate identity detected on packaging, invoking strict penal liability under Section 36(1) of the Act.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if conf < LOW_CONFIDENCE_THRESHOLD:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"Manufacturer identity detected with low optical confidence ({conf}% < {LOW_CONFIDENCE_THRESHOLD}%). Physical inspection required.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        raw = str(f_info.get("raw_text", "")).lower()
        if "marketed by" in raw and "mfd by" not in raw and "manufactured by" not in raw:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="PASS",
                explanation=f"Entity '{val}' declared as marketer. Under Section 49 and Rule 6(1) Explanation II, statutory liability attaches to the marketer as deemed manufacturer.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation=f"Corporate manufacturer identity established for '{val}' under Section 36(1).",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_manufacturer_name(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 6(1)(a): Manufacturer / Packer / Importer identity and role."""
        f_info = self._get_field(data, "manufacturer") or self._get_field(data, "manufacturer_name")
        val = f_info.get("value")
        conf = float(f_info.get("confidence", 0.0))
        evidence = self._make_evidence(f_info)

        if not val:
            if f_info.get("status") == "OCR_UNCERTAIN" or (0 < conf < LOW_CONFIDENCE_THRESHOLD):
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="NEEDS_REVIEW",
                    explanation=f"Manufacturer name detected with low optical confidence ({conf}%). Physical verification required.",
                    detected_value=f_info.get("raw_text"),
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="Mandatory declaration 'Manufacturer / Packer / Importer Name' is missing from the package label.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # OCR Uncertainty Check: Low confidence is NEVER a definite violation
        if conf < LOW_CONFIDENCE_THRESHOLD:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"Manufacturer name detected with low optical confidence ({conf}% < {LOW_CONFIDENCE_THRESHOLD}%). Physical inspection required.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # Verify Role Qualifier
        role_info = self._get_field(data, "manufacturer_packer_importer")
        role = role_info.get("value") or f_info.get("role") or ""
        raw_text = str(f_info.get("raw_text", "")).lower()

        has_role = bool(re.search(r'(?:mfd|manufactured|packed|pkd|imported|marketed)\s*(?:&|and)?\s*(?:packed)?\s*by', raw_text, re.IGNORECASE)) or bool(role)

        if not has_role:
            # Under Explanation I to Rule 6(1), company name without qualifier is deemed manufacturer
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="PASS",
                explanation=f"Manufacturer name '{val}' declared. (Presumed manufacturer under Explanation I to Rule 6(1)).",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation=f"Manufacturer/Packer identity declared as '{val}' with explicit role qualifier.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_manufacturer_address(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 6(1)(a) & Rule 10: Complete Postal Address."""
        f_info = self._get_field(data, "address") or self._get_field(data, "manufacturer_address")
        val = f_info.get("value")
        conf = float(f_info.get("confidence", 0.0))
        evidence = self._make_evidence(f_info)

        if not val:
            if f_info.get("status") == "OCR_UNCERTAIN" or (0 < conf < LOW_CONFIDENCE_THRESHOLD):
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="NEEDS_REVIEW",
                    explanation=f"Manufacturer address detected with low optical confidence ({conf}%). Physical verification of postal address required.",
                    detected_value=f_info.get("raw_text"),
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="Complete postal address of the manufacturer or packer is missing from the packaging.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # Check for obscured / illegible notes
        if "obscured" in str(val).lower() or "unreadable" in str(val).lower():
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation="Manufacturer address is partially obscured or illegible on the packaging substrate. Physical inspection required.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # OCR Uncertainty Check
        if conf < LOW_CONFIDENCE_THRESHOLD:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"Manufacturer address detected with low optical confidence ({conf}%). Physical verification of postal address required.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation=f"Complete postal address declared: '{val[:60]}...'.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_generic_name(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 6(1)(b): Generic / Common Name of Commodity."""
        f_info = self._get_field(data, "generic_name")
        val = f_info.get("value")
        conf = float(f_info.get("confidence", 0.0))
        evidence = self._make_evidence(f_info)

        if not val:
            if f_info.get("status") == "OCR_UNCERTAIN" or (0 < conf < LOW_CONFIDENCE_THRESHOLD):
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="NEEDS_REVIEW",
                    explanation=f"Generic commodity name detected with low optical confidence ({conf}%). Human officer review required.",
                    detected_value=f_info.get("raw_text"),
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )

            # Fallback: Check if product_name itself provides an informative generic descriptor
            prod_info = self._get_field(data, "product_name")
            p_val = prod_info.get("value")
            if p_val and p_val != "Packaged Commodity":
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="PASS",
                    explanation=f"Generic commodity descriptor derived from product title '{p_val}'.",
                    detected_value=p_val,
                    expected_requirement=rule.requirement,
                    evidence_reference=self._make_evidence(prod_info)
                )

            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="Generic or common name of the commodity is missing from the packaging in violation of Rule 6(1)(b).",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if conf < LOW_CONFIDENCE_THRESHOLD:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"Generic name '{val}' detected with low optical confidence ({conf}%). Human officer review required.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation=f"Generic or common name of commodity is clearly declared as '{val}'.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_net_quantity(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 6(1)(c) & Rule 11, 12: Net Quantity in standard metric units."""
        f_info = self._get_field(data, "net_quantity")
        val = f_info.get("value")
        conf = float(f_info.get("confidence", 0.0))
        evidence = self._make_evidence(f_info)

        if not val:
            if f_info.get("status") == "OCR_UNCERTAIN" or (0 < conf < LOW_CONFIDENCE_THRESHOLD):
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="NEEDS_REVIEW",
                    explanation=f"Net quantity numeral detected with low optical confidence ({conf}%). Physical inspection required.",
                    detected_value=f_info.get("raw_text"),
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )
            # Visual-Coverage Heuristic: distinguish DECLARATION_NOT_VERIFIABLE
            # from DECLARATION_CONFIRMED_ABSENT
            if self._is_partial_surface_capture(data, "net_quantity"):
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="NEEDS_REVIEW",
                    explanation=(
                        "Net quantity declaration was not detected in the provided image. "
                        "Other statutory declarations are present, indicating a partial "
                        "surface capture. Unable to verify from provided image — capture "
                        "the front/side/seal containing this declaration."
                    ),
                    detected_value=None,
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="Net quantity declaration was not detected on the package in violation of Rule 6(1)(c).",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if conf < LOW_CONFIDENCE_THRESHOLD:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"Net quantity '{val}' detected with low optical confidence ({conf}%). Physical verification of quantity numeral required.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # Validate standard metric unit
        val_lower = str(val).lower()
        has_metric = bool(re.search(r'(?:\b|\d)(g|gm|gms|kg|kilogram|ml|l|ltr|litre|litres|n|units|pieces)\b', val_lower))

        if not has_metric:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation=f"Net quantity '{val}' does not conform to standard metric units of weight or measure (must use g, kg, ml, l, or N).",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation=f"Net quantity declared in standard metric units: '{val}'.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_prohibited_qualifiers(self, data: Dict[str, Any], rule: LegalRuleSpecification, commodity: str) -> RuleValidationResult:
        """Rule 12(6): Prohibits ambiguous qualifiers ('approx', 'about', 'minimum')."""
        f_info = self._get_field(data, "net_quantity")
        val = f_info.get("value")
        raw = str(f_info.get("raw_text", "")).lower()
        evidence = self._make_evidence(f_info)

        if not val:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NOT_APPLICABLE",
                explanation="Cannot evaluate quantity qualifiers because net quantity declaration is missing.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        combined = f"{val} {raw}".lower()

        # Check for banned qualifiers: 'approx', 'about', 'minimum', 'not less than', 'average'
        prohibited_matches = [w for w in ["approx", "approximate", "approximately", "about", "minimum", "not less than", "average"] if w in combined]

        if prohibited_matches:
            matched_term = prohibited_matches[0]
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation=f"Net quantity uses prohibited ambiguous qualifier '{matched_term}'. Qualifiers like 'approx' or 'about' are strictly prohibited under Rule 12(6).",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # Check for 'when packed'
        if "when packed" in combined:
            is_exempt = any(ex in commodity for ex in THIRD_SCHEDULE_EXEMPT_COMMODITIES)
            if not is_exempt:
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="FAIL",
                    explanation=f"'When packed' qualification is prohibited on commodity '{commodity}'. Third Schedule restricts 'when packed' strictly to soaps, lotions, and creams.",
                    detected_value=val,
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation="Net quantity declaration is free from prohibited ambiguous qualifiers ('approx', 'about', 'minimum').",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_units_symbols(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 13(1)-(5): Prohibits dozen/gross; requires SI metric units."""
        f_info = self._get_field(data, "net_quantity")
        val = f_info.get("value")
        evidence = self._make_evidence(f_info)

        if not val:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NOT_APPLICABLE",
                explanation="Net quantity is missing; unit symbology not applicable.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        val_lower = str(val).lower()
        if any(banned in val_lower for banned in ["dozen", "score", "gross", "great gross"]):
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="Net quantity specifies non-metric collective count ('dozen' / 'gross') in violation of Rule 13(4).",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation="Measurement units conform to International System of Units (SI) standards under Rule 13.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_manufacturing_date(self, data: Dict[str, Any], rule: LegalRuleSpecification, commodity: str) -> RuleValidationResult:
        """Rule 6(1)(d): Month and Year of Manufacture / Pre-packing."""
        mfg_info = self._get_field(data, "manufacturing_date")
        pkd_info = self._get_field(data, "packing_date")

        mfg_val = mfg_info.get("value")
        pkd_val = pkd_info.get("value")

        val = mfg_val or pkd_val
        f_info = mfg_info if mfg_val else pkd_info
        conf = float(f_info.get("confidence", 0.0))
        evidence = self._make_evidence(f_info)

        # Check statutory exemption
        if any(ex in commodity for ex in ["bidi", "incense", "agarbatti"]):
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NOT_APPLICABLE",
                explanation=f"Commodity '{commodity}' is statutorily exempt from date of manufacture under Rule 6(1)(g) Proviso (A).",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if not val:
            if f_info.get("status") == "OCR_UNCERTAIN" or (0 < conf < LOW_CONFIDENCE_THRESHOLD):
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="NEEDS_REVIEW",
                    explanation=f"Manufacturing / Packing date detected with low optical confidence ({conf}%). Physical verification required.",
                    detected_value=f_info.get("raw_text"),
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )
            # Visual-Coverage Heuristic: distinguish DECLARATION_NOT_VERIFIABLE
            # from DECLARATION_CONFIRMED_ABSENT
            if self._is_partial_surface_capture(data, "manufacturing_date"):
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="NEEDS_REVIEW",
                    explanation=(
                        "Manufacturing / Packing date was not detected in the provided "
                        "image. Other statutory declarations are present, indicating a "
                        "partial surface capture. Unable to verify from provided image "
                        "— capture the front/side/seal containing this declaration."
                    ),
                    detected_value=None,
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="Neither Manufacturing Date (Mfg) nor Pre-packing Date (PKD) containing month and year was detected on the package.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # OCR Uncertainty Check
        if conf < LOW_CONFIDENCE_THRESHOLD:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"Manufacturing/Packing date '{val}' detected with low optical confidence ({conf}%). Physical verification of stamped date required.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation=f"Month and year of manufacture/packing declared as '{val}'.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_mrp(self, data: Dict[str, Any], rule: LegalRuleSpecification, commodity: str) -> RuleValidationResult:
        """Rule 6(1)(e): Maximum Retail Price in Rupees inclusive of all taxes."""
        f_info = self._get_field(data, "mrp") or self._get_field(data, "MRP")
        val = f_info.get("value")
        raw = str(f_info.get("raw_text", "") or f_info.get("raw", "")).lower()
        conf = float(f_info.get("confidence", 0.0))
        evidence = self._make_evidence(f_info)

        # Check statutory exemption
        if any(ex in commodity for ex in ["bidi", "lpg cylinder"]):
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NOT_APPLICABLE",
                explanation=f"Commodity '{commodity}' is exempt from retail sale price declaration under Rule 6(1)(g) Proviso (C).",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if not val:
            if f_info.get("status") == "OCR_UNCERTAIN" or (0 < conf < LOW_CONFIDENCE_THRESHOLD):
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="NEEDS_REVIEW",
                    explanation=f"Maximum Retail Price (MRP) detected with low optical confidence ({conf}%). Physical inspection required to verify printed price.",
                    detected_value=f_info.get("raw_text"),
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="Maximum Retail Price (MRP) declaration is completely missing from the package in violation of Rule 6(1)(e) and Section 18 of the Act.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if conf < LOW_CONFIDENCE_THRESHOLD:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"MRP '{val}' detected with low optical confidence ({conf}%). Physical inspection required to verify printed price.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # Currency Check
        has_currency = f_info.get("has_currency", False) or bool(re.search(r'(?:₹|rs\.?|inr)', f"{val} {raw}", re.IGNORECASE))
        if not has_currency:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation=f"MRP '{val}' is printed without official currency designation (₹ / Rs.) in violation of Rule 6(1)(e).",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # Taxes Clause Check
        has_tax = f_info.get("has_tax", False) or bool(re.search(r'(?:incl|inol|inclusive|tax|all\s*taxes)', f"{val} {raw}", re.IGNORECASE))
        if not has_tax:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation=f"MRP '{val}' does not explicitly state '(inclusive of all taxes)' or 'incl. of all taxes'.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation=f"Maximum Retail Price '{val}' declared in Indian Rupees inclusive of all taxes.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_unit_sale_price(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 6(1)(ea) & 6(11): Unit Sale Price for multi-quantity commodities."""
        net_qty = self._get_field(data, "net_quantity")
        qty_num = float(net_qty.get("numeric_value", 0.0))
        usp_info = self._get_field(data, "unit_sale_price")
        val = usp_info.get("value")
        conf = float(usp_info.get("confidence", 0.0))
        evidence = self._make_evidence(usp_info)

        # If net quantity is <= 1.0 (e.g. 1 piece, 1 g, 1 ml), USP is not legally required
        if qty_num > 0.0 and qty_num <= 1.0:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NOT_APPLICABLE",
                explanation="Unit Sale Price (USP) is not required for commodities containing 1 unit or less under Rule 6(1)(ea).",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if not val:
            if qty_num > 1.0:
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="FAIL",
                    explanation="Unit Sale Price (USP) is not declared on pre-packaged commodity exceeding 1 unit/g/ml in violation of Rule 6(1)(ea).",
                    detected_value=None,
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NOT_APPLICABLE",
                explanation="Unit Sale Price requirement indeterminate due to missing net quantity value.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if conf < LOW_CONFIDENCE_THRESHOLD and not usp_info.get("is_calculated", False):
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"Unit Sale Price '{val}' detected with low optical confidence ({conf}%). Physical verification recommended.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation=f"Unit Sale Price declared as '{val}'.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_country_of_origin(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 6(1)(ab): Country of origin declaration."""
        f_info = self._get_field(data, "country_of_origin")
        val = f_info.get("value")
        conf = float(f_info.get("confidence", 0.0))
        evidence = self._make_evidence(f_info)

        if not val:
            if f_info.get("status") == "OCR_UNCERTAIN" or (0 < conf < LOW_CONFIDENCE_THRESHOLD):
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="NEEDS_REVIEW",
                    explanation=f"Country of origin detected with low optical confidence ({conf}%). Verification required.",
                    detected_value=f_info.get("raw_text"),
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="Country of Origin declaration ('Made in India' / 'Country of Origin') was not detected on the package.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if conf < LOW_CONFIDENCE_THRESHOLD:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"Country of origin '{val}' detected with low optical confidence ({conf}%). Verification required.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation=f"Country of origin declared as '{val}'.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_consumer_care(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 6(2): Consumer complaint contact details."""
        f_info = self._get_field(data, "consumer_care")
        val = f_info.get("value")
        conf = float(f_info.get("confidence", 0.0))
        evidence = self._make_evidence(f_info)

        if not val:
            if f_info.get("status") == "OCR_UNCERTAIN" or (0 < conf < LOW_CONFIDENCE_THRESHOLD):
                return RuleValidationResult(
                    rule_id=rule.rule_id,
                    legal_reference=rule.legal_reference,
                    status="NEEDS_REVIEW",
                    explanation=f"Consumer care details detected with low optical confidence ({conf}%). Physical verification of contact helpline required.",
                    detected_value=f_info.get("raw_text"),
                    expected_requirement=rule.requirement,
                    evidence_reference=evidence
                )
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="Consumer care helpline or grievance address is missing from the package in violation of Rule 6(2).",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if conf < LOW_CONFIDENCE_THRESHOLD:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"Consumer care details detected with low optical confidence ({conf}%). Physical verification of contact helpline required.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # Check contact points (telephone or email)
        has_phone = bool(re.search(r'(?:[0-9]{3,4}[-\s]?[0-9]{3}[-\s]?[0-9]{3,4}|[0-9]{10,11}|1800|tel)', str(val), re.IGNORECASE))
        has_email = bool(re.search(r'@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', str(val)))

        if not (has_phone or has_email):
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation="Consumer care declaration lacks valid direct contact points (telephone helpline or email address).",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation=f"Consumer care grievance mechanism declared: '{val}'.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_sticker_restriction(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 6(3) & 6(4): Individual sticker restriction on packages."""
        f_info = self._get_field(data, "label_surface_stickers")
        val = f_info.get("value")
        evidence = self._make_evidence(f_info)

        if not val or val == "None" or val == "NO_STICKERS_DETECTED":
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="PASS",
                explanation="No prohibited individual sticker overlays detected on statutory declarations.",
                detected_value="No stickers",
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if "mrp_reduction" in str(val).lower():
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="PASS",
                explanation="Sticker reducing Maximum Retail Price is permitted under Proviso to Rule 6(3).",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="NEEDS_REVIEW",
            explanation=f"Potential individual sticker detected on packaging ('{val}'). Tactile physical inspection required to confirm if sticker alters statutory declarations.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_second_schedule(self, data: Dict[str, Any], rule: LegalRuleSpecification, commodity: str) -> RuleValidationResult:
        """Rule 5 & Second Schedule: Standard pack quantities."""
        # Check if commodity is scheduled in Second Schedule
        is_scheduled = any(k in commodity for k in SECOND_SCHEDULE_COMMODITIES.keys())

        if not is_scheduled:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NOT_APPLICABLE",
                explanation=f"Commodity '{commodity or 'General Commodity'}' is not restricted to standard pack sizes under the Second Schedule.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference={"commodity": commodity}
            )

        net_qty = self._get_field(data, "net_quantity")
        val = net_qty.get("value")
        evidence = self._make_evidence(net_qty)

        if not val:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NOT_APPLICABLE",
                explanation="Cannot evaluate standard pack size compliance because net quantity is missing.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        # Check for mandatory non-standard disclaimer if non-standard
        raw_text = " ".join([str(f.get("raw_text", "")) for f in data.values() if isinstance(f, dict)]).lower()
        has_disclaimer = "not a standard pack size" in raw_text or "non standard size" in raw_text

        # Standard pack sizes mapping for major scheduled commodities
        # (50g, 100g, 200g, 500g, 1kg, etc.)
        num_m = re.search(r'([0-9]+(?:\.[0-9]+)?)', str(val))
        num = float(num_m.group(1)) if num_m else 0.0

        standard_sizes = [25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 200.0, 250.0, 300.0, 500.0, 750.0, 1.0, 2.0, 3.0, 5.0]

        if num in standard_sizes or (num % 50 == 0) or (num % 100 == 0):
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="PASS",
                explanation=f"Quantity '{val}' conforms to Second Schedule standard packaging quantities.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        if has_disclaimer:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="PASS",
                explanation=f"Non-standard pack size '{val}' prominently declared with mandatory statutory disclaimer under Rule 5.",
                detected_value=val,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="FAIL",
            explanation=f"Scheduled commodity '{commodity}' packed in non-standard pack size '{val}' without mandatory label declaration 'Not a standard pack size under the Legal Metrology (Packaged Commodities) Rules, 2011'.",
            detected_value=val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_third_schedule(self, data: Dict[str, Any], rule: LegalRuleSpecification, commodity: str) -> RuleValidationResult:
        """Rule 11(4) & Third Schedule: 'When Packed' Exemption."""
        net_qty = self._get_field(data, "net_quantity")
        raw = str(net_qty.get("raw_text", "")).lower()
        val = net_qty.get("value")
        evidence = self._make_evidence(net_qty)

        if "when packed" not in raw and "when packed" not in str(val).lower():
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NOT_APPLICABLE",
                explanation="Package does not utilize the 'when packed' qualification.",
                detected_value=None,
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        is_exempt = any(ex in commodity for ex in THIRD_SCHEDULE_EXEMPT_COMMODITIES)

        if is_exempt:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="PASS",
                explanation=f"Commodity '{commodity}' is statutorily permitted to qualify net quantity with 'when packed' under the Third Schedule.",
                detected_value="'when packed' declared",
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="FAIL",
            explanation=f"'When packed' qualification used on commodity '{commodity}'. Under Third Schedule, it is strictly restricted to soaps, lotions, and creams.",
            detected_value="'when packed' declared",
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_legibility(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 9(1) & 9(4): Legibility, Prominence, and Language."""
        confidences = [
            float(f.get("confidence", 0.0))
            for f in data.values()
            if isinstance(f, dict) and f.get("value") is not None and f.get("confidence") is not None
        ]
        avg_c = sum(confidences) / len(confidences) if confidences else 90.0

        evidence = {
            "average_optical_confidence": round(avg_c, 1),
            "total_declarations_evaluated": len(confidences)
        }

        if avg_c < LOW_CONFIDENCE_THRESHOLD:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=f"Package declarations display low optical contrast or legibility (average confidence: {round(avg_c, 1)}%). Physical inspection required to verify contrast under Rule 9(1).",
                detected_value=f"Average confidence: {round(avg_c, 1)}%",
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="PASS",
            explanation="Statutory declarations meet legibility, prominence, and script requirements in English/Hindi under Rule 9.",
            detected_value=f"Average optical confidence: {round(avg_c, 1)}%",
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    def _validate_statutory_exemptions(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 26 & Rule 3: De-Minimis and Institutional Exemptions."""
        net_qty = self._get_field(data, "net_quantity")
        qty_num = float(net_qty.get("numeric_value", 0.0))
        unit = str(net_qty.get("unit", "")).lower()

        # Check for small package exemption <= 10 g / ml
        if qty_num > 0.0 and qty_num <= 10.0 and unit in ("g", "gm", "ml"):
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="PASS",
                explanation=f"Package qualifying under Rule 26(a) de-minimis exemption (net weight/measure <= 10 g/ml).",
                detected_value=f"{qty_num} {unit}",
                expected_requirement=rule.requirement,
                evidence_reference=self._make_evidence(net_qty)
            )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="NOT_APPLICABLE",
            explanation="Standard retail package not subject to Rule 26 de-minimis exemptions.",
            detected_value=None,
            expected_requirement=rule.requirement,
            evidence_reference={"is_exempt": False}
        )

    def _validate_physical_boundary(self, rule: LegalRuleSpecification) -> RuleValidationResult:
        """Rule 7 & First Schedule: Physical Measurement Advisory."""
        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status="NOT_APPLICABLE",
            explanation="Statutory Advisory: Physical numeral height in millimeters (Rule 7) and Maximum Permissible Error (MPE) on net contents require physical measurement tools.",
            detected_value="Routed to physical inspection",
            expected_requirement=rule.requirement,
            evidence_reference={"verification_type": "PHYSICAL_TOOL_REQUIRED"}
        )

    def _validate_font_size(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """
        Rule 7(1)-(3) & Tables I & II: Font & numeral height analysis.
        Compares measured character height against statutory minimums.
        Routes to NEEDS_REVIEW when scale is estimated or bounding box is missing/ambiguous.
        """
        from app.extraction.font_analysis import font_analysis_engine

        font_res = data.get("font_analysis") or data.get("_font_analysis")
        if not font_res or not isinstance(font_res, dict):
            dims = data.get("dimensions") or {}
            font_res = font_analysis_engine.analyze_declarations(
                extracted_declarations=data,
                image_dimensions=dims,
                package_length_mm=data.get("_package_length_mm") or data.get("package_length_mm"),
                package_width_mm=data.get("_package_width_mm") or data.get("package_width_mm")
            )
            data["font_analysis"] = font_res

        overall_status = font_res.get("overall_status", "NEEDS_REVIEW")
        method = font_res.get("estimation_method", "unknown")
        conf = float(font_res.get("confidence", 0.0))
        fields = font_res.get("fields", {})

        # Summarize measured fields
        measured_items = []
        failed_items = []
        for f_key, f_info in fields.items():
            if f_info.get("char_height_mm") is not None:
                item_str = f"{f_info.get('field_label')}: {f_info.get('char_height_mm')} mm (min {f_info.get('min_required_mm')} mm, {f_info.get('status')})"
                measured_items.append(item_str)
                if f_info.get("status") == "FAIL":
                    failed_items.append(item_str)

        evidence = {
            "estimation_method": method,
            "scale_confidence": conf,
            "pixel_to_mm_ratio": font_res.get("pixel_to_mm_ratio"),
            "measured_fields": fields,
            "limitations": font_res.get("limitations")
        }

        if overall_status == "FAIL":
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="FAIL",
                explanation=f"One or more declarations fail minimum character height under Rule 7: {'; '.join(failed_items)}.",
                detected_value="; ".join(failed_items),
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )
        elif overall_status == "PASS":
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="PASS",
                explanation=f"All evaluated declarations meet minimum character height requirements under Rule 7 ({'; '.join(measured_items[:3])}).",
                detected_value=f"Measured {len(measured_items)} declarations (Method: {method})",
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )
        else:
            return RuleValidationResult(
                rule_id=rule.rule_id,
                legal_reference=rule.legal_reference,
                status="NEEDS_REVIEW",
                explanation=(
                    f"Font size compliance requires officer physical verification. "
                    f"Estimation method '{method}' (confidence {int(conf * 100)}%). "
                    f"{font_res.get('limitations', '')}"
                ),
                detected_value=f"Provisional estimates: {'; '.join(measured_items[:2]) if measured_items else 'No measurable boxes'}",
                expected_requirement=rule.requirement,
                evidence_reference=evidence
            )

    def _validate_declaration_placement(self, data: Dict[str, Any], rule: LegalRuleSpecification) -> RuleValidationResult:
        """
        Rule 8(1)-(2): Declaration placement & grouping check on PDP,
        and clear space surrounding net quantity numeral.
        """
        from app.extraction.placement_checker import placement_checker

        placement_res = data.get("placement_analysis") or data.get("_placement_analysis")
        if not placement_res or not isinstance(placement_res, dict):
            dims = data.get("dimensions") or {}
            all_boxes = data.get("_bounding_boxes") or []
            placement_res = placement_checker.analyze_placement(
                extracted_declarations=data,
                all_detections=all_boxes,
                image_dimensions=dims
            )
            data["placement_analysis"] = placement_res

        overall_status = placement_res.get("status", "NEEDS_REVIEW")
        grouping = placement_res.get("grouping", {})
        clear_space = placement_res.get("clear_space", {})
        explanation = placement_res.get("explanation", "")

        evidence = {
            "grouping": grouping,
            "clear_space": clear_space,
            "limitations": placement_res.get("limitations", [])
        }

        detected_val = (
            f"Grouping: {grouping.get('status', 'UNKNOWN')} ({len(grouping.get('fields_analyzed', []))} fields); "
            f"Clear Space: {clear_space.get('status', 'UNKNOWN')}"
        )

        return RuleValidationResult(
            rule_id=rule.rule_id,
            legal_reference=rule.legal_reference,
            status=overall_status,
            explanation=explanation,
            detected_value=detected_val,
            expected_requirement=rule.requirement,
            evidence_reference=evidence
        )

    # -------------------------------------------------------------------------
    # Helper Utilities
    # -------------------------------------------------------------------------

    def _get_field(self, data: Dict[str, Any], field_name: str) -> Dict[str, Any]:
        val = data.get(field_name)
        if isinstance(val, dict):
            return val
        return {}

    def _get_val(self, data: Dict[str, Any], field_name: str) -> Optional[Any]:
        f = self._get_field(data, field_name)
        return f.get("value")

    def _get_conf(self, data: Dict[str, Any], field_name: str) -> float:
        f = self._get_field(data, field_name)
        return float(f.get("confidence", 0.0))

    def _make_evidence(self, field_dict: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "raw_text": field_dict.get("raw_text"),
            "bounding_box": field_dict.get("bounding_box"),
            "confidence": field_dict.get("confidence", 0.0),
            "status": field_dict.get("status")
        }

    def _is_partial_surface_capture(self, data: Dict[str, Any], field_to_exclude: str) -> bool:
        """
        Visual-Coverage Heuristic for Single-Image Inspection.

        Determines whether a missing declaration is likely due to partial
        image coverage (the declaration may exist on an unseen package
        surface) rather than being genuinely absent from the physical
        package.

        Heuristic: If at least 2 of the 5 core Section 18 statutory fields
        (product_name, manufacturer, net_quantity, mrp, consumer_care) are
        successfully detected AND the missing field is NOT among them, the
        image likely captures only a portion of the package surface.

        Returns True  → DECLARATION_NOT_VERIFIABLE (partial surface capture)
        Returns False → DECLARATION_CONFIRMED_ABSENT (sufficient coverage)
        """
        core_fields = ["product_name", "manufacturer", "net_quantity", "mrp", "consumer_care"]
        # Exclude the field under test so it doesn't count toward coverage
        check_fields = [f for f in core_fields if f != field_to_exclude]
        detected_count = sum(1 for f in check_fields if self._get_val(data, f))
        # If ≥2 OTHER core fields are detected, image has substantial label
        # content and the missing field is likely on another package surface
        return detected_count >= 2


# Global Compliance Validation Engine Singleton
compliance_engine = ComplianceEngine()
