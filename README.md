# Dorle's Stories: AI-Powered Historical Letter Digitization

A sophisticated multi-phase pipeline for digitizing, translating, and analyzing historical German handwritten letters using Google Gemini AI.

## Overview

This project transforms handwritten German letters into accessible English translations with comprehensive historical analysis. It employs a 6-phase processing pipeline that combines OCR, translation, socio-historical analysis, and academic formatting.

## Processing Pipeline

The `ImageTranslator.py` script orchestrates a comprehensive 6-phase workflow:

### Input → Output Flow

**INPUT:**
- **Source:** `input/` folder
- **Files:** All `.jpeg`, `.jpg`, or `.png` files
- **Processing order:** Sorted numerically (extracts numbers from filename)

**OUTPUTS (6 phases):**

1. **Phase 1 - OCR:** Each image → individual German text file
   - `input/image.jpeg` → `german_output/image_german.txt`
   - Temperature: 0.4 (optimized for accuracy)

2. **Phase 2 - Translation:** ALL German texts combined → single English file
   - All `german_output/*_german.txt` → `english_output/combined_english_translation.txt`
   - Also saves: `combined_german_letter.txt` (root folder)
   - Temperature: 0.8 (balanced for fluency)

3. **Phase 3 - Analysis:** Combined English → narrative analysis
   - `english_output/combined_english_translation.txt` → `narrative_analysis_of_letters.txt` (root folder)
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
├── analysis_output/        # Historical analysis outputs
├── characters/            # Character intelligence profiles (future)
├── ImageTranslator.py     # Main 6-phase pipeline
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
