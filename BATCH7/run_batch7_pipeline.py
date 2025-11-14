#!/usr/bin/env python3
"""
BATCH7 Pipeline: House Oversight Committee Document Processing

This pipeline processes three types of inputs:
1. NATIVES/ - Excel spreadsheets: Analyze structure, extract relationships, build connection maps
2. IMAGES/ - Images: OCR/extract text, describe pictures, output complex JSON
3. TEXT/ - Text conversations: Extract content, understand context, assemble into stories/letters

Usage:
    python run_batch7_pipeline.py --process natives
    python run_batch7_pipeline.py --process images
    python run_batch7_pipeline.py --process text
    python run_batch7_pipeline.py --process all
"""
from __future__ import annotations

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Import processing modules
# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from batch7_process_natives import process_natives
from batch7_process_images import process_images
from batch7_process_text import process_text


def main() -> None:
    # Load .env from script directory or parent directory
    script_dir = Path(__file__).parent.absolute()
    # Try script directory first (where .env actually is)
    env_path = script_dir / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        # Fallback to parent directory
        load_dotenv(dotenv_path=script_dir.parent / ".env")
        # Also try default location
        load_dotenv()
    
    ap = argparse.ArgumentParser(
        description="BATCH7 Pipeline: Process NATIVES, IMAGES, and TEXT directories"
    )
    ap.add_argument(
        "--process",
        choices=["natives", "images", "text", "all"],
        default="all",
        help="Which processing stage to run (default: all)"
    )
    # Default base_dir to the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    default_base_dir = script_dir if script_dir.name == "BATCH7" else script_dir / "BATCH7"
    
    ap.add_argument(
        "--base-dir",
        default=str(default_base_dir),
        help=f"Base directory containing NATIVES/, IMAGES/, TEXT/ (default: {default_base_dir})"
    )
    ap.add_argument(
        "--natives-dir",
        help="NATIVES directory (default: <base-dir>/NATIVES)"
    )
    ap.add_argument(
        "--images-dir",
        help="IMAGES directory (default: <base-dir>/IMAGES)"
    )
    ap.add_argument(
        "--text-dir",
        help="TEXT directory (default: <base-dir>/TEXT)"
    )
    ap.add_argument(
        "--output-dir",
        default="BATCH7/output",
        help="Output directory for all results (default: BATCH7/output)"
    )
    ap.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files that already have outputs"
    )
    args = ap.parse_args()

    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set up directory paths
    natives_dir = Path(args.natives_dir) if args.natives_dir else base_dir / "NATIVES"
    images_dir = Path(args.images_dir) if args.images_dir else base_dir / "IMAGES"
    text_dir = Path(args.text_dir) if args.text_dir else base_dir / "TEXT"

    # Check API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not set (set it or add it to .env)", file=sys.stderr)
        sys.exit(1)

    process_natives_flag = args.process in ("natives", "all")
    process_images_flag = args.process in ("images", "all")
    process_text_flag = args.process in ("text", "all")

    if process_natives_flag:
        print("=" * 80)
        print("PROCESSING NATIVES (Excel Spreadsheets)")
        print("=" * 80)
        if natives_dir.exists():
            process_natives(natives_dir, output_dir / "natives_analysis", args.skip_existing)
        else:
            print(f"NATIVES directory not found: {natives_dir}")

    if process_images_flag:
        print("\n" + "=" * 80)
        print("PROCESSING IMAGES")
        print("=" * 80)
        if images_dir.exists():
            process_images(images_dir, output_dir / "images_analysis", args.skip_existing)
        else:
            print(f"IMAGES directory not found: {images_dir}")

    if process_text_flag:
        print("\n" + "=" * 80)
        print("PROCESSING TEXT")
        print("=" * 80)
        if text_dir.exists():
            process_text(text_dir, output_dir / "text_analysis", args.skip_existing)
        else:
            print(f"TEXT directory not found: {text_dir}")

    print("\n" + "=" * 80)
    print("BATCH7 PIPELINE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

