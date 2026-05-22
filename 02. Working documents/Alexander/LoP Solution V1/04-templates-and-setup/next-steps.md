# Next steps — start a pursuit from `Alexander/`

When you are ready to move beyond this scaffold, create a pursuit folder and pick **one** skeleton.

## 1. Choose a skeleton

| Option | Copy from | Notes |
|--------|-----------|--------|
| **Fleur (default in AGENTS.md)** | [`../../../Fleur/pursuits/_template-lop-pursuit/`](../../../Fleur/pursuits/_template-lop-pursuit/) | Staged folders: `01-information-gathering` … `05-delivered`. See template [`README.md`](../../../Fleur/pursuits/_template-lop-pursuit/README.md). |
| **Jasper alternate** | [`../../../Jasper/templates/lop-pursuit-template/`](../../../Jasper/templates/lop-pursuit-template/) | Do not mix two skeletons in one pursuit without intent. |

Copy the chosen folder to:

**`pursuits/<Client-Topic>/`** — create `pursuits/` under this `Alexander/` folder if it does not exist.

## 2. Add the tracker

1. Copy [**`../../../Fleur/lop-build-tracker.template.md`**](../../../Fleur/lop-build-tracker.template.md) into `pursuits/<Client-Topic>/`.  
2. Rename to **`lop-build-tracker.md`**.  
3. Fill client/pursuit name, dates, roles, Step 0 manifest, pipeline status, and context spine table.

## 3. Run Step 0

Complete the **Step 0 — Source manifest** in `lop-build-tracker.md` with **Y** only for sources that apply to this pursuit.

Use **[`source-manifest.template.md`](source-manifest.template.md)** as a reminder; the full table lives in the tracker.

## 4. Follow the Cursor runbook

Work through [**`../../../Jasper/lop-cursor-runbook.md`**](../../../Jasper/lop-cursor-runbook.md) — attach sources via `@` matching your manifest rows.

## HITL gates (orchestrator checkpoints)

| Gate | Purpose |
|------|---------|
| **A** | Problem statement + assumptions agreed; opposing inputs resolved or branched. |
| **B** | Integrated draft direction OK; gaps owned or cut. |
| **C** | Final sign-off before send. |

Record status in **`lop-build-tracker.md`** as you pass each gate.

## Outputs (v0.1)

Per runbook: produce **PPT-oriented** structure and **HTML-oriented** parallel for comparison.

## After the pursuit exists

Follow **[`../02-operating-playbook/playbook-from-sketch.md`](../02-operating-playbook/playbook-from-sketch.md)** in Cursor (no code required).

## Pia / Python (only if the squad adopts it)

Optional automation lives under [`../../../Pia`](../../../Pia). See [`../../../Fleur/README.md`](../../../Fleur/README.md) for corpus and export env vars — not part of the default MD-first path.
