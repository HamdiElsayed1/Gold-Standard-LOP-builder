"""Tests for LLM judge prompt formatting and parsing."""

from lop_eval.llm_judge import format_judge_prompt, parse_judge_response


def test_format_judge_prompt_includes_sections():
    p = format_judge_prompt(
        criteria="Same metric must match.",
        reference="EUR 100 mln",
        response="EUR 120 mln",
    )
    assert "Same metric must match" in p
    assert "EUR 100 mln" in p
    assert "EUR 120 mln" in p


def test_parse_judge_pass():
    v = parse_judge_response("Score: 1\nReasoning: Labels are equivalent.")
    assert v is not None
    assert v.score == 1


def test_parse_judge_fail():
    v = parse_judge_response("Score: 0\nReasoning: Different values.")
    assert v is not None
    assert v.score == 0


def test_parse_judge_malformed():
    assert parse_judge_response("no score here") is None
