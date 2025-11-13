# BATCH7 Pipeline Walkthrough

## Overview

The BATCH7 pipeline processes House Oversight Committee documents through three parallel processing streams, extracting structured information using LLM-powered analysis. This document walks you through how to run the pipeline and what happens at each stage.

## Prerequisites

### 1. Install Dependencies

```powershell
cd BATCH7
pip install -r requirements.txt
```

This installs:
- `google-genai` - Gemini API client
- `pandas` & `openpyxl` - Excel processing
- `python-dotenv` - Environment variable management
- `Pillow` - Image processing

### 2. Set Up API Key

**Option A: Environment Variable (PowerShell)**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

**Option B: .env File**
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your-api-key-here
```

### 3. Verify Directory Structure

Ensure your `BATCH7/` directory has:
```
BATCH7/
├── NATIVES/          # Excel files (.xls, .xlsx)
│   └── 001/
├── IMAGES/           # Image files (.jpg, .tif, etc.)
│   └── 001/
└── TEXT/             # Text files (.txt)
    └── 001/
```

## Running the Pipeline

### Full Pipeline (All Stages)

Process all three document types in sequence:

```powershell
python run_batch7_pipeline.py --process all
```

This will:
1. Process all Excel files in `NATIVES/`
2. Process all images in `IMAGES/`
3. Process all text files in `TEXT/`

### Individual Stages

Run stages separately for debugging or selective processing:

```powershell
# Process Excel files only
python run_batch7_pipeline.py --process natives

# Process images only
python run_batch7_pipeline.py --process images

# Process text files only
python run_batch7_pipeline.py --process text
```

### Advanced Options

```powershell
# Skip files that already have outputs (resume interrupted runs)
python run_batch7_pipeline.py --process all --skip-existing

# Specify custom directories
python run_batch7_pipeline.py --process all `
    --base-dir "BATCH7" `
    --output-dir "BATCH7/output" `
    --natives-dir "BATCH7/NATIVES/001" `
    --images-dir "BATCH7/IMAGES/001" `
    --text-dir "BATCH7/TEXT/001"
```

## Pipeline Architecture

The pipeline consists of three **parallel processing streams** that operate independently:

### Stream 1: NATIVES Processing (Excel Files)

**Input:** Excel spreadsheets (`.xls`, `.xlsx`) in `NATIVES/` subdirectories

**Process:**
1. **Structure Analysis**
   - Identifies all worksheets/tabs
   - Analyzes column headers and data types
   - Detects formulas and calculated fields
   - Notes merged cells and formatting

2. **Data Extraction**
   - Extracts all tabular data preserving structure
   - Normalizes date formats
   - Preserves row/column relationships

3. **Entity Identification**
   - Extracts people, organizations, locations, dates
   - Identifies document references and file numbers

4. **Relationship Mapping**
   - Maps connections between entities
   - Identifies hierarchies and groupings
   - Extracts transaction amounts and numerical relationships
   - Builds connection graphs

**Output:** `output/natives_analysis/<filename>_analysis.json`

**JSON Structure:**
```json
{
  "file_name": "...",
  "structure": {
    "worksheets": [...]
  },
  "data": {
    "<sheet_name>": [...]
  },
  "entities": {
    "people": [...],
    "organizations": [...],
    "locations": [...],
    "dates": [...]
  },
  "relationships": [...],
  "context": {...}
}
```

### Stream 2: IMAGES Processing

**Input:** Image files (`.jpg`, `.tif`, etc.) in `IMAGES/` subdirectories

**Process:**
1. **OCR (Optical Character Recognition)**
   - Extracts ALL visible text (typed, handwritten, printed)
   - Preserves line breaks and paragraph structure
   - Identifies text regions (headers, body, footnotes, stamps)
   - Notes text type (handwritten vs typed)

2. **Visual Description**
   - Classifies image type (document, photograph, diagram)
   - Describes layout and structure
   - Notes image quality, orientation, damage

3. **Structured Extraction**
   - Extracts dates, names, organizations
   - Extracts document numbers, case numbers, file references
   - Identifies signatures, stamps, official markings
   - Extracts contact information (phone, email, addresses)
   - Extracts financial amounts

4. **Context Analysis**
   - Determines document type (letter, memo, form, photo)
   - Identifies sender/recipient
   - Notes subject matter and references

**Output:** `<image_name>.json` saved **alongside each image** (same folder)

**JSON Structure:**
```json
{
  "file_name": "...",
  "image_analysis": {
    "type": "document|photograph|diagram",
    "description": "...",
    "layout": "...",
    "quality": "high|medium|low"
  },
  "text_extraction": {
    "full_text": "...",
    "text_regions": [...]
  },
  "structured_data": {
    "dates": [...],
    "people": [...],
    "organizations": [...],
    "document_numbers": [...],
    "financial_amounts": [...],
    "contact_info": {...}
  },
  "document_metadata": {...}
}
```

### Stream 3: TEXT Processing

**Input:** Text files (`.txt`) in `TEXT/` subdirectories

**Process:**

#### Phase 1: Content Extraction
1. **Text Extraction**
   - Extracts all text content preserving structure
   - Identifies document sections
   - Preserves paragraph breaks and formatting

2. **Context Understanding**
   - Determines document type (conversation, transcript, article, memo)
   - Identifies participants/speakers
   - Extracts time periods and dates
   - Identifies main topics/themes

3. **Entity Extraction**
   - Extracts dates, names, organizations, locations
   - Extracts document references and file numbers
   - Extracts key events/actions

**Output:** `output/text_analysis/text_extractions.json`

#### Phase 2: LLM Grouping & Assembly
Uses `llm_group_letters.py` to:
1. **Group Related Pages**
   - Analyzes all text files together
   - Groups pages that belong to the same narrative/letter/memo
   - Orders pages within each group chronologically
   - Preserves provenance (which files belong to which letter)

2. **Story Assembly**
   - Assembles grouped pages into coherent narratives
   - Creates `letters/` folder structure:
     ```
     output/text_analysis/letters/
     ├── S0001/
     │   ├── meta.json          # Metadata with source_files
     │   ├── text.txt           # Assembled narrative
     │   └── source_files.txt   # List of source files
     ├── S0002/
     │   └── ...
     ```

**Output:** `output/text_analysis/letters/S0001/`, `S0002/`, etc.

#### Phase 3: Translation (Optional)
Run `translate_letters.py` to translate assembled letters:

```powershell
python translate_letters.py `
    --letters-dir "BATCH7/output/text_analysis/letters" `
    --latex
```

This creates:
- `en.txt` - English translation
- `en.tex` - LaTeX formatted version (if `--latex` flag used)

## Workflow Diagram

See `PIPELINE_DIAGRAM.tex` for a visual TikZ diagram showing:
- Input sources (NATIVES/, IMAGES/, TEXT/)
- Processing stages for each stream
- LLM interactions (Gemini 2.5 Pro Flash)
- Output locations and formats
- Data flow and dependencies

## Output Structure

After running the full pipeline:

```
BATCH7/
├── NATIVES/
│   └── 001/
│       └── *.xls, *.xlsx
├── IMAGES/
│   └── 001/
│       ├── *.jpg
│       └── *.json          # ← JSON saved alongside images
├── TEXT/
│   └── 001/
│       └── *.txt
└── output/
    ├── natives_analysis/
    │   └── *_analysis.json
    ├── images_analysis/    # (not used - JSON saved with images)
    └── text_analysis/
        ├── text_extractions.json
        ├── stories_assembly.json
        └── letters/
            ├── S0001/
            │   ├── meta.json
            │   ├── text.txt
            │   ├── source_files.txt
            │   ├── en.txt          # (after translation)
            │   └── en.tex          # (after translation --latex)
            └── S0002/
                └── ...
```

## Processing Details

### LLM Model
- **Model:** Gemini 2.5 Pro Flash
- **Usage:** Each file/image makes one API call
- **Cost:** Pay-per-use API pricing

### Error Handling
- Files with errors are logged but don't stop the pipeline
- Use `--skip-existing` to resume interrupted processing
- Check console output for error messages

### Performance Considerations
- **Large batches:** Processing thousands of files can take hours
- **API rate limits:** Gemini API has rate limits; the pipeline handles retries
- **Resume capability:** Use `--skip-existing` to avoid reprocessing completed files

### Provenance Tracking
All outputs include:
- Source file names
- Processing timestamps
- Confidence scores
- References to related documents

## Common Workflows

### 1. First-Time Run
```powershell
# Set API key
$env:GEMINI_API_KEY="your-key"

# Run full pipeline
python run_batch7_pipeline.py --process all
```

### 2. Resume Interrupted Run
```powershell
python run_batch7_pipeline.py --process all --skip-existing
```

### 3. Process Only New Images
```powershell
python run_batch7_pipeline.py --process images --skip-existing
```

### 4. Text Processing + Translation
```powershell
# Step 1: Extract and group text
python run_batch7_pipeline.py --process text

# Step 2: Translate assembled letters
python translate_letters.py `
    --letters-dir "BATCH7/output/text_analysis/letters" `
    --latex
```

### 5. Test on Small Batch
```powershell
# Process only one subdirectory
python run_batch7_pipeline.py `
    --natives-dir "BATCH7/NATIVES/001" `
    --process natives
```

## Troubleshooting

### API Key Not Found
```
Error: GEMINI_API_KEY not set
```
**Solution:** Set the environment variable or create `.env` file

### Missing Dependencies
```
Error: pandas and openpyxl required
```
**Solution:** `pip install -r requirements.txt`

### Directory Not Found
```
NATIVES directory not found: ...
```
**Solution:** Check directory paths or create missing directories

### JSON Parsing Errors
If LLM returns malformed JSON:
- Check console output for the raw response
- The pipeline logs errors but continues
- Re-run with `--skip-existing` to retry failed files

## Next Steps

After processing:
1. **Review outputs** in `output/` directory
2. **Analyze relationships** using the JSON files
3. **Build connection maps** from entity relationships
4. **Generate PDFs** using `build_pdfs.py` (if needed)

## Related Documentation

- `README.md` - Overview and installation
- `QUICKSTART.md` - Quick reference guide
- `PROMPT_DESIGN.md` - Prompt specifications
- `TASK_BREAKDOWN.md` - Detailed implementation plan
- `JSON_SCHEMA_RUBRIC.md` - JSON schema validation rules

