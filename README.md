# Epstein Estate Batch 7: House Oversight Committee Documents

## LIVE: Auto-Processing and Publishing

**This repository is processing itself and publishing findings in real-time.**

As House Oversight Committee documents are analyzed, images are processed, text is extracted, and connections are revealed. The system automatically commits and publishes updates every 5 minutes with detailed summaries of the latest findings.

**Last Update:** {LAST_GIT_COMMIT_TIME}  
**Update Frequency:** Every 5 minutes  
**Status:** Processing continues as long as API credits are available

### Latest Context Update

**Latest Image Analysis:**
- TRUMP MENTIONS DETECTED in newly processed images
- Key characters identified: Epstein identified in HOUSE_OVERSIGHT_010597.json, Mr. Epstein identified in HOUSE_OVERSIGHT_010595.json, Epstein identified in HOUSE_OVERSIGHT_010596.json
- 10 new image analysis files processed

**Latest Text Processing:**
- 10 new text extraction files processed


---

## **CLICK INTO THE BATCH7 FOLDER TO SEE ALL IMAGES AND EMAILS AS THEY ARE UPLOADED**

All processed documents, images, extracted text, and analysis files are available in the [`BATCH7/`](./BATCH7/) directory.

---

## How This Works

### Automated Document Processing Pipeline

This repository contains an automated system that processes thousands of House Oversight Committee documents using AI-powered analysis. The system runs **two parallel processing streams** simultaneously:

#### Part 1: Image Analysis & Character Building

**All images are being individually analyzed by Gemini 2.5 Pro** with:
- **OCR Text Extraction** - Full text extraction from every image
- **Character Building** - For each person identified: "Who is this person? Where else do they appear?"
- **Visual Analysis** - Document type classification, layout analysis, quality assessment
- **Structured Data Extraction** - Dates, names, organizations, document numbers, signatures

**Output:** JSON analysis files saved alongside each image in [`BATCH7/IMAGES/001/`](./BATCH7/IMAGES/001/)

These JSON files are machine-readable metadata (not great for human reading, but this is just the first step). Each image gets its own `.json` file with complete analysis. You can see example JSON files in [`BATCH7/IMAGES/001/`](./BATCH7/IMAGES/001/) - look for files ending in `.json`.

#### Part 2: Text Document Processing

**Two major text volumes** are being processed:

1. **Volume 1: 2,905 documents** in [`BATCH7/TEXT/001/`](./BATCH7/TEXT/001/)
   - Each document is analyzed with OCR, text extraction, and character dossier assembly
   - Extraction JSON files are saved back to this folder alongside each text file
   - Content extraction, entity identification, context understanding
   - Documents are grouped into coherent narratives/stories

2. **Volume 2: Additional text documents** in [`BATCH7/TEXT/002/`](./BATCH7/TEXT/002/)
   - Similar processing pipeline

**Output:** 
- Per-file extraction JSON files saved alongside text files
- Assembled stories/narratives in [`BATCH7/output/text_analysis/letters/`](./BATCH7/output/text_analysis/letters/)

#### Processing Timeline

- **Live Processing:** Files are processed as they are released by the House Oversight Committee
- **Update Frequency:** All changes are automatically committed and published every 5 minutes
- **Overnight Processing:** The system runs continuously through the night
- **Expected Completion:** By Friday morning, all files should be fully processed
- **Continuous Publishing:** Results publish automatically throughout the night

### Real-Time Publishing

Every 5 minutes, the system:

- Analyzes new and modified files
- Extracts key findings (people, dates, relationships, notable documents)
- Highlights mentions of key figures (especially Trump and other central characters)
- Generates detailed commit messages summarizing discoveries
- Automatically commits and pushes updates to this public repository

### Live Summary Feed

The main README in [`BATCH7/README.md`](./BATCH7/README.md) acts like a **sports board news ticker**, updating every 5 minutes with:

- Latest processing status
- Key findings and discoveries
- Notable documents identified
- Character mentions and connections
- Summary statistics

Check the commit history to see the live feed of discoveries as they happen.

---

## What's Being Processed

### Document Types & Locations

- **Images** (`BATCH7/IMAGES/001/`) - Photographs, scanned documents, handwritten notes
  - Each image has a corresponding `.json` file with complete analysis
  - See example: [`BATCH7/IMAGES/001/HOUSE_OVERSIGHT_010477.json`](./BATCH7/IMAGES/001/HOUSE_OVERSIGHT_010477.json)
  
- **Text Files** (`BATCH7/TEXT/001/`) - 2,905 documents including emails, transcripts, conversations, memos
  - Volume 1: 2,905 documents being processed
  - Each document gets an extraction JSON file saved back to the folder
  
- **Excel Files** (`BATCH7/NATIVES/`) - Spreadsheets, data tables, financial records (when processed)

### Output Files

All analysis results are saved as JSON files alongside the original documents:

- **Image Analysis JSON** (`BATCH7/IMAGES/001/*.json`) - OCR text, identified people, character profiles, document types, structured data
  - These files are machine-readable metadata (first processing step)
  - Each image gets comprehensive analysis saved as JSON
  
- **Text Extraction JSON** (`BATCH7/TEXT/001/*_extraction.json`) - Extracted content, entities, themes, document structure
  - Saved alongside each text file
  
- **Assembled Stories** (`BATCH7/output/text_analysis/letters/`) - Grouped narratives and coherent story assemblies

---

## Technical Details

### Processing Technology

- **AI Model:** Google Gemini 2.5 Pro (for image analysis and character building)
- **Processing Method:** LLM-powered extraction and analysis
- **Output Format:** Structured JSON with full provenance tracking
- **Update Mechanism:** Automated git commits via scheduled webhook

### Key Features

- **No Modifications** - All original files are preserved unchanged
- **Full Provenance** - Every output includes source file references
- **Structured Data** - Machine-readable JSON for analysis and relationship mapping
- **Public Access** - All files and outputs are publicly available

---

## Repository Structure

```
EpsteinEstateBatch7/
├── BATCH7/                    ← CLICK HERE FOR ALL DOCUMENTS
│   ├── IMAGES/               ← Processed images with JSON analysis
│   ├── TEXT/                 ← Extracted text and assembled narratives
│   ├── NATIVES/              ← Excel/spreadsheet analysis
│   └── output/               ← Processed results and assembled stories
└── README.md                 ← This file
```

---

## Important Notes

### Processing Status

- **Dual Processing:** Images and text are being processed **in parallel** simultaneously
- **Continuous Operation:** Processing runs continuously through the night and day
- **Volume 1:** 2,905 text documents being analyzed (each saved back to `BATCH7/TEXT/001/`)
- **Image Processing:** All images in `BATCH7/IMAGES/001/` being analyzed with OCR and character building
- **Auto-Publishing:** Updates commit and publish every 5 minutes automatically
- **Expected Completion:** By Friday morning, all files should be fully processed
- **Live Updates:** Results publish throughout the night as processing continues

### Data Integrity

- All original documents are **preserved unchanged**
- Analysis files are **additive only** (JSON metadata alongside originals)
- Full **provenance tracking** in all outputs
- **Public repository** - everything is transparent and verifiable

### For Press/Media

This repository demonstrates:

- Automated document analysis at scale
- Real-time transparency in government document processing
- AI-powered extraction of key information from large document sets
- Public access to both raw documents and processed analysis

All commits are timestamped and include detailed summaries of findings. The commit history serves as a live log of discoveries.

---

## Contact

For questions about this repository or the processing pipeline, see the technical documentation in [`BATCH7/README.md`](./BATCH7/README.md).

---

**Last Updated:** {LAST_GIT_COMMIT_TIME}  
**Next Update:** Within 5 minutes  
**Processing Status:** Active

