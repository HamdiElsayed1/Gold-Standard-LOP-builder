"""Convert Streamlit deck / flat text / intake into lop_eval document models."""

from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from typing import Any

from lop_eval.models import (
    FactRecord,
    HeadingBlock,
    ParagraphBlock,
    ProposalDocument,
    Section,
    SourceOfTruth,
    TableBlock,
)

_SLIDE_HEADER = re.compile(r"^---\s*Slide\s+\d+[^-]*---\s*$", re.M | re.I)


def _slug(s: str) -> str:
    t = re.sub(r"[^a-z0-9]+", "-", (s or "section").lower()).strip("-")
    return t or "section"


class _SlideHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.headings: list[tuple[int, str]] = []
        self.paragraphs: list[str] = []
        self.tables: list[tuple[list[str], list[list[str]]]] = []
        self._skip = 0
        self._buf: list[str] = []
        self._in_table = False
        self._table_headers: list[str] = []
        self._table_rows: list[list[str]] = []
        self._row: list[str] = []
        self._cell: list[str] = []
        self._in_cell = False
        self._in_header_row = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip += 1
        if tag in {"h1", "h2", "h3", "h4"}:
            self._flush_para()
            self._buf = []
        if tag == "p":
            self._flush_para()
            self._buf = []
        if tag == "table":
            self._flush_para()
            self._in_table = True
            self._table_headers = []
            self._table_rows = []
        if tag == "tr" and self._in_table:
            self._row = []
            self._in_header_row = not self._table_rows and not self._table_headers
        if tag in {"td", "th"} and self._in_table:
            self._in_cell = True
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip > 0:
            self._skip -= 1
        if tag in {"h1", "h2", "h3", "h4"} and self._skip == 0:
            text = "".join(self._buf).strip()
            if text:
                level = int(tag[1])
                self.headings.append((level, text))
            self._buf = []
        if tag == "p" and self._skip == 0:
            self._flush_para()
        if tag in {"td", "th"} and self._in_cell:
            cell = "".join(self._cell).strip()
            self._row.append(cell)
            self._in_cell = False
        if tag == "tr" and self._in_table and self._row:
            if self._in_header_row or not self._table_headers:
                self._table_headers = list(self._row)
            else:
                self._table_rows.append(list(self._row))
            self._row = []
        if tag == "table" and self._in_table:
            if self._table_headers or self._table_rows:
                self.tables.append((self._table_headers, self._table_rows))
            self._in_table = False

    def handle_data(self, data: str) -> None:
        if self._skip > 0:
            return
        if self._in_cell:
            self._cell.append(data)
        else:
            self._buf.append(data)

    def _flush_para(self) -> None:
        text = "".join(self._buf).strip()
        if text:
            self.paragraphs.append(text)
        self._buf = []


def _parse_slide_html(html: str) -> list[Any]:
    if not html:
        return []
    parser = _SlideHtmlParser()
    try:
        parser.feed(html)
        parser._flush_para()
    except Exception:
        plain = unescape(re.sub(r"<[^>]+>", " ", html)).strip()
        return [ParagraphBlock(text=plain)] if plain else []

    blocks: list[Any] = []
    for level, text in parser.headings[:1]:
        blocks.append(HeadingBlock(level=level, text=text))
    for _level, text in parser.headings[1:]:
        blocks.append(ParagraphBlock(text=text))
    for p in parser.paragraphs:
        blocks.append(ParagraphBlock(text=p))
    for headers, rows in parser.tables:
        blocks.append(TableBlock(headers=headers or [], rows=rows or []))
    if not blocks:
        plain = unescape(re.sub(r"<[^>]+>", " ", html))
        plain = re.sub(r"\s+", " ", plain).strip()
        if plain:
            blocks.append(ParagraphBlock(text=plain))
    return blocks


def proposal_from_deck(deck: Any, document_id: str) -> ProposalDocument:
    sections: list[Section] = []
    slides = getattr(deck, "slides", None) or []
    for i, slide in enumerate(slides, start=1):
        chapter = getattr(slide, "chapter", None) or getattr(slide, "filename", None) or f"Slide {i}"
        sid = _slug(str(chapter))
        html = getattr(slide, "html", None) or ""
        blocks = _parse_slide_html(html)
        if not blocks:
            blocks = [ParagraphBlock(text="(empty slide)")]
        sections.append(Section(id=sid, title=str(chapter), blocks=blocks))
    return ProposalDocument(document_id=document_id, title="LoP deck", sections=sections)


def proposal_from_text(text: str, document_id: str) -> ProposalDocument:
    if not text or not text.strip():
        return ProposalDocument(document_id=document_id, sections=[])

    headers = _SLIDE_HEADER.findall(text)
    if not headers:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        blocks = [ParagraphBlock(text=ln) for ln in lines] or [ParagraphBlock(text=text.strip())]
        return ProposalDocument(
            document_id=document_id,
            sections=[Section(id="body", title="Document", blocks=blocks)],
        )

    parts = re.split(_SLIDE_HEADER, text.strip())
    chunks = [p.strip() for p in parts if p.strip()]
    sections: list[Section] = []
    for i, (hdr, body) in enumerate(zip(headers, chunks), start=1):
        title = hdr.replace("---", "").strip() or f"Slide {i}"
        sid = _slug(title)
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        blocks = [ParagraphBlock(text=ln) for ln in lines] or [ParagraphBlock(text=body)]
        sections.append(Section(id=sid, title=title, blocks=blocks))

    return ProposalDocument(document_id=document_id, title="LoP proposal", sections=sections)


def source_of_truth_from_intake(intake: Any | None) -> SourceOfTruth | None:
    if intake is None:
        return None
    key_facts = getattr(intake, "key_facts", None) or []
    facts = [
        FactRecord(key=f"fact_{i}", value_text=str(f))
        for i, f in enumerate(key_facts)
        if str(f).strip()
    ]
    return SourceOfTruth(facts=facts) if facts else None
