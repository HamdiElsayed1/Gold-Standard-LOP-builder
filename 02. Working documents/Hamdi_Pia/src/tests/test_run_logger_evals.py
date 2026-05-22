"""Run logger eval export."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run_logger import append_evals_json_to_log, get_run_logger, log_evals_bundle


def test_log_evals_bundle_and_json_export(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "run_logger._RUNS_DIR",
        tmp_path,
    )
    run_id = "test_evals_run"
    bundle = {
        "run_id": run_id,
        "proposal_source": "in_app_deck",
        "updated_at": "2026-01-01T12:00:00",
        "consistency_eval": {
            "overall_score": 85,
            "passed": True,
            "summary": {"critical": 0, "major": 1, "minor": 0},
            "score_breakdown": {"numeric": 10.0},
            "issues": [
                {
                    "severity": "major",
                    "type": "numeric_conflict",
                    "description": "conflict",
                }
            ],
        },
    }
    log_evals_bundle(run_id, bundle)
    _, log_path = get_run_logger(run_id)
    text = log_path.read_text(encoding="utf-8")
    assert "[EVALS] Consistency QC" in text
    assert "EVALS_JSON_EXPORT" in text
    assert "numeric_conflict" in text
