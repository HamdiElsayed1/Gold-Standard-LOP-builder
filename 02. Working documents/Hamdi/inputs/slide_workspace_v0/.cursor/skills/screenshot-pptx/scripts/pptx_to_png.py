"""Export PowerPoint slides to PNG using COM automation.

Usage:
    python pptx_to_png.py <pptx_path> [--slides 1,2,3] [--outdir <dir>] [--width <px>]

Requires: comtypes, Microsoft PowerPoint installed on Windows.
"""

import argparse
import os
import sys
import time

def export_slides(pptx_path: str, slide_numbers: list[int] | None = None,
                  outdir: str | None = None, width: int = 1920) -> list[str]:
    pptx_path = os.path.abspath(pptx_path)
    if not os.path.isfile(pptx_path):
        print(f"Error: File not found: {pptx_path}", file=sys.stderr)
        sys.exit(1)

    if outdir is None:
        base = os.path.splitext(os.path.basename(pptx_path))[0]
        outdir = os.path.join(os.path.dirname(pptx_path), f"{base}_slides")
    os.makedirs(outdir, exist_ok=True)

    import comtypes.client

    created_new = False
    powerpoint = None
    presentation = None
    try:
        try:
            powerpoint = comtypes.client.GetActiveObject("PowerPoint.Application")
            print("Attached to running PowerPoint instance.")
        except OSError:
            powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            powerpoint.Visible = True
            powerpoint.WindowState = 2  # ppWindowMinimized
            created_new = True
            print("Started new PowerPoint instance.")

        presentation = powerpoint.Presentations.Open(
            pptx_path,
            ReadOnly=True,
            Untitled=False,
            WithWindow=False,
        )

        total = presentation.Slides.Count
        if slide_numbers is None:
            slide_numbers = list(range(1, total + 1))
        else:
            invalid = [s for s in slide_numbers if s < 1 or s > total]
            if invalid:
                print(f"Warning: slides {invalid} out of range (1-{total}), skipping.", file=sys.stderr)
                slide_numbers = [s for s in slide_numbers if 1 <= s <= total]

        slide_width = presentation.SlideMaster.Width   # in points
        slide_height = presentation.SlideMaster.Height
        height = int(width * slide_height / slide_width)

        exported: list[str] = []
        for num in slide_numbers:
            slide = presentation.Slides(num)
            out_path = os.path.join(outdir, f"slide_{num:03d}.png")
            slide.Export(out_path, "PNG", width, height)
            exported.append(out_path)
            print(f"Exported slide {num}/{total} -> {out_path}")

        return exported

    finally:
        if presentation is not None:
            try:
                presentation.Close()
            except Exception:
                pass
        if created_new and powerpoint is not None:
            try:
                if powerpoint.Presentations.Count == 0:
                    powerpoint.Quit()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="Export PPTX slides to PNG via PowerPoint COM")
    parser.add_argument("pptx", help="Path to the .pptx file")
    parser.add_argument("--slides", help="Comma-separated slide numbers (default: all)", default=None)
    parser.add_argument("--outdir", help="Output directory (default: <name>_slides/ next to the file)", default=None)
    parser.add_argument("--width", help="Image width in pixels (default: 1920)", type=int, default=1920)
    args = parser.parse_args()

    slide_numbers = None
    if args.slides:
        slide_numbers = [int(s.strip()) for s in args.slides.split(",")]

    exported = export_slides(args.pptx, slide_numbers, args.outdir, args.width)
    print(f"\nDone. {len(exported)} slide(s) exported to: {os.path.dirname(exported[0])}")


if __name__ == "__main__":
    main()
