"""
slide_renderer — Step 8 helper for the LoP builder.

Produces ONE self-contained HTML deck file (`index.html`) with the bundled
McKinsey `slide.css` inlined, every slide rendered as a directly-inlined
`<section class="slide">` block scaled to the viewport via CSS transform.
No iframes, no per-slide files, no `css/` folder, no zip — the BA gets a
single `.html` they can email or open offline.

Public functions
----------------
- parse_client_pptx_style(bytes)        — extract accent colours + theme fonts
- build_client_css_text(style)          — render a small CSS overlay string
                                          from a parsed style fingerprint
- build_deck_html(slides, mode, ...)    — assemble the single-file deck HTML
- write_single_deck(target_dir, ...)    — write `<target_dir>/index.html`
"""

from __future__ import annotations

import io
import re
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
    Extract a small style fingerprint from an uploaded PPTX so we can emit
    a CSS overlay. We deliberately do NOT try to fully re-skin every theme
    — only the high-signal pieces:

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
    # XML is straightforward to walk.
    try:
        master = prs.slide_master
        theme_el = None
        try:
            theme_part = master.part.related_part(
                next(iter(master.part.rels))
            )
            for rel in master.part.rels.values():
                if "theme" in rel.reltype:
                    theme_part = rel.target_part
                    break
            theme_el = theme_part.element
        except Exception:
            theme_el = None

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


# ─── CLIENT CSS OVERLAY ───────────────────────────────────────────────────────

def build_client_css_text(style: dict) -> str:
    """
    Render a CSS overlay string from a parsed style fingerprint.  The
    overlay re-declares the small set of CSS variables that the bundled
    `slide.css` references for accent colours and typography. Returns
    `""` when the style dict is empty or has nothing usable.
    """
    if not style:
        return ""

    accents = style.get("accent_colors") or []
    primary_font = style.get("primary_font") or ""
    secondary_font = style.get("secondary_font") or ""

    if not accents and not primary_font and not secondary_font:
        return ""

    lines: list[str] = [
        "/* client overlay — generated from the partner-supplied PPTX style fingerprint. */",
        ":root {",
    ]
    if accents:
        # Map accent1 -> --electric-blue-900, accent2 -> --cyan-500, accent3 -> --bright-blue-500
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
    return "\n".join(lines) + "\n"


# ─── DECK CSS (wrapper / nav / scaling / partial ribbon / print) ──────────────

_DECK_WRAPPER_CSS = """
/* Single-HTML deck wrapper — no iframes; pixel-perfect 1920x1080 sections
   scaled to the viewport using CSS transform. */
:root { color-scheme: light; }
html, body { margin: 0; padding: 0; }
body {
  background: #1a1a1a;
  padding: 0 0 64px;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: #ddd;
}

.deck-nav {
  position: sticky;
  top: 0;
  background: #0a0a0a;
  color: #fff;
  padding: 10px 24px;
  z-index: 1000;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}
.deck-nav .deck-title {
  font-weight: 700;
  margin-right: 16px;
  font-size: 12px;
  letter-spacing: 0.15em;
  color: #fff;
}
.deck-nav a {
  color: #cfcfcf;
  text-decoration: none;
  font-size: 12px;
  padding: 4px 10px;
  border: 1px solid #2a2a2a;
}
.deck-nav a:hover { background: #1f1f1f; color: #fff; }

.deck-main { padding: 32px 0 0; }
.slide-card { margin: 0 auto 32px; }
.slide-label {
  color: #bbb;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 0 auto 8px;
  max-width: 1280px;
  padding: 0 16px;
}

.slide-shell {
  width: min(calc(100vw - 64px), 1280px);
  aspect-ratio: 16 / 9;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45);
  margin: 0 auto;
  background: #ffffff;
}
.slide-shell > .slide {
  position: absolute;
  top: 0;
  left: 0;
  width: 1920px;
  height: 1080px;
  transform-origin: top left;
  /* The actual scale factor is set as an inline `transform` style by the
     deck-scale script at the bottom of <body>. Pure-CSS scaling against
     a length-divided-by-length result is rejected by Chromium/Firefox
     inside the transform property, so we drive scaling from JS instead. */
  transform: scale(1);
}

/* Cover-slide background — no external image needed. */
.slide[data-layout="Title"] {
  background: var(--navy);
  background-image: linear-gradient(135deg, var(--navy) 0%, var(--electric-blue-900) 100%);
}

/* Partial / placeholder ribbon — replaces the visible "Placeholder…" body
   paragraph that earlier agent runs leaked onto slides. */
.slide[data-confidence="partial"]::after,
.slide[data-confidence="placeholder"]::after {
  content: "PARTIAL — pending partner confirmation";
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 11px;
  letter-spacing: 0.15em;
  padding: 4px 10px;
  background: var(--amber-yellow-500);
  color: var(--black);
  font-family: var(--font-content);
  font-weight: 700;
  z-index: 200;
}
.slide[data-confidence="placeholder"]::after {
  content: "PLACEHOLDER — not yet drafted";
}

@media print {
  body { background: #fff; padding: 0; }
  .deck-nav, .slide-label { display: none !important; }
  .slide-card { margin: 0; page-break-after: always; }
  .slide-shell {
    width: 100vw;
    max-width: none;
    aspect-ratio: 16 / 9;
    box-shadow: none;
  }
  /* The deck-scale script re-runs on `beforeprint`, so .slide-shell > .slide
     gets a freshly computed inline transform sized to the print viewport. */
}
"""


# ─── DECK SCALE SCRIPT ────────────────────────────────────────────────────────
#
# Inlined at the bottom of <body> by `build_deck_html`. Sets
# `slide.style.transform = scale(<shell.clientWidth / 1920>)` for every
# `.slide-shell > .slide`, then re-runs on resize (via `ResizeObserver`
# with a `window.resize` fallback) and around print events. Keeps the
# 1920x1080 sections pixel-perfect while fitting them to the responsive
# `.slide-shell` width without iframes.

_DECK_SCALE_SCRIPT = """
(function () {
  function scaleOne(shell) {
    var slide = shell.querySelector(':scope > .slide');
    if (!slide) return;
    var w = shell.clientWidth;
    if (!w) return;
    slide.style.transform = 'scale(' + (w / 1920) + ')';
  }
  function scaleAll() {
    var shells = document.querySelectorAll('.slide-shell');
    for (var i = 0; i < shells.length; i++) scaleOne(shells[i]);
  }
  scaleAll();
  if ('ResizeObserver' in window) {
    var ro = new ResizeObserver(function (entries) {
      for (var i = 0; i < entries.length; i++) scaleOne(entries[i].target);
    });
    var shells = document.querySelectorAll('.slide-shell');
    for (var i = 0; i < shells.length; i++) ro.observe(shells[i]);
  } else {
    window.addEventListener('resize', scaleAll);
  }
  window.addEventListener('beforeprint', scaleAll);
  window.addEventListener('afterprint', scaleAll);
})();
"""


# ─── DECK ASSEMBLY ────────────────────────────────────────────────────────────

def _escape_text(value: str) -> str:
    return (
        (value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _read_bundled_slide_css() -> str:
    if not _BUNDLED_CSS.exists():
        raise FileNotFoundError(
            f"Bundled slide.css not found at {_BUNDLED_CSS}. "
            "Run from a checkout that includes inputs/slide_workspace_v0/."
        )
    return _BUNDLED_CSS.read_text(encoding="utf-8")


def build_deck_html(
    slides: list,  # list[SlideHTML]; typed loosely to avoid circular import
    format_mode: str = "mckinsey",
    client_css_text: str = "",
) -> str:
    """
    Assemble the full self-contained deck HTML:

    - Inlines `slide.css` and the deck-wrapper CSS inside one `<style>`.
    - Optionally appends `client_css_text` for the `client` format mode.
    - Renders a sticky top nav with anchor links to each slide.
    - Inlines every slide's `<section class="slide">` body inside a
      `.slide-shell` whose CSS transform scales the 1920×1080 section
      to fit the viewport without iframes.
    """
    base_css = _read_bundled_slide_css()
    style_blocks = [base_css, _DECK_WRAPPER_CSS]
    if format_mode == "client" and (client_css_text or "").strip():
        style_blocks.append(client_css_text)
    style_text = "\n\n".join(style_blocks)

    nav_links: list[str] = []
    cards: list[str] = []
    for i, sl in enumerate(slides, start=1):
        chapter = getattr(sl, "chapter", "") or f"Slide {i}"
        html_body = (getattr(sl, "html", "") or "").strip()
        nav_links.append(
            f'<a href="#slide-{i}">{i}. {_escape_text(chapter)}</a>'
        )
        cards.append(
            f'<section class="slide-card" id="slide-{i}">\n'
            f'  <div class="slide-label">Slide {i} — '
            f'{_escape_text(chapter)}</div>\n'
            f'  <div class="slide-shell">\n'
            f'    {html_body}\n'
            f'  </div>\n'
            f'</section>\n'
        )

    nav_html = (
        '<nav class="deck-nav">\n'
        '  <span class="deck-title">LOP DECK</span>\n'
        + "\n".join(f"  {link}" for link in nav_links)
        + "\n</nav>\n"
    )
    main_html = '<main class="deck-main">\n' + "".join(cards) + "</main>\n"

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>LoP slide deck</title>\n"
        "<style>\n"
        + style_text
        + "\n</style>\n"
        "</head>\n<body>\n"
        + nav_html
        + main_html
        + "<script>\n"
        + _DECK_SCALE_SCRIPT
        + "\n</script>\n"
        + "</body>\n</html>\n"
    )


def write_single_deck(
    target_dir: Path,
    slides: list,  # list[SlideHTML]
    format_mode: str = "mckinsey",
    client_css_text: str = "",
) -> Path:
    """
    Write the single self-contained deck file to `<target_dir>/index.html`.
    Returns the written path.
    """
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    html = build_deck_html(slides, format_mode, client_css_text)
    out = target_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
