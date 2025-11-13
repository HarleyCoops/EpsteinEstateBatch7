"""
Unit tests for batch7_process_images.py

Tests image processing functionality including:
- Image analysis with vision LLM
- OCR extraction and structured data
- Single image processing
- Batch directory processing
- Error handling and edge cases
"""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from batch7_process_images import (
    analyze_image_with_llm,
    process_single_image,
    process_images,
    PROMPT_IMAGE_ANALYSIS
)


# ============================================================================
# TESTS: analyze_image_with_llm()
# ============================================================================

@pytest.mark.unit
@pytest.mark.images
class TestAnalyzeImageWithLLM:
    """Tests for LLM image analysis."""

    def test_analyze_with_valid_response(self, sample_image_file, mock_llm_response_images):
        """Test image analysis with valid JSON response."""
        mock_client = Mock()

        # Mock file upload
        mock_file = Mock()
        mock_file.uri = "file://test-uri"
        mock_file.mime_type = "image/jpeg"
        mock_client.files.upload.return_value = mock_file

        # Mock response
        mock_stream = [Mock(text=json.dumps(mock_llm_response_images))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = analyze_image_with_llm(sample_image_file, mock_client)

        assert isinstance(result, dict)
        assert result["file_name"] == sample_image_file.name
        assert "file_path" in result
        assert "house_oversight_id" in result

    def test_analyze_uploads_image(self, sample_image_file):
        """Test that image file is uploaded."""
        mock_client = Mock()

        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        mock_stream = [Mock(text='{"file_name": "test.jpg"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream

        analyze_image_with_llm(sample_image_file, mock_client)

        # Check file was uploaded
        mock_client.files.upload.assert_called_once()
        call_args = mock_client.files.upload.call_args
        assert str(sample_image_file) in str(call_args)

    def test_analyze_uses_vision_model(self, sample_image_file):
        """Test that correct model is used for vision."""
        mock_client = Mock()

        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        mock_stream = [Mock(text='{"file_name": "test.jpg"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream

        analyze_image_with_llm(sample_image_file, mock_client)

        call_args = mock_client.models.generate_content_stream.call_args
        assert call_args.kwargs['model'] == 'gemini-2.5-pro'

    def test_analyze_extracts_house_oversight_id(self, temp_dir):
        """Test extraction of HOUSE_OVERSIGHT ID from filename."""
        img_path = temp_dir / "HOUSE_OVERSIGHT_010477.jpg"
        img = Image.new('RGB', (100, 100))
        img.save(img_path)

        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        response = {"file_name": "test.jpg", "image_analysis": {}}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = analyze_image_with_llm(img_path, mock_client)

        assert "house_oversight_id" in result
        assert result["house_oversight_id"] == "010477"

    def test_analyze_adds_processing_metadata(self, sample_image_file):
        """Test that processing metadata is added."""
        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        response = {"file_name": "test.jpg"}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = analyze_image_with_llm(sample_image_file, mock_client)

        assert "processing_metadata" in result
        assert "processed_at" in result["processing_metadata"]
        assert "model" in result["processing_metadata"]
        assert result["processing_metadata"]["model"] == "gemini-2.5-pro"

    def test_analyze_with_markdown_json(self, sample_image_file):
        """Test handling of markdown-wrapped JSON response."""
        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        response = {"file_name": "test.jpg", "image_analysis": {}}
        markdown_response = f"```json\n{json.dumps(response)}\n```"
        mock_stream = [Mock(text=markdown_response)]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = analyze_image_with_llm(sample_image_file, mock_client)

        assert result["file_name"] == "test.jpg"

    def test_analyze_with_invalid_json(self, sample_image_file, capsys):
        """Test handling of invalid JSON response."""
        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        mock_stream = [Mock(text="This is not valid JSON")]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = analyze_image_with_llm(sample_image_file, mock_client)

        assert "error" in result
        assert "raw_response" in result
        assert result["file_name"] == sample_image_file.name

    def test_analyze_with_exception(self, sample_image_file):
        """Test handling of exceptions during analysis."""
        mock_client = Mock()
        mock_client.files.upload.side_effect = Exception("Upload failed")

        result = analyze_image_with_llm(sample_image_file, mock_client)

        assert "error" in result
        assert result["file_name"] == sample_image_file.name
        assert "Upload failed" in result["error"]

    def test_analyze_streaming_response(self, sample_image_file):
        """Test handling of chunked streaming response."""
        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        response = {"file_name": "test.jpg", "image_analysis": {}}
        json_str = json.dumps(response)

        # Split into chunks
        chunk1 = Mock(text=json_str[:len(json_str)//2])
        chunk2 = Mock(text=json_str[len(json_str)//2:])

        mock_client.models.generate_content_stream.return_value = [chunk1, chunk2]

        result = analyze_image_with_llm(sample_image_file, mock_client)

        assert result["file_name"] == "test.jpg"

    def test_analyze_with_empty_chunks(self, sample_image_file):
        """Test handling of empty chunks in stream."""
        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        response = {"file_name": "test.jpg"}
        chunk1 = Mock(text=None)
        chunk2 = Mock(text=json.dumps(response))
        chunk3 = Mock(text=None)

        mock_client.models.generate_content_stream.return_value = [chunk1, chunk2, chunk3]

        result = analyze_image_with_llm(sample_image_file, mock_client)

        assert result["file_name"] == "test.jpg"

    def test_analyze_includes_prompt(self, sample_image_file):
        """Test that analysis includes the prompt."""
        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        mock_stream = [Mock(text='{"file_name": "test.jpg"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream

        analyze_image_with_llm(sample_image_file, mock_client)

        call_args = mock_client.models.generate_content_stream.call_args
        contents = call_args.kwargs['contents']

        # Should have both image and text prompt
        assert len(contents[0].parts) == 2

    def test_analyze_sets_relative_file_path(self, temp_dir):
        """Test that file_path is set as relative path."""
        # Create nested structure
        batch_dir = temp_dir / "BATCH7"
        images_dir = batch_dir / "IMAGES" / "001"
        images_dir.mkdir(parents=True)

        img_path = images_dir / "test.jpg"
        img = Image.new('RGB', (100, 100))
        img.save(img_path)

        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        response = {"file_name": "test.jpg"}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        result = analyze_image_with_llm(img_path, mock_client)

        assert "file_path" in result
        assert "IMAGES" in result["file_path"]


# ============================================================================
# TESTS: process_single_image()
# ============================================================================

@pytest.mark.unit
@pytest.mark.images
class TestProcessSingleImage:
    """Tests for single image processing."""

    def test_process_creates_json_output(self, sample_image_file):
        """Test that processing creates JSON output file."""
        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        response = {"file_name": sample_image_file.name, "image_analysis": {}}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        process_single_image(sample_image_file, mock_client, skip_existing=False)

        # Check output file created
        output_file = sample_image_file.parent / f"{sample_image_file.stem}.json"
        assert output_file.exists()

        # Check content
        with open(output_file) as f:
            data = json.load(f)
        assert "file_name" in data

    def test_process_output_location(self, sample_image_file):
        """Test that output is in same directory as image."""
        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        response = {"file_name": sample_image_file.name}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        process_single_image(sample_image_file, mock_client, skip_existing=False)

        output_file = sample_image_file.parent / f"{sample_image_file.stem}.json"
        assert output_file.exists()
        assert output_file.parent == sample_image_file.parent

    def test_process_skip_existing(self, sample_image_file, capsys):
        """Test skip_existing flag."""
        # Create existing output
        output_file = sample_image_file.parent / f"{sample_image_file.stem}.json"
        output_file.write_text('{"existing": true}')

        mock_client = Mock()

        process_single_image(sample_image_file, mock_client, skip_existing=True)

        # Client should not be called
        assert not mock_client.files.upload.called

        # Output should still be old content
        with open(output_file) as f:
            data = json.load(f)
        assert data == {"existing": True}

    def test_process_overwrites_when_not_skipping(self, sample_image_file):
        """Test that existing files are overwritten when not skipping."""
        output_file = sample_image_file.parent / f"{sample_image_file.stem}.json"
        output_file.write_text('{"existing": true}')

        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        response = {"file_name": sample_image_file.name, "new": True}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        process_single_image(sample_image_file, mock_client, skip_existing=False)

        # Should be new content
        with open(output_file) as f:
            data = json.load(f)
        assert "new" in data

    def test_process_error_handling(self, sample_image_file, capsys):
        """Test error handling during processing."""
        mock_client = Mock()
        mock_client.files.upload.side_effect = Exception("Upload error")

        # Should not raise
        process_single_image(sample_image_file, mock_client, skip_existing=False)

        captured = capsys.readouterr()
        assert "ERROR" in captured.err

    def test_process_json_encoding(self, temp_dir):
        """Test that JSON is saved with UTF-8 encoding."""
        img_path = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100))
        img.save(img_path)

        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        # Response with unicode characters
        response = {"file_name": "test.jpg", "text": "Café résumé"}
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream

        process_single_image(img_path, mock_client, skip_existing=False)

        output_file = img_path.parent / "test.json"
        with open(output_file, encoding='utf-8') as f:
            data = json.load(f)
        assert data["text"] == "Café résumé"


# ============================================================================
# TESTS: process_images()
# ============================================================================

@pytest.mark.unit
@pytest.mark.images
class TestProcessImages:
    """Tests for batch image processing."""

    def test_process_requires_api_key(self, temp_dir, mock_env_no_api_key):
        """Test that process_images requires GEMINI_API_KEY."""
        with pytest.raises(SystemExit):
            process_images(temp_dir, temp_dir, skip_existing=False)

    @patch('batch7_process_images.genai.Client')
    def test_process_finds_image_files(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that process_images finds all image files."""
        # Create test images
        (temp_dir / "file1.jpg").touch()
        (temp_dir / "file2.png").touch()
        (temp_dir / "file3.tiff").touch()
        (temp_dir / "file4.txt").touch()  # Not an image

        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file
        mock_stream = [Mock(text='{"file_name": "test.jpg"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        with patch('batch7_process_images.process_single_image') as mock_process:
            process_images(temp_dir, temp_dir, skip_existing=False)

            # Should find 3 image files, not txt
            assert mock_process.call_count == 3

    @patch('batch7_process_images.genai.Client')
    def test_process_finds_images_recursively(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that images are found in subdirectories."""
        (temp_dir / "file1.jpg").touch()
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file2.jpg").touch()

        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file
        mock_stream = [Mock(text='{"file_name": "test.jpg"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        with patch('batch7_process_images.process_single_image') as mock_process:
            process_images(temp_dir, temp_dir, skip_existing=False)

            assert mock_process.call_count == 2

    @patch('batch7_process_images.genai.Client')
    def test_process_no_files(self, mock_genai, temp_dir, mock_env_with_api_key, capsys):
        """Test behavior when no image files found."""
        mock_client = Mock()
        mock_genai.return_value = mock_client

        process_images(temp_dir, temp_dir, skip_existing=False)

        captured = capsys.readouterr()
        assert "No image files found" in captured.out

    @patch('batch7_process_images.genai.Client')
    def test_process_creates_output_dir(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that output directory is created."""
        images_dir = temp_dir / "images"
        images_dir.mkdir()
        (images_dir / "test.jpg").touch()

        output_dir = temp_dir / "output"

        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file
        mock_stream = [Mock(text='{"file_name": "test.jpg"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        with patch('batch7_process_images.process_single_image'):
            process_images(images_dir, output_dir, skip_existing=False)

        assert output_dir.exists()

    @patch('batch7_process_images.genai.Client')
    def test_process_skip_existing(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test skip_existing flag propagates."""
        (temp_dir / "test.jpg").touch()

        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file
        mock_stream = [Mock(text='{"file_name": "test.jpg"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        with patch('batch7_process_images.process_single_image') as mock_process:
            process_images(temp_dir, temp_dir, skip_existing=True)

            call_args = mock_process.call_args
            assert call_args.args[2] == True  # skip_existing parameter

    @patch('batch7_process_images.genai.Client')
    def test_process_creates_client(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that Gemini client is created with API key."""
        (temp_dir / "test.jpg").touch()

        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file
        mock_stream = [Mock(text='{"file_name": "test.jpg"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        with patch('batch7_process_images.process_single_image'):
            process_images(temp_dir, temp_dir, skip_existing=False)

        mock_genai.assert_called_once_with(api_key='test-api-key-12345')

    @patch('batch7_process_images.genai.Client')
    def test_process_handles_all_image_extensions(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test that all supported image extensions are processed."""
        extensions = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp']
        for ext in extensions:
            (temp_dir / f"file{ext}").touch()

        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file
        mock_stream = [Mock(text='{"file_name": "test.jpg"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        with patch('batch7_process_images.process_single_image') as mock_process:
            process_images(temp_dir, temp_dir, skip_existing=False)

            assert mock_process.call_count == len(extensions)


# ============================================================================
# TESTS: Prompt and Constants
# ============================================================================

@pytest.mark.unit
@pytest.mark.images
class TestConstants:
    """Tests for constants and prompts."""

    def test_prompt_structure(self):
        """Test that prompt has expected structure."""
        assert "TEXT EXTRACTION" in PROMPT_IMAGE_ANALYSIS
        assert "VISUAL DESCRIPTION" in PROMPT_IMAGE_ANALYSIS
        assert "STRUCTURED EXTRACTION" in PROMPT_IMAGE_ANALYSIS
        assert "CONTEXT ANALYSIS" in PROMPT_IMAGE_ANALYSIS
        assert "OUTPUT FORMAT" in PROMPT_IMAGE_ANALYSIS

    def test_prompt_json_schema(self):
        """Test that prompt includes JSON schema."""
        assert "file_name" in PROMPT_IMAGE_ANALYSIS
        assert "image_analysis" in PROMPT_IMAGE_ANALYSIS
        assert "text_extraction" in PROMPT_IMAGE_ANALYSIS
        assert "structured_data" in PROMPT_IMAGE_ANALYSIS
        assert "confidence" in PROMPT_IMAGE_ANALYSIS


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.images
class TestImagesIntegration:
    """Integration tests for complete workflow."""

    @patch('batch7_process_images.genai.Client')
    def test_end_to_end_processing(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test complete end-to-end image processing."""
        # Setup
        images_dir = temp_dir / "IMAGES" / "001"
        images_dir.mkdir(parents=True)
        output_dir = temp_dir / "output"

        # Create test image
        img_path = images_dir / "HOUSE_OVERSIGHT_010477.jpg"
        img = Image.new('RGB', (800, 600), color='white')
        img.save(img_path)

        # Mock client
        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file

        response = {
            "file_name": "HOUSE_OVERSIGHT_010477.jpg",
            "image_analysis": {"type": "document"},
            "text_extraction": {"full_text": "Test document"},
            "structured_data": {"dates": ["2024-01-15"]}
        }
        mock_stream = [Mock(text=json.dumps(response))]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        # Process
        process_images(images_dir, output_dir, skip_existing=False)

        # Verify
        output_file = img_path.parent / "HOUSE_OVERSIGHT_010477.json"
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert data["file_name"] == "HOUSE_OVERSIGHT_010477.jpg"
        assert "house_oversight_id" in data
        assert data["house_oversight_id"] == "010477"
        assert "processing_metadata" in data

    @patch('batch7_process_images.genai.Client')
    def test_multiple_images_processing(self, mock_genai, temp_dir, mock_env_with_api_key):
        """Test processing multiple images."""
        images_dir = temp_dir / "IMAGES"
        images_dir.mkdir()

        # Create multiple images
        for i in range(3):
            img_path = images_dir / f"test_{i}.jpg"
            img = Image.new('RGB', (100, 100))
            img.save(img_path)

        mock_client = Mock()
        mock_file = Mock(uri="file://test", mime_type="image/jpeg")
        mock_client.files.upload.return_value = mock_file
        mock_stream = [Mock(text='{"file_name": "test.jpg"}')]
        mock_client.models.generate_content_stream.return_value = mock_stream
        mock_genai.return_value = mock_client

        process_images(images_dir, temp_dir / "output", skip_existing=False)

        # All should have output files
        assert (images_dir / "test_0.json").exists()
        assert (images_dir / "test_1.json").exists()
        assert (images_dir / "test_2.json").exists()
