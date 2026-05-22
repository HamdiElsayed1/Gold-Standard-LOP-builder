"""Load structured documents from JSON (for tests and CLI)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lop_eval.models import ProposalDocument


def load_proposal(path: str | Path) -> ProposalDocument:
    raw = Path(path).read_text(encoding="utf-8")
    data: dict[str, Any] = json.loads(raw)
    return ProposalDocument.model_validate(data)
