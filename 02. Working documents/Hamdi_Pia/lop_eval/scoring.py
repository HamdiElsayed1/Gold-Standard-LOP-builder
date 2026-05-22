"""Per-checker weights and score breakdown helpers."""

from __future__ import annotations

from lop_eval.models import EvalConfig, EvalIssue

# Keys match EvalIssue.checker_id where set.
DEFAULT_CHECKER_WEIGHTS: dict[str, float] = {
    "numeric": 1.0,
    "terminology": 1.0,
    "scope": 1.0,
    "timeline": 1.0,
    "units": 1.0,
    "formatting": 1.0,
    "abbreviation": 1.0,
    "comparative": 1.0,
    "entity": 1.0,
    "claim_support": 1.0,
    "faithfulness": 1.0,
    "llm_judge": 1.0,
}

CHECKER_LABELS: dict[str, str] = {
    "numeric": "Numeric consistency",
    "terminology": "Terminology",
    "scope": "Scope",
    "timeline": "Timeline",
    "units": "Units & currency",
    "formatting": "Formatting",
    "abbreviation": "Abbreviations",
    "comparative": "Comparatives",
    "entity": "Entity names",
    "claim_support": "Claim vs table",
    "faithfulness": "Source-of-truth",
    "llm_judge": "LLM judge",
}


def checker_key_for_issue(issue: EvalIssue) -> str:
    if issue.checker_id:
        return issue.checker_id
    t = issue.type or ""
    if t.startswith("llm_judge"):
        return "llm_judge"
    if t.startswith("numeric"):
        return "numeric"
    if "terminology" in t:
        return "terminology"
    if "scope" in t:
        return "scope"
    if "timeline" in t:
        return "timeline"
    if "unit" in t or "currency" in t:
        return "units"
    if "representation" in t or "format" in t:
        return "formatting"
    if "abbreviation" in t:
        return "abbreviation"
    if "comparative" in t:
        return "comparative"
    if "entity" in t:
        return "entity"
    if "claim_support" in t:
        return "claim_support"
    if "faithfulness" in t:
        return "faithfulness"
    return "other"


def severity_base_deduction(severity: str, cfg: EvalConfig) -> float:
    if severity == "critical":
        return cfg.deduct_critical
    if severity == "major":
        return cfg.deduct_major
    return cfg.deduct_minor


def compute_score(
    issues: list[EvalIssue], cfg: EvalConfig
) -> tuple[float, dict[str, float], dict[str, int]]:
    """
    Returns (overall_score, breakdown_deductions_by_checker, issue_counts_by_checker).
    """
    breakdown: dict[str, float] = {k: 0.0 for k in DEFAULT_CHECKER_WEIGHTS}
    counts: dict[str, int] = {k: 0 for k in DEFAULT_CHECKER_WEIGHTS}
    total_deduction = 0.0

    weights = {**DEFAULT_CHECKER_WEIGHTS, **(cfg.checker_weights or {})}

    for issue in issues:
        sev = issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity)
        base = severity_base_deduction(sev, cfg)
        key = checker_key_for_issue(issue)
        w = weights.get(key, weights.get("other", 1.0))
        deduct = base * w
        total_deduction += deduct
        if key not in breakdown:
            breakdown[key] = 0.0
            counts[key] = 0
        breakdown[key] += deduct
        counts[key] += 1

    score = max(0.0, min(100.0, 100.0 - total_deduction))
    return round(score, 2), breakdown, counts
