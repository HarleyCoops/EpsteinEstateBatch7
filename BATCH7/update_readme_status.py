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
    """Update README.md with latest commit time."""
    readme_path = base_dir / "BATCH7" / "README.md"
    if not readme_path.exists():
        readme_path = base_dir / "README.md"
    
    if not readme_path.exists():
        print(f"Error: README.md not found at {readme_path}", file=sys.stderr)
        return False
    
    # Get last commit time
    last_commit_time = get_last_commit_time(base_dir)
    
    # Read README
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading README: {e}", file=sys.stderr)
        return False
    
    # Replace placeholder
    updated_content = content.replace("{LAST_GIT_COMMIT_TIME}", last_commit_time)
    
    # Only write if changed
    if updated_content != content:
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"Updated README.md with last commit time: {last_commit_time}")
            return True
        except Exception as e:
            print(f"Error writing README: {e}", file=sys.stderr)
            return False
    else:
        print(f"README.md already up to date (last commit: {last_commit_time})")
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

