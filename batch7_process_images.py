#!/usr/bin/env python3
"""
Process images (IMAGES/) to extract text via OCR, describe images, and output comprehensive JSON.

For each image, this module:
1. Extracts all visible text (OCR) - typed, handwritten, printed
2. Describes the image content, layout, document type
3. Extracts structured data (dates, names, document numbers, signatures)
4. Outputs complex JSON saved as <image_name>.json in the same folder
"""
from __future__ import annotations

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

from google import genai
from google.genai import types


PROMPT_IMAGE_ANALYSIS = """You are analyzing an image from House Oversight Committee documentation.

TASK: Perform comprehensive analysis of this image and extract all information.

REQUIREMENTS:
1. TEXT EXTRACTION (OCR):
   - Extract ALL visible text exactly as it appears
   - Preserve line breaks and paragraph structure
   - Note if text is handwritten, typed, or printed
   - Identify different text regions (headers, body, footnotes, etc.)
   - Extract text from any labels, stamps, or annotations

2. VISUAL DESCRIPTION:
   - Describe the image type (document, photograph, diagram, etc.)
   - Note layout and structure
   - Describe any visible objects, people, or scenes
   - Note image quality, orientation, any damage or artifacts

3. STRUCTURED EXTRACTION:
   - Extract all dates (normalize formats)
   - Extract all names (people, organizations)
   - Extract document numbers, case numbers, file references
   - Identify signatures, stamps, or official markings
   - Extract addresses, phone numbers, email addresses
   - Note any financial amounts or numerical data

4. CONTEXT ANALYSIS:
   - Determine document type (letter, memo, form, photo, etc.)
   - Identify sender/recipient if applicable
   - Note subject matter or topic
   - Identify any references to other documents

OUTPUT FORMAT (STRICT JSON):
{{
  "file_name": "<filename>",
  "image_analysis": {{
    "type": "<document|photograph|diagram|other>",
    "description": "<detailed_description>",
    "layout": "<description_of_structure>",
    "quality": "<high|medium|low>",
    "orientation": "<portrait|landscape>"
  }},
  "text_extraction": {{
    "full_text": "<complete_extracted_text>",
    "text_regions": [
      {{
        "region": "<header|body|footer|margin|stamp|etc>",
        "text": "<extracted_text>",
        "type": "<handwritten|typed|printed>"
      }}
    ]
  }},
  "structured_data": {{
    "dates": ["<date1>", "<date2>", ...],
    "people": ["<name1>", "<name2>", ...],
    "organizations": ["<org1>", ...],
    "locations": ["<address1>", ...],
    "document_numbers": ["<ref1>", ...],
    "financial_amounts": ["<amount1>", ...],
    "contact_info": {{
      "phone_numbers": ["<phone1>", ...],
      "email_addresses": ["<email1>", ...],
      "addresses": ["<address1>", ...]
    }},
    "signatures": ["<signature_text>", ...],
    "stamps_or_markings": ["<description>", ...]
  }},
  "document_metadata": {{
    "document_type": "<letter|memo|form|photo|etc>",
    "sender": "<name_or_null>",
    "recipient": "<name_or_null>",
    "subject": "<subject_or_null>",
    "date": "<primary_date_or_null>",
    "references": ["<file_number>", ...]
  }},
  "confidence": {{
    "text_extraction": 0.0-1.0,
    "structured_data": 0.0-1.0,
    "overall": 0.0-1.0
  }},
  "notes": "<any_uncertainties_or_observations>"
}}

CRITICAL RULES:
- Extract text exactly as it appears, do not correct or normalize
- If text is unclear, note it as "[unclear: <best_guess>]"
- Do not invent information not visible in the image
- Preserve original formatting and structure
- Note any areas that are illegible or damaged
"""


def analyze_image_with_llm(image_path: Path, client) -> Dict[str, Any]:
    """Analyze image using Gemini vision model."""
    try:
        # Upload image file
        files = [client.files.upload(file=str(image_path))]
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=files[0].uri,
                        mime_type=files[0].mime_type,
                    ),
                    types.Part.from_text(text=PROMPT_IMAGE_ANALYSIS),
                ],
            )
        ]
        
        cfg = types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json",
            max_output_tokens=16384,
            thinking_config=types.ThinkingConfig(thinking_budget=1024),
        )
        
        out = ""
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-pro",
            contents=contents,
            config=cfg,
        ):
            if chunk.text:
                out += chunk.text
        
        # Parse JSON response
        try:
            result = json.loads(out.strip())
            # Ensure file_name is set
            result["file_name"] = image_path.name
            result["file_path"] = str(image_path.relative_to(image_path.parents[2]))  # Relative to BATCH7
            
            # Extract HOUSE_OVERSIGHT ID from filename
            import re
            id_match = re.search(r'HOUSE_OVERSIGHT_(\d+)', image_path.name)
            if id_match:
                result["house_oversight_id"] = id_match.group(1)
            
            # Add processing metadata if not present
            if "processing_metadata" not in result:
                import datetime
                result["processing_metadata"] = {
                    "processed_at": datetime.datetime.utcnow().isoformat() + "Z",
                    "model": "gemini-2.5-pro"
                }
            
            return result
        except json.JSONDecodeError as e:
            print(f"    Warning: LLM response not valid JSON: {e}", file=sys.stderr)
            # Try to extract JSON from markdown code blocks
            if "```json" in out:
                json_start = out.find("```json") + 7
                json_end = out.find("```", json_start)
                if json_end > json_start:
                    result = json.loads(out[json_start:json_end].strip())
                    result["file_name"] = image_path.name
                    return result
            
            # Fallback: return error structure
            return {
                "file_name": image_path.name,
                "error": "Failed to parse LLM response as JSON",
                "raw_response": out[:1000]  # First 1000 chars
            }
            
    except Exception as e:
        return {
            "file_name": image_path.name,
            "error": str(e)
        }


def process_single_image(image_path: Path, client, skip_existing: bool) -> None:
    """Process a single image and save JSON output in same folder."""
    output_file = image_path.parent / f"{image_path.stem}.json"
    
    if skip_existing and output_file.exists():
        print(f"  Skipping (exists): {output_file.name}")
        return
    
    print(f"  Processing: {image_path.name}")
    
    try:
        # Analyze image with LLM
        analysis = analyze_image_with_llm(image_path, client)
        
        # Save JSON result in same folder as image
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"    Saved: {output_file.name}")
        
    except Exception as e:
        print(f"    ERROR processing {image_path.name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()


def process_images(images_dir: Path, output_dir: Path, skip_existing: bool = False) -> None:
    """Process all images in IMAGES directory recursively."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    
    client = genai.Client(api_key=api_key)
    
    # Find all image files recursively
    image_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif", ".bmp"}
    image_files = [
        f for f in images_dir.rglob("*")
        if f.suffix.lower() in image_extensions and f.is_file()
    ]
    
    if not image_files:
        print(f"No image files found in {images_dir}")
        return
    
    print(f"Found {len(image_files)} image file(s)")
    
    for i, image_file in enumerate(sorted(image_files), 1):
        print(f"[{i}/{len(image_files)}] {image_file.relative_to(images_dir)}")
        process_single_image(image_file, client, skip_existing)
    
    print(f"\nIMAGES processing complete. JSON files saved alongside images.")


if __name__ == "__main__":
    load_dotenv()
    ap = argparse.ArgumentParser(description="Process images from IMAGES directory")
    ap.add_argument("--images-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()
    
    process_images(args.images_dir, args.output_dir, args.skip_existing)

