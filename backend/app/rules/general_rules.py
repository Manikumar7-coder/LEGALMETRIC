from typing import Dict, Any, Tuple, Optional
from app.rules.base_rules import BaseRule

class BatchNumberRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="PCR-2011-R6-1-Q",
            field="batch_number",
            description="Lot, code, or batch number for trace and inspection audit.",
            required=False,
            applicability="All Packaged Commodities",
            severity="LOW",
            reference="Rule 6(1)(q), Legal Metrology (Packaged Commodities) Rules, 2011"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        field_info = extracted_data.get("batch_number", {})
        val = str(field_info.get("value", "")).strip()

        if not val or field_info.get("status") == "Missing":
            return (
                False,
                "Batch or Lot number was not detected.",
                "Verify batch/lot number markings on crimp, cap, or base of the container."
            )

        return (True, None, None)


class LegibilityGeneralRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="LMA-2009-SEC-18",
            field="general_legibility",
            description="Declarations must be legible, prominent, and conspicuous.",
            required=True,
            applicability="All Commodities",
            severity="HIGH",
            reference="Section 18, Legal Metrology Act, 2009"
        )

    def validate(self, extracted_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        # Checked via OCR confidence aggregation
        low_confidence_fields = [
            k for k, v in extracted_data.items()
            if isinstance(v, dict) and v.get("status") == "Low Confidence"
        ]

        if low_confidence_fields:
            return (
                False,
                f"Declarations for {', '.join(low_confidence_fields)} suffer from low contrast, small font, or poor legibility.",
                "Section 18 mandates all mandatory declarations to be conspicuous, legible and distinct from the background."
            )

        return (True, None, None)
