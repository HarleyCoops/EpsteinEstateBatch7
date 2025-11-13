# BATCH7 JSON Output Schema Rubric

This document defines the standardized JSON schemas for all output files in the BATCH7 pipeline. All outputs follow these schemas to ensure consistency and enable downstream aggregation.

---

## 1. Image Analysis JSON Schema

**File Location**: Same folder as image, `{image_name}.json`  
**Example**: `IMAGES/001/HOUSE_OVERSIGHT_012389.jpg` → `IMAGES/001/HOUSE_OVERSIGHT_012389.json`

```json
{
  "file_name": "string (required)",
  "file_path": "string (relative path from BATCH7 root)",
  "house_oversight_id": "string (extracted identifier, e.g., '012389')",
  
  "image_analysis": {
    "type": "string (required): 'document' | 'photograph' | 'diagram' | 'other'",
    "description": "string (required): Detailed visual description",
    "layout": "string: Description of document/image structure",
    "quality": "string: 'high' | 'medium' | 'low'",
    "orientation": "string: 'portrait' | 'landscape'"
  },
  
  "text_extraction": {
    "full_text": "string (required): Complete extracted text, 100% original",
    "text_regions": [
      {
        "region": "string: 'header' | 'body' | 'footer' | 'margin' | 'stamp' | 'other'",
        "text": "string: Extracted text from this region",
        "type": "string: 'handwritten' | 'typed' | 'printed'",
        "confidence": "number (0.0-1.0): OCR confidence for this region"
      }
    ]
  },
  
  "structured_data": {
    "dates": ["string: Normalized date strings (YYYY-MM-DD preferred)"],
    "people": ["string: Person names as extracted"],
    "organizations": ["string: Organization names"],
    "locations": ["string: Addresses, place names"],
    "document_numbers": ["string: Case numbers, file references, HOUSE_OVERSIGHT IDs"],
    "financial_amounts": ["string: Currency amounts, numbers"],
    "contact_info": {
      "phone_numbers": ["string"],
      "email_addresses": ["string"],
      "addresses": ["string"]
    },
    "signatures": ["string: Signature text or descriptions"],
    "stamps_or_markings": ["string: Official stamps, watermarks, etc."]
  },
  
  "document_metadata": {
    "document_type": "string: 'letter' | 'memo' | 'form' | 'photo' | 'receipt' | 'other'",
    "sender": "string | null",
    "recipient": "string | null",
    "subject": "string | null",
    "date": "string | null: Primary date from document",
    "references": ["string: File numbers, case references"]
  },
  
  "lower_right_tag": {
    "text": "string | null: Extracted tag from lower-right corner",
    "confidence": "number (0.0-1.0)"
  },
  
  "confidence": {
    "text_extraction": "number (0.0-1.0, required)",
    "structured_data": "number (0.0-1.0, required)",
    "overall": "number (0.0-1.0, required)"
  },
  
  "processing_metadata": {
    "processed_at": "string (ISO 8601 timestamp)",
    "model": "string: 'gemini-2.5-pro'",
    "processing_time_seconds": "number"
  },
  
  "notes": "string | null: Uncertainties, observations, edge cases"
}
```

**Required Fields**: `file_name`, `image_analysis.type`, `image_analysis.description`, `text_extraction.full_text`, `confidence.*`

---

## 2. Excel Analysis JSON Schema

**File Location**: Same folder as Excel file, `{excel_name}_analysis.json`  
**Example**: `NATIVES/001/HOUSE_OVERSIGHT_016552.xls` → `NATIVES/001/HOUSE_OVERSIGHT_016552_analysis.json`

```json
{
  "file_name": "string (required)",
  "file_path": "string (relative path from BATCH7 root)",
  "house_oversight_id": "string (extracted identifier, e.g., '016552')",
  
  "structure": {
    "worksheets": [
      {
        "name": "string (required): Worksheet/tab name",
        "purpose": "string: Description of worksheet purpose",
        "row_count": "number (required)",
        "column_count": "number (required)",
        "headers": ["string: Column headers (if detected)"],
        "data_types": {
          "column_name": "string: 'text' | 'number' | 'date' | 'formula' | 'mixed'"
        }
      }
    ]
  },
  
  "data": {
    "worksheet_name": [
      {
        "row_index": "number (0-based or 1-based, consistent)",
        "data": {
          "column_name_or_index": "string | number | null: Cell value"
        }
      }
    ]
  },
  
  "entities": {
    "people": ["string: Person names extracted from cells"],
    "organizations": ["string: Organization names"],
    "locations": ["string: Addresses, place names"],
    "dates": ["string: Normalized date strings"],
    "financial_amounts": ["string | number: Currency values, numbers"],
    "document_references": ["string: HOUSE_OVERSIGHT IDs, file numbers"]
  },
  
  "relationships": [
    {
      "type": "string: 'transaction' | 'contact' | 'schedule' | 'hierarchy' | 'other'",
      "source": "string: Entity name or cell reference",
      "target": "string: Entity name or cell reference",
      "context": "string: Description of relationship",
      "evidence": "string: Supporting data (cell range, formula, etc.)",
      "confidence": "number (0.0-1.0)"
    }
  ],
  
  "context": {
    "document_type": "string: 'financial_records' | 'contact_list' | 'schedule' | 'inventory' | 'other'",
    "time_period": {
      "start_date": "string | null: Earliest date found",
      "end_date": "string | null: Latest date found"
    },
    "key_themes": ["string: Main topics or themes"],
    "references": ["string: HOUSE_OVERSIGHT IDs, file numbers referenced"]
  },
  
  "processing_metadata": {
    "processed_at": "string (ISO 8601 timestamp)",
    "model": "string: 'gemini-2.5-pro'",
    "processing_time_seconds": "number",
    "chunk_count": "number: If file was chunked for processing"
  },
  
  "confidence": "number (0.0-1.0, required)",
  "notes": "string | null: Uncertainties, observations, edge cases"
}
```

**Required Fields**: `file_name`, `structure.worksheets[]`, `confidence`

---

## 3. Text Extraction JSON Schema

**File Location**: Same folder as text file, `{text_name}_extraction.json`  
**Example**: `TEXT/001/HOUSE_OVERSIGHT_010477.txt` → `TEXT/001/HOUSE_OVERSIGHT_010477_extraction.json`

```json
{
  "file_name": "string (required)",
  "file_path": "string (relative path from BATCH7 root)",
  "house_oversight_id": "string (extracted identifier, e.g., '010477')",
  
  "content": {
    "full_text": "string (required): Complete text content, 100% original",
    "sections": [
      {
        "section_index": "number (0-based)",
        "section_type": "string: 'header' | 'paragraph' | 'list' | 'quote' | 'other'",
        "text": "string: Text content of this section"
      }
    ],
    "character_count": "number",
    "word_count": "number",
    "line_count": "number"
  },
  
  "metadata": {
    "document_type": "string: 'conversation' | 'transcript' | 'article' | 'memo' | 'other'",
    "participants": ["string: Speaker/author names if identified"],
    "date_range": {
      "earliest": "string | null: Earliest date mentioned",
      "latest": "string | null: Latest date mentioned"
    },
    "file_references": ["string: HOUSE_OVERSIGHT IDs, file numbers referenced"]
  },
  
  "entities": {
    "people": ["string: Person names mentioned"],
    "organizations": ["string: Organization names"],
    "locations": ["string: Place names, addresses"],
    "dates": ["string: All dates mentioned (normalized)"],
    "events": ["string: Key events or actions described"]
  },
  
  "themes": ["string: Main topics or themes identified"],
  
  "processing_metadata": {
    "processed_at": "string (ISO 8601 timestamp)",
    "model": "string: 'gemini-2.5-pro'",
    "processing_time_seconds": "number"
  },
  
  "confidence": "number (0.0-1.0, required)",
  "notes": "string | null: Uncertainties, observations, edge cases"
}
```

**Required Fields**: `file_name`, `content.full_text`, `confidence`

---

## 4. Story Assembly JSON Schema

**File Location**: `output/text_analysis/stories_assembly.json` (aggregated, not per-file)

```json
{
  "stories": [
    {
      "id": "string (required): 'S0001', 'S0002', etc.",
      "title": "string: Descriptive title",
      "text_files": ["string: Source file names"],
      "text_file_paths": ["string: Full paths to source files"],
      "house_oversight_ids": ["string: All HOUSE_OVERSIGHT IDs in this story"],
      "assembled_text": "string: Combined narrative text",
      "date_range": {
        "earliest": "string | null",
        "latest": "string | null"
      },
      "participants": ["string: People mentioned"],
      "key_events": [
        {
          "event": "string: Event description",
          "date": "string | null",
          "entities_involved": ["string: People/organizations"]
        }
      ],
      "themes": ["string: Main themes"],
      "confidence": "number (0.0-1.0)",
      "reason": "string: Explanation of grouping logic"
    }
  ],
  
  "unassigned_files": ["string: Files that couldn't be grouped"],
  
  "cross_story_connections": [
    {
      "story_ids": ["string: Story IDs that connect"],
      "connection_type": "string: 'shared_entity' | 'temporal' | 'thematic'",
      "description": "string: How they connect"
    }
  ],
  
  "processing_metadata": {
    "processed_at": "string (ISO 8601 timestamp)",
    "total_files_processed": "number",
    "stories_created": "number",
    "unassigned_count": "number"
  }
}
```

---

## 5. Letter Metadata JSON Schema

**File Location**: `output/text_analysis/letters/S0001/meta.json` (from story assembly)

```json
{
  "id": "string (required): 'S0001', etc.",
  "title": "string",
  "text_files": ["string: Source file names"],
  "text_file_paths": ["string: Full paths"],
  "house_oversight_ids": ["string: All HOUSE_OVERSIGHT IDs"],
  "date_range": {
    "earliest": "string | null",
    "latest": "string | null"
  },
  "participants": ["string"],
  "key_events": [
    {
      "event": "string",
      "date": "string | null",
      "entities_involved": ["string"]
    }
  ],
  "themes": ["string"],
  "confidence": "number (0.0-1.0)",
  "reason": "string: Grouping explanation",
  
  "source_files": ["string: Full paths to original TEXT files"],
  "provenance": {
    "extraction_files": ["string: Paths to _extraction.json files"],
    "processing_timestamp": "string (ISO 8601)"
  }
}
```

---

## Common Field Conventions

### Dates
- **Format**: ISO 8601 preferred (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`)
- **Normalization**: Convert all date formats to ISO 8601 when possible
- **Uncertain dates**: Use `[unclear: YYYY-MM-DD]` or `[circa YYYY]` format

### Names
- **Preservation**: Keep original capitalization and formatting
- **Variations**: Note variations in `notes` field (e.g., "Jeffrey Epstein" vs "J. Epstein")
- **Normalization**: Don't normalize unless explicitly requested

### HOUSE_OVERSIGHT IDs
- **Extraction**: Extract from filenames and content
- **Format**: Numeric string (e.g., `"010477"`, `"016552"`)
- **Multiple IDs**: Array if file references multiple identifiers

### Confidence Scores
- **Range**: 0.0 to 1.0
- **Interpretation**:
  - 0.9-1.0: High confidence, clear extraction
  - 0.7-0.9: Good confidence, minor uncertainties
  - 0.5-0.7: Moderate confidence, some ambiguity
  - 0.0-0.5: Low confidence, significant uncertainty

### File Paths
- **Format**: Relative paths from `BATCH7/` root
- **Example**: `"IMAGES/001/HOUSE_OVERSIGHT_012389.jpg"`
- **Consistency**: Always use forward slashes `/` even on Windows

### Processing Metadata
- **Timestamp**: ISO 8601 format (`2025-01-XXT12:34:56Z`)
- **Model**: Always `"gemini-2.5-pro"` for current pipeline
- **Processing Time**: Seconds as float (e.g., `12.345`)

---

## Validation Rules

1. **Required Fields**: All schemas must include required fields
2. **Type Consistency**: Arrays must contain consistent types
3. **Null Handling**: Use `null` (not empty strings) for missing optional fields
4. **Encoding**: All JSON files must be UTF-8 encoded
5. **Pretty Print**: Use 2-space indentation for readability
6. **No Trailing Commas**: Ensure valid JSON (no trailing commas)

---

## Example Files

See `BATCH7/examples/` directory for sample JSON outputs matching these schemas (to be created during implementation).

---

## Version History

- **v1.0** (2025-01-XX): Initial schema definition
- Future versions will be tracked here as schemas evolve

