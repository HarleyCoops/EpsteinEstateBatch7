# BATCH7 Pipeline Test Suite

Comprehensive unit tests for the EpsteinEstateBatch7 document processing pipeline.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Running Tests](#running-tests)
- [Test Organization](#test-organization)
- [Test Coverage](#test-coverage)
- [Writing New Tests](#writing-new-tests)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

## Overview

This test suite provides comprehensive coverage for all components of the BATCH7 pipeline:

- **Natives Processing** (`batch7_process_natives.py`) - Excel/spreadsheet processing
- **Images Processing** (`batch7_process_images.py`) - Image OCR and analysis
- **Text Processing** (`batch7_process_text.py`) - Text extraction and story assembly
- **Pipeline Orchestration** (`run_batch7_pipeline.py`) - Main pipeline coordinator

### Test Statistics

- **Total Test Files**: 4
- **Test Functions**: 100+
- **Test Fixtures**: 20+
- **Coverage Areas**: Unit tests, Integration tests, Error handling, Edge cases

## Installation

### Prerequisites

- Python 3.8+
- All BATCH7 pipeline dependencies installed

### Install Test Dependencies

```bash
# Install pytest and related packages
pip install pytest pytest-cov pytest-mock

# Or install from requirements
pip install -r requirements.txt
```

### Verify Installation

```bash
# Check pytest is installed
pytest --version

# Should output: pytest 7.x.x or higher
```

## Running Tests

### Run All Tests

```bash
# From BATCH7/ directory
cd BATCH7
pytest

# With verbose output
pytest -v

# With detailed output
pytest -vv
```

### Run Specific Test Files

```bash
# Test natives processing only
pytest tests/test_batch7_process_natives.py

# Test images processing only
pytest tests/test_batch7_process_images.py

# Test text processing only
pytest tests/test_batch7_process_text.py

# Test pipeline orchestration only
pytest tests/test_run_batch7_pipeline.py
```

### Run Tests by Marker

Tests are organized with markers for selective execution:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests for specific modules
pytest -m natives
pytest -m images
pytest -m text

# Combine markers
pytest -m "unit and natives"
pytest -m "integration and not slow"
```

### Available Markers

- `unit` - Unit tests for individual functions
- `integration` - Integration tests for complete workflows
- `natives` - Tests for Excel/natives processing
- `images` - Tests for image processing
- `text` - Tests for text processing
- `llm` - Tests that interact with LLM APIs (requires API key)
- `slow` - Tests that take longer to execute

### Run with Coverage

```bash
# Run with coverage report
pytest --cov=. --cov-report=html --cov-report=term

# Open coverage report
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

### Run Specific Test Functions

```bash
# Run a specific test class
pytest tests/test_batch7_process_natives.py::TestReadExcelToText

# Run a specific test function
pytest tests/test_batch7_process_natives.py::TestReadExcelToText::test_read_simple_excel

# Run tests matching a pattern
pytest -k "test_read"
pytest -k "test_extract"
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto

# Run with 4 workers
pytest -n 4
```

## Test Organization

### Directory Structure

```
tests/
├── __init__.py                          # Test package init
├── conftest.py                          # Shared fixtures and configuration
├── test_batch7_process_natives.py       # Natives processing tests
├── test_batch7_process_images.py        # Images processing tests
├── test_batch7_process_text.py          # Text processing tests
├── test_run_batch7_pipeline.py          # Pipeline orchestration tests
└── README.md                            # This file
```

### Test File Structure

Each test file follows this structure:

1. **Imports and Setup** - Import modules and configure test environment
2. **Test Classes** - Group related tests by functionality
3. **Unit Tests** - Test individual functions in isolation
4. **Integration Tests** - Test complete workflows
5. **Edge Cases** - Test error handling and boundary conditions

### Naming Conventions

- Test files: `test_<module_name>.py`
- Test classes: `Test<FunctionName>` or `Test<Feature>`
- Test functions: `test_<what_is_being_tested>`

Examples:
- `test_read_excel_to_text()` - Tests the `read_excel_to_text()` function
- `test_extract_with_valid_response()` - Tests extraction with valid LLM response
- `test_process_skip_existing()` - Tests the skip_existing flag

## Test Coverage

### Natives Processing (`test_batch7_process_natives.py`)

**Functions Tested:**
- `read_excel_to_text()` - Excel to text conversion
- `analyze_excel_with_llm()` - LLM analysis of Excel data
- `process_single_excel()` - Single file processing
- `process_natives()` - Batch directory processing

**Test Categories:**
- ✅ File reading and parsing
- ✅ Text conversion accuracy
- ✅ LLM response handling (valid JSON, markdown, errors)
- ✅ Metadata extraction (file paths, HOUSE_OVERSIGHT IDs)
- ✅ Output file creation
- ✅ Skip existing logic
- ✅ Multi-sheet Excel files
- ✅ Error handling and recovery
- ✅ API key validation

**Total Tests:** 30+

### Images Processing (`test_batch7_process_images.py`)

**Functions Tested:**
- `analyze_image_with_llm()` - Image analysis with vision LLM
- `process_single_image()` - Single image processing
- `process_images()` - Batch directory processing

**Test Categories:**
- ✅ Image file upload
- ✅ Vision model analysis
- ✅ OCR extraction
- ✅ Metadata extraction
- ✅ JSON output creation
- ✅ Skip existing logic
- ✅ Multiple image formats (.jpg, .png, .tiff, etc.)
- ✅ Recursive directory scanning
- ✅ Error handling
- ✅ Unicode/UTF-8 encoding

**Total Tests:** 35+

### Text Processing (`test_batch7_process_text.py`)

**Functions Tested:**
- `extract_text_content()` - Text content extraction
- `assemble_stories()` - Story assembly and grouping
- `create_story_folders()` - Folder structure creation
- `process_text()` - Multi-phase processing

**Test Categories:**
- ✅ Text file reading
- ✅ Content extraction
- ✅ LLM response parsing (JSON, markdown, errors)
- ✅ Story grouping logic
- ✅ Folder structure creation
- ✅ Per-file JSON outputs
- ✅ Aggregated outputs
- ✅ Skip existing for each phase
- ✅ Error file generation
- ✅ Multi-file processing

**Total Tests:** 40+

### Pipeline Orchestration (`test_run_batch7_pipeline.py`)

**Functions Tested:**
- `main()` - Pipeline orchestration and execution

**Test Categories:**
- ✅ Argument parsing
- ✅ Process selection (all, natives, images, text)
- ✅ Directory path handling
- ✅ Custom directory arguments
- ✅ Output directory creation
- ✅ API key validation
- ✅ Missing directory handling
- ✅ Skip existing flag propagation
- ✅ Process execution order
- ✅ Console output messages

**Total Tests:** 25+

## Writing New Tests

### Basic Test Template

```python
import pytest
from pathlib import Path

@pytest.mark.unit
@pytest.mark.natives  # or images, text
def test_my_new_feature(temp_dir):
    """Test description of what this test validates."""
    # Arrange - Set up test data
    test_file = temp_dir / "test.xlsx"
    # ... create test file

    # Act - Execute the function being tested
    result = my_function(test_file)

    # Assert - Verify the results
    assert result is not None
    assert "expected_key" in result
```

### Using Fixtures

Common fixtures available in `conftest.py`:

```python
def test_with_fixtures(temp_dir, sample_excel_file, mock_llm_response_natives):
    """Example using multiple fixtures."""
    # temp_dir - Temporary directory for test files
    # sample_excel_file - Pre-created sample Excel file
    # mock_llm_response_natives - Mock LLM response for natives
```

### Mocking LLM Calls

```python
from unittest.mock import Mock

def test_with_mocked_llm():
    """Example of mocking LLM API calls."""
    mock_client = Mock()
    mock_stream = [Mock(text='{"result": "data"}')]
    mock_client.models.generate_content_stream.return_value = mock_stream

    result = analyze_with_llm(file_path, mock_client)

    assert result["result"] == "data"
```

### Testing Error Conditions

```python
def test_error_handling():
    """Test that errors are handled gracefully."""
    mock_client = Mock()
    mock_client.files.upload.side_effect = Exception("Upload failed")

    result = process_file(file_path, mock_client)

    assert "error" in result
    assert "Upload failed" in result["error"]
```

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        cd BATCH7
        pytest -v --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem:** `ModuleNotFoundError: No module named 'batch7_process_natives'`

**Solution:**
```bash
# Make sure you're in the BATCH7 directory
cd BATCH7

# Run pytest from BATCH7 directory
pytest
```

#### 2. API Key Warnings

**Problem:** Tests fail with "GEMINI_API_KEY not set"

**Solution:** The test suite uses mocked API calls, so you don't need a real API key. The tests mock the environment variable. If you see this error, check that `conftest.py` fixtures are being loaded.

#### 3. File Permission Errors

**Problem:** `PermissionError` when creating temp files

**Solution:**
```bash
# On Windows, run as administrator or check antivirus
# On Linux/Mac, check file permissions
chmod 755 BATCH7/tests
```

#### 4. Slow Test Execution

**Problem:** Tests take too long to run

**Solution:**
```bash
# Skip slow tests
pytest -m "not slow"

# Run in parallel
pip install pytest-xdist
pytest -n auto

# Run only unit tests (faster than integration)
pytest -m unit
```

#### 5. Fixture Not Found

**Problem:** `fixture 'temp_dir' not found`

**Solution:** Make sure `conftest.py` is in the tests directory and pytest can find it.

### Debug Mode

Run tests with debugging enabled:

```bash
# Show print statements
pytest -s

# Show local variables on failures
pytest -l

# Drop into debugger on failures
pytest --pdb

# Show full traceback
pytest --tb=long
```

### Verbose Output

```bash
# Show test names as they run
pytest -v

# Show even more detail
pytest -vv

# Show summary of all test outcomes
pytest -ra
```

## Best Practices

### 1. Test Isolation

Each test should be independent and not rely on other tests:

```python
# Good - Self-contained test
def test_feature(temp_dir):
    file = temp_dir / "test.txt"
    file.write_text("content")
    # ... test logic

# Bad - Relies on external state
def test_feature():
    file = Path("test.txt")  # Assumes file exists
    # ... test logic
```

### 2. Use Fixtures for Setup

```python
# Good - Use fixtures
def test_with_fixture(sample_excel_file):
    result = process(sample_excel_file)
    assert result is not None

# Bad - Repeat setup in every test
def test_without_fixture():
    file = create_excel()  # Repeated in every test
    result = process(file)
```

### 3. Test One Thing at a Time

```python
# Good - Tests one specific behavior
def test_extracts_house_oversight_id():
    result = extract_id("HOUSE_OVERSIGHT_010477.txt")
    assert result == "010477"

# Bad - Tests multiple unrelated things
def test_everything():
    result = process_file("test.txt")
    assert result["id"] == "010477"
    assert len(result["entities"]) > 0
    assert result["processing_metadata"]["model"] == "gemini-2.5-pro"
    # ... tests too much
```

### 4. Descriptive Test Names

```python
# Good
def test_skip_existing_flag_prevents_reprocessing():
    pass

# Bad
def test_skip():
    pass
```

### 5. Mock External Dependencies

Always mock:
- LLM API calls
- File system operations (when using temp_dir)
- Network requests
- Environment variables

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/mark.html)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## Contributing

When adding new features to the pipeline:

1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add tests for edge cases and error conditions
4. Update this README if adding new test categories
5. Maintain test coverage above 80%

---

**Last Updated:** 2025-01-15
**Test Suite Version:** 1.0
**Pipeline Version:** BATCH7
