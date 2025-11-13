"""
Unit tests for batch7_process_natives.py

Tests Excel/natives processing functionality including:
- Excel file reading and text conversion
- LLM analysis with mocked responses
- Single file processing
- Batch directory processing
- Error handling and edge cases
"""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from batch7_process_natives import (
    read_excel_to_text,
    analyze_excel_with_llm,
    process_single_excel,
    process_natives,
    PROMPT_EXCEL_ANALYSIS
)


# ============================================================================
# TESTS: read_excel_to_text()
# ============================================================================

@pytest.mark.unit
@pytest.mark.natives
class TestReadExcelToText:
    """Tests for Excel to text conversion."""

    def test_read_simple_excel(self, sample_excel_file):
        """Test reading a simple Excel file."""
        text = read_excel_to_text(sample_excel_file)

        assert "FILE:" in text
        assert sample_excel_file.name in text
        assert "SHEETS:" in text
        assert "WORKSHEET:" in text
        assert "Dimensions:" in text
        assert "rows x" in text
        assert "columns" in text

    def test_read_excel_contains_data(self, sample_excel_file, sample_excel_data):
        """Test that converted text contains actual data."""
        text = read_excel_to_text(sample_excel_file)

        # Check for data from sample
        assert "John Doe" in text
        assert "Jane Smith" in text
        assert "HOUSE_OVERSIGHT_010477" in text

    def test_read_nonexistent_file(self, temp_dir):
        """Test reading a file that doesn't exist."""
        fake_file = temp_dir / "nonexistent.xlsx"
        text = read_excel_to_text(fake_file)

        assert "ERROR" in text

    def test_read_excel_multiple_sheets(self, temp_dir):
        """Test reading Excel file with multiple sheets."""
        excel_path = temp_dir / "multisheet.xlsx"

        # Create Excel with multiple sheets
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            pd.DataFrame({'A': [1, 2]}).to_excel(writer, sheet_name='Sheet1', index=False)
            pd.DataFrame({'B': [3, 4]}).to_excel(writer, sheet_name='Sheet2', index=False)

        text = read_excel_to_text(excel_path)

        assert "Sheet1" in text
        assert "Sheet2" in text
        assert text.count("WORKSHEET:") == 2

    def test_read_empty_excel(self, temp_dir):
        """Test reading an empty Excel file."""
        excel_path = temp_dir / "empty.xlsx"
        pd.DataFrame().to_excel(excel_path, index=False, engine='openpyxl')

        text = read_excel_to_text(excel_path)

        assert "FILE:" in text
        assert "SHEETS:" in text
        # Should handle empty data gracefully

    def test_text_format_structure(self, sample_excel_file):
        """Test that text output has expected structure."""
        text = read_excel_to_text(sample_excel_file)

        lines = text.split('\n')
        assert lines[0].startswith("FILE:")
        assert lines[1].startswith("SHEETS:")

        # Should have worksheet separator
        assert any("===" in line and "WORKSHEET:" in line for line in lines)


# ============================================================================
# TESTS: analyze_excel_with_llm()
# ============================================================================

@pytest.mark.unit
@pytest.mark.natives
class TestAnalyzeExcelWithLLM:
    """Tests for LLM analysis of Excel data."""

    def test_analyze_with_valid_json_response(self, sample_excel_file, mock_llm_response_natives):
        """Test LLM analysis with valid JSON response."""
        mock_client = Mock()
        mock_stream = [Mock(text=json.dumps(mock_llm_response_natives))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        excel_text = "Sample Excel data"
        result = analyze_excel_with_llm(sample_excel_file, excel_text, mock_client)

        assert isinstance(result, dict)
        assert "structure_analysis" in result
        assert "data_extraction" in result
        assert "entity_identification" in result

    def test_analyze_with_streaming_response(self, sample_excel_file):
        """Test LLM analysis with chunked streaming response."""
        mock_client = Mock()
        response_data = {"file_name": "test.xlsx", "structure": {"worksheets": []}}

        # Simulate chunked response
        json_str = json.dumps(response_data)
        chunk1 = Mock(text=json_str[:len(json_str)//2])
        chunk2 = Mock(text=json_str[len(json_str)//2:])

        mock_client.models.generate_content_stream.return_value = [chunk1, chunk2]

        result = analyze_excel_with_llm(sample_excel_file, "data", mock_client)

        assert result == response_data

    def test_analyze_with_markdown_json_response(self, sample_excel_file):
        """Test LLM analysis when response is wrapped in markdown code blocks."""
        mock_client = Mock()
        response_data = {"file_name": "test.xlsx", "structure": {}}
        markdown_response = f"```json\n{json.dumps(response_data)}\n```"

        mock_stream = [Mock(text=markdown_response)]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = analyze_excel_with_llm(sample_excel_file, "data", mock_client)

        assert result == response_data

    def test_analyze_with_invalid_json_response(self, sample_excel_file, capsys):
        """Test LLM analysis with invalid JSON response."""
        mock_client = Mock()
        mock_stream = [Mock(text="This is not valid JSON")]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = analyze_excel_with_llm(sample_excel_file, "data", mock_client)

        # Should return error structure
        assert "error" in result
        assert "raw_response" in result
        assert result["file_name"] == sample_excel_file.name

    def test_analyze_prompt_includes_data(self, sample_excel_file):
        """Test that analysis prompt includes the Excel data."""
        mock_client = Mock()
        mock_stream = [Mock(text='{"file_name": "test.xlsx"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream

        excel_text = "UNIQUE_TEST_DATA_12345"
        analyze_excel_with_llm(sample_excel_file, excel_text, mock_client)

        # Check that generate_content_stream was called
        assert mock_client.models.generate_content_stream.called
        call_args = mock_client.models.generate_content_stream.call_args

        # The prompt should be in the contents
        contents = call_args.kwargs['contents']
        assert len(contents) > 0
        # Check that our unique data is in the prompt
        prompt_text = contents[0].parts[0].text
        assert "UNIQUE_TEST_DATA_12345" in prompt_text

    def test_analyze_uses_correct_model(self, sample_excel_file):
        """Test that correct model is specified."""
        mock_client = Mock()
        mock_stream = [Mock(text='{"file_name": "test.xlsx"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream

        analyze_excel_with_llm(sample_excel_file, "data", mock_client)

        call_args = mock_client.models.generate_content_stream.call_args
        assert call_args.kwargs['model'] == 'gemini-2.5-pro'

    def test_analyze_with_empty_chunks(self, sample_excel_file):
        """Test handling of empty chunks in stream."""
        mock_client = Mock()
        response_data = {"file_name": "test.xlsx"}

        # Some chunks with no text
        chunk1 = Mock(text=None)
        chunk2 = Mock(text=json.dumps(response_data))
        chunk3 = Mock(text=None)

        mock_client.models.generate_content_stream.return_value = [chunk1, chunk2, chunk3]

        result = analyze_excel_with_llm(sample_excel_file, "data", mock_client)

        assert result == response_data


# ============================================================================
# TESTS: process_single_excel()
# ============================================================================

@pytest.mark.unit
@pytest.mark.natives
class TestProcessSingleExcel:
    """Tests for single Excel file processing."""

    def test_process_single_excel_creates_output(self, sample_excel_file, temp_dir):
        """Test that processing creates output JSON file."""
        mock_client = Mock()
        response = {"file_name": sample_excel_file.name, "structure": {}}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        process_single_excel(sample_excel_file, temp_dir, mock_client, skip_existing=False)

        # Check output file created
        output_file = sample_excel_file.parent / f"{sample_excel_file.stem}_analysis.json"
        assert output_file.exists()

        # Check content
        with open(output_file) as f:
            data = json.load(f)
        assert "file_name" in data

    def test_process_single_excel_adds_metadata(self, sample_excel_file, temp_dir):
        """Test that processing adds file_path and house_oversight_id."""
        # Create Excel file with HOUSE_OVERSIGHT ID in name
        excel_path = temp_dir / "HOUSE_OVERSIGHT_010477.xlsx"
        pd.DataFrame({'A': [1, 2]}).to_excel(excel_path, index=False, engine='openpyxl')

        mock_client = Mock()
        response = {"file_name": excel_path.name}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        process_single_excel(excel_path, temp_dir, mock_client, skip_existing=False)

        output_file = excel_path.parent / f"{excel_path.stem}_analysis.json"
        with open(output_file) as f:
            data = json.load(f)

        assert "file_path" in data
        assert "house_oversight_id" in data
        assert data["house_oversight_id"] == "010477"

    def test_process_single_excel_skip_existing(self, sample_excel_file, temp_dir, capsys):
        """Test skip_existing flag."""
        # Create existing output file
        output_file = sample_excel_file.parent / f"{sample_excel_file.stem}_analysis.json"
        output_file.write_text('{"existing": true}')

        mock_client = Mock()

        # Should skip
        process_single_excel(sample_excel_file, temp_dir, mock_client, skip_existing=True)

        # Client should not be called
        assert not mock_client.models.generate_content_stream.called

        # Output should still be old content
        with open(output_file) as f:
            data = json.load(f)
        assert data == {"existing": True}

    def test_process_single_excel_error_handling(self, temp_dir, capsys):
        """Test error handling for processing failures."""
        excel_path = temp_dir / "test.xlsx"
        pd.DataFrame({'A': [1]}).to_excel(excel_path, index=False, engine='openpyxl')

        mock_client = Mock()
        # Simulate error
        mock_client.models.generate_content_stream.side_effect = Exception("API Error")

        # Should not raise, but print error
        process_single_excel(excel_path, temp_dir, mock_client, skip_existing=False)

        captured = capsys.readouterr()
        assert "ERROR" in captured.err

    def test_process_single_excel_output_location(self, sample_excel_file, temp_dir):
        """Test that output is saved in same directory as Excel file."""
        mock_client = Mock()
        response = {"file_name": sample_excel_file.name}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        # Pass different output_dir
        different_dir = temp_dir / "different"
        different_dir.mkdir()

        process_single_excel(sample_excel_file, different_dir, mock_client, skip_existing=False)

        # Output should be next to Excel file, not in different_dir
        output_file = sample_excel_file.parent / f"{sample_excel_file.stem}_analysis.json"
        assert output_file.exists()
        assert not (different_dir / f"{sample_excel_file.stem}_analysis.json").exists()


# ============================================================================
# TESTS: process_natives()
# ============================================================================

@pytest.mark.unit
@pytest.mark.natives
class TestProcessNatives:
    """Tests for batch natives processing."""

    def test_process_natives_requires_api_key(self, temp_dir, mock_env_no_api_key):
        """Test that process_natives requires GEMINI_API_KEY."""
        with pytest.raises(SystemExit):
            process_natives(temp_dir, temp_dir, skip_existing=False)

    @patch('batch7_process_natives.genai.Client')
    def test_process_natives_finds_excel_files(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that process_natives finds all Excel files."""
        # Create test Excel files
        (temp_dir / "file1.xlsx").touch()
        (temp_dir / "file2.xls").touch()
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "file3.xlsx").touch()

        mock_client = Mock()
        mock_stream = [Mock(text='{"file_name": "test.xlsx"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        with patch('batch7_process_natives.process_single_excel') as mock_process:
            process_natives(temp_dir, temp_dir, skip_existing=False)

            # Should find all 3 files
            assert mock_process.call_count == 3

    @patch('batch7_process_natives.genai.Client')
    def test_process_natives_no_files(self, mock_genai, temp_dir, mock_env_with_api_key, capsys):
        """Test behavior when no Excel files found."""
        mock_client = Mock()
        mock_genai.return_value = mock_client

        process_natives(temp_dir, temp_dir, skip_existing=False)

        captured = capsys.readouterr()
        assert "No Excel files found" in captured.out

    @patch('batch7_process_natives.genai.Client')
    def test_process_natives_skip_existing(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test skip_existing flag propagates to process_single_excel."""
        excel_path = temp_dir / "test.xlsx"
        pd.DataFrame({'A': [1]}).to_excel(excel_path, index=False, engine='openpyxl')

        mock_client = Mock()
        mock_stream = [Mock(text='{"file_name": "test.xlsx"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        with patch('batch7_process_natives.process_single_excel') as mock_process:
            process_natives(temp_dir, temp_dir, skip_existing=True)

            # Check that skip_existing was passed
            call_args = mock_process.call_args
            assert call_args.args[3] == True  # skip_existing parameter

    @patch('batch7_process_natives.genai.Client')
    def test_process_natives_creates_client(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that Gemini client is created with API key."""
        excel_path = temp_dir / "test.xlsx"
        excel_path.touch()

        mock_client = Mock()
        mock_stream = [Mock(text='{"file_name": "test.xlsx"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        with patch('batch7_process_natives.process_single_excel'):
            process_natives(temp_dir, temp_dir, skip_existing=False)

        # Check client was created with API key
        mock_genai.assert_called_once_with(api_key='test-api-key-12345')


# ============================================================================
# TESTS: Prompt and Constants
# ============================================================================

@pytest.mark.unit
@pytest.mark.natives
class TestConstants:
    """Tests for constants and prompts."""

    def test_prompt_structure(self):
        """Test that prompt has expected structure."""
        assert "STRUCTURE ANALYSIS" in PROMPT_EXCEL_ANALYSIS
        assert "DATA EXTRACTION" in PROMPT_EXCEL_ANALYSIS
        assert "RELATIONSHIP MAPPING" in PROMPT_EXCEL_ANALYSIS
        assert "OUTPUT FORMAT" in PROMPT_EXCEL_ANALYSIS
        assert "STRICT JSON" in PROMPT_EXCEL_ANALYSIS

    def test_prompt_json_schema(self):
        """Test that prompt includes JSON schema."""
        assert "file_name" in PROMPT_EXCEL_ANALYSIS
        assert "structure" in PROMPT_EXCEL_ANALYSIS
        assert "entities" in PROMPT_EXCEL_ANALYSIS
        assert "relationships" in PROMPT_EXCEL_ANALYSIS
        assert "confidence" in PROMPT_EXCEL_ANALYSIS


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.natives
class TestNativesIntegration:
    """Integration tests for complete workflow."""

    @patch('batch7_process_natives.genai.Client')
    def test_end_to_end_processing(self, mock_genai, temp_dir, sample_excel_data, mock_env_with_api_key):
        """Test complete end-to-end Excel processing."""
        # Setup
        natives_dir = temp_dir / "NATIVES"
        natives_dir.mkdir()
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Create test Excel file
        excel_path = natives_dir / "HOUSE_OVERSIGHT_010477.xlsx"
        sample_excel_data.to_excel(excel_path, index=False, engine='openpyxl')

        # Mock LLM response
        mock_client = Mock()
        response = {
            "file_name": "HOUSE_OVERSIGHT_010477.xlsx",
            "structure": {"worksheets": [{"name": "Sheet1"}]},
            "entities": {"people": ["John Doe"]},
            "relationships": []
        }
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        # Process
        process_natives(natives_dir, output_dir, skip_existing=False)

        # Verify
        output_file = excel_path.parent / "HOUSE_OVERSIGHT_010477_analysis.json"
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert data["file_name"] == "HOUSE_OVERSIGHT_010477.xlsx"
        assert "house_oversight_id" in data
        assert data["house_oversight_id"] == "010477"
        assert "file_path" in data

    @patch('batch7_process_natives.genai.Client')
    def test_multiple_files_processing(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test processing multiple Excel files."""
        natives_dir = temp_dir / "NATIVES"
        natives_dir.mkdir()

        # Create multiple Excel files
        for i in range(3):
            excel_path = natives_dir / f"test_{i}.xlsx"
            pd.DataFrame({'A': [i]}).to_excel(excel_path, index=False, engine='openpyxl')

        mock_client = Mock()
        mock_stream = [Mock(text='{"file_name": "test.xlsx"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        process_natives(natives_dir, temp_dir / "output", skip_existing=False)

        # All should have output files
        assert (natives_dir / "test_0_analysis.json").exists()
        assert (natives_dir / "test_1_analysis.json").exists()
        assert (natives_dir / "test_2_analysis.json").exists()
