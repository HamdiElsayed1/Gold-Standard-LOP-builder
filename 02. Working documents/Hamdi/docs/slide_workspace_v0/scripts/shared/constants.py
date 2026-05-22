"""Central contract for the HTML-PPTX harness.

Every component (compiler, importer, skills, tests) imports from here.
DO NOT modify this file during parallel development -- it is the shared
interface that all streams depend on.
"""

from __future__ import annotations

from pathlib import Path

from .emu import (
    SLIDE_HEIGHT_EMU,
    SLIDE_WIDTH_EMU,
    VIEWPORT_H,
    VIEWPORT_W,
)

# ---------------------------------------------------------------------------
# Paths (relative to the workspace root)
# ---------------------------------------------------------------------------

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_PATH = WORKSPACE_ROOT / "pptx-template.pptx"
CSS_PATH = WORKSPACE_ROOT / "css" / "slide.css"
EXTRACT_JS_PATH = WORKSPACE_ROOT / "scripts" / "extract_positions.js"


def get_template_path() -> Path:
    """Return a path to the template that python-pptx can open.

    OneDrive "cloud-only" placeholders are visible to the OS but cannot
    be opened by python-pptx's zipfile reader.  If the original path
    fails, we copy to a temp directory first.
    """
    import shutil
    import tempfile

    if TEMPLATE_PATH.stat().st_size > 0:
        try:
            import zipfile
            with zipfile.ZipFile(str(TEMPLATE_PATH), "r"):
                return TEMPLATE_PATH
        except Exception:
            pass

    tmp = Path(tempfile.gettempdir()) / "pptx-template.pptx"
    shutil.copy2(str(TEMPLATE_PATH), str(tmp))
    return tmp

# ---------------------------------------------------------------------------
# Slide layout grid
#
# Derived from the template's slide-master guides.  Guide positions are
# stored in the OOXML p15:guide extension as 1/8-point units from the
# top-left corner.
# ---------------------------------------------------------------------------

class _Zone:
    """A named rectangular zone on the slide."""

    __slots__ = ("name", "left_px", "top_px", "right_px", "bottom_px")

    def __init__(self, name: str, left_px: float, top_px: float,
                 right_px: float, bottom_px: float):
        self.name = name
        self.left_px = left_px
        self.top_px = top_px
        self.right_px = right_px
        self.bottom_px = bottom_px

    @property
    def width_px(self) -> float:
        return self.right_px - self.left_px

    @property
    def height_px(self) -> float:
        return self.bottom_px - self.top_px

    def __repr__(self) -> str:
        return (f"Zone({self.name!r}, "
                f"x={self.left_px:.0f}-{self.right_px:.0f}, "
                f"y={self.top_px:.0f}-{self.bottom_px:.0f})")


# Guide-derived constants (at 1920x1080 viewport)
LEFT_MARGIN_PX = 86.2    # guide 6: 43.125 pt = 345/8 pt
RIGHT_MARGIN_PX = 1832.2  # guide 5: 916.125 pt = 7329/8 pt
TITLE_BOTTOM_PX = 268.8   # guide 4 (orange horz): 134.375 pt
CONTENT_BOTTOM_PX = 978.0   # guide 3 (blue horz): 489.0 pt
FOOTNOTE_BOTTOM_PX = 1015.8  # guide 8 (orange horz): 507.875 pt

ZONES = {
    "title": _Zone("title",
                    left_px=LEFT_MARGIN_PX, top_px=0,
                    right_px=RIGHT_MARGIN_PX, bottom_px=TITLE_BOTTOM_PX),
    "content": _Zone("content",
                      left_px=LEFT_MARGIN_PX, top_px=TITLE_BOTTOM_PX,
                      right_px=RIGHT_MARGIN_PX, bottom_px=CONTENT_BOTTOM_PX),
    "footnote": _Zone("footnote",
                       left_px=LEFT_MARGIN_PX, top_px=CONTENT_BOTTOM_PX,
                       right_px=RIGHT_MARGIN_PX, bottom_px=FOOTNOTE_BOTTOM_PX),
    "source": _Zone("source",
                     left_px=LEFT_MARGIN_PX, top_px=FOOTNOTE_BOTTOM_PX,
                     right_px=RIGHT_MARGIN_PX, bottom_px=float(VIEWPORT_H)),
}

# ---------------------------------------------------------------------------
# Footnote / Source box positions (EMU) — from example.pptx reference
# ---------------------------------------------------------------------------

FOOTNOTE_BOX_LEFT = 553972
FOOTNOTE_BOX_TOP = 6279028
FOOTNOTE_BOX_WIDTH = 7278624
FOOTNOTE_BOX_HEIGHT = 123111

SOURCE_BOX_LEFT = 554735
SOURCE_BOX_TOP = 6501669
SOURCE_BOX_WIDTH = 7277861
SOURCE_BOX_HEIGHT = 123111

# ---------------------------------------------------------------------------
# data-pptx tag vocabulary
#
# Only HTML elements carrying one of these data-pptx values are converted
# to PPTX shapes.  Elements without data-pptx are invisible scaffolding.
# ---------------------------------------------------------------------------

PPTX_TAGS = {
    "rect",         # -> MSO_SHAPE.RECTANGLE
    "ellipse",      # -> MSO_SHAPE.OVAL
    "line",         # -> connector / line shape (SVG <line> element)
    "textbox",      # -> free-form text box
    "image",        # -> picture shape (<img> element)
    "placeholder",  # -> fills an existing layout placeholder (data-ph-idx)
    "chrome",       # -> skipped during compilation (visual reference only)
    "table",        # -> table shape (<table> element)
    "chart",        # -> native PPTX chart (JSON definition in HTML)
    "footnote",     # -> bottom-zone footnote textbox (fixed position)
    "source",       # -> bottom-zone source textbox (fixed position)
}

# Maps data-pptx values to python-pptx shape creation approach.
# The compiler uses this to dispatch shape creation.
SHAPE_TYPE_MAP = {
    "rect":        "add_shape",       # slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, ...)
    "ellipse":     "add_shape",       # slide.shapes.add_shape(MSO_SHAPE.OVAL, ...)
    "line":        "add_connector",   # slide.shapes.add_connector(MSO_CONNECTOR_TYPE.STRAIGHT, ...)
    "textbox":     "add_textbox",     # slide.shapes.add_textbox(...)
    "image":       "add_picture",     # slide.shapes.add_picture(...)
    "placeholder": "placeholder",     # slide.placeholders[idx]
    "table":       "add_table",       # slide.shapes.add_table(...)
    "chrome":      "skip",            # not converted
    "chart":       "add_chart",       # slide.shapes.add_chart(...)
    "footnote":    "add_footnote",    # fixed-position footnote textbox
    "source":      "add_source",      # fixed-position source textbox
}

# python-pptx MSO_SHAPE enum names for auto-shapes
MSO_SHAPE_NAMES = {
    "rect": "RECTANGLE",
    "ellipse": "OVAL",
}

# ---------------------------------------------------------------------------
# Template slide layouts (names as they appear in the template)
# ---------------------------------------------------------------------------

LAYOUT_NAMES = [
    "Title",       # [0] cover slide
    "Default",     # [1] standard content
    "Top Left",    # [2]
    "Mid Left",    # [3]
    "Section",     # [4] section divider
    "Quote",       # [5]
    "1/4",         # [6] left-quarter callout
    "1/3",         # [7] left-third callout
    "1/2",         # [8] half-and-half
    "2/3",         # [9] left-two-thirds
    "3/4",         # [10] left-three-quarters
    "3-line",      # [11] three-line title
    "Custom",      # [12] blank with chrome
    "End",         # [13] closing slide
]

LAYOUT_INDEX = {name: idx for idx, name in enumerate(LAYOUT_NAMES)}

# ---------------------------------------------------------------------------
# Computed styles that the extraction JS should capture
# ---------------------------------------------------------------------------

EXTRACTED_STYLE_PROPS = [
    "backgroundColor",
    "color",
    "fontFamily",
    "fontSize",
    "fontWeight",
    "fontStyle",
    "textAlign",
    "borderColor",
    "borderWidth",
    "borderStyle",
    "borderRadius",
    "opacity",
]
