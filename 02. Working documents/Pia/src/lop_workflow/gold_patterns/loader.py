"""Load ``catalog.yaml`` and resolve per-section patterns with LOP category overlays."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from lop_workflow.models.brief import LOPCategory
from lop_workflow.models.section import SectionId


class SourcePointer(BaseModel):
    """Human traceability to gold files (stem or doc title fragment)."""

    stem: str = ""
    note: str = ""


class SectionGoldPattern(BaseModel):
    structure_hints: list[str] = Field(default_factory=list)
    win_logic: list[str] = Field(default_factory=list)
    must_have_evidence: list[str] = Field(default_factory=list)
    sources: list[SourcePointer] = Field(default_factory=list)
    category_overrides: dict[str, dict[str, Any]] = Field(default_factory=dict)


class GoldCatalog(BaseModel):
    version: int = 1
    sections: dict[str, SectionGoldPattern] = Field(default_factory=dict)


def _catalog_path() -> Path:
    return Path(__file__).resolve().parent / "catalog.yaml"


@lru_cache(maxsize=1)
def load_gold_catalog(path: str | None = None) -> GoldCatalog:
    """Load catalog from package ``catalog.yaml`` (override path mainly for tests)."""
    p = Path(path) if path else _catalog_path()
    if not p.is_file():
        return GoldCatalog()
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    sections_raw = raw.get("sections") or {}
    sections: dict[str, SectionGoldPattern] = {}
    for key, val in sections_raw.items():
        if isinstance(val, dict):
            sections[key] = SectionGoldPattern.model_validate(val)
    return GoldCatalog(version=int(raw.get("version", 1)), sections=sections)


def _merge_override(base: SectionGoldPattern, overlay: dict[str, Any]) -> SectionGoldPattern:
    data = base.model_dump()
    for k, v in overlay.items():
        if k in {"structure_hints", "win_logic", "must_have_evidence"} and isinstance(v, list):
            data[k] = list(data.get(k, [])) + [str(x) for x in v]
        elif k == "sources" and isinstance(v, list):
            data[k] = list(data.get(k, [])) + v
        elif k != "category_overrides":
            data[k] = v
    return SectionGoldPattern.model_validate(data)


def get_section_pattern(
    section_id: SectionId,
    category: LOPCategory | None = None,
    *,
    catalog: GoldCatalog | None = None,
) -> SectionGoldPattern:
    """Return pattern for ``section_id``, merged with optional ``LOPCategory`` overlay."""
    cat = catalog or load_gold_catalog()
    key = section_id.value
    base = cat.sections.get(key) or SectionGoldPattern()
    if not category:
        return base
    ov = base.category_overrides.get(category.value)
    if not ov:
        return base
    return _merge_override(base, ov)
