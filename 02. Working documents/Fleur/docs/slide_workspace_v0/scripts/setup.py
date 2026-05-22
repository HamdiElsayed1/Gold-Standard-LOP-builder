"""Cross-platform dependency installer for the html-pptx workspace.

Creates a .venv at the project root, installs Python dependencies,
and downloads Playwright's Chromium browser.

Usage (from anywhere):
    python scripts/setup.py
"""

from __future__ import annotations

import filecmp
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _venv_python(venv_dir: Path) -> Path:
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _needs_install(project_root: Path, venv_dir: Path) -> bool:
    """Return True if the venv doesn't exist or requirements.txt changed."""
    src = project_root / "requirements.txt"
    cached = venv_dir / "requirements.txt"
    venv_python = _venv_python(venv_dir)

    if not venv_python.exists():
        return True
    if not cached.exists():
        return True
    if not filecmp.cmp(str(src), str(cached), shallow=False):
        return True
    return False


def _create_venv(venv_dir: Path) -> None:
    print(f"[html-pptx] Creating venv at {venv_dir} ...")
    subprocess.check_call(
        [sys.executable, "-m", "venv", str(venv_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _install_deps(venv_dir: Path, requirements: Path) -> None:
    python = _venv_python(venv_dir)
    print("[html-pptx] Installing Python dependencies ...")
    subprocess.check_call(
        [str(python), "-m", "pip", "install", "-q", "-r", str(requirements)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _install_chromium(venv_dir: Path) -> None:
    python = _venv_python(venv_dir)
    print("[html-pptx] Installing Playwright Chromium ...")
    subprocess.check_call(
        [str(python), "-m", "playwright", "install", "chromium"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main() -> None:
    venv_dir = PROJECT_ROOT / ".venv"
    requirements = PROJECT_ROOT / "requirements.txt"

    if not _needs_install(PROJECT_ROOT, venv_dir):
        return

    if not venv_dir.exists():
        _create_venv(venv_dir)

    _install_deps(venv_dir, requirements)
    _install_chromium(venv_dir)

    shutil.copy2(str(requirements), str(venv_dir / "requirements.txt"))
    print("[html-pptx] Setup complete.")


if __name__ == "__main__":
    main()
