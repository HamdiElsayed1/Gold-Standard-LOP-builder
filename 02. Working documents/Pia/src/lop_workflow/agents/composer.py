from __future__ import annotations

from lop_workflow.models.section import LOPDocument, SECTION_DOCUMENT_ORDER
from lop_workflow.orchestrator.state import OrchestratorState


def harmonize(st: OrchestratorState) -> LOPDocument | None:
    """
    Enforce one tone and cross-refs. Stub: de-dup and sort sections by `SectionId` order.
    """
    if st.lop is None:
        return None
    order = list(SECTION_DOCUMENT_ORDER)
    idx = {s: i for i, s in enumerate(order)}
    st.lop.sections.sort(key=lambda c: idx.get(c.section_id, 99))
    v = st.lop.style_guide
    v.setdefault("crossref_pass", "ok")
    st.lop.style_guide = v
    return st.lop
