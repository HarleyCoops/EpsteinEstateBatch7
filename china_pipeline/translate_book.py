#!/usr/bin/env python3
"""
Translate a single Chinese book/text file to English using Gemini 2.5 Pro.

Goals
- Treat the input as ONE continuous document (not letters).
- Make it explicit this is NOT German and NOT related to Dorle.
- Preserve paragraph breaks; add no headings, numbering, or commentary.

Usage
  python translate_chinese_book.py \
    --input-file chinese/zh.txt \
    --output-file chinese/en.txt \
    [--latex] [--force] [--chunk-chars 14000]
"""
from __future__ import annotations

import os
import sys
import argparse
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types


PROMPT_TRANSLATE = (
    "You are a careful literary translator. Translate the following Chinese book text into natural, idiomatic English.\n"
    "This is a single, continuous document (a book manuscript), not a set of letters.\n"
    "It is NOT German and NOT related to Dorle or any prior project context.\n"
    "Preserve paragraph breaks exactly. Do not add headings, numbering, footnotes, or commentary.\n"
    "Do not summarize; do not omit content. Output ONLY the translated text.\n\n"
    "--- BEGIN CHINESE TEXT ---\n"
    "{chinese}\n"
    "--- END CHINESE TEXT ---"
)


def to_latex_document(title: str, body_text: str) -> str:
    def esc(s: str) -> str:
        repl = {
            "\\": r"\\textbackslash{}",
            "{": r"\\{",
            "}": r"\\}",
            "$": r"\\$",
            "#": r"\\#",
            "&": r"\\&",
            "%": r"\\%",
            "_": r"\\_",
            "~": r"\\textasciitilde{}",
            "^": r"\\textasciicircum{}",
        }
        for k, v in repl.items():
            s = s.replace(k, v)
        return s

    return (
        "\\documentclass[12pt]{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[T1]{fontenc}\n"
        "\\usepackage[english]{babel}\n"
        "\\usepackage{geometry}\n\\geometry{margin=1in}\n"
        "\\usepackage{parskip}\n"
        "\\begin{document}\n"
        f"\\section*{{{esc(title)}}}\n"
        "\\noindent\n"
        f"{esc(body_text)}\n"
        "\\end{document}\n"
    )


def split_into_chunks(text: str, max_chars: int) -> List[str]:
    """Split text into chunks near max_chars, respecting paragraph breaks."""
    if len(text) <= max_chars:
        return [text]
    paras = text.split("\n\n")
    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for p in paras:
        # +2 accounts for the double newline when rejoining
        add_len = len(p) + (2 if cur else 0)
        if cur and cur_len + add_len > max_chars:
            chunks.append("\n\n".join(cur))
            cur = [p]
            cur_len = len(p)
        else:
            if cur:
                cur_len += 2  # for separator
            cur.append(p)
            cur_len += len(p)
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


def translate_chunk(chinese_text: str, client) -> str:
    prompt = PROMPT_TRANSLATE.format(chinese=chinese_text)
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
    return out.strip()


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser(description="Translate a single Chinese book/text file to English")
    ap.add_argument("--input-file", default=os.path.join("chinese", "zh.txt"))
    ap.add_argument("--output-file", default=os.path.join("chinese", "en.txt"))
    ap.add_argument("--latex", action="store_true", help="Also emit English LaTeX next to the output file")
    ap.add_argument("--force", action="store_true", help="Overwrite existing output file")
    ap.add_argument("--chunk-chars", type=int, default=14000, help="Approximate characters per chunk")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.input_file):
        print(f"Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(args.output_file) and not args.force:
        print(f"Output exists, skipping: {args.output_file} (use --force to overwrite)")
        return

    with open(args.input_file, "r", encoding="utf-8") as f:
        zh = f.read().strip()
    if not zh:
        print("Input is empty; nothing to translate.")
        # Still write empty output for completeness
        os.makedirs(os.path.dirname(args.output_file) or ".", exist_ok=True)
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write("")
        return

    client = genai.Client(api_key=api_key)

    chunks = split_into_chunks(zh, max_chars=args.chunk_chars)
    print(f"Translating book in {len(chunks)} chunk(s)…")
    outputs: List[str] = []
    for i, ch in enumerate(chunks, 1):
        print(f"  Chunk {i}/{len(chunks)} ({len(ch)} chars)")
        try:
            en = translate_chunk(ch, client)
        except Exception as e:
            print(f"    Translation error on chunk {i}: {e}", file=sys.stderr)
            raise
        outputs.append(en)

    english = "\n\n".join(outputs).strip()
    os.makedirs(os.path.dirname(args.output_file) or ".", exist_ok=True)
    with open(args.output_file, "w", encoding="utf-8") as f:
        f.write(english + "\n")

    if args.latex:
        title = os.path.splitext(os.path.basename(args.output_file))[0].replace("_", " ")
        en_tex = to_latex_document(title=f"{title} (English)", body_text=english)
        tex_path = os.path.join(os.path.dirname(args.output_file), "en.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(en_tex)

    print("Done.")


if __name__ == "__main__":
    main()

