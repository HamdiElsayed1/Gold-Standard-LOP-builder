"""
Shared McKinsey style guide rendered into every slide-author user_message.

Single source of truth for action-title rules, forbidden-phrase list, number
conventions, sourcing rule, and "no invented facts" guard. All ten chapter
agents under `agents/slide-*-agent.md` rely on the calling code in
`app.py` prepending this block to their user turn, so a rule change here
propagates to every slide without touching ten spec files.

Mirrors the pattern of `lop_chapters.render_chapter_brief()`.
"""

from __future__ import annotations


_FORBIDDEN_PHRASES: tuple[str, ...] = (
    "leverage",
    "going forward",
    "best-in-class",
    "low-hanging fruit",
    "synergize",
    "synergise",
    "various",
    "several (without a number)",
    "significant (without a magnitude)",
    "substantial (without a magnitude)",
    "it should be noted",
    "in order to",
    "at this point in time",
    "world-class",
    "robust (as filler)",
)


def render_slide_style_guide() -> str:
    """
    Render the McKinsey slide style guide as a markdown block to embed in the
    slide-author user_message. The block is self-contained: it begins with a
    `## McKinsey Slide Style Guide` header so it parses cleanly inside any
    wrapping prompt.

    The style guide enforces:
      * Action titles (declarative, sentence case, <=20 words).
      * Forbidden phrases the model must not emit (with rewrites).
      * Number / currency / time conventions.
      * Active voice, no hedging — concrete rewrite examples.
      * Sourcing rule + the exact `<div class="source">` snippet to use.
      * No-invented-facts guard.
    """
    forbidden_block = ", ".join(f"`{p}`" for p in _FORBIDDEN_PHRASES)

    return "\n".join(
        [
            "## McKinsey Slide Style Guide",
            "",
            "Apply ALL rules below when authoring the HTML body. These rules "
            "are non-negotiable and override any conflicting habit from "
            "general LLM training.",
            "",
            "### Action titles",
            "",
            "- Every content slide title is a complete declarative sentence "
            "stating the conclusion or insight, not a label.",
            "- Sentence case (only first word and proper nouns capitalised). "
            "No period at the end unless the title is two sentences.",
            "- Maximum ~20 words / 2 lines.",
            "- Correct: \"COGS assessment identifies EUR 15.7 mln potential "
            "with 95% of food validated\".",
            "- Incorrect: \"COGS Overview\", \"Synergy Dashboard\", "
            "\"Next Steps\", \"Financial Analysis Results\".",
            "",
            "### Forbidden phrases (do NOT emit)",
            "",
            f"{forbidden_block}.",
            "",
            "Replace with a specific, concrete formulation:",
            "",
            "- \"leverage X\" -> \"use X\".",
            "- \"going forward\" -> name the timeframe (e.g. \"in 2026 Q1\").",
            "- \"various initiatives\" -> state the number (e.g. \"three "
            "initiatives\").",
            "- \"significant savings\" -> state the magnitude (e.g. \"EUR 9.1 "
            "mln in savings\").",
            "- \"best-in-class\" -> cite the specific benchmark.",
            "- \"in order to\" -> just \"to\".",
            "",
            "### Numbers, currency, time",
            "",
            "- Currency: `EUR 9.1 mln` (currency code, space, number, space, "
            "unit). Use `mln`, `bln`, `trn` — not \"million\", \"M\", or \"$M\".",
            "- Percentages: `95%` (no space). Percentage points: `3pp`.",
            "- Multiples: `4.2x` (lowercase, no space).",
            "- Fiscal year: `FY2025`. Quarter: `2027 Q1`. CAGR: `8.2% CAGR`.",
            "- Ranges: `EUR 5-9 mln` (en dash, no spaces around).",
            "- Round to one decimal for millions, whole number for billions.",
            "",
            "### Voice and tone",
            "",
            "- Active voice. \"The team identified EUR 9.1 mln in savings\" "
            "— not \"EUR 9.1 mln in savings were identified\".",
            "- Authoritative, never enthusiastic. No exclamation marks. No "
            "italics for emphasis (italics are reserved for source citations).",
            "- Confident verbs: `recommend`, `deliver`, `identify`, `prove`. "
            "Not `consider`, `explore`, `aim to`, `look into`.",
            "- One idea per bullet; bullets <=20 words; parallel grammar "
            "across a list (all start with the same part of speech).",
            "",
            "### Source footer (every content slide)",
            "",
            "Every content slide ends with the source block below, citing "
            "the upstream source mode the facts came from (RFP, partner "
            "answers, ContextDoc web search, BA pack one-pagers, model "
            "knowledge). The cover slide and Appendix slides are exempt.",
            "",
            "```html",
            "<div class=\"source\"><p>Source: ...</p></div>",
            "```",
            "",
            "Examples of acceptable source lines:",
            "",
            "- `Source: RFP and partner answers`.",
            "- `Source: Partner answers; team analysis`.",
            "- `Source: ContextDoc web search 2026; team analysis`.",
            "- `Source: Model knowledge - context (directional only)` "
            "— only when no upstream source exists.",
            "",
            "### Chrome block (every Default and 2/3 content slide)",
            "",
            "Every content slide using `data-layout=\"Default\"` or "
            "`data-layout=\"2/3\"` MUST include the chrome block as the "
            "first child of `<section class=\"slide\">`. The cover "
            "(`data-layout=\"Title\"`) is exempt — its chrome is the "
            "full-bleed background.",
            "",
            "```html",
            "<div data-pptx=\"chrome\" class=\"chrome\">",
            "  <span class=\"slide-number\">N</span>",
            "  <span class=\"logo\">McKinsey &amp; Company</span>",
            "</div>",
            "```",
            "",
            "Substitute `N` with the 1-based slide number for THIS slide "
            "in the deck. Get it from `slide_index + 1` in your inputs.",
            "",
            "### Confidence ribbon (do NOT print 'Placeholder' as body text)",
            "",
            "When this slide's `confidence` is `partial` or `placeholder`, "
            "mark the section with the matching `data-confidence` "
            "attribute on the root element — the deck stylesheet renders "
            "a small amber ribbon in the top-right corner automatically:",
            "",
            "```html",
            "<section class=\"slide\" data-layout=\"Default\" "
            "data-confidence=\"partial\">",
            "```",
            "",
            "Do NOT add a paragraph saying \"Placeholder — pending partner "
            "confirmation\" inside the body. Do NOT add italic notes. The "
            "ribbon is the only indicator the BA needs.",
            "",
            "### No invented facts",
            "",
            "Use ONLY facts present in the inputs (intake package, context "
            "doc, synthesis problem statement, this slide's DotDashSlide "
            "headline + supporting points, BA pack source items, "
            "client_style_summary). If a name, number, date, competitor, "
            "credential, expert, or trend is NOT in the inputs, do not "
            "write it.",
            "",
            "When a chapter-specific input is missing (e.g. no fee model in "
            "the BA pack for the Fees chapter), render a single short "
            "placeholder cell `[fee model pending — partner to confirm]` "
            "INSIDE the relevant table cell or grid track only — never as "
            "a standalone body paragraph at the bottom of the slide.",
            "",
            "### Content zone flow",
            "",
            "The `.content` zone (the band between the title and the bottom "
            "source strip) is a flex column anchored to the TOP. Author "
            "content top-down: the most important band first, then the next, "
            "then the next. The CSS already provides `display: flex; "
            "flex-direction: column; align-items: stretch; "
            "justify-content: flex-start; gap: 32px;` on `.content` — your "
            "job is to not undo it.",
            "",
            "- Do NOT use `min-height: 100%`, `height: 100%`, or "
            "`flex: 1 1 100%` on a top-level child of `.content` to \"fill\" "
            "the slide. The bundled CSS sets `flex: 0 0 auto` on direct "
            "children precisely so a single block cannot grow to 100% and "
            "vertically-center its inner content — that is what produces "
            "the empty upper-third \"zoomed in\" effect.",
            "- Do NOT use `align-items: center` or `justify-content: center` "
            "on the immediate child of `.content`. Use `flex-start` / "
            "`start` (the default) so content fills the top of the zone "
            "first.",
            "- Stay inside the `.content` zone — CSS clips overflow at "
            "~102px from the slide bottom. Tighten language rather than "
            "overflow.",
            "- Do NOT emit body paragraphs inside `.footnote` or `.source`. "
            "Those two strips (988-1008px and 1024-1043px) are reserved "
            "for one-line footnote callouts and the source citation "
            "respectively. If you have nothing footnote-worthy, omit "
            "`.footnote` entirely. The CSS now hard-clips both strips to a "
            "single line with `text-overflow: ellipsis`, so anything longer "
            "is silently truncated.",
            "- Source line: keep to a single short line (~90 characters "
            "max) so the ellipsis clip never engages.",
            "",
            "### Hard formatting rules",
            "",
            "- No `<table>` — use `<div>` + CSS grid or flexbox.",
            "- No `<script>`, no external font imports, no images, no chart "
            "JSON. Charts are out of scope; substitute with text + CSS shapes.",
            "- Multi-paragraph blocks wrap each paragraph in `<p>`. Never "
            "leave bare text inside a multi-paragraph shape.",
            "- **Rectangles never get rounded corners.** Numbered indicators "
            "are circular `<div>`s with `border-radius: 50%` (50% only — "
            "never `8px`, `12px`, or any other pixel radius). Rectangles, "
            "cells, and containers stay sharp-cornered.",
            "- Visible lines use a thin `<div>` with `background` or `<line>` "
            "inside `<svg>`. Never CSS `border` / `border-bottom` for visible "
            "lines.",
            "- **Body text is `#000000` or `#FFFFFF` only.** Never apply a "
            "`color:` style on `<p>`, `<span>`, `<li>`, `<strong>`, `<em>`, "
            "or `<h*>` elements. This includes `color:var(--electric-blue-900)`, "
            "`color:var(--cyan-700)`, `color:#061F79`, etc. Use `background:` "
            "fills, shapes, and layout to create visual hierarchy — never "
            "font color. The ONLY exception is the cover slide title, which "
            "renders white on the navy gradient via the bundled CSS rule.",
            "- Highlights use `background:var(--electric-blue-900)` (with "
            "`color:#FFFFFF` text) or `background:var(--cyan-lightest)` "
            "(with `color:#000000` text). Pick ONE accent per slide.",
            "- Stay inside the `.content` zone (see \"Content zone flow\" "
            "above — the CSS hard-clips the bottom strip). Tighten language "
            "rather than overflow.",
            "",
            "### Output schema (multi-slide)",
            "",
            "Return a single JSON object `{ \"slides\": [...], \"notes\": "
            "\"\" }` where `slides` is an array of one or more slide "
            "fragments. Each fragment has the shape `{ \"html_body\": "
            "\"<section ...>...</section>\", \"notes\": \"\" }`. Most "
            "chapter agents return exactly one fragment; emit a second "
            "fragment only when the chapter content genuinely warrants a "
            "second page (e.g. Credentials with two anchor cases, Approach "
            "with a phased grid plus a workplan timeline). The cover agent "
            "always returns exactly one fragment.",
            "",
        ]
    )
