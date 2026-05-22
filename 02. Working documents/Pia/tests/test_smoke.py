import tempfile
from pathlib import Path

from lop_workflow.orchestrator import Phase, run_to_done_with_auto_approves


def test_full_run_exports_files():
    d = tempfile.mkdtemp()
    st, paths = run_to_done_with_auto_approves(out_dir=d, use_pipeline_agents=False)
    assert st.phase == Phase.DONE
    assert st.coach_report and st.lop
    p = Path(d)
    by_name = {x.name: x for x in p.iterdir() if x.is_file()}
    assert any(name.endswith(".html") for name in by_name)
    assert any(name.endswith(".pptx") for name in by_name)
    assert any(name.endswith(".xlsx") for name in by_name)
    assert len(paths) >= 3
