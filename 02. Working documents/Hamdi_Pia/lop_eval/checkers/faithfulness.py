"""Optional faithfulness checks against supplied facts."""

from __future__ import annotations

import re

from lop_eval.models import (
    EvalConfig,
    EvalIssue,
    IssueSeverity,
    ProposalDocument,
    SourceOfTruth,
)
from lop_eval.text_extract import iter_text_spans


def check_source_of_truth(
    doc: ProposalDocument, sot: SourceOfTruth | None, config: EvalConfig
) -> list[EvalIssue]:
    if not sot or not sot.facts:
        return []

    issues: list[EvalIssue] = []
    corpus = " ".join(s.text for s in iter_text_spans(doc))
    for fact in sot.facts:
        # v1: substring presence for value_text; future: normalized compare
        if fact.value_text and fact.value_text not in corpus:
            # allow currency/scale variants: soft check
            norm = re.sub(r"\s+", " ", fact.value_text.strip())
            if norm.lower() not in corpus.lower():
                issues.append(
                    EvalIssue(
                        type="faithfulness_missing_fact",
                        severity=IssueSeverity.major,
                        description=f"Source-of-truth fact '{fact.key}' not found verbatim in document.",
                        offending_text=fact.value_text[:120],
                        expected_text_or_rule="Reflect approved facts explicitly or document deliberate omission.",
                        checker_id="faithfulness",
                        evidence={"key": fact.key},
                    )
                )
    return issues
