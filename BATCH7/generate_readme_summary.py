#!/usr/bin/env python3
"""
Generate a summary of latest findings from JSON files for README.md using Gemini API.

This script:
1. Finds JSON files modified in the last 5 minutes
2. Sends RAW JSON content to Gemini API
3. Gets AI-generated summary of characters, context, settings, dates
4. Updates README.md with the summary
"""
from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from google import genai
from google.genai import types


PROMPT_SUMMARY = """You are analyzing House Oversight Committee document analysis JSON files that were just processed.

Analyze the provided JSON files and create a comprehensive summary focusing on:

1. **CHARACTERS**: Who are the key people mentioned? Pay special attention to:
   - Donald Trump, Trump family members
   - Jeffrey Epstein, Ghislaine Maxwell
   - Bill Clinton, Hillary Clinton
   - Any other notable political or public figures
   - List names and their roles/context

2. **CONTEXT**: What is happening in these documents?
   - What type of documents are these? (emails, letters, legal documents, photos, etc.)
   - What events or situations are described?
   - What relationships or connections are revealed?
   - Any notable patterns or themes?

3. **SETTINGS**: Where and when?
   - Dates mentioned (especially recent dates)
   - Locations mentioned
   - Organizations or institutions involved
   - Timeline of events if apparent

4. **KEY FINDINGS**: What stands out?
   - Any particularly significant or revealing information?
   - Any connections between people or events?
   - Any legal or financial implications?

Format your response as markdown with clear sections. Be specific and detailed. Focus on factual information extracted from the documents. If Trump or other key figures are mentioned, highlight this prominently.

Keep the summary concise but informative - aim for 200-400 words."""


def load_api_key(base_dir: Path) -> str:
    """Load GEMINI_API_KEY from .env file."""
    script_dir = Path(__file__).parent.absolute()
    
    # Try multiple locations for .env
    env_paths = [
        script_dir / ".env",
        base_dir / ".env",
        script_dir.parent / ".env"
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
            break
    else:
        # Try default location
        load_dotenv()
    
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file", file=sys.stderr)
        print(f"Checked: {env_paths}", file=sys.stderr)
        sys.exit(1)
    
    return api_key


def get_recent_json_files(base_dir: Path, minutes: int = 5) -> Dict[str, List[Path]]:
    """Get JSON files modified in the last N minutes."""
    cutoff_time = datetime.now() - timedelta(minutes=minutes)
    recent_files = {
        "images": [],
        "text": []
    }
    
    # Get image JSON files modified in last 5 minutes
    images_dir = base_dir / "BATCH7" / "IMAGES" / "001"
    if images_dir.exists():
        for json_file in images_dir.glob("*.json"):
            mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
            if mtime >= cutoff_time:
                recent_files["images"].append(json_file)
        # Sort by modification time, most recent first
        recent_files["images"].sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Get text extraction JSON files modified in last 5 minutes
    text_dir = base_dir / "BATCH7" / "TEXT" / "001"
    if text_dir.exists():
        for json_file in text_dir.glob("*_extraction.json"):
            mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
            if mtime >= cutoff_time:
                recent_files["text"].append(json_file)
        recent_files["text"].sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    return recent_files


def read_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Read and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not read {file_path.name}: {e}", file=sys.stderr)
        return None


def generate_ai_summary(recent_files: Dict[str, List[Path]], api_key: str, base_dir: Path) -> str:
    """Send JSON files to Gemini API and get AI-generated summary."""
    if not recent_files["images"] and not recent_files["text"]:
        return "No new files processed in the last 5 minutes. Processing continues..."
    
    # Collect all JSON content
    json_contents = []
    file_info = []
    
    # Add image JSON files
    for img_file in recent_files["images"][:10]:  # Limit to 10 most recent
        data = read_json_file(img_file)
        if data:
            json_contents.append({
                "file": img_file.name,
                "type": "image_analysis",
                "data": data
            })
            file_info.append(f"Image: {img_file.name}")
    
    # Add text JSON files
    for text_file in recent_files["text"][:10]:  # Limit to 10 most recent
        data = read_json_file(text_file)
        if data:
            json_contents.append({
                "file": text_file.name,
                "type": "text_extraction",
                "data": data
            })
            file_info.append(f"Text: {text_file.name}")
    
    if not json_contents:
        return "Files were found but could not be read. Processing continues..."
    
    # Prepare prompt with JSON data
    prompt = f"""{PROMPT_SUMMARY}

Here are {len(json_contents)} recently processed JSON files:

Files analyzed:
{chr(10).join(f"- {info}" for info in file_info)}

JSON Data:
{json.dumps(json_contents, indent=2, ensure_ascii=False)}

Please analyze these files and provide the summary as requested above."""

    try:
        # Initialize Gemini client
        client = genai.Client(api_key=api_key)
        
        # Make API call
        print(f"Sending {len(json_contents)} JSON files to Gemini for analysis...", file=sys.stderr)
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )]
        )
        
        summary = response.text.strip()
        print(f"Received AI summary ({len(summary)} chars)", file=sys.stderr)
        return summary
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}", file=sys.stderr)
        # Fallback to basic summary
        return f"**Latest Processing Update:**\n\n- {len(recent_files['images'])} new image analysis files processed\n- {len(recent_files['text'])} new text extraction files processed\n\n(API analysis temporarily unavailable - processing continues)"


def update_readme_with_summary(base_dir: Path) -> bool:
    """Update README.md with AI-generated summary from JSON files."""
    # Only update root README (main, public-facing)
    readme_path = base_dir / "README.md"
    
    if not readme_path.exists():
        print(f"README.md not found at {readme_path}", file=sys.stderr)
        return False
    
    # Load API key
    try:
        api_key = load_api_key(base_dir)
    except SystemExit:
        return False
    
    # Get recent JSON files (last 5 minutes)
    recent_files = get_recent_json_files(base_dir, minutes=5)
    
    # Generate AI summary
    summary_text = generate_ai_summary(recent_files, api_key, base_dir)
    
    # Read README
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading README: {e}", file=sys.stderr)
        return False
    
    # Replace the summary section
    import re
    
    # Pattern to find the summary section
    pattern = r'(### Latest Context Update\n\n)(.*?)(\n\n---)'
    
    updated_content = content
    if re.search(pattern, content, re.DOTALL):
        # Replace existing summary section
        updated_content = re.sub(
            pattern,
            r'\1' + summary_text + r'\3',
            content,
            flags=re.DOTALL
        )
    elif "{LATEST_SUMMARY}" in content:
        # Replace placeholder if it exists
        updated_content = content.replace("{LATEST_SUMMARY}", summary_text)
    else:
        # If neither exists, add it after status line
        status_section = "Status: Processing continues as long as API credits are available"
        if status_section in content:
            updated_content = content.replace(
                status_section,
                f"{status_section}\n\n### Latest Context Update\n\n{summary_text}\n"
            )
        else:
            # Fallback: append to end
            updated_content = content + f"\n\n### Latest Context Update\n\n{summary_text}\n"
    
    # Only write if changed
    if updated_content != content:
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"Updated README.md with AI-generated summary")
            return True
        except Exception as e:
            print(f"Error writing README: {e}", file=sys.stderr)
            return False
    
    return True


def main() -> None:
    # Determine base directory
    script_dir = Path(__file__).parent.absolute()
    if script_dir.name == "BATCH7":
        base_dir = script_dir.parent
    else:
        base_dir = script_dir
    
    update_readme_with_summary(base_dir)


if __name__ == "__main__":
    main()
