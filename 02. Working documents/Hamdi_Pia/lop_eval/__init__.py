"""LoP proposal output consistency evaluation (eval-only; no HTML, no drafting)."""

SPEC_VERSION = "0.1.0"

from lop_eval.document_io import load_proposal
from lop_eval.evaluator import evaluate_document
from lop_eval.models import EvalConfig, EvalResult, ProposalDocument, SourceOfTruth

__all__ = [
    "SPEC_VERSION",
    "evaluate_document",
    "load_proposal",
    "EvalConfig",
    "EvalResult",
    "ProposalDocument",
    "SourceOfTruth",
]
