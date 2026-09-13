"""
service.py
==========
SAFEMETRIC Evidence Linking & Traceability Service.

Constructs, links, and manages visual evidence records connecting:
- Page/Image Identifier
- Bounding Box Polygon Coordinates
- OCR Raw Text
- Optical Recognition Confidence
- Associated Statutory Declaration
- Associated Statutory Rule & Violation

Guarantees full statutory traceability: Every violation can be queried
and resolved back to visual ground truth on the physical package substrate.
"""

from typing import Dict, Any, List, Optional
from app.evidence.models import EvidenceItem, EvidenceStore
from app.rules.compliance_engine import RuleValidationResult, ComplianceEvaluation
from app.rules.knowledge_base import legal_rule_kb

# Canonical mapping from declaration fields to primary statutory rules
DECLARATION_TO_PRIMARY_RULE_MAP: Dict[str, Dict[str, str]] = {
    "product_name": {
        "rule_id": "PCR-2011-R6-1-B-GENERIC-NAME",
        "legal_reference": "Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "generic_name": {
        "rule_id": "PCR-2011-R6-1-B-GENERIC-NAME",
        "legal_reference": "Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "manufacturer": {
        "rule_id": "PCR-2011-R6-1-A-MFG-NAME",
        "legal_reference": "Rule 6(1)(a) & Rule 10(1)-(2), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "manufacturer_name": {
        "rule_id": "PCR-2011-R6-1-A-MFG-NAME",
        "legal_reference": "Rule 6(1)(a) & Rule 10(1)-(2), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "packer": {
        "rule_id": "PCR-2011-R6-1-A-MFG-NAME",
        "legal_reference": "Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "importer": {
        "rule_id": "PCR-2011-R6-1-A-MFG-NAME",
        "legal_reference": "Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "address": {
        "rule_id": "PCR-2011-R6-1-A-ADDR",
        "legal_reference": "Rule 6(1)(a) & Rule 10(1), Explanation, Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "manufacturer_address": {
        "rule_id": "PCR-2011-R6-1-A-ADDR",
        "legal_reference": "Rule 6(1)(a) & Rule 10(1), Explanation, Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "net_quantity": {
        "rule_id": "PCR-2011-R6-1-C-NET-QUANTITY",
        "legal_reference": "Rule 6(1)(c), Rule 11(1), and Rule 12(1), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "mrp": {
        "rule_id": "PCR-2011-R6-1-E-MRP",
        "legal_reference": "Rule 6(1)(e), Rule 2(m), PCR 2011 and Section 18, Legal Metrology Act, 2009"
    },
    "MRP": {
        "rule_id": "PCR-2011-R6-1-E-MRP",
        "legal_reference": "Rule 6(1)(e), Rule 2(m), PCR 2011 and Section 18, Legal Metrology Act, 2009"
    },
    "unit_sale_price": {
        "rule_id": "PCR-2011-R6-1-EA-USP",
        "legal_reference": "Rule 6(1)(ea) & Rule 6(11), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "manufacturing_date": {
        "rule_id": "PCR-2011-R6-1-D-DATE",
        "legal_reference": "Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "packing_date": {
        "rule_id": "PCR-2011-R6-1-D-DATE",
        "legal_reference": "Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "best_before": {
        "rule_id": "PCR-2011-R6-1-D-DATE",
        "legal_reference": "Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "consumer_care": {
        "rule_id": "PCR-2011-R6-2-CONSUMER-CARE",
        "legal_reference": "Rule 6(2), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "country_of_origin": {
        "rule_id": "PCR-2011-R6-1-AB-COUNTRY-ORIGIN",
        "legal_reference": "Rule 6(1)(ab) & Rule 10(1) Second Proviso, Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "batch_number": {
        "rule_id": "PCR-2011-R6-1-D-DATE",
        "legal_reference": "Rule 6(1)(d) & Rule 6(1)(f), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "ingredients": {
        "rule_id": "LMA-2009-SEC-18-MANDATORY",
        "legal_reference": "Section 18(1), Legal Metrology Act, 2009 read with Rule 6, PCR 2011"
    },
    "fssai_license": {
        "rule_id": "PCR-2011-R6-1-A-MFG-NAME",
        "legal_reference": "Rule 6(1) Explanation III, Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "nutrition_info": {
        "rule_id": "LMA-2009-SEC-18-MANDATORY",
        "legal_reference": "Section 18(1), Legal Metrology Act, 2009 read with Rule 6, PCR 2011"
    },
    "use_by": {
        "rule_id": "PCR-2011-R6-1-D-DATE",
        "legal_reference": "Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011"
    },
    "label_surface_stickers": {
        "rule_id": "PCR-2011-R6-3-STICKER-RESTRICTION",
        "legal_reference": "Rule 6(3) & Rule 6(4), Legal Metrology (Packaged Commodities) Rules, 2011"
    }
}


class EvidenceService:
    """
    Core Evidence Subsystem Service.
    Preserves and retrieves bidirectional links between raw packaging image substrates,
    OCR bounding boxes, declarations, and statutory compliance violations.
    """

    def create_evidence_item(
        self,
        image_id: str,
        associated_declaration: str,
        bounding_box: Optional[List[List[int]]] = None,
        ocr_text: Optional[str] = None,
        confidence: float = 0.0,
        associated_rule: Optional[str] = None,
        legal_reference: Optional[str] = None,
        declaration_value: Optional[Any] = None,
        page_number: int = 1,
        is_violation: bool = False,
        violation_details: Optional[Dict[str, Any]] = None,
        visual_status: Optional[str] = None
    ) -> EvidenceItem:
        """
        Instantiates a canonical EvidenceItem ensuring all 6 statutory parameters are recorded.
        """
        # Auto-resolve statutory rule citation if not explicitly given
        if not associated_rule:
            if associated_declaration in DECLARATION_TO_PRIMARY_RULE_MAP:
                rule_info = DECLARATION_TO_PRIMARY_RULE_MAP[associated_declaration]
                associated_rule = rule_info["rule_id"]
                if not legal_reference:
                    legal_reference = rule_info["legal_reference"]
            else:
                associated_rule = "LMA-2009-SEC-18-MANDATORY"
                if not legal_reference:
                    legal_reference = "Section 18(1), Legal Metrology Act, 2009"

        # Resolve visual status
        if visual_status is None:
            if bounding_box is not None and len(bounding_box) >= 4:
                visual_status = "LOW_CONFIDENCE" if (confidence < 80.0 and confidence > 0) else "DETECTED_ON_IMAGE"
            else:
                visual_status = "MISSING_FROM_IMAGE"

        return EvidenceItem(
            image_id=str(image_id),
            page_number=page_number,
            bounding_box=bounding_box,
            ocr_text=ocr_text,
            confidence=round(float(confidence), 1),
            associated_declaration=str(associated_declaration),
            associated_rule=associated_rule,
            declaration_value=declaration_value,
            legal_reference=legal_reference,
            is_violation=is_violation,
            violation_details=violation_details,
            visual_status=visual_status
        )

    def build_evidence_store(
        self,
        image_id: str,
        extracted_declarations: Dict[str, Any],
        rule_results: Optional[List[RuleValidationResult]] = None,
        violations: Optional[List[Dict[str, Any]]] = None,
        inspection_id: Optional[str] = None,
        image_path: Optional[str] = None,
        page_number: int = 1
    ) -> EvidenceStore:
        """
        Builds a comprehensive EvidenceStore linking all declarations and statutory violations
        directly to the original image substrate.
        """
        store = EvidenceStore(
            image_id=str(image_id),
            inspection_id=str(inspection_id) if inspection_id else None,
            image_path=image_path,
            page_count=1
        )

        if not extracted_declarations:
            extracted_declarations = {}

        # Index violations by rule_id and field for rapid matching
        violations_by_rule: Dict[str, Dict[str, Any]] = {}
        violations_by_field: Dict[str, Dict[str, Any]] = {}
        if violations:
            for v in violations:
                r_id = str(v.get("rule_id", "")).strip()
                f_name = str(v.get("field", "")).lower().strip().replace(" ", "_")
                if r_id:
                    violations_by_rule[r_id] = v
                if f_name:
                    violations_by_field[f_name] = v

        # Index rule validation results by rule_id
        results_by_rule: Dict[str, RuleValidationResult] = {}
        if rule_results:
            for r in rule_results:
                results_by_rule[r.rule_id] = r

        # Set of fields processed to avoid duplicate evidence records
        processed_fields = set()

        # ---------------------------------------------------------------------
        # 1. Process Extracted Declarations
        # ---------------------------------------------------------------------
        for field_name, f_data in extracted_declarations.items():
            if field_name.startswith("_") or not isinstance(f_data, dict):
                continue

            # Canonicalize duplicate aliases (e.g. MRP and mrp, manufacturer and manufacturer_name)
            canon_name = "mrp" if field_name.upper() == "MRP" else field_name
            if canon_name in processed_fields:
                continue
            processed_fields.add(canon_name)

            val = f_data.get("value")
            raw = f_data.get("raw_text") or f_data.get("raw")
            conf = float(f_data.get("confidence", 0.0))
            box = f_data.get("bounding_box")

            # Determine associated statutory rule
            rule_info = DECLARATION_TO_PRIMARY_RULE_MAP.get(canon_name, {})
            rule_id = rule_info.get("rule_id", "LMA-2009-SEC-18-MANDATORY")
            legal_ref = rule_info.get("legal_reference", "Section 18(1), Legal Metrology Act, 2009")

            # Check if this field failed in rule evaluation or violation list
            is_viol = False
            v_details = None

            if rule_id and rule_id in violations_by_rule:
                is_viol = True
                v_details = violations_by_rule[rule_id]
            elif canon_name in violations_by_field:
                is_viol = True
                v_details = violations_by_field[canon_name]
            elif rule_id and rule_id in results_by_rule:
                r_res = results_by_rule[rule_id]
                if r_res.status == "FAIL":
                    is_viol = True
                    v_details = {
                        "rule_id": r_res.rule_id,
                        "field": canon_name,
                        "issue": r_res.explanation,
                        "rule_reference": r_res.legal_reference
                    }

            # Visual status determination
            if box is not None and len(box) >= 4:
                visual_status = "LOW_CONFIDENCE" if (conf < 80.0 and conf > 0) else "DETECTED_ON_IMAGE"
            else:
                visual_status = "MISSING_FROM_IMAGE" if val is None else "DETECTED_ON_IMAGE"

            ev_item = EvidenceItem(
                image_id=str(image_id),
                page_number=page_number,
                bounding_box=box,
                ocr_text=raw,
                confidence=conf,
                associated_declaration=canon_name,
                associated_rule=rule_id,
                declaration_value=val,
                legal_reference=legal_ref,
                is_violation=is_viol,
                violation_details=v_details,
                visual_status=visual_status
            )
            store.add_item(ev_item)

        # ---------------------------------------------------------------------
        # 2. Process Any Remaining Violations (e.g. Schedule rules or unmapped rules)
        # ---------------------------------------------------------------------
        if rule_results:
            for r in rule_results:
                if r.status == "FAIL":
                    # Check if already covered by an evidence item
                    existing = store.trace_violation(r.rule_id)
                    if not existing:
                        spec = legal_rule_kb.get_rule_by_id(r.rule_id)
                        target_field = spec.field_to_check if spec else r.rule_id.lower()
                        
                        # Extract evidence reference from rule result
                        ev_ref = r.evidence_reference if isinstance(r.evidence_reference, dict) else {}
                        box = ev_ref.get("bounding_box")
                        raw = ev_ref.get("raw_text")
                        conf = float(ev_ref.get("confidence", 0.0))

                        v_item = EvidenceItem(
                            image_id=str(image_id),
                            page_number=page_number,
                            bounding_box=box,
                            ocr_text=raw,
                            confidence=conf,
                            associated_declaration=target_field,
                            associated_rule=r.rule_id,
                            declaration_value=r.detected_value,
                            legal_reference=r.legal_reference,
                            is_violation=True,
                            violation_details={
                                "rule_id": r.rule_id,
                                "field": target_field,
                                "issue": r.explanation,
                                "rule_reference": r.legal_reference
                            },
                            visual_status="DETECTED_ON_IMAGE" if (box and len(box) >= 4) else "MISSING_FROM_IMAGE"
                        )
                        store.add_item(v_item)

        return store

    def trace_violation_to_visual_evidence(
        self,
        store: EvidenceStore,
        rule_id_or_field: str
    ) -> Optional[EvidenceItem]:
        """
        Locates the visual evidence record for a given violation.
        Guarantees statutory traceability to bounding boxes and source OCR text.
        """
        return store.trace_violation(rule_id_or_field)


# Global Evidence Service Singleton
evidence_service = EvidenceService()
