# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

DorleStories is a multi-phase AI pipeline for digitizing historical German handwritten letters. It uses Google Gemini for OCR/translation and optionally OpenAI for character intelligence extraction.

### Processing Pipeline

1. **Phase 1 - OCR**: Extract German text from handwritten images using Gemini vision model
2. **Phase 2 - Translation**: Translate German to English using Gemini
3. **Phase 3 - Analysis**: Generate PhD-level socio-historical analysis
4. **Phase 4 - LaTeX**: Format for academic presentation
5. **Phase 5 - Markdown**: Convert for Google Docs

### Core Components

- `ImageTranslator.py`: Main 5-phase processing pipeline
- `config.yaml`: Central configuration for all settings
- `agent_monitor.py`: Character intelligence extraction (watches for new translations)
- `input/`: Source images directory
- `german_output/`: OCR results
- `english_output/`: Translations
- `analysis_output/`: Historical analysis
- `characters/`: Character profiles (JSON)

### Key Configuration (config.yaml)

- **Model**: `gemini-2.5-pro-preview-05-06`
- **OCR Temperature**: 0.4 (accuracy)
- **Translation Temperature**: 0.8 (fluency)
- **Analysis Temperature**: 0.75 (nuanced)
- **Environment**: Requires `GEMINI_API_KEY` in `.env` or environment

### Development Commands

```bash
# Setup
pip install -r requirements.txt

# Run main pipeline
python ImageTranslator.py

# Test character agent
python test_agent.py

# Download sample images
python download_test_images.py
```

### Processing Notes

- Files are processed in numeric order (IMG_3762, IMG_3763, etc.)
- Already processed files are skipped (resumable)
- Combined output files are created after individual processing
- Agent monitor runs independently to extract character data

### Important Patterns

- All Gemini API calls use streaming for large responses
- Error handling includes retry logic for API failures
- Output files use source filename as base (e.g., IMG_3762.jpg → IMG_3762_german.txt)
- Combined files aggregate all translations in order