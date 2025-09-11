#!/usr/bin/env python3
"""
Run the strict Chinese pipeline in one go:
- OCR missing pages (Chinese) + deterministic grouping + assemble zh.txt
- Translate assembled zh.txt to English (and English/Chinese LaTeX optionally)

Examples
  python run_chinese_strict_pipeline.py --base ChineseBook
  python run_chinese_strict_pipeline.py --base ChineseBook --no-latex
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
    ap = argparse.ArgumentParser(description="Run strict OCR+group+translate for Chinese")
    ap.add_argument("--base", required=True, help="Base folder (e.g., ChineseBook)")
    ap.add_argument("--images-dir", help="Images directory; defaults to <base>/<basename(base)>")
    ap.add_argument("--chinese-dir", help="Chinese OCR output dir; defaults to <base>/chinese_output")
    ap.add_argument("--letters-dir", help="Letters/book output dir; defaults to <base>/letters")
    ap.add_argument("--no-latex", action="store_true", help="Skip LaTeX generation")
    ap.add_argument("--force-translate", action="store_true", help="Re-translate even if en.txt exists")
    args = ap.parse_args()

    load_dotenv()

    base = args.base.rstrip("/\\")
    base_name = os.path.basename(base)

    images_dir = args.images_dir or os.path.join(base, base_name)
    chinese_dir = args.chinese_dir or os.path.join(base, "chinese_output")
    letters_dir = args.letters_dir or os.path.join(base, "letters")

    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not set (set it or add it to .env)", file=sys.stderr)
        sys.exit(1)

    os.makedirs(chinese_dir, exist_ok=True)
    os.makedirs(letters_dir, exist_ok=True)

    py = sys.executable

    # Step 1: OCR + deterministic grouping + assemble zh.txt
    cmd_strict = [
        py, "helperPython/pipeline_strict_zh.py",
        "--input-dir", images_dir,
        "--chinese-dir", chinese_dir,
        "--letters-dir", letters_dir,
        "--translate",
    ]
    if not args.no_latex:
        cmd_strict.append("--latex")
    run(cmd_strict)

    # Optionally re-run translation independently (for --force behavior)
    if args.force_translate:
        cmd_translate = [
            py, "translate_letters_zh.py",
            "--letters-dir", letters_dir,
            "--force",
        ]
        if not args.no_latex:
            cmd_translate.append("--latex")
        run(cmd_translate)

    print("All done.")


if __name__ == "__main__":
    main()

