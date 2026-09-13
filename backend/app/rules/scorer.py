"""
scorer.py
=========
SAFEMETRIC Compliance Score Calculation Engine.

Provides a deterministic, explainable, and statutory-grounded scoring calculation
for pre-packaged commodity label inspections.

Statutory Principles:
1. Determinism:
   Identical sets of validated rule verdicts always produce the exact same score.
2. Transparency & Explainability:
   Exposes the full mathematical breakdown, formula, earned points, maximum possible
   points, and per-rule credit attribution.
3. Accurate Status Handling:
   - PASS: Full credit (1.0). The statutory requirement is satisfied.
   - FAIL: Zero credit (0.0). Definite statutory infraction detected.
   - NEEDS_REVIEW: Calibrated provisional credit (0.5). Reflects optical uncertainty
     or low legibility contrast (<80%) under Rule 9(1) without penalizing as a confirmed violation.
4. Non-Penalization of Excluded Provisions:
   - NOT_APPLICABLE: Strictly excluded from both numerator and denominator.
     Never treated as a failure or penalty.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional

PASS_CREDIT = 1.0
REVIEW_CREDIT = 0.5
FAIL_CREDIT = 0.0

SEVERITY_WEIGHTS: Dict[str, float] = {
    "CRITICAL": 3.0,
    "HIGH": 2.0,
    "MEDIUM": 1.0,
    "LOW": 0.5,
    "INFORMATIONAL": 0.0
}


@dataclass
class RuleScoreContribution:
    """Detailed score contribution for an individual statutory rule."""
    rule_id: str
    legal_reference: str
    status: str                         # PASS | FAIL | NEEDS_REVIEW | NOT_APPLICABLE
    is_applicable: bool
    points_awarded: float
    max_points: float
    weight: float                       # Baseline rule weight (1.0)
    severity: str                       # CRITICAL, HIGH, MEDIUM, LOW
    severity_weight: float              # Weighted factor for severity-weighted score
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceScoreBreakdown:
    """
    Transparent, explainable mathematical breakdown of the compliance score calculation.
    """
    score: float                        # Final rounded compliance score (0.0 - 100.0)
    total_rules_evaluated: int          # Total rules passed to engine
    applicable_count: int               # Count of applicable rules (PASS + FAIL + NEEDS_REVIEW)
    not_applicable_count: int           # Count of NOT_APPLICABLE rules
    passed_count: int                   # Count of PASS rules
    failed_count: int                   # Count of FAIL rules
    needs_review_count: int             # Count of NEEDS_REVIEW rules
    points_earned: float                # Sum of earned points
    points_possible: float              # Maximum possible points (applicable_count * 1.0)
    pass_credit_rate: float = PASS_CREDIT
    review_credit_rate: float = REVIEW_CREDIT
    fail_credit_rate: float = FAIL_CREDIT
    formula: str = ""                   # Mathematical formula representation
    explanation: str = ""               # Human-readable plain language explanation
    severity_weighted_score: Optional[float] = None
    rule_contributions: List[RuleScoreContribution] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["rule_contributions"] = [r.to_dict() for r in self.rule_contributions]
        return d


class ComplianceScorer:
    """
    Statutory Compliance-Score Calculation Engine.
    Executes deterministic, explainable scoring based on evaluated rule results.
    """

    def __init__(
        self,
        pass_credit: float = PASS_CREDIT,
        review_credit: float = REVIEW_CREDIT,
        fail_credit: float = FAIL_CREDIT
    ):
        self.pass_credit = float(pass_credit)
        self.review_credit = float(review_credit)
        self.fail_credit = float(fail_credit)

    def calculate(
        self,
        rule_results: List[Any],
        kb: Optional[Any] = None
    ) -> ComplianceScoreBreakdown:
        """
        Calculates the compliance score from a list of RuleValidationResult objects.

        Handling:
        - PASS: Awards pass_credit (1.0) out of 1.0 possible points.
        - FAIL: Awards fail_credit (0.0) out of 1.0 possible points.
        - NEEDS_REVIEW: Awards review_credit (0.5) out of 1.0 possible points (provisional score).
        - NOT_APPLICABLE: 0.0 awarded out of 0.0 possible points (strictly excluded from denominator).
        """
        if not rule_results:
            return ComplianceScoreBreakdown(
                score=100.0,
                total_rules_evaluated=0,
                applicable_count=0,
                not_applicable_count=0,
                passed_count=0,
                failed_count=0,
                needs_review_count=0,
                points_earned=0.0,
                points_possible=0.0,
                pass_credit_rate=self.pass_credit,
                review_credit_rate=self.review_credit,
                fail_credit_rate=self.fail_credit,
                formula="No rules evaluated. Score = 100.0%",
                explanation="No statutory rules were evaluated.",
                severity_weighted_score=100.0,
                rule_contributions=[]
            )

        total_rules = len(rule_results)
        passed_count = 0
        failed_count = 0
        needs_review_count = 0
        not_applicable_count = 0

        points_earned = 0.0
        points_possible = 0.0

        weighted_points_earned = 0.0
        weighted_points_possible = 0.0

        contributions: List[RuleScoreContribution] = []

        for r in rule_results:
            status = getattr(r, "status", "NOT_APPLICABLE")
            rule_id = getattr(r, "rule_id", "UNKNOWN_RULE")
            legal_ref = getattr(r, "legal_reference", "")
            explanation = getattr(r, "explanation", "")

            # Resolve rule severity from knowledge base if available
            severity = "HIGH"
            if kb and hasattr(kb, "get_rule_by_id"):
                spec = kb.get_rule_by_id(rule_id)
                if spec:
                    severity = getattr(spec, "severity", "HIGH")
            sev_weight = SEVERITY_WEIGHTS.get(severity, 2.0)

            if status == "PASS":
                passed_count += 1
                is_applicable = True
                awarded = self.pass_credit
                max_pts = 1.0
                weighted_awarded = self.pass_credit * sev_weight
                weighted_max = 1.0 * sev_weight

            elif status == "FAIL":
                failed_count += 1
                is_applicable = True
                awarded = self.fail_credit
                max_pts = 1.0
                weighted_awarded = self.fail_credit * sev_weight
                weighted_max = 1.0 * sev_weight

            elif status == "NEEDS_REVIEW":
                needs_review_count += 1
                is_applicable = True
                awarded = self.review_credit
                max_pts = 1.0
                weighted_awarded = self.review_credit * sev_weight
                weighted_max = 1.0 * sev_weight

            else:  # NOT_APPLICABLE or other
                not_applicable_count += 1
                is_applicable = False
                awarded = 0.0
                max_pts = 0.0
                weighted_awarded = 0.0
                weighted_max = 0.0

            if is_applicable:
                points_earned += awarded
                points_possible += max_pts
                weighted_points_earned += weighted_awarded
                weighted_points_possible += weighted_max

            contributions.append(RuleScoreContribution(
                rule_id=rule_id,
                legal_reference=legal_ref,
                status=status,
                is_applicable=is_applicable,
                points_awarded=round(awarded, 2),
                max_points=round(max_pts, 2),
                weight=1.0 if is_applicable else 0.0,
                severity=severity,
                severity_weight=sev_weight if is_applicable else 0.0,
                explanation=explanation
            ))

        applicable_count = passed_count + failed_count + needs_review_count

        if applicable_count > 0:
            score = round((points_earned / points_possible) * 100.0, 1)
            formula = (
                f"Score = (({passed_count} PASS × {self.pass_credit}) + "
                f"({needs_review_count} REVIEW × {self.review_credit}) + "
                f"({failed_count} FAIL × {self.fail_credit})) / "
                f"{applicable_count} Applicable Rules × 100 = {score}%"
            )
        else:
            score = 100.0
            formula = f"Score = 100.0% (All {total_rules} rules classified as NOT_APPLICABLE)"

        # Severity-weighted score calculation
        if weighted_points_possible > 0:
            severity_weighted_score = round((weighted_points_earned / weighted_points_possible) * 100.0, 1)
        else:
            severity_weighted_score = 100.0

        # Construct explainable plain language narrative
        explanation_parts = []
        explanation_parts.append(
            f"Evaluated across {total_rules} statutory rules, of which {applicable_count} are applicable "
            f"and {not_applicable_count} are excluded as not applicable to this commodity category."
        )
        if passed_count > 0:
            explanation_parts.append(f"{passed_count} rules fully passed ({passed_count * self.pass_credit:.1f} pts).")
        if failed_count > 0:
            explanation_parts.append(f"{failed_count} rules failed with statutory infractions (0.0 pts).")
        if needs_review_count > 0:
            explanation_parts.append(
                f"{needs_review_count} rules require optical or physical verification under Rule 9(1) "
                f"(awarded provisional {self.review_credit * 100:.0f}% credit = {needs_review_count * self.review_credit:.1f} pts)."
            )
        explanation_parts.append(f"Total points earned: {points_earned:.1f} of {points_possible:.1f} maximum possible.")
        explanation_text = " ".join(explanation_parts)

        return ComplianceScoreBreakdown(
            score=score,
            total_rules_evaluated=total_rules,
            applicable_count=applicable_count,
            not_applicable_count=not_applicable_count,
            passed_count=passed_count,
            failed_count=failed_count,
            needs_review_count=needs_review_count,
            points_earned=round(points_earned, 2),
            points_possible=round(points_possible, 2),
            pass_credit_rate=self.pass_credit,
            review_credit_rate=self.review_credit,
            fail_credit_rate=self.fail_credit,
            formula=formula,
            explanation=explanation_text,
            severity_weighted_score=severity_weighted_score,
            rule_contributions=contributions
        )


# Global singleton instance
compliance_scorer = ComplianceScorer()
