"""Per-checker unit tests."""

from lop_eval.checkers import numeric, terminology
from lop_eval.document_io import load_proposal
from lop_eval.models import EvalConfig, ProposalDocument, Section
from lop_eval.models import ParagraphBlock

from pathlib import Path

_FIX = Path(__file__).resolve().parents[1] / "fixtures"


def test_numeric_checker_skips_generic_bucket():
    doc = ProposalDocument(
        document_id="bare",
        sections=[
            Section(
                id="x",
                blocks=[
                    ParagraphBlock(text="EUR 5 mln here."),
                    ParagraphBlock(text="EUR 9 mln elsewhere."),
                ],
            )
        ],
    )
    issues = numeric.check_numeric(doc, EvalConfig())
    assert not any(i.type == "numeric_conflict" for i in issues)


def test_terminology_checker_respects_classes():
    doc = load_proposal(_FIX / "negative_term_drift.json")
    issues = terminology.check_terminology(doc, EvalConfig())
    assert issues and issues[0].type == "terminology_drift"
