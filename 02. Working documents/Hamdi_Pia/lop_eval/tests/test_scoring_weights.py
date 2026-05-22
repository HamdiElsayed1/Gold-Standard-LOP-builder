"""Per-checker weight scoring."""

from lop_eval.models import EvalConfig, EvalIssue, IssueSeverity
from lop_eval.scoring import compute_score


def _issue(checker: str, severity: IssueSeverity) -> EvalIssue:
    return EvalIssue(
        type=f"{checker}_test",
        severity=severity,
        description="test",
        offending_text="x",
        expected_text_or_rule="y",
        checker_id=checker,
    )


def test_zero_weight_zeros_deduction_for_checker():
    cfg = EvalConfig(
        deduct_major=10.0,
        checker_weights={"numeric": 0.0, "terminology": 1.0},
    )
    issues = [
        _issue("numeric", IssueSeverity.major),
        _issue("terminology", IssueSeverity.major),
    ]
    score, breakdown, _counts = compute_score(issues, cfg)
    assert breakdown["numeric"] == 0.0
    assert breakdown["terminology"] == 10.0
    assert score == 90.0


def test_double_weight_doubles_deduction():
    cfg = EvalConfig(
        deduct_minor=3.0,
        checker_weights={"scope": 2.0},
    )
    issues = [_issue("scope", IssueSeverity.minor)]
    score, breakdown, _ = compute_score(issues, cfg)
    assert breakdown["scope"] == 6.0
    assert score == 94.0
