"""Abbreviation consistency."""

from __future__ import annotations

import re

from lop_eval.models import EvalConfig, EvalIssue, IssueSeverity, ProposalDocument
from lop_eval.text_extract import iter_text_spans

_LONG_FIRST = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(([A-Z]{2,5})\)(?=\s|$|[.,;:])"
)
_ACR_FIRST = re.compile(r"\b([A-Z]{2,5})\s*\(([A-Za-z][^)]+)\)(?=\s|$|[.,;:])")


def check_abbreviations(doc: ProposalDocument, config: EvalConfig) -> list[EvalIssue]:
    expansions: dict[str, set[str]] = {}
    for span in iter_text_spans(doc):
        text = span.text
        for m in _LONG_FIRST.finditer(text):
            long, ac = m.group(1), m.group(2)
            expansions.setdefault(ac, set()).add(long.strip())
        for m in _ACR_FIRST.finditer(text):
            ac, long = m.group(1), m.group(2)
            expansions.setdefault(ac, set()).add(long.strip())

    issues: list[EvalIssue] = []
    for ac, names in expansions.items():
        if len(names) > 1:
            issues.append(
                EvalIssue(
                    type="abbreviation_conflict",
                    severity=IssueSeverity.major,
                    description=f"Acronym '{ac}' mapped to multiple expansions.",
                    offending_text=ac,
                    expected_text_or_rule="One acronym should map to one expansion unless clearly distinct entities.",
                    checker_id="abbreviation",
                    evidence={"expansions": sorted(names)},
                )
            )
    return issues
