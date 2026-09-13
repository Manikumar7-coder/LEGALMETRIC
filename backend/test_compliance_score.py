"""
test_compliance_score.py
========================
Unit test suite for the SAFEMETRIC Compliance-Score Calculation Engine.

Verifies:
1. Fully Compliant Case (100.0% score, 0 infractions)
2. Partially Compliant Case (calibrated score, non-critical infractions)
3. Non-Compliant Case (penalized score, critical/high infractions)
4. Needs-Review Case (provisional 50% partial credit, optical uncertainty handling)
5. Not-Applicable Rules (strict exclusion from denominator, zero penalty)
6. Explainability & Calculation Details (formula, earned points, rule-level breakdown)
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.rules.scorer import (
    ComplianceScorer,
    compliance_scorer,
    ComplianceScoreBreakdown,
    RuleScoreContribution
)
from app.rules.compliance_engine import (
    compliance_engine,
    RuleValidationResult,
    ComplianceEvaluation
)
from app.rules.knowledge_base import legal_rule_kb


class MockRuleResult:
    """Helper mock to simulate RuleValidationResult."""
    def __init__(self, rule_id: str, status: str, explanation: str = ""):
        self.rule_id = rule_id
        self.legal_reference = f"Ref for {rule_id}"
        self.status = status
        self.explanation = explanation or f"Rule {rule_id} status: {status}"
        self.detected_value = None
        self.expected_requirement = f"Requirement for {rule_id}"
        self.evidence_reference = {}


def test_fully_compliant_case():
    """
    Test Case 1: Fully Compliant Case.
    All applicable rules pass without infractions.
    Expected score = 100.0%, status = COMPLIANT.
    """
    print("\n--- 1. Testing Fully Compliant Case ---")

    rules = [
        MockRuleResult(f"RULE-PASS-{i}", "PASS") for i in range(1, 11)
    ] + [
        MockRuleResult(f"RULE-NA-{i}", "NOT_APPLICABLE") for i in range(1, 6)
    ]

    scorer = ComplianceScorer()
    breakdown = scorer.calculate(rules, kb=legal_rule_kb)

    assert breakdown.score == 100.0, f"Expected 100.0, got {breakdown.score}"
    assert breakdown.applicable_count == 10
    assert breakdown.not_applicable_count == 5
    assert breakdown.passed_count == 10
    assert breakdown.failed_count == 0
    assert breakdown.needs_review_count == 0
    assert breakdown.points_earned == 10.0
    assert breakdown.points_possible == 10.0
    assert "100.0%" in breakdown.formula
    assert "All 10 applicable statutory requirements were fully satisfied" in breakdown.explanation or "10 rules fully passed" in breakdown.explanation

    print("  [PASS] Score is 100.0% with 10.0/10.0 points earned.")
    print(f"  Formula:     {breakdown.formula}")
    print(f"  Explanation: {breakdown.explanation}")


def test_partially_compliant_case():
    """
    Test Case 2: Partially Compliant Case.
    Majority of rules pass, but minor/non-critical infractions occur.
    Expected: calibrated score proportional to passed rules.
    """
    print("\n--- 2. Testing Partially Compliant Case ---")

    # 8 PASS, 2 FAIL, 4 NOT_APPLICABLE -> 8/10 = 80.0%
    rules = [
        MockRuleResult(f"RULE-PASS-{i}", "PASS") for i in range(1, 9)
    ] + [
        MockRuleResult("PCR-2011-R6-1-B-GENERIC-NAME", "FAIL", "Generic name missing"),
        MockRuleResult("PCR-2011-R6-1-EA-USP", "FAIL", "Unit sale price absent")
    ] + [
        MockRuleResult(f"RULE-NA-{i}", "NOT_APPLICABLE") for i in range(1, 5)
    ]

    scorer = ComplianceScorer()
    breakdown = scorer.calculate(rules, kb=legal_rule_kb)

    expected_score = round((8.0 / 10.0) * 100.0, 1)  # 80.0%
    assert breakdown.score == expected_score, f"Expected {expected_score}, got {breakdown.score}"
    assert breakdown.applicable_count == 10
    assert breakdown.passed_count == 8
    assert breakdown.failed_count == 2
    assert breakdown.needs_review_count == 0
    assert breakdown.points_earned == 8.0
    assert breakdown.points_possible == 10.0

    print(f"  [PASS] Partially compliant score verified: {breakdown.score}% ({breakdown.points_earned}/{breakdown.points_possible} pts).")
    print(f"  Formula:     {breakdown.formula}")


def test_non_compliant_case():
    """
    Test Case 3: Non-Compliant Case.
    Major infractions (e.g. 5 PASS, 5 FAIL).
    Expected score = 50.0%, reflects critical failures.
    """
    print("\n--- 3. Testing Non-Compliant Case ---")

    rules = [
        MockRuleResult(f"RULE-PASS-{i}", "PASS") for i in range(1, 6)
    ] + [
        MockRuleResult("LMA-2009-SEC-18-MANDATORY", "FAIL", "Missing mandatory declarations"),
        MockRuleResult("PCR-2011-R6-1-A-MFG-NAME", "FAIL", "Missing manufacturer"),
        MockRuleResult("PCR-2011-R6-1-C-NET-QUANTITY", "FAIL", "Missing net quantity"),
        MockRuleResult("PCR-2011-R6-1-E-MRP", "FAIL", "Missing MRP"),
        MockRuleResult("PCR-2011-R6-1-D-DATE", "FAIL", "Missing date of packing")
    ] + [
        MockRuleResult(f"RULE-NA-{i}", "NOT_APPLICABLE") for i in range(1, 5)
    ]

    scorer = ComplianceScorer()
    breakdown = scorer.calculate(rules, kb=legal_rule_kb)

    expected_score = round((5.0 / 10.0) * 100.0, 1)  # 50.0%
    assert breakdown.score == expected_score, f"Expected {expected_score}, got {breakdown.score}"
    assert breakdown.applicable_count == 10
    assert breakdown.passed_count == 5
    assert breakdown.failed_count == 5
    assert breakdown.points_earned == 5.0
    assert breakdown.points_possible == 10.0

    print(f"  [PASS] Non-compliant score verified: {breakdown.score}% ({breakdown.points_earned}/{breakdown.points_possible} pts).")


def test_needs_review_case():
    """
    Test Case 4: Needs-Review Case.
    Verifies that optical uncertainty (NEEDS_REVIEW) receives calibrated 50% provisional credit
    (0.5 point) rather than being treated as 0.0 (FAIL) or 1.0 (PASS).
    """
    print("\n--- 4. Testing Needs-Review Case & Provisional Credit ---")

    # 8 PASS, 2 NEEDS_REVIEW, 0 FAIL, 4 NOT_APPLICABLE
    # Points earned: 8 * 1.0 + 2 * 0.5 = 9.0 out of 10.0 -> 90.0%
    rules = [
        MockRuleResult(f"RULE-PASS-{i}", "PASS") for i in range(1, 9)
    ] + [
        MockRuleResult("PCR-2011-R9-LEGIBILITY-CONTRAST-LANG", "NEEDS_REVIEW", "Low optical contrast (72%)"),
        MockRuleResult("PCR-2011-R6-1-A-ADDR", "NEEDS_REVIEW", "Ambiguous street address text")
    ] + [
        MockRuleResult(f"RULE-NA-{i}", "NOT_APPLICABLE") for i in range(1, 5)
    ]

    scorer = ComplianceScorer()
    breakdown = scorer.calculate(rules, kb=legal_rule_kb)

    expected_score = round(((8 * 1.0 + 2 * 0.5) / 10.0) * 100.0, 1)  # 90.0%
    assert breakdown.score == expected_score, f"Expected {expected_score}, got {breakdown.score}"
    assert breakdown.applicable_count == 10
    assert breakdown.passed_count == 8
    assert breakdown.needs_review_count == 2
    assert breakdown.failed_count == 0
    assert breakdown.points_earned == 9.0
    assert breakdown.points_possible == 10.0
    assert breakdown.review_credit_rate == 0.5

    # Contrast against naive 0% failure penalty:
    naive_fail_score = round((8.0 / 10.0) * 100.0, 1)  # 80.0%
    assert breakdown.score > naive_fail_score, "NEEDS_REVIEW must not be penalized as 100% failure!"

    # Contrast against naive 100% full credit:
    naive_pass_score = 100.0
    assert breakdown.score < naive_pass_score, "NEEDS_REVIEW must not be awarded unverified 100% credit!"

    print(f"  [PASS] NEEDS_REVIEW awarded calibrated provisional credit (0.5 pts): score = {breakdown.score}%.")
    print(f"  Calculation: (8 PASS * 1.0 + 2 REVIEW * 0.5) / 10 = 9.0 / 10.0 = {breakdown.score}%")


def test_not_applicable_rules_exclusion():
    """
    Test Case 5: Not-Applicable Rules Exclusion.
    Verifies that NOT_APPLICABLE rules are strictly excluded from the denominator
    and NEVER count as failures or reduce the score.
    """
    print("\n--- 5. Testing Exclusion of NOT_APPLICABLE Rules ---")

    scorer = ComplianceScorer()

    # Case A: 6 PASS, 2 FAIL, 0 NOT_APPLICABLE (Total 8 rules)
    rules_a = [
        MockRuleResult(f"RULE-PASS-{i}", "PASS") for i in range(1, 7)
    ] + [
        MockRuleResult(f"RULE-FAIL-{i}", "FAIL") for i in range(1, 3)
    ]
    breakdown_a = scorer.calculate(rules_a)

    # Case B: 6 PASS, 2 FAIL, 15 NOT_APPLICABLE (Total 23 rules)
    rules_b = [
        MockRuleResult(f"RULE-PASS-{i}", "PASS") for i in range(1, 7)
    ] + [
        MockRuleResult(f"RULE-FAIL-{i}", "FAIL") for i in range(1, 3)
    ] + [
        MockRuleResult(f"RULE-NA-{i}", "NOT_APPLICABLE") for i in range(1, 16)
    ]
    breakdown_b = scorer.calculate(rules_b)

    # Both cases have identical 6 PASS and 2 FAIL applicable rules -> 6/8 = 75.0%
    assert breakdown_a.score == 75.0, f"Expected 75.0, got {breakdown_a.score}"
    assert breakdown_b.score == 75.0, f"Expected 75.0, got {breakdown_b.score}"

    # Critical Invariant: Adding 15 NOT_APPLICABLE rules must NOT change the score
    assert breakdown_a.score == breakdown_b.score, (
        f"Adding NOT_APPLICABLE rules changed score from {breakdown_a.score} to {breakdown_b.score}!"
    )
    assert breakdown_b.applicable_count == 8
    assert breakdown_b.not_applicable_count == 15
    assert breakdown_b.points_possible == 8.0  # Denominator is 8.0, not 23.0!

    print(f"  [PASS] Invariant verified: 0 NA rules = {breakdown_a.score}%, 15 NA rules = {breakdown_b.score}%.")
    print("  NOT_APPLICABLE rules strictly excluded from both numerator and denominator.")


def test_calculation_details_and_serialization():
    """
    Test Case 6: Calculation Details & Transparency.
    Verifies that the score breakdown exposes rule contributions, formula,
    points earned/possible, and serializes cleanly to JSON-compatible dict.
    """
    print("\n--- 6. Testing Calculation Details & Serialization ---")

    rules = [
        MockRuleResult("PCR-2011-R6-1-E-MRP", "PASS", "MRP declaration present"),
        MockRuleResult("PCR-2011-R6-1-C-NET-QUANTITY", "FAIL", "Net weight absent"),
        MockRuleResult("PCR-2011-R9-LEGIBILITY", "NEEDS_REVIEW", "Contrast low"),
        MockRuleResult("PCR-2011-R5-SECOND-SCHEDULE", "NOT_APPLICABLE", "Commodity not in schedule")
    ]

    breakdown = compliance_scorer.calculate(rules, kb=legal_rule_kb)
    d = breakdown.to_dict()

    # Verify all expected keys are exposed
    required_keys = [
        "score", "total_rules_evaluated", "applicable_count", "not_applicable_count",
        "passed_count", "failed_count", "needs_review_count", "points_earned",
        "points_possible", "formula", "explanation", "rule_contributions"
    ]
    for key in required_keys:
        assert key in d, f"Key '{key}' missing from score breakdown dict"

    assert len(d["rule_contributions"]) == 4

    # Verify individual contribution schema
    mrp_contrib = d["rule_contributions"][0]
    assert mrp_contrib["rule_id"] == "PCR-2011-R6-1-E-MRP"
    assert mrp_contrib["status"] == "PASS"
    assert mrp_contrib["points_awarded"] == 1.0
    assert mrp_contrib["max_points"] == 1.0
    assert mrp_contrib["is_applicable"] is True

    qty_contrib = d["rule_contributions"][1]
    assert qty_contrib["status"] == "FAIL"
    assert qty_contrib["points_awarded"] == 0.0

    rev_contrib = d["rule_contributions"][2]
    assert rev_contrib["status"] == "NEEDS_REVIEW"
    assert rev_contrib["points_awarded"] == 0.5

    na_contrib = d["rule_contributions"][3]
    assert na_contrib["status"] == "NOT_APPLICABLE"
    assert na_contrib["points_awarded"] == 0.0
    assert na_contrib["max_points"] == 0.0
    assert na_contrib["is_applicable"] is False

    print("  [PASS] Calculation details completely transparent and fully serialized.")


def run_all_tests():
    print("=" * 75)
    print(" EXECUTING SAFEMETRIC COMPLIANCE-SCORE CALCULATION TEST SUITE")
    print("=" * 75)
    test_fully_compliant_case()
    test_partially_compliant_case()
    test_non_compliant_case()
    test_needs_review_case()
    test_not_applicable_rules_exclusion()
    test_calculation_details_and_serialization()
    print("\n" + "=" * 75)
    print(" ALL 6 COMPLIANCE-SCORE CALCULATION TESTS PASSED (100%)!")
    print("=" * 75)


if __name__ == "__main__":
    run_all_tests()
