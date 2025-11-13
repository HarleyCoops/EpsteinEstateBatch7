#!/usr/bin/env python3
"""
LLM-driven grouping of document pages into coherent letters/stories.

What it does
- Reads all page text files from --text-dir/--pages-dir (any *.txt files).
- Optionally maps them to the original image filenames from --images-dir.
- Builds a single prompt context that lists (filename, page_text) for every page.
- Calls Gemini 2.5 Pro Flash to infer contiguous letters and page order purely from content.
- Saves the model's JSON grouping and, if --assemble, writes one de.txt/text.txt per letter with no extra markers.

Important constraints
- No narrative analysis. No invented pages. Do not add markers or headers to letters.
- Provenance is preserved in the JSON output (mapping letter -> page filenames) and meta.json.

Outputs
- <output-dir>/llm_grouping_input.txt  (audit: what we sent)
- <output-dir>/llm_grouping.json       (LLM result)
- <output-dir>/L0001/de.txt + text.txt, L0002/..., etc. (if --assemble)
"""
from __future__ import annotations

import os
import re
import sys
import json
import argparse
from typing import List, Dict

from dotenv import load_dotenv
from google import genai
from google.genai import types

HOUSE_OVERSIGHT_PATTERN = re.compile(r"house[_-]?oversight[_-]?(\d+)", re.IGNORECASE)


def current_model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-pro-flash")


def list_text_pages(text_dir: str) -> List[str]:
    files: List[str] = []
    for root, _, filenames in os.walk(text_dir):
        for fname in filenames:
            if fname.lower().endswith(".txt"):
                files.append(os.path.join(root, fname))
    files.sort()
    return files


def to_base(filename: str) -> str:
    name = os.path.basename(filename)
    lower = name.lower()
    for suffix in ("_german.txt", "_text.txt", ".txt"):
        if lower.endswith(suffix):
            return name[: -len(suffix)]
    return os.path.splitext(name)[0]


PROMPT_IMAGE_EXTRACTION = (
    "This is a single page image from an official House Oversight Committee document set.\n"
    "Transcribe the text exactly as it appears (handwritten, typed, stamped, etc.).\n"
    "Do not add numbering, bullets, labels, or commentary.\n"
    "Do not prefix lines with numbers or symbols.\n"
    "Return only the raw text with original line breaks."
)


PROMPT_TASK = (
    "You will receive a list of document pages released by the House Oversight Committee.\n"
    "Each item has a filename and its full text content.\n"
    "Group pages that belong to the same narrative/letter/memo and order pages within each group.\n\n"
    "Rules:\n"
    "- Use ONLY the provided pages. Do not invent or omit pages.\n"
    "- Group pages that clearly continue the same document (shared salutations, signatures, identifiers, dates, or topics).\n"
    "- Order pages according to content flow; maintain chronological continuity when dates are present.\n"
    "- If a page is ambiguous, place it in the best-fitting group with low confidence or leave it unassigned.\n"
    "- Do NOT alter or rewrite page text. Preserve provenance.\n"
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
        parts.append("text:")
        parts.append(it["text"])  # do not modify
        if "english" in it and it["english"]:
            parts.append("english:")
            parts.append(it["english"])  # optional aid; do not modify
        parts.append("=== PAGE END ===")
    parts.append("--- PAGES END ---")
    return "\n".join(parts)


def extract_page_text(image_path: str, client) -> str:
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
        model=current_model(),
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
        model=current_model(),
        contents=contents,
        config=cfg,
    ):
        if chunk.text:
            out += chunk.text
    return out.strip()


def extract_house_ids(value: str) -> List[str]:
    matches = HOUSE_OVERSIGHT_PATTERN.findall(value)
    if matches:
        return matches
    return re.findall(r"\d{4,}", value)


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

        # Concatenate page texts as-is
        texts: List[str] = []
        source_files: List[str] = []
        ids: List[str] = []
        for fn in letter.get("pages", []):
            item = items_by_filename.get(fn)
            if not item:
                # try matching by UUID prefix (model may omit suffix like _1_105_c)
                item = items_by_prefix.get(fn.split("_", 1)[0])
            if item:
                texts.append(item.get("text", ""))  # do not modify or add markers
                source_path = item.get("source_path")
                if source_path:
                    source_files.append(source_path)
                    ids.extend(extract_house_ids(os.path.basename(source_path)))

        meta = dict(letter)
        if source_files:
            meta["source_files"] = source_files
        if ids:
            seen = set()
            ordered = []
            for _id in ids:
                if _id not in seen:
                    seen.add(_id)
                    ordered.append(_id)
            meta["house_oversight_ids"] = ordered

        with open(os.path.join(ldir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        de_text = "".join(texts)
        with open(os.path.join(ldir, "de.txt"), "w", encoding="utf-8") as f:
            f.write(de_text)
        with open(os.path.join(ldir, "text.txt"), "w", encoding="utf-8") as f:
            f.write(de_text)


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser(description="LLM-driven grouping of text pages into letters/stories")
    ap.add_argument("--images-dir", help="Directory with original images (optional)")
    ap.add_argument(
        "--text-dir",
        "--pages-dir",
        "--german-dir",
        dest="text_dir",
        default="german_output",
        help="Directory containing per-page text files (*.txt). Legacy flag --german-dir is retained for compatibility.",
    )
    ap.add_argument("--english-dir", help="Directory with per-page English translations (optional)")
    ap.add_argument("--output-dir", default="letters")
    ap.add_argument("--assemble", action="store_true", help="Write de.txt per letter using grouped pages")
    ap.add_argument("--save-input", action="store_true", help="Save the constructed listing file for audit")
    ap.add_argument("--reuse-json", action="store_true", help="Reuse existing llm_grouping.json in output-dir instead of calling LLM")
    ap.add_argument("--run-ocr", action="store_true", help="Run OCR for missing page text using Gemini 2.5 Pro Flash")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(args.text_dir):
        os.makedirs(args.text_dir, exist_ok=True)

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
            out_path = os.path.join(args.text_dir, f"{base}_german.txt")
            if os.path.exists(out_path):
                continue
            print(f"[{i}/{len(all_images)}] OCR: {os.path.basename(img)}")
            try:
                text = extract_page_text(img, client)
            except Exception as e:
                print(f"  OCR error for {img}: {e}", file=sys.stderr)
                text = ""
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)

    page_paths = list_text_pages(args.text_dir)
    if not page_paths:
        print("No text .txt files found.")
        sys.exit(1)

    # Build input items
    items: List[Dict[str, str]] = []
    for p in page_paths:
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read()
        base = to_base(p)
        filename = base  # keep base as filename key
        obj = {
            "filename": filename,
            "text": txt,
            "source_path": os.path.relpath(p),
        }
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
