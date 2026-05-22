"""Adapter tests for Streamlit deck / text ingestion."""

from lop_eval.adapters.from_streamlit import proposal_from_text
from lop_eval.evaluator import evaluate_document
from lop_eval.models import ParagraphBlock, ProposalDocument, Section


def test_proposal_from_text_slide_split():
    text = """--- Slide 1: Context ---
Revenue was EUR 100 mln.

--- Slide 2: Fees ---
Revenue was EUR 100 mln."""
    doc = proposal_from_text(text, "t1")
    assert len(doc.sections) == 2
    assert doc.sections[0].title.startswith("Slide")


def test_evaluate_positive_numeric_fixture():
    from pathlib import Path
    from lop_eval.document_io import load_proposal

    fix = Path(__file__).resolve().parents[1] / "fixtures" / "positive_numeric.json"
    doc = load_proposal(fix)
    res = evaluate_document(doc)
    assert res.overall_score >= 70
    assert not any(i.type == "numeric_conflict" for i in res.issues)


def test_proposal_from_minimal_section():
    doc = ProposalDocument(
        document_id="x",
        sections=[
            Section(
                id="a",
                blocks=[ParagraphBlock(text="Revenue was EUR 100 mln.")],
            )
        ],
    )
    res = evaluate_document(doc)
    assert res.document_id == "x"
