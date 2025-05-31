# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

DorleStories is a handwritten German text OCR and translation system using Google's Gemini AI. The workflow consists of two sequential AI operations:

1. **OCR Extraction**: Processes handwritten German document images through Gemini's vision model to extract text
2. **Translation**: Translates the extracted German markdown to English using Gemini's text model

### Core Components

- `StoryTranslator.py`: Main processing script with OCR and translation functions
- `download_test_images.py`: Utility to download sample German handwritten documents for testing
- `input/`: Directory containing source images (JPG, JPEG, PNG)
- `german_output/`: Extracted German text saved as `.txt` files 
- `english_output/`: Final English translations saved as `.txt` files

### Key Configuration

- Model: `gemini-2.5-pro-preview-05-20`
- OCR Temperature: 0.3 (for accuracy)
- Translation Temperature: 0.7 (balance of accuracy and fluency)
- Requires `GEMINI_API_KEY` environment variable in `.env` file

## Development Commands

### Setup
```bash
pip install google-generativeai python-dotenv requests
```

### Running the translator
```bash
python StoryTranslator.py
```

### Download test images
```bash
python download_test_images.py
```

## Processing Workflow

The system processes each image independently:
1. Upload image to Gemini API
2. Extract German text using vision model with streaming response
3. Save extracted text to `german_output/`
4. Translate German text to English using text model
5. Save translation to `english_output/`

Files are skipped if output already exists, allowing for resumable processing.