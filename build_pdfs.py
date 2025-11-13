#!/usr/bin/env python3
"""
Compile LaTeX translations (en.tex) to PDFs for all letter folders.

Behavior
- Scans base directories matching a glob (default: DorleLetters[A-Z]).
- For each base, finds letter folders under <base>/letters/* containing en.tex.
- Compiles en.tex with Tectonic (preferred) or pdflatex/xelatex if available.
- Renames the produced en.pdf to "<letter-folder-name>.pdf" in the same folder.
- Optional cleanup of LaTeX aux/log files.

Examples
  python build_pdfs.py --glob "DorleLetters[A-M]"
  python build_pdfs.py --glob "DorleLettersE" --engine tectonic --cleanup
  python build_pdfs.py --engine auto --dry-run
"""
from __future__ import annotations

import argparse
import os
import sys
import subprocess
from pathlib import Path
from shutil import which
from typing import Iterable, List, Optional


def detect_engine(preferred: str) -> Optional[str]:
    if preferred != "auto":
        return preferred if which(preferred) else None
    # Preference order: tectonic, then pdflatex, then xelatex
    for name in ("tectonic", "pdflatex", "xelatex"):
        if which(name):
            return name
    return None


def compile_tex(tex_path: Path, engine: str, dry_run: bool = False) -> bool:
    cwd = tex_path.parent
    if engine == "tectonic":
        cmd = ["tectonic", "-q", tex_path.name]
    elif engine == "pdflatex":
        cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name]
    elif engine == "xelatex":
        cmd = ["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name]
    else:
        print(f"Unsupported engine: {engine}", file=sys.stderr)
        return False

    if dry_run:
        print(f"[DRY] Compile: {' '.join(cmd)} (cwd={cwd})")
        return True

    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    except FileNotFoundError:
        print(f"Engine not found on PATH: {engine}", file=sys.stderr)
        return False

    if proc.returncode != 0:
        print(f"Compile failed for {tex_path}", file=sys.stderr)
        # Show a short tail of output for context
        out_tail = (proc.stdout or "").splitlines()[-20:]
        err_tail = (proc.stderr or "").splitlines()[-20:]
        if out_tail:
            print("--- stdout (tail) ---", file=sys.stderr)
            print("\n".join(out_tail), file=sys.stderr)
        if err_tail:
            print("--- stderr (tail) ---", file=sys.stderr)
            print("\n".join(err_tail), file=sys.stderr)
        return False

    return True


def cleanup_aux_files(letter_dir: Path, dry_run: bool = False) -> None:
    patterns = ("*.aux", "*.log", "*.out", "*.toc", "*.fls", "*.fdb_latexmk")
    for pat in patterns:
        for p in letter_dir.glob(pat):
            if dry_run:
                print(f"[DRY] Remove: {p}")
            else:
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass


def find_letter_tex_files(bases_glob: str) -> List[Path]:
    tex_files: List[Path] = []
    for base in Path.cwd().glob(bases_glob):
        letters_dir = base / "letters"
        if not letters_dir.is_dir():
            continue
        # en.tex in immediate subdirectories
        for sub in letters_dir.iterdir():
            if not sub.is_dir():
                continue
            tex_path = sub / "en.tex"
            if tex_path.is_file():
                tex_files.append(tex_path)
    tex_files.sort()
    return tex_files


def process_all(bases_glob: str, engine_pref: str, cleanup: bool, dry_run: bool) -> int:
    engine = detect_engine(engine_pref)
    if not engine:
        if engine_pref == "auto":
            print("No LaTeX engine found. Install 'tectonic' (recommended) or 'pdflatex'/'xelatex' and ensure it is on PATH.", file=sys.stderr)
        else:
            print(f"Requested engine '{engine_pref}' not found on PATH.", file=sys.stderr)
        return 2

    tex_files = find_letter_tex_files(bases_glob)
    if not tex_files:
        print(f"No en.tex files found under {bases_glob}.")
        return 0

    print(f"Using engine: {engine}")
    ok = 0
    fail = 0

    for tex_path in tex_files:
        letter_dir = tex_path.parent
        folder_pdf = letter_dir / f"{letter_dir.name}.pdf"
        produced_pdf = letter_dir / "en.pdf"  # Tectonic/pdflatex default when input is en.tex

        print(f"-> {tex_path}")
        if compile_tex(tex_path, engine, dry_run=dry_run):
            # Move/rename en.pdf to <folder>.pdf
            if dry_run:
                print(f"[DRY] Rename: {produced_pdf.name} -> {folder_pdf.name}")
                ok += 1
            else:
                if not produced_pdf.is_file():
                    # Some engines might output to cwd with a different name; fall back to checking any PDF
                    # matching the tex stem.
                    alt_pdf = letter_dir / f"{tex_path.stem}.pdf"
                    src_pdf = produced_pdf if produced_pdf.is_file() else alt_pdf
                else:
                    src_pdf = produced_pdf

                if src_pdf.is_file():
                    try:
                        if folder_pdf.exists():
                            folder_pdf.unlink()
                        src_pdf.rename(folder_pdf)
                        ok += 1
                    except Exception as exc:
                        print(f"Rename failed for {src_pdf} -> {folder_pdf}: {exc}", file=sys.stderr)
                        fail += 1
                else:
                    print(f"PDF not found after compile: expected {produced_pdf} or {tex_path.stem}.pdf", file=sys.stderr)
                    fail += 1

            if cleanup:
                cleanup_aux_files(letter_dir, dry_run=dry_run)
        else:
            fail += 1

    print(f"Done. Success: {ok}, Failed: {fail}")
    return 0 if fail == 0 else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="Build PDFs for letter translations (en.tex -> <folder>.pdf)")
    ap.add_argument("--glob", default="DorleLetters[A-Z]", help="Glob for base folders (default: DorleLetters[A-Z])")
    ap.add_argument("--engine", default="auto", choices=["auto", "tectonic", "pdflatex", "xelatex"], help="LaTeX engine to use (default: auto)")
    ap.add_argument("--cleanup", action="store_true", help="Remove LaTeX aux/log files after successful compile")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    args = ap.parse_args()

    rc = process_all(bases_glob=args.glob, engine_pref=args.engine, cleanup=args.cleanup, dry_run=args.dry_run)
    sys.exit(rc)


if __name__ == "__main__":
    main()

