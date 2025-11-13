# BATCH7 Pipeline: House Oversight Committee Document Processing

## Overview

This pipeline processes House Oversight Committee documents using the same LLM-based extraction and analysis approach as the Dorle's Stories pipeline, but adapted for official government documentation.

## Structure

The pipeline processes three types of inputs:

1. **NATIVES/** - Excel spreadsheets: Analyze structure, extract relationships, build connection maps
2. **IMAGES/** - Images: OCR/extract text, describe pictures, output complex JSON
3. **TEXT/** - Text conversations: Extract content, understand context, assemble into stories/letters

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

Note: This adds `pandas` and `openpyxl` for Excel processing.

## Configuration

Set your Gemini API key:

```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

Or create a `.env` file in the project root:
```
GEMINI_API_KEY=your-api-key-here
```

## Usage

### Run All Processing Stages

```bash
python BATCH7/run_batch7_pipeline.py --process all
```

### Run Individual Stages

```bash
# Process Excel files only
python BATCH7/run_batch7_pipeline.py --process natives

# Process images only
python BATCH7/run_batch7_pipeline.py --process images

# Process text files only
python BATCH7/run_batch7_pipeline.py --process text
```

### Options

- `--base-dir BATCH7` - Base directory containing NATIVES/, IMAGES/, TEXT/
- `--output-dir BATCH7/output` - Output directory for all results
- `--skip-existing` - Skip files that already have outputs

## Output Structure

```
BATCH7/
├── NATIVES/
│   └── 001/
│       └── *.xls, *.xlsx
├── IMAGES/
│   └── 001/
│       └── *.jpg (with *.json alongside)
├── TEXT/
│   └── 001/
│       └── *.txt
└── output/
    ├── natives_analysis/
    │   └── *_analysis.json
    ├── images_analysis/  (not used - JSON saved with images)
    └── text_analysis/
        ├── text_extractions.json
        ├── stories_assembly.json
        └── letters/
            ├── S0001/
            │   ├── meta.json
            │   ├── text.txt
            │   └── source_files.txt
            └── S0002/...
```

## Processing Details

### NATIVES (Excel)

- Reads all worksheets in each Excel file
- Extracts tabular data preserving structure
- Identifies entities (people, organizations, dates, locations)
- Maps relationships between entities
- Outputs JSON analysis files

### IMAGES

- Performs OCR to extract all visible text
- Describes image content and layout
- Extracts structured data (dates, names, document numbers)
- Outputs JSON file alongside each image (same name, .json extension)

### TEXT

- Extracts content from each text file
- Groups related texts into coherent narratives
- Assembles stories similar to Dorle's Stories pipeline
- Creates `letters/` folder structure with:
  - `meta.json` - Story metadata
  - `text.txt` - Assembled narrative
  - `source_files.txt` - List of source files

## Prompt Design

All prompts are designed with these principles:

1. **Accuracy First**: Never hallucinate or infer beyond what is present
2. **Structured Output**: Always use JSON for machine-readable results
3. **Provenance**: Always include source file names and references
4. **Confidence Scores**: Include confidence levels for uncertain extractions
5. **Error Handling**: Note unclear, damaged, or ambiguous content

See `PROMPT_DESIGN.md` for detailed prompt specifications.


## Notes

- The pipeline uses Gemini 2.5 Pro for all LLM operations
- Processing can be time-consuming for large batches
- Use `--skip-existing` to resume interrupted processing
- JSON outputs are designed for downstream analysis and relationship mapping

