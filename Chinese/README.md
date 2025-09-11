Chinese Book Translation
========================

Overview
- This folder is for translating a single Chinese book/text into English.
- The pipeline treats the input as one continuous document, not a collection of letters.
- The translation prompt explicitly states this is not German and not related to Dorle.

Quick Start
- Put your Chinese text into `chinese/zh.txt` (UTF-8, paragraphs separated by blank lines).
- Ensure `GEMINI_API_KEY` is set in your environment or `.env`.
- Run:
  `python translate_chinese_book.py --input-file chinese/zh.txt --output-file chinese/en.txt --latex`

Notes
- The script automatically chunks long input by paragraph to fit model limits.
- It preserves paragraph breaks and does not add headings or commentary.
- Add `--force` to overwrite an existing `en.txt`.

