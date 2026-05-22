"""Theme constants extracted from pptx-template.pptx.

Color scheme: "Custom Scheme" (theme3 -- the primary working theme).
Font scheme: Georgia (headings) / Arial (body).

The PALETTE dict holds every CSS custom property defined in css/slide.css
(:root block).  Keys use underscores matching the CSS variable names
(e.g. "navy" → var(--navy), "cyan_light" → var(--cyan-light)).
Values are hex strings WITHOUT the leading '#'.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

FONT_HEADING = "Georgia"
FONT_BODY = "Arial"

FONTS = {
    "heading": FONT_HEADING,
    "body": FONT_BODY,
}

# ---------------------------------------------------------------------------
# Guide colors (for reference only -- not used in output)
# ---------------------------------------------------------------------------

GUIDE_COLOR_BLUE = "5ACBF0"
GUIDE_COLOR_ORANGE = "F26B43"

# ---------------------------------------------------------------------------
# Full color palette  (hex strings WITHOUT the leading '#')
#
# Organised into:
#   1. Theme accent colors + tint/shade rows  (42 colours)
#   2. Custom color families from custClrLst   (37 colours)
#   3. Grays (unified theme + custom scale)    ( 9 colours)
# ---------------------------------------------------------------------------

PALETTE: dict[str, str] = {
    # -- fundamentals --
    "black":                "000000",    # dk1
    "white":                "FFFFFF",    # lt1

    # -- Accent 1: Navy (dk2 = #051C2C) -- 6 colours --
    "navy":                 "051C2C",
    "navy_lightest":        "CDD2D5",    # 80% tint
    "navy_lighter":         "9BA4AB",    # 60% tint
    "navy_light":           "697780",    # 40% tint
    "navy_dark":            "041521",    # 25% shade
    "navy_darkest":         "020E16",    # 50% shade

    # -- Accent 2: Cyan (#00A9F4) -- 6 colours --
    "cyan":                 "00A9F4",
    "cyan_lightest":        "CCEEFD",    # 80% tint
    "cyan_lighter":         "99DDFB",    # 60% tint
    "cyan_light":           "66CBF8",    # 40% tint
    "cyan_dark":            "007FB7",    # 25% shade
    "cyan_darkest":         "00547A",    # 50% shade

    # -- Accent 3: Bright Blue (#1F40E6) -- 6 colours --
    "bright_blue":          "1F40E6",
    "bright_blue_lightest": "D2D9FA",    # 80% tint
    "bright_blue_lighter":  "A5B3F5",    # 60% tint
    "bright_blue_light":    "798CF0",    # 40% tint
    "bright_blue_dark":     "1730AC",    # 25% shade
    "bright_blue_darkest":  "102073",    # 50% shade

    # -- Accent 4: Light Teal (#AAE6F0) -- 6 colours --
    "light_teal":           "AAE6F0",
    "light_teal_lightest":  "EEFAFC",    # 80% tint
    "light_teal_lighter":   "DDF5F9",    # 60% tint
    "light_teal_light":     "CCF0F6",    # 40% tint
    "light_teal_dark":      "80ACB4",    # 25% shade
    "light_teal_darkest":   "557378",    # 50% shade

    # -- Accent 5: Teal (#3C96B4) -- 6 colours --
    "teal":                 "3C96B4",
    "teal_lightest":        "D8EAF0",    # 80% tint
    "teal_lighter":         "B1D5E1",    # 60% tint
    "teal_light":           "8AC0D2",    # 40% tint
    "teal_dark":            "2D7087",    # 25% shade
    "teal_darkest":         "1E4B5A",    # 50% shade

    # -- Accent 6: Periwinkle (#AFC3FF) -- 6 colours --
    "periwinkle":           "AFC3FF",
    "periwinkle_lightest":  "EFF3FF",    # 80% tint
    "periwinkle_lighter":   "DFE7FF",    # 60% tint
    "periwinkle_light":     "CFDBFF",    # 40% tint
    "periwinkle_dark":      "8392BF",    # 25% shade
    "periwinkle_darkest":   "586280",    # 50% shade

    # -- Grays (darkness %, 0 = white, 100 = black) -- 9 colours --
    "gray_10":              "E6E6E6",
    "gray_20":              "CCCCCC",
    "gray_25":              "BFBFBF",
    "gray_30":              "B3B3B3",
    "gray_40":              "999999",
    "gray_50":              "808080",
    "gray_54":              "757575",
    "gray_60":              "666666",
    "gray_70":              "4D4D4D",

    # -- Custom palette: Electric Blue -- 6 shades --
    "electric_blue_200":    "99C4FF",
    "electric_blue_300":    "5E9DFF",
    "electric_blue_500":    "2251FF",
    "electric_blue_700":    "1537BA",
    "electric_blue_800":    "0E2B99",
    "electric_blue_900":    "061F79",

    # -- Custom palette: Cyan -- 5 shades --
    "cyan_200":             "99E6FF",
    "cyan_300":             "6ECBF7",
    "cyan_500":             "00A9F4",
    "cyan_700":             "0679C3",
    "cyan_900":             "084D91",

    # -- Custom palette: Deep Blue -- 6 shades --
    "deep_blue_200":        "82A6C9",
    "deep_blue_300":        "5380AC",
    "deep_blue_500":        "2B5580",
    "deep_blue_600":        "1B456E",
    "deep_blue_700":        "103559",
    "deep_blue_900":        "051C2C",

    # -- Custom palette: Crimson Red -- 5 shades --
    "crimson_red_300":      "F17E7E",
    "crimson_red_500":      "E33B3B",
    "crimson_red_600":      "CD3030",
    "crimson_red_700":      "B82525",
    "crimson_red_900":      "8E0B0B",

    # -- Custom palette: Marine Green -- 5 shades --
    "marine_green_300":     "75F0E7",
    "marine_green_500":     "0BDACB",
    "marine_green_600":     "10CBBC",
    "marine_green_700":     "14B8AB",
    "marine_green_900":     "108980",

    # -- Custom palette: Sand Neutral --
    "sand_neutral_300":     "E6D7BC",

    # -- Custom palette: Amber Yellow --
    "amber_yellow_500":     "FFA800",
}

PALETTE_HEX = {k: f"#{v}" for k, v in PALETTE.items()}

# Backward-compat aliases (same data, flat access for existing code)
COLORS = PALETTE
COLORS_HEX = PALETTE_HEX
