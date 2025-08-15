# Implementation Plan: Migrate to Gemini 2.5 Pro + Per-Phase Thinking Budgets

This document summarizes the refactor to standardize on Gemini 2.5 Pro and introduce per-phase "thinking" budgets and output token ceilings across the pipeline.

## Summary of Changes

- Standardized model to gemini-2.5-pro:
  - ImageTranslator.py
  - combinedEnglish.py
  - test_single_extraction.py
- Introduced per-phase thinking budgets and max_output_tokens:
  - OCR: thinking_budget 512, max_output_tokens 4096, temp 0.4
  - Translation (per page): thinking_budget 1024, max_output_tokens 8192, temp 0.8
  - Analysis: thinking_budget -1 (dynamic), max_output_tokens 16384, temp 0.75
  - LaTeX (EN/DE): thinking_budget 256, max_output_tokens 16384, temp 0.2
  - Markdown (Google Docs): thinking_budget 128, max_output_tokens 8192, temp 0.1
  - Combined Translation (combinedEnglish.py): thinking_budget 1024, max_output_tokens 16384, temp 0.8
- Updated documentation:
  - CLAUDE.md to reflect new model and per-phase budgets.
- Aligned legacy config.yaml translation provider/model to Google/Gemini:
  - translation.provider: google
  - translation.model: gemini-2.5-pro

## Files Touched (with rationale)

- ImageTranslator.py
  - MODEL_NAME = "gemini-2.5-pro"
  - Each GenerateContentConfig now sets:
    - temperature per phase
    - max_output_tokens (ceiling for response length)
    - thinking_config=types.ThinkingConfig(thinking_budget=...) per phase
  - Streaming, retries, and prompts preserved

- combinedEnglish.py
  - MODEL_NAME = "gemini-2.5-pro"
  - GenerateContentConfig includes thinking_config and max_output_tokens tuned for long combined translation

- test_single_extraction.py
  - Model switched to gemini-2.5-pro
  - Added thinking_config(thinking_budget=512) for OCR-like extraction tests

- CLAUDE.md
  - Documented new model and standardized per-phase budgets

- config.yaml
  - translation.provider -> google
  - translation.model -> gemini-2.5-pro
  - Note: The current runtime does not yet consume config.yaml for LLM parameters. These settings are documented for future centralization.

## Reasoning Budget Notes (Gemini 2.5 Pro)

- 2.5 Pro supports thinking budgets with min 128 and max 32,768 tokens.
- thinking_budget = -1 enables dynamic thinking (model decides per prompt).
- For production, include_thoughts is not requested to avoid chain-of-thought exposure and cost overhead.
- For 2.5 Pro, thinking cannot be disabled (budget 0); Flash allows 0 to disable.

## Proposed Future Centralization (Optional Next Step)

Centralize LLM configuration in code (and optionally read from config.yaml):

- Add a helper (e.g., llm_config.py or local function) with a mapping:
  - phase -> { temperature, thinking_budget, max_output_tokens }
- Optionally load overrides from config.yaml:
  ```
  llm:
    provider: google
    model: gemini-2.5-pro
    defaults:
      include_thoughts: false
    phases:
      ocr:
        temperature: 0.35
        thinking_budget: 512
        max_output_tokens: 4096
      translation:
        temperature: 0.8
        thinking_budget: 1024
        max_output_tokens: 8192
      analysis:
        temperature: 0.75
        thinking_budget: -1
        max_output_tokens: 16384
      latex:
        temperature: 0.2
        thinking_budget: 256
        max_output_tokens: 16384
      markdown:
        temperature: 0.1
        thinking_budget: 128
        max_output_tokens: 8192
      combined_translation:
        temperature: 0.8
        thinking_budget: 1024
        max_output_tokens: 16384
  ```
- Build GenerateContentConfig per phase using the above.

## Testing Instructions

1. Ensure environment contains GEMINI_API_KEY.
2. Run the main pipeline:
   - python ImageTranslator.py
   - Verify generated outputs in german_output, english_output, and combined files.
   - Confirm LaTeX and Markdown phases complete with longer outputs within limits.
3. Combined translation test:
   - python combinedEnglish.py
   - Inspect translation_from_all_german_files.txt
4. Single extraction tester:
   - python test_single_extraction.py
   - Inspect test_output_*.txt artifacts.
5. Monitor output lengths and quality. If analysis is overly slow/verbose, consider fixing analysis thinking_budget to 4096–8192 for cost control.

## References

- Gemini thinking guide: https://ai.google.dev/gemini-api/docs/thinking
- Text generation examples: https://ai.google.dev/gemini-api/docs/text-generation
- Vertex AI thinking docs: https://cloud.google.com/vertex-ai/generative-ai/docs/thinking

## Known Gaps / Follow-ups

- Current runtime does not read per-phase config from config.yaml; implemented constants are in code. If desired, add a YAML loader and phase config resolver.
- agent_monitor.py continues to use OpenAI as previously documented (optional path per repo design).
- Optional: add logging of usage metadata (e.g., thoughts_token_count, output_token_count) if/when exposed in google-genai responses for cost observability.
- requirements.txt already includes google-genai. If using agent_monitor.py proactively, consider ensuring jsonschema and watchdog are installed.
