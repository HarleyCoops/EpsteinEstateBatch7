#!/usr/bin/env python3
"""
Combined English Translation Script

This script reads all individual German text files from the 'german_output' directory,
sorts them numerically, concatenates their content, and then uses the Gemini AI
to translate the entire combined German text into English. The result is saved
to a single file.
"""
import os
import sys
import time
import traceback
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GERMAN_OUTPUT_DIR = os.path.join(BASE_DIR, 'german_output')
# Define output file for the combined English translation
COMBINED_ENGLISH_OUTPUT_FILE = os.path.join(BASE_DIR, 'translation_from_all_german_files.txt')

# Model and generation settings
MODEL_NAME = "gemini-2.5-pro-preview-05-06" # Using the same model as ImageTranslator
TRANSLATION_TEMPERATURE = 0.8 # Consistent with ImageTranslator

PROMPT_TRANSLATION_TEMPLATE = (
    "Translate the following combined German text, which consists of several concatenated documents, into English. "
    "Ensure the translation is fluent and accurately reflects the content of each original document segment. "
    "The segments are separated by lines like '--- End of content from [original_filename] ---'. Preserve the sense of these breaks, perhaps with a clear paragraph break or a similar textual separator in the English output if appropriate, but do not translate the separator lines themselves literally.\n\n"
    "German Text:\n"
    "---------------------\n"
    "{german_content}"
    "---------------------\n"
    "End of German Text.\n\n"
    "English Translation:"
)

def get_filenumber_for_german_file(filename):
    """
    Extracts the base number from a German filename like 'IMG_3762_german.txt'
    to ensure correct numerical sorting.
    Assumes format like 'PREFIX_NUMBER_german.txt' or 'NUMBER_german.txt'.
    """
    # Remove '_german.txt' suffix
    name_part = filename.replace('_german.txt', '')
    # Remove common prefixes like 'IMG_' if they exist before the number
    if '_' in name_part:
        name_part = name_part.split('_')[-1] # Takes the part after the last underscore

    number_str = ''.join(filter(str.isdigit, name_part))
    return int(number_str) if number_str.isdigit() else float('inf')

def translate_combined_german_to_english(german_text, client):
    """
    Translates a large block of German text to English using Gemini AI.
    Returns the translated English text.
    """
    print(f"  Translating {len(german_text)} characters of combined German text...")
    start_time = time.time()
    
    try:
        prompt = PROMPT_TRANSLATION_TEMPLATE.format(german_content=german_text)
        # print(f"  Translation prompt length: {len(prompt)} characters") # Optional: for debugging
        
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
                if chunk_count % 5 == 0: # Print progress less frequently for large texts
                    print(f"    Received translation chunk {chunk_count} ({len(chunk.text)} chars)")
            # else:
                # print(f"    Received empty translation chunk {chunk_count}") # Can be noisy
        
        print(f"  Translation complete! Took {time.time() - start_time:.2f} seconds")
        print(f"  Total English output length: {len(output)} characters")
        
        return output
        
    except Exception as e:
        print(f"  ERROR in translate_combined_german_to_english: {str(e)}")
        print(f"  Full traceback: {traceback.format_exc()}")
        raise

def main():
    print("Starting Combined English Translation Process...")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    if not os.path.isdir(GERMAN_OUTPUT_DIR):
        print(f"Error: German output directory not found: {GERMAN_OUTPUT_DIR}", file=sys.stderr)
        sys.exit(1)

    # Get and sort German text files
    german_files = sorted(
        (f for f in os.listdir(GERMAN_OUTPUT_DIR) if f.endswith('_german.txt')),
        key=get_filenumber_for_german_file
    )

    if not german_files:
        print(f"No German text files found in {GERMAN_OUTPUT_DIR}")
        return

    print(f"Found {len(german_files)} German text files to combine and translate.")

    combined_german_content = ""
    for i, german_file in enumerate(german_files, 1):
        file_path = os.path.join(GERMAN_OUTPUT_DIR, german_file)
        print(f"  ({i}/{len(german_files)}) Reading: {german_file}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if content.strip():
                combined_german_content += content
                # Add a separator, clearly indicating the source file
                combined_german_content += f"\n\n--- End of content from {german_file} ---\n\n"
            else:
                print(f"    Warning: File {german_file} is empty, skipping its content.")
        except Exception as e:
            print(f"    Error reading file {german_file}: {e}. Skipping.", file=sys.stderr)
            continue
    
    if not combined_german_content.strip():
        print("No content was aggregated from German files. Cannot proceed with translation.", file=sys.stderr)
        sys.exit(1)
        
    print(f"\nTotal combined German content length: {len(combined_german_content)} characters.")

    # Translate the combined German text
    try:
        print("\nStarting translation of combined German text...")
        english_translation = translate_combined_german_to_english(combined_german_content, client)
        
        print(f"\nSaving combined English translation to: {COMBINED_ENGLISH_OUTPUT_FILE}")
        with open(COMBINED_ENGLISH_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(english_translation)
        print("Combined English translation saved successfully.")
        
    except Exception as e:
        print(f"An error occurred during the translation or saving phase: {e}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)

    print("\nCombined English Translation Process Complete.")

if __name__ == "__main__":
    main() 