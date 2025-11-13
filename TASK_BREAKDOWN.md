# BATCH7 Pipeline: Verbose Task Breakdown

## Overview

This document breaks down each major task into 6-7 detailed sub-steps, addressing:
- **Provenance/Aggregation**: Stitching together Excel/text/image outputs by HOUSE_OVERSIGHT identifier
- **Token/Runtime Management**: Chunking and batching to avoid context window limits
- **Text Files → Letters Flow**: Adapting llm_group_letters.py for TEXT directory processing

---

## Task 1: Text Files → Letters Flow

### Objective
Feed TEXT files through `llm_group_letters.py` by either:
- Option A: Pointing `--images-dir` at pre-rendered TIFF/PDFs, OR
- Option B: Creating a lightweight adapter that treats `.txt` files as "already OCR'd" `_german.txt` equivalents (reusing `--german-dir` argument)

### Step 1.1: Analyze TEXT Directory Structure
**Purpose**: Understand the current TEXT file organization and naming conventions.

**Actions**:
- Scan `BATCH7/TEXT/` recursively to inventory all `.txt` files
- Extract HOUSE_OVERSIGHT identifiers from filenames (e.g., `HOUSE_OVERSIGHT_010477.txt` → `010477`)
- Map file paths to their identifiers: `{identifier: [list of file paths]}`
- Identify any subdirectory patterns (e.g., `001/`, `002/`) that might indicate batches
- Document file count per subdirectory
- Check for any existing metadata or organization patterns
- Output: `text_inventory.json` mapping identifiers to file paths

**Output**: JSON file with structure:
```json
{
  "total_files": 2895,
  "by_identifier": {
    "010477": ["TEXT/001/HOUSE_OVERSIGHT_010477.txt"],
    "010478": ["TEXT/001/HOUSE_OVERSIGHT_010478.txt"]
  },
  "by_subdirectory": {
    "001": 1998,
    "002": 897
  }
}
```

---

### Step 1.2: Create Text-to-German Adapter Module
**Purpose**: Build adapter that converts TEXT files to `llm_group_letters.py` compatible format.

**Actions**:
- Create `BATCH7/batch7_text_adapter.py` module
- Implement `convert_txt_to_german_format()` function that:
  - Reads `.txt` files from TEXT directory
  - Extracts base filename (without extension)
  - Creates `{base}_german.txt` files in a staging directory (e.g., `BATCH7/staging/german_output/`)
  - Preserves 100% of original text content (no modification)
  - Maintains file encoding (UTF-8)
- Implement `list_text_files_as_german()` function that:
  - Scans TEXT directory recursively
  - Returns list of paths matching `llm_group_letters.py`'s expected format
  - Maps original TEXT paths to staging `_german.txt` paths
- Add `--text-dir` argument support
- Add `--staging-dir` argument for temporary `_german.txt` files
- Preserve provenance: Save mapping `{original_txt_path: staging_german_path}` to JSON

**Code Structure**:
```python
def convert_txt_to_german_format(text_dir: Path, staging_dir: Path) -> Dict[str, str]:
    """Convert .txt files to _german.txt format for llm_group_letters.py"""
    mapping = {}
    for txt_file in text_dir.rglob("*.txt"):
        base = txt_file.stem  # HOUSE_OVERSIGHT_010477
        staging_path = staging_dir / f"{base}_german.txt"
        # Copy content exactly, no modification
        shutil.copy2(txt_file, staging_path)
        mapping[str(txt_file)] = str(staging_path)
    return mapping
```

**Output**: 
- Staging directory with `*_german.txt` files
- `text_to_german_mapping.json` preserving provenance

---

### Step 1.3: Integrate Adapter with llm_group_letters.py
**Purpose**: Modify or wrap `llm_group_letters.py` to accept TEXT directory input.

**Actions**:
- Option A (Preferred): Create wrapper script `batch7_group_text_letters.py` that:
  - Calls adapter to convert TEXT → staging `_german.txt`
  - Invokes `llm_group_letters.py` with `--german-dir` pointing to staging directory
  - Passes through all original `llm_group_letters.py` arguments (`--assemble`, `--save-input`, etc.)
  - Cleans up staging directory after processing (optional flag `--keep-staging`)
  
- Option B (Alternative): Modify `llm_group_letters.py` directly:
  - Add `--text-dir` argument alongside `--german-dir`
  - In `list_german_pages()`, check if `--text-dir` is provided
  - If `--text-dir` exists, convert `.txt` files on-the-fly to `_german.txt` format
  - Maintain backward compatibility with existing `--german-dir` usage

- Ensure adapter preserves 100% of original text (no normalization, no cleaning)
- Preserve all original `llm_group_letters.py` functionality:
  - `--assemble` flag for creating `de.txt` files
  - `--save-input` flag for audit trail
  - `--reuse-json` flag for reusing existing groupings
  - `--english-dir` support (if applicable)

**Output**: 
- Wrapper script or modified `llm_group_letters.py`
- Integration test verifying TEXT files are processed correctly

---

### Step 1.4: Implement Chunked Processing for Large Batches
**Purpose**: Avoid token limits by processing TEXT files in manageable chunks.

**Actions**:
- Analyze token usage: Estimate tokens per TEXT file (average ~2000 chars = ~500 tokens)
- Calculate safe batch size: Gemini 2.5 Pro context window ~1M tokens, reserve 50K for prompt → ~1900 files max per batch
- Implement chunking logic in adapter/wrapper:
  - Group TEXT files by subdirectory or identifier prefix
  - Process in batches of N files (configurable, default 500 for safety margin)
  - Each batch creates its own staging directory: `staging/batch_001/`, `staging/batch_002/`, etc.
  - Each batch calls `llm_group_letters.py` separately
  - Merge results: Combine `llm_grouping.json` outputs from all batches
- Handle cross-batch grouping: If a letter spans multiple batches, merge those groups
- Add `--batch-size` argument (default: 500)
- Add `--chunk-by` argument (`subdirectory` | `identifier_prefix` | `file_count`)

**Output**:
- Chunked processing implementation
- Batch metadata: `batch_metadata.json` tracking which files in which batch

---

### Step 1.5: Preserve Provenance Through Grouping Process
**Purpose**: Maintain traceability from original TEXT files → grouped letters.

**Actions**:
- Extend `llm_grouping.json` output to include original TEXT file paths:
  - Modify `assemble_letters()` to store original paths in `meta.json`
  - Add `source_files` field: `["TEXT/001/HOUSE_OVERSIGHT_010477.txt", ...]`
- Create provenance chain:
  - `text_to_german_mapping.json` (Step 1.2)
  - `batch_metadata.json` (Step 1.4)
  - `llm_grouping.json` (from llm_group_letters.py)
  - `letters/L0001/meta.json` (with source_files)
- Implement `build_provenance_report()` function:
  - Reads all provenance files
  - Builds reverse lookup: `{letter_id: [original_text_files]}`
  - Outputs `provenance_report.json`
- Add HOUSE_OVERSIGHT identifier extraction to letter metadata:
  - Extract identifiers from source files
  - Store in `meta.json` as `house_oversight_ids: ["010477", "010478"]`

**Output**:
- Enhanced `meta.json` files with `source_files` and `house_oversight_ids`
- `provenance_report.json` mapping letters back to original TEXT files

---

### Step 1.6: Test End-to-End Text → Letters Flow
**Purpose**: Verify the complete pipeline works correctly.

**Actions**:
- Create test dataset: Copy 10-20 TEXT files to `BATCH7/test_text/`
- Run adapter: Convert test files to staging `_german.txt` format
- Run grouping: Execute `llm_group_letters.py` (or wrapper) on test batch
- Verify outputs:
  - Check `letters/L0001/de.txt` contains original text (100% match)
  - Verify `meta.json` includes correct `source_files`
  - Confirm `llm_grouping.json` structure matches expected format
  - Validate provenance chain: Can trace from letter back to original TEXT file
- Test chunking: Process test files in 2-3 batches, verify merging works
- Test edge cases:
  - Single file per letter
  - Very long files (>10K chars)
  - Files with special characters/encoding issues
  - Empty or malformed files
- Performance test: Measure processing time per file, estimate full batch runtime

**Output**:
- Test results document
- Sample outputs in `BATCH7/test_output/`
- Performance benchmarks

---

### Step 1.7: Integration with Main Pipeline
**Purpose**: Integrate TEXT → Letters flow into `run_batch7_pipeline.py`.

**Actions**:
- Add `--process text-letters` option to `run_batch7_pipeline.py`
- Create `batch7_process_text_letters.py` module that:
  - Calls adapter (Step 1.2)
  - Runs chunked processing (Step 1.4)
  - Executes `llm_group_letters.py` integration (Step 1.3)
  - Builds provenance reports (Step 1.5)
- Add configuration options:
  - `--text-letters-staging-dir` (default: `BATCH7/staging/text_letters/`)
  - `--text-letters-batch-size` (default: 500)
  - `--text-letters-chunk-by` (default: `subdirectory`)
- Update `run_batch7_pipeline.py` to call text-letters processing
- Ensure output directory structure: `BATCH7/output/text_letters/letters/`
- Add `--skip-existing` support for resuming interrupted processing

**Output**:
- Integrated `batch7_process_text_letters.py` module
- Updated `run_batch7_pipeline.py` with text-letters support
- Documentation update

---

## Task 2: Provenance and Aggregation by HOUSE_OVERSIGHT Identifier

### Objective
Stitch together isolated JSON outputs from Excel/text/image processing using HOUSE_OVERSIGHT identifiers and lower-right tags.

### Step 2.1: Extract HOUSE_OVERSIGHT Identifiers from All Sources
**Purpose**: Build comprehensive identifier extraction across all file types.

**Actions**:
- **Excel files**: 
  - Parse filenames: `HOUSE_OVERSIGHT_016552.xls` → `016552`
  - Scan cell contents for HOUSE_OVERSIGHT references (regex: `HOUSE_OVERSIGHT_(\d+)`)
  - Extract from document metadata if present
  - Output: `natives_identifiers.json`: `{file_path: [identifiers_found]}`

- **Image files**:
  - Parse filenames: `HOUSE_OVERSIGHT_012389.jpg` → `012389`
  - Extract from OCR text (if already processed): Scan `full_text` field in JSON
  - Extract from lower-right tags (if visible in image description)
  - Output: `images_identifiers.json`: `{file_path: [identifiers_found]}`

- **Text files**:
  - Parse filenames: `HOUSE_OVERSIGHT_010477.txt` → `010477`
  - Scan file content for HOUSE_OVERSIGHT references
  - Extract from document headers/footers if structured
  - Output: `text_identifiers.json`: `{file_path: [identifiers_found]}`

- Create unified extraction function: `extract_house_oversight_ids(file_path, file_type)`
- Handle edge cases: Multiple identifiers per file, partial matches, variations

**Output**: Three JSON files mapping file paths to identifiers

---

### Step 2.2: Build Cross-Source Identifier Index
**Purpose**: Create master index linking all files by HOUSE_OVERSIGHT identifier.

**Actions**:
- Read all three identifier JSON files (from Step 2.1)
- Build reverse index: `{identifier: {natives: [files], images: [files], text: [files]}}`
- Handle identifier variations:
  - Normalize formats: `010477` vs `10477` vs `HOUSE_OVERSIGHT_010477`
  - Create alias mapping for variations
- Calculate statistics:
  - Identifiers appearing in multiple sources
  - Identifiers unique to one source
  - Most referenced identifiers
- Output: `master_identifier_index.json`:
```json
{
  "010477": {
    "natives": ["NATIVES/001/HOUSE_OVERSIGHT_016552.xls"],
    "images": ["IMAGES/001/HOUSE_OVERSIGHT_012389.jpg"],
    "text": ["TEXT/001/HOUSE_OVERSIGHT_010477.txt"]
  }
}
```

**Output**: `master_identifier_index.json` with cross-source mappings

---

### Step 2.3: Extract Lower-Right Tags from Images
**Purpose**: Identify and extract document tags from image lower-right corners.

**Actions**:
- Analyze image JSON outputs (from `batch7_process_images.py`)
- Look for lower-right region in `image_analysis.description` or `text_regions`
- Implement tag extraction logic:
  - Identify text regions with coordinates or position hints
  - Filter for "lower-right" position indicators
  - Extract tag patterns (may include HOUSE_OVERSIGHT IDs, page numbers, dates)
- Create `extract_lower_right_tags(image_json_path)` function
- Handle variations:
  - Different tag formats
  - Rotated images (adjust coordinate system)
  - Low-quality images (use OCR confidence scores)
- Output: `image_tags.json`: `{image_path: {lower_right_tag: "...", identifiers: [...]}}`

**Output**: `image_tags.json` with extracted tags and identifiers

---

### Step 2.4: Create Aggregation Module
**Purpose**: Build module that stitches together JSON outputs by identifier.

**Actions**:
- Create `BATCH7/batch7_aggregate.py` module
- Implement `aggregate_by_identifier()` function:
  - Reads `master_identifier_index.json` (Step 2.2)
  - For each identifier, loads corresponding JSON outputs:
    - `natives_analysis/*_analysis.json`
    - `images_analysis/*.json` (from image directories)
    - `text_analysis/text_extractions.json` (filtered by identifier)
    - `text_analysis/letters/*/meta.json` (if letters processed)
  - Combines into unified structure:
```json
{
  "identifier": "010477",
  "sources": {
    "natives": [...],
    "images": [...],
    "text": [...],
    "letters": [...]
  },
  "relationships": {
    "shared_entities": [...],
    "temporal_connections": [...],
    "thematic_links": [...]
  }
}
```
- Implement `build_relationship_graph()` function:
  - Extract entities from all sources (people, organizations, dates)
  - Find shared entities across sources
  - Build connection graph: `{entity: {connected_entities: [...], evidence: [...]}}`
- Handle missing data: If identifier appears in one source but not others, still include

**Output**: `aggregated_by_identifier.json` with unified view per identifier

---

### Step 2.5: Implement Cross-Source Relationship Mapping
**Purpose**: Identify and map relationships between entities across different source types.

**Actions**:
- Extract entities from each source type:
  - **Natives**: From `entities.people`, `entities.organizations` in Excel analysis JSON
  - **Images**: From `structured_data.people`, `structured_data.organizations` in image JSON
  - **Text**: From `entities.people`, `entities.organizations` in text extraction JSON
- Normalize entity names:
  - Handle variations: "Jeffrey Epstein" vs "J. Epstein" vs "Epstein, Jeffrey"
  - Create entity aliases mapping
  - Use fuzzy matching for similar names (threshold: 0.85 similarity)
- Build relationship matrix:
  - For each identifier, collect all entities from all sources
  - Find entities appearing in multiple sources (high confidence)
  - Find entities appearing with same dates/locations (temporal/spatial links)
  - Extract relationship types: `co_mentioned`, `same_date`, `same_location`, `document_reference`
- Output: `cross_source_relationships.json`:
```json
{
  "010477": {
    "entities": {
      "Jeffrey Epstein": {
        "sources": ["natives", "images", "text"],
        "mentions": 15,
        "dates": ["1997-04-08"]
      }
    },
    "relationships": [
      {
        "type": "co_mentioned",
        "entities": ["Jeffrey Epstein", "Ghislaine Maxwell"],
        "sources": ["text", "images"],
        "evidence": ["TEXT/001/HOUSE_OVERSIGHT_010477.txt", "IMAGES/001/HOUSE_OVERSIGHT_012389.jpg"]
      }
    ]
  }
}
```

**Output**: `cross_source_relationships.json` with entity relationships

---

### Step 2.6: Generate Unified Provenance Reports
**Purpose**: Create human-readable and machine-readable provenance reports.

**Actions**:
- Implement `generate_provenance_report()` function:
  - Reads all aggregation outputs (Steps 2.4, 2.5)
  - Builds reverse lookup: For each file, list all identifiers it's associated with
  - Builds forward lookup: For each identifier, list all files and their analysis outputs
- Create report formats:
  - **JSON**: `provenance_report.json` (machine-readable)
  - **Markdown**: `provenance_report.md` (human-readable)
  - **CSV**: `provenance_report.csv` (spreadsheet-friendly)
- Include in reports:
  - File → Identifier mappings
  - Identifier → File mappings
  - Cross-source connections
  - Entity relationships
  - Processing timestamps
  - Confidence scores
- Add visualization data:
  - Graph structure for relationship visualization
  - Statistics: Most connected identifiers, most referenced entities
- Output location: `BATCH7/output/provenance/`

**Output**: Multiple format provenance reports

---

### Step 2.7: Integrate Aggregation into Main Pipeline
**Purpose**: Add aggregation step to `run_batch7_pipeline.py`.

**Actions**:
- Add `--aggregate` flag to `run_batch7_pipeline.py`
- Create aggregation step that runs after all processing:
  - Waits for natives/images/text processing to complete
  - Runs identifier extraction (Step 2.1)
  - Builds master index (Step 2.2)
  - Extracts image tags (Step 2.3)
  - Runs aggregation (Step 2.4)
  - Maps relationships (Step 2.5)
  - Generates reports (Step 2.6)
- Add `--aggregate-only` flag for re-running aggregation without reprocessing
- Add configuration:
  - `--aggregation-output-dir` (default: `BATCH7/output/aggregation/`)
  - `--provenance-output-dir` (default: `BATCH7/output/provenance/`)
- Update documentation with aggregation workflow

**Output**: Integrated aggregation in main pipeline

---

## Task 3: Token/Runtime Optimization

### Objective
Address token and runtime pressure by implementing chunking, batching, and efficient processing strategies.

### Step 3.1: Analyze Token Usage Patterns
**Purpose**: Understand current token consumption and identify bottlenecks.

**Actions**:
- Instrument existing code to measure token usage:
  - Add token counting to LLM calls (input + output)
  - Log token usage per file type (Excel, image, text)
  - Track peak token usage per batch
- Analyze patterns:
  - Average tokens per Excel file (with full cell dump)
  - Average tokens per image (OCR + analysis)
  - Average tokens per text file (extraction + assembly)
- Identify bottlenecks:
  - Which operations consume most tokens?
  - Which files are outliers (very large)?
  - What's the distribution of file sizes?
- Create token usage report: `token_analysis.json`
- Estimate total tokens for full batch:
  - Natives: 10 files × avg_tokens_per_file
  - Images: 4000 files × avg_tokens_per_file
  - Text: 2895 files × avg_tokens_per_file

**Output**: `token_analysis.json` with usage patterns and estimates

---

### Step 3.2: Implement Excel Chunking Strategy
**Purpose**: Break large Excel files into manageable chunks for LLM processing.

**Actions**:
- Modify `batch7_process_natives.py` to chunk Excel data:
  - Instead of dumping entire worksheet to text (current line 121-165), chunk by:
    - **Option A**: Process worksheet-by-worksheet (separate LLM call per sheet)
    - **Option B**: Process row-by-row in batches (e.g., 100 rows per call)
    - **Option C**: Process column-by-column for wide spreadsheets
  - Implement `chunk_excel_dataframe(df, chunk_size=100)` function
  - For each chunk:
    - Convert to text representation
    - Call LLM for analysis
    - Store chunk-level JSON
  - Merge chunk results: Combine analyses from all chunks
  - Preserve relationships: Track which chunks belong to same worksheet/file
- Add `--excel-chunk-size` argument (default: 100 rows)
- Add `--excel-chunk-method` argument (`rows` | `sheets` | `columns`)
- Handle edge cases:
  - Very wide spreadsheets (many columns)
  - Very long spreadsheets (many rows)
  - Merged cells spanning chunks
- Update prompt to handle chunked input: "This is chunk X of Y from worksheet Z..."

**Output**: Chunked Excel processing implementation

---

### Step 3.3: Implement Text File Batching for Story Assembly
**Purpose**: Avoid sending hundreds of text files to single "assemble stories" call.

**Actions**:
- Modify `batch7_process_text.py` `assemble_stories()` function (line 330):
  - Instead of single LLM call with all text extractions, implement batching:
    - Group text files by subdirectory or identifier prefix
    - Process each batch separately (e.g., 50-100 files per batch)
    - Each batch produces its own `stories_assembly_batch_N.json`
  - Implement `batch_text_extractions(extractions, batch_size=50)` function
  - For each batch:
    - Build input listing (truncated version of current approach)
    - Call LLM for story assembly
    - Store batch results
  - Merge batch results:
    - Combine stories from all batches
    - Handle cross-batch connections (if story spans batches)
    - Deduplicate entities and relationships
  - Add `--text-batch-size` argument (default: 50)
  - Add `--text-batch-method` argument (`subdirectory` | `identifier_prefix` | `file_count`)
- Update prompt to indicate batch context: "This is batch X of Y. Focus on grouping within this batch..."

**Output**: Batched text story assembly implementation

---

### Step 3.4: Implement Image Processing Queue with Rate Limiting
**Purpose**: Manage API rate limits and prevent overwhelming the system.

**Actions**:
- Create image processing queue system:
  - Process images in batches (e.g., 10-20 at a time)
  - Add delays between batches to respect rate limits
  - Implement retry logic for failed API calls
- Add rate limiting:
  - Configurable requests per minute (default: 60)
  - Exponential backoff for rate limit errors
  - Queue management: Process queue with worker threads/processes
- Add progress tracking:
  - Save progress checkpoint after each batch
  - Resume from checkpoint if interrupted (`--resume-from-checkpoint`)
  - Progress bar showing: `[X/Y] images processed`
- Implement `process_images_with_queue()` function:
  - Enqueue all images
  - Process in batches with rate limiting
  - Save results incrementally (don't wait for all to complete)
- Add `--image-batch-size` argument (default: 10)
- Add `--rate-limit-rpm` argument (default: 60)

**Output**: Queue-based image processing with rate limiting

---

### Step 3.5: Implement Caching and Skip Logic
**Purpose**: Avoid reprocessing files that haven't changed.

**Actions**:
- Add file hash tracking:
  - Calculate MD5/SHA256 hash of each input file
  - Store hash in output JSON metadata
  - On subsequent runs, compare hashes
- Implement skip logic:
  - If output exists AND hash matches → skip processing
  - If output exists BUT hash differs → reprocess
  - Add `--force-reprocess` flag to override
- Add cache directory:
  - Store file hashes: `BATCH7/cache/file_hashes.json`
  - Store processing metadata: `BATCH7/cache/processing_metadata.json`
- Update each processing module:
  - `batch7_process_natives.py`: Check hash before Excel analysis
  - `batch7_process_images.py`: Check hash before image analysis
  - `batch7_process_text.py`: Check hash before text extraction
- Handle edge cases:
  - Files deleted from source (mark as stale in cache)
  - Cache corruption (rebuild cache)

**Output**: Caching system with hash-based skip logic

---

### Step 3.6: Add Parallel Processing Support
**Purpose**: Speed up processing by running multiple operations in parallel.

**Actions**:
- Analyze parallelization opportunities:
  - Excel files: Can process multiple files in parallel (I/O bound)
  - Images: Can process multiple images in parallel (API bound, respect rate limits)
  - Text files: Can extract from multiple files in parallel (I/O + API bound)
- Implement parallel processing:
  - Use `concurrent.futures.ThreadPoolExecutor` or `ProcessPoolExecutor`
  - For Excel: Process N files in parallel (default: 4)
  - For Images: Process N images in parallel with rate limiting (default: 5)
  - For Text: Process N files in parallel (default: 10)
- Add `--parallel-workers` argument (default: auto-detect CPU count)
- Handle shared resources:
  - Thread-safe file writing
  - API client thread safety
  - Progress tracking synchronization
- Test parallel processing:
  - Verify no race conditions
  - Measure speedup vs sequential
  - Ensure API rate limits still respected

**Output**: Parallel processing implementation

---

### Step 3.7: Add Monitoring and Progress Tracking
**Purpose**: Track processing progress and estimate completion time.

**Actions**:
- Implement progress tracking:
  - Save progress to `BATCH7/output/progress.json`:
```json
{
  "natives": {"processed": 5, "total": 10, "started": "2025-01-XX", "estimated_completion": "2025-01-XX"},
  "images": {"processed": 1500, "total": 4000, "started": "2025-01-XX", "estimated_completion": "2025-01-XX"},
  "text": {"processed": 1000, "total": 2895, "started": "2025-01-XX", "estimated_completion": "2025-01-XX"}
}
```
  - Update progress after each file/batch
  - Calculate ETA based on processing rate
- Add monitoring:
  - Log token usage per operation
  - Log API call counts and errors
  - Log processing times
  - Generate summary report: `processing_summary.json`
- Add progress visualization:
  - Print progress bars to console
  - Generate HTML progress dashboard (optional)
- Handle interruptions gracefully:
  - Save state before exit
  - Resume from last checkpoint

**Output**: Progress tracking and monitoring system

---

## Summary

### Task 1: Text Files → Letters Flow (7 steps)
1. Analyze TEXT directory structure
2. Create text-to-German adapter module
3. Integrate adapter with llm_group_letters.py
4. Implement chunked processing for large batches
5. Preserve provenance through grouping process
6. Test end-to-end text → letters flow
7. Integration with main pipeline

### Task 2: Provenance and Aggregation (7 steps)
1. Extract HOUSE_OVERSIGHT identifiers from all sources
2. Build cross-source identifier index
3. Extract lower-right tags from images
4. Create aggregation module
5. Implement cross-source relationship mapping
6. Generate unified provenance reports
7. Integrate aggregation into main pipeline

### Task 3: Token/Runtime Optimization (7 steps)
1. Analyze token usage patterns
2. Implement Excel chunking strategy
3. Implement text file batching for story assembly
4. Implement image processing queue with rate limiting
5. Implement caching and skip logic
6. Add parallel processing support
7. Add monitoring and progress tracking

---

## Implementation Priority

**Phase 1 (Critical)**:
- Task 1: Steps 1.1, 1.2, 1.3 (Text adapter and integration)
- Task 3: Steps 3.2, 3.3 (Chunking/batching to avoid token limits)

**Phase 2 (Important)**:
- Task 1: Steps 1.4, 1.5, 1.6 (Chunking, provenance, testing)
- Task 2: Steps 2.1, 2.2, 2.4 (Identifier extraction and aggregation)

**Phase 3 (Enhancement)**:
- Task 2: Steps 2.3, 2.5, 2.6, 2.7 (Tag extraction, relationships, reports)
- Task 3: Steps 3.1, 3.4, 3.5, 3.6, 3.7 (Optimization and monitoring)

