"""Numeric consistency: cluster by metric context + unit and flag conflicts."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from lop_eval.models import EvalConfig, EvalIssue, IssueLocation, IssueSeverity, ProposalDocument
from lop_eval.normalize import extract_normalized_numbers, numbers_close
from lop_eval.text_extract import iter_text_spans

_METRIC_WORDS = [
    "revenue",
    "ebitda",
    "margin",
    "stock",
    "price",
    "share",
    "growth",
    "sales",
    "profit",
    "valuation",
    "ebit",
]


def _metric_token(sentence: str) -> str:
    low = sentence.lower()
    for w in _METRIC_WORDS:
        if w in low:
            return w
    return "generic"


_YEAR = re.compile(r"\b(20\d{2})\b|FY\s*(20\d{2})\b|FY(20\d{2})\b", re.I)


def _years_in(text: str) -> set[int]:
    years: set[int] = set()
    for m in _YEAR.finditer(text):
        for i in range(1, 4):
            g = m.group(i)
            if g:
                years.add(int(g))
    return years


@dataclass(frozen=True)
class Obs:
    key: tuple[str, str, str | None, str | None]
    value: Decimal
    raw: str
    sentence: str
    section_id: str
    block_index: int


def check_numeric(doc: ProposalDocument, config: EvalConfig) -> list[EvalIssue]:
    issues: list[EvalIssue] = []
    obs: list[Obs] = []
    for span in iter_text_spans(doc):
        sentence = span.text
        mtok = _metric_token(sentence)
        for nn in extract_normalized_numbers(sentence):
            if nn.value is None:
                continue
            key = (mtok, nn.kind, nn.currency, nn.scale)
            obs.append(
                Obs(
                    key=key,
                    value=nn.value,
                    raw=nn.raw,
                    sentence=sentence,
                    section_id=span.section.id,
                    block_index=span.block_index,
                )
            )

    buckets: dict[tuple[str, str, str | None, str | None], list[Obs]] = defaultdict(list)
    for o in obs:
        buckets[o.key].append(o)

    for key, items in buckets.items():
        mtok, _kind, _cur, _scale = key
        if mtok == "generic":
            # Without a metric anchor, comparing bare numbers creates false positives.
            continue
        if len(items) < 2:
            continue
        values = [i.value for i in items]
        # Compare pairwise — if any pair is far, report once per bucket
        base = items[0]
        worse: Obs | None = None
        for other in items[1:]:
            if not numbers_close(base.value, other.value, config.numeric_relative_tolerance):
                worse = other
                break
        if worse:
            mtok, kind, cur, scale = key
            issues.append(
                EvalIssue(
                    type="numeric_conflict",
                    severity=IssueSeverity.critical if mtok != "generic" else IssueSeverity.major,
                    description=(
                        f"Inconsistent {kind} values under metric context '{mtok}' "
                        f"(currency={cur}, scale={scale})."
                    ),
                    offending_text=f"{base.raw} vs {worse.raw}",
                    expected_text_or_rule=(
                        "Same metric should use one value, or explicitly restate/revise figures with wording like "
                        "'updated to' or 'restated'."
                    ),
                    location=IssueLocation(
                        section_id=base.section_id,
                        block_index=base.block_index,
                    ),
                    related_locations=[
                        {"section_id": worse.section_id, "block_index": worse.block_index},
                    ],
                    checker_id="numeric",
                    evidence={"key": list(key), "values": [str(v) for v in values[:5]]},
                )
            )

    # Year vs same headline number: stock price style
    stock_obs = [o for o in obs if "stock" in o.sentence.lower() or "price" in o.sentence.lower()]
    by_val: dict[Decimal, list[Obs]] = defaultdict(list)
    for o in stock_obs:
        if o.key[1] == "currency":
            by_val[o.value].append(o)

    for val, group in by_val.items():
        if len(group) < 2:
            continue
        year_sets = [_years_in(o.sentence) for o in group]
        flat = set().union(*year_sets) if year_sets else set()
        if len(flat) > 1:
            issues.append(
                EvalIssue(
                    type="numeric_year_inconsistency",
                    severity=IssueSeverity.major,
                    description="Same monetary level tied to different years without restatement.",
                    offending_text=" | ".join(o.sentence[:120] for o in group[:2]),
                    expected_text_or_rule="Align as-of year for stock/price references or explain revision.",
                    checker_id="numeric",
                    evidence={"value": str(val), "years": sorted(flat)},
                )
            )

    return issues
