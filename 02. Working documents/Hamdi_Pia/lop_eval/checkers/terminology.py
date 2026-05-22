"""Terminology drift (deterministic synonym classes)."""

from __future__ import annotations

import re

from lop_eval.models import EvalConfig, EvalIssue, IssueSeverity, ProposalDocument
from lop_eval.text_extract import iter_text_spans

_BRIDGE = re.compile(
    r"\b(also referred to as|hereinafter|aka|a\.k\.a\.|known as)\b",
    re.I,
)


def check_terminology(doc: ProposalDocument, config: EvalConfig) -> list[EvalIssue]:
    corpus = " ".join(s.text for s in iter_text_spans(doc))
    low = corpus.lower()
    issues: list[EvalIssue] = []

    has_bridge = bool(_BRIDGE.search(corpus))

    for term_class in config.drift_term_classes:
        present = [t for t in term_class if re.search(rf"\b{re.escape(t)}\b", low)]
        if len(present) < 2:
            continue
        sev = IssueSeverity.minor if has_bridge else IssueSeverity.major
        issues.append(
            EvalIssue(
                type="terminology_drift",
                severity=sev,
                description="Multiple program labels from the same drift class appear; verify they refer to the same object.",
                offending_text=", ".join(sorted(set(present))),
                expected_text_or_rule=(
                    "Use one primary label or add explicit definitional language linking synonyms."
                ),
                checker_id="terminology",
                evidence={"class": term_class, "equivalence_bridge_present": has_bridge},
            )
        )
    return issues
