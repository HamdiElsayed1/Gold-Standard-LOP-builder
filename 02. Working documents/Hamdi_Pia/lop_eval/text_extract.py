"""Walk proposal blocks and yield text snippets with locations."""

from __future__ import annotations

from dataclasses import dataclass

from lop_eval.models import (
    Block,
    CaptionBlock,
    FootnoteBlock,
    HeadingBlock,
    ListBlock,
    ParagraphBlock,
    ProposalDocument,
    Section,
    TableBlock,
)


@dataclass(frozen=True)
class TextSpan:
    section: Section
    section_index: int
    block_index: int
    block: Block
    text: str


def iter_text_spans(doc: ProposalDocument) -> list[TextSpan]:
    spans: list[TextSpan] = []
    for si, sec in enumerate(doc.sections):
        for bi, block in enumerate(sec.blocks):
            if isinstance(block, ParagraphBlock):
                spans.append(TextSpan(sec, si, bi, block, block.text))
            elif isinstance(block, HeadingBlock):
                spans.append(TextSpan(sec, si, bi, block, block.text))
            elif isinstance(block, ListBlock):
                for item in block.items:
                    spans.append(TextSpan(sec, si, bi, block, item))
            elif isinstance(block, FootnoteBlock | CaptionBlock):
                spans.append(TextSpan(sec, si, bi, block, block.text))
            elif isinstance(block, TableBlock):
                if block.caption:
                    spans.append(TextSpan(sec, si, bi, block, block.caption))
                for row in block.rows:
                    for cell in row:
                        spans.append(TextSpan(sec, si, bi, block, cell))
                for h in block.headers:
                    spans.append(TextSpan(sec, si, bi, block, h))
    return spans


def section_joined_text(sec: Section) -> list[str]:
    parts: list[str] = []
    for block in sec.blocks:
        if isinstance(block, ParagraphBlock):
            parts.append(block.text)
        elif isinstance(block, HeadingBlock):
            parts.append(block.text)
        elif isinstance(block, ListBlock):
            parts.extend(block.items)
        elif isinstance(block, TableBlock):
            if block.caption:
                parts.append(block.caption)
            parts.extend(" | ".join(r) for r in block.rows)
            parts.append(" | ".join(block.headers))
        elif isinstance(block, FootnoteBlock | CaptionBlock):
            parts.append(block.text)
    return parts


def section_narrative_text(sec: Section) -> str:
    """Paragraphs, lists, headings, captions/footnotes — excludes table cell bodies."""

    parts: list[str] = []
    for block in sec.blocks:
        if isinstance(block, ParagraphBlock):
            parts.append(block.text)
        elif isinstance(block, HeadingBlock):
            parts.append(block.text)
        elif isinstance(block, ListBlock):
            parts.extend(block.items)
        elif isinstance(block, TableBlock):
            if block.caption:
                parts.append(block.caption)
        elif isinstance(block, FootnoteBlock | CaptionBlock):
            parts.append(block.text)
    return " ".join(parts)
