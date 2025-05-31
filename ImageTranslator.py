#!/usr/bin/env python3
"""
StoryTranslator Script

Processes handwritten German document images to extract German text and translate it into English.
Results are saved as markdown files in separate output directories.
"""
import os
import sys
import time
import traceback
from dotenv import load_dotenv

# Use the same Google GenAI imports as the working Alberta/BC scripts
from google import genai
from google.genai import types

load_dotenv()

# Directory paths
BASE_DIR = os.path.dirname(__file__)
INPUT_DIR = os.path.join(BASE_DIR, 'input')
GERMAN_OUTPUT_DIR = os.path.join(BASE_DIR, 'german_output')
ENGLISH_OUTPUT_DIR = os.path.join(BASE_DIR, 'english_output')

# Model and generation settings
MODEL_NAME = "gemini-2.5-pro-preview-05-06"
EXTRACTION_TEMPERATURE = 0.3  # Lower temperature for accurate OCR
TRANSLATION_TEMPERATURE = 0.7  # Balance accuracy and fluency for translation

PROMPT_IMAGE_EXTRACTION = (
    "This is a single page image of a handwritten German document.\n"
    "Extract the handwritten German text exactly as it appears, preserving line breaks.\n"
    "Return the result in plain text format."
)

PROMPT_TRANSLATION_TEMPLATE = (
    "Translate the following German text to English, preserving line breaks and structure:\n\n"
    "{german_content}"
)

def extract_german_text(image_path, client):
    """
    Uses Gemini AI to perform OCR on a handwritten German image.
    Returns the extracted text.
    """
    print(f"  Uploading file: {image_path}")
    start_time = time.time()
    
    try:
        files = [
            client.files.upload(file=image_path),
        ]
        print(f"  File uploaded successfully. URI: {files[0].uri}")
        print(f"  Upload took {time.time() - start_time:.2f} seconds")
        
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
        
        generate_content_config = types.GenerateContentConfig(
            temperature=EXTRACTION_TEMPERATURE,
            response_mime_type="text/plain",
        )
        
        print(f"  Starting content generation with model: {MODEL_NAME}")
        generation_start = time.time()
        
        output = ""
        chunk_count = 0
        for chunk in client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=generate_content_config,
        ):
            chunk_count += 1
            if chunk.text:
                output += chunk.text
                print(f"  Received chunk {chunk_count} ({len(chunk.text)} chars)")
            else:
                print(f"  Received empty chunk {chunk_count}")
        
        print(f"  Generation complete! Took {time.time() - generation_start:.2f} seconds")
        print(f"  Total output length: {len(output)} characters")
        
        return output
        
    except Exception as e:
        print(f"  ERROR in extract_german_text: {str(e)}")
        print(f"  Full traceback: {traceback.format_exc()}")
        raise

def translate_to_english(german_text, client):
    """
    Translates German text to English using Gemini AI.
    Returns the translated text.
    """
    print(f"  Translating {len(german_text)} characters of German text")
    start_time = time.time()
    
    try:
        prompt = PROMPT_TRANSLATION_TEMPLATE.format(german_content=german_text)
        print(f"  Translation prompt length: {len(prompt)} characters")
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=TRANSLATION_TEMPERATURE,
            response_mime_type="text/plain",
        )
        
        print(f"  Starting translation with model: {MODEL_NAME}")
        
        output = ""
        chunk_count = 0
        for chunk in client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=generate_content_config,
        ):
            chunk_count += 1
            if chunk.text:
                output += chunk.text
                print(f"  Translation chunk {chunk_count} ({len(chunk.text)} chars)")
            else:
                print(f"  Received empty translation chunk {chunk_count}")
        
        print(f"  Translation complete! Took {time.time() - start_time:.2f} seconds")
        print(f"  Translation output length: {len(output)} characters")
        
        return output
        
    except Exception as e:
        print(f"  ERROR in translate_to_english: {str(e)}")
        print(f"  Full traceback: {traceback.format_exc()}")
        raise

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    # Use single client like the working Alberta/BC scripts
    client = genai.Client(api_key=api_key)

    # Ensure directories exist
    os.makedirs(GERMAN_OUTPUT_DIR, exist_ok=True)
    os.makedirs(ENGLISH_OUTPUT_DIR, exist_ok=True)

    if not os.path.isdir(INPUT_DIR):
        print(f"Input directory not found: {INPUT_DIR}", file=sys.stderr)
        sys.exit(1)

    # Process image files
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

        # Extract German text
        if os.path.exists(german_path):
            print(f"  Skipping extraction (exists): {german_file}")
        else:
            print(f"  Starting German text extraction...")
            try:
                overall_start = time.time()
                german_text = extract_german_text(
                    os.path.join(INPUT_DIR, image_file), client
                )
                
                print(f"  Saving German text to: {german_path}")
                with open(german_path, 'w', encoding='utf-8') as f:
                    f.write(german_text)
                
                print(f"  German extraction completed in {time.time() - overall_start:.2f} seconds")
                
            except Exception as e:
                print(f"  ERROR extracting {image_file}: {e}", file=sys.stderr)
                print(f"  Full traceback: {traceback.format_exc()}", file=sys.stderr)
                continue

        # Translate to English
        if os.path.exists(english_path):
            print(f"  Skipping translation (exists): {english_file}")
        else:
            print(f"  Starting English translation...")
            try:
                with open(german_path, 'r', encoding='utf-8') as f:
                    german_text = f.read()
                
                if not german_text.strip():
                    print(f"  WARNING: German text file is empty, skipping translation")
                    continue
                
                overall_start = time.time()
                english_text = translate_to_english(german_text, client)
                
                print(f"  Saving English translation to: {english_path}")
                with open(english_path, 'w', encoding='utf-8') as f:
                    f.write(english_text)
                
                print(f"  Translation completed in {time.time() - overall_start:.2f} seconds")
                
            except Exception as e:
                print(f"  ERROR translating {german_file}: {e}", file=sys.stderr)
                print(f"  Full traceback: {traceback.format_exc()}", file=sys.stderr)
                continue
        
        print(f"  ✓ Completed processing {image_file}\n")

    print(f"Processing complete. German texts in {GERMAN_OUTPUT_DIR}, English translations in {ENGLISH_OUTPUT_DIR}.")


if __name__ == "__main__":
    main()