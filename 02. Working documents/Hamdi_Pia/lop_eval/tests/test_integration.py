"""Integration tests over fixtures."""

from pathlib import Path

import pytest

from lop_eval.document_io import load_proposal
from lop_eval.evaluator import evaluate_document
from lop_eval.models import FactRecord, SourceOfTruth

_FIX = Path(__file__).resolve().parents[1] / "fixtures"


def _types(doc_path: str) -> set[str]:
    doc = load_proposal(_FIX / doc_path)
    res = evaluate_document(doc)
    return {i.type for i in res.issues}


def test_positive_numeric_clean():
    assert "numeric_conflict" not in _types("positive_numeric.json")


def test_negative_numeric_revenue():
    t = _types("negative_numeric_revenue.json")
    assert "numeric_conflict" in t


def test_negative_stock_year():
    assert "numeric_year_inconsistency" in _types("negative_stock_year.json")


def test_positive_terminology():
    assert "terminology_drift" not in _types("positive_terminology.json")


def test_negative_term_drift():
    res = evaluate_document(load_proposal(_FIX / "negative_term_drift.json"))
    drift = [i for i in res.issues if i.type == "terminology_drift"]
    assert drift
    assert drift[0].severity.value == "major"


def test_terminology_bridge_downgrades():
    res = evaluate_document(load_proposal(_FIX / "terminology_bridge_minor.json"))
    drift = [i for i in res.issues if i.type == "terminology_drift"]
    assert drift
    assert drift[0].severity.value == "minor"


def test_negative_scope():
    assert "scope_drift" in _types("negative_scope.json")


def test_negative_timeline():
    assert "timeline_phase_month_conflict" in _types("negative_timeline.json")


def test_negative_units():
    assert "unit_currency_mixing" in _types("negative_units.json")


def test_negative_formatting():
    assert "representation_percent_vs_decimal" in _types("negative_formatting.json")


def test_negative_claim_support():
    assert "claim_support_table_prose_gap" in _types("negative_claim_support.json")


def test_negative_comparative():
    assert "comparative_conflict" in _types("negative_comparative.json")


def test_negative_abbreviation():
    assert "abbreviation_conflict" in _types("negative_abbreviation.json")


def test_faithfulness_flag_when_configured():
    doc = load_proposal(_FIX / "faithfulness_missing.json")
    sot = SourceOfTruth(
        facts=[FactRecord(key="approved_baseline", value_text="EUR 9 mln baseline approved")]
    )
    res = evaluate_document(doc, source_of_truth=sot)
    assert "faithfulness_missing_fact" in {i.type for i in res.issues}


def test_end_to_end_result_schema():
    doc = load_proposal(_FIX / "positive_numeric.json")
    res = evaluate_document(doc)
    payload = res.model_dump()
    assert payload["document_id"] == "positive_numeric"
    assert "overall_score" in payload
    assert "passed" in payload
    assert "summary" in payload
    assert "issues" in payload
