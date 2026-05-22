"""Tests for EvalsBundle sync logic."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas import (
    ClientEvaluationReport,
    EvalsBundle,
    LossAnalysisReport,
    ReasonablenessCheck,
)


def _refresh_evals_done_flags(client: bool, loss: bool, consistency: bool) -> bool:
    return client and loss and consistency


def test_evals_done_requires_all_three():
    assert _refresh_evals_done_flags(True, True, True)
    assert not _refresh_evals_done_flags(True, True, False)


def test_evals_bundle_shape():
    bundle = EvalsBundle(
        run_id="20260101_120000",
        proposal_source="in_app_deck",
        client_eval=ClientEvaluationReport(
            overall_verdict="would_buy",
            score=80,
            headline_takeaway="Strong",
            timeline_check=ReasonablenessCheck(verdict="reasonable"),
            fees_check=ReasonablenessCheck(verdict="reasonable"),
            team_check=ReasonablenessCheck(verdict="reasonable"),
            approach_check=ReasonablenessCheck(verdict="reasonable"),
        ),
        loss_eval=LossAnalysisReport(
            framing_question="Why lose?",
            competitive_context="competitive",
            save_or_kill_verdict="competitive_as_is",
            loss_likelihood="low",
            loss_risk_score=20,
            punchline="ok",
        ),
        consistency_eval={"overall_score": 85, "passed": True},
        updated_at=datetime.now().isoformat(),
    )
    d = bundle.model_dump()
    assert d["run_id"] == "20260101_120000"
    assert d["consistency_eval"]["passed"] is True
