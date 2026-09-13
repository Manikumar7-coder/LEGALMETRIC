from typing import Dict, Any, List
from app.rules.packaged_commodities import (
    GenericNameRule,
    MRPValidationRule,
    NetQuantityRule,
    UnitSalePriceRule,
    ManufacturerIdentityRule,
    ManufacturerAddressRule,
    ConsumerCareRule,
    ManufacturingDateRule,
    BestBeforeRule,
    CountryOfOriginRule
)
from app.rules.general_rules import BatchNumberRule, LegibilityGeneralRule

class RuleEngine:
    def __init__(self):
        self.rules = [
            GenericNameRule(),
            ManufacturerIdentityRule(),
            ManufacturerAddressRule(),
            NetQuantityRule(),
            MRPValidationRule(),
            UnitSalePriceRule(),
            ManufacturingDateRule(),
            ConsumerCareRule(),
            CountryOfOriginRule(),
            BestBeforeRule(),
            BatchNumberRule(),
            LegibilityGeneralRule()
        ]

    def evaluate(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes Legal Metrology validation across all applicable statutory rules.
        Calculates compliance score, collects violations, and determines regulatory status.
        """
        applicable_count = 0
        detected_count = 0
        missing_count = 0
        invalid_count = 0
        low_conf_count = 0
        violations: List[Dict[str, Any]] = []

        has_critical_failure = False
        has_review_condition = False

        for rule in self.rules:
            # General legibility rule is a secondary evaluation
            if rule.rule_id == "LMA-2009-SEC-18":
                is_valid, issue, rec = rule.validate(extracted_data)
                if not is_valid:
                    has_review_condition = True
                    violations.append({
                        "field": "General Legibility",
                        "issue": issue,
                        "severity": rule.severity,
                        "rule_reference": rule.reference,
                        "recommendation": rec
                    })
                continue

            # Core statutory declaration evaluation
            applicable_count += 1
            field_data = extracted_data.get(rule.field, {})
            status = field_data.get("status", "Missing")

            if status == "Found":
                is_valid, issue, rec = rule.validate(extracted_data)
                if is_valid:
                    detected_count += 1
                else:
                    invalid_count += 1
                    if rule.severity == "HIGH":
                        has_critical_failure = True
                    else:
                        has_review_condition = True

                    violations.append({
                        "field": rule.field.replace("_", " ").title(),
                        "issue": issue,
                        "severity": rule.severity,
                        "rule_reference": rule.reference,
                        "recommendation": rec
                    })
            elif status == "Low Confidence":
                low_conf_count += 1
                has_review_condition = True
                violations.append({
                    "field": rule.field.replace("_", " ").title(),
                    "issue": f"Declaration for {rule.field.replace('_', ' ')} detected with low OCR confidence.",
                    "severity": "MEDIUM",
                    "rule_reference": rule.reference,
                    "recommendation": "Inspect the container physically to verify declaration accuracy."
                })
            else: # Missing
                missing_count += 1
                if rule.required:
                    if rule.severity == "HIGH":
                        has_critical_failure = True
                    else:
                        has_review_condition = True

                    violations.append({
                        "field": rule.field.replace("_", " ").title(),
                        "issue": f"Mandatory declaration '{rule.field.replace('_', ' ').title()}' is not present on the label.",
                        "severity": rule.severity,
                        "rule_reference": rule.reference,
                        "recommendation": f"Statutory requirement under {rule.reference}. Verify package manually."
                    })
                else:
                    # Optional rule missing (e.g. batch number or best-before on non-perishable)
                    pass

        # Calculate compliance score (0 - 100%)
        if applicable_count > 0:
            score = round((detected_count / applicable_count) * 100, 1)
        else:
            score = 0.0

        # Determine Compliance Status
        # PRINCIPLE: Compliance score alone must NOT determine legal compliance.
        # Critical missing declarations must result in NON-COMPLIANT.
        if has_critical_failure:
            compliance_status = "NON-COMPLIANT"
        elif has_review_condition or low_conf_count > 0:
            compliance_status = "REVIEW REQUIRED"
        elif score >= 90.0 and len(violations) == 0:
            compliance_status = "COMPLIANT"
        elif score >= 70.0:
            compliance_status = "PARTIALLY COMPLIANT"
        else:
            compliance_status = "NON-COMPLIANT"

        return {
            "compliance_status": compliance_status,
            "compliance_score": score,
            "applicable_fields": applicable_count,
            "detected_fields": detected_count,
            "missing_fields": missing_count,
            "invalid_fields": invalid_count,
            "low_confidence_fields": low_conf_count,
            "violations": violations
        }

    def get_all_rules_metadata(self) -> List[Dict[str, Any]]:
        """Returns list of configured rules with full statutory metadata for the /api/rules endpoint."""
        return [r.to_dict() for r in self.rules]


rule_engine = RuleEngine()
