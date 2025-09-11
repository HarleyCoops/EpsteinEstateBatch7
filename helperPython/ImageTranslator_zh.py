#!/usr/bin/env python3
"""
ImageTranslator (Chinese)

Processes handwritten Chinese document images to:
1) Extract Chinese text to chinese_output/*_chinese.txt
2) Translate per-page to english_output/*_english.txt
3) Combine English to combined_english_translation.txt
4) (Optional) Narrative analysis over combined English
5) Generate LaTeX for combined English and Chinese
6) Format English for Google Docs (Markdown)

Prompts explicitly state: this is Chinese (not German, not Dorle context).
"""
import os
import sys
import time
import traceback
import argparse
from dotenv import load_dotenv

from google import genai
from google.genai import types

load_dotenv()

parser = argparse.ArgumentParser(description='Process handwritten Chinese documents through OCR, translation, and analysis pipeline.')
parser.add_argument('--input-dir', type=str, help='Input directory containing images (default: ./input)')
parser.add_argument('--output-base', type=str, help='Base directory for all outputs (default: current directory)')
parser.add_argument('--chinese-output-dir', type=str, help='Chinese OCR output directory (default: {output-base}/chinese_output)')
parser.add_argument('--english-output-dir', type=str, help='English translation output directory (default: {output-base}/english_output)')
args = parser.parse_args()

BASE_DIR = os.path.dirname(__file__)

if args.output_base:
    OUTPUT_BASE = args.output_base
    base_name = os.path.basename(OUTPUT_BASE)
    INPUT_DIR = args.input_dir if args.input_dir else os.path.join(OUTPUT_BASE, base_name)
    CHINESE_OUTPUT_DIR = args.chinese_output_dir if args.chinese_output_dir else os.path.join(OUTPUT_BASE, 'chinese_output')
    ENGLISH_OUTPUT_DIR = args.english_output_dir if args.english_output_dir else os.path.join(OUTPUT_BASE, 'english_output')
    COMBINED_OUTPUT_DIR = OUTPUT_BASE
else:
    INPUT_DIR = args.input_dir if args.input_dir else os.path.join(BASE_DIR, 'input')
    CHINESE_OUTPUT_DIR = args.chinese_output_dir if args.chinese_output_dir else os.path.join(BASE_DIR, 'chinese_output')
    ENGLISH_OUTPUT_DIR = args.english_output_dir if args.english_output_dir else os.path.join(BASE_DIR, 'english_output')
    COMBINED_OUTPUT_DIR = BASE_DIR

MODEL_NAME = "gemini-2.5-pro"
EXTRACTION_TEMPERATURE = 0.4
TRANSLATION_TEMPERATURE = 0.7
ANALYSIS_TEMPERATURE = 0.75
LATEX_GENERATION_TEMPERATURE = 0.2
GDOC_FORMAT_TEMPERATURE = 0.1

PROMPT_IMAGE_EXTRACTION = (
    "This is a single page image of a handwritten Chinese document.\n"
    "Extract the handwritten Chinese text exactly as it appears.\n"
    "Return the result in plain text format only."
)

PROMPT_TRANSLATION_TEMPLATE = (
    "You are a careful literary translator. Translate the following Chinese text into natural, idiomatic English, while preserving meaning, names, and paragraphing. "
    "This text is Chinese (not German) and not related to Dorle or any prior project context. "
    "Output only the translated text, with no preamble or labels.\n\n"
    "{chinese_content}"
)

PROMPT_NARRATIVE_ANALYSIS_TEMPLATE = (
    "You are a text analyst. Analyze the following English translation of a Chinese document. "
    "Identify key themes, narrative arc, main individuals, relationships, timeline, and socio-cultural context strictly from the text. "
    "Structure the analysis with clear sections and concise, evidence-based observations.\n\n"
    "--- BEGIN ENGLISH TEXT ---\n"
    "{english_letter_content}\n"
    "--- END ENGLISH TEXT ---"
)

PROMPT_ENGLISH_TO_LATEX_TEMPLATE = (
    "Convert the following English text into a clean LaTeX article document. "
    "Preserve paragraph breaks; do not add commentary. Provide only LaTeX.\n\n"
    "--- BEGIN TEXT ---\n"
    "{english_letter_content}\n"
    "--- END TEXT ---"
)

PROMPT_CHINESE_TO_LATEX_TEMPLATE = (
    "Create a LaTeX document suitable for Chinese text using ctex. "
    "Preserve paragraph breaks; do not add commentary. Provide only LaTeX.\n\n"
    "--- BEGIN CHINESE TEXT ---\n"
    "{chinese_letter_content}\n"
    "--- END CHINESE TEXT ---"
)

PROMPT_FORMAT_FOR_GDOC_TEMPLATE = (
    "Clean and minimally format the following English text as Markdown for pasting into Google Docs. "
    "Preserve paragraph breaks; convert thematic separators to '---' lines if present. "
    "Output only Markdown.\n\n"
    "--- BEGIN TEXT ---\n"
    "{combined_english_text}\n"
    "--- END TEXT ---"
)


def normalize_chinese_text(text: str) -> str:
    # For Chinese, just merge hard-wrapped lines inside paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n")]
    normalized = ["".join(p.splitlines()) for p in paragraphs]
    return "\n\n".join(normalized).strip()


def extract_chinese_text(image_path, client):
    print(f"  Uploading file: {image_path}")
    try:
        files = [client.files.upload(file=image_path)]
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(file_uri=files[0].uri, mime_type=files[0].mime_type),
                    types.Part.from_text(text=PROMPT_IMAGE_EXTRACTION),
                ],
            ),
        ]
        cfg = types.GenerateContentConfig(
            temperature=EXTRACTION_TEMPERATURE,
            response_mime_type="text/plain",
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(thinking_budget=512),
        )
        out = ""
        for chunk in client.models.generate_content_stream(model=MODEL_NAME, contents=contents, config=cfg):
            if chunk.text:
                out += chunk.text
        return out
    except Exception as e:
        print(f"  ERROR in extract_chinese_text: {e}")
        print(traceback.format_exc())
        raise


def translate_to_english(chinese_text, client):
    try:
        normalized = normalize_chinese_text(chinese_text)
        prompt = PROMPT_TRANSLATION_TEMPLATE.format(chinese_content=normalized)
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        cfg = types.GenerateContentConfig(
            temperature=TRANSLATION_TEMPERATURE,
            response_mime_type="text/plain",
            max_output_tokens=8192,
            thinking_config=types.ThinkingConfig(thinking_budget=1024),
        )
        out = ""
        for chunk in client.models.generate_content_stream(model=MODEL_NAME, contents=contents, config=cfg):
            if chunk.text:
                out += chunk.text
        return out
    except Exception as e:
        print(f"  ERROR in translate_to_english: {e}")
        print(traceback.format_exc())
        raise


def analyze_letters(english_text, client):
    prompt = PROMPT_NARRATIVE_ANALYSIS_TEMPLATE.format(english_letter_content=english_text)
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    cfg = types.GenerateContentConfig(
        temperature=ANALYSIS_TEMPERATURE,
        response_mime_type="text/plain",
        max_output_tokens=16384,
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
    )
    out = ""
    for chunk in client.models.generate_content_stream(model=MODEL_NAME, contents=contents, config=cfg):
        if chunk.text:
            out += chunk.text
    return out


def generate_latex_from_english(english_text, client):
    prompt = PROMPT_ENGLISH_TO_LATEX_TEMPLATE.format(english_letter_content=english_text)
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    cfg = types.GenerateContentConfig(
        temperature=LATEX_GENERATION_TEMPERATURE,
        response_mime_type="text/plain",
        max_output_tokens=16384,
        thinking_config=types.ThinkingConfig(thinking_budget=256),
    )
    out = ""
    for chunk in client.models.generate_content_stream(model=MODEL_NAME, contents=contents, config=cfg):
        if chunk.text:
            out += chunk.text
    return out


def generate_latex_from_chinese(chinese_text, client):
    prompt = PROMPT_CHINESE_TO_LATEX_TEMPLATE.format(chinese_letter_content=chinese_text)
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    cfg = types.GenerateContentConfig(
        temperature=LATEX_GENERATION_TEMPERATURE,
        response_mime_type="text/plain",
        max_output_tokens=16384,
        thinking_config=types.ThinkingConfig(thinking_budget=256),
    )
    out = ""
    for chunk in client.models.generate_content_stream(model=MODEL_NAME, contents=contents, config=cfg):
        if chunk.text:
            out += chunk.text
    return out


def format_english_for_gdoc(combined_english_text, client):
    prompt = PROMPT_FORMAT_FOR_GDOC_TEMPLATE.format(combined_english_text=combined_english_text)
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    cfg = types.GenerateContentConfig(
        temperature=GDOC_FORMAT_TEMPERATURE,
        response_mime_type="text/plain",
        max_output_tokens=8192,
        thinking_config=types.ThinkingConfig(thinking_budget=128),
    )
    out = ""
    for chunk in client.models.generate_content_stream(model=MODEL_NAME, contents=contents, config=cfg):
        if chunk.text:
            out += chunk.text
    if out.startswith("```"):
        out = out.split("\n", 1)[1] if "\n" in out else ""
    if out.endswith("```"):
        out = out.rsplit("\n", 1)[0] if "\n" in out else ""
    return out.strip()


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    os.makedirs(CHINESE_OUTPUT_DIR, exist_ok=True)
    os.makedirs(ENGLISH_OUTPUT_DIR, exist_ok=True)

    if not os.path.isdir(INPUT_DIR):
        print(f"Input directory not found: {INPUT_DIR}", file=sys.stderr)
        sys.exit(1)

    image_files_unsorted = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]

    def get_filenumber(filename):
        name_part = os.path.splitext(filename)[0]
        number_str = ''.join(filter(str.isdigit, name_part.split('_')[0]))
        return int(number_str) if number_str.isdigit() else float('inf')

    images = sorted(image_files_unsorted, key=get_filenumber)

    if not images:
        print(f"No images found in input directory: {INPUT_DIR}")
        return

    print(f"Found {len(images)} images to process\n")

    # Phase 1: OCR Chinese
    print("--- Phase 1: Extracting Chinese Text ---")
    zh_text_paths = []
    for i, image_file in enumerate(images, 1):
        stem, _ = os.path.splitext(image_file)
        zh_file = f"{stem}_chinese.txt"
        zh_path = os.path.join(CHINESE_OUTPUT_DIR, zh_file)
        zh_text_paths.append(zh_path)
        print(f"[{i}/{len(images)}] {image_file}")
        if os.path.exists(zh_path):
            print(f"  Skipping extraction (exists): {zh_file}")
            continue
        try:
            zh_text = extract_chinese_text(os.path.join(INPUT_DIR, image_file), client)
            with open(zh_path, 'w', encoding='utf-8') as f:
                f.write(zh_text)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    print("\n--- Phase 2: Translating Chinese Texts to English (One-to-One) ---")
    english_paths = []
    for i, (image_file, zh_path) in enumerate(zip(images, zh_text_paths), 1):
        stem = os.path.splitext(image_file)[0]
        en_file = f"{stem}_english.txt"
        en_path = os.path.join(ENGLISH_OUTPUT_DIR, en_file)
        english_paths.append(en_path)
        print(f"[{i}/{len(images)}] {os.path.basename(zh_path)} → {en_file}")
        if os.path.exists(en_path):
            print(f"  Skipping translation (exists): {en_file}")
            continue
        try:
            if not os.path.exists(zh_path):
                print("  Missing OCR file; skipping")
                continue
            with open(zh_path, 'r', encoding='utf-8') as f:
                zh_text = f.read()
            if not zh_text.strip():
                print("  Empty OCR; skipping")
                continue
            en_text = translate_to_english(zh_text, client)
            with open(en_path, 'w', encoding='utf-8') as f:
                f.write(en_text)
        except Exception as e:
            print(f"  ERROR translating: {e}")
            continue

    # Phase 3: Combine English
    combined_english_output = os.path.join(COMBINED_OUTPUT_DIR, 'combined_english_translation.txt')
    if os.path.exists(combined_english_output):
        print(f"\nSkipping combine (exists): {combined_english_output}")
    else:
        print("\n--- Phase 3: Combining English Texts ---")
        combined = []
        for p in english_paths:
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    combined.append(f.read().strip())
        combined_english = "\n\n---\n\n".join([c for c in combined if c])
        with open(combined_english_output, 'w', encoding='utf-8') as f:
            f.write(combined_english)
        print(f"Saved: {combined_english_output}")

    # Phase 4: Analysis
    if os.path.exists(combined_english_output):
        try:
            with open(combined_english_output, 'r', encoding='utf-8') as f:
                english_text = f.read()
            print("\n--- Phase 4: Narrative Analysis ---")
            analysis = analyze_letters(english_text, client)
            out_path = os.path.join(COMBINED_OUTPUT_DIR, 'narrative_analysis_of_chinese_text.txt')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(analysis)
            print(f"Saved analysis: {out_path}")
        except Exception as e:
            print(f"  Analysis error: {e}")

    # Phase 5: LaTeX outputs
    try:
        if os.path.exists(combined_english_output):
            with open(combined_english_output, 'r', encoding='utf-8') as f:
                english_text = f.read()
            en_tex = generate_latex_from_english(english_text, client)
            en_tex_path = os.path.join(COMBINED_OUTPUT_DIR, 'combined_english_letter.tex')
            with open(en_tex_path, 'w', encoding='utf-8') as f:
                f.write(en_tex)
            print(f"Saved: {en_tex_path}")
        # Also try to combine raw Chinese for LaTeX
        combined_chinese_output = os.path.join(COMBINED_OUTPUT_DIR, 'combined_chinese_text.txt')
        if not os.path.exists(combined_chinese_output):
            zh_combined = []
            for p in zh_text_paths:
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        zh_combined.append(f.read().strip())
            with open(combined_chinese_output, 'w', encoding='utf-8') as f:
                f.write("\n\n".join([c for c in zh_combined if c]))
        with open(combined_chinese_output, 'r', encoding='utf-8') as f:
            zh_text = f.read()
        zh_tex = generate_latex_from_chinese(zh_text, client)
        zh_tex_path = os.path.join(COMBINED_OUTPUT_DIR, 'combined_chinese_text.tex')
        with open(zh_tex_path, 'w', encoding='utf-8') as f:
            f.write(zh_tex)
        print(f"Saved: {zh_tex_path}")
    except Exception as e:
        print(f"  LaTeX generation error: {e}")

    # Phase 6: GDoc Markdown
    try:
        if os.path.exists(combined_english_output):
            with open(combined_english_output, 'r', encoding='utf-8') as f:
                english_text = f.read()
            md = format_english_for_gdoc(english_text, client)
            md_path = os.path.join(COMBINED_OUTPUT_DIR, 'combined_english_for_google_docs.md')
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"Saved: {md_path}")
    except Exception as e:
        print(f"  Markdown formatting error: {e}")

    print("\n--- All Processing Complete ---")


if __name__ == "__main__":
    main()

