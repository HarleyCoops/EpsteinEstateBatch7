# Dorle's Stories: Bringing Handwritten History to Life

Welcome to **Dorle's Stories**, a project dedicated to preserving and understanding a collection of handwritten German letters from the past. Using the power of AI, we transform these precious documents into accessible English translations, uncover the narratives they hold, and even prepare them for formal presentation.

This project is more than just translation; it's about connecting with personal histories and gaining a glimpse into the daily lives, thoughts, and experiences of individuals from a different era.

## The Journey of a Letter

Our process, orchestrated by the `ImageTranslator.py` script, takes each letter on a fascinating journey:

1.  **From Image to Text:** We start with a scanned image of a handwritten German letter.
2.  **AI-Powered OCR:** A Generative AI model carefully "reads" the handwriting and extracts the original German text.
3.  **German to English Translation:** The extracted German text is then translated into English by the AI, making the content accessible.
4.  **Deep Narrative Analysis:** The combined English translations are analyzed by AI to produce a rich, PhD-level socio-historical understanding of the letters' content, characters, and context.
5.  **LaTeX Formatting:** Finally, both the original German text and the English translations are converted into formal LaTeX documents, ready for elegant presentation or archiving. Each segment within the documents is marked with its source filename for easy traceability.

## Translation Demo: A Glimpse into the Letters

The original letter images can be viewed in this Google Drive folder: [View Original Letter Scans](https://drive.google.com/drive/folders/1cENU2bUHmNftyPIvsNaEoNaGSY0HfxZS?usp=sharing)

Let's take a look at an example from one of the first letters in the collection, `IMG_3762.jpg`:

**Original Image (IMG_3762.jpg):**
*(A handwritten letter, likely on aged paper. You can view the actual image via the Google Drive link above.)*

**English Translation:**
```text
Hofheim, November 22nd

Dear Mech!

Many thanks for your
letter. When are you finally going to send me
the pictures from
Säntis? I've been waiting
half a year for them already. Can you
write me your Christmas wishes?
Preferably before the
1st of Advent. Because I'll be doing
a big shopping trip in Frankfurt
then. What are you all giving
the various rela-
tives? Are Liesel and Mr.
Geser gone already? Where are they actual-
```

This snippet offers a small window into the correspondence, mentioning everyday concerns, upcoming events like Christmas shopping, and questions about mutual acquaintances.

## Project Components

*   **`input/`**: This directory is where you place the scanned images of the handwritten letters (e.g., `.jpg`, `.png`).
*   **`german_output/`**: Contains the extracted German text from each image, saved as individual `.txt` files.
*   **`english_output/`**: Contains `combined_english_translation.txt`, which holds all the English translations concatenated together.
*   **`combined_german_letter.txt`**: A single text file containing the concatenated content from all extracted German letters.
*   **`narrative_analysis_of_letters.txt`**: An AI-generated socio-historical analysis of the combined letters.
*   **`combined_german_letter.tex`**: A LaTeX document of the combined German letters, with source traceability.
*   **`combined_english_letter.tex`**: A LaTeX document of the combined English translations, with source traceability.
*   **`ImageTranslator.py`**: The main Python script that orchestrates the entire workflow.
*   **`requirements.txt`**: Lists the necessary Python packages to run the script.
*   **`GOOGLEDRIVELINK.txt`**: Contains the link to the Google Drive folder with original images.

## How to Run

1.  Ensure you have Python installed.
2.  Set up your Google Gemini API Key as an environment variable (e.g., `GEMINI_API_KEY`).
3.  Place your letter images into the `input/` directory.
4.  Install the required packages: `pip install -r requirements.txt`
5.  Run the script: `python ImageTranslator.py`

The script will process the images and generate the various output files.

---

This README aims to provide a clear and engaging overview of the Dorle's Stories project. We hope it inspires an appreciation for the personal histories held within these letters! 