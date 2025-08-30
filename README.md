# Dorle's Stories: AI-Powered Historical Letter Digitization

An academic-grade pipeline for reconstructing decades of family correspondence into bilingual, typeset documents. A strict mode is provided to avoid any narrative interpretation and to preserve exact provenance.

## Vision & Context

DorleStories is a digital humanities effort that turns fragile handwritten pages into a searchable corpus spanning generations. Beyond simple OCR, the goal is to produce coherent stories that can be read either in their original German or in a faithful English translation. Each step preserves provenance so historians can trace every sentence back to the source image.

## Processing Pipelines

Two entry points are available:

- LLM grouping (recommended): `llm_group_letters.py` — Uses Gemini 2.5 Pro to group pages into letters by contextual continuity from the German OCR. Produces grouping JSON and optional per-letter de.txt with no added markers.
- Strict heuristic (optional): `pipeline_strict.py` — OCR → heuristic grouping → LaTeX → optional translation. Deprecated for production grouping.

### Input → Output Flow

**INPUT:**
- **Source:** `input/` folder
- **Files:** All `.jpeg`, `.jpg`, or `.png` files
- **Processing order:** Sorted numerically (extracts numbers from filename)

### Strict Pipeline Outputs

Per letter (under `letters/` by default):
- `Lxxxx/meta.json`: Image list, timestamps, and paths.
- `Lxxxx/de.txt`: Concatenated German text with page markers.
- `Lxxxx/de.tex`: Deterministic LaTeX (German).
- `Lxxxx/en.txt`: English translation (if `--translate`).
- `Lxxxx/en.tex`: Deterministic LaTeX (English, if `--translate --latex`).

Grouping uses only EXIF/file timestamps and adjacent-page lexical similarity — no envelope or narrative inference.

### Legacy Pipeline Outputs (deprecated)

1. **Phase 1 - OCR:** Each image → individual German text file
   - `input/image.jpeg` → `german_output/image_german.txt`
   - Temperature: 0.4 (optimized for accuracy)

2. **Phase 2 - Translation:** ALL German texts combined → single English file
   - All `german_output/*_german.txt` → `english_output/combined_english_translation.txt`
   - Also saves: `combined_german_letter.txt` (root folder)
   - Temperature: 0.8 (balanced for fluency)

3. Narrative/analysis phases are deprecated in strict mode and disabled by default.
   - Temperature: 0.75 (nuanced interpretation)

4. **Phase 4 - English LaTeX:** Combined English → LaTeX document with source traceability
   - `english_output/combined_english_translation.txt` → `combined_english_letter.tex` (root folder)
   - Temperature: 0.2 (precise formatting)

5. **Phase 5 - German LaTeX:** Combined German → LaTeX document with source traceability
   - `combined_german_letter.txt` → `combined_german_letter.tex` (root folder)
   - Temperature: 0.2 (precise formatting)

6. **Phase 6 - Markdown:** Combined English → clean Markdown for Google Docs
   - `english_output/combined_english_translation.txt` → `combined_english_for_google_docs.md` (root folder)
   - Temperature: 0.1 (minimal alteration)

## Project Structure

```
DorleStories/
├── input/                  # Source images (JPEG handwritten letters)
├── german_output/          # OCR results (German text files)
├── english_output/         # Translation results
├── analysis_output/        # Cultural analysis outputs
├── characters/            # Character intelligence profiles (future)
├── ImageTranslator.py     # Main 6-phase pipeline (OCR → Translation → Analysis → LaTeX)
├── culturalshifts.py      # Cultural analysis focusing on post-war German shifts
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

### Recommended Workflow (LLM Grouping + Translation)

- Requirements: Python 3.10+, `pip install -r requirements.txt`, and environment variable `GEMINI_API_KEY`.
- Scope: Works on any image collection directory. Example uses `DorleLettersE/DorleLettersE`.

1) OCR (German) per page
- If you already have `german_output/<base>_german.txt` files, skip this step.
- With Gemini OCR in one pass during grouping:
  - PowerShell: `$env:GEMINI_API_KEY="YOUR_KEY"`
  - `python llm_group_letters.py --images-dir DorleLettersE/DorleLettersE --german-dir DorleLettersE/german_output --output-dir DorleLettersE/letters --run-ocr --save-input`

2) Group pages into letters via LLM (context-only)
- If OCR is done, assemble pure German letters with no added markers:
  - `python llm_group_letters.py --german-dir DorleLettersE/german_output --output-dir DorleLettersE/letters --save-input --assemble`
- Outputs:
  - `DorleLettersE/letters/llm_grouping_input.txt` — the exact input listing sent to the LLM.
  - `DorleLettersE/letters/llm_grouping.json` — strict JSON with letter groups, page order, confidence, reason.
  - `DorleLettersE/letters/L0001/de.txt`, `L0002/de.txt`, … — pure German letters (no inserted markers/headers).

3) Translate grouped letters to English
- Letter-by-letter, plain text only; optional LaTeX rendering:
  - `python translate_letters.py --letters-dir DorleLettersE/letters --latex`
- Outputs per letter:
  - `en.txt` — English translation
  - `en.tex` — deterministic LaTeX (no LLM formatting)

4) Optional: build PDFs from LaTeX
- Run your LaTeX toolchain in each `Lxxxx/` folder (e.g., `pdflatex en.tex`).

### Core Processing Scripts

**llm_group_letters.py** - Group pages into letters via LLM (no added text):
```bash
# 1) Ensure OCR exists (run ImageTranslator.py or your OCR step first)
# 2) Group via LLM and assemble letters (German only, no markers)
python llm_group_letters.py --german-dir german_output --output-dir letters --save-input --assemble
```

**translate_letters.py** - Translate LLM-grouped German letters to English (plain text + optional LaTeX):
```bash
python translate_letters.py --letters-dir letters --latex
```

**ImageTranslator.py** - Legacy 6-phase pipeline for OCR, translation, and document generation:
```bash
python ImageTranslator.py
python ImageTranslator.py --output-base DorleLettersE
python ImageTranslator.py --output-base DorleLettersF
python ImageTranslator.py --output-base DorleLettersG
```

### Additional Tools

```bash
# Process PDF files (for bulk documents)
python PDFTranslator.py
```

## Key Features

- **Resumable Processing**: Already processed files are automatically skipped
- **Ordered Processing**: Strict mode groups pages by capture time and lexical similarity
- **Source Traceability**: LaTeX documents include source filename for each segment
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

✅ Phase 1-6: Fully functional pipeline with German/English LaTeX generation
⚠️ Character intelligence agent: In development
📝 Config integration: Planned enhancement

## Research Roadmap

- **Letter aggregation**: detect and merge multi-page letters to preserve narrative flow across decades.
- **Bilingual typesetting**: parallel German/English LaTeX with cross-references and page provenance.
- **Narrative corpus building**: compile outputs into a chronological archive that enables long-term cultural or familial analysis.

## Codex CLI and MCP Translation Workflow (OpenAI)

This repository also includes an OpenAI-based translation path under `codex/` that converts each OCR’d German text into an English Markdown file, one-to-one. It is designed for local agent workflows (Codex CLI), optional MCP-style service integration, and a modern OpenAI Responses API fallback so batches complete reliably.

- Location: `codex/`
  - `translator.py` — orchestrates discovery and translation
  - `cli.py` — batch CLI entry point
  - `direct_openai.py` — modern OpenAI Python SDK v1.x client (Responses API; no legacy Completions)
  - `outputs/` — English Markdown (one file per input image base)
  - `translations.log` — audit log (timestamps, successes/skips)

### What the Codex CLI is
OpenAI Codex CLI is a local coding agent that can read/write files and propose or run commands with approval controls.
- Install: `npm install -g @openai/codex`
- Start: `codex` (Suggest mode by default)
- Approval modes:
  - Suggest: proposes edits/commands; you approve before execution
  - Auto Edit: edits files automatically; still asks before shell commands
  - Full Auto: reads/writes and executes commands autonomously in a sandbox
- Models: defaults to a fast reasoning model; you can select any Responses API model (e.g., `-m gpt-5`)
- Windows: experimental; WSL recommended

Refer to “OpenAI Codex CLI – Getting Started” and https://github.com/openai/codex for details.

### How MCP fits here
We support an optional, minimal HTTP contract that aligns with MCP-style tool exposure. The translator can send German text to a service that calls an LLM and returns Markdown.

- Expected endpoint: `POST {mcp-endpoint}/translate`
- Request JSON:
  ```json
  {
    "source_text": "<german text>",
    "format": "markdown",
    "mode": "german_to_english"
  }
  ```
- Response JSON:
  ```json
  { "translation": "<english markdown>" }
  ```

You can implement this behind a proper MCP server or a simple web service that calls the OpenAI Responses API. The translator prefers MCP when you pass `--use-mcp`.

### End-to-end file flow (Codex workflow)
1) Discover pairs
   - For each `input/<base>.(jpeg|jpg|png)`, locate `german_output/<base>_german.txt`.
2) Translate (preference order)
   - If `--use-mcp` provided: POST to `{mcp-endpoint}/translate` (your service calls the LLM and returns Markdown).
   - Else attempt Codex CLI (if installed) for a local agent call.
   - Fallback (default-enabled): call OpenAI Responses API directly via the modern Python SDK v1.x (`client.responses.create(...)`) with translation instructions and the German text as input.
3) Write outputs
   - Save to `codex/outputs/<base>.md`.
4) Log
   - Append to `codex/translations.log` with timestamps and success/skip counts.

### Where the LLM is actually called
- MCP path: inside your MCP-compatible service (or thin HTTP service) that receives the German text and calls the OpenAI model (e.g., `gpt-5` or `gpt-4.1`) via the Responses API, then returns Markdown.
- Codex CLI path: the `codex` agent runs locally; for batch translation we call it non-interactively if present.
- Fallback path (built-in): within `direct_openai.py`, using `OpenAI().responses.create(model=..., input=..., instructions=...)` (SDK v1.x). This avoids all legacy Completion/ChatCompletion calls.

### How to expose the MCP to other users
1) Implement a small web service (e.g., FastAPI) that exposes `/translate` and calls OpenAI’s Responses API under your organization’s policies.
2) Package & deploy (containerize, secure with TLS and auth).
3) Share the endpoint (e.g., `https://your-mcp.example.com`). Other users run:
   ```bash
   python -m codex.cli --input-dir input --german-dir german_output --output-dir codex/outputs --use-mcp --mcp-endpoint https://your-mcp.example.com
   ```
4) Optional advanced path: register a true remote MCP tool and integrate with agent frameworks that understand MCP, enabling richer multi-tool workflows.

### Running the Codex workflow locally
Environment:
- Set `OPENAI_API_KEY` (e.g., via `.env` in repo root)
- Optional: `CODEX_OPENAI_MODEL` (e.g., `gpt-5`, defaults to `gpt-4.1`)
- Optional: `--use-mcp --mcp-endpoint http://localhost:8000` if you host a service

Examples:
```bash
# Dry run (no writes)
python -m codex.cli --input-dir input --german-dir german_output --output-dir codex/outputs --dry-run

# Prefer MCP (if you have a service running)
python -m codex.cli --input-dir input --german-dir german_output --output-dir codex/outputs --use-mcp --mcp-endpoint http://localhost:8000

# Rely on built-in OpenAI Responses API fallback (no MCP, no Codex CLI)
python -m codex.cli --input-dir input --german-dir german_output --output-dir codex/outputs --verbose
```

Troubleshooting:
- “Failed to run Codex CLI wrapper: [WinError 2]”: Codex CLI is not installed or not on PATH; fallback will still translate via Responses API.
- “OPENAI_API_KEY not configured”: set it in your environment or `.env`.
- Windows: prefer WSL for Codex CLI agent usage.

## Deprecated/Disabled Components
- Narrative analysis (`narrative_analysis_of_letters.txt`) is deprecated for strict mode.
- Character/agent workflows are disabled by default. See `config.yaml` if needed.
