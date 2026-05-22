# Engagement workplan — generate from intake

Use in **Cursor** with:

1. **`@02. Working documents/Sjors/prompts/workplan-from-intake.md`** (this file).
2. **JSON from the dashboard** [`../html-decks/workplan-dashboard.html`](../html-decks/workplan-dashboard.html) — use **Copy JSON** (includes `intake.uploadedContextFiles` when you used **Choose files**).
3. **Gold tone / structure:** attach **1–3** proposals from **`@01. Background material/`** (PDF or PPTX). Use them for **how sections are framed and worded**, not for facts from a different client. If you cannot attach files, paste **slide titles** from the workplan part of a gold proposal.
4. **Related context:** Use `intake.uploadedContextFiles` — **text** files may include `textContent` read in the browser; **binary** entries only have `note` (user should **`@`** the real file in Cursor). Also honor `intake.relatedContextDocuments` (extra paths). **`@`** attach gold proposals from `01. Background material/` when drafting tone.

## Intake block

Paste the JSON in a fenced `json` block below (replace this line).

## Instructions for the model

You are drafting an **engagement-level** workplan (client project), **not** the internal LOP-builder program.

1. Read all keys in `intake` (including optional `softStartWeek1`, `steercoEveryWeeks`, `firstSteercoWeek`, **`relatedContextDocuments`**, **`uploadedContextFiles`**, and optional LoP scaffolds **`gateAProblemDraft`** (legacy key: optional **slide notes** from the dashboard), **`whyMcKinseyNotes`**, **`approachOutlineNotes`** — use the latter only where they help sections A–D; they do not replace manifest-backed facts).
2. For each **`uploadedContextFiles`** entry: if `textContent` is present, you may quote it; if only `note` (binary / too large), ask the user to **`@`** the original file for detail.
3. Echo **Background material** style only where the user attached files — stay factual to **this** intake.

### A. End-deliverables

- 5–8 bullets; each = **deliverable title** + **definition of done** (one clause).
- Align language with **scope** / **topic**; use **TBD** where unsupported.

### B. Workstreams (strict format)

- **3–5 substantive streams** (not “Prep” or “Readout” as standalone streams).
- For **each** stream output **all** of: **Name** | **Objective** (one sentence) | **% of team capacity** (approximate; **sum ≈ 100%** across streams, note remainder if PM/overhead) | **Dependencies** | **Definition of done**.
- Embed **kickoff / mobilization** and **readout / final materials** inside stream objectives or week cells — do not spin them off as separate workstreams.

### C. Week-by-week plan

- Markdown table with **Week 1 … Week N** (`N` = `durationWeeks`).
- **First data row = “Milestones”`** (or merged label): mark **Week 1** as **Soft start** when `softStartWeek1` is true (default treat as true if missing). Mark **Steerco / workshop** in weeks per **`steercoEveryWeeks`** starting **`firstSteercoWeek`** (defaults: every **2** weeks from week **2**, e.g. 2,4,6). Final week(s): **Readout prep / final readout** as appropriate. Use **TBD** if cadence unknown.
- **Following rows** = same workstreams as section B. Cells = **2–4 bullets** each (activities + micro-deliverables). Reflect soft start in **Week 1** cells (interviews, data, alignment).

### D. Risks and open questions

- Short bullets; end with **1–3 numbered clarifying questions** if needed.

## Guardrails

- No invented **fees**, **client metrics**, or **confidential** details from gold files.
- No **named** owners unless in intake.

## After the model responds

- Partner **review** before client use.
- Optionally merge into `workplan-dashboard.html` or a pursuit markdown file under `Sjors/`.
