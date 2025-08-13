# Dorle's Stories: AI-Powered Historical Letter Digitization

A sophisticated multi-phase pipeline for digitizing, translating, and analyzing historical German handwritten letters using Google Gemini AI.

## Overview

This project transforms handwritten German letters into accessible English translations with comprehensive historical analysis. It employs a 5-phase processing pipeline that combines OCR, translation, socio-historical analysis, and academic formatting.

## Processing Pipeline

The `ImageTranslator.py` script orchestrates a comprehensive 5-phase workflow:

### Input → Output Flow

**INPUT:**
- **Source:** `input/` folder
- **Files:** All `.jpeg`, `.jpg`, or `.png` files
- **Processing order:** Sorted numerically (extracts numbers from filename)

**OUTPUTS (5 phases):**

1. **Phase 1 - OCR:** Each image → individual German text file
   - `input/image.jpeg` → `german_output/image_german.txt`
   - Temperature: 0.4 (optimized for accuracy)

2. **Phase 2 - Translation:** ALL German texts combined → single English file
   - All `german_output/*_german.txt` → `english_output/combined_english_translation.txt`
   - Temperature: 0.8 (balanced for fluency)

3. **Phase 3 - Analysis:** Combined English → narrative analysis
   - `english_output/combined_english_translation.txt` → `narrative_analysis_of_letters.txt` (root folder)
   - Temperature: 0.75 (nuanced interpretation)

4. **Phase 4 - LaTeX:** Combined English → LaTeX document
   - `english_output/combined_english_translation.txt` → `combined_english_letter.tex` (root folder)
   - Temperature: 0.2 (precise formatting)

5. **Phase 5 - Markdown:** Combined English → clean Markdown
   - `english_output/combined_english_translation.txt` → `combined_english_for_google_docs.md` (root folder)
   - Temperature: 0.1 (minimal alteration)

## Project Structure

```
DorleStories/
├── input/                  # Source images (JPEG handwritten letters)
├── german_output/          # OCR results (German text files)
├── english_output/         # Translation results
├── analysis_output/        # Historical analysis outputs
├── characters/            # Character intelligence profiles (future)
├── ImageTranslator.py     # Main 5-phase pipeline
├── PDFTranslator.py       # PDF processing variant
├── agent_monitor.py       # Character intelligence extraction
├── config.yaml           # Configuration (currently unused by main pipeline)
├── requirements.txt      # Dependencies
└── CLAUDE.md            # Project instructions for Claude AI

```

## Requirements

- Python 3.8+
- Google Gemini API key (set as `GEMINI_API_KEY` environment variable)
- Dependencies: `google-genai`, `python-dotenv`, `Pillow`

## Installation

```bash
# Install dependencies
pip install google-genai python-dotenv Pillow

# Set up environment variable
export GEMINI_API_KEY="your-api-key-here"
# Or create a .env file with: GEMINI_API_KEY=your-api-key-here
```

## Usage

```bash
# Run the main pipeline
python ImageTranslator.py

# Process PDF files (for bulk documents)
python PDFTranslator.py

# Run character intelligence agent (optional)
python agent_monitor.py
```

## Key Features

- **Resumable Processing**: Already processed files are automatically skipped
- **Ordered Processing**: Files are processed in numerical order
- **Streaming API**: Handles large responses efficiently
- **Error Handling**: Includes retry logic and detailed error reporting
- **Modular Design**: Each phase can be run independently

## Sample Output

Original letter images: [Google Drive Folder](https://drive.google.com/drive/folders/1cENU2bUHmNftyPIvsNaEoNaGSY0HfxZS?usp=sharing)

Example translation (from handwritten German):
```
Hofheim, November 22nd

Dear Mech!

Many thanks for your letter. When are you finally going to send me
the pictures from Säntis? I've been waiting half a year for them already...
```

## Configuration Notes

- Model: Gemini 2.5 Pro (specified as "gemini-2.5-pro" in code)
- The `config.yaml` file exists but is not currently used by the main pipeline
- All settings are hardcoded in `ImageTranslator.py` for simplicity

## Development Status

✅ Phase 1-5: Fully functional pipeline
⚠️ Character intelligence agent: In development
📝 Config integration: Planned enhancement 