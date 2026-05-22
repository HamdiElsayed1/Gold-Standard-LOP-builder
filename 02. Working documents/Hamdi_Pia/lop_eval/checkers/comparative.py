"""Comparative language collisions (heuristic)."""

from __future__ import annotations

import re

from lop_eval.models import EvalConfig, EvalIssue, IssueSeverity, ProposalDocument
from lop_eval.text_extract import iter_text_spans

_UP = re.compile(
    r"\b(largest|biggest|fastest|best|highest|strongest|more efficient|better than|leader)\b",
    re.I,
)
_DOWN = re.compile(
    r"\b(smallest|slowest|worst|lowest|weakest|less efficient|worse than|laggard)\b",
    re.I,
)


def check_comparatives(doc: ProposalDocument, config: EvalConfig) -> list[EvalIssue]:
    up_lines: list[str] = []
    down_lines: list[str] = []
    for span in iter_text_spans(doc):
        t = span.text
        if _UP.search(t):
            up_lines.append(t)
        if _DOWN.search(t):
            down_lines.append(t)

    issues: list[EvalIssue] = []
    if up_lines and down_lines:
        # crude subject overlap: share significant words length>4
        def sig_words(s: str) -> set[str]:
            return {w.lower() for w in re.findall(r"[A-Za-z]{5,}", s)}

        for u in up_lines:
            su = sig_words(u)
            for d in down_lines:
                if su & sig_words(d) and len(su & sig_words(d)) >= 2:
                    issues.append(
                        EvalIssue(
                            type="comparative_conflict",
                            severity=IssueSeverity.major,
                            description="Positive and negative superlatives appear on overlapping subject matter.",
                            offending_text=f"UP: {u[:120]} | DOWN: {d[:120]}",
                            expected_text_or_rule="Comparative claims should not contradict across sections.",
                            checker_id="comparative",
                        )
                    )
                    return issues
    return issues
