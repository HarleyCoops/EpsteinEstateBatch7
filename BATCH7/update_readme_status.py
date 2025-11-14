#!/usr/bin/env python3
"""
Update the README.md with the latest git commit time.

This script updates the {LAST_GIT_COMMIT_TIME} placeholder in README.md
with the timestamp of the most recent git commit.
"""
from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def get_last_commit_time(base_dir: Path) -> str:
    """Get the timestamp of the last git commit."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            # Parse git timestamp and format it nicely
            git_time = result.stdout.strip()
            try:
                # Git format: "2024-01-15 14:30:00 -0500"
                dt = datetime.strptime(git_time[:19], "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                return git_time[:19] if len(git_time) >= 19 else git_time
        return "Never"
    except Exception:
        return "Unknown"


def update_readme(base_dir: Path) -> bool:
    """Update README.md files with latest commit time."""
    # Update both root README and BATCH7 README
    readme_files = [
        base_dir / "README.md",  # Root README
        base_dir / "BATCH7" / "README.md"  # BATCH7 README
    ]
    
    # Get last commit time
    last_commit_time = get_last_commit_time(base_dir)
    
    updated_count = 0
    for readme_path in readme_files:
        if not readme_path.exists():
            continue
        
        # Read README - use binary mode to avoid encoding issues
        try:
            with open(readme_path, 'rb') as f:
                content_bytes = f.read()
                # Remove BOM if present
                if content_bytes.startswith(b'\xef\xbb\xbf'):
                    content_bytes = content_bytes[3:]
                content = content_bytes.decode('utf-8')
        except Exception as e:
            print(f"Error reading {readme_path}: {e}", file=sys.stderr)
            continue
        
        # Replace placeholder OR hardcoded timestamp
        original_content = content
        
        # Replace placeholder if it exists
        if "{LAST_GIT_COMMIT_TIME}" in content:
            content = content.replace("{LAST_GIT_COMMIT_TIME}", last_commit_time)
        
        # Also replace any hardcoded timestamp pattern OR corrupted "P25" pattern
        import re
        
        # Fix corrupted "P25" pattern first (encoding issue)
        if 'P25-' in content:
            content = re.sub(r'P25-\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', '**Last Update:** ' + last_commit_time, content)
        
        # Pattern to match: **Last Update:** followed by timestamp (with or without UTC)
        pattern = r'(\*\*Last Update:\*\*\s*)\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\s*(?:UTC)?\s*\n)'
        if re.search(pattern, content):
            content = re.sub(pattern, r'\1' + last_commit_time + r'\2', content)
        
        # Pattern for "last update was **timestamp**"
        pattern2 = r'(last update was \*\*)\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\s*(?:UTC)?\s*\*\*)'
        if re.search(pattern2, content, re.IGNORECASE):
            content = re.sub(pattern2, r'\1' + last_commit_time + r'\2', content, flags=re.IGNORECASE)
        
        # More flexible pattern - any timestamp after "Last Update:"
        pattern3 = r'(\*\*Last Update:\*\*\s*)\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(.*?\n)'
        if re.search(pattern3, content):
            content = re.sub(pattern3, r'\1' + last_commit_time + r'\2', content)
        
        # Only write if changed
        if content != original_content:
            try:
                # Write with UTF-8 encoding without BOM - use binary mode to avoid encoding issues
                content_bytes = content.encode('utf-8')
                # Remove BOM if present
                if content_bytes.startswith(b'\xef\xbb\xbf'):
                    content_bytes = content_bytes[3:]
                with open(readme_path, 'wb') as f:
                    f.write(content_bytes)
                print(f"Updated {readme_path.name} with last commit time: {last_commit_time}")
                updated_count += 1
            except Exception as e:
                print(f"Error writing {readme_path}: {e}", file=sys.stderr)
    
    if updated_count > 0:
        return True
    else:
        print(f"README files already up to date (last commit: {last_commit_time})")
        return True


def main() -> None:
    # Determine base directory
    script_dir = Path(__file__).parent.absolute()
    if script_dir.name == "BATCH7":
        base_dir = script_dir.parent
    else:
        base_dir = script_dir
    
    update_readme(base_dir)


if __name__ == "__main__":
    main()

