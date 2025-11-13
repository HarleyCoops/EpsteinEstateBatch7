# Repository Guidelines

## Project Structure & Module Organization
- Root holds pipeline entry points like un_letters_pipeline.py, uild_pdfs.py, 	ranslate_letters.py.
- helperPython/ stores reusable modules (grouping.py, translator helpers) and targeted tests (	est_*.py).
- Chinese/ hosts Chinese compilation workflow via compile_chinese_texts.py.
- DorleLetters*/ directories contain scanned inputs and generated letters/ outputs; input/ mirrors raw assets for experiments.
- codex/ captures logs and markdown notes from automation runs.

## Build, Test, and Development Commands
- pip install -r requirements.txt installs notebooks, pipeline, and PDF tooling dependencies.
- python run_letters_pipeline.py --base DorleLettersF performs the end-to-end translation and layout pass for a collection.
- python translate_letters.py --base DorleLettersF --force-translate re-runs the LLM translation stage.
- python build_pdfs.py --glob "DorleLetters[A-M]" --engine xelatex composes printable PDFs for matching collections.
- pytest -q executes repository tests in helperPython/.

## Coding Style & Naming Conventions
- Target Python 3.10+, PEP 8 formatting, 4-space indentation, and snake_case module/function names; constants stay in UPPER_CASE.
- Public helpers should expose docstrings and type hints where useful; break large scripts into composable functions.
- Keep imports grouped: stdlib, third-party, then local modules; avoid unused dependencies.

## Testing Guidelines
- Tests live alongside helpers in helperPython/test_*.py; follow 	est_<unit>.py naming and deterministic fixtures.
- Run pytest -q before pushing; extend coverage when adding translator utilities or grouping logic.
- For pipeline changes, consider temporary smoke runs with python run_letters_pipeline.py --base <collection>.

## Commit & Pull Request Guidelines
- Use Conventional Commit prefixes (eat:, ix:, docs:) and keep messages imperative and scoped.
- PRs should summarize intent, note reproduction commands, link issues, and attach before/after assets (e.g., new letters/ outputs) when relevant.
- Document the exact --base collection and command flags used during validation.

## Security & Configuration Tips
- Never commit API keys; load GEMINI_API_KEY via .env or shell environment.
- Record new dependencies in equirements.txt and mention any external tools in the PR description.
- Large binaries stay out of Git—store source scans under DorleLetters*/ and regenerate outputs through the pipeline.
