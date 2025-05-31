# StoryTranslator

This script processes images of handwritten German text and translates them to English.
It performs two main steps:

1. **Extract German Text**: Uses Gemini AI to extract handwritten German text from images in the `input` directory.
2. **Translate to English**: Uses Gemini AI to translate the extracted German markdown into English.

## Prerequisites

- A `.env` file at the project root with your API key:
  ```
  GEMINI_API_KEY=your_api_key_here
  ```
- Install required Python packages:
  ```bash
  pip install google-generativeai python-dotenv requests
  ```

## Usage

1. Place your input images (e.g., JPG, PNG) into the `input` directory (create it if it doesn't exist).
2. Run the script:
   ```bash
   python StoryTranslator.py
   ```
3. Extracted and translated markdown files will be saved in the `output` directory:
   - `German_<image_name>.md` contains the extracted German text.
   - `English_<image_name>.md` contains the translated English text.

## Directory Structure

```
StoryTranslator/
├── input/            # Place handwritten German images here
├── output/           # Generated markdown files will be saved here
├── StoryTranslator.py
└── README.md
```