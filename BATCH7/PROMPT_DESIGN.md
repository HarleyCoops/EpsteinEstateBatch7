# BATCH7 Prompt Design Document

## Context
This pipeline processes House Oversight Committee documents related to official investigations. All prompts must prioritize:
- **Accuracy**: No hallucinations, only extract what is actually present
- **Provenance**: Track source files and page numbers
- **Structured Output**: JSON/structured formats for downstream analysis
- **Factual Extraction**: Focus on dates, names, relationships, events

---

## 1. NATIVES (Excel Spreadsheets)

### Goal
Understand spreadsheet structure, extract data, identify relationships, dates, characters, and build connection maps.

### Prompt Strategy
**Multi-stage approach:**
1. **Structure Analysis**: Understand what the spreadsheet represents
2. **Data Extraction**: Extract all tabular data with headers
3. **Relationship Mapping**: Identify connections between entities
4. **Context Understanding**: Determine the purpose/context of the spreadsheet

### Prompt Template
```
You are analyzing an Excel spreadsheet from House Oversight Committee documentation.

TASK: Analyze this spreadsheet comprehensively and extract all relevant information.

REQUIREMENTS:
1. STRUCTURE ANALYSIS:
   - Identify all worksheets/tabs
   - Describe the purpose and context of each worksheet
   - Note column headers and data types
   - Identify any formulas or calculated fields

2. DATA EXTRACTION:
   - Extract all tabular data preserving structure
   - Note any merged cells or special formatting
   - Identify date fields and normalize formats
   - Extract all names, organizations, locations mentioned

3. RELATIONSHIP MAPPING:
   - Identify connections between entities (people, organizations, dates, locations)
   - Note any hierarchies or groupings
   - Extract transaction amounts, quantities, or other numerical relationships
   - Identify patterns or sequences

4. CONTEXT UNDERSTANDING:
   - Determine what this spreadsheet documents (financial records, contacts, schedules, etc.)
   - Note any references to other documents or file numbers
   - Identify key dates and time periods covered

OUTPUT FORMAT (STRICT JSON):
{
  "file_name": "<filename>",
  "structure": {
    "worksheets": [
      {
        "name": "<sheet_name>",
        "purpose": "<description>",
        "row_count": <number>,
        "column_count": <number>,
        "headers": ["<col1>", "<col2>", ...]
      }
    ]
  },
  "data": {
    "<sheet_name>": [
      {
        "row_index": <number>,
        "data": { "<header>": "<value>", ... }
      }
    ]
  },
  "entities": {
    "people": ["<name1>", "<name2>", ...],
    "organizations": ["<org1>", ...],
    "locations": ["<loc1>", ...],
    "dates": ["<date1>", ...]
  },
  "relationships": [
    {
      "type": "<relationship_type>",
      "source": "<entity1>",
      "target": "<entity2>",
      "context": "<description>",
      "evidence": "<supporting_data>"
    }
  ],
  "context": {
    "document_type": "<type>",
    "time_period": "<start_date> to <end_date>",
    "key_themes": ["<theme1>", ...],
    "references": ["<file_number>", ...]
  },
  "confidence": 0.0-1.0,
  "notes": "<any_uncertainties_or_observations>"
}

CRITICAL RULES:
- Extract ONLY what is present in the spreadsheet
- Do not infer or assume relationships not explicitly shown
- Preserve exact text, dates, and numbers as they appear
- Note any ambiguities or unclear data
- If a field is empty, note it as null, not omit it
```

---

## 2. IMAGES

### Goal
Extract text/handwriting via OCR, describe images, and output comprehensive JSON with all extracted information.

### Prompt Strategy
**Multi-modal analysis:**
1. **OCR Extraction**: Extract all visible text (typed, handwritten, printed)
2. **Visual Description**: Describe the image content, layout, document type
3. **Structured Extraction**: Extract dates, names, document numbers, signatures
4. **Context Analysis**: Understand what type of document/image this is

### Prompt Template
```
You are analyzing an image from House Oversight Committee documentation.

TASK: Perform comprehensive analysis of this image and extract all information.

REQUIREMENTS:
1. TEXT EXTRACTION (OCR):
   - Extract ALL visible text exactly as it appears
   - Preserve line breaks and paragraph structure
   - Note if text is handwritten, typed, or printed
   - Identify different text regions (headers, body, footnotes, etc.)
   - Extract text from any labels, stamps, or annotations

2. VISUAL DESCRIPTION:
   - Describe the image type (document, photograph, diagram, etc.)
   - Note layout and structure
   - Describe any visible objects, people, or scenes
   - Note image quality, orientation, any damage or artifacts

3. STRUCTURED EXTRACTION:
   - Extract all dates (normalize formats)
   - Extract all names (people, organizations)
   - Extract document numbers, case numbers, file references
   - Identify signatures, stamps, or official markings
   - Extract addresses, phone numbers, email addresses
   - Note any financial amounts or numerical data

4. CONTEXT ANALYSIS:
   - Determine document type (letter, memo, form, photo, etc.)
   - Identify sender/recipient if applicable
   - Note subject matter or topic
   - Identify any references to other documents

OUTPUT FORMAT (STRICT JSON):
{
  "file_name": "<filename>",
  "image_analysis": {
    "type": "<document|photograph|diagram|other>",
    "description": "<detailed_description>",
    "layout": "<description_of_structure>",
    "quality": "<high|medium|low>",
    "orientation": "<portrait|landscape>"
  },
  "text_extraction": {
    "full_text": "<complete_extracted_text>",
    "text_regions": [
      {
        "region": "<header|body|footer|margin|stamp|etc>",
        "text": "<extracted_text>",
        "type": "<handwritten|typed|printed>"
      }
    ]
  },
  "structured_data": {
    "dates": ["<date1>", "<date2>", ...],
    "people": ["<name1>", "<name2>", ...],
    "organizations": ["<org1>", ...],
    "locations": ["<address1>", ...],
    "document_numbers": ["<ref1>", ...],
    "financial_amounts": ["<amount1>", ...],
    "contact_info": {
      "phone_numbers": ["<phone1>", ...],
      "email_addresses": ["<email1>", ...],
      "addresses": ["<address1>", ...]
    },
    "signatures": ["<signature_text>", ...],
    "stamps_or_markings": ["<description>", ...]
  },
  "document_metadata": {
    "document_type": "<letter|memo|form|photo|etc>",
    "sender": "<name_or_null>",
    "recipient": "<name_or_null>",
    "subject": "<subject_or_null>",
    "date": "<primary_date_or_null>",
    "references": ["<file_number>", ...]
  },
  "confidence": {
    "text_extraction": 0.0-1.0,
    "structured_data": 0.0-1.0,
    "overall": 0.0-1.0
  },
  "notes": "<any_uncertainties_or_observations>"
}

CRITICAL RULES:
- Extract text exactly as it appears, do not correct or normalize
- If text is unclear, note it as "[unclear: <best_guess>]"
- Do not invent information not visible in the image
- Preserve original formatting and structure
- Note any areas that are illegible or damaged
```

---

## 3. TEXT

### Goal
Extract content from text conversations, understand long context, and assemble into coherent stories/letters similar to Dorle's Stories pipeline.

### Prompt Strategy
**Multi-stage approach:**
1. **Content Extraction**: Extract and clean text content
2. **Context Understanding**: Understand the conversation/document structure
3. **Entity Extraction**: Extract dates, names, events, topics
4. **Story Assembly**: Group related texts into coherent narratives
5. **Relationship Mapping**: Build connections between entities and events

### Prompt Template (Content Extraction)
```
You are analyzing a text file from House Oversight Committee documentation.

TASK: Extract and structure the content of this text file.

REQUIREMENTS:
1. CONTENT EXTRACTION:
   - Extract all text content preserving structure
   - Identify document sections or parts
   - Note any formatting markers or special characters
   - Preserve paragraph breaks and line structure

2. CONTEXT UNDERSTANDING:
   - Determine document type (conversation, transcript, article, memo, etc.)
   - Identify participants or speakers if applicable
   - Note time period or dates mentioned
   - Identify main topics or themes

3. ENTITY EXTRACTION:
   - Extract all dates mentioned
   - Extract all names (people, organizations)
   - Extract locations, addresses
   - Extract document references or file numbers
   - Extract key events or actions

OUTPUT FORMAT (STRICT JSON):
{
  "file_name": "<filename>",
  "content": {
    "full_text": "<complete_text_content>",
    "sections": [
      {
        "section_index": <number>,
        "section_type": "<header|paragraph|list|quote|etc>",
        "text": "<section_text>"
      }
    ]
  },
  "metadata": {
    "document_type": "<type>",
    "participants": ["<name1>", ...],
    "date_range": {
      "earliest": "<date_or_null>",
      "latest": "<date_or_null>"
    },
    "file_references": ["<file_number>", ...]
  },
  "entities": {
    "people": ["<name1>", ...],
    "organizations": ["<org1>", ...],
    "locations": ["<loc1>", ...],
    "dates": ["<date1>", ...],
    "events": ["<event1>", ...]
  },
  "themes": ["<theme1>", "<theme2>", ...],
  "confidence": 0.0-1.0,
  "notes": "<any_observations>"
}
```

### Prompt Template (Story Assembly)
```
You are analyzing multiple text files from House Oversight Committee documentation.

TASK: Group related texts into coherent narratives and understand connections.

REQUIREMENTS:
1. GROUPING:
   - Group texts that are part of the same conversation, story, or topic
   - Order texts chronologically when dates are available
   - Identify continuation or related content

2. NARRATIVE CONSTRUCTION:
   - Assemble grouped texts into coherent stories
   - Note narrative flow and connections
   - Identify key events and their sequence

3. RELATIONSHIP MAPPING:
   - Map connections between entities across texts
   - Identify recurring themes or topics
   - Note temporal relationships (what happened when)

OUTPUT FORMAT (STRICT JSON):
{
  "stories": [
    {
      "id": "S0001",
      "title": "<descriptive_title>",
      "text_files": ["<filename1>", "<filename2>", ...],
      "assembled_text": "<combined_narrative>",
      "date_range": {
        "earliest": "<date_or_null>",
        "latest": "<date_or_null>"
      },
      "participants": ["<name1>", ...],
      "key_events": [
        {
          "event": "<description>",
          "date": "<date_or_null>",
          "entities_involved": ["<name1>", ...]
        }
      ],
      "themes": ["<theme1>", ...],
      "confidence": 0.0-1.0,
      "reason": "<explanation_of_grouping>"
    }
  ],
  "unassigned_files": ["<filename>", ...],
  "cross_story_connections": [
    {
      "story_ids": ["S0001", "S0002"],
      "connection_type": "<shared_entity|temporal|thematic>",
      "description": "<how_they_connect>"
    }
  ]
}

CRITICAL RULES:
- Use ONLY the provided text files
- Do not invent connections not supported by the content
- Preserve exact text, do not rewrite or summarize
- Note any ambiguities in grouping
- Maintain chronological order when possible
```

---

## General Prompt Principles

1. **Accuracy First**: Never hallucinate or infer beyond what is present
2. **Structured Output**: Always use JSON for machine-readable results
3. **Provenance**: Always include source file names and references
4. **Confidence Scores**: Include confidence levels for uncertain extractions
5. **Error Handling**: Note unclear, damaged, or ambiguous content
6. **No Commentary**: Output only structured data, no analysis or opinions
7. **Preserve Original**: Keep original text/values, don't normalize unless requested

