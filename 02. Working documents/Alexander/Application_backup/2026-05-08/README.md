# Application Backup — 2026-05-08

This folder is a dated backup of the core LoP app from `Hamdi`.

## Structure

- `src/` — Streamlit app runtime files
- `agents/` — agent prompt/spec files used by the orchestrator

## What is included

### `src/`
- `app.py` — main Streamlit UI and workflow steps
- `orchestrator.py` — OpenAI call orchestration + response parsing
- `run_logger.py` — run/event logging helpers
- `schemas.py` — Pydantic data models
- `mock_answers.py` — mock partner answer generation
- `test_api.py` — API connectivity smoke test
- `requirements.txt` — Python dependencies
- `.env.example` — environment variable template
- `README.md` — original app setup/run guide

### `agents/`
- `intake-agent.md`
- `context-agent.md`
- `synthesis-agent.md`
- `mock-partner-agent.md`
- `validation-agent.md`
- `dot-dash-agent.md`

## How to run from this backup

1. Create and activate a virtual env.
2. Install dependencies from `src/requirements.txt`.
3. Ensure your personal API key file exists at:
   - `02. Working documents/<YourName>/api-keys.env`
4. Start:

```bash
streamlit run src/app.py
```

## Notes
- This is a point-in-time snapshot for recovery/reference.
- Keep personal API keys outside this backup folder.
