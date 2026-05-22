"""
Anthropic Claude wrapper — mirrors the call-shape of `orchestrator.run_agent`
so the orchestrator can dispatch to either provider behind a single entry
point.

Reuses `ANTHROPIC_BASE_URL` / `ANTHROPIC_API_KEY` from `src/.env` (already
loaded by `orchestrator` at import time). The McKinsey / QuantumBlack
gateway exposes the Anthropic native API on a separate prefix from OpenAI,
so this module talks to the official `anthropic` SDK rather than reusing
the OpenAI client.

Two key translations from the OpenAI shape:

  1. JSON output. Anthropic has no `response_format={"type": "json_object"}`.
     We coerce JSON via tool-use: declare a single `emit_result` tool whose
     `input_schema` mirrors the agent's `output_schema`, force
     `tool_choice={"type": "tool", "name": "emit_result"}`, and read the
     `tool_use.input` block. If the gateway / model does not return a
     tool_use block (rare, e.g. when the schema is rejected), fall back to
     parsing the assistant text via `orchestrator._extract_json`.

  2. Native PDF. OpenAI takes `{"type": "file", "file": {...}}`. Anthropic
     takes `{"type": "document", "source": {"type": "base64",
     "media_type": "application/pdf", "data": "<b64>"}}`. We translate the
     same `files` list-of-dicts shape that `app.py` already builds.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any

# Local import — avoids a circular import at module load by re-using the
# extractor only when we need it inside the function.
from orchestrator import _extract_json

try:
    import anthropic
except ImportError as exc:  # pragma: no cover — surfaced at first call
    anthropic = None  # type: ignore[assignment]
    _IMPORT_ERROR: Exception | None = exc
else:
    _IMPORT_ERROR = None


# Match the OpenAI cap so prompts that fit on one provider fit on the other.
MAX_COMPLETION_TOKENS = 16_000

# Name of the synthetic tool we use to coerce JSON output. Kept stable so
# the model can be told (in the system prompt extension) to call it.
_EMIT_TOOL_NAME = "emit_result"

_client: Any = None


def _get_anthropic_client() -> Any:
    """
    Return a singleton `anthropic.Anthropic` client wired to the McKinsey
    gateway. Raises a friendly, env-var-named error when the SDK is missing
    or the JWT is unset.
    """
    global _client
    if _client is not None:
        return _client

    if anthropic is None:
        raise EnvironmentError(
            "The `anthropic` package is not installed. "
            "Run `pip install -r requirements.txt` to add it."
        ) from _IMPORT_ERROR

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. Refresh the McKinsey JWT and "
            "paste it into src/.env (the same JWT works for "
            "OPENAI_API_KEY and ANTHROPIC_API_KEY)."
        )

    kwargs: dict = {"api_key": api_key}
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url

    _client = anthropic.Anthropic(**kwargs)
    return _client


def _build_anthropic_content(
    user_message: str,
    files: list[dict] | None = None,
) -> list[dict]:
    """
    Translate the same `files` list-of-dicts shape `app.py` builds for the
    OpenAI path into Anthropic-native content blocks.

    Each entry in `files` is a dict with:
      filename  : str
      doc_type  : str   (RFP | RFI | Best Practice LoP | …)
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
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": b64,
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


def _infer_property_schema(example_value: Any) -> dict:
    """
    Infer a permissive JSON Schema fragment from a single example value
    drawn from an agent spec's example dict.

    We do NOT enforce strictness — descriptions and `required` lists are
    omitted on purpose; the goal is only to give Claude enough type
    information at each property that its tool-use coercion does not
    fall back to wrapping the whole payload as a JSON string under a
    synthetic `input` key (the failure mode observed when properties
    were declared as bare `{}` schemas).

    Recurses one level into objects so nested fields like
    `question_list -> questions[]` get their array type declared too.
    """
    if isinstance(example_value, bool):
        return {"type": "boolean"}
    if isinstance(example_value, int):
        return {"type": "integer"}
    if isinstance(example_value, float):
        return {"type": "number"}
    if isinstance(example_value, str):
        return {"type": "string"}
    if example_value is None:
        # JSON Schema does not have a strict "any" — allow any type.
        return {"type": ["string", "number", "boolean", "object", "array", "null"]}
    if isinstance(example_value, list):
        item_schema: dict
        if not example_value:
            item_schema = {}
        else:
            # Use the first item as the items schema. Permissive — does
            # not require homogeneity.
            item_schema = _infer_property_schema(example_value[0])
        return {"type": "array", "items": item_schema}
    if isinstance(example_value, dict):
        nested_props = {
            str(k): _infer_property_schema(v) for k, v in example_value.items()
        }
        return {
            "type": "object",
            "properties": nested_props,
            "additionalProperties": True,
        }
    # Unknown type — allow anything.
    return {"type": ["string", "number", "boolean", "object", "array", "null"]}


def _coerce_schema_for_tool(output_schema: dict) -> dict:
    """
    Anthropic's tool-use `input_schema` must be a JSON Schema object
    starting with `{"type": "object", ...}`. The agent specs in
    `agents/*.md` store output schemas as plain example dicts (the
    OpenAI path stringifies them and asks the model to mimic the shape).

    To make the example usable as a robust tool schema we infer the type
    of every top-level property from its example value (recursing one
    level for nested objects so arrays and sub-objects get declared
    too). Empty `{}` per property is unsafe — Claude observably falls
    back to wrapping the whole payload as a JSON string under a
    synthetic `input` key when properties carry no type information.

    If the spec already supplies a real JSON Schema (`type == "object"`
    plus `properties`), pass it through unchanged.
    """
    if not isinstance(output_schema, dict) or not output_schema:
        return {"type": "object", "properties": {}}

    if output_schema.get("type") == "object" and "properties" in output_schema:
        return output_schema

    properties: dict[str, dict] = {
        str(key): _infer_property_schema(value)
        for key, value in output_schema.items()
    }

    return {
        "type": "object",
        "properties": properties,
        "additionalProperties": True,
    }


def _unwrap_input_envelope(payload: dict) -> dict:
    """
    Defensively unwrap the failure mode where Claude returns
    `{"input": <real_payload>}` or `{"input": "<json string of real payload>"}`
    instead of the real payload directly. With well-typed `properties` in
    the tool's `input_schema` this should not happen, but we keep this
    belt-and-braces fallback so a single drift does not break the run.

    Only unwraps when:
      * the payload has exactly one top-level key, AND
      * that key is `input`, AND
      * the value is either a dict, or a string that parses as a JSON object.
    """
    if not isinstance(payload, dict):
        return payload
    if list(payload.keys()) != ["input"]:
        return payload

    inner = payload["input"]
    if isinstance(inner, dict):
        return inner
    if isinstance(inner, str):
        try:
            parsed_inner = json.loads(inner)
        except (json.JSONDecodeError, ValueError):
            return payload
        if isinstance(parsed_inner, dict):
            return parsed_inner
    return payload


def _extract_tool_use_input(message: Any) -> dict | None:
    """
    Walk `message.content` and return the `input` dict of the first
    `tool_use` block named `_EMIT_TOOL_NAME`. Returns None if no such
    block is present. Applies a defensive `_unwrap_input_envelope` so a
    single misbehaved response does not break the caller.
    """
    for block in getattr(message, "content", None) or []:
        if getattr(block, "type", None) != "tool_use":
            continue
        if getattr(block, "name", None) != _EMIT_TOOL_NAME:
            continue
        payload = getattr(block, "input", None)
        if isinstance(payload, dict):
            return _unwrap_input_envelope(payload)
    return None


def _collect_assistant_text(message: Any) -> str:
    """
    Concatenate every `text` block on the assistant message. Used as the
    fallback path when the model returns prose instead of a tool_use block.
    """
    parts: list[str] = []
    for block in getattr(message, "content", None) or []:
        if getattr(block, "type", None) != "text":
            continue
        text_value = getattr(block, "text", "") or ""
        if text_value:
            parts.append(text_value)
    return "".join(parts).strip()


def run_anthropic_agent(
    system_prompt: str,
    user_message: str,
    files: list[dict] | None,
    output_schema: dict,
    model: str,
) -> dict:
    """
    Run one Anthropic Messages call and return the agent's JSON output as
    a dict. Same return contract as `orchestrator.run_agent`.

    Strategy:
      1. Wrap `output_schema` as a JSON Schema for tool-use coercion.
      2. Send a single tool (`emit_result`) and force the model to call it.
      3. Read the `tool_use.input` block and return it.
      4. If no tool_use block is present (gateway / schema edge case),
         fall back to parsing the assistant's text via `_extract_json`.
    """
    client = _get_anthropic_client()

    tool_schema = _coerce_schema_for_tool(output_schema)
    tool_def = {
        "name": _EMIT_TOOL_NAME,
        "description": (
            "Emit the agent's structured result. Call this tool exactly "
            "once with your final answer as the input payload. Do not "
            "produce any other output."
        ),
        "input_schema": tool_schema,
    }

    # The system prompt extension mirrors the OpenAI path's schema
    # instruction so the agent specs do not need to change.
    schema_instruction = (
        "\n\n---\n"
        f"Return your final answer by calling the `{_EMIT_TOOL_NAME}` tool "
        "exactly once. The tool's input must match the schema described "
        "above. Do not produce any text outside the tool call."
    )
    system = system_prompt + schema_instruction

    content = _build_anthropic_content(user_message, files)

    try:
        message = client.messages.create(
            model=model,
            max_tokens=MAX_COMPLETION_TOKENS,
            system=system,
            tools=[tool_def],
            tool_choice={"type": "tool", "name": _EMIT_TOOL_NAME},
            messages=[{"role": "user", "content": content}],
        )
    except Exception as exc:
        # Re-raise with a friendlier message naming the right env var so the
        # fix (refresh JWT) is obvious. We deliberately do not catch the
        # specific anthropic.* error classes here because the SDK version
        # may differ across environments; the wrapped exception preserves
        # the original traceback.
        raise RuntimeError(
            f"Anthropic call failed against {os.environ.get('ANTHROPIC_BASE_URL', 'default endpoint')} "
            f"using model {model!r}: {exc}. "
            "If this is an authentication error, refresh the McKinsey JWT "
            "and update ANTHROPIC_API_KEY in src/.env."
        ) from exc

    parsed = _extract_tool_use_input(message)
    if parsed is not None:
        return parsed

    # Fallback: model returned prose despite the forced tool_choice. Try to
    # parse JSON out of the text blocks before giving up.
    text = _collect_assistant_text(message)
    if not text:
        raise ValueError(
            f"Anthropic model {model!r} returned no tool_use block and no "
            "text content. Cannot extract a structured response."
        )
    return _extract_json(text)
