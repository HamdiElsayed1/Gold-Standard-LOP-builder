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
import httpx
from openai import OpenAI


def _find_working_documents_dir() -> Path | None:
    """Walk upward until we find the folder named '02. Working documents'."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if parent.name == "02. Working documents":
            return parent
    return None


def _resolve_user_folder() -> Path | None:
    """Resolve the current user's folder under 02. Working documents."""
    working_docs = _find_working_documents_dir()
    if working_docs is None or not working_docs.exists():
        return None

    hints: list[str] = []
    for raw in (
        os.environ.get("LOP_USER_FOLDER"),
        os.environ.get("LOP_USER"),
        os.environ.get("USERNAME"),
        os.environ.get("USER"),
        Path.home().name,
    ):
        if not raw:
            continue
        cleaned = raw.strip()
        if not cleaned:
            continue
        hints.append(cleaned)
        if "_" in cleaned:
            hints.append(cleaned.split("_", 1)[0])

    deduped_hints = list(dict.fromkeys(hints))
    subdirs = [d for d in working_docs.iterdir() if d.is_dir()]
    by_lower = {d.name.lower(): d for d in subdirs}

    for hint in deduped_hints:
        direct = by_lower.get(hint.lower())
        if direct:
            return direct
        for d in subdirs:
            d_lower = d.name.lower()
            h_lower = hint.lower()
            if d_lower.startswith(h_lower) or h_lower.startswith(d_lower):
                return d
    return None


def _load_user_env() -> Path | None:
    """Load API keys from the user's own folder."""
    user_folder = _resolve_user_folder()
    if not user_folder:
        return None
    for name in ("api-keys.env", ".env"):
        env_path = user_folder / name
        if env_path.exists():
            load_dotenv(env_path, override=True)
            return env_path
    return None


_ENV_SOURCE = _load_user_env()

# ─── CONFIG ───────────────────────────────────────────────────────────────────

AGENT_DIR = Path(__file__).parent.parent / "agents"
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
MAX_COMPLETION_TOKENS = 16_000

_clients: dict[bool, OpenAI] = {}


def _get_client(use_system_proxy: bool) -> OpenAI:
    if use_system_proxy not in _clients:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. "
                "Create 02. Working documents/<YourName>/api-keys.env with your key."
            )
        kwargs: dict = {"api_key": api_key}
        base_url = os.environ.get("OPENAI_BASE_URL")
        if base_url:
            kwargs["base_url"] = base_url
        kwargs["http_client"] = httpx.Client(trust_env=use_system_proxy, timeout=120.0)
        _clients[use_system_proxy] = OpenAI(**kwargs)
    return _clients[use_system_proxy]


def _root_exc_text(exc: Exception) -> str:
    """Return the deepest available exception detail."""
    cur: BaseException = exc
    while getattr(cur, "__cause__", None) or getattr(cur, "__context__", None):
        nxt = getattr(cur, "__cause__", None) or getattr(cur, "__context__", None)
        if nxt is None:
            break
        cur = nxt
    return f"{cur.__class__.__name__}: {cur}"


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
) -> dict:
    """
    Load agent spec, call OpenAI, return the parsed JSON response as a dict.

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
    """
    spec = load_agent_spec(agent_name)
    system_prompt = spec["system_prompt"]
    output_schema = spec["output_schema"]

    schema_instruction = (
        "\n\n---\nReturn ONLY a valid JSON object. "
        "Do not include any text, explanation, or markdown outside the JSON. "
        f"Your response must match this structure exactly:\n"
        f"```json\n{json.dumps(output_schema, indent=2)}\n```"
    )

    content = _build_content(user_message + schema_instruction, files)

    prefer_system_proxy = os.environ.get("LOP_USE_SYSTEM_PROXY", "").lower() in {
        "1", "true", "yes",
    }
    modes = [prefer_system_proxy, not prefer_system_proxy]
    last_exc: Exception | None = None
    failures: list[str] = []
    response = None

    for mode in modes:
        try:
            response = _get_client(mode).chat.completions.create(
                model=MODEL,
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": content},
                ],
            )
            break
        except Exception as exc:
            last_exc = exc
            mode_label = "system-proxy" if mode else "direct"
            failures.append(f"{mode_label}={_root_exc_text(exc)}")

    if response is None:
        assert last_exc is not None
        raise RuntimeError(
            "OpenAI request failed with both network modes "
            f"(with and without system proxy): {'; '.join(failures)}"
        ) from last_exc

    text = response.choices[0].message.content or ""
    return _extract_json(text)
