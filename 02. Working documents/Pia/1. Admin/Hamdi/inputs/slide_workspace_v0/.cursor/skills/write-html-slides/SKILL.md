---
name: write-html-slides
description: >-
  Author PowerPoint slides as native HTML using flexbox and grid layout.
  Use when creating new slides, editing slide content, or building
  presentation decks from scratch.
---

# Write HTML Slides

Author PowerPoint slides as standard HTML. Write any valid HTML/CSS —
the compiler handles converting it to native PPTX shapes.

This skill has two parts:

1. **HTML specification** — the technical contract for how slides are authored
2. **Slide design** — general layout and styling principles

---

# Part 1 — HTML Specification

## Boilerplate

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1920, height=1080">
  <link rel="stylesheet" href="css/slide.css">
</head>
<body>
<section class="slide" data-layout="Default">

  <div class="title">
    <div data-pptx="placeholder" data-ph-idx="0"
         style="position:absolute; left:1.2px; top:28.7px; width:1745.3px; height:115.2px">
      Slide Title Goes Here
    </div>
  </div>

  <div class="content">
    <!-- Your layout here -->
  </div>

  <div class="footnote">
    <p>1. Footnote text</p>
  </div>

  <div class="source">
    <p>Source: Your source</p>
  </div>

</section>
</body>
</html>
```

The `href` for `slide.css` and `chart-renderer.js` must resolve from the
HTML file's location to the workspace root. If the HTML file is at the
project root, use `css/slide.css`. If it is in a subdirectory (e.g.
`slides/`), use `../css/slide.css`. Adjust the relative path accordingly.

## Slide Structure

The zones (`.title`, `.content`, `.footnote`, `.source`) and their exact
pixel boundaries are defined in `css/slide.css` (at the workspace root).
Read that file for dimensions and positions.

**Title** — put your title text inside the placeholder. **Every template
layout has its own title position and size.** The placeholder `<div>` must
carry an inline `style` with `position:absolute` and the exact `left`,
`top`, `width`, `height` values from the template. Without this, the
compiler cannot place the title correctly in the PPTX output.

For the **Default** layout the values are:

```html
<div class="title">
  <div data-pptx="placeholder" data-ph-idx="0"
       style="position:absolute; left:1.2px; top:28.7px; width:1745.3px; height:115.2px">
    Your title text here
  </div>
</div>
```

Other layouts will have different positioning values — always copy the
exact coordinates from the template placeholder definition for the layout
you are using. Do not modify the formatting or font.

**Content area** — this is where your layout goes. Use flexbox or CSS
grid inside `.content`.

**Footnote and source** — text areas at the bottom of the slide
(see boilerplate above).

## `data-pptx` Attribute

Most elements do not need any special attributes. The `data-pptx` attribute
is required in two cases:

| Value | Purpose |
|---|---|
| `placeholder` | Fills a template placeholder (requires `data-ph-idx`) |
| `chrome` | Marks template-replica elements the compiler should skip |

## Lines

CSS borders are **not** compiled to PPTX. Use one of these instead:

**SVG line:**
```html
<svg style="position:absolute; bottom:0; left:0; width:100%; height:3px; overflow:visible;">
  <line x1="0" y1="1" x2="100%" y2="1" stroke="#000000" stroke-width="1.5"/>
</svg>
```

**Thin div with background:**
```html
<div style="position:absolute; bottom:0; left:0; width:100%; height:2px; background:#7F7F7F;"></div>
```

## Template Layouts

Set the layout on the `<section>` element: `<section class="slide" data-layout="Default">`.
Each layout has its own zone geometry, placeholder positions, and chrome.
Boilerplate templates are in [`reference/templates/`](reference/templates/).

### Available Layouts

| Layout | Index | Use-case | Template file |
|--------|-------|----------|---------------|
| Title | 0 | Cover / title slide | `title.html` |
| Default | 1 | Standard content slide | `default.html` |
| 2/3 | 9 | Content on the left 2/3, gray callout panel on the right 1/3 | `two-thirds.html` |

### Title (cover slide)

Full-bleed blue background with template branding. Only the title
placeholder is authored — subtitle, date, client logo, disclaimer,
and McKinsey logo are all template chrome rendered automatically.

The background image (`title-background.jpg` in the templates folder)
is included as a `data-pptx="chrome"` element for browser preview.
The compiler skips it; the real PPTX uses the template's own background.

```html
<section class="slide" data-layout="Title">
  <div data-pptx="chrome" style="position:absolute; top:0; left:0; width:1920px; height:1080px;">
    <img src="title-background.jpg" style="width:1920px; height:1080px;">
  </div>
  <div class="title">
    <div data-pptx="placeholder" data-ph-idx="0"
         style="position:absolute; left:0px; top:322.8px;
                width:947.5px; height:302.6px">
      <p>Presentation title goes here</p>
    </div>
  </div>
</section>
```

No `.content`, `.footnote`, or `.source` zones. White text on blue.
Adjust the `src` path for `title-background.jpg` relative to where your
HTML file lives (e.g. `../../.cursor/skills/.../title-background.jpg`).

### Default

Standard content slide with a top title bar and full-width content area.
See the [boilerplate section](#boilerplate) above for the full template.

```html
<div class="title">
  <div data-pptx="placeholder" data-ph-idx="0"
       style="position:absolute; left:1.2px; top:28.7px;
              width:1745.3px; height:115.2px">
    Slide Title
  </div>
</div>
```

### 2/3

Left 2/3 is white (title + content). Right 1/3 is a gray (#E6E6E6)
panel provided by the template. Content goes in the left 2/3; the gray
panel is for visual balance or can hold manually positioned elements.

The title and content zones are narrower than Default — they stop at
~1185 px (left margin + 1097 px).

```html
<section class="slide" data-layout="2/3">
  <div class="title">
    <div data-pptx="placeholder" data-ph-idx="0"
         style="position:absolute; left:1.0px; top:28.7px;
                width:1097.3px; height:115.2px">
      Slide Title
    </div>
  </div>
  <div class="content">
    <!-- Content here — spans the left 2/3 -->
  </div>
  <div class="source">
    <p>Source: Your source</p>
  </div>
</section>
```

## Font sizes

Specify text size in **px**. CSS `pt` does not match this viewport’s DPI, so
it will look wrong unless you convert deliberately.

**Common zones** — default sizes for the title placeholder, slide body,
footnote, and source are set in `css/slide.css` (at the workspace root).
Read those rules instead of guessing.

**Everything else** — render the slide in a browser at the slide viewport
size, **take a screenshot**, and adjust `font-size` (and `line-height` if
needed) until text fits without clipping or crowding. Repeat until the
layout looks right.

### Line Spacing

PowerPoint "100% single spacing" = CSS `line-height: 1.2` (not 1.0).
The `.slide` rule sets `line-height: 1.2` as the default.

| OOXML spacing | CSS `line-height` |
|---|---|
| 100% (single) | 1.2 |
| 115% | 1.38 |
| 150% | 1.80 |
| 200% (double) | 2.40 |

## Charts

Charts are defined declaratively as JSON inside a `data-pptx="chart"`
container. The browser renders an SVG preview; the compiler creates a
native editable PPTX chart from the same JSON.

**Required script** -- add to `<head>` (after `slide.css`):

```html
<script src="js/chart-renderer.js" defer></script>
```

Use the same relative-path logic as for `slide.css` — resolve from the
HTML file's location to the workspace root.

### Chart container

```html
<div data-pptx="chart" style="width:800px; height:500px;">
  <script type="application/json">
  {
    "type": "bar_stacked",
    "categories": ["2022", "2023", "2024"],
    "series": [
      { "name": "Revenue", "values": [100, 120, 150], "color": "#061F79" },
      { "name": "Cost",    "values": [80, 90, 110],   "color": "#1F40E6" }
    ]
  }
  </script>
</div>
```

Size the container with inline `width`/`height` or CSS. The chart fills
the container. Position the container inside `.content` using normal
flexbox/grid layout.

### Chart types

| JSON `type` | PPTX chart | Orientation | Use-case |
|---|---|---|---|
| `column_stacked` | Stacked column | Vertical | Present categorical data |
| `bar_stacked` | Stacked bar | Horizontal | Present categorical data when there are too many categories to fit a horizontal column chart |


More types will be added. The `type` value maps directly to a
`python-pptx` `XL_CHART_TYPE` enum.

### JSON schema

```
type            : string    -- chart type (see table above)
categories      : string[]  -- category labels
series[]        : object[]  -- one per data series
  .name         : string    -- series name (legend label)
  .values       : number[]  -- one value per category
  .color        : string    -- CSS hex color for the series fill
dataLabels?     : object
  .show         : boolean   -- default false
  .numberFormat : string    -- e.g. "0", "0.0", "0%"
  .fontColor    : string    -- hex color (default "#FFFFFF")
  .fontSize     : number    -- in pt (default 28)
totalLabels?    : object
  .show         : boolean   -- default true when multiple series
  .numberFormat : string    -- e.g. "0" (default "0")
  .fontColor    : string    -- hex color (default "#000000")
  .fontSize     : number    -- in px (default 28)
valueAxis?      : object
  .visible      : boolean   -- default false
  .max          : number?   -- null = auto
  .min          : number?   -- default 0
  .numberFormat : string
  .gridlines    : boolean   -- default false
gapWidth?       : number    -- gap between bar groups, % (default 150)
```

### Chart legends

Legends are **not** part of the chart JSON. Author them as explicit HTML
elements (colored `<div>` boxes + text `<span>` labels) placed above or
beside the chart. The compiler auto-detects these as separate PPTX
shapes -- no `data-pptx` attribute is needed. A legend is not needed if there is only one series and the subtitle explains the series sufficiently well.

**Right-aligned legend row** (place next to the subtitle):

```html
<div style="display:flex; justify-content:space-between; align-items:flex-end;">
  <div style="position:relative; padding-bottom:8px; flex:1;">
    <p style="font-size:28px;"><strong>Chart title</strong>, unit</p>
    <div style="position:absolute; bottom:0; left:0; width:100%; height:2px; background:#7F7F7F;"></div>
  </div>
  <div style="display:flex; gap:16px; padding-bottom:12px; margin-left:24px;">
    <div style="display:flex; align-items:center; gap:6px;">
      <div style="width:12px; height:12px; background:#061F79;"></div>
      <span style="font-size:20px; color:#000000;">Series A</span>
    </div>
    <div style="display:flex; align-items:center; gap:6px;">
      <div style="width:12px; height:12px; background:#1F40E6;"></div>
      <span style="font-size:20px; color:#000000;">Series B</span>
    </div>
  </div>
</div>
```

Each colored `<div>` becomes a filled rectangle and each `<span>` becomes
a textbox in the PPTX output. Repeat the swatch + label pair for every
series. Match the `background` color to the series `color` in the chart
JSON.

### Category labels

Category labels are always authored as **external HTML** elements beside
the chart. The SVG preview does not draw category tick text inside the
chart, and the compiler hides native category tick labels in PPTX
(`tick_label_position = NONE`). **`categories[]` is still required** in
JSON so series data and the PPTX workbook match PowerPoint.

Author category names as normal HTML beside the chart; they compile to
separate text boxes like any other body text.

#### `data-chart-labels` — automatic label positioning

Add a **`data-chart-labels`** attribute to a sibling container of the
chart (sharing the same parent). Put one `<div>` child per category
inside it. The chart renderer (`chart-renderer.js`) automatically
positions each child to align with the corresponding bar or column
after rendering the SVG, so labels align pixel-perfectly regardless of
`gapWidth` or category count.

- **`bar_stacked`** — label container goes **to the left** of the chart;
  each child is positioned at the vertical center of the corresponding bar.
- **`column_stacked`** — label container goes **below** the chart;
  each child is positioned at the horizontal center of the corresponding
  column.

**Horizontal bar (`bar_stacked`) example:**

```html
<div style="display:grid; flex:1; min-height:0; column-gap:14px;
            grid-template-columns:minmax(0,22%) minmax(0,1fr)">
  <div data-chart-labels style="min-width:0; font-size:20px">
    <div>North America</div>
    <div>Europe</div>
    <div>Asia Pacific</div>
  </div>
  <div data-pptx="chart" style="min-width:0; min-height:0">
    <script type="application/json">
    { "type": "bar_stacked", ... }
    </script>
  </div>
</div>
```

**Vertical column (`column_stacked`) example:**

```html
<div style="display:flex; flex-direction:column; flex:1; min-height:0">
  <div data-pptx="chart" style="flex:1; min-height:0">
    <script type="application/json">
    { "type": "column_stacked", ... }
    </script>
  </div>
  <div data-chart-labels style="font-size:22px">
    <div>2021</div>
    <div>2022</div>
    <div>2023</div>
  </div>
</div>
```

No CSS layout properties are needed on the label children — the
renderer handles all positioning via absolute placement within the
container.

**Sync:** Label count and **order** must match `categories[]`. Use
`<div>` children (not `<li>`), since `<li>` elements are detected as
bullet paragraphs in the PPTX output.

### Chart slide conventions

Chart slides follow a standard layout:

1. **Subtitle above the chart** with a description and unit, with a
   divider line underneath. Use the existing subtitle pattern:

```html
<div style="position:relative; padding-bottom:8px;">
  <p style="font-size:28px;"><strong>Revenue by region</strong>, USD millions</p>
  <div style="position:absolute; bottom:0; left:0; width:100%; height:2px; background:#7F7F7F;"></div>
</div>
```

2. **No value axis** -- do not show the value axis, its labels, or
   gridlines by default. The data labels and total labels communicate
   the values.

3. **No tick marks** -- never include tick marks on either axis.

4. **Total labels** -- when a chart has multiple stacked series, show
   the stack total at the end of each bar/column. This is on by default.

5. **Legend above the chart, right-aligned** -- author the legend as
   explicit HTML (colored `<div>` swatches + `<span>` labels) next to the
   subtitle. See **Chart legends** above for the pattern.

6. **Category labels** -- author as **external HTML labels** with a
   `data-chart-labels` container (see **Category labels** above). The
   chart renderer positions labels automatically.

7. **Full content width** -- the chart + label layout should span the full
   `.content` area width (e.g. a flex row: label column + chart).

8. **Data labels** -- if there is only one series of data do not use regular data tables. Use only total labels for a cleaner look.

### Examples

- [`reference/examples/stacked-bar-chart.html`](reference/examples/stacked-bar-chart.html) — horizontal bar chart with external labels
- [`reference/examples/chart-with-commentary.html`](reference/examples/chart-with-commentary.html) — vertical column chart with commentary

## Anti-Patterns

| Anti-pattern | Correct approach |
|---|---|
| `<table>` elements | Build tables from `<div>` elements with CSS Grid |
| CSS `border-bottom` for divider lines | Thin `<div>` with `background` or SVG `<line>` |
| Text outside `<p>` or `<li>` in a multi-paragraph shape | Wrap each paragraph in `<p>` |
| `<line>` outside `<svg>` | Always nest inside an `<svg>` container |
| Fixed padding that overflows the content area | Use `align-content: space-between` or `1fr` rows |
| Modifying title formatting or dimensions | Leave the title placeholder as-is |

---

# Part 2 — Slide Design

General principles for creating well-structured, professional slides.

## Content Area Usage

- **Fill the full content width.** Layouts should span the entire
  `.content` area. Do not leave large unused margins inside it. See
  `css/slide.css` (at the workspace root) for the exact dimensions.
- **Stay within the content area.** Content should remain inside the
  `.content` zone. Only extend above it in exceptional circumstances
  (e.g., a legend placed beside the title).
- **Avoid stacked layouts.** Multiple subsections of a slide should primarily be next to each other on a slide instead of stacked on top of each other.

## Element Styling

- **No rounded corners on rectangles.** Do not apply `border-radius` to rectangles, cells, or containers. Rectangular element should have sharp corner. Elliptical and circular shapes are allowed.
- **Limit use of various coloring.** Do not use various colors on different shapes to highlight variety within a category. Different colors are reserved for highlighting different things without ambiguity. Primarily use the electric-blue-900 color for highlighting and secondarily the cyan-lightest color.
- **Subtitles have no background and a line underneath.** When a slide has section subtitles or column headers, render them as plain text (no background color) with a thin divider line directly below:

```html
<div style="position:relative; padding-bottom:8px;">
  <p style="font-size:28px;"><strong>Section heading</strong></p>
  <div style="position:absolute; bottom:0; left:0; width:100%; height:2px; background:#7F7F7F;"></div>
</div>
```

- **Level underlines on side-by-side subtitles.** When two subtitles sit
  next to each other (e.g. in a two-column layout), their underlines must
  be at the same vertical position. If one subtitle wraps to two lines and
  the other stays on one line, bottom-anchor both so the divider lines
  align. Use `display:flex; flex-direction:column; justify-content:flex-end`
  on the subtitle wrapper so the text is pushed to the bottom:

```html
<!-- Two-column subtitle row with level underlines -->
<div style="display:flex; gap:24px; align-items:flex-end;">
  <div style="flex:1; position:relative; padding-bottom:8px;">
    <p style="font-size:28px;"><strong>Short title</strong></p>
    <div style="position:absolute; bottom:0; left:0; width:100%; height:2px; background:#7F7F7F;"></div>
  </div>
  <div style="flex:1; position:relative; padding-bottom:8px;">
    <p style="font-size:28px;"><strong>Longer title that wraps to two lines</strong></p>
    <div style="position:absolute; bottom:0; left:0; width:100%; height:2px; background:#7F7F7F;"></div>
  </div>
</div>
```

## Font Colors

- **Only use black and white for text.** Never apply any other font color.
  Use `#000000` (black) or `#FFFFFF` (white) only.
  Do not use grey, blue, red, or any other color for body text, labels,
  or headings. Use background fills, shapes, and layout to create visual
  hierarchy — not font color.

## Numbered Step Indicators

Use **circles** (not squares) for numbered step indicators. The text
inside should be **center-aligned** both horizontally and vertically.
`border-radius: 50%` compiles to an oval auto-shape in PPTX.

```html
<div style="width:32px; height:32px; border-radius:50%; background:#061F79;
            display:flex; align-items:center; justify-content:center;
            text-align:center; flex-shrink:0;">
  <span style="font-size:18px; color:#FFFFFF; font-weight:bold;">1</span>
</div>
```

For larger icons (e.g. criteria cards), use `48px` × `48px` with
`font-size: 24px`. Always pair the circle with adjacent text in a
`display:flex; gap:12px` row.

## Rating Labels

When showing a colored dot + rating word (e.g. "Strong", "Weak",
"Moderate"), always set **`white-space: nowrap`** on the label container
so the rating text never wraps mid-word in narrow PPTX text boxes:

```html
<span style="display:inline-flex; align-items:center; gap:8px;
             font-size:22px; white-space:nowrap;">
  <span style="width:14px; height:14px; background:#0BDACB; flex-shrink:0;"></span>
  Strong
</span>
```

## Two-Section Layouts

- **Always place two sections side by side, never stacked.** The human
  eye reads top-to-bottom first, then left-to-right. If a secondary
  section (e.g. "Next steps") is placed below the main content, the
  reader encounters it before finishing the primary section to its right.
  Always split such layouts into left and right columns so the reader
  finishes one column before moving to the next:

```html
<!-- Correct: two sections side by side -->
<div style="display:flex; gap:24px; flex:1;">
  <div style="flex:1;"><!-- Main content --></div>
  <div style="flex:1;"><!-- Secondary content / next steps --></div>
</div>
```

## Row-Based Layouts

Slides frequently use a tabular or row-based format — comparison tables,
scorecard rows, feature matrices. When laying out rows vertically, use
one of two strategies:

**Equal distribution of white space** (preferred for varied content):

```css
.content {
  align-content: space-between !important;
}
```

Each row sizes to fit its content. `space-between` distributes the
remaining vertical space into equal gaps between rows, giving symmetric
whitespace throughout the slide.

**Equal-height rows** (for uniform content density):

```css
.content {
  grid-template-rows: repeat(N, 1fr) !important;
}
```

Every row gets the same height regardless of content size.

### Tabular slides — alignment within rows

For div-and-grid “tables” (column headers + data rows, scorecards, etc.),
separate **vertical alignment**, **text alignment**, and **indicator
alignment**:

- **Middle-align rows vertically.** On each **row** (a grid container),
  set `align-items: center` so cells of different height (e.g. one-line
  product name vs multi-line “Key drivers”) share a common vertical
  centerline. If each cell is `display: flex`, keep `align-items: center`
  on the cell as well so content sits in the middle of the row band.
- **Left-align text inside its cell.** Use `justify-content: flex-start`
  and `text-align: left` on cells that hold titles, numbers, or
  paragraphs. Column headers in a header row should use **left** text
  alignment too, unless the visual design explicitly calls for centered
  headers.
- **Center glyphs only in their own track.** For number + bubble (or
  similar) columns, lay out as a **row flex**: fixed or intrinsic width
  for the **text**, then a child that **grows** (`flex: 1`) with
  `display: flex; justify-content: center; align-items: center` so dots,
  bubbles, or icons stay **centered in the remaining column width** —
  not centered across the full column over the number.
- **Bullet / description columns.** Prefer `text-align: left` on the
  whole cell. Centering cell text often breaks custom bullet
  `::before` layouts; full-width left-aligned lists usually match firm
  style and compile predictably.

### Tabular slides — column headers

- **Bottom-align the header row.** When some column titles wrap to two
  lines and others stay one line, use `align-items: end` (not `center`)
  on the **header** grid row so every header sits on the same baseline
  at the bottom of the row. Data rows can still use `align-items: center`
  as in **Tabular slides — alignment within rows** above.
- **Avoid a double gap above the first data row when using
  `align-content: space-between`.** CSS Grid treats each direct child of
  `.content` as its own row. If the column-header row,
  the horizontal rule under it, and the first data row are **separate**
  children, `space-between` injects slack **between each pair**, so the
  gap above the first line of data looks twice as large as intended.
  Wrap the header row **and** the divider (`.sep` or thin rule `div`) in
  a single full-width wrapper (for example `grid-column: 1 / -1` with
  `display: flex; flex-direction: column`) so that block is **one** grid
  item; only then does extra vertical space sit between the header block
  and the first data row.
- **Tighten the header band** by keeping `padding-bottom` on the header
  row small or zero once the rule sits directly under the text.

## Reference

- [`reference/examples/tabular-grid.html`](reference/examples/tabular-grid.html) — Tabular grid (see **Tabular slides — alignment within rows** and **Tabular slides — column headers** above)
