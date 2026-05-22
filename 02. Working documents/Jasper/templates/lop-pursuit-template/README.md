# LoP pursuit folder template

**Copy this entire folder** for each new pursuit, then rename the copy (for example `LoP-ClientName-ShortTopic`). Work inside the copy only.

**Start here**

1. Fill placeholders in `lop-build-tracker.md` (title, dates, roles).
2. Drop source material into `inputs/` (`01_RFP`, `02_Partner_inputs`, etc.—see `inputs/README.md`).
3. Keep drafts and coach output under `working/`; put signed-off deliverables under `output/final/` (use dated subfolders or `v0.x` as your squad prefers).

**Sensitivity:** This tree may hold client-confidential and commercial material. Follow firm rules on storage, sharing, and retention.

**If you use the Pia CLI** (`lop_workflow`): the library defaults still point at workspace `Background Material` and `02. Working documents/Fleur/exports` in code—**override them** when you work from Jasper so outputs land under your pursuit or under `Jasper/`, for example:

- `LOP_BACKGROUND_MATERIAL_DIR` → absolute path to this pursuit’s `inputs` folder (or a merged corpus subfolder you maintain).
- `LOP_EXPORT_DIR` → absolute path to this pursuit’s `output/scratch` (or `output/final` when appropriate), or e.g. `02. Working documents/Jasper/exports`.

Adjust paths to your machine; restart the shell after changing env vars.

**Tracker:** Use the bundled `lop-build-tracker.md` in this template. An older copy of the same table may exist under another teammate’s folder for history only—not the default working location.
