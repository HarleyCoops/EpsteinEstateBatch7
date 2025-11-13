#!/usr/bin/env python3
"""
Process Excel spreadsheets (NATIVES/) to extract structure, context, and relationships.

For each Excel file, this module:
1. Analyzes spreadsheet structure (worksheets, headers, data types)
2. Extracts all tabular data
3. Identifies entities (people, organizations, dates, locations)
4. Maps relationships between entities
5. Builds connection maps for downstream analysis
"""
from __future__ import annotations

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

try:
    import pandas as pd
    import openpyxl
except ImportError:
    print("Error: pandas and openpyxl required. Install with: pip install pandas openpyxl", file=sys.stderr)
    sys.exit(1)

from google import genai
from google.genai import types


PROMPT_EXCEL_ANALYSIS = """You are analyzing an Excel spreadsheet from House Oversight Committee documentation.

TASK: Analyze this spreadsheet comprehensively and extract all relevant information.

REQUIREMENTS:
1. STRUCTURE ANALYSIS:
   - Identify all worksheets/tabs
   - Describe the purpose and context of each worksheet
   - Note column headers and data types
   - Identify any formulas or calculated fields

2. DATA EXTRACTION:
   - Extract all tabular data preserving structure
   - Note any merged cells or special formatting
   - Identify date fields and normalize formats
   - Extract all names, organizations, locations mentioned

3. RELATIONSHIP MAPPING:
   - Identify connections between entities (people, organizations, dates, locations)
   - Note any hierarchies or groupings
   - Extract transaction amounts, quantities, or other numerical relationships
   - Identify patterns or sequences

4. CONTEXT UNDERSTANDING:
   - Determine what this spreadsheet documents (financial records, contacts, schedules, etc.)
   - Note any references to other documents or file numbers
   - Identify key dates and time periods covered

OUTPUT FORMAT (STRICT JSON):
{{
  "file_name": "<filename>",
  "structure": {{
    "worksheets": [
      {{
        "name": "<sheet_name>",
        "purpose": "<description>",
        "row_count": <number>,
        "column_count": <number>,
        "headers": ["<col1>", "<col2>", ...]
      }}
    ]
  }},
  "data": {{
    "<sheet_name>": [
      {{
        "row_index": <number>,
        "data": {{ "<header>": "<value>", ... }}
      }}
    ]
  }},
  "entities": {{
    "people": ["<name1>", "<name2>", ...],
    "organizations": ["<org1>", ...],
    "locations": ["<loc1>", ...],
    "dates": ["<date1>", ...]
  }},
  "relationships": [
    {{
      "type": "<relationship_type>",
      "source": "<entity1>",
      "target": "<entity2>",
      "context": "<description>",
      "evidence": "<supporting_data>"
    }}
  ],
  "context": {{
    "document_type": "<type>",
    "time_period": "<start_date> to <end_date>",
    "key_themes": ["<theme1>", ...],
    "references": ["<file_number>", ...]
  }},
  "confidence": 0.0-1.0,
  "notes": "<any_uncertainties_or_observations>"
}}

CRITICAL RULES:
- Extract ONLY what is present in the spreadsheet
- Do not infer or assume relationships not explicitly shown
- Preserve exact text, dates, and numbers as they appear
- Note any ambiguities or unclear data
- If a field is empty, note it as null, not omit it
"""


def read_excel_to_text(file_path: Path) -> str:
    """Read Excel file and convert to structured text representation for LLM."""
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        sheets_data = {}
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
            # Convert to text representation
            sheets_data[sheet_name] = {
                "shape": df.shape,
                "data": df.to_string(index=True, header=False)
            }
        
        # Build text representation
        text_parts = [f"FILE: {file_path.name}"]
        text_parts.append(f"SHEETS: {', '.join(excel_file.sheet_names)}")
        text_parts.append("")
        
        for sheet_name, sheet_info in sheets_data.items():
            text_parts.append(f"=== WORKSHEET: {sheet_name} ===")
            text_parts.append(f"Dimensions: {sheet_info['shape'][0]} rows x {sheet_info['shape'][1]} columns")
            text_parts.append("")
            text_parts.append("Data:")
            text_parts.append(sheet_info['data'])
            text_parts.append("")
        
        return "\n".join(text_parts)
    except Exception as e:
        return f"ERROR reading Excel file: {e}"


def analyze_excel_with_llm(file_path: Path, excel_text: str, client) -> Dict[str, Any]:
    """Send Excel data to LLM for analysis."""
    prompt = f"{PROMPT_EXCEL_ANALYSIS}\n\n--- EXCEL DATA ---\n{excel_text}\n--- END EXCEL DATA ---"
    
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
    except json.JSONDecodeError as e:
        print(f"  Warning: LLM response not valid JSON: {e}", file=sys.stderr)
        # Try to extract JSON from markdown code blocks
        if "```json" in out:
            json_start = out.find("```json") + 7
            json_end = out.find("```", json_start)
            if json_end > json_start:
                return json.loads(out[json_start:json_end].strip())
        # Fallback: return raw text wrapped in structure
        return {
            "file_name": file_path.name,
            "error": "Failed to parse LLM response as JSON",
            "raw_response": out
        }


def process_single_excel(file_path: Path, output_dir: Path, client, skip_existing: bool) -> None:
    """Process a single Excel file."""
    output_file = output_dir / f"{file_path.stem}_analysis.json"
    
    if skip_existing and output_file.exists():
        print(f"  Skipping (exists): {output_file.name}")
        return
    
    print(f"  Processing: {file_path.name}")
    
    try:
        # Read Excel to text
        excel_text = read_excel_to_text(file_path)
        
        # Analyze with LLM
        analysis = analyze_excel_with_llm(file_path, excel_text, client)
        
        # Save result
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"    Saved: {output_file.name}")
        
    except Exception as e:
        print(f"    ERROR processing {file_path.name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()


def process_natives(natives_dir: Path, output_dir: Path, skip_existing: bool = False) -> None:
    """Process all Excel files in NATIVES directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    
    client = genai.Client(api_key=api_key)
    
    # Find all Excel files recursively
    excel_files = []
    for ext in [".xls", ".xlsx"]:
        excel_files.extend(natives_dir.rglob(f"*{ext}"))
    
    if not excel_files:
        print(f"No Excel files found in {natives_dir}")
        return
    
    print(f"Found {len(excel_files)} Excel file(s)")
    
    for i, excel_file in enumerate(sorted(excel_files), 1):
        print(f"[{i}/{len(excel_files)}] {excel_file.relative_to(natives_dir)}")
        process_single_excel(excel_file, output_dir, client, skip_existing)
    
    print(f"\nNATIVES processing complete. Results in: {output_dir}")


if __name__ == "__main__":
    load_dotenv()
    ap = argparse.ArgumentParser(description="Process Excel spreadsheets from NATIVES directory")
    ap.add_argument("--natives-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()
    
    process_natives(args.natives_dir, args.output_dir, args.skip_existing)

