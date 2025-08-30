#!/usr/bin/env python3
"""
LLM-driven grouping of German OCR pages into letters.

What it does
- Reads all German OCR page files from --german-dir (expects "<base>_german.txt").
- Optionally maps them to the original image filenames from --images-dir.
- Builds a single prompt context that lists (filename, german_text) for every page.
- Calls Gemini 2.5 Pro to infer contiguous letters and page order purely from content.
- Saves the model's JSON grouping and, if --assemble, writes one de.txt per letter with no extra markers.

Important constraints
- No narrative analysis. No invented pages. Do not add markers or headers to letters.
- Provenance is preserved in the JSON output (mapping letter -> page filenames).

Outputs
- <output-dir>/llm_grouping_input.txt  (audit: what we sent)
- <output-dir>/llm_grouping.json       (LLM result)
- <output-dir>/L0001/de.txt, L0002/de.txt, ... (if --assemble)
"""
from __future__ import annotations

import os
import sys
import json
import argparse
from typing import List, Dict

from dotenv import load_dotenv
from google import genai
from google.genai import types


def list_german_pages(german_dir: str) -> List[str]:
    files = [f for f in os.listdir(german_dir) if f.lower().endswith("_german.txt")]
    files.sort()
    return [os.path.join(german_dir, f) for f in files]


def to_base(filename: str) -> str:
    name = os.path.basename(filename)
    if name.lower().endswith("_german.txt"):
        return name[: -len("_german.txt")]
    return os.path.splitext(name)[0]


PROMPT_IMAGE_EXTRACTION = (
    "This is a single page image of a handwritten German document.\n"
    "Transcribe the handwritten German text exactly as it appears.\n"
    "Do not add numbering, bullets, labels, or commentary.\n"
    "Do not prefix lines with numbers or symbols.\n"
    "Return only the raw text with original line breaks."
)


PROMPT_TASK = (
    "You will receive a list of pages from scanned German letters. Each item has a filename and its German text.\n"
    "Your task is to group pages into complete letters and order pages within each letter.\n\n"
    "Rules:\n"
    "- Use ONLY the provided pages. Do not invent or omit pages.\n"
    "- Group pages that clearly continue the same letter (salutations, closing formulas, consistent topics/dates/names).\n"
    "- Order pages within a letter according to content flow.\n"
    "- If any page is ambiguous, place it in the best-fitting group with low confidence, or leave it unassigned.\n"
    "- Do NOT alter or rewrite the page texts.\n"
    "- Output STRICT JSON only with this schema (no commentary):\n"
    "  {\n"
    "    \"letters\": [\n"
    "      { \"id\": \"L0001\", \"pages\": [\"<filename>\", ...], \"confidence\": 0.0, \"reason\": \"...\" },\n"
    "      { \"id\": \"L0002\", \"pages\": [ ... ], \"confidence\": 0.0, \"reason\": \"...\" }\n"
    "    ],\n"
    "    \"unassigned_pages\": [\"<filename>\", ...]\n"
    "  }\n"
)


def build_input_listing(items: List[Dict[str, str]]) -> str:
    # Plain text context. We explicitly mark page boundaries.
    parts: List[str] = ["--- PAGES START ---"]
    for it in items:
        parts.append("=== PAGE START ===")
        parts.append(f"filename: {it['filename']}")
        parts.append("german:")
        parts.append(it["german"])  # do not modify
        if "english" in it and it["english"]:
            parts.append("english:")
            parts.append(it["english"])  # optional aid; do not modify
        parts.append("=== PAGE END ===")
    parts.append("--- PAGES END ---")
    return "\n".join(parts)


def extract_german_text(image_path: str, client) -> str:
    files = [client.files.upload(file=image_path)]
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                    file_uri=files[0].uri,
                    mime_type=files[0].mime_type,
                ),
                types.Part.from_text(text=PROMPT_IMAGE_EXTRACTION),
            ],
        ),
    ]
    cfg = types.GenerateContentConfig(
        temperature=0.3,
        response_mime_type="text/plain",
        max_output_tokens=4096,
        thinking_config=types.ThinkingConfig(thinking_budget=256),
    )
    out = ""
    for chunk in client.models.generate_content_stream(
        model="gemini-2.5-pro",
        contents=contents,
        config=cfg,
    ):
        if chunk.text:
            out += chunk.text
    return out


def call_llm_grouping(client, task_instructions: str, listing: str) -> str:
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=task_instructions),
                types.Part.from_text(text=listing),
            ],
        )
    ]
    cfg = types.GenerateContentConfig(
        temperature=0.3,
        response_mime_type="application/json",
        max_output_tokens=8192,
        thinking_config=types.ThinkingConfig(thinking_budget=512),
    )
    out = ""
    for chunk in client.models.generate_content_stream(
        model="gemini-2.5-pro",
        contents=contents,
        config=cfg,
    ):
        if chunk.text:
            out += chunk.text
    return out.strip()


def assemble_letters(groups: dict, items_by_filename: Dict[str, Dict[str, str]], output_dir: str) -> None:
    # Create per-letter folders and emit de.txt without any added markers
    os.makedirs(output_dir, exist_ok=True)
    letters = groups.get("letters", [])

    # Also index by prefix before first underscore (handles UUID-only refs)
    items_by_prefix: Dict[str, Dict[str, str]] = {}
    for k, v in items_by_filename.items():
        pref = k.split("_", 1)[0]
        items_by_prefix[pref] = v
    # Determine collection name (parent of output_dir), e.g., DorleLettersE
    parent = os.path.basename(os.path.normpath(os.path.dirname(output_dir)))
    collection_prefix = parent if parent and parent.lower() != "" and parent.lower() != "." else ""

    for i, letter in enumerate(letters, 1):
        lid = letter.get("id") or f"L{i:04d}"
        folder_name = f"{collection_prefix} {lid}".strip() if collection_prefix else lid
        ldir = os.path.join(output_dir, folder_name)
        os.makedirs(ldir, exist_ok=True)
        # Save JSON snippet per letter for provenance
        with open(os.path.join(ldir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(letter, f, ensure_ascii=False, indent=2)

        # Concatenate page texts as-is
        texts: List[str] = []
        for fn in letter.get("pages", []):
            item = items_by_filename.get(fn)
            if not item:
                # try matching by UUID prefix (model may omit suffix like _1_105_c)
                item = items_by_prefix.get(fn.split("_", 1)[0])
            if item:
                texts.append(item.get("german", ""))  # do not modify or add markers
        de_text = "".join(texts)
        with open(os.path.join(ldir, "de.txt"), "w", encoding="utf-8") as f:
            f.write(de_text)


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser(description="LLM-driven grouping of German OCR pages into letters")
    ap.add_argument("--images-dir", help="Directory with original images (optional)")
    ap.add_argument("--german-dir", default="german_output")
    ap.add_argument("--english-dir", help="Directory with per-page English translations (optional)")
    ap.add_argument("--output-dir", default="letters")
    ap.add_argument("--assemble", action="store_true", help="Write de.txt per letter using grouped pages")
    ap.add_argument("--save-input", action="store_true", help="Save the constructed listing file for audit")
    ap.add_argument("--reuse-json", action="store_true", help="Reuse existing llm_grouping.json in output-dir instead of calling LLM")
    ap.add_argument("--run-ocr", action="store_true", help="Run OCR for missing german pages using Gemini 2.5 Pro")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(args.german_dir):
        os.makedirs(args.german_dir, exist_ok=True)

    client = genai.Client(api_key=api_key)

    # Optionally OCR missing pages from images-dir
    if args.run_ocr and args.images_dir is None:
        print("--run-ocr requires --images-dir", file=sys.stderr)
        sys.exit(1)

    if args.run_ocr and args.images_dir:
        all_images = [
            os.path.join(args.images_dir, f)
            for f in os.listdir(args.images_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        all_images.sort()
        for i, img in enumerate(all_images, 1):
            base = to_base(img)
            out_path = os.path.join(args.german_dir, f"{base}_german.txt")
            if os.path.exists(out_path):
                continue
            print(f"[{i}/{len(all_images)}] OCR: {os.path.basename(img)}")
            try:
                text = extract_german_text(img, client)
            except Exception as e:
                print(f"  OCR error for {img}: {e}", file=sys.stderr)
                text = ""
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)

    page_paths = list_german_pages(args.german_dir)
    if not page_paths:
        print("No *_german.txt files found.")
        sys.exit(1)

    # Build input items
    items: List[Dict[str, str]] = []
    for p in page_paths:
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read()
        base = to_base(p)
        filename = base  # keep base as filename key
        obj = {"filename": filename, "german": txt}
        if args.english_dir:
            ep = os.path.join(args.english_dir, f"{base}_english.txt")
            if os.path.exists(ep):
                try:
                    with open(ep, "r", encoding="utf-8") as ef:
                        obj["english"] = ef.read()
                except Exception:
                    pass
        items.append(obj)

    listing = build_input_listing(items)
    os.makedirs(args.output_dir, exist_ok=True)
    if args.save_input:
        with open(os.path.join(args.output_dir, "llm_grouping_input.txt"), "w", encoding="utf-8") as f:
            f.write(listing)

    out_json_path = os.path.join(args.output_dir, "llm_grouping.json")
    if args.reuse_json and os.path.exists(out_json_path):
        with open(out_json_path, "r", encoding="utf-8") as f:
            raw = f.read()
        print(f"Reusing existing grouping JSON: {out_json_path}")
    else:
        # Call LLM for grouping
        print(f"Submitting {len(items)} pages to Gemini for grouping…")
        raw = call_llm_grouping(client, PROMPT_TASK, listing)
        # Persist JSON
        with open(out_json_path, "w", encoding="utf-8") as f:
            f.write(raw)
        print(f"Saved grouping JSON to: {out_json_path}")

    # Parse and optionally assemble
    try:
        groups = json.loads(raw)
    except Exception as e:
        print(f"Error parsing LLM JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if args.assemble:
        items_by_fn = {it["filename"]: it for it in items}
        assemble_letters(groups, items_by_fn, args.output_dir)
        print(f"Assembled letters under: {args.output_dir}")


if __name__ == "__main__":
    main()
