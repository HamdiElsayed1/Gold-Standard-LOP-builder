# LoP prompt stubs (v0.1)

Copy the body of a file into Cursor **after** `@`-attaching the files listed in **Step 0** of your [`lop-build-tracker`](../../Fleur/lop-build-tracker.template.md) (copy into the pursuit as `lop-build-tracker.md`). Follow the main [`lop-cursor-runbook.md`](../lop-cursor-runbook.md).

**Full deck in one pass (optional):** [`lop-deck-orchestrator.md`](./lop-deck-orchestrator.md) — orchestrates cover → problem statement → full spine → workplan → appendix, with McKinsey formatting and manifest discipline; refine or paste HTML into the unified [`../../Sjors/html-decks/workplan-dashboard.html`](../../Sjors/html-decks/workplan-dashboard.html) rail.

Suggested order follows the **spine** (see `.cursor/rules/lop-builder-workflow.mdc`). Parallelize only when **Gate A** is done and chapters do not share unresolved dependencies.

| Step | File | Spine / role |
|------|------|----------------|
| — | [`lop-deck-orchestrator.md`](./lop-deck-orchestrator.md) | **Full LoP deck** — all chapters + workplan slot + HTML/PPT output spec |
| 0 | [`step0-source-manifest.md`](./step0-source-manifest.md) | Lock inputs for this LoP |
| 1 | [`intake-synthesis.md`](./intake-synthesis.md) | Problem statement + assumptions + questions → **Gate A** |
| 2 | [`chapter-context-objectives.md`](./chapter-context-objectives.md) | Context & objectives |
| 3 | [`chapter-why-mckinsey.md`](./chapter-why-mckinsey.md) | Why McKinsey (agent-first, evidence-bound) |
| 4 | [`chapter-timeline-team.md`](./chapter-timeline-team.md) | Timeline and team |
| 5 | [`chapter-team-shortlist.md`](./chapter-team-shortlist.md) | Team narrative + placeholders + shortlist |
| 6 | [`chapter-credentials.md`](./chapter-credentials.md) | Credentials |
| 7 | [`chapter-market-trends.md`](./chapter-market-trends.md) | Market trends |
| 8 | [`chapter-approach-outline.md`](./chapter-approach-outline.md) | Approach — outline / questions only (human-first v0.1) |
| 9 | [`chapter-fees.md`](./chapter-fees.md) | Fees — numbers only if sourced; else TBD |
| 10 | [`chapter-appendix-references.md`](./chapter-appendix-references.md) | Appendix, references, Team CVs checklist |
| — | [`lop-coach.md`](./lop-coach.md) | Critic pass (**after Gate B** — human direction OK; then apply only approved fixes) |
| — | [`assembler-ppt-html.md`](./assembler-ppt-html.md) | PPT + HTML handoff (**after** coach-approved revisions; **Gate C** signs packaged output) |

After each chapter: one line **Sources used:** manifest row #s.
