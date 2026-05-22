"""Workspace-relative paths: Background Material (inputs) and default LoP exports (outputs)."""

from __future__ import annotations

import os
from pathlib import Path


def documents_workspace_root() -> Path:
    """
    Root folder `Gold Standard LOP Builder - Documents`
    (four levels above this file: lop_workflow -> src -> Pia -> 02. Working documents -> root).
    """
    return Path(__file__).resolve().parents[4]


def _candidate_background_dirs() -> list[Path]:
    """Prefer numbered folder used in this workspace; fall back to legacy `Background Material`."""
    root = documents_workspace_root()
    return [
        root / "01. Background material",
        root / "Background Material",
    ]


def background_material_dir() -> Path:
    """
    Authoritative read-only corpus for `run_research`.

    Resolution order: ``LOP_BACKGROUND_MATERIAL_DIR`` env → first existing candidate → create preferred.
    """
    override = os.environ.get("LOP_BACKGROUND_MATERIAL_DIR")
    if override:
        return Path(override)
    for p in _candidate_background_dirs():
        if p.is_dir():
            return p
    preferred = documents_workspace_root() / "01. Background material"
    preferred.mkdir(parents=True, exist_ok=True)
    return preferred


def background_material_extracted_dir() -> Path:
    """
    Normalized markdown cache for PPTX/PDF extractions (workspace root).

    Lives under ``Background Material/extracted`` per gold-standard workflow (not inside numbered folder).
    """
    return documents_workspace_root() / "Background Material" / "extracted"


def jasper_prompts_dir() -> Path:
    """Jasper chapter prompts for LoP drafting (shared team assets)."""
    return documents_workspace_root() / "02. Working documents" / "Jasper" / "prompts"


def lop_exports_dir() -> Path:
    """Generated PPT/HTML/XLSX land here by default (``02. Working documents/Fleur/exports``)."""
    override = os.environ.get("LOP_EXPORT_DIR") or os.environ.get("LOP_SJORS_EXPORT_DIR")
    if override:
        return Path(override)
    return documents_workspace_root() / "02. Working documents" / "Fleur" / "exports"


def lop_workspace_dir() -> Path:
    """Parent folder for default exports and other personal artifacts (e.g. ``audit.log``)."""
    return lop_exports_dir().parent


def ensure_workspace_directories() -> None:
    """Ensure corpus, extraction cache, and default export folders exist."""
    background_material_dir()
    background_material_extracted_dir().mkdir(parents=True, exist_ok=True)
    lop_exports_dir().mkdir(parents=True, exist_ok=True)


def sjors_exports_dir() -> Path:
    """Backward-compatible alias for :func:`lop_exports_dir`."""
    return lop_exports_dir()


def sjors_workspace_dir() -> Path:
    """Backward-compatible alias for :func:`lop_workspace_dir`."""
    return lop_workspace_dir()
