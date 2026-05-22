"""Entity near-duplicate detection (deterministic fuzzy)."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from lop_eval.models import EvalConfig, EvalIssue, IssueSeverity, ProposalDocument
from lop_eval.text_extract import iter_text_spans

_CAP_PHRASE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def check_entities(doc: ProposalDocument, config: EvalConfig) -> list[EvalIssue]:
    phrases: set[str] = set()
    for span in iter_text_spans(doc):
        for m in _CAP_PHRASE.finditer(span.text):
            phrases.add(m.group(1).strip())

    items = sorted(phrases)
    issues: list[EvalIssue] = []
    for i, a in enumerate(items):
        for b in items[i + 1 :]:
            r = _ratio(a, b)
            if config.near_duplicate_ratio <= r < 1.0:
                issues.append(
                    EvalIssue(
                        type="entity_near_duplicate",
                        severity=IssueSeverity.minor,
                        description="Two capitalized phrases are near-identical; verify not two entities conflated.",
                        offending_text=f"{a} | {b}",
                        expected_text_or_rule="Use identical spelling for the same entity or disambiguate.",
                        checker_id="entity",
                        evidence={"similarity": round(r, 4)},
                    )
                )
                if len(issues) >= 5:
                    return issues
    return issues
