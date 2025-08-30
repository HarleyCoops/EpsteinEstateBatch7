#!/usr/bin/env python3
"""
Translate grouped German letters (de.txt) to English using Gemini 2.5 Pro.

Inputs
- --letters-dir: directory containing Lxxxx/ subfolders with de.txt

Outputs (per letter)
- en.txt          (plain English translation)
- en.tex (opt)    (deterministic LaTeX of the English text; no LLM)

Notes
- No narrative or analysis; strict one-to-one letter translation.
- The prompt forbids headings/numbering/commentary. Output is plain text only.
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
    "Translate the following German letter to natural, idiomatic English.\n"
    "Preserve meaning, dates, names, and paragraph breaks.\n"
    "Do not add headings, numbering, labels, or commentary.\n"
    "Output only the translated text.\n\n"
    "--- BEGIN GERMAN ---\n"
    "{german}\n"
    "--- END GERMAN ---"
)


def list_letter_dirs(letters_dir: str) -> List[str]:
    if not os.path.isdir(letters_dir):
        return []
    dirs: List[str] = []
    for name in os.listdir(letters_dir):
        path = os.path.join(letters_dir, name)
        if not os.path.isdir(path):
            continue
        # Accept both legacy "L0001" and new "<Collection> L0001" directories
        if os.path.isfile(os.path.join(path, "de.txt")):
            dirs.append(path)
    dirs.sort()
    return dirs


def to_latex_document(title: str, body_text: str) -> str:
    def esc(s: str) -> str:
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


def translate_letter(german_text: str, client) -> str:
    prompt = PROMPT_TRANSLATE.format(german=german_text)
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
    ap = argparse.ArgumentParser(description="Translate grouped German letters to English")
    ap.add_argument("--letters-dir", default="letters")
    ap.add_argument("--latex", action="store_true")
    ap.add_argument("--force", action="store_true", help="Overwrite existing en.txt")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    letter_dirs = list_letter_dirs(args.letters_dir)
    if not letter_dirs:
        print(f"No letter directories found in {args.letters_dir}")
        return

    for ldir in letter_dirs:
        de_path = os.path.join(ldir, "de.txt")
        en_path = os.path.join(ldir, "en.txt")
        if not os.path.exists(de_path):
            continue
        if os.path.exists(en_path) and not args.force:
            print(f"Skip existing: {en_path}")
            continue

        with open(de_path, "r", encoding="utf-8") as f:
            german = f.read().strip()
        if not german:
            with open(en_path, "w", encoding="utf-8") as f:
                f.write("")
            continue

        print(f"Translating {ldir} ({len(german)} chars)")
        try:
            english = translate_letter(german, client)
        except Exception as e:
            print(f"  Translation error: {e}", file=sys.stderr)
            continue

        with open(en_path, "w", encoding="utf-8") as f:
            f.write(english + "\n")

        if args.latex:
            en_tex = to_latex_document(title=f"{os.path.basename(ldir)} (English)", body_text=english)
            with open(os.path.join(ldir, "en.tex"), "w", encoding="utf-8") as f:
                f.write(en_tex)

    print("Done.")


if __name__ == "__main__":
    main()
