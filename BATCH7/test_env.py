#!/usr/bin/env python3
"""Test if .env file is being loaded correctly."""
from dotenv import load_dotenv
import os
from pathlib import Path

script_dir = Path(__file__).parent.absolute()
env_path = script_dir / ".env"

print(f"Script directory: {script_dir}")
print(f"Looking for .env at: {env_path}")
print(f".env exists: {env_path.exists()}")

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    key = os.environ.get("GEMINI_API_KEY", "")
    print(f"\nAPI Key loaded: {len(key) > 0}")
    print(f"Key length: {len(key)}")
    if key:
        print(f"Key starts with: {key[:10]}")
        print(f"Key ends with: {key[-10:]}")
        print(f"Key matches expected: {key.startswith('AIzaSy')}")
else:
    print("\n.env file not found!")

