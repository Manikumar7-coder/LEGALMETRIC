from typing import Dict, Any, Tuple, Optional
from app.rules.knowledge_base import legal_rule_kb, LegalRuleSpecification


class BaseRule:
    """
    Statutory Base Rule class supporting both direct evaluation
    and declarative LegalRuleSpecification integration.
    """
    def __init__(
        self,
        rule_id: str,
        field: str,
        description: str,
        required: bool = True,
        applicability: str = "All Packaged Commodities",
        severity: str = "HIGH",  # CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL
        reference: str = "Legal Metrology (Packaged Commodities) Rules, 2011",
        legal_reference: Optional[str] = None,
        requirement: Optional[str] = None,
        applicable_conditions: Optional[str] = None,
        field_to_check: Optional[str] = None,
        validation_type: str = "PRESENCE",
        violation_message: Optional[str] = None,
        evidence_requirement: Optional[str] = None,
        provision_type: str = "RULES_PROVISION",
        punitive_reference: Optional[str] = None,
        image_verifiable: bool = True
    ):
        self.rule_id = rule_id
        
        # Link to registered LegalRuleSpecification if defined in knowledge base
        kb_spec = legal_rule_kb.get_rule_by_id(rule_id)
        
        self.legal_reference = legal_reference or (kb_spec.legal_reference if kb_spec else reference)
        self.reference = self.legal_reference  # backward-compatible alias
        
        self.requirement = requirement or (kb_spec.requirement if kb_spec else description)
        self.description = self.requirement    # backward-compatible alias
        
        self.applicable_conditions = applicable_conditions or (kb_spec.applicable_conditions if kb_spec else applicability)
        self.applicability = self.applicable_conditions  # backward-compatible alias
        
        self.field_to_check = field_to_check or (kb_spec.field_to_check if kb_spec else field)
        self.field = self.field_to_check        # backward-compatible alias
        
        self.validation_type = validation_type or (kb_spec.validation_type if kb_spec else "PRESENCE")
        self.violation_message = violation_message or (kb_spec.violation_message if kb_spec else f"Mandatory declaration '{self.field}' was not detected on the package label.")
        self.evidence_requirement = evidence_requirement or (kb_spec.evidence_requirement if kb_spec else f"Principal display panel image crop showing '{self.field}' declaration.")
        
        self.provision_type = provision_type or (kb_spec.provision_type if kb_spec else "RULES_PROVISION")
        self.severity = severity or (kb_spec.severity if kb_spec else "HIGH")
        self.required = required
        self.punitive_reference = punitive_reference or (kb_spec.punitive_reference if kb_spec else "Rule 32(2), PCR 2011")
        self.image_verifiable = image_verifiable if kb_spec is None else kb_spec.image_verifiable

    def to_dict(self) -> Dict[str, Any]:
        """Returns complete rule specification dictionary."""
        return {
            "rule_id": self.rule_id,
            "legal_reference": self.legal_reference,
            "requirement": self.requirement,
            "applicable_conditions": self.applicable_conditions,
            "field_to_check": self.field_to_check,
            "validation_type": self.validation_type,
            "violation_message": self.violation_message,
            "evidence_requirement": self.evidence_requirement,
            "provision_type": self.provision_type,
            "severity": self.severity,
            "required": self.required,
            "punitive_reference": self.punitive_reference,
            "image_verifiable": self.image_verifiable,
            "field": self.field,
            "description": self.description,
            "reference": self.reference,
            "active": True
        }

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates extracted field data against the legal metrology rule.
        Returns: (is_valid: bool, issue: str | None, recommendation: str | None)
        """
        field_info = extracted_data.get(self.field, {})
        val = str(field_info.get("value", "")).strip()
        status = field_info.get("status", "Missing")

        if not val or status == "Missing":
            if self.required:
                return (
                    False,
                    self.violation_message,
                    f"Statutory requirement under {self.legal_reference}. Verify packaging manually."
                )
            return (True, None, None)

        if status == "Low Confidence":
            return (
                False,
                f"Declaration '{self.field}' detected with low OCR confidence or partially illegible text.",
                f"Perform physical visual inspection of '{self.field}' on the container to verify accuracy."
            )

        return (True, None, None)
