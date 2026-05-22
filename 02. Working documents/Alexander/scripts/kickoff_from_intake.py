#!/usr/bin/env python3
"""
Alexander LoP helper: list Background Material paths + print intake / kickoff blocks.

Resolves `Gold Standard LOP Builder - Documents` from this file location
(`Alexander/scripts/` -> parents[3]).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def documents_root(script_path: Path) -> Path:
    """Workspace root: folder containing `01. Background material` and `02. Working documents`."""
    return script_path.resolve().parents[3]


def background_roots(root: Path) -> list[Path]:
    candidates = [root / "01. Background material", root / "Background Material"]
    return [p for p in candidates if p.is_dir()]


def iter_background_files(roots: list[Path], max_files: int) -> list[Path]:
    files: list[Path] = []
    for base in roots:
        for p in sorted(base.rglob("*")):
            if not p.is_file():
                continue
            if p.name.startswith("."):
                continue
            files.append(p)
            if len(files) >= max_files:
                return files
    return files


def rel_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def build_tracker_block(client: str, topic: str, duration: str | None, team: str | None) -> str:
    lines = [
        "## Pursuit intake (paste into tracker or chat)",
        "",
        f"- **Client:** {client}",
        f"- **Topic:** {topic}",
    ]
    if duration:
        lines.append(f"- **Project duration:** {duration}")
    if team:
        lines.append(f"- **Team size:** {team}")
    lines.append("")
    slug_client = client.replace("`", "").replace("\\", "")[:80]
    slug_topic = topic.replace("`", "").replace("\\", "")[:60].replace(" ", "-")
    lines.append(f"Suggested pursuit folder name: `{slug_client}-{slug_topic}` *(edit for your naming convention)*")
    lines.append("")
    lines.append(
        "Next: `@` relevant files from `01. Background material`, paste the **Cursor kickoff** "
        "(from intake.html or `kickoff_from_intake.py --kickoff`), then confirm manifest **Y** rows "
        "per `Jasper/lop-cursor-runbook.md`."
    )
    return "\n".join(lines)


def build_kickoff(client: str, topic: str, duration: str | None, team: str | None) -> str:
    intake_lines = [f"- **Client:** {client}", f"- **Topic / opportunity:** {topic}"]
    if duration:
        intake_lines.append(f"- **Project duration:** {duration}")
    if team:
        intake_lines.append(f"- **Team size:** {team}")

    body = f"""You are the LoP builder assistant for this workspace. Obey `.cursor/rules/lop-builder-*.mdc` and `02. Working documents/Jasper/lop-cursor-runbook.md`. Do not invent client facts, fees, credentials, or legal / practice disclaimers — use only attached sources for substantive claims; label inferences clearly; use **TBD** + owner when evidence is missing.

## Pursuit intake (user-provided)

{chr(10).join(intake_lines)}

## Attached sources (Step 0)

I have attached files with `@` from `01. Background material` and/or my pursuit folder. **Only** those attachments may be treated as sources of fact for this run.

Your outputs in **two phases**:

**Phase 1 (this message only):** Output the **Step 0 — Source manifest** as a markdown table: `# | Source label | Path / filename | In use for this run? (Y/N) | Notes`. List **every** file I attached (and this intake). Suggest **Y** only where clearly in scope for this client/topic; use **N** or **TBD** where ambiguous. **Stop after the table** — do not draft problem statement or LoP body until I reply confirming which rows are **Y**.

**Phase 2 (after I confirm Y rows):** (1) **Problem statement (one page)** — only from **Y** rows; explicit **assumptions** where thin. (2) **Clarifying questions** — one numbered list; blocking vs non-blocking. (3) **LoP spine** — section titles only (Context & objectives; Why McKinsey; Timeline and team; Team; Credentials; Market trends; Approach; Fees; Appendix; References; Team CVs). No long **Approach** prose yet.

When I reply **Gate A OK**, proceed with chapter drafting per `Jasper/prompts/`, one section at a time, stating **Sources used:** manifest row numbers after each. Fees: **TBD** or attached numbers only. End with **LOP coach** issue list and **assembler** PPT + HTML packs per runbook."""
    return body


def manifest_hint_table(paths: list[Path], root: Path) -> str:
    lines = [
        "## Step 0 manifest hints (from disk — you must still confirm Y in Cursor)",
        "",
        "| # | Source label | Path (for `@` in Cursor) | In use? (Y/N) | Notes |",
        "|---|----------------|-------------------------|---------------|--------|",
    ]
    for i, p in enumerate(paths, start=1):
        rel = rel_posix(p, root)
        lines.append(f"| {i} | | `{rel}` | | |")
    lines.append("")
    lines.append("_Paths are relative to the workspace `Gold Standard LOP Builder - Documents` root._")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List Background Material files and/or print tracker + Cursor kickoff text."
    )
    parser.add_argument("--list-bg", action="store_true", help="Print manifest-hint table for files under 01. Background material")
    parser.add_argument("--max-files", type=int, default=400, help="Cap when listing Background Material (default 400)")
    parser.add_argument("--kickoff", action="store_true", help="Print tracker block + Cursor kickoff (requires --client and --topic)")
    parser.add_argument("--client", default="", help="Client name")
    parser.add_argument("--topic", default="", help="Topic / opportunity")
    parser.add_argument("--duration", default="", help="Optional project duration")
    parser.add_argument("--team", default="", help="Optional team size")
    parser.add_argument(
        "--separator",
        default="\n\n---\n\n",
        help="String between tracker block and kickoff when both printed (default: markdown horizontal rule)",
    )
    args = parser.parse_args(argv)

    here = Path(__file__)
    root = documents_root(here)
    roots = background_roots(root)

    if not args.list_bg and not args.kickoff:
        parser.print_help()
        print("\nTip: pass --list-bg and/or --kickoff (with --client and --topic).", file=sys.stderr)
        return 1

    if args.list_bg:
        if not roots:
            print(f"No Background Material folder found under {root}", file=sys.stderr)
            return 2
        paths = iter_background_files(roots, args.max_files)
        print(manifest_hint_table(paths, root))
        if len(paths) >= args.max_files:
            print(f"\n_Listing capped at {args.max_files} files._", file=sys.stderr)

    if args.kickoff:
        client, topic = args.client.strip(), args.topic.strip()
        if not client or not topic:
            print("--kickoff requires non-empty --client and --topic", file=sys.stderr)
            return 3
        duration = args.duration.strip() or None
        team = args.team.strip() or None
        tracker = build_tracker_block(client, topic, duration, team)
        kick = build_kickoff(client, topic, duration, team)
        if args.list_bg:
            print(args.separator, end="")
        print(tracker)
        print(args.separator, end="")
        print(kick)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
