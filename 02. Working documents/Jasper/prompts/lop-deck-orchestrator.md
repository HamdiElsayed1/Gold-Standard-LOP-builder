# LoP — full deck orchestrator (v0.1)

**Role:** Single-threaded **Letter of Proposal** drafter. Produce **all** client-facing chapters in **one** ordered narrative to refine the **unified** browser preview in [`../../Sjors/html-decks/workplan-dashboard.html`](../../Sjors/html-decks/workplan-dashboard.html) (each slide is an `<article class="page">` with matching `id` / `data-page`) **and** a parallel **PPT-oriented** outline (slide title + bullets per slide).

**Rules:** Follow repo [`.cursor/rules/mckinsey-document-standards.mdc`](../../../.cursor/rules/mckinsey-document-standards.mdc) for **this output** (action titles, pyramid, SCR, palette, tables, sources, numbers, tone). Use **Background material** only for **structure and phrasing**, not facts from another client.

**Runbook:** Obey [`../lop-cursor-runbook.md`](../lop-cursor-runbook.md) — Step 0 manifest, Gate A before long Approach prose, Approach remains **outline + questions** until partner-approved scope (v0.1), **fees** only from sourced numbers or **TBD**, no invented credentials or disclaimers.

---

## Attach in Cursor (minimum)

1. **This file** (`lop-deck-orchestrator.md`).
2. **Step 0** — [`step0-source-manifest.md`](./step0-source-manifest.md) content **filled** for this pursuit, or paste the manifest table from `lop-build-tracker.md` with **Y** rows only.
3. **Sources** — ` @ ` every **Y** file from the manifest (RFP, partner notes, CST, gold LoPs, market clips, approved boilerplate from `01. Background material/` or pursuit `inputs/`).
4. **Gold tone** — ` @ ` **1–3** proposals or excerpts under **`01. Background material/`** (or equivalent) for slide patterns and wording only.
5. **Workplan (optional but recommended)** — ` @ ` [`../../Sjors/prompts/workplan-from-intake.md`](../../Sjors/prompts/workplan-from-intake.md) **and** the dashboard **JSON** if the engagement workplan is in scope; otherwise state **Workplan: TBD** with questions.

**Optional:** ` @ ` individual chapter stubs below if you want the model to quote task wording verbatim; otherwise follow their intent from this orchestrator.

---

## Chapter stubs (intent reference)

| Stub | Use for |
|------|--------|
| [`intake-synthesis.md`](./intake-synthesis.md) | Problem statement / Gate A framing (already done before full deck, or refresh here) |
| [`chapter-context-objectives.md`](./chapter-context-objectives.md) | Context & objectives |
| [`chapter-why-mckinsey.md`](./chapter-why-mckinsey.md) | Why McKinsey — evidence-bound |
| [`chapter-timeline-team.md`](./chapter-timeline-team.md) | Timeline and team |
| [`chapter-team-shortlist.md`](./chapter-team-shortlist.md) | Team narrative / shortlist |
| [`chapter-credentials.md`](./chapter-credentials.md) | Credentials |
| [`chapter-market-trends.md`](./chapter-market-trends.md) | Market trends |
| [`chapter-approach-outline.md`](./chapter-approach-outline.md) | Approach (“solution”) — outline + questions only until approved |
| [`chapter-fees.md`](./chapter-fees.md) | Fees |
| [`chapter-appendix-references.md`](./chapter-appendix-references.md) | Appendix, references, Team CVs checklist |

---

## Deck order (strict)

Emit content **in this order**. Each item = **one slide** (or one HTML `section`) unless you split for density (McKinsey: do not overcrowd; prefer an extra slide).

1. **Cover** — Client-facing title (declarative where appropriate), subtitle/context line, date placeholder, confidentiality line only from **approved** boilerplate in sources.
2. **Problem statement** — One-page Gate A style: situation, complication, resolution path, assumptions (sourced vs needs confirmation), numbered questions, opposing inputs flagged. Align with [`intake-synthesis.md`](./intake-synthesis.md).
3. **Context & objectives** — [`chapter-context-objectives.md`](./chapter-context-objectives.md).
4. **Why McKinsey** — [`chapter-why-mckinsey.md`](./chapter-why-mckinsey.md).
5. **Timeline and team** — [`chapter-timeline-team.md`](./chapter-timeline-team.md).
6. **Team** — [`chapter-team-shortlist.md`](./chapter-team-shortlist.md).
7. **Credentials** — [`chapter-credentials.md`](./chapter-credentials.md).
8. **Market trends** — [`chapter-market-trends.md`](./chapter-market-trends.md).
9. **Approach** (“solution”) — [`chapter-approach-outline.md`](./chapter-approach-outline.md).
10. **Fees** — [`chapter-fees.md`](./chapter-fees.md).
11. **Workplan** — If JSON + workplan prompt attached: output **A–D** (end-deliverables, workstreams with %, week grid, risks/questions) per [`../../Sjors/prompts/workplan-from-intake.md`](../../Sjors/prompts/workplan-from-intake.md). If not in scope: short **TBD** slide + questions.
12. **Appendix / references / Team CVs** — [`chapter-appendix-references.md`](./chapter-appendix-references.md) — merge pass; **no new facts**.

After **each** numbered segment above, output one line: **`Sources used:`** manifest row #s (and note if inference).

---

## Output format (two blocks)

### Block A — PPT-oriented pack

Ordered list. For each slide: **`Title`** (declarative action title), **`Bullets`**, optional **`Notes`**.

### Block B — HTML paste pack

For each slide, emit a fragment the user can paste into the matching **`<article class="page">`** in `Sjors/html-decks/workplan-dashboard.html` (replace the slide’s **`.action-title`**, **`.slide-body`** / inner lists, and **`.slide-source`** where present):

- **Targets:** `#page-cover`, `#page-problem`, `#page-context`, `#page-why`, `#page-timeline`, `#page-team`, `#page-credentials`, `#page-market`, `#page-approach`, `#page-fees`, workplan slides `#page-deliverables` / `#page-workstreams` / `#page-weekly`, `#page-appendix` (`data-page` attributes mirror these).
- Inside each fragment: **`<h2 class="action-title">`**, **`<div class="slide-body">`**, **`<p class="slide-source">Source: …</p>`** where data appears (use manifest labels; no invented URLs in footers).

---

## Guardrails (repeat)

- No **new** client facts, fees, win rates, or legal/disclaimer text not in **Y** sources.
- Label **inferred** vs **stated** content.
- **“Solution”** language lives under **Approach**; keep MECE and pyramid structure throughout.

After human passes **Gate B** and optional **lop-coach**, use [`assembler-ppt-html.md`](./assembler-ppt-html.md) for final packaging if the team wants a clean v0.1 handoff.
