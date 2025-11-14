#!/usr/bin/env python3
"""
Generate a summary of latest findings from JSON files for README.md

This script analyzes the most recent JSON files in TEXT/001 and IMAGES/001
and generates a summary of the latest context/content that was updated.
"""
from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict


def get_recent_json_files(base_dir: Path, max_files: int = 10) -> Dict[str, List[Path]]:
    """Get the most recently modified JSON files from TEXT/001 and IMAGES/001."""
    recent_files = {
        "images": [],
        "text": []
    }
    
    # Get image JSON files
    images_dir = base_dir / "BATCH7" / "IMAGES" / "001"
    if images_dir.exists():
        json_files = list(images_dir.glob("*.json"))
        # Sort by modification time, most recent first
        json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        recent_files["images"] = json_files[:max_files]
    
    # Get text extraction JSON files
    text_dir = base_dir / "BATCH7" / "TEXT" / "001"
    if text_dir.exists():
        json_files = list(text_dir.glob("*_extraction.json"))
        json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        recent_files["text"] = json_files[:max_files]
    
    return recent_files


def analyze_image_json(file_path: Path) -> Dict[str, Any]:
    """Extract key information from an image JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        summary = {
            "file": file_path.name,
            "doc_type": data.get("image_analysis", {}).get("type", "unknown"),
            "people": data.get("structured_data", {}).get("people", [])[:5],  # Top 5
            "has_trump": False,
            "key_characters": [],
            "has_text": bool(data.get("text_extraction", {}).get("full_text")),
            "text_preview": (data.get("text_extraction", {}).get("full_text", "") or "")[:150]
        }
        
        # Check for Trump mentions
        people_list = data.get("structured_data", {}).get("people", [])
        for person in people_list:
            if "trump" in str(person).lower():
                summary["has_trump"] = True
                break
        
        # Check for key characters
        key_names = ["epstein", "maxwell", "clinton", "biden", "giuliani", "prince andrew"]
        for person in people_list:
            person_lower = str(person).lower()
            if any(key in person_lower for key in key_names):
                summary["key_characters"].append(person)
        
        return summary
    except Exception as e:
        return {"file": file_path.name, "error": str(e)}


def analyze_text_json(file_path: Path) -> Dict[str, Any]:
    """Extract key information from a text extraction JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        summary = {
            "file": file_path.name,
            "doc_type": data.get("metadata", {}).get("document_type", "unknown"),
            "people": data.get("entities", {}).get("people", [])[:5],  # Top 5
            "themes": data.get("themes", [])[:3],  # Top 3 themes
            "has_trump": False,
            "text_preview": (data.get("content", {}).get("full_text", "") or "")[:200]
        }
        
        # Check for Trump mentions
        people_list = data.get("entities", {}).get("people", [])
        for person in people_list:
            if "trump" in str(person).lower():
                summary["has_trump"] = True
                break
        
        return summary
    except Exception as e:
        return {"file": file_path.name, "error": str(e)}


def generate_summary_text(recent_files: Dict[str, List[Path]], base_dir: Path) -> str:
    """Generate a human-readable summary of the latest findings."""
    summary_parts = []
    
    # Analyze recent image files
    if recent_files["images"]:
        summary_parts.append("**Latest Image Analysis:**")
        
        trump_found = False
        key_findings = []
        people_mentioned = set()
        
        for img_file in recent_files["images"][:5]:  # Top 5 most recent
            analysis = analyze_image_json(img_file)
            if "error" not in analysis:
                if analysis.get("has_trump"):
                    trump_found = True
                    key_findings.append(f"Trump mentioned in {analysis['file']}")
                
                for person in analysis.get("people", []):
                    people_mentioned.add(person)
                
                if analysis.get("key_characters"):
                    for char in analysis["key_characters"]:
                        key_findings.append(f"{char} identified in {analysis['file']}")
        
        if trump_found:
            summary_parts.append("- TRUMP MENTIONS DETECTED in newly processed images")
        
        if key_findings:
            summary_parts.append(f"- Key characters identified: {', '.join(set(key_findings[:3]))}")
        
        summary_parts.append(f"- {len(recent_files['images'])} new image analysis files processed")
        summary_parts.append("")
    
    # Analyze recent text files
    if recent_files["text"]:
        summary_parts.append("**Latest Text Processing:**")
        
        trump_found = False
        themes = set()
        people_mentioned = set()
        
        for text_file in recent_files["text"][:5]:  # Top 5 most recent
            analysis = analyze_text_json(text_file)
            if "error" not in analysis:
                if analysis.get("has_trump"):
                    trump_found = True
                
                for theme in analysis.get("themes", []):
                    themes.add(theme)
                
                for person in analysis.get("people", []):
                    people_mentioned.add(person)
        
        if trump_found:
            summary_parts.append("- TRUMP MENTIONS DETECTED in newly processed text documents")
        
        if themes:
            summary_parts.append(f"- Key themes: {', '.join(list(themes)[:3])}")
        
        summary_parts.append(f"- {len(recent_files['text'])} new text extraction files processed")
        summary_parts.append("")
    
    if not summary_parts:
        return "Processing files... Analysis summary will appear here as files are processed."
    
    return "\n".join(summary_parts)


def update_readme_with_summary(base_dir: Path) -> bool:
    """Update README.md with latest summary from JSON files."""
    readme_path = base_dir / "README.md"
    
    if not readme_path.exists():
        print(f"README.md not found at {readme_path}", file=sys.stderr)
        return False
    
    # Get recent JSON files
    recent_files = get_recent_json_files(base_dir, max_files=10)
    
    # Generate summary
    summary_text = generate_summary_text(recent_files, base_dir)
    
    # Read README
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading README: {e}", file=sys.stderr)
        return False
    
    # Replace the {LATEST_SUMMARY} placeholder
    if "{LATEST_SUMMARY}" in content:
        updated_content = content.replace("{LATEST_SUMMARY}", summary_text)
    else:
        # If placeholder doesn't exist, add it after status line
        status_section = "Status: Processing continues as long as API credits are available"
        if status_section in content:
            updated_content = content.replace(
                status_section,
                f"{status_section}\n\n### Latest Context Update\n\n{summary_text}"
            )
        else:
            # Fallback: append to end
            updated_content = content + f"\n\n### Latest Context Update\n\n{summary_text}\n"
    
    # Only write if changed
    if updated_content != content:
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"Updated README.md with latest summary")
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

