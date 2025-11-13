# Compiling the Pipeline Diagram

The pipeline diagram is created using TikZ and LaTeX. Here's how to compile it:

## Prerequisites

You need a LaTeX distribution installed:

- **Windows:** [MiKTeX](https://miktex.org/) or [TeX Live](https://www.tug.org/texlive/)
- **macOS:** [MacTeX](https://www.tug.org/mactex/)
- **Linux:** `sudo apt-get install texlive-latex-base texlive-latex-extra` (or equivalent)

## Compilation Methods

### Method 1: Command Line (pdflatex)

```powershell
cd BATCH7
pdflatex PIPELINE_DIAGRAM.tex
```

This creates `PIPELINE_DIAGRAM.pdf`.

### Method 2: Online LaTeX Compiler

1. Go to [Overleaf](https://www.overleaf.com/) or [LaTeX Base](https://latexbase.com/)
2. Create a new project
3. Copy the contents of `PIPELINE_DIAGRAM.tex`
4. Compile to PDF

### Method 3: VS Code with LaTeX Workshop Extension

1. Install the "LaTeX Workshop" extension in VS Code
2. Open `PIPELINE_DIAGRAM.tex`
3. Press `Ctrl+Alt+B` (or `Cmd+Alt+B` on Mac) to build
4. Press `Ctrl+Alt+V` (or `Cmd+Alt+V` on Mac) to view PDF

## Output

The compiled PDF will show:
- Three parallel processing streams (NATIVES, IMAGES, TEXT)
- Input sources on the left
- Processing stages in the middle
- LLM interactions (dashed orange arrows)
- Output files on the right
- Color-coded stream backgrounds
- Legend explaining all components

## Troubleshooting

### Missing TikZ Libraries
If you get errors about missing libraries, install:
```powershell
# For MiKTeX (Windows)
mpm --install=pgf

# For TeX Live
tlmgr install pgf
```

### Font Issues
The diagram uses standard fonts. If you see font warnings, they can be ignored.

### Compilation Errors
Make sure you have:
- `tikz` package
- `standalone` document class
- All required TikZ libraries (shapes, arrows, positioning, etc.)

Most LaTeX distributions include these by default.

