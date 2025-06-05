#!/usr/bin/env python3
"""
Combine raw text outputs into single German and English letters,
and generate a LaTeX Beamer presentation including the letters and input images.

Usage:
  python combine_letters_and_presentation.py

This script:
  - Reads all .txt files in german_output/ (sorted) and concatenates them into combined_german_letter.txt.
  - Reads all .txt files in english_output/ (sorted) and concatenates them into combined_english_letter.txt.
  - Generates presentation.tex (Beamer) that includes the German and English letters and one slide per input image.
"""
import os
import glob


def read_and_combine(dir_path):
    """Read all .txt files in dir_path (sorted) and return combined content."""
    paths = sorted(glob.glob(os.path.join(dir_path, '*.txt')))
    parts = []
    for p in paths:
        with open(p, encoding='utf-8') as f:
            text = f.read().strip()
        if text:
            parts.append(text)
    return '\n\n'.join(parts)


def write_file(path, content):
    """Write content to path."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def generate_presentation(german_text, english_text, image_dir, output_path):
    """Generate a Beamer presentation including letters and images."""
    images = sorted([f for f in os.listdir(image_dir)
                     if os.path.splitext(f)[1].lower() in {'.jpg', '.jpeg', '.png', '.pdf'}])

    lines = []
    lines.append(r'\documentclass{beamer}')
    lines.append(r'\usepackage[utf8]{inputenc}')
    lines.append(r'\usepackage{graphicx}')
    lines.append(r'\title{Handwritten Letters Presentation}')
    lines.append(r'\date{}')
    lines.append(r'\begin{document}')
    lines.append(r'\frame{\titlepage}')

    lines.append(r'\begin{frame}[fragile]{German Letter}')
    lines.append(r'\begin{verbatim}')
    lines.append(german_text)
    lines.append(r'\end{verbatim}')
    lines.append(r'\end{frame}')

    lines.append(r'\begin{frame}[fragile]{English Letter}')
    lines.append(r'\begin{verbatim}')
    lines.append(english_text)
    lines.append(r'\end{verbatim}')
    lines.append(r'\end{frame}')

    for img in images:
        lines.append(f'\\begin{{frame}}{{{img}}}')
        lines.append(r'\centering')
        lines.append(f'\\includegraphics[width=0.9\\linewidth]{{{os.path.join(image_dir, img)}}}')
        lines.append(r'\end{frame}')

    lines.append(r'\end{document}')
    write_file(output_path, '\n'.join(lines))


def main():
    german_text = read_and_combine('german_output')
    english_text = read_and_combine('english_output')

    write_file('combined_german_letter.txt', german_text)
    write_file('combined_english_letter.txt', english_text)

    generate_presentation(german_text, english_text, 'input', 'presentation.tex')
    print('Generated:')
    print('  combined_german_letter.txt')
    print('  combined_english_letter.txt')
    print('  presentation.tex')


if __name__ == '__main__':
    main()