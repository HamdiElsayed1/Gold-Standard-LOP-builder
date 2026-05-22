from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from lop_workflow.models.section import SectionId
from lop_workflow.orchestrator.state import OrchestratorState


def write_fees_excel(st: OrchestratorState, out_dir: str) -> str:
    """
    Fee table from Fees section ``extra.fees_table`` when present; else stub rows.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Fees (indicative)"

    fees_sec = None
    if st.lop:
        fees_sec = next((s for s in st.lop.sections if s.section_id == SectionId.FEES), None)

    ft = None
    if fees_sec and isinstance(fees_sec.extra, dict):
        ft = fees_sec.extra.get("fees_table")

    if ft and isinstance(ft, dict):
        headers = list(ft.get("headers") or [])
        rows = list(ft.get("rows") or [])
        if headers:
            ws.append(headers)
        else:
            ws.append(["Line item", "Unit", "Amount (indicative)", "Notes / citation"])
        for r in rows:
            ws.append(list(r))
    else:
        ws.append(["Line item", "Unit", "Amount (indicative)", "Notes / citation"])
        for r in (
            ("Program management", "month", "", "TBD with CST"),
            ("Workstreams (x3)", "month", "", "TBD"),
        ):
            ws.append(list(r))

    out = Path(out_dir) / f"{st.run_id}_fees.xlsx"
    wb.save(str(out))
    st.meta["fees_excel"] = str(out)
    st.meta["section_for_fees"] = SectionId.FEES.value
    return str(out)
