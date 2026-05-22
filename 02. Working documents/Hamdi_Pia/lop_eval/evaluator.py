"""Orchestrate deterministic checkers and produce a scored EvalResult."""

from __future__ import annotations

from lop_eval import SPEC_VERSION
from lop_eval.checkers import abbreviation
from lop_eval.checkers import claim_support
from lop_eval.checkers import comparative
from lop_eval.checkers import entity
from lop_eval.checkers import faithfulness
from lop_eval.checkers import numeric
from lop_eval.checkers import scope
from lop_eval.checkers import terminology
from lop_eval.checkers import timeline
from lop_eval.checkers import units_formatting
from lop_eval.llm_adapter import JudgeCandidate, NullSemanticDriftAdapter, SemanticDriftAdapter
from lop_eval.models import EvalConfig, EvalIssue, EvalResult, EvalSummary, ProposalDocument, SourceOfTruth
from lop_eval.scoring import DEFAULT_CHECKER_WEIGHTS, compute_score


def _dedupe_issues(issues: list[EvalIssue]) -> list[EvalIssue]:
    seen: set[tuple[str, str]] = set()
    out: list[EvalIssue] = []
    for issue in issues:
        key = (issue.type, issue.offending_text[:120])
        if key in seen:
            continue
        seen.add(key)
        out.append(issue)
    return out


def collect_judge_candidates(doc: ProposalDocument, issues: list[EvalIssue]) -> list[JudgeCandidate]:
    """Build LLM judge candidates from ambiguous deterministic flags."""
    candidates: list[JudgeCandidate] = []
    for issue in issues:
        if issue.type == "terminology_drift" and issue.evidence and issue.evidence.get(
            "equivalence_bridge_present"
        ):
            candidates.append(
                JudgeCandidate(
                    criteria=(
                        "Two program labels appear in the same drift class. "
                        "If they refer to the same engagement object, this is acceptable; "
                        "otherwise it is inconsistent terminology."
                    ),
                    reference=issue.expected_text_or_rule,
                    response=issue.offending_text,
                    issue_type="llm_judge_terminology",
                )
            )
    return candidates


def evaluate_document(
    doc: ProposalDocument,
    *,
    config: EvalConfig | None = None,
    source_of_truth: SourceOfTruth | None = None,
    llm_adapter: SemanticDriftAdapter | None = None,
    judge_candidates: list[JudgeCandidate] | None = None,
) -> EvalResult:
    cfg = config or EvalConfig()
    issues: list[EvalIssue] = []
    issues.extend(numeric.check_numeric(doc, cfg))
    issues.extend(terminology.check_terminology(doc, cfg))
    issues.extend(scope.check_scope(doc, cfg))
    issues.extend(timeline.check_timeline(doc, cfg))
    issues.extend(units_formatting.check_units(doc, cfg))
    issues.extend(units_formatting.check_formatting(doc, cfg))
    issues.extend(abbreviation.check_abbreviations(doc, cfg))
    issues.extend(comparative.check_comparatives(doc, cfg))
    issues.extend(entity.check_entities(doc, cfg))
    issues.extend(claim_support.check_claim_support(doc, cfg))
    issues.extend(faithfulness.check_source_of_truth(doc, source_of_truth, cfg))

    adapter = llm_adapter or NullSemanticDriftAdapter()
    candidates = judge_candidates if judge_candidates is not None else collect_judge_candidates(doc, issues)
    if candidates:
        issues.extend(adapter.propose_issues(doc, candidates))

    issues = _dedupe_issues(issues)

    summary = EvalSummary()
    for issue in issues:
        sev = issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity)
        if sev == "critical":
            summary.critical += 1
        elif sev == "major":
            summary.major += 1
        else:
            summary.minor += 1

    overall_score, breakdown, counts = compute_score(issues, cfg)
    weights_used = {**DEFAULT_CHECKER_WEIGHTS, **(cfg.checker_weights or {})}

    critical_fail = cfg.fail_on_critical and summary.critical > 0
    passed = overall_score >= cfg.pass_threshold and not critical_fail

    return EvalResult(
        document_id=doc.document_id,
        eval_version=SPEC_VERSION,
        overall_score=overall_score,
        passed=passed,
        threshold=cfg.pass_threshold,
        issues=issues,
        summary=summary,
        score_breakdown=breakdown,
        issue_counts_by_checker=counts,
        checker_weights_used=weights_used,
    )
