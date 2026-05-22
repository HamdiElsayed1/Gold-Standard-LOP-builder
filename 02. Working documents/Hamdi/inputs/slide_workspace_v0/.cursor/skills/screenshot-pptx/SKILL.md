---
name: screenshot-pptx
description: >-
  Take screenshots of PowerPoint (.pptx) slides and view them as images, then
  crop and zoom into regions of interest to verify fine layout details.
  Uses COM automation on Windows to render slides to PNG via the PowerPoint
  engine. Use when you need to visually inspect a presentation, check slide
  layout, verify template output, or understand what a PPTX file looks like.
---

# Screenshot & Inspect PPTX Slides

Export PowerPoint slides to PNG images, view them with the Read tool, and
crop/zoom into regions of interest to catch layout issues that full-slide
screenshots cannot reveal.

## Prerequisites

- Windows with Microsoft PowerPoint installed
- `comtypes` and `Pillow` (installed by `python scripts/setup.py` or
  automatically on first Cursor session via the sessionStart hook)

## Quick Start

To screenshot all slides of a presentation:

```bash
python .cursor/skills/screenshot-pptx/scripts/pptx_to_png.py "path/to/file.pptx"
```

To screenshot specific slides only (1-indexed):

```bash
python .cursor/skills/screenshot-pptx/scripts/pptx_to_png.py "path/to/file.pptx" --slides 1,2
```

Output PNGs are saved to `<filename>_slides/` next to the source file by default.

## Script Reference

`scripts/pptx_to_png.py` -- export slides to PNG via PowerPoint COM.

| Argument   | Description                              | Default          |
|------------|------------------------------------------|------------------|
| `pptx`     | Path to the .pptx file (required)        | --               |
| `--slides` | Comma-separated 1-indexed slide numbers  | all slides       |
| `--outdir` | Output directory for PNGs                | `<name>_slides/` |
| `--width`  | Image width in pixels                    | 1920             |

## Typical Workflow

### 1. Export the slide(s)

**Always use `--slides`** to export only the slides you changed. Exporting
all slides wastes 5-10 seconds of COM automation time per unnecessary slide.

```bash
python .cursor/skills/screenshot-pptx/scripts/pptx_to_png.py "output.pptx" --slides 2
```

### 2. View the full-slide screenshot

Use the **Read** tool on the generated PNG files to view them:

```
Read: path/to/file_slides/slide_002.png
```

### 3. Crop and zoom regions of interest

Full-slide 1920 px screenshots compress a 33 cm-wide slide into ~1920 pixels,
making 1-2 mm overlaps invisible. **Always crop-and-zoom immediately** in the
same step as the full screenshot -- don't wait for a second round.

Combine screenshot + crop in one Python snippet to avoid multiple Shell calls:

```python
import subprocess, sys
from PIL import Image

pptx_path = sys.argv[1]
slide_nums = sys.argv[2]  # e.g. "2,3"
skill_dir = '.cursor/skills/screenshot-pptx'

subprocess.run(['python', f'{skill_dir}/scripts/pptx_to_png.py', pptx_path,
                '--slides', slide_nums], check=True)

for n in slide_nums.split(','):
    img = Image.open(f'{pptx_path.replace(".pptx","")}_slides/slide_{int(n):03d}.png')
    cropped = img.crop((x1, y1, x2, y2))
    cropped = cropped.resize((cropped.width * 2, cropped.height * 2), Image.LANCZOS)
    cropped.save(f'{pptx_path.replace(".pptx","")}_slides/crop_s{n}.png')
```

Then **Read** the cropped image to view it.

#### EMU-to-pixel conversion

A standard slide exported at 1920 px width maps EMU positions to pixels:

```
pixel_x = emu_left / 12192000 * 1920
pixel_y = emu_top  / 6858000  * 1080
```

Common crop regions on a 1920x1080 export:

| Slide area                      | Approximate pixel crop       |
|---------------------------------|------------------------------|
| Full left panel                 | `(20, 0, 750, 1080)`        |
| Value chain section (slide 2)   | `(20, 550, 750, 900)`       |
| Title area                      | `(20, 0, 800, 120)`         |
| Right panel (financials)        | `(720, 0, 1000, 1080)`      |

### 4. What to check at 2x zoom

- **Overlap**: Do labels touch or overlap dots, lines, or other shapes?
- **Footnote clearance**: Do dividers, logos, or shapes extend below the
  footnote/source line?
- **Column boundaries**: Do images/text stay within their column?
- **Alignment**: Are items in the same row at the same vertical position?
- **Spacing consistency**: Are gaps between repeated elements uniform?
- **Font rendering**: Does the font match the template (weight, size, color)?

### 5. Iterate

If issues are found, fix and re-export **only the affected slide**, then
re-crop the same region to confirm the fix rather than relying on the
full-slide view.

## Measuring EMU Positions

When you need to diagnose overlap or spacing issues, dump exact shape
positions with python-pptx:

```python
from pptx import Presentation
prs = Presentation('output.pptx')
slide = list(prs.slides)[1]

for shape in slide.shapes:
    if shape.top > AREA_TOP and shape.top < AREA_BOTTOM:
        right = shape.left + shape.width
        bottom = shape.top + shape.height
        print(f'{shape.name:30s}  L={shape.left:>8d}  R={right:>8d}  '
              f'T={shape.top:>8d}  B={bottom:>8d}')
```

Key relationships to check:
- **No overlap**: Element A's right edge < Element B's left edge (horizontal)
  or Element A's bottom < Element B's top (vertical)
- **Minimum gap**: Aim for >= 50 000 EMU (~4 pt) between unrelated elements
- **Divider clearance**: Logos should have >= 80 000 EMU (~6 pt) padding from
  divider lines on each side

## Common Pitfalls

- **Two-line labels need more vertical space** than single-line labels in the
  same-height text box. If replacing a single-line label with a two-liner,
  either reduce font size or move the text box up.
- **Wide logos in narrow columns**: Always calculate
  `max_width = column_width * 0.65` and scale the logo down if it exceeds this.
- **Aspect ratio distortion**: When resizing logos, always preserve the
  original aspect ratio. Calculate one dimension from the other:
  `new_width = int(new_height * original_width / original_height)`.

## Notes

- The script attaches to an already-running PowerPoint instance
  (`GetActiveObject`) for fast startup. It only launches a new instance as a
  fallback, and only quits that instance if it created it -- the user's
  existing PowerPoint window is never closed.
- The script uses PowerPoint's own rendering engine, so output matches what
  the user sees.
