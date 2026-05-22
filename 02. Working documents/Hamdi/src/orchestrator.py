"""
Orchestrator — thin runner that loads agent specs from markdown files and
calls the OpenAI API. No LangChain, no framework overhead.

Agent intelligence lives in Hamdi/agents/*.md.
Python here is just file I/O + API calls + JSON parsing.

PDF note: PDFs are passed natively to OpenAI as base64-encoded file content
blocks (type: "file"). No text extraction is needed.
"""

import base64
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent / ".env")

# ─── CONFIG ───────────────────────────────────────────────────────────────────

AGENT_DIR = Path(__file__).parent.parent / "agents"
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
MAX_COMPLETION_TOKENS = 16_000

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. "
                "Copy src/.env.example to src/.env and add your key."
            )
        kwargs: dict = {"api_key": api_key}
        base_url = os.environ.get("OPENAI_BASE_URL")
        if base_url:
            kwargs["base_url"] = base_url
        _client = OpenAI(**kwargs)
    return _client


# ─── SPEC LOADING ─────────────────────────────────────────────────────────────

def load_agent_spec(agent_name: str) -> dict:
    """
    Parse agents/<agent_name>.md and return:
      {
        "system_prompt": str,   # full text under ## System Prompt
        "output_schema": dict,  # parsed JSON from ## Output Schema code block
      }
    """
    spec_path = AGENT_DIR / f"{agent_name}.md"
    if not spec_path.exists():
        raise FileNotFoundError(
            f"Agent spec not found: {spec_path}\n"
            f"Expected one of: {list(AGENT_DIR.glob('*.md'))}"
        )

    text = spec_path.read_text(encoding="utf-8")

    sections: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_key is not None:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = line[3:].strip().lower()
            current_lines = []
        else:
            if current_key is not None:
                current_lines.append(line)

    if current_key is not None:
        sections[current_key] = "\n".join(current_lines).strip()

    system_prompt = sections.get("system prompt", "").strip()
    if not system_prompt:
        raise ValueError(f"No '## System Prompt' section found in {spec_path}")

    schema_text = sections.get("output schema", "")
    json_match = re.search(r"```json\s*(.*?)\s*```", schema_text, re.DOTALL)
    output_schema: dict = {}
    if json_match:
        try:
            output_schema = json.loads(json_match.group(1))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Could not parse output schema JSON in {spec_path}: {exc}"
            )

    return {"system_prompt": system_prompt, "output_schema": output_schema}


# ─── CONTENT BUILDER ──────────────────────────────────────────────────────────

def _build_content(user_message: str, files: list[dict] | None = None) -> list[dict]:
    """
    Build the OpenAI content array for the user turn.

    PDFs are passed as native base64 file blocks so OpenAI reads them directly.
    DOCX / TXT are already converted to plain text by app.py and included as
    text blocks.

    Each entry in `files` is a dict with:
      filename  : str
      doc_type  : str   (RFP | RFI | Best Practice LoP)
      is_pdf    : bool
      bytes     : bytes (populated when is_pdf=True)
      text      : str   (populated when is_pdf=False)
    """
    content: list[dict] = []

    if files:
        for f in files:
            if f.get("is_pdf"):
                b64 = base64.b64encode(f["bytes"]).decode("utf-8")
                content.append(
                    {
                        "type": "text",
                        "text": (
                            f"[Document: {f.get('filename', 'unknown')} | "
                            f"Type: {f.get('doc_type', 'unknown')}]"
                        ),
                    }
                )
                content.append(
                    {
                        "type": "file",
                        "file": {
                            "filename": f.get("filename", "document.pdf"),
                            "file_data": f"data:application/pdf;base64,{b64}",
                        },
                    }
                )
            else:
                content.append(
                    {
                        "type": "text",
                        "text": (
                            f"[Document: {f.get('filename', 'unknown')} | "
                            f"Type: {f.get('doc_type', 'unknown')}]\n\n"
                            f"{f['text']}"
                        ),
                    }
                )

    content.append({"type": "text", "text": user_message})
    return content


# ─── RESPONSE PARSING ─────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """
    Try three strategies to extract a JSON object from the response text:
    1. The whole text parsed directly (expected path when JSON mode is on)
    2. ```json ... ``` fenced block
    3. First {...} block found by regex (greedy — outermost braces)
    """
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    fence = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass

    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not extract JSON from agent response. "
        f"First 500 chars:\n{text[:500]}"
    )


# ─── MAIN ENTRY POINTS ────────────────────────────────────────────────────────

def run_agent(
    agent_name: str,
    user_message: str,
    files: list[dict] | None = None,
    use_extended_thinking: bool = True,  # kept for API compatibility; not used by OpenAI
    model: str | None = None,
) -> dict:
    """
    Load agent spec, dispatch to the right provider (OpenAI or Anthropic
    based on the model identifier), and return the parsed JSON response as
    a dict.

    Provider routing
    ----------------
    Model identifiers starting with `claude-` are sent to the Anthropic
    wrapper in `llm_anthropic.run_anthropic_agent`, which talks to
    `ANTHROPIC_BASE_URL` from `.env`. Everything else (including the empty
    / None case, which falls back to the OpenAI default) goes through the
    OpenAI `chat.completions` path below. Callers do not need to know
    which provider they hit — the JSON return shape is identical.

    Parameters
    ----------
    agent_name : str
        Matches the filename under agents/ without the .md suffix.
    user_message : str
        Task instruction or context passed as the user turn.
    files : list[dict] | None
        Uploaded documents (only needed for intake-agent).
    use_extended_thinking : bool
        Ignored — kept for call-site compatibility with original Anthropic version.
    model : str | None
        Optional override for the model identifier. When None, falls back
        to the module-level `MODEL` (sourced from `OPENAI_MODEL` env var).
        Used by the per-step model selectors in the Streamlit UI to pick
        faster / higher-capability / Claude tracks per agent.
    """
    spec = load_agent_spec(agent_name)
    system_prompt = spec["system_prompt"]
    output_schema = spec["output_schema"]

    chosen_model = (model or MODEL).strip()

    if chosen_model.startswith("claude-"):
        # Local import keeps the Anthropic SDK optional at module load —
        # users who only run the OpenAI track do not need it installed.
        from llm_anthropic import run_anthropic_agent

        return run_anthropic_agent(
            system_prompt=system_prompt,
            user_message=user_message,
            files=files,
            output_schema=output_schema,
            model=chosen_model,
        )

    schema_instruction = (
        "\n\n---\nReturn ONLY a valid JSON object. "
        "Do not include any text, explanation, or markdown outside the JSON. "
        f"Your response must match this structure exactly:\n"
        f"```json\n{json.dumps(output_schema, indent=2)}\n```"
    )

    content = _build_content(user_message + schema_instruction, files)

    response = _get_client().chat.completions.create(
        model=chosen_model,
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": content},
        ],
    )

    text = response.choices[0].message.content or ""
    return _extract_json(text)
