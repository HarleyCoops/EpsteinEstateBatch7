# Chinese Text Compilation System

## Overview
This system compiles individual Chinese text transcriptions and their English translations into organized, formatted documents suitable for various uses including LaTeX typesetting and Google Docs.

## System Components

### 1. Directory Structure
```
Chinese/
├── IMG_*.jpeg                    # Original image files
├── chinese_output/               # Individual Chinese transcriptions
│   └── IMG_*_chinese.txt
├── english_output/               # Individual English translations
│   └── IMG_*_english.txt
├── letters/                      # Organized letter folders
│   └── L0001/
│       ├── zh.txt               # Chinese text
│       ├── zh.tex               # Chinese LaTeX
│       ├── en.txt               # English text
│       ├── en.tex               # English LaTeX
│       └── meta.json            # Metadata
├── compileinstructions.txt       # Compilation instructions
├── compile_chinese_texts.py      # Main compilation script
└── [Generated Files]
    ├── combined_chinese_text.txt
    ├── combined_chinese_text.tex
    ├── combined_english_translation.txt
    ├── combined_english_letter.tex
    └── combined_english_for_google_docs.md
```

### 2. Compilation Script Features

The `compile_chinese_texts.py` script provides:

- **Automatic File Sorting**: Files are sorted by image number (IMG_6260, IMG_6261, etc.)
- **Source Tracking**: Each section includes source file references
- **Multiple Output Formats**:
  - Plain text (.txt) for easy reading
  - LaTeX (.tex) for professional typesetting
  - Markdown (.md) for Google Docs and web viewing
- **Letter Organization**: Groups related texts into letter folders
- **Metadata Generation**: Creates JSON metadata for tracking and organization
- **UTF-8 Support**: Full support for Chinese characters

### 3. Running the Compilation

To compile all texts:
```bash
cd Chinese
python compile_chinese_texts.py
```

### 4. Output Files

#### Combined Text Files
- `combined_chinese_text.txt` - All Chinese texts in order
- `combined_english_translation.txt` - All English translations in order

#### LaTeX Documents
- `combined_chinese_text.tex` - Chinese LaTeX document with proper CJK support
- `combined_english_letter.tex` - English LaTeX document

#### Markdown for Google Docs
- `combined_english_for_google_docs.md` - Formatted for easy import to Google Docs

### 5. LaTeX Compilation

To compile the LaTeX documents to PDF:

For Chinese document (requires XeLaTeX):
```bash
xelatex combined_chinese_text.tex
```

For English document:
```bash
pdflatex combined_english_letter.tex
```

### 6. Adding New Texts

To add new texts to the compilation:

1. Place the image file in the main Chinese directory (e.g., `IMG_6279.jpeg`)
2. Add the Chinese transcription to `chinese_output/IMG_6279_chinese.txt`
3. Add the English translation to `english_output/IMG_6279_english.txt`
4. Run the compilation script

### 7. Customization

The script can be customized by modifying:
- Page break markers (currently "="*80)
- LaTeX templates in the `create_latex_document` method
- Markdown formatting in the `create_markdown_version` method
- File naming patterns in the `get_sorted_files` method

### 8. Requirements

- Python 3.6+
- Standard library modules: os, re, json, pathlib, datetime, typing
- For LaTeX compilation:
  - XeLaTeX (for Chinese documents)
  - pdfLaTeX (for English documents)
  - CJK fonts (SimSun or similar for Chinese)

### 9. Troubleshooting

**Issue**: Chinese characters not displaying in LaTeX
- **Solution**: Ensure XeLaTeX is installed and use appropriate CJK fonts

**Issue**: Files not being found
- **Solution**: Check file naming convention (IMG_[number]_chinese.txt or IMG_[number]_english.txt)

**Issue**: Sorting incorrect
- **Solution**: Ensure image numbers are consistent (e.g., IMG_6260, not IMG_260)

### 10. Future Enhancements

Potential improvements:
- Automatic PDF generation
- Web interface for viewing compiled documents
- Integration with OCR for automatic transcription
- Version control for tracking changes
- Batch processing for multiple document sets
- Export to additional formats (DOCX, EPUB, etc.)

## Contact

For questions or issues with the compilation system, please refer to the main project documentation or contact the project maintainer.
