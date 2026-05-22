"""Phase and month conflicts (lightweight)."""

from __future__ import annotations

import re

from lop_eval.models import EvalConfig, EvalIssue, IssueSeverity, ProposalDocument
from lop_eval.text_extract import iter_text_spans

_PHASE = re.compile(r"phase\s*(?P<n>\d+)", re.I)
_MONTH = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    re.I,
)


def check_timeline(doc: ProposalDocument, config: EvalConfig) -> list[EvalIssue]:
    phase_to_months: dict[str, set[str]] = {}
    for span in iter_text_spans(doc):
        ph = _PHASE.search(span.text)
        if not ph:
            continue
        pid = ph.group("n")
        months = {m.group(1).lower() for m in _MONTH.finditer(span.text)}
        if not months:
            continue
        phase_to_months.setdefault(pid, set()).update(months)

    issues: list[EvalIssue] = []
    for pid, months in phase_to_months.items():
        if len(months) > 1:
            issues.append(
                EvalIssue(
                    type="timeline_phase_month_conflict",
                    severity=IssueSeverity.major,
                    description=f"Phase {pid} is associated with multiple different months.",
                    offending_text=", ".join(sorted(months)),
                    expected_text_or_rule="Phase start/end months should be unique unless a revision is explicit.",
                    checker_id="timeline",
                    evidence={"phase": pid},
                )
            )
    return issues
