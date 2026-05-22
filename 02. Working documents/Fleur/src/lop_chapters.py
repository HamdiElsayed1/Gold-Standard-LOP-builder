"""
Canonical LoP chapter definitions — single source of truth for every agent
in the pipeline.

Agents do not classify, score, or draft against bare chapter names. They
classify and grade against the definitions below. When chapter intent
changes, change it here and all agents pick up the new behaviour the next
time they run (each call-site appends `render_chapter_brief()` to its
user_message).

The order of `CHAPTER_DEFINITIONS` is the canonical order of the LoP itself
and must be preserved by every consumer (intake `chapter_buckets`,
synthesis question_list, dot-dash slides).
"""

from __future__ import annotations

# Insertion order is the canonical chapter order — do not reorder casually.
CHAPTER_DEFINITIONS: dict[str, str] = {
    "Context and Objectives": (
        "States the client's core issue and presents a day-one answer based on "
        "the inputs. This is the partner's working hypothesis on the problem and "
        "the recommended response, established up front so the rest of the LoP "
        "supports a clear position."
    ),
    "Why McKinsey": (
        "Multiple distinct points explaining why McKinsey is the ideal partner "
        "for THIS client, for THIS study type, against the competitors named "
        "in the pursuit. Tailoring is mandatory; generic boilerplate fails this "
        "chapter."
    ),
    "Timeline and Team": (
        "High-level timing and staffing schematic for the first partner "
        "conversation. Detailed workplan lives under Approach; detailed team "
        "under Team. This chapter is the at-a-glance summary, not the full plan."
    ),
    "Team": (
        "The McKinsey team delivering the work: core team on the ground, "
        "leadership, partner group, and experts. Must explicitly flag any "
        "QuantumBlack, Aberkyn, or Orphoz involvement so the client sees the "
        "full firm capability assembled for them."
    ),
    "Credentials": (
        "Comparable prior McKinsey work where we have done a similar "
        "engagement. In most pursuits we ASK the partner to supply internal "
        "references so we can pull one-pagers or case descriptions and adapt "
        "them to this client's situation."
    ),
    "Market Trends": (
        "Market and sector context relevant to the client's problem. Drawn "
        "from public/published sources or McKinsey research, clearly labelled "
        "when sourced from model knowledge so the partner can validate before "
        "sending to the client."
    ),
    "Approach": (
        "A schematic workplan and the deliverables. Drives the bulk of the "
        "partner conversation: guiding questions on how the study will be run, "
        "plus an initial hypothesis sized to the project length (short "
        "engagement = focused diagnostic; long engagement = phased delivery)."
    ),
    "Fees": (
        "The commercial fee structure for the engagement. In most cases this "
        "is a synthesis of an Excel fee model the partner provides; the "
        "chapter cannot be drafted credibly without it."
    ),
    "Appendix": (
        "Supporting material that does not fit the main narrative but the "
        "client may want to see: additional credentials, methodology detail, "
        "references, supporting analysis."
    ),
}


CHAPTER_ORDER: tuple[str, ...] = tuple(CHAPTER_DEFINITIONS.keys())


def render_chapter_brief() -> str:
    """
    Render the canonical chapter definitions as a markdown block to embed in
    an agent's `user_message`. The block is self-contained: it includes a
    header so it parses cleanly inside any wrapping prompt.

    Returns
    -------
    str
        A markdown section beginning with `## LoP Chapter Definitions`,
        listing each chapter as `**<name>** — <definition>`.
    """
    lines = ["## LoP Chapter Definitions", ""]
    for name, definition in CHAPTER_DEFINITIONS.items():
        lines.append(f"- **{name}** — {definition}")
    lines.append("")
    lines.append(
        "Use these definitions when classifying, grading, asking partner "
        "questions about, or drafting any chapter. A chapter is only "
        "`complete` when its content matches what the chapter is meant to "
        "deliver per the definition above — not merely when the topic is "
        "mentioned."
    )
    return "\n".join(lines)
