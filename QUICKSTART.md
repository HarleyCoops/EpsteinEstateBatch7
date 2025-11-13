# BATCH7 Pipeline Quick Start

## Setup

1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Set API key:**
   ```powershell
   $env:GEMINI_API_KEY="your-api-key-here"
   ```
   Or add to `.env` file in project root:
   ```
   GEMINI_API_KEY=your-api-key-here
   ```

## Run Pipeline

From the `BATCH7` directory:

```powershell
# Process everything
python run_batch7_pipeline.py --process all

# Or process individually
python run_batch7_pipeline.py --process natives
python run_batch7_pipeline.py --process images
python run_batch7_pipeline.py --process text
```

## What Gets Processed

- **NATIVES/**: Excel files (`.xls`, `.xlsx`) → JSON analysis files
- **IMAGES/**: Image files (`.jpg`, `.tif`, etc.) → JSON files saved alongside images
- **TEXT/**: Text files (`.txt`) → Extracted content + assembled stories in `letters/` folder

## Output Locations

- Excel analysis: `BATCH7/output/natives_analysis/*_analysis.json`
- Image JSON: Saved next to each image (same folder, `.json` extension)
- Text stories: `BATCH7/output/text_analysis/letters/S0001/`, `S0002/`, etc.

## Resume Processing

Use `--skip-existing` to resume interrupted processing:

```powershell
python run_batch7_pipeline.py --process all --skip-existing
```

## Testing on Small Batch

To test on a subset, you can temporarily move files or use PowerShell filtering:

```powershell
# Process only one subdirectory
python run_batch7_pipeline.py --natives-dir "BATCH7/NATIVES/001" --process natives
```

## Notes

- Processing can take time for large batches (thousands of files)
- Each image/text file makes an API call to Gemini
- JSON outputs are designed for downstream relationship mapping
- See `PROMPT_DESIGN.md` for prompt details

