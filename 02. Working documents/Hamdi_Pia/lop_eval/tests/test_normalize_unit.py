"""Unit tests for normalization helpers."""

from decimal import Decimal

from lop_eval.normalize import extract_normalized_numbers, numbers_close


def test_extract_currency_mln():
    s = "Revenue reached EUR 100 mln in FY2024."
    nums = extract_normalized_numbers(s)
    assert any(n.kind == "currency" and n.value == Decimal("100000000") for n in nums)


def test_numbers_close_tolerance():
    assert numbers_close(Decimal("100"), Decimal("101"), 0.005) is False
    assert numbers_close(Decimal("100"), Decimal("100.2"), 0.005) is True
