# Alexander — LoP workspace

Personal working folder for Letter of Proposal (LoP) work with Cursor. **Start from the sketch**, then follow Markdown instructions in **`LoP Solution V1/`** — no Python required unless the squad later adopts Pia automation.

## Start here (sketch → execution)

| Step | Where |
|------|--------|
| 1 | Visual sketch: [`../Workflow.jpeg`](../Workflow.jpeg) |
| 2 | Mirror + anchors: [`LoP Solution V1/01-workflow-and-sketch/workflow-from-sketch.md`](LoP%20Solution%20V1/01-workflow-and-sketch/workflow-from-sketch.md) |
| 3 | **Operating playbook (MD only):** [`LoP Solution V1/02-operating-playbook/playbook-from-sketch.md`](LoP%20Solution%20V1/02-operating-playbook/playbook-from-sketch.md) |
| 4 | **Intake form (HTML):** [`intake.html`](intake.html) — client, topic, optional fields + **Cursor kickoff** for Background Material |
| 5 | **Intake → LoP flow:** [`LoP Solution V1/02-operating-playbook/flow-intake-to-lop.md`](LoP%20Solution%20V1/02-operating-playbook/flow-intake-to-lop.md) |
| 6 | Step 0 stub: [`LoP Solution V1/04-templates-and-setup/source-manifest.template.md`](LoP%20Solution%20V1/04-templates-and-setup/source-manifest.template.md) |
| 7 | First pursuit folder: [`LoP Solution V1/04-templates-and-setup/next-steps.md`](LoP%20Solution%20V1/04-templates-and-setup/next-steps.md) |

**V1 index (all instruction MDs):** [`LoP Solution V1/README.md`](LoP%20Solution%20V1/README.md). Legacy `instructions/README.md` redirects there.

## Where everything lives

| What | Where |
|------|--------|
| Sketch | [`../Workflow.jpeg`](../Workflow.jpeg) |
| Markdown mirror | [`LoP Solution V1/01-workflow-and-sketch/workflow-from-sketch.md`](LoP%20Solution%20V1/01-workflow-and-sketch/workflow-from-sketch.md) |
| Playbook (how to run the agent in Cursor) | [`LoP Solution V1/02-operating-playbook/playbook-from-sketch.md`](LoP%20Solution%20V1/02-operating-playbook/playbook-from-sketch.md) |
| Browser intake + kickoff | [`intake.html`](intake.html) |
| Intake → LoP (Background Material) | [`LoP Solution V1/02-operating-playbook/flow-intake-to-lop.md`](LoP%20Solution%20V1/02-operating-playbook/flow-intake-to-lop.md) |
| Formatting spec + HTML preview | [`LoP Solution V1/03-formatting-spec/`](LoP%20Solution%20V1/03-formatting-spec/) |
| Python helper (optional) | [`scripts/README.md`](scripts/README.md) — list BG files + print kickoff from CLI |
| Step 0 manifest stub | [`LoP Solution V1/04-templates-and-setup/source-manifest.template.md`](LoP%20Solution%20V1/04-templates-and-setup/source-manifest.template.md) |
| Pursuit setup | [`LoP Solution V1/04-templates-and-setup/next-steps.md`](LoP%20Solution%20V1/04-templates-and-setup/next-steps.md) |
| Pursuit folders | [`pursuits/README.md`](pursuits/README.md) |

## Project anchors (read-only references)

Do not edit teammates’ folders under `02. Working documents/` unless asked — see [`../../.cursor/rules/lop-builder-peer-folders.mdc`](../../.cursor/rules/lop-builder-peer-folders.mdc).

| Anchor | Path |
|--------|------|
| Core persona / risks | [`../../.cursor/rules/lop-builder-core.mdc`](../../.cursor/rules/lop-builder-core.mdc) |
| Chapter spine & cadence | [`../../.cursor/rules/lop-builder-workflow.mdc`](../../.cursor/rules/lop-builder-workflow.mdc) |
| Tools & data sources | [`../../.cursor/rules/lop-builder-tools-data.mdc`](../../.cursor/rules/lop-builder-tools-data.mdc) |
| Cursor runbook (gates A/B/C, PPT + HTML) | [`../Jasper/lop-cursor-runbook.md`](../Jasper/lop-cursor-runbook.md) |
| Prompts | [`../Jasper/prompts/README.md`](../Jasper/prompts/README.md) |
| Full tracker template | [`../Fleur/lop-build-tracker.template.md`](../Fleur/lop-build-tracker.template.md) |
| Project overview | [`../../AGENTS.md`](../../AGENTS.md) |

## v0.1 non-goals

- No assumed connectors (Know, MVI, email, voice) unless you configure them.
- No invented client facts, fees, credentials, or legal disclaimers — only approved boilerplate from `Background Material/` or pursuit inputs.

## Python (optional)

- **`Alexander/scripts/`** — small stdlib CLI to **list** `01. Background material` paths and print **kickoff** text (see [scripts/README.md](scripts/README.md)). Use when a filesystem listing is faster than manual picking.
- **Pia `lop-workflow`** under [`../Pia`](../Pia) — separate automation path; not required for the Cursor + MD flow.
