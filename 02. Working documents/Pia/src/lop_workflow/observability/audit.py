from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Generator

from lop_workflow.orchestrator.state import OrchestratorState, Phase


class EventKind(StrEnum):
    RUN_START = "run_start"
    PHASE = "phase"
    CHECKPOINT = "checkpoint"
    METRIC = "metric"
    EXPORT = "export"
    DONE = "done"
    ERROR = "error"


@dataclass
class AuditEvent:
    ts: str
    kind: str
    run_id: str
    message: str
    data: dict[str, Any] | None = None


@dataclass
class AuditLogger:
    log_path: str | None
    _events: list[AuditEvent] = field(default_factory=list)

    def emit(self, ts: str, kind: EventKind | str, run_id: str, message: str, data: dict | None) -> None:
        ev = AuditEvent(ts=ts, kind=str(kind), run_id=run_id, message=message, data=data)
        self._events.append(ev)
        if self.log_path:
            line = json.dumps(
                {
                    "ts": ev.ts,
                    "kind": ev.kind,
                    "run_id": ev.run_id,
                    "message": ev.message,
                    "data": ev.data,
                },
                ensure_ascii=False,
            )
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")


def get_audit_logger(log_path: str | None) -> AuditLogger:
    return AuditLogger(log_path=log_path)


@contextmanager
def phase_timer(
    alog: AuditLogger,
    st: OrchestratorState,
    phase: Phase,
) -> Generator[None, None, None]:
    t0 = time.perf_counter()
    try:
        yield
    finally:
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc).isoformat()
        dt_ms = (time.perf_counter() - t0) * 1000.0
        alog.emit(
            ts,
            EventKind.METRIC,
            st.run_id,
            f"phase_s_ms:{phase.value}",
            {
                "phase": phase.value,
                "duration_ms": round(dt_ms, 2),
                "export_type": st.meta.get("export_type"),
            },
        )


def emit_eval_metrics(alog: AuditLogger, st: OrchestratorState, **extra: Any) -> None:
    from datetime import datetime, timezone

    rubric = st.meta.get("eval_rubric_scores") or {}
    alog.emit(
        datetime.now(timezone.utc).isoformat(),
        EventKind.METRIC,
        st.run_id,
        "eval_snapshot",
        {
            "rounds": st.meta.get("human_rounds", 0),
            "export_type": st.meta.get("export_type"),
            **rubric,
            **extra,
        },
    )
