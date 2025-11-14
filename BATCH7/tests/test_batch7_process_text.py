"""
Unit tests for batch7_process_text.py

Tests text processing functionality including:
- Text content extraction
- Story assembly and grouping
- Folder structure creation
- Multi-phase processing workflow
- Error handling and edge cases
"""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from batch7_process_text import (
    extract_text_content,
    assemble_stories,
    create_story_folders,
    process_text,
    PROMPT_TEXT_EXTRACTION,
    PROMPT_STORY_ASSEMBLY
)


# ============================================================================
# TESTS: extract_text_content()
# ============================================================================

@pytest.mark.unit
@pytest.mark.text
class TestExtractTextContent:
    """Tests for text content extraction."""

    def test_extract_with_valid_response(self, sample_text_file, mock_llm_response_text):
        """Test extraction with valid JSON response."""
        mock_client = Mock()
        mock_stream = [Mock(text=json.dumps(mock_llm_response_text))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = extract_text_content(sample_text_file, mock_client, save_per_file=False)

        assert isinstance(result, dict)
        assert result["file_name"] == sample_text_file.name
        assert "file_path" in result
        assert "processing_metadata" in result

    def test_extract_creates_per_file_json(self, sample_text_file):
        """Test that per-file JSON is created when enabled."""
        mock_client = Mock()
        response = {"file_name": sample_text_file.name, "content": {}}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        extract_text_content(sample_text_file, mock_client, save_per_file=True)

        # Check output file created
        output_file = sample_text_file.parent / f"{sample_text_file.stem}_extraction.json"
        assert output_file.exists()

    def test_extract_no_per_file_json(self, sample_text_file):
        """Test that per-file JSON is not created when disabled."""
        mock_client = Mock()
        response = {"file_name": sample_text_file.name, "content": {}}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        extract_text_content(sample_text_file, mock_client, save_per_file=False)

        output_file = sample_text_file.parent / f"{sample_text_file.stem}_extraction.json"
        assert not output_file.exists()

    def test_extract_reads_file_content(self, temp_dir):
        """Test that file content is read correctly."""
        text_path = temp_dir / "test.txt"
        text_path.write_text("UNIQUE_CONTENT_12345")

        mock_client = Mock()
        response = {"file_name": "test.txt"}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        extract_text_content(text_path, mock_client, save_per_file=False)

        # Check that generate_content_stream was called
        call_args = mock_client.models.generate_content_stream.call_args
        contents = call_args.kwargs['contents']
        prompt_text = contents[0].parts[0].text

        assert "UNIQUE_CONTENT_12345" in prompt_text

    def test_extract_file_not_found(self, temp_dir):
        """Test handling of non-existent file."""
        text_path = temp_dir / "nonexistent.txt"

        mock_client = Mock()

        result = extract_text_content(text_path, mock_client, save_per_file=False)

        assert "error" in result
        assert "Failed to read file" in result["error"]

    def test_extract_extracts_house_oversight_id(self, temp_dir):
        """Test extraction of HOUSE_OVERSIGHT ID from filename."""
        text_path = temp_dir / "HOUSE_OVERSIGHT_010477.txt"
        text_path.write_text("Test content")

        mock_client = Mock()
        response = {"file_name": "test.txt"}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = extract_text_content(text_path, mock_client, save_per_file=False)

        assert "house_oversight_id" in result
        assert result["house_oversight_id"] == "010477"

    def test_extract_handles_markdown_json(self, sample_text_file):
        """Test handling of markdown-wrapped JSON response."""
        mock_client = Mock()
        response = {"file_name": "test.txt", "content": {}}
        markdown_response = f"```json\n{json.dumps(response)}\n```"
        mock_stream = [Mock(text=markdown_response)]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = extract_text_content(sample_text_file, mock_client, save_per_file=False)

        assert result["file_name"] == "test.txt"

    def test_extract_handles_generic_code_block(self, sample_text_file):
        """Test handling of generic code block."""
        mock_client = Mock()
        response = {"file_name": "test.txt"}
        code_block = f"```\n{json.dumps(response)}\n```"
        mock_stream = [Mock(text=code_block)]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = extract_text_content(sample_text_file, mock_client, save_per_file=False)

        assert result["file_name"] == "test.txt"

    def test_extract_handles_extra_text_before_json(self, sample_text_file):
        """Test handling of extra text before JSON object."""
        mock_client = Mock()
        response = {"file_name": "test.txt"}
        prefixed_response = f"Here is the response:\n{json.dumps(response)}"
        mock_stream = [Mock(text=prefixed_response)]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = extract_text_content(sample_text_file, mock_client, save_per_file=False)

        assert result["file_name"] == "test.txt"

    def test_extract_invalid_json_creates_error_file(self, sample_text_file):
        """Test that invalid JSON creates error file."""
        mock_client = Mock()
        mock_stream = [Mock(text="This is not valid JSON")]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = extract_text_content(sample_text_file, mock_client, save_per_file=False)

        # Should create error file
        error_file = sample_text_file.parent / f"{sample_text_file.stem}_extraction_error.txt"
        assert error_file.exists()

        # Should return fallback structure
        assert "error" in result
        assert "content" in result
        assert "full_text" in result["content"]

    def test_extract_adds_processing_metadata(self, sample_text_file):
        """Test that processing metadata is added."""
        mock_client = Mock()
        response = {"file_name": "test.txt"}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = extract_text_content(sample_text_file, mock_client, save_per_file=False)

        assert "processing_metadata" in result
        assert "processed_at" in result["processing_metadata"]
        assert "model" in result["processing_metadata"]
        assert result["processing_metadata"]["model"] == "gemini-2.5-pro"

    def test_extract_uses_correct_model(self, sample_text_file):
        """Test that correct model is used."""
        mock_client = Mock()
        mock_stream = [Mock(text='{"file_name": "test.txt"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream

        extract_text_content(sample_text_file, mock_client, save_per_file=False)

        call_args = mock_client.models.generate_content_stream.call_args
        assert call_args.kwargs['model'] == 'gemini-2.5-pro'

    def test_extract_streaming_response(self, sample_text_file):
        """Test handling of chunked streaming response."""
        mock_client = Mock()
        response = {"file_name": "test.txt"}
        json_str = json.dumps(response)

        chunk1 = Mock(text=json_str[:len(json_str)//2])
        chunk2 = Mock(text=json_str[len(json_str)//2:])

        mock_client.models.generate_content_stream.return_value = [chunk1, chunk2]

        result = extract_text_content(sample_text_file, mock_client, save_per_file=False)

        assert result["file_name"] == "test.txt"


# ============================================================================
# TESTS: assemble_stories()
# ============================================================================

@pytest.mark.unit
@pytest.mark.text
class TestAssembleStories:
    """Tests for story assembly."""

    def test_assemble_with_valid_response(self, mock_llm_response_grouping):
        """Test story assembly with valid response."""
        mock_client = Mock()
        mock_stream = [Mock(text=json.dumps(mock_llm_response_grouping))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        text_extractions = [
            {"file_name": "file1.txt", "content": {"full_text": "Text 1"}, "metadata": {}, "entities": {}},
            {"file_name": "file2.txt", "content": {"full_text": "Text 2"}, "metadata": {}, "entities": {}}
        ]

        result = assemble_stories(text_extractions, mock_client)

        assert "stories" in result
        assert isinstance(result["stories"], list)

    def test_assemble_includes_all_extractions(self):
        """Test that all text extractions are included in prompt."""
        mock_client = Mock()
        mock_stream = [Mock(text='{"stories": []}')]
        mock_client.models.generate_content_stream.return_value = mock_stream

        text_extractions = [
            {"file_name": "UNIQUE_FILE_12345.txt", "content": {"full_text": "Text"}, "metadata": {}, "entities": {}}
        ]

        assemble_stories(text_extractions, mock_client)

        call_args = mock_client.models.generate_content_stream.call_args
        contents = call_args.kwargs['contents']
        prompt_text = contents[0].parts[0].text

        assert "UNIQUE_FILE_12345.txt" in prompt_text

    def test_assemble_with_invalid_json(self):
        """Test handling of invalid JSON response."""
        mock_client = Mock()
        mock_stream = [Mock(text="Not valid JSON")]
        mock_client.models.generate_content_stream.return_value = mock_stream

        text_extractions = [{"file_name": "file1.txt", "content": {"full_text": "Text"}, "metadata": {}, "entities": {}}]

        result = assemble_stories(text_extractions, mock_client)

        assert "stories" in result
        assert result["stories"] == []
        assert "error" in result

    def test_assemble_empty_extractions(self):
        """Test assembling with no text extractions."""
        mock_client = Mock()
        mock_stream = [Mock(text='{"stories": []}')]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = assemble_stories([], mock_client)

        assert "stories" in result

    def test_assemble_uses_correct_model(self):
        """Test that correct model is used."""
        mock_client = Mock()
        mock_stream = [Mock(text='{"stories": []}')]
        mock_client.models.generate_content_stream.return_value = mock_stream

        text_extractions = [{"file_name": "file1.txt", "content": {"full_text": "Text"}, "metadata": {}, "entities": {}}]

        assemble_stories(text_extractions, mock_client)

        call_args = mock_client.models.generate_content_stream.call_args
        assert call_args.kwargs['model'] == 'gemini-2.5-pro'

    def test_assemble_truncates_long_content(self):
        """Test that long content is truncated in prompt."""
        mock_client = Mock()
        mock_stream = [Mock(text='{"stories": []}')]
        mock_client.models.generate_content_stream.return_value = mock_stream

        long_text = "A" * 5000  # Very long text
        text_extractions = [
            {"file_name": "file1.txt", "content": {"full_text": long_text}, "metadata": {}, "entities": {}}
        ]

        assemble_stories(text_extractions, mock_client)

        call_args = mock_client.models.generate_content_stream.call_args
        contents = call_args.kwargs['contents']
        prompt_text = contents[0].parts[0].text

        # Should be truncated to 2000 chars
        assert prompt_text.count("A") <= 2000


# ============================================================================
# TESTS: create_story_folders()
# ============================================================================

@pytest.mark.unit
@pytest.mark.text
class TestCreateStoryFolders:
    """Tests for story folder creation."""

    def test_create_folders_structure(self, temp_dir):
        """Test that correct folder structure is created."""
        stories = {
            "stories": [
                {
                    "id": "S0001",
                    "title": "Test Story",
                    "text_files": ["file1.txt", "file2.txt"],
                    "assembled_text": "Combined narrative"
                }
            ]
        }

        create_story_folders(stories, temp_dir, {})

        # Check structure
        letters_dir = temp_dir / "letters"
        story_dir = letters_dir / "S0001"

        assert letters_dir.exists()
        assert story_dir.exists()
        assert (story_dir / "meta.json").exists()
        assert (story_dir / "text.txt").exists()
        assert (story_dir / "source_files.txt").exists()

    def test_create_folders_meta_content(self, temp_dir):
        """Test that meta.json contains story data."""
        story_data = {
            "id": "S0001",
            "title": "Test Story",
            "text_files": ["file1.txt"],
            "assembled_text": "Text"
        }

        stories = {"stories": [story_data]}

        create_story_folders(stories, temp_dir, {})

        meta_file = temp_dir / "letters" / "S0001" / "meta.json"
        with open(meta_file) as f:
            meta = json.load(f)

        assert meta["id"] == "S0001"
        assert meta["title"] == "Test Story"

    def test_create_folders_text_content(self, temp_dir):
        """Test that text.txt contains assembled text."""
        stories = {
            "stories": [
                {
                    "id": "S0001",
                    "title": "Test",
                    "text_files": [],
                    "assembled_text": "UNIQUE_TEXT_CONTENT_12345"
                }
            ]
        }

        create_story_folders(stories, temp_dir, {})

        text_file = temp_dir / "letters" / "S0001" / "text.txt"
        content = text_file.read_text()

        assert "UNIQUE_TEXT_CONTENT_12345" in content

    def test_create_folders_source_files(self, temp_dir):
        """Test that source_files.txt lists all files."""
        stories = {
            "stories": [
                {
                    "id": "S0001",
                    "title": "Test",
                    "text_files": ["file1.txt", "file2.txt", "file3.txt"],
                    "assembled_text": "Text"
                }
            ]
        }

        create_story_folders(stories, temp_dir, {})

        source_file = temp_dir / "letters" / "S0001" / "source_files.txt"
        content = source_file.read_text()

        assert "file1.txt" in content
        assert "file2.txt" in content
        assert "file3.txt" in content

    def test_create_folders_multiple_stories(self, temp_dir):
        """Test creation of multiple story folders."""
        stories = {
            "stories": [
                {"id": "S0001", "title": "Story 1", "text_files": [], "assembled_text": "Text 1"},
                {"id": "S0002", "title": "Story 2", "text_files": [], "assembled_text": "Text 2"},
                {"id": "S0003", "title": "Story 3", "text_files": [], "assembled_text": "Text 3"}
            ]
        }

        create_story_folders(stories, temp_dir, {})

        letters_dir = temp_dir / "letters"
        assert (letters_dir / "S0001").exists()
        assert (letters_dir / "S0002").exists()
        assert (letters_dir / "S0003").exists()

    def test_create_folders_no_stories(self, temp_dir):
        """Test handling of no stories."""
        stories = {"stories": []}

        create_story_folders(stories, temp_dir, {})

        letters_dir = temp_dir / "letters"
        assert letters_dir.exists()
        # Should have no subdirectories
        assert list(letters_dir.iterdir()) == []

    def test_create_folders_missing_fields(self, temp_dir):
        """Test handling of stories with missing fields."""
        stories = {
            "stories": [
                {"id": "S0001"}  # Missing other fields
            ]
        }

        # Should not raise
        create_story_folders(stories, temp_dir, {})

        story_dir = temp_dir / "letters" / "S0001"
        assert story_dir.exists()


# ============================================================================
# TESTS: process_text()
# ============================================================================

@pytest.mark.unit
@pytest.mark.text
class TestProcessText:
    """Tests for main text processing function."""

    def test_process_requires_api_key(self, temp_dir, mock_env_no_api_key):
        """Test that process_text requires GEMINI_API_KEY."""
        with pytest.raises(SystemExit):
            process_text(temp_dir, temp_dir, skip_existing=False)

    @patch('batch7_process_text.genai.Client')
    def test_process_no_files(self, mock_genai, temp_dir, mock_env_with_api_key, capsys):
        """Test behavior when no text files found."""
        mock_client = Mock()
        mock_genai.return_value = mock_client

        process_text(temp_dir, temp_dir, skip_existing=False)

        captured = capsys.readouterr()
        assert "No text files found" in captured.out

    @patch('batch7_process_text.genai.Client')
    def test_process_creates_output_files(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that processing creates expected output files."""
        # Create text files
        text_dir = temp_dir / "text"
        text_dir.mkdir()
        (text_dir / "file1.txt").write_text("Content 1")

        output_dir = temp_dir / "output"

        mock_client = Mock()
        extraction_response = {"file_name": "file1.txt", "content": {"full_text": "Content 1"}, "metadata": {}, "entities": {}}
        stories_response = {"stories": []}

        mock_stream1 = [Mock(text=json.dumps(extraction_response))]
        mock_stream2 = [Mock(text=json.dumps(stories_response))]

        mock_client.models.generate_content_stream.side_effect = [mock_stream1, mock_stream2]
        mock_genai.return_value = mock_client

        process_text(text_dir, output_dir, skip_existing=False)

        # Check outputs
        assert (output_dir / "text_extractions.json").exists()
        assert (output_dir / "stories_assembly.json").exists()
        assert (output_dir / "letters").exists()

    @patch('batch7_process_text.genai.Client')
    def test_process_skip_existing_extractions(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that skip_existing skips extraction phase."""
        text_dir = temp_dir / "text"
        text_dir.mkdir()
        (text_dir / "file1.txt").write_text("Content 1")

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Create existing extractions file
        existing_extractions = [{"file_name": "file1.txt", "content": {"full_text": "Existing"}, "metadata": {}, "entities": {}}]
        (output_dir / "text_extractions.json").write_text(json.dumps(existing_extractions))

        mock_client = Mock()
        stories_response = {"stories": []}
        mock_stream = [Mock(text=json.dumps(stories_response))]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        process_text(text_dir, output_dir, skip_existing=True)

        # Should only call once for stories, not for extraction
        assert mock_client.models.generate_content_stream.call_count == 1

    @patch('batch7_process_text.genai.Client')
    def test_process_skip_existing_stories(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that skip_existing skips story assembly."""
        text_dir = temp_dir / "text"
        text_dir.mkdir()
        (text_dir / "file1.txt").write_text("Content 1")

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Create existing files
        existing_extractions = [{"file_name": "file1.txt", "content": {"full_text": "Content"}, "metadata": {}, "entities": {}}]
        existing_stories = {"stories": []}
        (output_dir / "text_extractions.json").write_text(json.dumps(existing_extractions))
        (output_dir / "stories_assembly.json").write_text(json.dumps(existing_stories))

        mock_client = Mock()
        mock_genai.return_value = mock_client

        process_text(text_dir, output_dir, skip_existing=True)

        # Should not call LLM at all
        assert not mock_client.models.generate_content_stream.called

    @patch('batch7_process_text.genai.Client')
    def test_process_finds_text_files_recursively(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that text files are found recursively."""
        text_dir = temp_dir / "text"
        text_dir.mkdir()
        (text_dir / "file1.txt").write_text("Content 1")

        subdir = text_dir / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("Content 2")

        output_dir = temp_dir / "output"

        mock_client = Mock()
        extraction_response = {"file_name": "test.txt", "content": {"full_text": "Content"}, "metadata": {}, "entities": {}}
        stories_response = {"stories": []}

        # Need 3 responses: 2 extractions + 1 stories
        mock_stream1 = [Mock(text=json.dumps(extraction_response))]
        mock_stream2 = [Mock(text=json.dumps(extraction_response))]
        mock_stream3 = [Mock(text=json.dumps(stories_response))]

        mock_client.models.generate_content_stream.side_effect = [mock_stream1, mock_stream2, mock_stream3]
        mock_genai.return_value = mock_client

        process_text(text_dir, output_dir, skip_existing=False)

        # Should have found both files
        with open(output_dir / "text_extractions.json") as f:
            extractions = json.load(f)
        assert len(extractions) == 2

    @patch('batch7_process_text.genai.Client')
    def test_process_creates_client(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that Gemini client is created with API key."""
        text_dir = temp_dir / "text"
        text_dir.mkdir()
        (text_dir / "test.txt").write_text("Content")

        mock_client = Mock()
        extraction_response = {"file_name": "test.txt", "content": {"full_text": "Content"}, "metadata": {}, "entities": {}}
        stories_response = {"stories": []}

        mock_stream1 = [Mock(text=json.dumps(extraction_response))]
        mock_stream2 = [Mock(text=json.dumps(stories_response))]

        mock_client.models.generate_content_stream.side_effect = [mock_stream1, mock_stream2]
        mock_genai.return_value = mock_client

        process_text(text_dir, temp_dir / "output", skip_existing=False)

        mock_genai.assert_called_once_with(api_key='test-api-key-12345')


# ============================================================================
# TESTS: Prompts and Constants
# ============================================================================

@pytest.mark.unit
@pytest.mark.text
class TestConstants:
    """Tests for constants and prompts."""

    def test_extraction_prompt_structure(self):
        """Test extraction prompt has expected structure."""
        assert "CONTENT EXTRACTION" in PROMPT_TEXT_EXTRACTION
        assert "CONTEXT UNDERSTANDING" in PROMPT_TEXT_EXTRACTION
        assert "ENTITY EXTRACTION" in PROMPT_TEXT_EXTRACTION
        assert "OUTPUT FORMAT" in PROMPT_TEXT_EXTRACTION
        assert "STRICT JSON" in PROMPT_TEXT_EXTRACTION

    def test_assembly_prompt_structure(self):
        """Test assembly prompt has expected structure."""
        assert "GROUPING" in PROMPT_STORY_ASSEMBLY
        assert "NARRATIVE CONSTRUCTION" in PROMPT_STORY_ASSEMBLY
        assert "RELATIONSHIP MAPPING" in PROMPT_STORY_ASSEMBLY
        assert "OUTPUT FORMAT" in PROMPT_STORY_ASSEMBLY

    def test_extraction_prompt_json_schema(self):
        """Test extraction prompt includes JSON schema."""
        assert "file_name" in PROMPT_TEXT_EXTRACTION
        assert "content" in PROMPT_TEXT_EXTRACTION
        assert "metadata" in PROMPT_TEXT_EXTRACTION
        assert "entities" in PROMPT_TEXT_EXTRACTION

    def test_assembly_prompt_json_schema(self):
        """Test assembly prompt includes JSON schema."""
        assert "stories" in PROMPT_STORY_ASSEMBLY
        assert "unassigned_files" in PROMPT_STORY_ASSEMBLY
        assert "cross_story_connections" in PROMPT_STORY_ASSEMBLY


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.text
class TestTextIntegration:
    """Integration tests for complete workflow."""

    @patch('batch7_process_text.genai.Client')
    def test_end_to_end_processing(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test complete end-to-end text processing."""
        # Setup
        text_dir = temp_dir / "TEXT" / "001"
        text_dir.mkdir(parents=True)
        output_dir = temp_dir / "output" / "text_analysis"

        # Create test files
        (text_dir / "HOUSE_OVERSIGHT_010477.txt").write_text("Document 1 content")
        (text_dir / "HOUSE_OVERSIGHT_010478.txt").write_text("Document 2 content")

        # Mock responses
        mock_client = Mock()

        extraction1 = {
            "file_name": "HOUSE_OVERSIGHT_010477.txt",
            "content": {"full_text": "Document 1 content"},
            "metadata": {},
            "entities": {}
        }
        extraction2 = {
            "file_name": "HOUSE_OVERSIGHT_010478.txt",
            "content": {"full_text": "Document 2 content"},
            "metadata": {},
            "entities": {}
        }
        stories = {
            "stories": [
                {
                    "id": "S0001",
                    "title": "Combined Story",
                    "text_files": ["HOUSE_OVERSIGHT_010477.txt", "HOUSE_OVERSIGHT_010478.txt"],
                    "assembled_text": "Combined narrative"
                }
            ]
        }

        mock_stream1 = [Mock(text=json.dumps(extraction1))]
        mock_stream2 = [Mock(text=json.dumps(extraction2))]
        mock_stream3 = [Mock(text=json.dumps(stories))]

        mock_client.models.generate_content_stream.side_effect = [mock_stream1, mock_stream2, mock_stream3]
        mock_genai.return_value = mock_client

        # Process
        process_text(text_dir, output_dir, skip_existing=False)

        # Verify outputs
        assert (output_dir / "text_extractions.json").exists()
        assert (output_dir / "stories_assembly.json").exists()
        assert (output_dir / "letters" / "S0001").exists()
        assert (output_dir / "letters" / "S0001" / "meta.json").exists()
        assert (output_dir / "letters" / "S0001" / "text.txt").exists()
        assert (output_dir / "letters" / "S0001" / "source_files.txt").exists()

        # Check per-file extractions
        assert (text_dir / "HOUSE_OVERSIGHT_010477_extraction.json").exists()
        assert (text_dir / "HOUSE_OVERSIGHT_010478_extraction.json").exists()
