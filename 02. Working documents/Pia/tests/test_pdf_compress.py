from __future__ import annotations

from pathlib import Path

import pytest

from lop_workflow.pdf_compress import collect_pdf_paths, compress_pdf_file


def test_collect_pdf_paths_folder(tmp_path: Path) -> None:
    d = tmp_path / "pdfs"
    d.mkdir()
    (d / "a.pdf").write_bytes(b"x")
    found = collect_pdf_paths([str(d)], recursive=False)
    assert len(found) == 1


def test_compress_writes_smaller_or_reasonable(tmp_path: Path) -> None:
    fitz = pytest.importorskip("fitz")
    src = tmp_path / "in.pdf"
    out = tmp_path / "out.pdf"
    doc = fitz.open()
    doc.new_page()
    page = doc[0]
    page.insert_text((72, 72), "Hello LoP compress test.")
    doc.save(src.as_posix())
    doc.close()

    bi, bo = compress_pdf_file(src, out, strong=False)
    assert out.is_file()
    assert bo > 0
    assert bi > 0
