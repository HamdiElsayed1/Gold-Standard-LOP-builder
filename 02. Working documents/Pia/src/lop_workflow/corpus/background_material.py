"""Load provenance snippets from the Background Material folder (markdown, text, pptx, pdf)."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from lop_workflow.corpus.document_extract import ensure_extracted_markdown
from lop_workflow.models.source import SourceRef
from lop_workflow.workspace_paths import background_material_extracted_dir

logger = logging.getLogger(__name__)


def _stable_id(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:16]


def classify_background_source_type(path: Path) -> str:
    """Heuristic labels for RAG weighting and drafting (not legal classification)."""
    name = path.name.lower()
    if "proposal" in name and path.suffix.lower() == ".pdf":
        return "prior_proposal"
    if "rfp" in name or "tender" in name:
        return "rfp_tender"
    if "lop guide" in name or "gem lop" in name or "gold standard" in name:
        return "gold_lop"
    if "introduction" in name or "aberkyn" in name:
        return "capability_deck"
    if name.endswith(".msg"):
        return "email_stub"
    return "gold_lop"


def load_background_sources(
    root: Path,
    *,
    max_files: int = 400,
    snippet_chars: int = 2000,
    extracted_dir: Path | None = None,
) -> list[SourceRef]:
    """
    Index ``*.md``, ``*.txt``, ``*.pptx``, ``*.pdf`` under ``root``.

    PPTX/PDF are normalized to markdown under ``Background Material/extracted`` (cached by mtime).
    ``*.msg`` is skipped (log only).
    Returns empty list if ``root`` is missing or not a directory.
    """
    if not root.is_dir():
        return []

    ext_root = extracted_dir if extracted_dir is not None else background_material_extracted_dir()
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()

    paths: list[Path] = []
    for pattern in ("**/*.md", "**/*.txt", "**/*.pptx", "**/*.pdf", "**/*.msg"):
        paths.extend(p for p in root.glob(pattern) if p.is_file())

    # De-dupe: if we have both raw pptx and its extracted md under extracted/, prefer indexing extracted once
    paths = sorted({p.resolve() for p in paths})[:max_files]

    out: list[SourceRef] = []
    for p in paths:
        suffix = p.suffix.lower()
        if suffix == ".msg":
            logger.info("Skipping Outlook .msg (not indexed): %s", p.name)
            continue

        read_path = p
        uri = str(p)
        source_type = classify_background_source_type(p)

        if suffix in {".pptx", ".pdf"}:
            cached = ensure_extracted_markdown(p, ext_root)
            if cached and cached.is_file():
                read_path = cached
                uri = f"{p}|extracted:{cached}"

        try:
            text = read_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        snippet = text.strip()[:snippet_chars]
        if not snippet:
            continue

        out.append(
            SourceRef(
                source_id=f"bm-{_stable_id(p)}",
                source_type=source_type,
                title=p.stem,
                uri=uri,
                retrieved_at=now,
                snippet=snippet,
            )
        )

    return out
