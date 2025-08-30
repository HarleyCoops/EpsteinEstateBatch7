#!/usr/bin/env python3
"""
openai_imageTranslator Script

Processes handwritten German document images to extract German text and translate to English using OpenAI API.
Results are saved as text files in separate output directories.
"""
import os
import sys
import time
import traceback
import base64
import io
from PIL import Image

from dotenv import load_dotenv
import openai

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
INPUT_DIR = os.path.join(BASE_DIR, 'input')
GERMAN_OUTPUT_DIR = os.path.join(BASE_DIR, 'german_output')
ENGLISH_OUTPUT_DIR = os.path.join(BASE_DIR, 'english_output')

OCR_MODEL = os.getenv('OCR_MODEL', 'o3')
TRANSLATION_MODEL = os.getenv('TRANSLATION_MODEL', 'gpt-4.1')
#OCR_TEMPERATURE = float(os.getenv('OCR_TEMPERATURE', 0.3))
#TRANSLATION_TEMPERATURE = float(os.getenv('TRANSLATION_TEMPERATURE', 0.7))

PROMPT_IMAGE_EXTRACTION = (
    "extract the original german from this file and extract German in a text file. "
    "Offer no explanations or ancillary commentary. Only reply with German text extractions"
)

PROMPT_TRANSLATION_TEMPLATE = (
    "translate this extracted Text to english\n\n\n{german_content}"
)

client = openai.OpenAI()

def extract_german_text(image_path):
    """Extract handwritten German text from an image using OpenAI vision-enabled model."""
    print(f"  Reading image file: {image_path}")
    start_time = time.time()
    try:
        # Open the image and resize it
        with Image.open(image_path) as img:
            # Determine the new size, maintaining aspect ratio
            max_dim = 1024  # Max dimension for the longest side
            if max(img.size) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

            # Save the resized image to a BytesIO object
            buffered = io.BytesIO()
            mime_type = _get_mime_type(image_path)
            # PIL save function needs format, e.g., 'JPEG' or 'PNG'
            img_format = 'JPEG' if mime_type == 'image/jpeg' else 'PNG'
            img.save(buffered, format=img_format)
            image_data = buffered.getvalue()

        encoded_image = base64.b64encode(image_data).decode('ascii')
        image_url = f"data:{mime_type};base64,{encoded_image}"

        response = client.chat.completions.create(
            model=OCR_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PROMPT_IMAGE_EXTRACTION
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            max_completion_tokens=4096
        )
        german_text = response.choices[0].message.content
        print(f"  Extraction complete in {time.time() - start_time:.2f} seconds")
        print(f"  Extracted {len(german_text)} characters of German text")
        return german_text
    except Exception as e:
        print(f"  ERROR in extract_german_text: {e}")
        print(f"  Full traceback: {traceback.format_exc()}")
        raise

def translate_to_english(german_text):
    """Translate German text to English using OpenAI chat model."""
    print(f"  Translating {len(german_text)} characters of German text")
    start_time = time.time()
    try:
        prompt = PROMPT_TRANSLATION_TEMPLATE.format(german_content=german_text)
        response = client.chat.completions.create(
            model=TRANSLATION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            temperature=1.0,
            max_tokens=4000,
            top_p=1.0
        )
        english_text = response.choices[0].message.content
        print(f"  Translation complete in {time.time() - start_time:.2f} seconds")
        print(f"  Translated {len(english_text)} characters of English text")
        return english_text
    except Exception as e:
        print(f"  ERROR in translate_to_english: {e}", file=sys.stderr)
        print(f"  Full traceback: {traceback.format_exc()}", file=sys.stderr)
        raise

def _get_mime_type(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        return 'image/jpeg'
    if ext == '.png':
        return 'image/png'
    return 'application/octet-stream'

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)
    os.makedirs(GERMAN_OUTPUT_DIR, exist_ok=True)
    os.makedirs(ENGLISH_OUTPUT_DIR, exist_ok=True)
    if not os.path.isdir(INPUT_DIR):
        print(f"Input directory not found: {INPUT_DIR}", file=sys.stderr)
        sys.exit(1)
    images = sorted(
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    )
    if not images:
        print(f"No images found in input directory: {INPUT_DIR}")
        return
    print(f"Found {len(images)} images to process\n")
    for i, image_file in enumerate(images, 1):
        print(f"[{i}/{len(images)}] Processing: {image_file}")
        stem, _ = os.path.splitext(image_file)
        german_file = f"{stem}_german.txt"
        english_file = f"{stem}_english.txt"
        german_path = os.path.join(GERMAN_OUTPUT_DIR, german_file)
        english_path = os.path.join(ENGLISH_OUTPUT_DIR, english_file)
        if os.path.exists(german_path):
            print(f"  Skipping extraction (exists): {german_file}")
        else:
            print("  Starting German text extraction...")
            try:
                german_text = extract_german_text(os.path.join(INPUT_DIR, image_file))
                with open(german_path, 'w', encoding='utf-8') as f:
                    f.write(german_text)
            except Exception:
                continue
        if os.path.exists(english_path):
            print(f"  Skipping translation (exists): {english_file}")
        else:
            print("  Starting English translation...")
            try:
                with open(german_path, 'r', encoding='utf-8') as f:
                    german_text = f.read()
                if not german_text.strip():
                    print("  WARNING: German text file is empty, skipping translation")
                    continue
                english_text = translate_to_english(german_text)
                with open(english_path, 'w', encoding='utf-8') as f:
                    f.write(english_text)
            except Exception:
                continue
        print(f"  ✓ Completed processing {image_file}\n")
    print(f"Processing complete. German texts in {GERMAN_OUTPUT_DIR}, English translations in {ENGLISH_OUTPUT_DIR}.")

if __name__ == "__main__":
    main()
