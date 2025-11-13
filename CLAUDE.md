# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

DorleStories is a multi-pipeline system for document digitization and analysis using Google Gemini AI. It includes three distinct pipelines:

1. **German Letters Pipeline**: LLM-based semantic grouping for handwritten historical letters
2. **Chinese Pipeline**: Deterministic grouping for Chinese documents
3. **BATCH7 Pipeline**: House Oversight Committee document processing (Excel, images, text)

## Pipeline Systems

### German Letters Pipeline (LLM-Based Semantic Grouping)

Main entry point: [run_letters_pipeline.py](run_letters_pipeline.py)

**Stage 1 - OCR & LLM Grouping** ([llm_group_letters.py](llm_group_letters.py)):

- Performs OCR on handwritten German images using Gemini 2.5 Pro
- Uses LLM to semantically group pages into complete letters based on content
- Assembles German text (`de.txt`) for each letter with provenance metadata

**Stage 2 - Translation** ([translate_letters.py](translate_letters.py)):

- Translates German letters to English using Gemini 2.5 Pro
- Generates LaTeX documents (`en.tex`) for PDF compilation

**Why LLM Grouping?** File metadata (dates, filenames) is unreliable for scanned historical documents. The LLM reads content to understand narrative flow and correctly groups pages that belong together.

### Chinese Pipeline (Deterministic Grouping)

Main entry point: [run_chinese_strict_pipeline.py](run_chinese_strict_pipeline.py)

**Architecture**: Module-based in [china_pipeline/](china_pipeline/)

- [pipeline.py](china_pipeline/pipeline.py): OCR + deterministic grouping + assembly
- [translate_letters.py](china_pipeline/translate_letters.py): Translation to English + LaTeX
- [grouping.py](china_pipeline/grouping.py): Deterministic grouping based on timestamps and lexical similarity

**Key Difference**: Uses capture time and content similarity instead of LLM inference for grouping, providing deterministic and auditable results.

### BATCH7 Pipeline (Government Document Processing)

Main entry point: [BATCH7/run_batch7_pipeline.py](BATCH7/run_batch7_pipeline.py)

**Purpose**: Process House Oversight Committee documents with three specialized workflows:

1. **NATIVES Processing** ([batch7_process_natives.py](BATCH7/batch7_process_natives.py)):
   - Analyzes Excel spreadsheets (.xls, .xlsx)
   - Extracts tabular data and identifies entities (people, organizations, dates)
   - Maps relationships between entities
   - Outputs JSON analysis files

2. **IMAGES Processing** ([batch7_process_images.py](BATCH7/batch7_process_images.py)):
   - Performs OCR on document images
   - Describes image content and layout
   - Extracts structured data (dates, names, document numbers)
   - Outputs JSON file alongside each image

3. **TEXT Processing** ([batch7_process_text.py](BATCH7/batch7_process_text.py)):
   - Extracts content from text files
   - Groups related texts into coherent narratives
   - Assembles stories similar to Dorle's Stories pipeline
   - Creates structured output in `letters/S####/` format

See [BATCH7/README.md](BATCH7/README.md) for detailed documentation.

## Common Development Commands

### Setup

```bash
# Install dependencies (includes pandas/openpyxl for BATCH7 Excel processing)
pip install -r requirements.txt

# Set API key (PowerShell)
$env:GEMINI_API_KEY="your-api-key-here"

# Or create .env file
echo "GEMINI_API_KEY=your-api-key-here" > .env
```

### German Letters Processing
```bash
# Full pipeline (OCR → Group → Translate → LaTeX)
python run_letters_pipeline.py --base DorleLettersF

# Skip LaTeX generation
python run_letters_pipeline.py --base DorleLettersE --no-latex

# Force re-translation
python run_letters_pipeline.py --base DorleLettersG --force-translate

# Individual stages
python llm_group_letters.py --images-dir DorleLettersF/DorleLettersF --german-dir DorleLettersF/german_output --output-dir DorleLettersF/letters --run-ocr --assemble
python translate_letters.py --letters-dir DorleLettersF/letters --latex
```

### Chinese Document Processing

```bash
# Full Chinese pipeline
python run_chinese_strict_pipeline.py --base ChineseBook

# Skip LaTeX
python run_chinese_strict_pipeline.py --base ChineseBook --no-latex

# Force re-translation
python run_chinese_strict_pipeline.py --base ChineseBook --force-translate
```

### BATCH7 Document Processing

```bash
# Process all document types (Excel, images, text)
python BATCH7/run_batch7_pipeline.py --process all

# Process specific document types
python BATCH7/run_batch7_pipeline.py --process natives   # Excel only
python BATCH7/run_batch7_pipeline.py --process images    # Images only
python BATCH7/run_batch7_pipeline.py --process text      # Text only

# Resume interrupted processing
python BATCH7/run_batch7_pipeline.py --process all --skip-existing

# Process specific subdirectory
python BATCH7/run_batch7_pipeline.py --natives-dir "BATCH7/NATIVES/001" --process natives
```

### PDF Generation

```bash
# Compile LaTeX to PDF for multiple collections
python build_pdfs.py --glob "DorleLetters[A-M]" --engine xelatex --cleanup

# Auto-detect LaTeX engine
python build_pdfs.py --glob "DorleLetters[A-M]"

# Dry run
python build_pdfs.py --glob "DorleLetters[A-M]" --dry-run
```

**LaTeX Engine Prerequisites**:

- Tectonic (recommended): `winget install Tectonic.Tectonic`
- Or MiKTeX (pdflatex/xelatex)

### Testing

```bash
# Run all tests
pytest -q

# Tests are in helperPython/test_*.py
```

## Directory Structure

```text
DorleStories/
├── run_letters_pipeline.py          # German letters main wrapper
├── llm_group_letters.py              # LLM-based grouping for German
├── translate_letters.py              # Translation for German letters
├── run_chinese_strict_pipeline.py   # Chinese pipeline main wrapper
├── build_pdfs.py                     # LaTeX → PDF compiler
├── china_pipeline/                   # Chinese processing modules
│   ├── pipeline.py                   # OCR + deterministic grouping
│   ├── translate_letters.py          # Chinese translation
│   └── grouping.py                   # Grouping utilities
├── helperPython/                     # Legacy code & utilities
│   ├── ImageTranslator.py            # Legacy 6-phase pipeline
│   ├── culturalshifts.py             # Cultural analysis (optional)
│   ├── agent_monitor.py              # Character intelligence (optional)
│   └── test_*.py                     # Test files
├── DorleLetters[A-M]/                # German letter collections
│   ├── DorleLetters*/                # Input images
│   ├── german_output/                # OCR results
│   └── letters/                      # Assembled letters
│       ├── L0001/
│       │   ├── de.txt                # German text
│       │   ├── en.txt                # English translation
│       │   ├── en.tex                # LaTeX document
│       │   └── meta.json             # Provenance metadata
│       └── llm_grouping.json         # Grouping manifest
├── Chinese/                          # Chinese document collections
├── BATCH7/                           # Government document processing
│   ├── run_batch7_pipeline.py        # Main BATCH7 wrapper
│   ├── batch7_process_natives.py     # Excel processing
│   ├── batch7_process_images.py      # Image OCR + analysis
│   ├── batch7_process_text.py        # Text extraction + assembly
│   ├── NATIVES/                      # Input: Excel files
│   ├── IMAGES/                       # Input: Document images
│   ├── TEXT/                         # Input: Text files
│   └── output/                       # All processing outputs
│       ├── natives_analysis/         # Excel analysis JSON
│       └── text_analysis/
│           └── letters/S####/        # Assembled stories
├── config.yaml                       # Configuration (not fully used)
└── .env                              # API keys (not committed)
```

## Output Files Explained

### German & Chinese Letters

After processing, each letter directory contains:

- **`llm_grouping.json`**: Manifest showing which source images belong to each letter
- **`L####/de.txt`** or **`L####/zh.txt`**: Original language text
- **`L####/en.txt`**: English translation
- **`L####/en.tex`**: LaTeX formatted document
- **`L####/meta.json`**: Provenance metadata (source files, timestamps)

### BATCH7 Documents

After processing BATCH7 documents:

- **Excel**: `output/natives_analysis/*_analysis.json` (entity extraction, relationships)
- **Images**: `*.json` saved alongside each image file (OCR text, layout description, structured data)
- **Text**: `output/text_analysis/letters/S####/` directories containing:
  - `meta.json`: Story metadata
  - `text.txt`: Assembled narrative
  - `source_files.txt`: List of source text files

## Important Implementation Details

### API Configuration

- **Model**: `gemini-2.5-pro` (set in code, not config.yaml)
- **API Key**: Must be set via `GEMINI_API_KEY` environment variable or `.env` file
- **Streaming**: All Gemini API calls use streaming for large responses

### Processing Behavior

- **Resumable**: Already processed files are skipped automatically (use `--skip-existing` for BATCH7)
- **File Naming**: OCR outputs preserve source filenames (e.g., `IMG_3762.jpg` → `IMG_3762_german.txt`)
- **Provenance**: Every output includes metadata tracking source images/files
- **Error Handling**: Retry logic for API failures

### BATCH7 Specific

BATCH7 follows strict accuracy principles:

- **No Hallucination**: Never infers information beyond what is present in documents
- **Structured Output**: All outputs are JSON for machine-readable analysis
- **Confidence Scores**: Includes confidence levels for uncertain extractions
- **Entity Extraction**: Identifies people, organizations, dates, locations from Excel, images, and text
- **Relationship Mapping**: Maps connections between entities across documents

### Legacy Code (helperPython/)

The `helperPython/` directory contains:

- **ImageTranslator.py**: Original 6-phase pipeline (OCR → Translation → Analysis → LaTeX → Markdown)
- **culturalshifts.py**: PhD-level socio-historical analysis (optional)
- **agent_monitor.py**: OpenAI-based character intelligence extraction (optional)

These are NOT part of the main pipeline but remain for specialized workflows.

## Coding Conventions

- **Python Version**: 3.10+
- **Style**: PEP 8, 4-space indentation, snake_case functions, UPPER_CASE constants
- **Type Hints**: Use where appropriate for public APIs
- **Imports**: Group as stdlib, third-party, local modules
- **Testing**: Add tests to `helperPython/test_*.py` for new utilities

## Commit Guidelines

- **Format**: Conventional Commits (feat:, fix:, docs:)
- **Messages**: Imperative mood, scoped to component
- **PRs**: Include reproduction commands, mention `--base` collection used for validation
- **Security**: Never commit API keys or large binaries
