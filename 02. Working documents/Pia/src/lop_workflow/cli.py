"""CLI: paths, demo run, and stepping through human checkpoints."""

from __future__ import annotations

import argparse
import json
import sys

from lop_workflow.models import LOPCategory
from lop_workflow.orchestrator.graph import LopWorkflow, run_to_done_with_auto_approves
from lop_workflow.orchestrator.state import HumanCheckpoint, OrchestratorState, Phase
from lop_workflow.pdf_compress import build_compress_parser
from lop_workflow.workspace_paths import (
    background_material_dir,
    ensure_workspace_directories,
    lop_exports_dir,
    lop_workspace_dir,
)


def _print_state(st: OrchestratorState) -> None:
    payload = {
        "run_id": st.run_id,
        "phase": st.phase.value,
        "pending_checkpoint": st.pending_checkpoint.value if st.pending_checkpoint else None,
        "sections": len(st.lop.sections) if st.lop else 0,
    }
    print(json.dumps(payload, indent=2))


def cmd_paths() -> int:
    ensure_workspace_directories()
    print("background_material:", str(background_material_dir()))
    print("lop_exports:", str(lop_exports_dir()))
    print("lop_workspace:", str(lop_workspace_dir()))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    ensure_workspace_directories()
    out = args.out or str(lop_exports_dir())
    st, paths = run_to_done_with_auto_approves(
        out_dir=out,
        lop_category=LOPCategory.NON_COMPETITIVE,
        use_pipeline_agents=not args.stub_agents,
    )
    print("phase:", st.phase.value)
    for p in paths:
        print("export:", p)
    return 0 if st.phase == Phase.DONE else 1


def cmd_step(args: argparse.Namespace) -> int:
    """Advance the graph with explicit human resolutions (for integration tests / demos)."""
    from lop_workflow.agents.pipeline_agents import PipelineAgentContext

    ensure_workspace_directories()
    agents = PipelineAgentContext() if not args.stub_agents else None
    from lop_workflow.orchestrator.graph import NoOpAgents

    w = LopWorkflow(
        agents=agents or NoOpAgents(),
        audit_path=str(lop_workspace_dir() / "audit.log"),
        out_dir=args.out or str(lop_exports_dir()),
    )
    st = w.new_run(
        project_name=args.project or "CLI LOP",
        client_name=args.client or "Client",
        voice_transcript=args.voice or "",
    )
    st = w.resolve_intake(st, lop_category=LOPCategory.NON_COMPETITIVE)

    max_steps = args.max_steps
    for _ in range(max_steps):
        if st.phase == Phase.DONE:
            break
        st = w.advance(st)
        if st.pending_checkpoint == HumanCheckpoint.POST_TOC:
            st = w.resolve_post_toc(st)
        elif st.pending_checkpoint == HumanCheckpoint.PRE_FINAL:
            if args.send_back:
                st = w.resolve_pre_final_send_back(st, feedback=args.send_back)
            else:
                st = w.resolve_pre_final(st)
        if args.verbose:
            _print_state(st)

    if args.json:
        print(json.dumps({"phase": st.phase.value, "export_paths": st.meta.get("export_paths", [])}))
    else:
        print("final_phase:", st.phase.value)
    return 0 if st.phase == Phase.DONE else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="lop-workflow", description="LoP agentic workflow CLI")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("paths", help="Print Background Material and default export paths; ensure folders exist")
    sp.set_defaults(func=lambda _args: cmd_paths())

    sr = sub.add_parser(
        "run",
        help=(
            "Full auto-approved demo run to export. "
            "Default: PipelineAgentContext (indexes Background Material / optional LLM). "
            "With --stub-agents: NoOpAgents only (no corpus scan)."
        ),
    )
    sr.add_argument("--out", default=None, help="Export directory (default: Fleur/exports)")
    sr.add_argument(
        "--stub-agents",
        action="store_true",
        help="Use NoOpAgents instead of PipelineAgentContext (no Background Material scan; offline stubs)",
    )
    sr.set_defaults(func=cmd_run)

    ss = sub.add_parser("step", help="Run state machine with scripted checkpoint resolutions")
    ss.add_argument("--out", default=None)
    ss.add_argument("--project", default="CLI LOP")
    ss.add_argument("--client", default="Client")
    ss.add_argument("--voice", default="")
    ss.add_argument("--max-steps", type=int, default=96)
    ss.add_argument("--verbose", action="store_true")
    ss.add_argument("--json", action="store_true")
    ss.add_argument(
        "--stub-agents",
        action="store_true",
        help="Use NoOpAgents only",
    )
    ss.add_argument(
        "--send-back",
        default="",
        metavar="FEEDBACK",
        help="At pre-final, send draft back to writers with this feedback instead of exporting",
    )
    ss.set_defaults(func=cmd_step)

    build_compress_parser(sub)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
