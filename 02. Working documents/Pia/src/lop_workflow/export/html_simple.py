"""Minimal Markdown-like body → HTML (no extra deps)."""

from __future__ import annotations

import html


def markdownish_to_html(md: str) -> str:
    lines = md.splitlines()
    parts: list[str] = []
    ul_open = False

    def close_ul() -> None:
        nonlocal ul_open
        if ul_open:
            parts.append("</ul>")
            ul_open = False

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("- ") or line.startswith("* "):
            if not ul_open:
                parts.append("<ul>")
                ul_open = True
            parts.append(f"<li>{html.escape(line[2:].strip())}</li>")
            continue
        close_ul()
        if line.startswith("###"):
            parts.append(f"<h3>{html.escape(line.lstrip('#').strip())}</h3>")
        elif line.startswith("##"):
            parts.append(f"<h2>{html.escape(line.lstrip('#').strip())}</h2>")
        elif line.startswith("#"):
            parts.append(f"<h1>{html.escape(line.lstrip('#').strip())}</h1>")
        elif line.strip():
            parts.append(f"<p>{html.escape(line)}</p>")
    close_ul()
    return "\n".join(parts) if parts else "<p></p>"
