"""
test_rules_knowledge_base.py
============================
Automated verification test suite for the SAFEMETRIC Legal-Rule Knowledge Base.

Validates that:
1. Every rule definition contains all required statutory fields:
   - rule_id
   - legal_reference
   - requirement
   - applicable_conditions
   - field_to_check
   - validation_type
   - violation_message
   - evidence_requirement
2. Clear statutory distinctions are maintained (Act vs Rules vs Commodity-specific vs Physical boundaries).
3. Query and lookup operations operate correctly.
4. BaseRule and RuleEngine integrate directly with the knowledge base.
5. REST API endpoint (/api/rules) serves the complete structured schema.
"""

import sys
from fastapi.testclient import TestClient
from app.main import app
from app.rules.knowledge_base import (
    legal_rule_kb,
    LegalRuleSpecification,
    LEGAL_RULE_KNOWLEDGE_BASE
)
from app.rules.rule_engine import rule_engine


MANDATORY_KEYS = [
    "rule_id",
    "legal_reference",
    "requirement",
    "applicable_conditions",
    "field_to_check",
    "validation_type",
    "violation_message",
    "evidence_requirement"
]


def test_knowledge_base_minimum_fields():
    """Verify that every single rule contains all mandatory fields with non-empty values."""
    print("\n--- 1. Testing Mandatory Field Specification on All Rules ---")
    rules = legal_rule_kb.get_all_rules()
    assert len(rules) >= 15, f"Expected at least 15 verified statutory rules, found {len(rules)}"
    print(f"  Total verified rules in knowledge base: {len(rules)}")

    for r in rules:
        r_dict = r.to_dict()
        for key in MANDATORY_KEYS:
            assert key in r_dict, f"Rule '{r.rule_id}' is missing mandatory key '{key}'"
            val = r_dict[key]
            assert val is not None and str(val).strip() != "", (
                f"Rule '{r.rule_id}' has empty value for mandatory key '{key}'"
            )
        print(f"  [PASS] Rule: {r.rule_id:<36} | Ref: {r.legal_reference[:40]}...")

    print(f"  [SUCCESS] All {len(rules)} rules strictly contain all 8 mandatory specification fields.")


def test_statutory_taxonomy_distinctions():
    """Verify clear distinction between Act, Rules, Commodity-Specific, and Physical Boundary provisions."""
    print("\n--- 2. Testing Statutory Taxonomy & Category Distinctions ---")
    
    act_rules = legal_rule_kb.get_rules_by_provision_type("ACT_PROVISION")
    rules_provisions = legal_rule_kb.get_rules_by_provision_type("RULES_PROVISION")
    commodity_specific = legal_rule_kb.get_rules_by_provision_type("COMMODITY_SPECIFIC")
    physical_boundaries = legal_rule_kb.get_rules_by_provision_type("PHYSICAL_BOUNDARY")

    print(f"  Act Provisions count:             {len(act_rules)}")
    print(f"  Rules Provisions count:           {len(rules_provisions)}")
    print(f"  Commodity-Specific count:         {len(commodity_specific)}")
    print(f"  Physical Boundary Advisory count: {len(physical_boundaries)}")

    assert len(act_rules) >= 2, "Expected at least 2 Act provisions (Sections 18 and 36/49)"
    assert len(rules_provisions) >= 10, "Expected at least 10 Rules provisions"
    assert len(commodity_specific) >= 2, "Expected Second and Third Schedule commodity-specific rules"
    assert len(physical_boundaries) >= 1, "Expected physical boundary advisory for uncalibrated image testing"

    # Verify Act provisions mention Act
    for r in act_rules:
        assert "Act, 2009" in r.legal_reference, f"Act rule {r.rule_id} missing Act citation"
        print(f"    * Act Rule: {r.rule_id} -> {r.legal_reference}")

    # Verify Commodity-specific rules specify applicable commodities
    for r in commodity_specific:
        assert r.applicable_commodities is not None and len(r.applicable_commodities) > 0, (
            f"Commodity-specific rule {r.rule_id} missing applicable commodities list"
        )
        print(f"    * Commodity-Specific Rule: {r.rule_id} -> {r.applicable_commodities[:3]}...")

    # Verify physical boundary rules are marked non-image-verifiable
    for r in physical_boundaries:
        assert r.image_verifiable is False, f"Physical boundary rule {r.rule_id} must have image_verifiable=False"
        print(f"    * Physical Boundary: {r.rule_id} -> image_verifiable={r.image_verifiable}")

    print("  [SUCCESS] Legal taxonomy categories strictly segregated.")


def test_query_operations():
    """Verify lookup operations by ID, field, and commodity class."""
    print("\n--- 3. Testing Knowledge Base Query Operations ---")
    
    # 1. Lookup by ID
    mrp_rule = legal_rule_kb.get_rule_by_id("PCR-2011-R6-1-E-MRP")
    assert mrp_rule is not None
    assert mrp_rule.field_to_check == "mrp"
    assert "Rule 6(1)(e)" in mrp_rule.legal_reference
    print(f"  Lookup by ID (PCR-2011-R6-1-E-MRP) OK: {mrp_rule.requirement[:60]}...")

    # 2. Lookup by Field
    qty_rules = legal_rule_kb.get_rules_by_field("net_quantity")
    assert len(qty_rules) >= 3, "Expected multiple net_quantity rules (Standard, Qualifiers, Units, Schedules)"
    print(f"  Lookup by Field ('net_quantity') OK: Found {len(qty_rules)} rules: {[r.rule_id for r in qty_rules]}")

    # 3. Commodity-specific filtering (e.g. Soap vs Potato Chips)
    soap_rules = legal_rule_kb.get_rules_for_commodity("Toilet Soap")
    chips_rules = legal_rule_kb.get_rules_for_commodity("Potato Chips")

    soap_ids = [r.rule_id for r in soap_rules]
    chips_ids = [r.rule_id for r in chips_rules]

    # Soap should include Third Schedule 'when packed' rule
    assert "PCR-2011-THIRD-SCHEDULE-WHEN-PACKED" in soap_ids
    # Potato chips (food) must NOT include Third Schedule 'when packed' rule
    assert "PCR-2011-THIRD-SCHEDULE-WHEN-PACKED" not in chips_ids

    print(f"  Commodity Filter (Soap):  {len(soap_rules)} rules applicable (includes Third Schedule)")
    print(f"  Commodity Filter (Chips): {len(chips_rules)} rules applicable (excludes 'when packed')")
    print("  [SUCCESS] Knowledge base query operations passed.")


def test_base_rule_integration():
    """Verify that BaseRule instances in RuleEngine inherit and expose all knowledge base fields."""
    print("\n--- 4. Testing BaseRule and RuleEngine Integration ---")
    engine_rules = rule_engine.rules
    assert len(engine_rules) >= 12
    print(f"  RuleEngine contains {len(engine_rules)} active statutory rules.")

    for r in engine_rules:
        r_dict = r.to_dict()
        for key in MANDATORY_KEYS:
            assert key in r_dict, f"Engine rule '{r.rule_id}' missing key '{key}'"
            assert r_dict[key] is not None and str(r_dict[key]).strip() != "", (
                f"Engine rule '{r.rule_id}' has empty value for key '{key}'"
            )
        # Verify backward-compatibility aliases exist
        assert "field" in r_dict
        assert "description" in r_dict
        assert "reference" in r_dict

    print("  [PASS] Every BaseRule in RuleEngine exposes all mandatory fields.")


def test_api_rules_endpoint():
    """Verify that GET /api/rules returns the complete structured knowledge base schema."""
    print("\n--- 5. Testing REST API Endpoint (GET /api/rules) ---")
    client = TestClient(app)
    res = client.get("/api/rules")
    assert res.status_code == 200, f"GET /api/rules failed: {res.text}"
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 12
    
    first_rule = data[0]
    for key in MANDATORY_KEYS:
        assert key in first_rule, f"API response missing mandatory key '{key}'"
    
    print(f"  GET /api/rules returned {len(data)} rule specifications successfully.")
    print(f"  Sample API Rule #1: ID='{first_rule['rule_id']}', Field='{first_rule['field_to_check']}', Ref='{first_rule['legal_reference'][:40]}'")
    print("  [SUCCESS] REST API endpoint verified.")


def run_all_tests():
    print("=" * 70)
    print(" TESTING SAFEMETRIC LEGAL-RULE KNOWLEDGE BASE SPECIFICATIONS")
    print("=" * 70)
    
    test_knowledge_base_minimum_fields()
    test_statutory_taxonomy_distinctions()
    test_query_operations()
    test_base_rule_integration()
    test_api_rules_endpoint()
    
    print("\n" + "=" * 70)
    print(" ALL LEGAL-RULE KNOWLEDGE BASE TESTS PASSED (100%)!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
