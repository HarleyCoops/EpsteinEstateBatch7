#!/usr/bin/env python3
"""
Strict pipeline: OCR -> Group -> Assemble -> (optional) Translate.

Principles
- No narrative or agent logic; no envelope heuristics.
- Preserve provenance: filenames map 1:1 to OCR outputs and group metadata.
- Deterministic grouping based on capture time and lexical similarity.
- Deterministic LaTeX (no LLM formatting) so PDF is stable and auditable.

Outputs per letter (under --letters-dir):
- <LID>/meta.json               # images, timestamps, paths
- <LID>/de.txt                  # concatenated German text
- <LID>/de.tex                  # typeset German
- <LID>/en.txt (if --translate) # translation to English
- <LID>/en.tex (if --translate and --latex)
"""
from __future__ import annotations

import os
import sys
import json
import time
import argparse
from typing import Dict, List
import re

from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

from grouping import build_pages, propose_breakpoints, apply_overrides, group_pages


def _ensure_dirs(*paths: str) -> None:
    for p in paths:
        os.makedirs(p, exist_ok=True)


def _list_images(input_dir: str) -> List[str]:
    files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    # Name sort is only for initial pass; grouping sorts by EXIF/mtime later
    return sorted(files)


PROMPT_IMAGE_EXTRACTION = (
    "This is a single page image of a handwritten German document.\n"
    "Transcribe the handwritten German text exactly as it appears.\n"
    "Do not add numbering, bullets, labels, or commentary.\n"
    "Do not prefix lines with numbers or symbols.\n"
    "Return only the raw text with original line breaks."
)

PROMPT_TRANSLATION_TEMPLATE = (
    "Translate the following German letter to natural English.\n"
    "Keep all details and formatting. No commentary.\n\n"
    "{german}"
)


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
    return _clean_leading_numbering(out)


def translate_to_english(german_text: str, client) -> str:
    prompt = PROMPT_TRANSLATION_TEMPLATE.format(german=german_text)
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    cfg = types.GenerateContentConfig(
        temperature=0.6,
        top_p=0.8,
        response_mime_type="text/plain",
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
    return _clean_leading_numbering(out.strip())


def _clean_leading_numbering(text: str) -> str:
    """
    Remove artificially added line numbering like:
    "1. ...", "2) ..." at line starts when it appears as a long sequential run.
    Keeps legitimate lists by requiring a run >= 4 lines.
    """
    # Remove control characters except newlines and tabs
    def _strip_ctrl(s: str) -> str:
        return "".join(ch for ch in s if ch in ("\n", "\r", "\t") or ord(ch) >= 32)

    text = _strip_ctrl(text)
    lines = text.splitlines()
    pattern = re.compile(r"^\s*(\d{1,4})[\.)]\s+")
    # Detect longest sequential run
    longest_run = 0
    run = 0
    last = None
    for ln in lines:
        m = pattern.match(ln)
        if m:
            n = int(m.group(1))
            if last is None and n in (1, 2):
                run = 1
                last = n
            elif last is not None and n == last + 1:
                run += 1
                last = n
            else:
                longest_run = max(longest_run, run)
                run = 1 if n in (1, 2) else 0
                last = n if run else None
        else:
            longest_run = max(longest_run, run)
            run = 0
            last = None
    longest_run = max(longest_run, run)

    if longest_run >= 4:
        cleaned = [pattern.sub("", ln) for ln in lines]
        return "\n".join(cleaned)
    return text


def _latex_escape(s: str) -> str:
    repl = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "#": r"\#",
        "&": r"\&",
        "%": r"\%",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    return s


def to_latex_document(title: str, body_text: str, lang: str = "ngerman") -> str:
    body = _latex_escape(body_text)
    return (
        "\\documentclass[12pt]{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[T1]{fontenc}\n"
        f"\\usepackage[{lang}]{{babel}}\n"
        "\\usepackage{geometry}\n\\geometry{margin=1in}\n"
        "\\usepackage{parskip}\n"
        "\\begin{document}\n"
        f"\\section*{{{_latex_escape(title)}}}\n"
        "\\noindent\n"
        f"{body}\n"
        "\\end{document}\n"
    )


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser(description="Strict OCR→Grouping→LaTeX→(optional) Translation")
    ap.add_argument("--input-dir", default="input")
    ap.add_argument("--german-dir", default="german_output")
    ap.add_argument("--letters-dir", default="letters")
    ap.add_argument("--time-gap-seconds", type=int, default=180)
    ap.add_argument("--sim-threshold", type=float, default=0.08)
    ap.add_argument("--overrides", help="JSON file with break_after list", default=None)
    ap.add_argument("--skip-ocr", action="store_true")
    ap.add_argument("--translate", action="store_true")
    ap.add_argument("--latex", action="store_true")
    args = ap.parse_args()

    if genai is None or types is None:
        print("google-genai not available. Install requirements and retry.", file=sys.stderr)
        sys.exit(1)

    _ensure_dirs(args.german_dir, args.letters_dir)

    # Discover images
    images = _list_images(args.input_dir)
    if not images:
        print(f"No images in {args.input_dir}")
        return

    # OCR (German) if needed
    api_key = os.environ.get("GEMINI_API_KEY")
    if not args.skip_ocr and not api_key:
        print("GEMINI_API_KEY not set; cannot run OCR. Use --skip-ocr to proceed with existing outputs.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key) if not args.skip_ocr else None

    german_text_by_base: Dict[str, str] = {}
    german_path_by_base: Dict[str, str] = {}

    for i, img in enumerate(images, 1):
        base = os.path.splitext(os.path.basename(img))[0]
        out_path = os.path.join(args.german_dir, f"{base}_german.txt")
        german_path_by_base[base] = out_path
        if os.path.exists(out_path):
            # Use existing
            with open(out_path, "r", encoding="utf-8") as f:
                german_text_by_base[base] = f.read()
            continue
        if args.skip_ocr:
            continue
        print(f"[{i}/{len(images)}] OCR: {os.path.basename(img)}")
        try:
            text = extract_german_text(img, client)
        except Exception as e:
            print(f"  OCR error: {e}", file=sys.stderr)
            text = ""
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        german_text_by_base[base] = text

    # Read any missing OCR files (e.g., when --skip-ocr)
    for img in images:
        base = os.path.splitext(os.path.basename(img))[0]
        if base in german_text_by_base:
            continue
        out_path = german_path_by_base.get(base) or os.path.join(args.german_dir, f"{base}_german.txt")
        german_path_by_base[base] = out_path
        if os.path.exists(out_path):
            with open(out_path, "r", encoding="utf-8") as f:
                german_text_by_base[base] = f.read()
        else:
            german_text_by_base[base] = ""

    # Build pages and propose groups
    pages = build_pages(images, german_text_by_base, german_path_by_base)
    breaks = propose_breakpoints(pages, time_gap_threshold=args.time_gap_seconds, sim_threshold=args.sim_threshold)
    breaks = apply_overrides(breaks, pages, args.overrides)
    groups = group_pages(pages, breaks)

    # Emit per-letter outputs
    for g in groups:
        lid = g["id"]
        gdir = os.path.join(args.letters_dir, lid)
        _ensure_dirs(gdir)
        meta_path = os.path.join(gdir, "meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(g, f, ensure_ascii=False, indent=2)

        # Concatenate German text exactly as extracted (no headers/markers)
        page_texts: List[str] = []
        for p in g["pages"]:
            base = p["base"]
            raw = german_text_by_base.get(base, "")
            txt = _clean_leading_numbering(raw)
            page_texts.append(txt)
        de_text = "".join(page_texts)
        with open(os.path.join(gdir, "de.txt"), "w", encoding="utf-8") as f:
            f.write(de_text)

        if args.latex:
            de_tex = to_latex_document(title=f"Letter {lid} (German)", body_text=de_text, lang="ngerman")
            with open(os.path.join(gdir, "de.tex"), "w", encoding="utf-8") as f:
                f.write(de_tex)

        if args.translate:
            if client is None:
                # Need a client for translation
                api_key = os.environ.get("GEMINI_API_KEY")
                if not api_key:
                    print("Translation requested but GEMINI_API_KEY not set.", file=sys.stderr)
                    sys.exit(1)
                client = genai.Client(api_key=api_key)
            print(f"Translating {lid} ({len(de_text)} chars)")
            en_text = translate_to_english(de_text, client)
            with open(os.path.join(gdir, "en.txt"), "w", encoding="utf-8") as f:
                f.write(en_text + "\n")
            if args.latex:
                en_tex = to_latex_document(title=f"Letter {lid} (English)", body_text=en_text, lang="english")
                with open(os.path.join(gdir, "en.tex"), "w", encoding="utf-8") as f:
                    f.write(en_tex)

    print(f"Done. Letters in: {args.letters_dir}")


if __name__ == "__main__":
    main()
