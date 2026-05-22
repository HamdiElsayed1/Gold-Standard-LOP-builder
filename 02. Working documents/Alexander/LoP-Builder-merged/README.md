# LoP Builder — merged copy (Alexander + Hamdi)

**Updated:** 2026-05-15  
**Last refreshed from Hamdi:** 2026-05-15 — full sync of `Hamdi/src` → `LoP-Builder-merged/src` and `Hamdi/agents` → `LoP-Builder-merged/agents` (excludes Hamdi’s `src/.env`, `.venv`, `__pycache__`). Includes all seven agent specs (e.g. `lop-quality-eval-agent.md` for **Evals**).

This folder is a **working copy of the latest Hamdi application** placed under your personal workspace, set up so you keep **your workflow** (personal API keys, logs here) while staying aligned with **Hamdi’s codebase**.

## What was merged (“best of both”)

| Source | What it contributes |
|--------|---------------------|
| **Hamdi** (`02. Working documents/Hamdi/`) | **Canonical app code** — `src/*.py`, `agents/*.md`, `requirements.txt`, `.env.example`, and Hamdi’s `.gitignore`. Snapshot taken from Hamdi on the date above (files match `Hamdi/src` and `Hamdi/agents`; Hamdi’s `src/.env` is **not** copied — secrets stay out of this tree). |
| **Your folder (Alexander)** | **Personal credentials** — the app loads keys from `02. Working documents/Alexander/api-keys.env` (or `Alexander/.env`) via the user-folder logic in `app.py` / `orchestrator.py`. **Do not** commit or share that file. Code walks up the path until it finds `02. Working documents`, so this works whether you run from `Hamdi/src` or from this merged `src` folder. |
| **`Application_backup/2026-05-08`** | Compared Line-by-line with current Hamdi: **same logical content** for `app.py`, `orchestrator.py`, and `test_api.py`; differences were **line endings (CRLF vs LF)** from OneDrive. The merged copy uses Hamdi’s files (UTF-8 / LF). |

## Layout

```
LoP-Builder-merged/
├── README.md           ← this file
├── .gitignore          ← from Hamdi (excludes venv, logs, etc.)
├── src/                ← Streamlit app + orchestrator + schemas + tests
├── agents/             ← agent markdown specs
└── runs/               ← run logs (created when you use the app from here)
```

## Run from this copy

1. Create a venv and install deps:

   ```bash
   cd "LoP-Builder-merged/src"
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Ensure your keys exist at:

   - `02. Working documents/Alexander/api-keys.env`

3. Start Streamlit:

   ```bash
   streamlit run app.py
   ```

Logs for sessions started from this app instance go to `LoP-Builder-merged/runs/`.

## Keeping in sync with Hamdi later

When Hamdi changes, refresh this tree by copying again from `Hamdi/src` and `Hamdi/agents` (excluding `.env`, `.venv`, `__pycache__`), or ask to redo a merge pass. Your `api-keys.env` stays in `Alexander/` and is not overwritten by that sync.
