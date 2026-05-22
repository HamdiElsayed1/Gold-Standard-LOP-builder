from __future__ import annotations

import html as html_module
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from lop_workflow.export.html_simple import markdownish_to_html
from lop_workflow.models.section import SECTION_DOCUMENT_ORDER, SectionId
from lop_workflow.orchestrator.state import OrchestratorState


def _template_path() -> Path:
    return Path(__file__).resolve().parent / "templates"


def _markdown_table_to_html(md: str) -> str:
    """Render coach issue table markdown (pipe tables) to HTML."""
    lines = [ln.strip() for ln in md.splitlines() if ln.strip()]
    if len(lines) < 2 or "|" not in lines[0]:
        return f"<pre>{md}</pre>"
    rows: list[list[str]] = []
    for ln in lines:
        if ln.startswith("| ---") or ln.startswith("|---"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return ""
    out = ['<table class="issue-grid">']
    out.append("<thead><tr>")
    for h in rows[0]:
        out.append(f"<th>{html_module.escape(h)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows[1:]:
        out.append("<tr>")
        for c in r:
            out.append(f"<td>{html_module.escape(c)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def write_html(st: OrchestratorState, out_dir: str) -> str:
    assert st.lop
    tdir = _template_path()
    tdir.mkdir(parents=True, exist_ok=True)
    tpl_file = tdir / "lop.html.j2"
    if not tpl_file.is_file():
        raise FileNotFoundError(f"Missing template: {tpl_file}")

    jenv = Environment(loader=FileSystemLoader(str(tdir)), autoescape=select_autoescape(["html"]))
    tpl = jenv.get_template("lop.html.j2")

    by_id = st.lop.by_section_id()
    chapters: list[dict] = []
    for sid in SECTION_DOCUMENT_ORDER:
        s = by_id.get(sid)
        if not s:
            continue
        title = sid.value.replace("_", " ").title()
        if sid == SectionId.CONTEXT:
            title = "Context and objectives"
        elif sid == SectionId.WHY_MCKINSEY:
            title = "Why McKinsey"
        elif sid == SectionId.TIMELINE_TEAM:
            title = "Timeline and team"
        elif sid == SectionId.MARKET:
            title = "Market trends"
        elif sid == SectionId.TEAM_CVS:
            title = "Team CVs"

        ch: dict = {
            "id": sid.value,
            "title": title,
            "body_html": markdownish_to_html(s.body_markdown),
            "fees_headers": None,
            "fees_rows": None,
        }
        if sid == SectionId.FEES and isinstance(s.extra, dict):
            ft = s.extra.get("fees_table")
            if isinstance(ft, dict):
                ch["fees_headers"] = ft.get("headers")
                ch["fees_rows"] = ft.get("rows")
        chapters.append(ch)

    rubric = dict(st.coach_report.rubric_dimensions) if st.coach_report else {}
    issue_md = st.coach_report.issue_table_markdown if st.coach_report else ""
    issue_html = _markdown_table_to_html(issue_md) if issue_md else ""

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out = Path(out_dir) / f"{st.run_id}_lop.html"
    st.meta["export_type"] = st.meta.get("export_type") or "html"

    html_out = tpl.render(
        project_name=st.lop.project_name,
        run_id=st.run_id,
        client_name=st.brief.client_name if st.brief else "",
        style=st.lop.style_guide,
        chapters=chapters,
        coach_ok=st.coach_report.overall_ok if st.coach_report else None,
        rubric=rubric,
        issue_table_md=issue_html,
    )
    out.write_text(html_out, encoding="utf-8")
    return str(out)
