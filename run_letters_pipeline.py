#!/usr/bin/env python3
"""
Wrapper to run the full letters workflow in one command:
- OCR missing pages + LLM grouping + assemble source letters
- Translate assembled letters to English (and LaTeX)

Examples
  python run_letters_pipeline.py --base DorleLettersF
  python run_letters_pipeline.py --base DorleLettersE --no-latex

By default, if --images-dir not provided, images are assumed at
  <base>/<basename(base)> (e.g., DorleLettersF/DorleLettersF)
and outputs go to
  <base>/german_output (page text) and <base>/letters
"""
from __future__ import annotations

import os
import sys
import argparse
import subprocess
from dotenv import load_dotenv


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Run OCR+LLM grouping+translation in one go")
    ap.add_argument("--base", required=True, help="Base folder (e.g., DorleLettersF)")
    ap.add_argument("--images-dir", help="Images directory; defaults to <base>/<basename(base)>")
    ap.add_argument(
        "--text-dir",
        "--pages-dir",
        "--german-dir",
        dest="text_dir",
        help="Page text output dir; defaults to <base>/german_output (legacy flag --german-dir supported)",
    )
    ap.add_argument("--letters-dir", help="Letters output dir; defaults to <base>/letters")
    ap.add_argument("--no-latex", action="store_true", help="Skip LaTeX generation for English translations")
    ap.add_argument("--force-translate", action="store_true", help="Re-translate even if en.txt exists")
    ap.add_argument("--save-input", action="store_true", help="Save LLM input listing", default=True)
    args = ap.parse_args()

    # Load .env so GEMINI_API_KEY is available when set there
    load_dotenv()

    base = args.base.rstrip("/\\")
    base_name = os.path.basename(base)

    images_dir = args.images_dir or os.path.join(base, base_name)
    german_dir = args.text_dir or os.path.join(base, "german_output")
    letters_dir = args.letters_dir or os.path.join(base, "letters")

    # Ensure API key exists
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not set (set it or add it to .env)", file=sys.stderr)
        sys.exit(1)

    os.makedirs(german_dir, exist_ok=True)
    os.makedirs(letters_dir, exist_ok=True)

    py = sys.executable

    # Step 1: OCR (missing) + LLM grouping + assemble de.txt
    cmd_group = [
        py, "llm_group_letters.py",
        "--images-dir", images_dir,
        "--text-dir", german_dir,
        "--output-dir", letters_dir,
        "--run-ocr",
        "--assemble",
    ]
    if args.save_input:
        cmd_group.append("--save-input")
    run(cmd_group)

    # Step 2: Translate assembled letters
    cmd_translate = [
        py, "translate_letters.py",
        "--letters-dir", letters_dir,
    ]
    if not args.no_latex:
        cmd_translate.append("--latex")
    if args.force_translate:
        cmd_translate.append("--force")
    run(cmd_translate)

    print("All done.")


if __name__ == "__main__":
    main()
