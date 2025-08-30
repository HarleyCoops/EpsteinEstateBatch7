#!/usr/bin/env python3
"""
Test script to debug single image extraction
"""
import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def test_extract(image_path):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set")
        return
    
    client = genai.Client(api_key=api_key)
    
    print(f"Testing extraction on: {image_path}")
    print(f"File exists: {os.path.exists(image_path)}")
    print(f"File size: {os.path.getsize(image_path)} bytes")
    
    # Try with modified prompt that handles rotated images
    prompts = [
        # Original prompt
        "This is a single page image of a handwritten German document.\nExtract the handwritten German text exactly as it appears.\nReturn the result in plain text format.",
        
        # More specific prompt
        "This image contains a historical German letter or document. The image may be rotated or sideways. Please extract ALL handwritten German text you can see, regardless of orientation. If the page appears blank or only contains an envelope, indicate that. Return the extracted text in plain format.",
        
        # Even more aggressive prompt
        "Carefully examine this image. It may contain:\n1. Handwritten German text (possibly sideways or upside down)\n2. Typed German text\n3. An envelope\n4. A blank page\n\nExtract ANY text you can find, noting if the image needs rotation to read properly. If you see text but it's hard to read due to orientation, still attempt to extract it.",
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n--- Attempt {i} with prompt variant ---")
        print(f"Prompt: {prompt[:100]}...")
        
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=image_data,
                            mime_type="image/jpeg"
                        ),
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]
            
            config = types.GenerateContentConfig(
                temperature=0.4,
                response_mime_type="text/plain",
                thinking_config=types.ThinkingConfig(thinking_budget=512),
            )
            
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=contents,
                config=config,
            )
            
            result = response.text if response.text else "[EMPTY RESPONSE]"
            print(f"Response length: {len(result)} chars")
            print(f"First 500 chars: {result[:500]}")
            
            if len(result) > 10:  # If we got meaningful content, stop trying
                return result
                
        except Exception as e:
            print(f"Error: {e}")
    
    return None

if __name__ == "__main__":
    # Test on a problematic image
    test_images = [
        "input/0E3AFA2B-CD87-45C7-AA85-5D7FAE9770C6_1_105_c.jpeg",  # First sideways one
        "input/450111BB-700E-40F8-AE4D-E0B4FF3A0B7D_1_105_c.jpeg",  # Another sideways one
        "input/FCDDE3CA-6A98-4E2E-A058-A6380FA5A2DD_1_105_c.jpeg",  # The one that worked
    ]
    
    for img_path in test_images:
        print(f"\n{'='*60}")
        result = test_extract(img_path)
        if result:
            output_file = img_path.replace("input/", "test_output_").replace(".jpeg", ".txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"\nFull result saved to: {output_file}")
        print(f"{'='*60}\n")
