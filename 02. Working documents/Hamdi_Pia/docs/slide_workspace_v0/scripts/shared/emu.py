"""EMU / pixel / point conversion utilities.

PowerPoint uses English Metric Units (EMU) internally.
  1 inch  = 914400 EMU
  1 point = 12700 EMU
  1 cm    = 360000 EMU

The HTML slides are rendered at a fixed viewport of 1920x1080 pixels,
which maps to the full slide area of 12192000 x 6858000 EMU.
"""

from __future__ import annotations

SLIDE_WIDTH_EMU = 12_192_000
SLIDE_HEIGHT_EMU = 6_858_000
VIEWPORT_W = 1920
VIEWPORT_H = 1080

EMU_PER_INCH = 914_400
EMU_PER_PT = 12_700
EMU_PER_CM = 360_000

_PX_TO_EMU_X = SLIDE_WIDTH_EMU / VIEWPORT_W   # 6350.0
_PX_TO_EMU_Y = SLIDE_HEIGHT_EMU / VIEWPORT_H  # 6350.0

# Viewport effective DPI: slide is 13.333 inches wide at 1920 px → 144 DPI.
# CSS assumes 96 DPI for pt/in units, so a PPTX point appears smaller in the
# browser by a factor of 96/144 = 2/3.  To compensate, font sizes must be
# emitted in px using these helpers.
VIEWPORT_DPI = VIEWPORT_W / (SLIDE_WIDTH_EMU / EMU_PER_INCH)  # 144.0
PT_TO_CSS_PX = VIEWPORT_DPI / 72  # 2.0  (1 PPTX-pt = 2 CSS-px on our viewport)
CSS_PX_TO_PT = 72 / VIEWPORT_DPI  # 0.5  (1 CSS-px = 0.5 PPTX-pt)


def px_to_emu_x(px: float) -> int:
    """Convert horizontal pixels (at 1920px viewport) to EMU."""
    return round(px * _PX_TO_EMU_X)


def px_to_emu_y(px: float) -> int:
    """Convert vertical pixels (at 1080px viewport) to EMU."""
    return round(px * _PX_TO_EMU_Y)


def px_to_emu(px: float, axis: str = "x") -> int:
    """Convert pixels to EMU along the given axis ('x' or 'y')."""
    if axis == "x":
        return px_to_emu_x(px)
    return px_to_emu_y(px)


def emu_to_px_x(emu: int) -> float:
    """Convert EMU to horizontal pixels (at 1920px viewport)."""
    return emu / _PX_TO_EMU_X


def emu_to_px_y(emu: int) -> float:
    """Convert EMU to vertical pixels (at 1080px viewport)."""
    return emu / _PX_TO_EMU_Y


def emu_to_px(emu: int, axis: str = "x") -> float:
    """Convert EMU to pixels along the given axis ('x' or 'y')."""
    if axis == "x":
        return emu_to_px_x(emu)
    return emu_to_px_y(emu)


def pt_to_emu(pt: float) -> int:
    """Convert points to EMU."""
    return round(pt * EMU_PER_PT)


def emu_to_pt(emu: int) -> float:
    """Convert EMU to points."""
    return emu / EMU_PER_PT


def inches_to_emu(inches: float) -> int:
    """Convert inches to EMU."""
    return round(inches * EMU_PER_INCH)


def emu_to_inches(emu: int) -> float:
    """Convert EMU to inches."""
    return emu / EMU_PER_INCH


def pt_to_css_px(pt: float) -> float:
    """Convert PPTX points to CSS pixels at viewport DPI (144)."""
    return pt * PT_TO_CSS_PX


def css_px_to_pt(px: float) -> float:
    """Convert CSS pixels (at viewport DPI) back to PPTX points."""
    return px * CSS_PX_TO_PT
