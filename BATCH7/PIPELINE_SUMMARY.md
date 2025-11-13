# BATCH7 Pipeline Quick Reference

## Quick Start

```powershell
# 1. Set API key
$env:GEMINI_API_KEY="your-api-key-here"

# 2. Run full pipeline
python run_batch7_pipeline.py --process all
```

## Pipeline Overview

Three **parallel processing streams** operate independently:

| Stream | Input | Processing | Output |
|--------|-------|------------|--------|
| **1. NATIVES** | Excel files (`.xls`, `.xlsx`) | Structure analysis → Data extraction → Entity identification → Relationship mapping | `output/natives_analysis/*_analysis.json` |
| **2. IMAGES** | Image files (`.jpg`, `.tif`) | OCR → Visual description → Structured extraction → Context analysis | `*.json` (saved alongside images) |
| **3. TEXT** | Text files (`.txt`) | Content extraction → Context understanding → LLM grouping → Story assembly | `output/text_analysis/letters/S0001/` |

## Common Commands

```powershell
# Process everything
python run_batch7_pipeline.py --process all

# Process individual streams
python run_batch7_pipeline.py --process natives
python run_batch7_pipeline.py --process images
python run_batch7_pipeline.py --process text

# Resume interrupted processing
python run_batch7_pipeline.py --process all --skip-existing

# Translate assembled letters
python translate_letters.py --letters-dir "BATCH7/output/text_analysis/letters" --latex
```

## Directory Structure

```
BATCH7/
├── NATIVES/          # Input: Excel files
├── IMAGES/           # Input: Image files
├── TEXT/             # Input: Text files
└── output/
    ├── natives_analysis/    # Excel analysis JSON
    ├── images_analysis/     # (not used - JSON saved with images)
    └── text_analysis/
        └── letters/         # Assembled stories
            ├── S0001/
            │   ├── meta.json
            │   ├── text.txt
            │   ├── en.txt      # (after translation)
            │   └── en.tex      # (after translation --latex)
            └── S0002/
```

## LLM Model

- **Model:** Gemini 2.5 Pro Flash
- **Usage:** One API call per file/image
- **Cost:** Pay-per-use API pricing

## Documentation

- **`PIPELINE_WALKTHROUGH.md`** - Comprehensive guide with detailed explanations
- **`PIPELINE_DIAGRAM.tex`** - Visual TikZ diagram of the architecture
- **`COMPILE_DIAGRAM.md`** - Instructions for compiling the diagram
- **`README.md`** - Project overview
- **`QUICKSTART.md`** - Quick reference guide

## Visual Diagram

See `PIPELINE_DIAGRAM.tex` for a stylish TikZ diagram showing:
- Input sources → Processing stages → Output files
- LLM interactions (dashed orange arrows)
- Color-coded stream backgrounds
- Complete workflow visualization

Compile with: `pdflatex PIPELINE_DIAGRAM.tex`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `GEMINI_API_KEY not set` | Set environment variable or create `.env` file |
| Missing dependencies | Run `pip install -r requirements.txt` |
| Directory not found | Check paths or create missing directories |
| JSON parsing errors | Check console output, re-run with `--skip-existing` |

## Workflow Examples

### First-Time Run
```powershell
$env:GEMINI_API_KEY="your-key"
python run_batch7_pipeline.py --process all
```

### Process Only New Images
```powershell
python run_batch7_pipeline.py --process images --skip-existing
```

### Text Processing + Translation
```powershell
python run_batch7_pipeline.py --process text
python translate_letters.py --letters-dir "BATCH7/output/text_analysis/letters" --latex
```

## Key Features

- **Parallel Processing** - Three independent streams
- **Provenance Tracking** - Source files tracked in all outputs
- **Resume Capability** - `--skip-existing` flag
- **Structured Output** - JSON format for downstream analysis
- **LLM-Powered** - Gemini 2.5 Pro Flash for intelligent extraction
- **Optional Translation** - Translate assembled letters to English/LaTeX

