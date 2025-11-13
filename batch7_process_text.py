#!/usr/bin/env python3
"""
Process text files (TEXT/) to extract content, understand context, and assemble into stories.

This module:
1. Extracts content from each text file
2. Understands document structure and context
3. Groups related texts into coherent narratives (like Dorle's Stories)
4. Assembles stories from grouped texts
5. Creates letters/ folder structure similar to Dorle's Stories pipeline
"""
from __future__ import annotations

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

from google import genai
from google.genai import types


PROMPT_TEXT_EXTRACTION = """You are analyzing a text file from House Oversight Committee documentation.

TASK: Extract and structure the content of this text file.

REQUIREMENTS:
1. CONTENT EXTRACTION:
   - Extract all text content preserving structure
   - Identify document sections or parts
   - Note any formatting markers or special characters
   - Preserve paragraph breaks and line structure

2. CONTEXT UNDERSTANDING:
   - Determine document type (conversation, transcript, article, memo, etc.)
   - Identify participants or speakers if applicable
   - Note time period or dates mentioned
   - Identify main topics or themes

3. ENTITY EXTRACTION:
   - Extract all dates mentioned
   - Extract all names (people, organizations)
   - Extract locations, addresses
   - Extract document references or file numbers
   - Extract key events or actions

OUTPUT FORMAT (STRICT JSON):
{{
  "file_name": "<filename>",
  "content": {{
    "full_text": "<complete_text_content>",
    "sections": [
      {{
        "section_index": <number>,
        "section_type": "<header|paragraph|list|quote|etc>",
        "text": "<section_text>"
      }}
    ]
  }},
  "metadata": {{
    "document_type": "<type>",
    "participants": ["<name1>", ...],
    "date_range": {{
      "earliest": "<date_or_null>",
      "latest": "<date_or_null>"
    }},
    "file_references": ["<file_number>", ...]
  }},
  "entities": {{
    "people": ["<name1>", ...],
    "organizations": ["<org1>", ...],
    "locations": ["<loc1>", ...],
    "dates": ["<date1>", ...],
    "events": ["<event1>", ...]
  }},
  "themes": ["<theme1>", "<theme2>", ...],
  "confidence": 0.0-1.0,
  "notes": "<any_observations>"
}}

CRITICAL RULES:
- Extract text exactly as it appears
- Do not summarize or rewrite content
- Preserve all original formatting
- Note any unclear or damaged sections
"""


PROMPT_STORY_ASSEMBLY = """You are analyzing multiple text files from House Oversight Committee documentation.

TASK: Group related texts into coherent narratives and understand connections.

REQUIREMENTS:
1. GROUPING:
   - Group texts that are part of the same conversation, story, or topic
   - Order texts chronologically when dates are available
   - Identify continuation or related content

2. NARRATIVE CONSTRUCTION:
   - Assemble grouped texts into coherent stories
   - Note narrative flow and connections
   - Identify key events and their sequence

3. RELATIONSHIP MAPPING:
   - Map connections between entities across texts
   - Identify recurring themes or topics
   - Note temporal relationships (what happened when)

OUTPUT FORMAT (STRICT JSON):
{{
  "stories": [
    {{
      "id": "S0001",
      "title": "<descriptive_title>",
      "text_files": ["<filename1>", "<filename2>", ...],
      "assembled_text": "<combined_narrative>",
      "date_range": {{
        "earliest": "<date_or_null>",
        "latest": "<date_or_null>"
      }},
      "participants": ["<name1>", ...],
      "key_events": [
        {{
          "event": "<description>",
          "date": "<date_or_null>",
          "entities_involved": ["<name1>", ...]
        }}
      ],
      "themes": ["<theme1>", ...],
      "confidence": 0.0-1.0,
      "reason": "<explanation_of_grouping>"
    }}
  ],
  "unassigned_files": ["<filename>", ...],
  "cross_story_connections": [
    {{
      "story_ids": ["S0001", "S0002"],
      "connection_type": "<shared_entity|temporal|thematic>",
      "description": "<how_they_connect>"
    }}
  ]
}}

CRITICAL RULES:
- Use ONLY the provided text files
- Do not invent connections not supported by the content
- Preserve exact text, do not rewrite or summarize
- Note any ambiguities in grouping
- Maintain chronological order when possible
"""


def extract_text_content(text_path: Path, client, save_per_file: bool = True) -> Dict[str, Any]:
    """Extract and structure content from a text file.
    
    Args:
        text_path: Path to text file
        client: Gemini client
        save_per_file: If True, save extraction JSON next to text file (consistent with images/natives)
    """
    try:
        with open(text_path, "r", encoding="utf-8", errors="replace") as f:
            text_content = f.read()
    except Exception as e:
        return {
            "file_name": text_path.name,
            "error": f"Failed to read file: {e}"
        }
    
    prompt = f"{PROMPT_TEXT_EXTRACTION}\n\n--- TEXT FILE ---\n{text_content}\n--- END TEXT FILE ---"
    
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
    ]
    
    cfg = types.GenerateContentConfig(
        temperature=0.3,
        response_mime_type="application/json",
        max_output_tokens=16384,
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
    
    try:
        result = json.loads(out.strip())
        result["file_name"] = text_path.name
        result["file_path"] = str(text_path.relative_to(text_path.parents[2]))  # Relative to BATCH7
        
        # Extract HOUSE_OVERSIGHT ID from filename
        import re
        id_match = re.search(r'HOUSE_OVERSIGHT_(\d+)', text_path.name)
        if id_match:
            result["house_oversight_id"] = id_match.group(1)
        
        # Add processing metadata
        import datetime
        result["processing_metadata"] = {
            "processed_at": datetime.datetime.utcnow().isoformat() + "Z",
            "model": "gemini-2.5-pro"
        }
        
        # Save per-file JSON next to text file (consistent with images/natives)
        if save_per_file:
            extraction_file = text_path.parent / f"{text_path.stem}_extraction.json"
            with open(extraction_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    except json.JSONDecodeError:
        # Fallback: return basic structure
        result = {
            "file_name": text_path.name,
            "file_path": str(text_path.relative_to(text_path.parents[2])),
            "content": {"full_text": text_content},
            "error": "Failed to parse LLM response"
        }
        if save_per_file:
            extraction_file = text_path.parent / f"{text_path.stem}_extraction.json"
            with open(extraction_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        return result


def assemble_stories(text_extractions: List[Dict[str, Any]], client) -> Dict[str, Any]:
    """Group text files into stories using LLM."""
    # Build input listing
    listing_parts = ["--- TEXT FILES START ---"]
    for ext in text_extractions:
        listing_parts.append(f"=== FILE: {ext.get('file_name', 'unknown')} ===")
        listing_parts.append(f"Content: {ext.get('content', {}).get('full_text', '')[:2000]}...")
        listing_parts.append(f"Metadata: {json.dumps(ext.get('metadata', {}), ensure_ascii=False)}")
        listing_parts.append(f"Entities: {json.dumps(ext.get('entities', {}), ensure_ascii=False)}")
        listing_parts.append("=== FILE END ===")
    listing_parts.append("--- TEXT FILES END ---")
    
    listing = "\n".join(listing_parts)
    prompt = f"{PROMPT_STORY_ASSEMBLY}\n\n{listing}"
    
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
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
    
    try:
        return json.loads(out.strip())
    except json.JSONDecodeError:
        return {
            "stories": [],
            "unassigned_files": [ext["file_name"] for ext in text_extractions],
            "error": "Failed to parse story assembly response"
        }


def create_story_folders(stories: Dict[str, Any], output_dir: Path, text_extractions_by_file: Dict[str, Dict[str, Any]]) -> None:
    """Create letters/ folder structure similar to Dorle's Stories."""
    letters_dir = output_dir / "letters"
    letters_dir.mkdir(parents=True, exist_ok=True)
    
    for story in stories.get("stories", []):
        story_id = story.get("id", "S0000")
        story_dir = letters_dir / story_id
        story_dir.mkdir(exist_ok=True)
        
        # Save metadata
        with open(story_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(story, f, ensure_ascii=False, indent=2)
        
        # Save assembled text
        assembled_text = story.get("assembled_text", "")
        with open(story_dir / "text.txt", "w", encoding="utf-8") as f:
            f.write(assembled_text)
        
        # Save individual file references
        file_refs = story.get("text_files", [])
        with open(story_dir / "source_files.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(file_refs))


def process_text(text_dir: Path, output_dir: Path, skip_existing: bool = False) -> None:
    """Process all text files and assemble into stories."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    
    client = genai.Client(api_key=api_key)
    
    # Find all text files recursively
    text_files = list(text_dir.rglob("*.txt"))
    
    if not text_files:
        print(f"No text files found in {text_dir}")
        return
    
    print(f"Found {len(text_files)} text file(s)")
    
    # Step 1: Extract content from each text file
    print("\nStep 1: Extracting content from text files...")
    text_extractions = []
    text_extractions_by_file = {}
    
    extraction_output = output_dir / "text_extractions.json"
    if skip_existing and extraction_output.exists():
        print(f"  Loading existing extractions from {extraction_output}")
        with open(extraction_output, "r", encoding="utf-8") as f:
            text_extractions = json.load(f)
            text_extractions_by_file = {ext["file_name"]: ext for ext in text_extractions}
    else:
        for i, text_file in enumerate(sorted(text_files), 1):
            print(f"[{i}/{len(text_files)}] Extracting: {text_file.relative_to(text_dir)}")
            # Extract and save per-file JSON (saved next to text file)
            extraction = extract_text_content(text_file, client, save_per_file=True)
            text_extractions.append(extraction)
            text_extractions_by_file[extraction["file_name"]] = extraction
        
        # Save extractions
        with open(extraction_output, "w", encoding="utf-8") as f:
            json.dump(text_extractions, f, ensure_ascii=False, indent=2)
        print(f"  Saved extractions to {extraction_output}")
    
    # Step 2: Assemble stories
    print("\nStep 2: Assembling stories from text files...")
    stories_output = output_dir / "stories_assembly.json"
    if skip_existing and stories_output.exists():
        print(f"  Loading existing stories from {stories_output}")
        with open(stories_output, "r", encoding="utf-8") as f:
            stories = json.load(f)
    else:
        stories = assemble_stories(text_extractions, client)
        with open(stories_output, "w", encoding="utf-8") as f:
            json.dump(stories, f, ensure_ascii=False, indent=2)
        print(f"  Saved stories to {stories_output}")
    
    # Step 3: Create letters/ folder structure
    print("\nStep 3: Creating letters/ folder structure...")
    create_story_folders(stories, output_dir, text_extractions_by_file)
    
    print(f"\nTEXT processing complete.")
    print(f"  - Per-file extractions: JSON files saved alongside text files (*_extraction.json)")
    print(f"  - Aggregated extractions: {extraction_output}")
    print(f"  - Stories assembly: {stories_output}")
    print(f"  - Letters folder: {output_dir / 'letters'}")


if __name__ == "__main__":
    load_dotenv()
    ap = argparse.ArgumentParser(description="Process text files from TEXT directory")
    ap.add_argument("--text-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()
    
    process_text(args.text_dir, args.output_dir, args.skip_existing)

