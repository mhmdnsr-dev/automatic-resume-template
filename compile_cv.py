#!/usr/bin/env python3
"""
Compile a CV .tex file to PDF or DOCX. PDF is the default.

Note: the PyPI package `pdflatex` is a thin wrapper with known issues
(wrong -interaction-mode flag, stdin quirks, 15s timeout). This script
calls the system `pdflatex` executable directly instead.

Usage:
  python compile_cv.py
  python compile_cv.py path/to/resume.tex
  python compile_cv.py 2026-07-19_insense-frontend-developer
  python compile_cv.py --format docx
  python compile_cv.py 2026-07-19_insense-frontend-developer --format docx
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

MASTER_TEX_NAME = "resume.tex"

DOCX_INSTALL_HELP = """DOCX output requires python-docx.

Install dependencies in the repository virtual environment (do not use --break-system-packages):

Linux/macOS:
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
  .venv/bin/python compile_cv.py --format docx

Windows:
  python -m venv .venv
  .venv\\Scripts\\python.exe -m pip install -r requirements.txt
  .venv\\Scripts\\python.exe compile_cv.py --format docx"""

COMMON_PDFLATEX = [
    Path(os.environ.get("LOCALAPPDATA", ""))
    / "Programs"
    / "MiKTeX"
    / "miktex"
    / "bin"
    / "x64"
    / "pdflatex.exe",
    Path(os.environ.get("LOCALAPPDATA", ""))
    / "MiKTeX"
    / "miktex"
    / "bin"
    / "x64"
    / "pdflatex.exe",
    Path(r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe"),
]


def find_pdflatex() -> Path:
    which = shutil.which("pdflatex")
    if which:
        return Path(which)
    for candidate in COMMON_PDFLATEX:
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        "pdflatex binary not found.\n"
        "Install MiKTeX (https://miktex.org/) or TeX Live, then reopen the terminal.\n"
        "On Linux, ensure pdflatex is on PATH. On Windows, expected e.g. "
        "%LOCALAPPDATA%\\Programs\\MiKTeX\\miktex\\bin\\x64\\pdflatex.exe"
    )


def resolve_tex(arg: str | None, root: Path) -> Path:
    if arg is None:
        candidates = [
            root / MASTER_TEX_NAME,
            root / "Example_Candidate_CV.tex",  # legacy fallback
        ]
        for c in candidates:
            if c.is_file():
                return c
        raise FileNotFoundError(f"No {MASTER_TEX_NAME} found under {root}")

    p = Path(arg)
    if not p.is_absolute():
        p = (root / p).resolve()

    if p.is_dir():
        for name in (MASTER_TEX_NAME, "Example_Candidate_CV.tex"):
            tex = p / name
            if tex.is_file():
                return tex
        raise FileNotFoundError(f"No {MASTER_TEX_NAME} in {p}")

    if p.suffix.lower() != ".tex" or not p.is_file():
        raise FileNotFoundError(f"Not a .tex file: {p}")
    return p


def compile_pdf(tex_path: Path) -> Path:
    pdflatex = find_pdflatex()
    out_dir = tex_path.parent
    pdf_path = out_dir / f"{tex_path.stem}.pdf"
    log_path = out_dir / f"{tex_path.stem}.log"
    temp_job = f"{tex_path.stem}__build"
    temp_pdf = out_dir / f"{temp_job}.pdf"
    temp_log = out_dir / f"{temp_job}.log"

    print(f"Using: {pdflatex}", flush=True)

    # Build to a temp jobname so an open PDF viewer cannot block compilation.
    for leftover in out_dir.glob(f"{temp_job}.*"):
        try:
            leftover.unlink()
        except OSError:
            pass

    cmd = [
        str(pdflatex),
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={out_dir}",
        f"-jobname={temp_job}",
        tex_path.name,
    ]
    for pass_number in range(1, 3):
        print(f"Compiling (pass {pass_number}/2) ...", flush=True)
        result = subprocess.run(
            cmd,
            cwd=str(tex_path.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )

        if result.returncode != 0 or not temp_pdf.is_file():
            log_tail = ""
            if temp_log.is_file():
                log_tail = temp_log.read_text(encoding="utf-8", errors="replace")[-2500:]
            elif result.stdout:
                log_tail = result.stdout[-2500:]
            raise RuntimeError(
                f"pdflatex pass {pass_number} did not produce PDF "
                f"(exit {result.returncode}).\n"
                f"--- log tail ---\n{log_tail}"
            )

    try:
        if pdf_path.exists():
            pdf_path.unlink()
        temp_pdf.replace(pdf_path)
        final = pdf_path
    except OSError:
        # Viewer still locking the destination — keep a unique unlocked copy.
        alt = out_dir / f"{tex_path.stem}_latest.pdf"
        try:
            if alt.exists():
                alt.unlink()
        except OSError:
            alt = out_dir / f"{tex_path.stem}_{os.getpid()}.pdf"
        temp_pdf.replace(alt)
        print(
            f"NOTE: could not overwrite {pdf_path.name} (open in viewer). Using {alt.name}",
            flush=True,
        )
        final = alt

    # Refresh main log name for convenience
    if temp_log.is_file():
        try:
            if log_path.exists():
                log_path.unlink()
            temp_log.replace(log_path)
        except OSError:
            pass

    for leftover in out_dir.glob(f"{temp_job}.*"):
        try:
            leftover.unlink()
        except OSError:
            pass

    return final


def compile_docx(tex_path: Path) -> Path:
    try:
        from helpers.compile_cv_docx import compile_docx as build_docx
    except ModuleNotFoundError as exc:
        if exc.name == "docx":
            raise RuntimeError(DOCX_INSTALL_HELP) from exc
        raise
    return build_docx(tex_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile a CV .tex file. PDF output is the default."
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="A .tex file or directory containing resume.tex",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str.lower,
        choices=("pdf", "docx"),
        default="pdf",
        dest="output_format",
        help="Output format (default: pdf)",
    )
    return parser


def compile_cv(tex_path: Path, output_format: str = "pdf") -> Path:
    if output_format == "pdf":
        return compile_pdf(tex_path)
    if output_format == "docx":
        return compile_docx(tex_path)
    raise ValueError(f"Unsupported output format: {output_format}")


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parent
    args = build_parser().parse_args(argv)

    try:
        tex = resolve_tex(args.source, root)
        print(f"Compiling {args.output_format.upper()}: {tex}", flush=True)
        output = compile_cv(tex, args.output_format)
        print(f"Wrote: {output}", flush=True)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
