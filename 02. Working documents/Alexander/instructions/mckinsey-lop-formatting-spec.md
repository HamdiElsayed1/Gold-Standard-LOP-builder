# McKinsey-style LoP formatting (PDF-first + HTML)

**Purpose:** Single reference so HTML exports and PowerPoint LoPs **visually align** with the gold example. **Canonical look-and-feel** is the **exported PDF** (what clients and reviewers actually see when not in edit mode). The **PPTX** remains the best source for **theme hex**, **exact point sizes**, **bullet ladder metrics**, and **think-cell** structure.

**Important:** This file **does not** replace Visual Identity / template governance. Use **approved** firm templates, logos, and disclaimers from your official channels or pursuit-specific boilerplate. Do **not** paste legal or confidentiality language into drafts unless it comes from an **explicitly approved** source for that pursuit.

---

## Source hierarchy

| Priority | File | Use for |
|----------|------|--------|
| **1 — Visual truth** | `01. Background material/928635 Gold Standard Asset-enabled Commercial IDP  GEM LOP Guide.pdf` | Overall appearance, spacing impression, **embedded fonts**, page size, **cover strip + title cluster**, footer behavior when flattened |
| **2 — Structure / tokens** | `01. Background material/928635 Gold Standard Asset-enabled Commercial IDP  GEM LOP Guide.pptx` | **sRGB** palette (`theme1.xml`), **OOXML font sizes**, bullet **EMU** indents, slide master layout names, think-cell objects |

**PDF generation (reproducible on this machine):** Microsoft PowerPoint **16.108.1** (macOS) → **Save as PDF** from the `.pptx` above. Re-export after material template changes so HTML/CSS targets stay aligned.

---

## 1. PDF technical profile (measured export)

| Property | Value |
|----------|--------|
| **Path** | `01. Background material/928635 Gold Standard Asset-enabled Commercial IDP  GEM LOP Guide.pdf` |
| **Page count** | **23** (matches slide count in source deck) |
| **MediaBox** | **960 × 540 pt** per page → **16:9** (this is **13.333″ × 7.5″** at **72 pt/in**, i.e. standard widescreen slide width/height expressed in points) |
| **Vector vs raster** | Text remains selectable; fonts are **embedded** subsets (names below) |

### 1.1 Fonts embedded in the PDF (flattened output)

Subset prefixes (`AAAA+`, etc.) are omitted below—these are the **actual faces** the PDF carries:

| Face | Typical role in this deck |
|------|---------------------------|
| **Georgia-Bold** | Slide / section titles (no separate “Georgia” regular subset appears in the PDF—titles render as **bold Georgia**) |
| **ArialMT** | Body text, labels, footers |
| **Arial-BoldMT** | Bold emphasis inside body |
| **Arial-ItalicMT** | Italics (quotes, emphasis) |
| **Wingdings-Regular** | Icon / bullet glyphs (nested bullet styling) |

**Implication for HTML/CSS:** Use `font-family: Georgia, serif; font-weight: 700` for titles (not Georgia 400). Body stack: `Arial, Helvetica, sans-serif` with `font-weight` / `font-style` as needed.

**Note:** The PPTX slide master still references **Segoe UI** for first-level bullet font metadata; the **exported PDF** does not embed Segoe—flattening resolves body copy to **Arial**. When matching **PPT edit mode**, defer to PPTX; when matching **PDF / read-only**, defer to **Arial** as above.

### 1.2 Cover page (PDF page 1) — structure

Text extraction from the export confirms this **order of elements** (exact legal wording lives **only** in the PDF—pull from there or from your pursuit boilerplate folder):

1. **Top strip:** confidential / proprietary / © notice block (multi-line in PDF).
2. **Date line** (e.g. month/year) and **“Discussion document”** style descriptor.
3. **Main title** cluster (GEM / LoP framing in the example).

**HTML:** Reserve a **narrow top band** (small **Arial** text, **tight line-height**) for that strip; populate from **approved** snippets only—never invent legal text.

### 1.3 Footer / slide label (inner pages)

Extracted text shows **“McKinsey & Company”** on section and content pages, with **slide numbers** adjacent in the same text flow (e.g. title pages combine label + number when copy-pasted). In layout terms: **firm name bottom-right**, **page/slide index** on the **left** or integrated per template—**verify by eye on the PDF** for pixel placement.

---

## 2. Slide geometry (PPTX + PDF)

| Item | PPTX (DrawingML) | PDF export |
|------|------------------|------------|
| Aspect ratio | **16:9** | **16:9** |
| Native slide | `cx="12192000"` × `cy="6858000"` EMU → **13.333″ × 7.5″** | **960 × 540 pt** (= same aspect at 72 pt/in) |
| HTML/CSS | `aspect-ratio: 16 / 9`; scale width to viewport; preserve margins **proportionally** to PDF | Match **relative** padding to PDF screenshot at 100% zoom |

---

## 3. Color system (PPTX `theme1.xml`; verify visually on PDF)

PDF streams are **compressed**; reliable **hex** values are read from the **PPTX theme**. Always **spot-check** charts and blue fills against the **PDF** (display calibration can shift appearance).

**Core mapping (`clrMap` on slide master):** `bg1` → white, `tx1` → body text (**#000000** on white slides).

**Theme accents (sRGB hex):**

| Role | Hex | Notes |
|------|-----|--------|
| Accent 1 (primary blue) | **#061F79** | Headline bars, key shapes |
| Accent 2 | **#00A9F4** | Bright cyan-blue |
| Accent 3 | **#2251FF** | Electric blue 500 |
| Accent 4 | **#99E6FF** | Light aqua |
| Accent 5 | **#0679C3** | Mid blue |
| Accent 6 | **#75F0E7** | Mint / marine highlight |

**Neutrals (named in theme):** Gray 10% **#E6E6E6** · Gray 20% **#CCCCCC** · Gray 30% **#B3B3B3** · Gray 54% **#757575** · Gray 70% **#4D4D4D** · Deep Blue 900 **#051C2C**

**Usage:** Body on white **#000000**; primary chrome **#061F79**; supporting type **#4D4D4D**–**#757575**; light panels **#E6E6E6** / **#CCCCCC** sparingly.

---

## 4. Typography (PPTX measurements + PDF font faces)

OOXML `sz` = hundredths of a point → **÷ 100** for pt. **Weights** below align with **PDF-embedded** faces.

| Element | PDF face | PPTX / notes |
|---------|-----------|----------------|
| **Slide title** | Georgia-Bold | Georgia, **25 pt**, bold; title style line spacing **93%** |
| **Body** | ArialMT (+ Bold / Italic variants) | **16 pt**, 1.0 line spacing, **3 pt** before/after paragraphs (`spcBef`/`spcAft` = 300) |
| **Footer** | ArialMT | **9 pt**, black, bottom **right** |
| **Footnote / source** | ArialMT | **8 pt** region in master |
| **Cover hero** | Georgia-Bold | Sample cover uses **large** white-on-blue Georgia (e.g. **44 pt** in `slide1.xml`) |
| **Default outline** | — | `presentation.xml` default **18 pt** for generic outline |

**CSS:** `font-kerning: normal`; do not add artificial letter-spacing unless matching a measured export.

---

## 5. Bullet ladder (PPTX `slideMaster1.xml` → `bodyStyle`)

Use the PPTX for **exact** indent/bullet characters; use the PDF for **how it reads** once flattened (Arial + Wingdings).

| Level | Bullet font (PPTX) | Character | `marL` (EMU) | `indent` (EMU) |
|-------|---------------------|-----------|-------------|----------------|
| 1 | Segoe UI (PPTX) / **Arial in PDF** | (template) | 0 | 0 |
| 2 | Wingdings | template glyph | 228600 | −225425 |
| 3 | Arial | **—** | 515938 | −287338 |
| 4 | Arial | **»** | 742950 | −182563 |
| 5 | Arial | **›** | 914400 | −136525 |
| 6–9 | Arial | **▫** | 1085850 | −171450 |

**EMU → CSS (96 px/in):** multiply EMU by **96 / 914400**.

**HTML:** Semantic `<ul><li>`; optional `::before` for PPT parity; keep accessible contrast.

---

## 6. Slide chrome & layout

- **Background:** white.
- **Blue structural fills:** **#061F79** (accent1).
- **Title:** left-aligned **Georgia bold** band with **#061F79** underline / bar per layout.
- **Body:** **Arial** block.
- **Charts / think-cell:** Present in PPTX; in PDF they are **flattened**—for HTML, prefer **static images** cut from PDF or re-exported PNG/SVG from PPT.

---

## 7. Narrative patterns (PDF + PPTX)

- **Numbered section heads** (e.g. “1. …”) with bold theme labels.
- **Pull quotes:** italic **Arial** body with attribution in **#4D4D4D** (verify on PDF).
- **Sources:** small grey **8–10 pt** under exhibits.

---

## 8. HTML/CSS checklist (PDF-aligned)

1. **Title:** `font-family: Georgia, serif; font-weight: 700;` (matches **Georgia-Bold** in PDF).
2. **Body / footer:** `Arial, Helvetica, sans-serif`.
3. **Variables:** `--mck-accent1: #061F79;` `--mck-text: #000;` `--mck-gray-70: #4D4D4D;` `--mck-gray-10: #E6E6E6;`
4. **Slide:** `aspect-ratio: 16 / 9`; white background; **proportional** padding—tune against **PDF at 100% zoom**.
5. **Cover:** blue panel + white **Georgia 700**; **confidential strip** = approved copy only.
6. **Charts:** PDF screenshot or image export, not live think-cell.

---

## 9. Other Background material

| File | Role |
|------|------|
| `928635 … GEM LOP Guide.pdf` | **Primary** visual reference (this doc) |
| `928635 … GEM LOP Guide.pptx` | **Secondary** token / master reference |
| Other `.pptx` / `.pdf` in `01. Background material/` | Optional alternates—re-export PDF when adopting a new template |

---

## 10. Related project paths

- LoP chapter spine: `.cursor/rules/lop-builder-workflow.mdc`
- HTML workflow: `02. Working documents/Jasper/lop-workflow-overview.html`, `lop-cursor-runbook.md`

---

## 11. Live preview

Open **`mckinsey-lop-formatting-preview.html`** (same folder). Tune spacing against **`928635 … GEM LOP Guide.pdf`** side-by-side.
