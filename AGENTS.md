# Repository Guidelines

## Project Structure & Module Organization
- Root: pipeline entry points and tools (`run_letters_pipeline.py`, `build_pdfs.py`, `llm_group_letters.py`, `translate_letters.py`).
- `helperPython/`: reusable modules (`grouping.py`, pipelines, translators) and light tests (`test_*.py`).
- `Chinese/`: Chinese-specific workflow and compiler (`compile_chinese_texts.py`).
- `DorleLetters*/` and `input/`: source images and generated outputs; outputs appear under `letters/` inside each collection.
- `codex/`: logs and generated markdown snippets from prior experiments.

## Build, Test, and Development Commands
- Install deps: `pip install -r requirements.txt`.
- Set API key (PowerShell): `$env:GEMINI_API_KEY="..."` or use `.env` with `GEMINI_API_KEY=...`.
- Run full pipeline: `python run_letters_pipeline.py --base DorleLettersF`.
- Re-translate only: `python translate_letters.py --base DorleLettersF --force-translate`.
- Build PDFs: `python build_pdfs.py --glob "DorleLetters[A-M]" --engine xelatex`.
- Tests (from repo root): `pytest -q` (discovers `helperPython/test_*.py`).

## Coding Style & Naming Conventions
- Python 3.10+, PEP 8, 4-space indentation.
- Names: modules/files `snake_case.py`; constants `UPPER_CASE`; functions `snake_case`; classes `CamelCase`.
- Docstrings for public functions. Prefer clear, small functions over large scripts.
- Type hints encouraged where practical; keep imports standard-library first.

## Testing Guidelines
- Framework: `pytest`. Place tests near code (`helperPython/test_*.py`).
- Name tests `test_<unit>.py`; target pure helpers (e.g., `grouping.py`) with deterministic cases.
- Run locally with `pytest -q`; add minimal fixtures for I/O-heavy logic.

## Commit & Pull Request Guidelines
- Commits: prefer Conventional Commits (e.g., `feat:`, `fix:`, `docs:`, `chore:`). Keep messages imperative and scoped.
- PRs: include a concise summary, steps to reproduce/verify, linked issues, and sample commands (e.g., pipeline invocation). Add before/after screenshots for output changes when applicable.
- Do not commit secrets or large binary outputs; respect `.gitignore`.

## Security & Configuration Tips
- Secrets: use `.env` (loaded via `python-dotenv`). Never hardcode keys.
- Reproducibility: record exact command lines and `--base` folder in PR descriptions.
- Large data: store raw images in `DorleLetters*/` and let the pipeline generate `letters/` outputs.

