"""
Ingestion agent: voice → structured brief pieces; email threads; RFP chunking.

Policy / PII: emit `pii_flags` for fields that may need redaction before external tools.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lop_workflow.models.brief import Brief, VoiceIngestionMeta
from lop_workflow.models.source import SourceRef


def _unique_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


@dataclass
class IngestionInput:
    """Inputs for the ingestion step."""

    voice_transcript: str = ""
    email_thread_text: str = ""
    tender_chunks: list[str] = field(default_factory=list)
    run_id: str = ""
    project_name: str = ""
    client_name: str = ""


@dataclass
class IngestionOutput:
    brief_partial: dict[str, Any]
    sources: list[SourceRef]
    pii_flags: list[str]


def run_ingestion(inp: IngestionInput) -> IngestionOutput:
    """
    Deterministic stub: split transcript to bullets; tag client line as possible PII.
    Replace with ASR cleanup + LLM extraction in production.
    """
    voice = VoiceIngestionMeta.from_transcript(inp.voice_transcript) if inp.voice_transcript else None
    pii_parts: list[str] = []
    if inp.client_name:
        pii_parts.append("client_name")
    if inp.email_thread_text.strip():
        pii_parts.append("email_excerpt")
    if voice:
        pii_parts.extend(voice.pii_flags)
        if voice.raw_transcript.strip():
            pii_parts.append("raw_transcript")
    pii = _unique_keep_order(pii_parts)
    sources: list[SourceRef] = []
    for i, ch in enumerate(inp.tender_chunks):
        sources.append(
            SourceRef(
                source_id=f"tender-chunk-{i}",
                source_type="tender",
                title=f"Tender chunk {i+1}",
                snippet=ch[:2000],
            )
        )
    return IngestionOutput(
        brief_partial={
            "run_id": inp.run_id,
            "project_name": inp.project_name,
            "client_name": inp.client_name,
            "voice": voice.model_dump() if voice else None,
            "email_excerpt": inp.email_thread_text[:5000],
        },
        sources=sources,
        pii_flags=pii,
    )


def apply_ingestion_to_brief(b: Brief, out: IngestionOutput) -> None:
    d = out.brief_partial
    b.project_name = d.get("project_name") or b.project_name
    b.client_name = d.get("client_name") or b.client_name
    b.email_excerpt = d.get("email_excerpt") or b.email_excerpt
    if d.get("voice") and b.voice is None:
        b.voice = VoiceIngestionMeta.model_validate(d["voice"])
    b.rfp_tender_references.extend(out.sources)
