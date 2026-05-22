"""Normalize numbers, percents, and simple currency scales for comparison."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


_RE_SPACES = re.compile(r"\s+")
_RE_THOUS = re.compile(r",\d{3}\b")


def strip_noise(s: str) -> str:
    s = _RE_SPACES.sub(" ", s.strip())
    return s


def parse_fraction_percent(text: str) -> Decimal | None:
    t = text.strip()
    if t.endswith("%"):
        try:
            return Decimal(t[:-1].strip()) / Decimal(100)
        except InvalidOperation:
            return None
    return None


def parse_plain_decimal(text: str) -> Decimal | None:
    t = text.replace(",", "").strip()
    try:
        return Decimal(t)
    except InvalidOperation:
        return None


@dataclass(frozen=True)
class NormalizedNumber:
    raw: str
    kind: str  # "percent" | "currency" | "plain" | "basis_points"
    value: Decimal | None
    currency: str | None
    scale: str | None  # mln, bln, none
    year: int | None = None


_CURRENCY = re.compile(
    r"\b(?P<cur>EUR|USD|GBP|\$|€)\s*(?P<num>[\d.,]+)\s*(?P<scale>mln|bln|million|billion)?\b",
    re.I,
)
_CURRENCY_SUFFIX = re.compile(
    r"\b(?P<num>[\d.,]+)\s*(?P<scale>mln|bln|million|billion)\s*(?P<cur>EUR|USD|GBP)\b",
    re.I,
)
_YEAR_NEAR = re.compile(r"\b(20\d{2})\b")
_PERCENT = re.compile(r"(?P<num>[\d.,]+)\s*%")
_BP = re.compile(r"(?P<num>[\d.,]+)\s*(bp|bps)\b", re.I)


def _scale_to_mult(scale: str | None) -> Decimal:
    if not scale:
        return Decimal(1)
    s = scale.lower()
    if s in ("mln", "million"):
        return Decimal(1_000_000)
    if s in ("bln", "billion"):
        return Decimal(1_000_000_000)
    return Decimal(1)


def _cur_norm(cur: str) -> str:
    c = cur.upper()
    if c == "$":
        return "USD"
    if c == "€":
        return "EUR"
    return c


def extract_normalized_numbers(sentence: str) -> list[NormalizedNumber]:
    """Extract a conservative set of numeric tokens from a sentence."""
    out: list[NormalizedNumber] = []
    year_m = _YEAR_NEAR.search(sentence)
    year = int(year_m.group(1)) if year_m else None

    for m in _CURRENCY.finditer(sentence):
        num = parse_plain_decimal(m.group("num"))
        mult = _scale_to_mult(m.group("scale"))
        val = num * mult if num is not None else None
        out.append(
            NormalizedNumber(
                raw=m.group(0),
                kind="currency",
                value=val,
                currency=_cur_norm(m.group("cur")),
                scale=m.group("scale") or None,
                year=year,
            )
        )
    for m in _CURRENCY_SUFFIX.finditer(sentence):
        num = parse_plain_decimal(m.group("num"))
        mult = _scale_to_mult(m.group("scale"))
        val = num * mult if num is not None else None
        out.append(
            NormalizedNumber(
                raw=m.group(0),
                kind="currency",
                value=val,
                currency=_cur_norm(m.group("cur")),
                scale=m.group("scale") or None,
                year=year,
            )
        )
    for m in _PERCENT.finditer(sentence):
        num = parse_plain_decimal(m.group("num"))
        frac = num / Decimal(100) if num is not None else None
        out.append(
            NormalizedNumber(
                raw=m.group(0),
                kind="percent",
                value=frac,
                currency=None,
                scale=None,
                year=year,
            )
        )
    for m in _BP.finditer(sentence):
        num = parse_plain_decimal(m.group("num"))
        frac = num / Decimal(10_000) if num is not None else None  # bp to fraction
        out.append(
            NormalizedNumber(
                raw=m.group(0),
                kind="basis_points",
                value=frac,
                currency=None,
                scale=None,
                year=year,
            )
        )
    return out


def numbers_close(a: Decimal | None, b: Decimal | None, rel_tol: float) -> bool:
    if a is None or b is None:
        return False
    if a == b:
        return True
    diff = abs(a - b)
    base = max(abs(a), abs(b), Decimal("1e-9"))
    return float(diff / base) <= rel_tol


def mentions_percent_and_decimal_pair(texts: list[str]) -> bool:
    """Heuristic: same section has both '10%' style and bare '0.1' that could be confused."""
    joined = " ".join(texts)
    has_pct = _PERCENT.search(joined) is not None
    if not has_pct:
        return False
    bare = re.findall(r"(?<![\d.])(0\.\d+)(?![\d%])", joined)
    return len(bare) > 0


def json_safe_decimal(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    return obj
