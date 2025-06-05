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
EXTRACTION_TEMPERATURE = 0.4  # Lower temperature for accurate OCR
TRANSLATION_TEMPERATURE = 0.8  # Balance accuracy and fluency for translation
ANALYSIS_TEMPERATURE = 0.75 # For nuanced and insightful interpretations
LATEX_GENERATION_TEMPERATURE = 0.2 # Lower temperature for precise LaTeX code

PROMPT_IMAGE_EXTRACTION = (
    "This is a single page image of a handwritten German document.\\n"
    "Extract the handwritten German text exactly as it appears.\\n"
    "Return the result in plain text format."
)

PROMPT_TRANSLATION_TEMPLATE = (
    "Translate the following German text to English, :\\n\\n"
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
    "These letters are concatenated, with separators like '--- End of Document from [filename] ---' marking the transition between original documents.\\n"
    "Your task is to convert this entire text into a single, well-formatted, and compilable LaTeX document. "
    "Use the standard 'article' class. Include necessary packages like 'inputenc' (for utf-8, use \\usepackage[utf8]{inputenc}) and 'geometry' for reasonable margins (e.g., \\usepackage{geometry}\\geometry{a4paper, margin=1in}).\\n"
    "The English text should flow as a continuous document. "
    "Replace the '--- End of Document from ... ---' separators with a visual break, such as \\bigskip\\hrule\\bigskip, to indicate the end of one letter segment and the beginning of the next.\\n"
    "Preserve all other paragraph breaks as observed in the input text (typically a blank line between paragraphs in the input should translate to a new paragraph in LaTeX).\\n"
    "Handle special LaTeX characters (like $, %, &, #, _, {, }) in the input text by escaping them appropriately (e.g., \\$, \\%, \\&, \\#, \\_, \\{, \\}).\\n"
    "Do not add any commentary or text that is not part of the original letters themselves. "
    "The output must be ONLY the valid LaTeX code, starting with \\documentclass{article} and ending with \\end{document}. Ensure the document is self-contained and ready to compile.\\n\\n"
    "Here is the English text to convert:\\n\\n"
    "--- BEGIN ENGLISH TEXT ---\\n"
    "{english_letter_content}\\n"
    "--- END ENGLISH TEXT ---"
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

    # Phase 2: Combine German texts and translate to English
    print("\n--- Phase 2: Combining German Texts and Translating to English ---")
    
    combined_german_text = ""
    for german_path in german_texts_paths:
        if os.path.exists(german_path):
            try:
                with open(german_path, 'r', encoding='utf-8') as f:
                    german_text_content = f.read()
                    if german_text_content.strip(): # Add separator only if content exists
                        combined_german_text += german_text_content + "\n\n--- End of Document from " + os.path.basename(german_path) + " ---\n\n"
                    else:
                        print(f"  WARNING: German text file {german_path} is empty.")
            except Exception as e:
                print(f"  ERROR reading {german_path}: {e}", file=sys.stderr)
                # Potentially skip this file's content or handle error
        else:
            print(f"  WARNING: Expected German text file {german_path} not found. It might have failed during extraction.")

    if not combined_german_text.strip():
        print("No German text was extracted or combined. Skipping translation.", file=sys.stderr)
        sys.exit(1)

    english_output_filename = "combined_english_translation.txt"
    english_output_path = os.path.join(ENGLISH_OUTPUT_DIR, english_output_filename)

    if os.path.exists(english_output_path):
        print(f"  Skipping translation (combined English file exists): {english_output_filename}")
    else:
        print(f"  Starting combined English translation...")
        try:
            overall_start = time.time()
            english_text = translate_to_english(combined_german_text, client)
            
            print(f"  Saving combined English translation to: {english_output_path}")
            with open(english_output_path, 'w', encoding='utf-8') as f:
                f.write(english_text)
            
            print(f"  Combined translation completed in {time.time() - overall_start:.2f} seconds")
            
        except Exception as e:
            print(f"  ERROR translating combined German text: {e}", file=sys.stderr)
            print(f"  Full traceback: {traceback.format_exc()}", file=sys.stderr)
            # Handle error, perhaps save partial or indicate failure
            sys.exit(1) # Exit if combined translation fails, as analysis depends on it

    print(f"\nProcessing complete for German extraction and English translation.")
    print(f"Individual German texts in {GERMAN_OUTPUT_DIR}, Combined English translation in {english_output_path}.")

    # --- Phase 3: Narrative Analysis of Combined English Text ---
    print("\n--- Phase 3: Generating Narrative Analysis ---")
    
    analysis_output_filename = "narrative_analysis_of_letters.txt"
    # Save in the base directory as discussed
    analysis_output_path = os.path.join(BASE_DIR, analysis_output_filename) 

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

    # --- Phase 4: Generate LaTeX from Combined English Text ---
    print("\n--- Phase 4: Generating LaTeX Document from English Text ---")
    
    latex_output_filename = "combined_english_letter.tex"
    latex_output_path = os.path.join(BASE_DIR, latex_output_filename)

    if os.path.exists(latex_output_path):
        print(f"  Skipping LaTeX generation (file exists): {latex_output_filename}")
    else:
        if not os.path.exists(english_output_path):
            print(f"  ERROR: Combined English translation file not found at {english_output_path}. Cannot proceed with LaTeX generation.", file=sys.stderr)
            sys.exit(1) # Critical dependency missing
            
        print(f"  Reading combined English text from: {english_output_path} for LaTeX generation")
        try:
            with open(english_output_path, 'r', encoding='utf-8') as f:
                combined_english_letters_for_latex = f.read()
            
            if not combined_english_letters_for_latex.strip():
                print(f"  ERROR: Combined English text file is empty. Cannot proceed with LaTeX generation.", file=sys.stderr)
                sys.exit(1) # Critical dependency empty

            print(f"  Starting LaTeX document generation...")
            latex_gen_start_time = time.time()
            latex_document = generate_latex_from_english(combined_english_letters_for_latex, client)
            
            print(f"  Saving LaTeX document to: {latex_output_path}")
            with open(latex_output_path, 'w', encoding='utf-8') as f:
                f.write(latex_document)
            
            print(f"  LaTeX document saved successfully. Took {time.time() - latex_gen_start_time:.2f} seconds.")

        except Exception as e:
            print(f"  ERROR during LaTeX generation phase: {str(e)}", file=sys.stderr)
            print(f"  Full traceback: {traceback.format_exc()}", file=sys.stderr)
            # Optionally exit or decide how to proceed

    print(f"\n--- All Processing Complete ---")
    print(f"Final LaTeX document (if generated) is in: {latex_output_path}")


if __name__ == "__main__":
    main()