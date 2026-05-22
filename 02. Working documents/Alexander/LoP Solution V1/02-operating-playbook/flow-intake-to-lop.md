# Flow: intake → Background Material → LoP (Cursor)

This is the end-to-end path from **[`../../intake.html`](../../intake.html)** to a draft LoP using **approved inputs under the workspace Background Material tree** — without Python or servers.

## Why not “auto-read” from the browser?

A local `intake.html` file **cannot** scan `01. Background material` on your disk (browser security). **Cursor** can read whatever you `@`-attach from that folder. The flow below wires **human attach** → **assistant read** → **manifest + draft**.

## Prerequisites

- Pursuit folder (optional but recommended): see [`../04-templates-and-setup/next-steps.md`](../04-templates-and-setup/next-steps.md).
- `lop-build-tracker.md` in the pursuit (copy from [`../../../Fleur/lop-build-tracker.template.md`](../../../Fleur/lop-build-tracker.template.md)).

## Step 1 — Intake (browser)

1. Open **[`../../intake.html`](../../intake.html)** in your browser (double-click or open from Cursor).
2. Enter **client**, **topic**, and optionally **duration** and **team size**.
3. Click **Generate summary**, then **Copy to clipboard** → paste into `lop-build-tracker.md` (or keep for Step 3).

## Step 2 — Pick Background Material files (human)

### Optional — list files from disk (Python)

From a terminal, you can print a **manifest-hint table** (paths to `@` in Cursor) plus the same **tracker + kickoff** text as `intake.html`:

```bash
python3 "02. Working documents/Alexander/scripts/kickoff_from_intake.py" \
  --list-bg --max-files 400 \
  --kickoff --client "Your client" --topic "Your topic" \
  --duration "12 weeks" --team "4–6 FTE"
```

- `--list-bg` only → table of files under `01. Background material` (and `Background Material` if present).  
- `--kickoff` only → tracker block + Cursor kickoff (requires `--client` and `--topic`).  
- Stdlib only; paths are relative to the **`Gold Standard LOP Builder - Documents`** root.

You still **confirm Y** and **`@` attach** only what you want the model to use.

### Choose what to attach

In Finder / Explorer, identify what you will use from **`01. Background material`** (repo sibling of `02. Working documents`):

| Bucket (from runbook) | Typical sources |
|----------------------|------------------|
| Boilerplate / disclaimers | Only firm-approved snippets your squad stores here |
| Gold / prior LoP examples | Label competitive vs exploratory when you attach |
| Market / context | Public or approved internal clips — cite in draft |
| RFP / tender | If stored here or under pursuit `01-information-gathering/` |

Do **not** attach unrelated pursuits. If a file is not in scope for **this** client, leave it out.

## Step 3 — New Cursor chat

1. Open **[`../../../Jasper/lop-cursor-runbook.md`](../../../Jasper/lop-cursor-runbook.md)** for reference (or keep it split-screen).
2. Start a **new chat** (traceability; runbook default).
3. **Attach** (`@`):
   - [`../../intake.html`](../../intake.html) *or* paste the intake markdown block from Step 1.
   - Each chosen file under **`01. Background material`** (and pursuit inputs if applicable).
   - Optionally `@` [`cursor-kickoff-from-intake.md`](cursor-kickoff-from-intake.md) if you filled it manually instead of using the HTML **Copy Cursor kickoff** button.
4. Paste the **Cursor kickoff** message:
   - From **`intake.html`**: after Step 1, use **Copy Cursor kickoff**.
   - Or copy from [`cursor-kickoff-from-intake.md`](cursor-kickoff-from-intake.md) after replacing `{{CLIENT}}`, `{{TOPIC}}`, and optional lines.

## Step 4 — What the assistant should produce first

Per **[`../../../Jasper/lop-cursor-runbook.md`](../../../Jasper/lop-cursor-runbook.md)** and the kickoff **Phase 1 / Phase 2** split:

1. **Phase 1:** **Step 0 source manifest** only (every `@` attachment + intake) — assistant **stops** after the table.
2. You confirm **Y** rows (edit tracker; reply in chat with row numbers or “all Y except …”).
3. **Phase 2:** **Problem statement** + questions + **spine titles only** — from **Y** rows only; align style with [`../../../Jasper/prompts/intake-synthesis.md`](../../../Jasper/prompts/intake-synthesis.md) if you `@` that file.
4. **No long Approach body** until **Gate A** is explicitly OK’d; update `lop-build-tracker.md` Gate A row.

Optional stricter manifest formatting: `@` [`../../../Jasper/prompts/step0-source-manifest.md`](../../../Jasper/prompts/step0-source-manifest.md).

## Step 5 — After Gate A

Continue the same chat (or follow runbook): chapter passes using [`../../../Jasper/prompts/`](../../../Jasper/prompts/), then **LOP coach**, then **assembler** for PPT + HTML packs.

After each chapter the assistant should state **Sources used:** manifest row numbers.

## Step 6 — Outputs

Deliverables match v0.1 runbook: **PPT-oriented** structure **and** **HTML-oriented** parallel, disclaimers **only** from attached boilerplate — never invented.

## Quick link map

| Artifact | Path |
|----------|------|
| Intake form | [`../../intake.html`](../../intake.html) |
| Kickoff template (manual) | [`cursor-kickoff-from-intake.md`](cursor-kickoff-from-intake.md) |
| Playbook | [`playbook-from-sketch.md`](playbook-from-sketch.md) |
| Cursor runbook | [`../../../Jasper/lop-cursor-runbook.md`](../../../Jasper/lop-cursor-runbook.md) |
| Rules | [`../../../../.cursor/rules/lop-builder-core.mdc`](../../../../.cursor/rules/lop-builder-core.mdc) |
