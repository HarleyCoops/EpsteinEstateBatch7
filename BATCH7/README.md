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
- Reuses `llm_group_letters.py` with the new `--text-dir/--pages-dir` flag (no adapters needed):
  ```bash
  python llm_group_letters.py --text-dir BATCH7/TEXT/001 --output-dir BATCH7/output/text_letters --assemble --save-input
  ```
- Produces `letters/` folder structure with:
  - `meta.json` - Story metadata including `source_files` and `house_oversight_ids`
  - `text.txt` (and legacy `de.txt`) - Assembled narrative
  - `en.txt` / `en.tex` when `translate_letters.py --letters-dir BATCH7/output/text_letters --latex` is run

## Prompt Design

All prompts are designed with these principles:

1. **Accuracy First**: Never hallucinate or infer beyond what is present
2. **Structured Output**: Always use JSON for machine-readable results
3. **Provenance**: Always include source file names and references
4. **Confidence Scores**: Include confidence levels for uncertain extractions
5. **Error Handling**: Note unclear, damaged, or ambiguous content

See `PROMPT_DESIGN.md` for detailed prompt specifications.

See `TASK_BREAKDOWN.md` for verbose 21-step implementation plan covering:
- Text Files → Letters Flow (7 steps)
- Provenance and Aggregation (7 steps)  
- Token/Runtime Optimization (7 steps)

## Notes

- The pipeline uses Gemini 2.5 Pro Flash for all LLM operations
- Processing can be time-consuming for large batches
- Use `--skip-existing` to resume interrupted processing
- JSON outputs are designed for downstream analysis and relationship mapping
- Core orchestration scripts (`llm_group_letters.py`, `translate_letters.py`, `run_letters_pipeline.py`, `build_pdfs.py`) and `requirements.txt` are now copied into this `BATCH7/` folder so the project can run in isolation or be pushed to a standalone repo (e.g., `EpsteinEstateBatch7`). Run them from this directory to avoid reaching back into the parent repo.

## Future Directions

### Enhanced Image Classification and Schema Variants

Currently, `batch7_process_images.py` sends every image through the same prompt (`PROMPT_IMAGE_ANALYSIS`), producing a generic schema. To better handle different document types (court documents vs casual photos), we can enrich the prompt without overhauling the pipeline:

#### Explicit Classification Step

Add a document type decision tree before extraction:
- "Determine whether this image is a court/official document, a photographed page, or other. Use the appropriate schema rules."

Then describe each schema block:

- **Court/Official documents** → require docket numbers, case captions, filing dates, parties, judge, signature blocks, stamps, etc.
- **Photographed/other text sources** → emphasize raw text transcription plus contextual analysis (topics, people, locations) and character profile hooks.

The existing `PROMPT_IMAGE_ANALYSIS` string (lines 15-76 in `batch7_process_images.py`) is the place to encode these instructions.

#### Schema Switch Inside Same JSON

Keep a top-level `document_class` field and provide separate sub-objects:

```json
{
  "file_name": "...",
  "document_class": "court_document",
  "court_document": {
    "docket_number": "...",
    "case_caption": "...",
    "filing_date": "...",
    "parties": [...],
    "judge": "...",
    "signature_blocks": [...],
    "stamps": [...]
  },
  "general_text": null,
  "character_profiles": null
}
```

Gemini can leave the unused section null. That keeps the output single-schema while still forcing it to fill the right subsection.

#### Character/Context Extraction

Add a `character_profiles` array in the prompt requirements:
- "For each named person, provide role, affiliations, and evidence snippet."

That feeds character intelligence without running a separate agent.

#### Implementation

1. Edit `PROMPT_IMAGE_ANALYSIS` to spell out:
   - The classification rubric
   - The two schema variants (court_document vs general_text)
   - The requirement to populate `document_class`
   - Character profile extraction requirements

2. No code change beyond the prompt is needed; `batch7_process_images.py` already writes the JSON next to each image.

3. Optional: Add JSON Schema validation (per `JSON_SCHEMA_RUBRIC.md`) and validate before saving.

4. Rerun processing: `python BATCH7/run_batch7_pipeline.py --process images --skip-existing` to update existing images with new schema, or process new images with the enhanced prompt.

This enhancement maintains backward compatibility (existing JSONs remain valid) while enabling more targeted extraction for different document types.

