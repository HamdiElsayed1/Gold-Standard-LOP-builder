"""Compress PDF files using PyMuPDF (re-save with deflate, garbage collection, optional font subsetting)."""

from __future__ import annotations

import sys
from pathlib import Path


def require_fitz():  # pragma: no cover - import guard
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise SystemExit(
            "PDF compression requires PyMuPDF. Install with:\n"
            '  pip install "lop-workflow[compress]"\n'
            "or: pip install pymupdf"
        ) from e
    return fitz


def compress_pdf_file(
    src: Path,
    dest: Path,
    *,
    strong: bool = False,
) -> tuple[int, int]:
    """
    Rewrite ``src`` to ``dest`` with stream compression and cleanup.

    Returns ``(bytes_in, bytes_out)`` after writing ``dest``.
    """
    fitz = require_fitz()
    src = src.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    size_in = src.stat().st_size
    doc = fitz.open(src)
    try:
        if strong:
            try:
                doc.subset_fonts()
            except Exception:
                # Older PDFs or subset-unfriendly fonts — skip
                pass
        doc.save(
            dest.as_posix(),
            garbage=4,
            deflate=True,
            clean=True,
            deflate_images=True,
            deflate_fonts=True,
        )
    finally:
        doc.close()
    size_out = dest.stat().st_size
    return size_in, size_out


def collect_pdf_paths(inputs: list[str], *, recursive: bool) -> list[Path]:
    """Expand files and directories into a sorted list of PDF paths."""
    out: list[Path] = []
    for raw in inputs:
        p = Path(raw).expanduser()
        if not p.exists():
            print(f"warning: skip missing path: {raw}", file=sys.stderr)
            continue
        if p.is_dir():
            gen = p.rglob("*.pdf") if recursive else p.glob("*.pdf")
            out.extend(sorted(gen))
        elif p.suffix.lower() == ".pdf":
            out.append(p)
        else:
            print(f"warning: not a PDF or folder: {raw}", file=sys.stderr)
    # de-dupe preserve order
    seen: set[Path] = set()
    unique: list[Path] = []
    for item in out:
        r = item.resolve()
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


def cmd_compress_pdf(args) -> int:
    paths = collect_pdf_paths(list(args.inputs), recursive=args.recursive)
    if not paths:
        print("No PDF files found.", file=sys.stderr)
        return 1

    suffix = args.suffix.strip() or "_compressed"
    if not suffix.startswith("_") and suffix:
        suffix = "_" + suffix

    if getattr(args, "out", None):
        if len(paths) != 1:
            print("--out applies only when exactly one PDF is given.", file=sys.stderr)
            return 1
        dest = Path(args.out).expanduser().resolve()
        bi, bo = compress_pdf_file(paths[0], dest, strong=args.strong)
        _report(paths[0], dest, bi, bo)
        return 0

    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None

    for src in paths:
        if out_dir:
            dest = out_dir / f"{src.stem}{suffix}.pdf"
        else:
            dest = src.with_name(f"{src.stem}{suffix}.pdf")
        bi, bo = compress_pdf_file(src, dest, strong=args.strong)
        _report(src, dest, bi, bo)
    return 0


def _report(src: Path, dest: Path, bi: int, bo: int) -> None:
    pct = (100.0 * (1 - bo / bi)) if bi > 0 else 0.0
    sign = "smaller" if bo < bi else "larger"
    print(f"{src.name} -> {dest}")
    print(f"  {bi:,} B -> {bo:,} B ({pct:.1f}% {sign})")


def build_compress_parser(sub):
    sc = sub.add_parser(
        "compress-pdf",
        help="Compress PDF(s) with PyMuPDF (optional extra: pip install lop-workflow[compress])",
    )
    sc.add_argument(
        "inputs",
        nargs="+",
        metavar="PATH",
        help="PDF file(s) and/or folder(s) containing .pdf",
    )
    sc.add_argument(
        "--out",
        default=None,
        help="Output path when exactly one input PDF is provided",
    )
    sc.add_argument(
        "--output-dir",
        default=None,
        metavar="DIR",
        help="Write outputs here instead of next to each source file",
    )
    sc.add_argument(
        "--suffix",
        default="_compressed",
        help='Stem suffix before .pdf (default: "_compressed")',
    )
    sc.add_argument(
        "--recursive",
        action="store_true",
        help="When input is a folder, include PDFs in subfolders",
    )
    sc.add_argument(
        "--strong",
        action="store_true",
        help="Also attempt font subsetting (may shrink text-heavy PDFs more)",
    )
    sc.set_defaults(func=cmd_compress_pdf)
    return sc
