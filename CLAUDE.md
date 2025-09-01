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

- `ImageTranslator.py`: Main 6-phase processing pipeline with command-line arguments
- `culturalshifts.py`: Specialized cultural analysis focusing on post-war German shifts
- `config.yaml`: Central configuration for all settings (not currently used by main pipeline)
- `agent_monitor.py`: Character intelligence extraction (watches for new translations)
- `input/`: Source images directory (or custom via --output-base)
- `german_output/`: OCR results
- `english_output/`: Translations
- `analysis_output/`: Cultural analysis outputs
- `characters/`: Character profiles (JSON)

### Key Configuration (config.yaml)

- **Model**: `gemini-2.5-pro`
- **Thinking Budgets (Gemini 2.5 Pro)**:
  - OCR: thinking_budget 512, max_output_tokens 4096, temperature 0.4
  - Translation: thinking_budget 1024, max_output_tokens 8192, temperature 0.8
  - Analysis: thinking_budget -1 (dynamic), max_output_tokens 16384, temperature 0.75
  - LaTeX (EN/DE): thinking_budget 256, max_output_tokens 16384, temperature 0.2
  - Markdown (Google Docs): thinking_budget 128, max_output_tokens 8192, temperature 0.1
- **OCR Temperature**: 0.4 (accuracy)
- **Translation Temperature**: 0.8 (fluency)
- **Analysis Temperature**: 0.75 (nuanced)
- **Environment**: Requires `GEMINI_API_KEY` in `.env` or environment

### Development Commands

```bash
# Setup
pip install -r requirements.txt

# Run main pipeline (default directories)
python ImageTranslator.py

# Process specific letter collections
python ImageTranslator.py --output-base DorleLettersE
python ImageTranslator.py --output-base DorleLettersF
python ImageTranslator.py --output-base DorleLettersG

# Run cultural analysis (after translation)
python culturalshifts.py --output-base DorleLettersE

# Test character agent
python test_agent.py

# Download sample images
python download_test_images.py
```

### Processing Notes

- Files are processed in numeric order (IMG_3762, IMG_3763, etc.)
- Already processed files are skipped (resumable)
- Individual translations are done one-to-one (each German file → English file)
- Combined output files are created after individual processing for analysis phases
- Agent monitor runs independently to extract character data
- Cultural analysis requires completed English translation

### Important Patterns

- All Gemini API calls use streaming for large responses
- Error handling includes retry logic for API failures
- Output files use source filename as base (e.g., IMG_3762.jpg → IMG_3762_german.txt)
- Combined files aggregate all translations in order

---

## Research Query

can you explain the main pipleine of this code through the existing wrapper script? 

*Session: d7a3548c67ec94d00bbff0e1f1fe5a03 | Generated: 9/1/2025, 10:23:02 AM*

### Analysis Summary

# Codebase Pipeline Report

## High-Level Architecture

The codebase implements a pipeline for processing scanned German letters, involving Optical Character Recognition (OCR), LLM-driven grouping of pages into letters, and subsequent translation into English. The entire workflow is orchestrated by a central wrapper script, [run_letters_pipeline.py](c:/Users/chris/DorleStories/run_letters_pipeline.py), which sequentially executes two main components: the **LLM Grouping and Assembly** module and the **Translation** module.

### Main Pipeline Orchestrator: [run_letters_pipeline.py](c:/Users/chris/DorleStories/run_letters_pipeline.py)

This script serves as the entry point for the entire letter processing pipeline. It handles argument parsing, environment setup (loading `.env` for API keys), and sequentially calls the core processing scripts.

*   **Purpose**: To provide a unified command-line interface for running the complete workflow from OCR to English translation.
*   **Internal Parts**:
    *   `main()` function: Coordinates the execution of the two main steps.
    *   `run()` function: A helper to execute shell commands using `subprocess.run`.
*   **External Relationships**:
    *   Calls [llm_group_letters.py](c:/Users/chris/DorleStories/llm_group_letters.py) for the first stage of processing.
    *   Calls [translate_letters.py](c:/Users/chris/DorleStories/translate_letters.py) for the second stage of processing.
    *   Interacts with the file system to manage input image directories, intermediate German OCR output, and final letter directories.

## Mid-Level Pipeline Stages

The pipeline is divided into two distinct stages, each managed by a dedicated Python script.

### Stage 1: LLM Grouping and Assembly ([llm_group_letters.py](c:/Users/chris/DorleStories/llm_group_letters.py))

This module is responsible for converting image scans into German text, grouping these pages into logical letters using an LLM, and assembling the German text for each letter.

*   **Purpose**: To process raw image files (or pre-existing German OCR text) and organize them into coherent German letters based on content, leveraging a large language model.
*   **Internal Parts**:
    *   `main()` function: Orchestrates the OCR, page listing, LLM call, and assembly steps.
    *   `extract_german_text()`: Performs OCR on image files using the Gemini 2.5 Pro model ([llm_group_letters.py:100](c:/Users/chris/DorleStories/llm_group_letters.py:100)).
    *   `list_german_pages()`: Lists German OCR text files from a specified directory ([llm_group_letters.py:20](c:/Users/chris/DorleStories/llm_group_letters.py:20)).
    *   `build_input_listing()`: Formats the page data into a text listing for the LLM prompt ([llm_group_letters.py:80](c:/Users/chris/DorleStories/llm_group_letters.py:80)).
    *   `call_llm_grouping()`: Interacts with the Gemini 2.5 Pro model to perform the page grouping task ([llm_group_letters.py:125](c:/Users/chris/DorleStories/llm_group_letters.py:125)).
    *   `assemble_letters()`: Takes the LLM's JSON output and concatenates German page texts into `de.txt` files for each letter ([llm_group_letters.py:150](c:/Users/chris/DorleStories/llm_group_letters.py:150)).
*   **External Relationships**:
    *   Reads image files from an `--images-dir` (if OCR is enabled).
    *   Reads/writes German OCR text files (`_german.txt`) to/from a `--german-dir`.
    *   Communicates with the Google Gemini API for OCR and grouping tasks.
    *   Writes LLM grouping input (`llm_grouping_input.txt`) and output (`llm_grouping.json`) to the `--output-dir`.
    *   Creates letter-specific subdirectories within `--output-dir` (e.g., `L0001/`) and writes `de.txt` (German text) and `meta.json` (LLM provenance) files within them.

### Stage 2: Translation ([translate_letters.py](c:/Users/chris/DorleStories/translate_letters.py))

This module takes the assembled German letters and translates them into English, with an option to generate LaTeX output.

*   **Purpose**: To translate the grouped German letters into English using an LLM and optionally generate LaTeX documents.
*   **Internal Parts**:
    *   `main()` function: Iterates through letter directories, performs translation, and handles LaTeX generation.
    *   `list_letter_dirs()`: Identifies directories containing `de.txt` files, representing individual letters ([translate_letters.py:30](c:/Users/chris/DorleStories/translate_letters.py:30)).
    *   `translate_letter()`: Calls the Gemini 2.5 Pro model to translate German text to English ([translate_letters.py:70](c:/Users/chris/DorleStories/translate_letters.py:70)).
    *   `to_latex_document()`: Generates a basic LaTeX document from the English text ([translate_letters.py:50](c:/Users/chris/DorleStories/translate_letters.py:50)).
*   **External Relationships**:
    *   Reads German letter text from `de.txt` files within subdirectories of `--letters-dir`.
    *   Communicates with the Google Gemini API for translation tasks.
    *   Writes English translations to `en.txt` files within the respective letter directories.
    *   Optionally writes LaTeX files to `en.tex` within the respective letter directories.

