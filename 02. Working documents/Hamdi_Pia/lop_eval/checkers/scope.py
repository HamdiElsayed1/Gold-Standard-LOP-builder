"""Geography / scope markers."""

from __future__ import annotations

import re

from lop_eval.models import EvalConfig, EvalIssue, IssueSeverity, ProposalDocument
from lop_eval.text_extract import iter_text_spans


def check_scope(doc: ProposalDocument, config: EvalConfig) -> list[EvalIssue]:
    present_global = False
    present_emea_only = False
    for span in iter_text_spans(doc):
        t = span.text.lower()
        if re.search(r"\b(global|worldwide)\b", t):
            present_global = True
        if "emea" in t and re.search(r"\b(only|exclusively)\b", t):
            present_emea_only = True

    issues: list[EvalIssue] = []
    if present_emea_only and present_global:
        issues.append(
            EvalIssue(
                type="scope_drift",
                severity=IssueSeverity.major,
                description="Document implies both EMEA-only scope and global/worldwide scope.",
                offending_text="EMEA-only vs global/worldwide",
                expected_text_or_rule="Clarify whether the engagement is regional or global; remove silent scope expansion.",
                checker_id="scope",
            )
        )
    return issues
