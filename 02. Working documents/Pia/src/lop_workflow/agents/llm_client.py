"""Optional OpenAI calls for structured workplan synthesis and section drafts."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from lop_workflow.agents.jasper_prompts import load_jasper_chapter_prompt
from lop_workflow.gold_patterns.loader import SectionGoldPattern, get_section_pattern
from lop_workflow.models.brief import LOPCategory
from lop_workflow.models.section import SectionId
from lop_workflow.models.source import SourceRef

if TYPE_CHECKING:
    from lop_workflow.models.brief import Brief
    from lop_workflow.models.problem import ProblemStatement


_CORPUS_PRIORITY: dict[SectionId, tuple[str, ...]] = {
    SectionId.CONTEXT: ("rfp_tender", "prior_proposal", "gold_lop", "capability_deck"),
    SectionId.WHY_MCKINSEY: ("gold_lop", "capability_deck", "prior_proposal"),
    SectionId.TIMELINE_TEAM: ("gold_lop", "prior_proposal", "rfp_tender"),
    SectionId.TEAM: ("gold_lop", "prior_proposal"),
    SectionId.CREDENTIALS: ("gold_lop", "capability_deck", "prior_proposal"),
    SectionId.MARKET: ("gold_lop", "rfp_tender"),
    SectionId.APPROACH: ("gold_lop", "prior_proposal", "rfp_tender"),
    SectionId.FEES: ("prior_proposal", "rfp_tender", "gold_lop"),
    SectionId.APPENDIX: ("gold_lop", "prior_proposal"),
    SectionId.REFERENCES: ("prior_proposal", "gold_lop"),
    SectionId.TEAM_CVS: ("gold_lop", "prior_proposal"),
}


def _tone_rider(category: LOPCategory | None) -> str:
    if category == LOPCategory.COMPETITIVE:
        return (
            "Tone: competitive pursuit — sharpen differentiation and proof; "
            "every claim needs manifest citation or `evidence required`."
        )
    if category == LOPCategory.RELATIONSHIP:
        return (
            "Tone: relationship-building — emphasize partnership and trust; "
            "avoid speculative ROI; keep market section proportionate."
        )
    if category == LOPCategory.EXPLORATORY:
        return (
            "Tone: exploratory — shorter Approach detail until Gate B; "
            "surface questions and TBDs explicitly."
        )
    return (
        "Tone: professional LoP — neutral staffing labels; no invented fees or client facts."
    )


def corpus_excerpt_for_section(
    section_id: SectionId,
    corpus: list[SourceRef],
    *,
    max_sources: int = 10,
    chars_per_snippet: int = 1200,
) -> str:
    """Pick top sources by ``source_type`` relevance for ``section_id``."""
    priority = _CORPUS_PRIORITY.get(section_id, ("gold_lop", "prior_proposal", "rfp_tender"))
    rank = {t: i for i, t in enumerate(priority)}

    def sort_key(s: SourceRef) -> tuple[int, str]:
        return (rank.get(s.source_type, len(priority)), s.source_id)

    ordered = sorted(corpus, key=sort_key)
    parts: list[str] = []
    for src in ordered[:max_sources]:
        parts.append(
            f"### {src.title} (type={src.source_type}, id={src.source_id})\n"
            f"{src.snippet[:chars_per_snippet]}"
        )
    return "\n\n".join(parts)


def _gold_scaffold_block(pattern: SectionGoldPattern) -> str:
    lines = ["Gold-pattern scaffold (follow structure; do not invent facts):"]
    if pattern.structure_hints:
        lines.append("Structure hints:")
        lines.extend(f"- {h}" for h in pattern.structure_hints)
    if pattern.win_logic:
        lines.append("Win logic:")
        lines.extend(f"- {w}" for w in pattern.win_logic)
    if pattern.must_have_evidence:
        lines.append("Evidence gates:")
        lines.extend(f"- {m}" for m in pattern.must_have_evidence)
    if pattern.sources:
        lines.append("Traceability (gold stems in corpus — cite snippets, not filenames alone):")
        for sp in pattern.sources[:8]:
            frag = sp.stem + (f" — {sp.note}" if sp.note else "")
            lines.append(f"- {frag}")
    return "\n".join(lines)


def llm_synthesize_problem(brief: Brief) -> ProblemStatement | None:
    """
    If ``OPENAI_API_KEY`` is set and ``openai`` is installed, draft a problem statement
    from the brief. Otherwise returns ``None`` (caller falls back to stub agents).
    """
    if not os.environ.get("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    from lop_workflow.models.problem import ProblemStatement

    client = OpenAI()
    payload = {
        "project_name": brief.project_name,
        "client_name": brief.client_name,
        "voice_notes": (brief.voice.raw_transcript if brief.voice else "")[:8000],
        "lop_category": (brief.lop_category.value if brief.lop_category else None),
    }
    resp = client.chat.completions.create(
        model=os.environ.get("LOP_OPENAI_MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You help draft McKinsey-style Letter of Proposal problem statements. "
                    "Return JSON only with keys: statement (string), lop_category "
                    "(one of: competitive, non_competitive, exploratory, relationship_building)."
                ),
            },
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=0.3,
    )
    choice = resp.choices[0].message.content
    if not choice:
        return None
    data = json.loads(choice)
    statement = str(data.get("statement", "")).strip()
    if not statement:
        return None
    raw_cat = str(data.get("lop_category", "exploratory")).lower()
    cat_map = {
        "competitive": LOPCategory.COMPETITIVE,
        "non_competitive": LOPCategory.NON_COMPETITIVE,
        "exploratory": LOPCategory.EXPLORATORY,
        "relationship_building": LOPCategory.RELATIONSHIP,
        "relationship_led": LOPCategory.RELATIONSHIP,
    }
    lop_cat = cat_map.get(raw_cat.replace(" ", "_"), LOPCategory.EXPLORATORY)
    return ProblemStatement(statement=statement, lop_category=lop_cat)


def llm_draft_section_markdown(
    *,
    section_id: SectionId,
    section_title: str,
    brief_excerpt: str,
    corpus_excerpt: str,
    lop_category: LOPCategory | None = None,
    prompts_root: str = "",
) -> str | None:
    """
    Section-specific draft using Jasper chapter stub + gold-pattern scaffold.

    Returns ``None`` if LLM unavailable.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    pattern = get_section_pattern(section_id, lop_category)
    jasper = load_jasper_chapter_prompt(section_id, prompts_root=prompts_root)
    gold_block = _gold_scaffold_block(pattern)
    tone = _tone_rider(lop_category)

    system_parts = [
        "You draft LoP (Letter of Proposal) sections in Markdown.",
        "Rules: no invented client facts, fees, credentials, or legal disclaimers.",
        "Mark unknowns as TBD; label inference as [inference] when needed.",
        "Reference sources by title/id from the corpus excerpt when stating proof.",
        tone,
    ]
    if jasper.strip():
        system_parts.append("--- Firm chapter instructions (Jasper) ---\n" + jasper.strip())
    system_parts.append("--- Gold scaffold ---\n" + gold_block)

    client = OpenAI()
    user_msg = (
        f"Section ID: {section_id.value}\n"
        f"Section title: {section_title}\n\n"
        f"Brief:\n{brief_excerpt}\n\n"
        f"Corpus excerpts:\n{corpus_excerpt}"
    )

    max_tokens = 1100 if section_id in (SectionId.APPROACH, SectionId.WHY_MCKINSEY) else 900
    resp = client.chat.completions.create(
        model=os.environ.get("LOP_OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "\n\n".join(system_parts)},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.35,
        max_tokens=max_tokens,
    )
    text = (resp.choices[0].message.content or "").strip()
    return text or None
