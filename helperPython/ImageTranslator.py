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
import argparse
from dotenv import load_dotenv

# Use the same Google GenAI imports as the working Alberta/BC scripts
from google import genai
from google.genai import types

load_dotenv()

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Process handwritten German documents through OCR, translation, and analysis pipeline.')
parser.add_argument('--input-dir', type=str, help='Input directory containing images (default: ./input)')
parser.add_argument('--output-base', type=str, help='Base directory for all outputs (default: current directory)')
parser.add_argument('--german-output-dir', type=str, help='German OCR output directory (default: {output-base}/german_output)')
parser.add_argument('--english-output-dir', type=str, help='English translation output directory (default: {output-base}/english_output)')
args = parser.parse_args()

# Directory paths
BASE_DIR = os.path.dirname(__file__)

# Determine directories based on arguments
if args.output_base:
    OUTPUT_BASE = args.output_base
    # For DorleLettersE/F/G, the input is in a subdirectory with the same name
    base_name = os.path.basename(OUTPUT_BASE)
    INPUT_DIR = args.input_dir if args.input_dir else os.path.join(OUTPUT_BASE, base_name)
    GERMAN_OUTPUT_DIR = args.german_output_dir if args.german_output_dir else os.path.join(OUTPUT_BASE, 'german_output')
    ENGLISH_OUTPUT_DIR = args.english_output_dir if args.english_output_dir else os.path.join(OUTPUT_BASE, 'english_output')
    # For combined outputs, use output_base instead of BASE_DIR
    COMBINED_OUTPUT_DIR = OUTPUT_BASE
else:
    INPUT_DIR = args.input_dir if args.input_dir else os.path.join(BASE_DIR, 'input')
    GERMAN_OUTPUT_DIR = args.german_output_dir if args.german_output_dir else os.path.join(BASE_DIR, 'german_output')
    ENGLISH_OUTPUT_DIR = args.english_output_dir if args.english_output_dir else os.path.join(BASE_DIR, 'english_output')
    # For default mode, combined outputs go to BASE_DIR
    COMBINED_OUTPUT_DIR = BASE_DIR

# Model and generation settings
MODEL_NAME = "gemini-2.5-pro"
EXTRACTION_TEMPERATURE = 0.4  # Lower temperature for accurate OCR
TRANSLATION_TEMPERATURE = 0.8  # Balance accuracy and fluency for translation
ANALYSIS_TEMPERATURE = 0.75 # For nuanced and insightful interpretations
LATEX_GENERATION_TEMPERATURE = 0.2 # Lower temperature for precise LaTeX code
GDOC_FORMAT_TEMPERATURE = 0.1 # Low temperature for minimal alteration, just cleanup.

PROMPT_IMAGE_EXTRACTION = (
    "This is a single page image of a handwritten German document.\\n"
    "Extract the handwritten German text exactly as it appears.\\n"
    "Return the result in plain text format."
)

PROMPT_TRANSLATION_TEMPLATE = (
    "You are a careful literary translator. Translate the following mid-20th-century German letter into natural, idiomatic English as if written by a native speaker, while preserving meaning, factual details, dates, names, and measurement units. "
    "Guidelines: Resolve line-wrap hyphenations and hard line breaks inside paragraphs; keep paragraph breaks from the original; prefer fluent phrasing over literal calques; split or join sentences for readability when appropriate; do not add explanations or commentary, and do not omit content. "
    "Output only the translated text, with no preamble or labels.\\n\\n"
    "{german_content}"
)

PROMPT_NARRATIVE_ANALYSIS_TEMPLATE = (
    "You are a socio-historical analyst with deep expertise in epistolary communication and mid-20th century European daily life. "
    "You have been provided with a series of translated personal letters. Your task is to conduct a PhD-level analysis of these letters. "
    "Synthesize the information to construct a compelling narrative that offers a profound glimpse into the daily lives, experiences, relationships, and socio-economic context of the individuals involved. "
    "Focus meticulously on the following aspects:\\n\\n"
    "1.  **Narrative Reconstruction & Thematic Analysis:** Weave together the events, concerns, and activities mentioned into a coherent story. Identify the central themes and recurring motifs that emerge from these letters (e.g., family ties, economic concerns, personal aspirations, search for opportunities, post-war adjustments if applicable).\\n"
    "2.  **In-depth Character Analysis:** Identify all key individuals (sender, recipients, other mentioned persons). Based SOLELY on the textual evidence, construct detailed profiles. Describe their inferred personalities, roles within the family/social structure, relationships (including power dynamics and emotional undertones), and their psychological states (aspirations, anxieties, joys, frustrations).\\n"
    "3.  **Socio-Economic & Historical Contextualization:** Analyze subtle clues related to their economic situation, professions, cost of goods, consumption patterns (e.g., shopping habits, types of purchases), and living conditions. What can be inferred about their social standing, class, and the broader economic and historical environment they are navigating? Are there any hints towards specific historical events or periods?\\n"
    "4.  **Cultural Practices & Daily Life Insights:** Describe their daily routines, leisure activities (e.g., music, social gatherings, intellectual pursuits), social interactions, and cultural references. What do these details reveal about their lifestyle, values, access to cultural resources, and engagement with contemporary society?\\n"
    "5.  **Future Plans, Ambitions, and Uncertainties:** Identify and critically discuss any future plans, career aspirations (including international opportunities), travel desires, or significant life decisions mentioned. How do these reflect their hopes, fears, and the constraints or opportunities of their time?\\n"
    "6.  **Epistolary Analysis:** Analyze the language, tone, implicit meanings, and style of the letters. What does the form and content of their communication reveal about the relationships between the correspondents, the social conventions of letter-writing, and the expression of emotion during that period?\\n\\n"
    "Present your analysis as a well-structured, insightful, and academically rigorous essay. "
    "Go beyond surface-level observations; interpret the textual evidence critically, draw nuanced conclusions, and support your assertions with specific examples from the letters. "
    "These are authentic historical personal documents; your analysis should reflect their value as primary sources, offering a window into real human experiences.\\n\\n"
    "The combined text of the letters is as follows:\\n\\n"
    "--- BEGIN LETTERS ---\\n"
    "{english_letter_content}\\n"
    "--- END LETTERS ---"
)

PROMPT_ENGLISH_TO_LATEX_TEMPLATE = (
    "You are an expert in LaTeX document formatting. You have been provided with the combined text of several translated English letters. "
    "The text is concatenated, with separators like '--- End of Document from [filename] ---' marking the transition between original documents.\\n"
    "Your task is to convert this entire text into a single, well-formatted, and compilable LaTeX 'article' class document.\\n\\n"
    "**Formatting Rules:**\\n"
    "1.  **Document Class & Packages:** Use `\\documentclass{{article}}`. Include `\\usepackage[utf8]{{inputenc}}` for UTF-8 support and `\\usepackage{{geometry}}` with `\\geometry{{a4paper, margin=1in}}` for margins.\\n"
    "2.  **Traceability:** For each segment, you MUST add a header to indicate its source. Before the text from a file like '--- End of Document from IMG_1234_german.txt ---', you must insert a subsection command like: `\\subsection*{{Source: IMG_1234.jpg}}`. Extract the original filename (e.g., 'IMG_1234.jpg') from the separator string.\\n"
    "3.  **Separators:** Do NOT render the '--- End of Document from...' separators in the output. Their only purpose is to provide the source filename for the `\\subsection*` command.\\n"
    "4.  **Paragraphs:** Preserve all paragraph breaks from the input text. A blank line in the input signifies a new paragraph in the LaTeX output.\\n"
    "5.  **Special Characters:** Handle special LaTeX characters (e.g., $, %, &, #, _, {{, }}) by escaping them correctly (e.g., `\\$`, `\\%`, `\\&`, `\\#`, `\\_`, `\\{{`, `\\}}`)..\\n"
    "6.  **Output:** The output must be ONLY the valid, self-contained LaTeX code, starting with `\\documentclass{{article}}` and ending with `\\end{{document}}`. Do not add any commentary.\\n\\n"
    "Here is the English text to convert:\\n\\n"
    "--- BEGIN ENGLISH TEXT ---\\n"
    "{english_letter_content}\\n"
    "--- END ENGLISH TEXT ---"
)

PROMPT_GERMAN_TO_LATEX_TEMPLATE = (
    "You are an expert in LaTeX document formatting. You have been provided with the combined text of several German letters. "
    "The text is concatenated, with separators like '--- End of Document from [filename] ---' marking the transition between original documents.\\n"
    "Your task is to convert this entire text into a single, well-formatted, and compilable LaTeX 'article' class document suitable for German text.\\n\\n"
    "**Formatting Rules:**\\n"
    "1.  **Document Class & Packages:** Use `\\documentclass{{article}}`. For proper German typesetting, include `\\usepackage[utf8]{{inputenc}}` and `\\usepackage[T1]{{fontenc}}`. Also include `\\usepackage{{geometry}}` with `\\geometry{{a4paper, margin=1in}}`.\\n"
    "2.  **Traceability:** For each segment, you MUST add a header to indicate its source. Before the text from a file like '--- End of Document from IMG_1234_german.txt ---', you must insert a subsection command like: `\\subsection*{{Quelle: IMG_1234.jpg}}`. Extract the original filename (e.g., 'IMG_1234.jpg') from the separator string.\\n"
    "3.  **Separators:** Do NOT render the '--- End of Document from...' separators in the output. Their only purpose is to provide the source filename for the `\\subsection*` command.\\n"
    "4.  **Paragraphs:** Preserve all paragraph breaks from the input text. A blank line in the input signifies a new paragraph in the LaTeX output.\\n"
    "5.  **Special Characters:** Handle special LaTeX characters (e.g., $, %, &, #, _, {{, }}) by escaping them correctly (e.g., `\\$`, `\\%`, `\\&`, `\\#`, `\\_`, `\\{{`, `\\}}`).\\n"
    "6.  **Output:** The output must be ONLY the valid, self-contained LaTeX code, starting with `\\documentclass{{article}}` and ending with `\\end{{document}}`. Do not add any commentary.\\n\\n"
    "Here is the German text to convert:\\n\\n"
    "--- BEGIN GERMAN TEXT ---\\n"
    "{german_letter_content}\\n"
    "--- END GERMAN TEXT ---"
)

PROMPT_FORMAT_FOR_GDOC_TEMPLATE = (
    "You are an expert text formatter. The following text is a compilation of several English letters, "
    "separated by a Markdown thematic break ('---'). Your task is to ensure this text is presented as clean, "
    "readable Markdown, suitable for pasting directly into a Google Doc. "
    "Preserve all existing paragraph breaks (typically indicated by blank lines). "
    "Ensure that the thematic breaks ('---') used to separate individual letters are correctly formatted as standalone Markdown thematic breaks. "
    "Do not add any new content, titles, or commentary. Simply ensure the provided text is well-formed Markdown. "
    "The text is:\\n\\n"
    "--- BEGIN TEXT ---\\n"
    "{combined_english_text}\\n"
    "--- END TEXT ---"
)

def normalize_german_text(text: str) -> str:
    """
    Normalize OCR German text before translation:
    - De-hyphenate across line breaks (e.g., 'Osterge-\\nschenk' -> 'Ostergeschenk')
    - Merge hard-wrapped lines within paragraphs, preserving paragraph breaks
    """
    # Join hyphenated line breaks
    joined = text.replace("-\n", "")
    # Preserve paragraph breaks (double newlines), merge single newlines within paragraphs
    paragraphs = [p.strip() for p in joined.split("\n\n")]
    normalized_paragraphs = [" ".join(p.splitlines()) for p in paragraphs]
    return "\n\n".join(normalized_paragraphs).strip()

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
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(thinking_budget=512),
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
    
    # Add retry logic for connection errors
    max_retries = 3
    retry_delay = 10  # Start with 10 seconds delay
    
    for attempt in range(max_retries):
        try:
            # For very large texts (>30k chars), warn and proceed
            if len(german_text) > 30000:
                print(f"  WARNING: Large text ({len(german_text)} chars). This may take longer...")
            
            normalized_text = normalize_german_text(german_text)
            prompt = PROMPT_TRANSLATION_TEMPLATE.format(german_content=normalized_text)
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
                temperature=0.6,
                top_p=0.8,
                response_mime_type="text/plain",
                max_output_tokens=8192,
                thinking_config=types.ThinkingConfig(thinking_budget=2048),
            )
            
            print(f"  Starting translation with model: {MODEL_NAME} (attempt {attempt + 1}/{max_retries})")
            
            output = ""
            chunk_count = 0
            last_chunk_time = time.time()
            
            for chunk in client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=contents,
                config=generate_content_config,
            ):
                chunk_count += 1
                current_time = time.time()
                
                if chunk.text:
                    output += chunk.text
                    # Only print every 5th chunk to reduce output noise
                    if chunk_count % 5 == 0:
                        print(f"  Translation chunk {chunk_count} ({len(output)} total chars, {current_time - last_chunk_time:.1f}s since last)")
                    last_chunk_time = current_time
                else:
                    print(f"  Received empty translation chunk {chunk_count}")
            
            print(f"  Translation complete! Took {time.time() - start_time:.2f} seconds")
            print(f"  Translation output length: {len(output)} characters")
            
            return output
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ERROR in translate_to_english (attempt {attempt + 1}/{max_retries}): {error_msg}")
            
            # Check if it's a connection error that we should retry
            if "disconnected" in error_msg.lower() or "timeout" in error_msg.lower():
                if attempt < max_retries - 1:
                    print(f"  Connection error detected. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
            
            # If not a connection error or last attempt, print full trace and raise
            print(f"  Full traceback: {traceback.format_exc()}")
            raise

def analyze_letters(english_text, client):
    """
    Analyzes the combined English letters using Gemini AI with a specific prompt.
    Returns the analysis text.
    """
    print(f"  Analyzing {len(english_text)} characters of combined English letters")
    start_time = time.time()
    
    try:
        prompt = PROMPT_NARRATIVE_ANALYSIS_TEMPLATE.format(english_letter_content=english_text)
        print(f"  Analysis prompt length: {len(prompt)} characters")
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=ANALYSIS_TEMPERATURE, # Using the new temperature setting
            response_mime_type="text/plain",
            max_output_tokens=16384,
            thinking_config=types.ThinkingConfig(thinking_budget=-1),  # dynamic thinking
        )
        
        print(f"  Starting narrative analysis with model: {MODEL_NAME}")
        
        output = ""
        chunk_count = 0
        # Using generate_content_stream for potentially long outputs, similar to other calls
        for chunk in client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=generate_content_config,
        ):
            chunk_count += 1
            if chunk.text:
                output += chunk.text
                print(f"  Analysis chunk {chunk_count} ({len(chunk.text)} chars)")
            else:
                print(f"  Received empty analysis chunk {chunk_count}")
        
        print(f"  Narrative analysis complete! Took {time.time() - start_time:.2f} seconds")
        print(f"  Analysis output length: {len(output)} characters")
        
        return output
        
    except Exception as e:
        print(f"  ERROR in analyze_letters: {str(e)}")
        print(f"  Full traceback: {traceback.format_exc()}")
        raise

def generate_latex_from_english(english_text, client):
    """
    Converts combined English text to a LaTeX document using Gemini AI.
    Returns the LaTeX code as a string.
    """
    print(f"  Generating LaTeX for {len(english_text)} characters of English text")
    start_time = time.time()
    
    try:
        prompt = PROMPT_ENGLISH_TO_LATEX_TEMPLATE.format(english_letter_content=english_text)
        print(f"  LaTeX generation prompt length: {len(prompt)} characters")
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=LATEX_GENERATION_TEMPERATURE,
            response_mime_type="text/plain", # Expecting raw LaTeX code
            max_output_tokens=16384,
            thinking_config=types.ThinkingConfig(thinking_budget=256),
        )
        
        print(f"  Starting LaTeX generation with model: {MODEL_NAME}")
        
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
                # Avoid printing too much for potentially large LaTeX output, maybe just chunk count
                if chunk_count % 10 == 0 or len(chunk.text) > 100: # Print less frequently
                    print(f"  Received LaTeX chunk {chunk_count} (length {len(chunk.text)} chars)")
            else:
                print(f"  Received empty LaTeX chunk {chunk_count}")
        
        print(f"  LaTeX generation complete! Took {time.time() - start_time:.2f} seconds")
        print(f"  Generated LaTeX output length: {len(output)} characters")
        
        return output
        
    except Exception as e:
        print(f"  ERROR in generate_latex_from_english: {str(e)}")
        print(f"  Full traceback: {traceback.format_exc()}")
        raise

def generate_latex_from_german(german_text, client):
    """
    Converts combined German text to a LaTeX document using Gemini AI.
    Returns the LaTeX code as a string.
    """
    print(f"  Generating LaTeX for {len(german_text)} characters of German text")
    start_time = time.time()

    try:
        prompt = PROMPT_GERMAN_TO_LATEX_TEMPLATE.format(german_letter_content=german_text)
        print(f"  German LaTeX generation prompt length: {len(prompt)} characters")

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            temperature=LATEX_GENERATION_TEMPERATURE,
            response_mime_type="text/plain", # Expecting raw LaTeX code
            max_output_tokens=16384,
            thinking_config=types.ThinkingConfig(thinking_budget=256),
        )

        print(f"  Starting German LaTeX generation with model: {MODEL_NAME}")

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
                if chunk_count % 10 == 0 or len(chunk.text) > 100:
                    print(f"  Received German LaTeX chunk {chunk_count} (length {len(chunk.text)} chars)")
            else:
                print(f"  Received empty German LaTeX chunk {chunk_count}")

        print(f"  German LaTeX generation complete! Took {time.time() - start_time:.2f} seconds")
        print(f"  Generated German LaTeX output length: {len(output)} characters")

        return output

    except Exception as e:
        print(f"  ERROR in generate_latex_from_german: {str(e)}")
        print(f"  Full traceback: {traceback.format_exc()}")
        raise

def format_english_for_gdoc(combined_english_text, client):
    """
    Formats the combined English text as clean Markdown for Google Docs pasting.
    Returns the formatted Markdown text.
    """
    print(f"  Formatting {len(combined_english_text)} characters of English text for Google Docs (Markdown)...")
    start_time = time.time()
    
    try:
        prompt = PROMPT_FORMAT_FOR_GDOC_TEMPLATE.format(combined_english_text=combined_english_text)
        # print(f"  GDoc Formatting prompt length: {len(prompt)} characters") # Can be verbose
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=GDOC_FORMAT_TEMPERATURE,
            response_mime_type="text/plain",
            max_output_tokens=8192,
            thinking_config=types.ThinkingConfig(thinking_budget=128),
        )
        
        print(f"  Starting GDoc Markdown formatting with model: {MODEL_NAME}")
        
        output = ""
        # Using generate_content directly as the input/output should not be excessively large here
        # and streaming might be overkill for a simple formatting pass.
        # However, to be consistent with other calls and handle potential edge cases of long texts:
        for chunk in client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                output += chunk.text
        
        print(f"  GDoc Markdown formatting complete! Took {time.time() - start_time:.2f} seconds")
        # print(f"  Formatted Markdown output length: {len(output)} characters")
        
        # The LLM might sometimes wrap the output in ```markdown ... ```, remove if present.
        if output.startswith("```markdown"):
            output = output.split("\n", 1)[1] if "\n" in output else ""
        if output.endswith("```"):
            output = output.rsplit("\n", 1)[0] if "\n" in output else ""
        return output.strip()
        
    except Exception as e:
        print(f"  ERROR in format_english_for_gdoc: {str(e)}")
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

    # Get image files
    image_files_unsorted = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]

    # Sort image files numerically based on the number in their filename
    def get_filenumber(filename):
        # Extracts number from filename like "3762_anything.jpg" or "3762.jpg"
        name_part = os.path.splitext(filename)[0]
        number_str = ''.join(filter(str.isdigit, name_part.split('_')[0]))
        return int(number_str) if number_str.isdigit() else float('inf') # Place non-numeric names at the end

    images = sorted(image_files_unsorted, key=get_filenumber)

    if not images:
        print(f"No images found in input directory: {INPUT_DIR}")
        return

    print(f"Found {len(images)} images to process\n")
    
    # Phase 1: Extract German text from all images
    print("--- Phase 1: Extracting German Text ---")
    german_texts_paths = [] # Store paths for ordered reading later

    for i, image_file in enumerate(images, 1):
        print(f"[{i}/{len(images)}] Processing for German extraction: {image_file}")
        
        stem, _ = os.path.splitext(image_file)
        german_file_name = f"{stem}_german.txt"
        german_path = os.path.join(GERMAN_OUTPUT_DIR, german_file_name)
        german_texts_paths.append(german_path) # Save path for later

        # Extract German text
        if os.path.exists(german_path):
            print(f"  Skipping extraction (exists): {german_file_name}")
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
                
                print(f"  German extraction for {image_file} completed in {time.time() - overall_start:.2f} seconds\n")
                
            except Exception as e:
                print(f"  ERROR extracting {image_file}: {e}", file=sys.stderr)
                print(f"  Full traceback: {traceback.format_exc()}", file=sys.stderr)
                # Decide if we should continue with other files or stop
                # For now, we'll skip to the next file
                continue 
        
    print("\n--- German Text Extraction Phase Complete ---")

    # Phase 2: Translate each German text to English individually
    print("\n--- Phase 2: Translating German Texts to English (One-to-One) ---")
    
    english_texts_paths = []  # Store paths for English files
    
    for i, (image_file, german_path) in enumerate(zip(images, german_texts_paths), 1):
        if os.path.exists(german_path):
            # Derive English file path
            stem = os.path.splitext(image_file)[0]
            english_file_name = f"{stem}_english.txt"
            english_path = os.path.join(ENGLISH_OUTPUT_DIR, english_file_name)
            english_texts_paths.append(english_path)
            
            print(f"[{i}/{len(images)}] Processing translation: {os.path.basename(german_path)} → {english_file_name}")
            
            # Check if English translation already exists
            if os.path.exists(english_path):
                print(f"  Skipping translation (exists): {english_file_name}")
            else:
                try:
                    # Read German text
                    with open(german_path, 'r', encoding='utf-8') as f:
                        german_text = f.read()
                    
                    if not german_text.strip():
                        print(f"  WARNING: German text file {german_path} is empty. Skipping translation.")
                        continue
                    
                    # Translate to English
                    print(f"  Starting English translation...")
                    translation_start = time.time()
                    english_text_single = translate_to_english(german_text, client)
                    
                    # Save English translation
                    print(f"  Saving English text to: {english_path}")
                    with open(english_path, 'w', encoding='utf-8') as f:
                        f.write(english_text_single)
                    
                    print(f"  Translation completed in {time.time() - translation_start:.2f} seconds\n")
                    
                except Exception as e:
                    print(f"  ERROR translating {os.path.basename(german_path)}: {e}", file=sys.stderr)
                    print(f"  Continuing with next file...", file=sys.stderr)
                    continue
        else:
            print(f"  WARNING: German file not found: {german_path}")
    
    print("\n--- Individual Translation Phase Complete ---")
    
    # Phase 2b: Combine all texts for later analysis phases
    print("\n--- Phase 2b: Creating Combined Files for Analysis ---")
    
    # Combine German texts with separators
    combined_german_raw_text = ""
    for german_path in german_texts_paths:
        if os.path.exists(german_path):
            try:
                with open(german_path, 'r', encoding='utf-8') as f:
                    german_text_content = f.read()
                    if german_text_content.strip():
                        base_german_name = os.path.basename(german_path)
                        original_image_name = base_german_name.replace('_german.txt', '.jpg')
                        combined_german_raw_text += german_text_content + "\n\n--- End of Document from " + original_image_name + " ---\n\n"
            except Exception as e:
                print(f"  ERROR reading {german_path}: {e}", file=sys.stderr)
    
    # Save combined German text
    if combined_german_raw_text.strip():
        combined_german_filename = "combined_german_letter.txt"
        combined_german_path = os.path.join(COMBINED_OUTPUT_DIR, combined_german_filename)
        print(f"  Saving combined German text to: {combined_german_path}")
        with open(combined_german_path, 'w', encoding='utf-8') as f:
            f.write(combined_german_raw_text)
    
    # Combine English texts with separators
    english_text = ""  # This will be used by later phases
    for english_path in english_texts_paths:
        if os.path.exists(english_path):
            try:
                with open(english_path, 'r', encoding='utf-8') as f:
                    english_text_content = f.read()
                    if english_text_content.strip():
                        base_english_name = os.path.basename(english_path)
                        original_image_name = base_english_name.replace('_english.txt', '.jpg')
                        english_text += english_text_content + "\n\n--- End of Document from " + original_image_name + " ---\n\n"
            except Exception as e:
                print(f"  ERROR reading {english_path}: {e}", file=sys.stderr)
    
    # Save combined English text
    combined_english_filename = "combined_english_translation.txt"
    combined_english_path = os.path.join(ENGLISH_OUTPUT_DIR, combined_english_filename)
    
    if english_text.strip():
        print(f"  Saving combined English text to: {combined_english_path}")
        with open(combined_english_path, 'w', encoding='utf-8') as f:
            f.write(english_text)
    else:
        print("No English text was translated. Skipping analysis phases.", file=sys.stderr)
        sys.exit(1)
    
    # Set this for later phases to use
    english_output_path = combined_english_path

    print(f"\nProcessing complete for German extraction and English translation.")
    print(f"Individual German texts in {GERMAN_OUTPUT_DIR}, Individual English texts in {ENGLISH_OUTPUT_DIR}.")
    print(f"Combined files saved in {COMBINED_OUTPUT_DIR}.")

    # --- Phase 3: Narrative Analysis of Combined English Text ---
    print("\n--- Phase 3: Generating Narrative Analysis ---")
    
    analysis_output_filename = "narrative_analysis_of_letters.txt"
    # Save in the combined output directory
    analysis_output_path = os.path.join(COMBINED_OUTPUT_DIR, analysis_output_filename) 

    if os.path.exists(analysis_output_path):
        print(f"  Skipping narrative analysis (analysis file exists): {analysis_output_filename}")
    else:
        if not os.path.exists(english_output_path):
            print(f"  ERROR: Combined English translation file not found at {english_output_path}. Cannot proceed with analysis.", file=sys.stderr)
            sys.exit(1)
            
        print(f"  Reading combined English text from: {english_output_path} for analysis")
        try:
            with open(english_output_path, 'r', encoding='utf-8') as f:
                combined_english_letters_for_analysis = f.read()
            
            if not combined_english_letters_for_analysis.strip():
                print(f"  ERROR: Combined English text file is empty. Cannot proceed with analysis.", file=sys.stderr)
                sys.exit(1)

            print(f"  Starting narrative analysis of the combined letters...")
            analysis_start_time = time.time()
            narrative_analysis = analyze_letters(combined_english_letters_for_analysis, client)
            
            print(f"  Saving narrative analysis to: {analysis_output_path}")
            with open(analysis_output_path, 'w', encoding='utf-8') as f:
                f.write(narrative_analysis)
            
            print(f"  Narrative analysis saved successfully. Took {time.time() - analysis_start_time:.2f} seconds.")

        except Exception as e:
            print(f"  ERROR during narrative analysis phase: {str(e)}", file=sys.stderr)
            print(f"  Full traceback: {traceback.format_exc()}", file=sys.stderr)
            # Optionally exit or decide how to proceed if analysis fails

    print(f"\n--- Phase 3 Complete: Narrative Analysis ---")
    print(f"Narrative analysis (if generated) is in: {analysis_output_path}")

    # --- Phase 4: Generate English LaTeX from Combined English Text ---
    print("\n--- Phase 4: Generating English LaTeX Document from English Text ---")
    
    english_latex_output_filename = "combined_english_letter.tex"
    english_latex_output_path = os.path.join(COMBINED_OUTPUT_DIR, english_latex_output_filename)

    if os.path.exists(english_latex_output_path):
        print(f"  Skipping English LaTeX generation (file exists): {english_latex_output_filename}")
    else:
        # We use the 'english_text' variable which was either read or generated above.
        if not english_text.strip():
            print(f"  ERROR: English text is empty. Cannot proceed with LaTeX generation.", file=sys.stderr)
        else:
            print(f"  Starting English LaTeX document generation...")
            try:
                latex_gen_start_time = time.time()
                english_latex_document = generate_latex_from_english(english_text, client)

                print(f"  Saving English LaTeX document to: {english_latex_output_path}")
                with open(english_latex_output_path, 'w', encoding='utf-8') as f:
                    f.write(english_latex_document)

                print(f"  English LaTeX document saved successfully. Took {time.time() - latex_gen_start_time:.2f} seconds.")

            except Exception as e:
                print(f"  ERROR during English LaTeX generation phase: {str(e)}", file=sys.stderr)
                print(f"  Full traceback: {traceback.format_exc()}", file=sys.stderr)

    print(f"\n--- Phase 4 Complete: English LaTeX Generation ---")
    print(f"Final English LaTeX document (if generated) is in: {english_latex_output_path}")

    # --- Phase 5: Generate German LaTeX from Combined German Text ---
    print("\n--- Phase 5: Generating German LaTeX Document from German Text ---")

    german_latex_output_filename = "combined_german_letter.tex"
    german_latex_output_path = os.path.join(COMBINED_OUTPUT_DIR, german_latex_output_filename)

    if os.path.exists(german_latex_output_path):
        print(f"  Skipping German LaTeX generation (file exists): {german_latex_output_filename}")
    else:
        if not combined_german_raw_text.strip():
            print(f"  ERROR: German text is empty. Cannot proceed with LaTeX generation.", file=sys.stderr)
        else:
            print(f"  Starting German LaTeX document generation...")
            try:
                latex_gen_start_time = time.time()
                german_latex_document = generate_latex_from_german(combined_german_raw_text, client)

                print(f"  Saving German LaTeX document to: {german_latex_output_path}")
                with open(german_latex_output_path, 'w', encoding='utf-8') as f:
                    f.write(german_latex_document)

                print(f"  German LaTeX document saved successfully. Took {time.time() - latex_gen_start_time:.2f} seconds.")

            except Exception as e:
                print(f"  ERROR during German LaTeX generation phase: {str(e)}", file=sys.stderr)
                print(f"  Full traceback: {traceback.format_exc()}", file=sys.stderr)

    print(f"\n--- Phase 5 Complete: German LaTeX Generation ---")
    print(f"Final German LaTeX document (if generated) is in: {german_latex_output_path}")

    # --- Phase 6: Generate Formatted Markdown for Google Docs from English Text ---
    print("\n--- Phase 6: Generating Markdown for Google Docs ---")
    
    gdoc_markdown_filename = "combined_english_for_google_docs.md"
    gdoc_markdown_path = os.path.join(COMBINED_OUTPUT_DIR, gdoc_markdown_filename)

    if os.path.exists(gdoc_markdown_path):
        print(f"  Skipping GDoc Markdown generation (file exists): {gdoc_markdown_filename}")
    else:
        if not english_text.strip():
            print(f"  ERROR: English text is empty. Cannot proceed with GDoc Markdown generation.", file=sys.stderr)
        else:
            print(f"  Starting GDoc Markdown formatting for the combined English text...")
            try:
                gdoc_format_start_time = time.time()

                # The LLM call to format for GDoc can be simplified if the input is already clean.
                # Here we will re-use the `english_text` which contains the separators.
                # We can update the prompt to handle this or clean it up here.
                # Let's update the prompt to be more robust.

                final_markdown_for_gdoc = format_english_for_gdoc(english_text, client)

                print(f"  Saving GDoc-formatted Markdown to: {gdoc_markdown_path}")
                with open(gdoc_markdown_path, 'w', encoding='utf-8') as f:
                    f.write(final_markdown_for_gdoc)

                print(f"  GDoc-formatted Markdown saved successfully. Took {time.time() - gdoc_format_start_time:.2f} seconds.")

            except Exception as e:
                print(f"  ERROR during GDoc Markdown generation phase: {str(e)}", file=sys.stderr)
                print(f"  Full traceback: {traceback.format_exc()}", file=sys.stderr)

    print(f"\n--- All Processing Complete ---")
    print(f"Final Markdown for Google Docs (if generated) is in: {gdoc_markdown_path}")


if __name__ == "__main__":
    main()
