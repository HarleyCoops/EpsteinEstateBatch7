#!/usr/bin/env python3
"""
Chinese Text Compilation Script
Compiles individual Chinese text transcriptions and English translations
into organized, formatted documents.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

class ChineseTextCompiler:
    def __init__(self, base_dir: str = "."):
        """Initialize the compiler with the base directory."""
        self.base_dir = Path(base_dir)
        self.chinese_dir = self.base_dir / "chinese_output"
        self.english_dir = self.base_dir / "english_output"
        self.letters_dir = self.base_dir / "letters"
        
    def get_sorted_files(self, directory: Path, pattern: str) -> List[Path]:
        """Get sorted list of files matching pattern."""
        files = list(directory.glob(pattern))
        # Extract numbers from filenames for sorting
        def get_number(filepath):
            match = re.search(r'IMG_(\d+)', filepath.name)
            return int(match.group(1)) if match else 0
        return sorted(files, key=get_number)
    
    def read_file_content(self, filepath: Path) -> str:
        """Read content from a file with UTF-8 encoding."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return ""
    
    def write_file_content(self, filepath: Path, content: str):
        """Write content to a file with UTF-8 encoding."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created: {filepath}")
    
    def combine_chinese_texts(self) -> str:
        """Combine all Chinese text files into one document."""
        print("\n=== Combining Chinese Texts ===")
        chinese_files = self.get_sorted_files(self.chinese_dir, "IMG_*_chinese.txt")
        combined_content = []
        
        for i, filepath in enumerate(chinese_files):
            content = self.read_file_content(filepath)
            if content:
                # Add source reference
                combined_content.append(f"[Source: {filepath.name}]\n")
                combined_content.append(content)
                # Add page break between different sources
                if i < len(chinese_files) - 1:
                    combined_content.append("\n" + "="*80 + "\n\n")
        
        combined_text = "".join(combined_content)
        output_path = self.base_dir / "combined_chinese_text.txt"
        self.write_file_content(output_path, combined_text)
        return combined_text
    
    def combine_english_translations(self) -> str:
        """Combine all English translation files into one document."""
        print("\n=== Combining English Translations ===")
        english_files = self.get_sorted_files(self.english_dir, "IMG_*_english.txt")
        combined_content = []
        
        for i, filepath in enumerate(english_files):
            content = self.read_file_content(filepath)
            if content:
                # Add source reference
                combined_content.append(f"[Source: {filepath.name}]\n")
                combined_content.append(content)
                # Add page break between different sources
                if i < len(english_files) - 1:
                    combined_content.append("\n" + "="*80 + "\n\n")
        
        combined_text = "".join(combined_content)
        output_path = self.base_dir / "combined_english_translation.txt"
        self.write_file_content(output_path, combined_text)
        return combined_text
    
    def create_latex_document(self, content: str, title: str, language: str = "english") -> str:
        """Create a LaTeX document from the content."""
        if language == "chinese":
            latex_template = r"""\documentclass[12pt]{article}
\usepackage{xeCJK}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
\setCJKmainfont{SimSun}  % or another Chinese font available on your system

\title{""" + title + r"""}
\author{Compiled Document}
\date{\today}

\begin{document}
\maketitle

"""
        else:
            latex_template = r"""\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\geometry{a4paper, margin=1in}

\title{""" + title + r"""}
\author{Compiled Document}
\date{\today}

\begin{document}
\maketitle

"""
        
        # Escape special LaTeX characters
        content_escaped = content.replace('\\', r'\\')
        content_escaped = content_escaped.replace('&', r'\&')
        content_escaped = content_escaped.replace('%', r'\%')
        content_escaped = content_escaped.replace('$', r'\$')
        content_escaped = content_escaped.replace('#', r'\#')
        content_escaped = content_escaped.replace('_', r'\_')
        content_escaped = content_escaped.replace('{', r'\{')
        content_escaped = content_escaped.replace('}', r'\}')
        content_escaped = content_escaped.replace('~', r'\textasciitilde{}')
        content_escaped = content_escaped.replace('^', r'\textasciicircum{}')
        
        # Replace page breaks with LaTeX page breaks
        content_escaped = content_escaped.replace("="*80, r"\newpage")
        
        latex_content = latex_template + content_escaped + r"""

\end{document}"""
        
        return latex_content
    
    def generate_latex_documents(self, chinese_text: str, english_text: str):
        """Generate LaTeX versions of the combined texts."""
        print("\n=== Generating LaTeX Documents ===")
        
        # Chinese LaTeX
        chinese_latex = self.create_latex_document(
            chinese_text, 
            "Chinese Text Compilation",
            "chinese"
        )
        chinese_latex_path = self.base_dir / "combined_chinese_text.tex"
        self.write_file_content(chinese_latex_path, chinese_latex)
        
        # English LaTeX
        english_latex = self.create_latex_document(
            english_text,
            "English Translation Compilation",
            "english"
        )
        english_latex_path = self.base_dir / "combined_english_letter.tex"
        self.write_file_content(english_latex_path, english_latex)
    
    def create_markdown_version(self, english_text: str):
        """Create a Markdown version for Google Docs."""
        print("\n=== Creating Markdown Version ===")
        
        markdown_content = f"""# English Translation Compilation

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

---

"""
        
        # Convert the text to markdown format
        lines = english_text.split('\n')
        for line in lines:
            if line.startswith('[Source:'):
                markdown_content += f"\n## {line}\n\n"
            elif line == "="*80:
                markdown_content += "\n---\n\n"
            else:
                markdown_content += line + '\n'
        
        markdown_path = self.base_dir / "combined_english_for_google_docs.md"
        self.write_file_content(markdown_path, markdown_content)
    
    def organize_letters(self):
        """Organize texts into letter folders with metadata."""
        print("\n=== Organizing Letters ===")
        
        # Check if there are existing letter folders
        existing_letters = list(self.letters_dir.glob("L*"))
        
        if not existing_letters:
            print("No existing letter folders found. Creating L0001...")
            # Create first letter folder as example
            letter_dir = self.letters_dir / "L0001"
            letter_dir.mkdir(parents=True, exist_ok=True)
            
            # Get first Chinese and English files
            chinese_files = self.get_sorted_files(self.chinese_dir, "IMG_*_chinese.txt")
            english_files = self.get_sorted_files(self.english_dir, "IMG_*_english.txt")
            
            if chinese_files and english_files:
                # Use first file as example
                chinese_content = self.read_file_content(chinese_files[0])
                english_content = self.read_file_content(english_files[0])
                
                # Create text files
                self.write_file_content(letter_dir / "zh.txt", chinese_content)
                self.write_file_content(letter_dir / "en.txt", english_content)
                
                # Create LaTeX files
                chinese_latex = self.create_latex_document(
                    chinese_content, "Letter L0001 - Chinese", "chinese"
                )
                english_latex = self.create_latex_document(
                    english_content, "Letter L0001 - English", "english"
                )
                
                self.write_file_content(letter_dir / "zh.tex", chinese_latex)
                self.write_file_content(letter_dir / "en.tex", english_latex)
                
                # Create metadata
                metadata = {
                    "letter_id": "L0001",
                    "source_images": [chinese_files[0].name.replace("_chinese.txt", ".jpeg")],
                    "created": datetime.now().isoformat(),
                    "chinese_file": "zh.txt",
                    "english_file": "en.txt",
                    "status": "compiled"
                }
                
                self.write_file_content(
                    letter_dir / "meta.json",
                    json.dumps(metadata, indent=2, ensure_ascii=False)
                )
        else:
            print(f"Found {len(existing_letters)} existing letter folders.")
    
    def compile_all(self):
        """Run the complete compilation process."""
        print("="*80)
        print("Chinese Text Compilation Script")
        print("="*80)
        
        # Step 1: Combine Chinese texts
        chinese_text = self.combine_chinese_texts()
        
        # Step 2: Combine English translations
        english_text = self.combine_english_translations()
        
        # Step 3: Generate LaTeX documents
        self.generate_latex_documents(chinese_text, english_text)
        
        # Step 4: Organize into letters
        self.organize_letters()
        
        # Step 5: Create Markdown version
        self.create_markdown_version(english_text)
        
        print("\n" + "="*80)
        print("Compilation Complete!")
        print("="*80)
        print("\nGenerated files:")
        print("  - combined_chinese_text.txt")
        print("  - combined_english_translation.txt")
        print("  - combined_chinese_text.tex")
        print("  - combined_english_letter.tex")
        print("  - combined_english_for_google_docs.md")
        print("  - letters/ (organized letter structure)")


def main():
    """Main entry point for the script."""
    compiler = ChineseTextCompiler()
    compiler.compile_all()


if __name__ == "__main__":
    main()
