#!/usr/bin/env python3
"""Test if API key works with Gemini."""
from dotenv import load_dotenv
import os
from pathlib import Path
from google import genai
from google.genai import types

script_dir = Path(__file__).parent.absolute()
env_path = script_dir / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("GEMINI_API_KEY", "").strip()
print(f"Testing API key (length: {len(api_key)})...")

if not api_key:
    print("ERROR: No API key found")
    exit(1)

try:
    client = genai.Client(api_key=api_key)
    print("Client created successfully")
    
    # Try a simple test call
    print("Making test API call...")
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[types.Content(
            role="user",
            parts=[types.Part.from_text(text="Say 'API key works' if you can read this.")]
        )]
    )
    
    print(f"SUCCESS! API key is valid.")
    print(f"Response: {response.text[:100]}")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

