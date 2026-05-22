"""Load Jasper chapter prompt stubs (shared team markdown)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from lop_workflow.models.section import SectionId
from lop_workflow.workspace_paths import jasper_prompts_dir

_SECTION_FILES: dict[SectionId, str] = {
    SectionId.CONTEXT: "chapter-context-objectives.md",
    SectionId.WHY_MCKINSEY: "chapter-why-mckinsey.md",
    SectionId.TIMELINE_TEAM: "chapter-timeline-team.md",
    SectionId.TEAM: "chapter-team-shortlist.md",
    SectionId.CREDENTIALS: "chapter-credentials.md",
    SectionId.MARKET: "chapter-market-trends.md",
    SectionId.APPROACH: "chapter-approach-outline.md",
    SectionId.FEES: "chapter-fees.md",
    SectionId.APPENDIX: "chapter-appendix-references.md",
    SectionId.REFERENCES: "chapter-appendix-references.md",
    SectionId.TEAM_CVS: "chapter-appendix-references.md",
}


@lru_cache(maxsize=32)
def load_jasper_chapter_prompt(section_id: SectionId, prompts_root: str = "") -> str:
    """
    Return markdown body of the Jasper chapter file for ``section_id``.

    ``prompts_root`` is for tests; default uses :func:`jasper_prompts_dir`.
    """
    name = _SECTION_FILES.get(section_id)
    if not name:
        return ""
    base = Path(prompts_root) if prompts_root else jasper_prompts_dir()
    p = base / name
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def jasper_prompt_filename(section_id: SectionId) -> str:
    return _SECTION_FILES.get(section_id, "")
