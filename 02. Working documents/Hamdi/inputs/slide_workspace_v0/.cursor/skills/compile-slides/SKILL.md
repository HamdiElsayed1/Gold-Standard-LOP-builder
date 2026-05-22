---
name: compile-slides
description: >-
  Compile HTML slides to a native PowerPoint file. Renders HTML in a
  headless browser, extracts element positions, and creates PPTX shapes
  on the firm template. Use after authoring slides with write-html-slides.
---

# Compile HTML to PPTX

Dependencies are installed into `.venv/` at the workspace root. Setup
runs automatically on first Cursor session (via the sessionStart hook)
or manually with `python scripts/setup.py`.

## Quick start

Single slide:

```bash
compile-slides slide.html -o output.pptx
```

Directory of slides (one `.html` per slide, sorted alphabetically for slide order):

```bash
compile-slides slides/ -o deck.pptx
```

## CLI reference

```
compile-slides <input> [-t <template>] [-o <output.pptx>]

positional arguments:
  input               Path to a .html file or directory of .html files

options:
  -t, --template      PPTX template path (default: bundled pptx-template.pptx)
  -o, --output        Output PPTX path (default: output.pptx)
```

## How it works

1. **Playwright renders** each HTML file at a 1920 x 1080 viewport with Chromium in headless mode.
2. **`extract_positions.js`** runs inside the page and auto-detects visible elements in two passes:
   - **Pass 1 (visual shapes):** Elements with background colors, borders, `<img>` tags, `<line>` inside `<svg>`, and `<table>` elements. High `border-radius` (≥ 40% of the smaller dimension) classifies as ellipse; otherwise rectangle.
   - **Pass 2 (text shapes):** Remaining elements whose children are all inline or paragraph-forming become textboxes. Layout containers (divs with child divs) are skipped.
   - Elements with `data-pptx="placeholder"` fill template placeholders; `data-pptx="chrome"` marks elements to skip.
   - Explicit `data-pptx` values override auto-detection when needed.
   - Extracts bounding rects, computed styles, text runs (with `<sup>`/`<sub>` support), image sources, table data, and the slide's `data-layout` value. Marks `<li>` paragraphs with `bullet: true`.
3. **`html_to_pptx.py`** iterates over the extracted shapes and creates native PPTX objects via python-pptx:

   | Shape tag | PPTX result |
   |---|---|
   | `rect` | Rectangle auto-shape |
   | `ellipse` | Oval auto-shape |
   | `line` | Straight connector (from SVG `<line>`) |
   | `textbox` | Free-form text box |
   | `image` | Picture shape (resolves `src` relative to the HTML file) |
   | `placeholder` | Fills an existing layout placeholder by `data-ph-idx` |
   | `table` | Table shape |
   | `chrome` | Skipped (visual reference only) |

4. Pixel positions convert to EMU with `px * 6350` (both axes at 1920 x 1080).
5. Font sizes convert from CSS px to PPTX pt via `px * 0.5 = pt` (the viewport's 144 DPI means `PPTX pt * 2 = CSS px`). Border/stroke widths use the same factor.
6. Bullet paragraphs (from `<li>` elements inside `<ul data-bullet-char>`) are converted to PPTX paragraphs with explicit `buChar` bullet formatting.
7. The output `.pptx` is saved with one slide per input HTML file.

## Template handling

The compiler uses the bundled `pptx-template.pptx` by default. Override with `-t`:

```bash
compile-slides slides/ -t custom_template.pptx -o deck.pptx
```

The template's slide layouts are selected per-slide using the `data-layout` attribute on `<section class="slide">`. Available layouts:

| Index | Name |
|---|---|
| 1 | Default |

If `data-layout` is missing, layout `1` (Default) is used.

## Troubleshooting

### Shapes missing from the output

The compiler auto-detects visible elements (backgrounds, images, text, lines). Layout scaffolding (flexbox containers, grid wrappers) is intentionally skipped. If an element is missing, check that:
- It has visible content (text, background, border, or is an `<img>`/`<table>`/`<line>`)
- It is not nested inside a parent that was already detected as a shape
- CSS borders are **not** auto-detected -- use a thin `<div>` with `background` or an SVG `<line>` for divider lines
- You can add an explicit `data-pptx` attribute to force detection if auto-detection misclassifies

### Position drift / elements misaligned

The compiler renders at exactly 1920 x 1080. If your HTML uses a different viewport (e.g. `<meta name="viewport" content="width=device-width">`), positions will not match. Ensure the slide HTML uses `<meta name="viewport" content="width=1920">` and links `css/slide.css`.

### Images not found in output

Image `src` paths are resolved relative to the HTML file's directory. If you pass `slides/slide_001.html` and it references `images/chart.png`, the file must exist at `slides/images/chart.png`.
