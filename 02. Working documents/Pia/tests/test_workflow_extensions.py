import tempfile

from lop_workflow.agents.planner import build_default_toc
from lop_workflow.models import LOPCategory
from lop_workflow.models.section import SECTION_DOCUMENT_ORDER
from lop_workflow.orchestrator.graph import LopWorkflow, NoOpAgents
from lop_workflow.orchestrator.state import HumanCheckpoint, Phase


def test_canonical_toc_has_eleven_chapters():
    toc = build_default_toc()
    assert len(toc) == 11
    assert [t.section_id for t in toc] == list(SECTION_DOCUMENT_ORDER)


def test_resolve_pre_final_send_back_returns_to_write():
    out = tempfile.mkdtemp()
    w = LopWorkflow(agents=NoOpAgents(), audit_path=None, out_dir=out)
    st = w.new_run(project_name="P", client_name="C", voice_transcript="note")
    st = w.resolve_intake(st, lop_category=LOPCategory.NON_COMPETITIVE)
    hit = False
    for _ in range(100):
        st = w.advance(st)
        if st.pending_checkpoint == HumanCheckpoint.POST_TOC:
            st = w.resolve_post_toc(st)
        elif st.pending_checkpoint == HumanCheckpoint.PRE_FINAL:
            st = w.resolve_pre_final_send_back(st, feedback="Sharpen win themes")
            assert st.phase == Phase.WRITE_ELEMENTS
            assert st.meta.get("revision_feedback") == "Sharpen win themes"
            hit = True
            break
    assert hit


def test_background_material_loads_readme(tmp_path):
    from lop_workflow.corpus.background_material import load_background_sources

    (tmp_path / "note.md").write_text("# RFP\nKey ask: digital.", encoding="utf-8")
    refs = load_background_sources(tmp_path)
    assert len(refs) == 1
    assert refs[0].source_type == "background_material"
    assert "digital" in refs[0].snippet
