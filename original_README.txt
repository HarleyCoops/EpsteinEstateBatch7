# DorleStories

This project processes images and PDFs of handwritten German text and translates them to English using AI models. The system has evolved into a modular architecture with separate processors for different document types.

## Core Components

### ImageTranslator.py
Processes handwritten German document images through Gemini AI:
1. **OCR Extraction**: Uses Gemini vision model to extract German text from images
2. **Translation**: Translates extracted German text to English using Gemini text model

### PDFTranslator.py
Configurable processor for PDF documents (under development):
- Supports multiple OCR engines (Tesseract)
- Multiple translation providers (OpenAI GPT-4)
- YAML-based configuration system

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/HarleyCoops/DorleStories.git
cd DorleStories
```

### 2. Install Dependencies
Install the required Python packages:
```bash
pip install google-generativeai python-dotenv requests
```

For PDF processing and character intelligence features (optional):
```bash
pip install openai watchdog jsonschema
```

### 3. Set Up Environment Variables
Create a `.env` file in the project root with your API keys:
```bash
# Required for image processing
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: For character intelligence agent (PDF processor)
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Configure Processing (Optional)
The `config.yaml` file contains settings for the PDF processor and character intelligence agent. Default settings work out of the box, but you can customize:
- OCR and translation providers
- Character intelligence monitoring
- File processing options

### 5. Test with Sample Data
Download sample German handwritten documents:
```bash
python download_test_images.py
```

This will populate the `input/` directory with test images.

## Usage

### Image Processing
1. Place your input images (JPG, JPEG, PNG) into the `input` directory.
2. Run the image translator:
   ```bash
   python ImageTranslator.py
   ```
3. Results will be saved as text files:
   - `german_output/<image_name>_german.txt` contains the extracted German text
   - `english_output/<image_name>_english.txt` contains the English translation

### PDF Processing (Under Development)
The PDF processor supports configurable OCR and translation pipelines:
```bash
python PDFTranslator.py --config config.yaml
```

#### Character Intelligence Agent
When enabled in `config.yaml`, the system automatically:
- Monitors translated English files in real-time
- Extracts character information (names, relationships, locations, events)
- Builds per-character JSON profiles in the `characters/` directory
- Maintains persistent processing state for crash recovery

To enable/disable the agent, modify `config.yaml`:
```yaml
agent:
  enabled: true  # Set to false to disable
  model: "gpt-4"
  watch_path: "english_output"
  characters_path: "characters"
```

## Directory Structure

```
DorleStories/
├── input/            # Source images (JPG, JPEG, PNG)
├── german_output/    # Extracted German text (.txt files)
├── english_output/   # English translations (.txt files)
├── characters/       # Character intelligence JSON profiles (auto-created)
├── ImageTranslator.py # Main image processing script
├── PDFTranslator.py  # PDF processing script (configurable)
├── agent_monitor.py  # Character intelligence agent
├── config.yaml       # Configuration for PDF processor and agent
├── download_test_images.py # Test data utility
├── .env              # API keys
└── .env.example      # Environment template
```

## Configuration

### ImageTranslator
- Model: `gemini-2.5-pro-preview-05-06`
- OCR Temperature: 0.3 (for accuracy)
- Translation Temperature: 0.7 (balance of accuracy and fluency)
- Uses `.env` file for API key

### PDFTranslator
- YAML-based configuration in `config.yaml`
- Supports multiple OCR engines and translation providers
- Environment variables for API keys

## Processing Workflow

Files are processed independently and skipped if output already exists, allowing for resumable processing. The system maintains the original two-step workflow (OCR → Translation) while providing better organization through separate output directories.