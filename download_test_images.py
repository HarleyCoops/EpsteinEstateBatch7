#!/usr/bin/env python3
"""
Download German handwritten document sample images for testing StoryTranslator
"""
import os
import requests
from urllib.parse import urlparse

# Sample German handwritten document URLs from Deutsche Fotothek and other sources
SAMPLE_URLS = [
    # Athanasius Kircher handwritten manuscript about sunspots
    "https://upload.wikimedia.org/wikipedia/commons/9/9a/Athanasius_Kircher_sunspots.jpg",
    
    # Geometry manuscript with handwritten German text
    "https://upload.wikimedia.org/wikipedia/commons/3/3d/Fotothek_df_tg_0000038_Geometrie_%5E_Messger%C3%A4t.jpg",
    
    # Another geometry manuscript
    "https://upload.wikimedia.org/wikipedia/commons/7/72/Fotothek_df_tg_0000039_Titelkupfer.jpg",
]

def download_image(url, output_dir):
    """Download an image from URL to output directory"""
    try:
        # Get filename from URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # Ensure filename has proper extension
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            filename += '.jpg'
        
        output_path = os.path.join(output_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(output_path):
            print(f"Skipping {filename} (already exists)")
            return output_path
        
        print(f"Downloading {url}...")
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Saved: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def main():
    # Set up directories
    base_dir = os.path.dirname(__file__)
    input_dir = os.path.join(base_dir, 'input')
    
    # Create input directory if it doesn't exist
    os.makedirs(input_dir, exist_ok=True)
    
    print(f"Downloading sample German handwritten documents to: {input_dir}")
    
    downloaded_files = []
    for url in SAMPLE_URLS:
        result = download_image(url, input_dir)
        if result:
            downloaded_files.append(result)
    
    print(f"\nDownload complete! {len(downloaded_files)} files downloaded:")
    for file_path in downloaded_files:
        print(f"  - {os.path.basename(file_path)}")
    
    print(f"\nTo test StoryTranslator with these samples, run:")
    print(f"  python {os.path.join(base_dir, 'StoryTranslator.py')}")

if __name__ == "__main__":
    main()