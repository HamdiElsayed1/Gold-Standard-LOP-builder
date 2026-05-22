"""
slide_renderer — Step 8 helper for the LoP builder.

Provides pure-Python file plumbing around the slide-author-agent. No
Playwright, no PPTX compile this iteration; we only emit HTML that links
the bundled `css/slide.css` from `inputs/slide_workspace_v0/`.

Public functions
----------------
- copy_mckinsey_assets(target_dir)   — clone the bundled CSS + templates
- parse_client_pptx_style(bytes)     — extract accent colours + theme fonts
- write_client_css(style, target_dir)— emit `css/client.css` overrides
- wrap_slide_html(...)               — wrap an agent-produced <section> in
                                       a full HTML document
- write_deck(target_dir, slides, mode, ...) — write per-slide files +
                                       index.html for in-app preview
- zip_deck(target_dir)               — package the deck for download
"""

from __future__ import annotations

import io
import re
import shutil
import zipfile
from pathlib import Path

# python-pptx is optional at import time so the module still loads on
# environments where the dep isn't installed (e.g. unit tests for
# unrelated helpers). The PPTX parsing path raises a clear error if
# the user actually tries to use it without python-pptx installed.
try:  # pragma: no cover - import guard
    from pptx import Presentation
    from pptx.util import Length  # noqa: F401  (kept for type clarity)
    _HAS_PPTX = True
except Exception:  # pragma: no cover
    _HAS_PPTX = False


# ─── PATHS ────────────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # Hamdi/
_SLIDE_WORKSPACE = _PROJECT_ROOT / "inputs" / "slide_workspace_v0"
_BUNDLED_CSS = _SLIDE_WORKSPACE / "css" / "slide.css"
_BUNDLED_TEMPLATES_DIR = (
    _SLIDE_WORKSPACE
    / ".cursor"
    / "skills"
    / "write-html-slides"
    / "reference"
    / "templates"
)


# ─── ASSET COPY ───────────────────────────────────────────────────────────────

def copy_mckinsey_assets(target_dir: Path) -> None:
    """
    Clone the bundled McKinsey CSS + layout templates into `target_dir`.

    Layout
    ------
    ``<target_dir>/css/slide.css`` — the shared stylesheet every slide links.
    ``<target_dir>/templates/<layout>.html`` — reference templates the BA
    can open in a browser to compare against.

    Idempotent: if a destination file already exists with the same content,
    it is left alone. If it exists but differs, we overwrite — the BA
    should always have the latest bundled CSS.
    """
    target_dir = Path(target_dir)
    css_target = target_dir / "css"
    css_target.mkdir(parents=True, exist_ok=True)

    if not _BUNDLED_CSS.exists():
        raise FileNotFoundError(
            f"Bundled slide.css not found at {_BUNDLED_CSS}. "
            "Run from a checkout that includes inputs/slide_workspace_v0/."
        )
    shutil.copy2(_BUNDLED_CSS, css_target / "slide.css")

    if _BUNDLED_TEMPLATES_DIR.exists():
        templates_target = target_dir / "templates"
        templates_target.mkdir(parents=True, exist_ok=True)
        for tpl in _BUNDLED_TEMPLATES_DIR.glob("*.html"):
            shutil.copy2(tpl, templates_target / tpl.name)


# ─── CLIENT STYLE EXTRACTION ──────────────────────────────────────────────────

_HEX_RE = re.compile(r"^[0-9A-Fa-f]{6}$")


def _normalise_hex(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip().lstrip("#")
    if _HEX_RE.match(v):
        return f"#{v.upper()}"
    return ""


def parse_client_pptx_style(pptx_bytes: bytes) -> dict:
    """
    Extract a small style fingerprint from an uploaded PPTX so we can
    emit a `client.css` overlay. We deliberately do NOT try to fully
    re-skin every theme — only the high-signal pieces:

    - ``accent_colors``: list of theme accent hex strings (best-effort)
    - ``primary_font``: theme major font (titles)
    - ``secondary_font``: theme minor font (body)
    - ``summary``: a one-paragraph human-readable description

    Returns ``{}`` when the upload cannot be parsed at all (so the caller
    can fall back to McKinsey defaults without crashing the run).
    """
    if not _HAS_PPTX:
        return {}

    try:
        prs = Presentation(io.BytesIO(pptx_bytes))
    except Exception:
        return {}

    accent_colors: list[str] = []
    primary_font = ""
    secondary_font = ""

    # python-pptx does not expose the theme cleanly, but the underlying
    # XML is straightforward to walk. Each slide master carries a
    # reference to a theme part with `<a:clrScheme>` + `<a:fontScheme>`.
    try:
        master = prs.slide_master
        # `_element` is undocumented but stable; `.part.theme.element` is
        # the theme XML root. Wrap defensively.
        theme_el = None
        try:
            theme_el = master.element.getparent().getparent()  # safety fallback
        except Exception:
            theme_el = None
        # Preferred path — explicit theme accessor
        try:
            theme_part = master.part.related_part(
                next(iter(master.part.rels))
            )
            # Walk rels to find the theme part
            for rel in master.part.rels.values():
                if "theme" in rel.reltype:
                    theme_part = rel.target_part
                    break
            theme_el = theme_part.element
        except Exception:
            pass

        if theme_el is not None:
            ns = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
            clr_scheme = theme_el.find(f".//{ns}clrScheme")
            if clr_scheme is not None:
                for accent_tag in (
                    "accent1", "accent2", "accent3",
                    "accent4", "accent5", "accent6",
                ):
                    el = clr_scheme.find(f"{ns}{accent_tag}")
                    if el is None:
                        continue
                    srgb = el.find(f"{ns}srgbClr")
                    if srgb is not None and srgb.get("val"):
                        accent_colors.append(_normalise_hex(srgb.get("val")))

            font_scheme = theme_el.find(f".//{ns}fontScheme")
            if font_scheme is not None:
                major = font_scheme.find(f"{ns}majorFont/{ns}latin")
                minor = font_scheme.find(f"{ns}minorFont/{ns}latin")
                if major is not None and major.get("typeface"):
                    primary_font = major.get("typeface").strip()
                if minor is not None and minor.get("typeface"):
                    secondary_font = minor.get("typeface").strip()
    except Exception:
        # Best-effort — partial extraction is fine, total failure → empty
        pass

    accent_colors = [c for c in accent_colors if c]

    parts: list[str] = []
    if accent_colors:
        parts.append(f"accents {', '.join(accent_colors[:3])}")
    if primary_font:
        parts.append(f"title font {primary_font}")
    if secondary_font:
        parts.append(f"body font {secondary_font}")
    summary = "Client style: " + "; ".join(parts) if parts else ""

    return {
        "accent_colors": accent_colors,
        "primary_font": primary_font,
        "secondary_font": secondary_font,
        "summary": summary,
    }


# ─── CLIENT CSS WRITER ────────────────────────────────────────────────────────

def write_client_css(style: dict, target_dir: Path) -> Path | None:
    """
    Emit `<target_dir>/css/client.css` re-declaring the CSS variables
    that the bundled `slide.css` references for accent colours and
    typography. Returns the path on success, or None if `style` is empty.
    """
    if not style:
        return None

    target_dir = Path(target_dir)
    css_dir = target_dir / "css"
    css_dir.mkdir(parents=True, exist_ok=True)

    accents = style.get("accent_colors") or []
    primary_font = style.get("primary_font") or ""
    secondary_font = style.get("secondary_font") or ""

    lines: list[str] = [
        "/* client.css — overrides for slide.css custom properties.",
        " * Generated from the partner-supplied PPTX style fingerprint.",
        " * Edit by hand if the auto-extracted values do not match. */",
        ":root {",
    ]
    if accents:
        # Map accent1 -> --electric-blue-900, accent2 -> --cyan-500, accent3 -> --bright-blue-500
        # The bundled slide.css uses these as the highlight palette.
        if len(accents) >= 1:
            lines.append(f"  --electric-blue-900: {accents[0]};")
            lines.append(f"  --electric-blue-800: {accents[0]};")
            lines.append(f"  --electric-blue-700: {accents[0]};")
        if len(accents) >= 2:
            lines.append(f"  --cyan-500: {accents[1]};")
            lines.append(f"  --cyan-700: {accents[1]};")
        if len(accents) >= 3:
            lines.append(f"  --bright-blue: {accents[2]};")
    if primary_font:
        lines.append(f"  --font-title: '{primary_font}', Georgia, serif;")
    if secondary_font:
        lines.append(
            f"  --font-content: '{secondary_font}', Arial, sans-serif;"
        )
    lines.append("}")

    out = css_dir / "client.css"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# ─── HTML WRAPPING ────────────────────────────────────────────────────────────

def _slide_doc_head(format_mode: str, title: str) -> str:
    css_links = ['<link rel="stylesheet" href="../css/slide.css">']
    if format_mode == "client":
        css_links.append('<link rel="stylesheet" href="../css/client.css">')
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=1920, height=1080">\n'
        f"<title>{title}</title>\n"
        + "\n".join(css_links)
        + "\n</head>\n<body>\n"
    )


def wrap_slide_html(
    section_html: str,
    format_mode: str,
    slide_index: int,
    chapter: str,
) -> str:
    """
    Wrap an agent-produced ``<section class="slide">…</section>`` block in
    a full standalone HTML document so it can be opened directly in a
    browser at the 1920×1080 viewport.

    The CSS link uses ``../css/slide.css`` because slide files live in
    ``<deck>/slides/`` while the stylesheet lives in ``<deck>/css/``.
    """
    title = f"Slide {slide_index + 1} — {chapter}"
    head = _slide_doc_head(format_mode, title)
    return head + section_html.strip() + "\n</body>\n</html>\n"


# ─── DECK WRITING ─────────────────────────────────────────────────────────────

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(name: str) -> str:
    slug = _SLUG_RE.sub("-", name.lower()).strip("-")
    return slug or "slide"


def _index_html(
    deck_dir: Path,
    slide_files: list[tuple[int, str, str]],
) -> str:
    """
    Build a scrollable preview document. Each slide is embedded as an
    iframe at 1920×1080 and scaled down to the viewport width via CSS
    transform. The transform preserves the slide's pixel-perfect layout
    — what you see is exactly what compile-slides would render.
    """
    rows: list[str] = []
    for idx, chapter, filename in slide_files:
        rows.append(
            "    <div class=\"slide-card\">\n"
            f"      <div class=\"slide-label\">Slide {idx + 1} — "
            f"{chapter}</div>\n"
            "      <div class=\"slide-frame-outer\">\n"
            "        <div class=\"slide-frame-inner\">\n"
            f'          <iframe src="slides/{filename}" '
            'width="1920" height="1080" '
            'style="border:0; display:block;"></iframe>\n'
            "        </div>\n"
            "      </div>\n"
            "    </div>\n"
        )

    body = "\n".join(rows)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        "<title>LoP slide deck preview</title>\n"
        "<style>\n"
        "  * { box-sizing: border-box; margin: 0; padding: 0; }\n"
        "  body { background: #1a1a1a; padding: 32px;"
        " font-family: system-ui, sans-serif; }\n"
        "  .slide-card { margin-bottom: 32px; }\n"
        "  .slide-label { color: #ddd; font-size: 14px; margin-bottom: 8px;"
        " letter-spacing: 0.3px; }\n"
        "  .slide-frame-outer { width: 100%; max-width: 1280px;"
        " aspect-ratio: 16 / 9; background: #fff;"
        " box-shadow: 0 4px 18px rgba(0,0,0,0.45); overflow: hidden; }\n"
        "  .slide-frame-inner { width: 1920px; height: 1080px;"
        " transform-origin: top left;"
        " transform: scale(calc(min(100vw, 1280px) / 1920)); }\n"
        "</style>\n"
        "</head>\n<body>\n"
        + body
        + "</body>\n</html>\n"
    )


def write_deck(
    target_dir: Path,
    slides: list,  # list[SlideHTML]; typed loosely to avoid circular import
    format_mode: str = "mckinsey",
) -> Path:
    """
    Write per-slide HTML files into ``<target_dir>/slides/`` and an
    ``index.html`` at ``<target_dir>/`` that previews the whole deck.

    Returns the path to ``index.html``.
    """
    target_dir = Path(target_dir)
    slides_dir = target_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)

    slide_files: list[tuple[int, str, str]] = []
    for idx, s in enumerate(slides):
        # `s.filename` is set by the caller; if it isn't, derive a slug.
        filename = getattr(s, "filename", "") or (
            f"{idx + 1:02d}-{_slugify(getattr(s, 'chapter', f'slide-{idx}'))}.html"
        )
        chapter = getattr(s, "chapter", f"Slide {idx + 1}")
        html_body = getattr(s, "html", "")
        doc = wrap_slide_html(html_body, format_mode, idx, chapter)
        (slides_dir / filename).write_text(doc, encoding="utf-8")
        slide_files.append((idx, chapter, filename))

    index_path = target_dir / "index.html"
    index_path.write_text(
        _index_html(target_dir, slide_files), encoding="utf-8"
    )
    return index_path


def zip_deck(target_dir: Path) -> bytes:
    """
    Package ``target_dir`` (CSS + slides + index.html) as a single ZIP
    blob suitable for ``st.download_button``. The archive preserves the
    relative layout so the BA can unzip and double-click any slide HTML
    to open it directly in their browser.
    """
    target_dir = Path(target_dir)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in target_dir.rglob("*"):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(target_dir))
    return buf.getvalue()
