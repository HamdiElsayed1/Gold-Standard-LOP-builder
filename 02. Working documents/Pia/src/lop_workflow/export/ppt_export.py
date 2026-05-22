from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from lop_workflow.export.ppt_layouts import add_section_slides, add_title_slide
from lop_workflow.models.section import SECTION_DOCUMENT_ORDER
from lop_workflow.orchestrator.state import OrchestratorState


def write_pptx(st: OrchestratorState, out_dir: str) -> str:
    assert st.lop
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    add_title_slide(prs, st)

    by_id = st.lop.by_section_id()
    for sid in SECTION_DOCUMENT_ORDER:
        s = by_id.get(sid)
        if s:
            add_section_slides(prs, st, s)

    out = Path(out_dir) / f"{st.run_id}_lop.pptx"
    prs.save(str(out))
    st.meta["export_pptx"] = str(out)
    return str(out)
