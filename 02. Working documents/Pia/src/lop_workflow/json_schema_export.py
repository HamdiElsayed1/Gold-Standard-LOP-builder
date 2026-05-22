"""
Emit JSON Schema files for the core LOP workflow models.
Run: python -m lop_workflow.json_schema_export
"""
from __future__ import annotations

import json
from pathlib import Path

from lop_workflow.models import (
    Brief,
    ClientTruth,
    ConflictLog,
    FactsRegistry,
    LOPCoachReport,
    LOPDocument,
    ProblemStatement,
    ScaffoldingOut,
    SectionContent,
    SectionSpec,
    VoiceIngestionMeta,
)
from lop_workflow.models.coach import LOPCoachIssue, SectionScore
from lop_workflow.models.conflict import ConflictEntry
from lop_workflow.models.facts import FactEntry
from lop_workflow.models.source import Citation, SourceRef

_SCHEMA_MAP: dict[str, type] = {
    "brief": Brief,
    "voice_ingestion_meta": VoiceIngestionMeta,
    "problem_statement": ProblemStatement,
    "section_spec": SectionSpec,
    "section_content": SectionContent,
    "lop_document": LOPDocument,
    "scaffolding": ScaffoldingOut,
    "facts_registry": FactsRegistry,
    "fact_entry": FactEntry,
    "lop_coach_report": LOPCoachReport,
    "lop_coach_issue": LOPCoachIssue,
    "section_score": SectionScore,
    "conflict_log": ConflictLog,
    "conflict_entry": ConflictEntry,
    "client_truth": ClientTruth,
    "citation": Citation,
    "source_ref": SourceRef,
}


def export_json_schemas(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, model in _SCHEMA_MAP.items():
        path = out_dir / f"{name}.schema.json"
        if hasattr(model, "model_json_schema"):
            schema = model.model_json_schema(mode="validation")
        else:
            raise TypeError(f"Not a Pydantic model: {model}")
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        written.append(path)
    return written


def main() -> None:
    # Project root: two levels up from this file: src/lop_workflow/json_schema_export.py -> project root
    root = Path(__file__).resolve().parents[2] / "json_schemas"
    for p in export_json_schemas(root):
        print(p)


if __name__ == "__main__":
    main()
