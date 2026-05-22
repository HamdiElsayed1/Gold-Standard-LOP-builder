"""Units and numeric representation consistency."""

from __future__ import annotations

from lop_eval.models import EvalConfig, EvalIssue, IssueSeverity, ProposalDocument
from lop_eval.normalize import extract_normalized_numbers, mentions_percent_and_decimal_pair
from lop_eval.text_extract import section_joined_text


def check_units(doc: ProposalDocument, config: EvalConfig) -> list[EvalIssue]:
    """Flag EUR vs USD under same section with similar magnitudes (heuristic)."""
    issues: list[EvalIssue] = []
    for sec in doc.sections:
        parts = " ".join(section_joined_text(sec)).lower()
        has_eur = "eur" in parts or "€" in parts
        has_usd = "usd" in parts or "$" in parts
        if has_eur and has_usd:
            issues.append(
                EvalIssue(
                    type="unit_currency_mixing",
                    severity=IssueSeverity.major,
                    description=f"Section '{sec.id}' mixes EUR and USD references.",
                    offending_text=parts[:200],
                    expected_text_or_rule="Keep currency consistent or clearly separate contexts.",
                    location=None,
                    checker_id="units",
                )
            )
    return issues


def check_formatting(doc: ProposalDocument, config: EvalConfig) -> list[EvalIssue]:
    issues: list[EvalIssue] = []
    for sec in doc.sections:
        texts = section_joined_text(sec)
        if mentions_percent_and_decimal_pair(texts):
            issues.append(
                EvalIssue(
                    type="representation_percent_vs_decimal",
                    severity=IssueSeverity.major,
                    description=f"Section '{sec.id}' mixes percent and decimal forms that may confuse readers.",
                    offending_text=" | ".join(texts)[:240],
                    expected_text_or_rule="Prefer one representation or state that decimals are share of total.",
                    checker_id="formatting",
                )
            )
    return issues
