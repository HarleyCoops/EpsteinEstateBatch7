#!/usr/bin/env python3
"""
Update the README.md with the latest git commit time.

This script updates the {LAST_GIT_COMMIT_TIME} placeholder in README.md
with the timestamp of the most recent git commit.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone
import re


LAST_UPDATE_PATTERNS = [
    re.compile(r"(\*\*Last Update:\*\*\s*)(.*?)(\s{2,})", re.IGNORECASE),
    re.compile(r"(\*\*Last Updated:\*\*\s*)(.*?)(\s{2,})", re.IGNORECASE),
    re.compile(r"(last update was \*\*)(.*?)(\*\*)", re.IGNORECASE),
]


def get_current_timestamp() -> str:
    """Return a UTC timestamp string for README use."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def update_timestamps(content: str, timestamp: str) -> tuple[str, bool]:
    """Replace any Last Update markers with the provided timestamp."""
    updated = False
    
    for pattern in LAST_UPDATE_PATTERNS:
        def replacement(match: re.Match, *, pattern=pattern) -> str:
            nonlocal updated
            updated = True
            suffix = ""
            if match.lastindex and match.lastindex >= 3:
                suffix = match.group(3)
            return f"{match.group(1)}{timestamp}{suffix}"
        
        content, count = pattern.subn(replacement, content)
        if count:
            updated = True
    
    return content, updated


def update_readme(base_dir: Path) -> bool:
    """Update README.md files with the current timestamp."""
    # Update both root README and BATCH7 README
    readme_files = [
        base_dir / "README.md",  # Root README
        base_dir / "BATCH7" / "README.md"  # BATCH7 README
    ]
    
    current_timestamp = get_current_timestamp()
    
    updated_count = 0
    for readme_path in readme_files:
        if not readme_path.exists():
            continue
        
        # Read README
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {readme_path}: {e}", file=sys.stderr)
            continue
        
        updated_content, changed = update_timestamps(content, current_timestamp)
        
        if changed:
            try:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"Updated {readme_path.name} with timestamp: {current_timestamp}")
                updated_count += 1
            except Exception as e:
                print(f"Error writing {readme_path}: {e}", file=sys.stderr)
    
    if updated_count == 0:
        print("README files already up to date.")
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

