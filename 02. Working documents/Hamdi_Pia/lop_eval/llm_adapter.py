"""Optional LLM-based semantic drift checks (off by default in CI)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from lop_eval.llm_judge import format_judge_prompt, parse_judge_response
from lop_eval.models import EvalIssue, IssueSeverity, ProposalDocument


@dataclass(frozen=True)
class JudgeCandidate:
    criteria: str
    reference: str
    response: str
    issue_type: str = "llm_judge_semantic"
    checker_id: str = "llm_judge"


class SemanticDriftAdapter:
    def propose_issues(
        self,
        doc: ProposalDocument,
        candidates: list[JudgeCandidate] | None = None,
    ) -> list[EvalIssue]:
        return []


class LlmJudgeAdapter:
    def __init__(self, call_llm: Callable[[str], str]) -> None:
        self._call_llm = call_llm

    def propose_issues(
        self,
        doc: ProposalDocument,
        candidates: list[JudgeCandidate] | None = None,
    ) -> list[EvalIssue]:
        if not candidates:
            return []
        issues: list[EvalIssue] = []
        for cand in candidates:
            prompt = format_judge_prompt(
                criteria=cand.criteria,
                reference=cand.reference,
                response=cand.response,
            )
            try:
                raw = self._call_llm(prompt)
            except Exception as exc:
                issues.append(
                    EvalIssue(
                        type="llm_judge_error",
                        severity=IssueSeverity.minor,
                        description=f"LLM judge call failed: {exc}",
                        offending_text=cand.response[:200],
                        expected_text_or_rule=cand.criteria,
                        checker_id=cand.checker_id,
                    )
                )
                continue
            verdict = parse_judge_response(raw or "")
            if verdict is None:
                issues.append(
                    EvalIssue(
                        type="llm_judge_parse_error",
                        severity=IssueSeverity.minor,
                        description="Could not parse LLM judge response.",
                        offending_text=(raw or "")[:200],
                        expected_text_or_rule="Score: 0|1 and Reasoning:",
                        checker_id=cand.checker_id,
                    )
                )
                continue
            if verdict.score == 0:
                issues.append(
                    EvalIssue(
                        type=cand.issue_type,
                        severity=IssueSeverity.major,
                        description=verdict.reasoning or "LLM judge flagged inconsistency.",
                        offending_text=cand.response[:300],
                        expected_text_or_rule=cand.reference[:300],
                        checker_id=cand.checker_id,
                        evidence={"score": 0},
                    )
                )
        return issues


class NullSemanticDriftAdapter(SemanticDriftAdapter):
    pass
