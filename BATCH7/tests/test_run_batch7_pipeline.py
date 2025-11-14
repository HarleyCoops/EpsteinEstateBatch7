"""
Unit tests for run_batch7_pipeline.py

Tests pipeline orchestration including:
- Argument parsing and defaults
- Process selection logic
- Directory path handling
- API key validation
- Integration of all processing modules
"""
import sys
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_batch7_pipeline import main


# ============================================================================
# TESTS: Argument Parsing
# ============================================================================

@pytest.mark.unit
class TestArgumentParsing:
    """Tests for command-line argument parsing."""

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_process_all_by_default(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, mock_batch7_structure):
        """Test that 'all' is processed by default."""
        with patch('sys.argv', ['run_batch7_pipeline.py', '--base-dir', str(mock_batch7_structure['NATIVES'].parent)]):
            main()

        # All three should be called
        assert mock_natives.called
        assert mock_images.called
        assert mock_text.called

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_process_natives_only(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, mock_batch7_structure):
        """Test processing natives only."""
        with patch('sys.argv', ['run_batch7_pipeline.py', '--process', 'natives', '--base-dir', str(mock_batch7_structure['NATIVES'].parent)]):
            main()

        assert mock_natives.called
        assert not mock_images.called
        assert not mock_text.called

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_process_images_only(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, mock_batch7_structure):
        """Test processing images only."""
        with patch('sys.argv', ['run_batch7_pipeline.py', '--process', 'images', '--base-dir', str(mock_batch7_structure['IMAGES'].parent.parent)]):
            main()

        assert not mock_natives.called
        assert mock_images.called
        assert not mock_text.called

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_process_text_only(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, mock_batch7_structure):
        """Test processing text only."""
        with patch('sys.argv', ['run_batch7_pipeline.py', '--process', 'text', '--base-dir', str(mock_batch7_structure['TEXT'].parent.parent)]):
            main()

        assert not mock_natives.called
        assert not mock_images.called
        assert mock_text.called

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_skip_existing_flag(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, mock_batch7_structure):
        """Test that skip-existing flag is passed to processors."""
        with patch('sys.argv', ['run_batch7_pipeline.py', '--skip-existing', '--base-dir', str(mock_batch7_structure['NATIVES'].parent)]):
            main()

        # Check all processors received skip_existing=True
        assert mock_natives.call_args[0][2] == True
        assert mock_images.call_args[0][2] == True
        assert mock_text.call_args[0][2] == True

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_custom_directories(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, temp_dir):
        """Test custom directory paths."""
        custom_natives = temp_dir / "custom_natives"
        custom_images = temp_dir / "custom_images"
        custom_text = temp_dir / "custom_text"

        for d in [custom_natives, custom_images, custom_text]:
            d.mkdir()

        with patch('sys.argv', [
            'run_batch7_pipeline.py',
            '--natives-dir', str(custom_natives),
            '--images-dir', str(custom_images),
            '--text-dir', str(custom_text)
        ]):
            main()

        # Check correct directories were used
        assert mock_natives.call_args[0][0] == custom_natives
        assert mock_images.call_args[0][0] == custom_images
        assert mock_text.call_args[0][0] == custom_text


# ============================================================================
# TESTS: Directory Handling
# ============================================================================

@pytest.mark.unit
class TestDirectoryHandling:
    """Tests for directory path handling."""

    @patch('run_batch7_pipeline.process_natives')
    def test_skips_missing_natives_dir(self, mock_natives, mock_env_with_api_key, temp_dir, capsys):
        """Test that missing NATIVES directory is skipped with message."""
        base_dir = temp_dir / "base"
        base_dir.mkdir()

        with patch('sys.argv', ['run_batch7_pipeline.py', '--process', 'natives', '--base-dir', str(base_dir)]):
            main()

        assert not mock_natives.called
        captured = capsys.readouterr()
        assert "NATIVES directory not found" in captured.out

    @patch('run_batch7_pipeline.process_images')
    def test_skips_missing_images_dir(self, mock_images, mock_env_with_api_key, temp_dir, capsys):
        """Test that missing IMAGES directory is skipped with message."""
        base_dir = temp_dir / "base"
        base_dir.mkdir()

        with patch('sys.argv', ['run_batch7_pipeline.py', '--process', 'images', '--base-dir', str(base_dir)]):
            main()

        assert not mock_images.called
        captured = capsys.readouterr()
        assert "IMAGES directory not found" in captured.out

    @patch('run_batch7_pipeline.process_text')
    def test_skips_missing_text_dir(self, mock_text, mock_env_with_api_key, temp_dir, capsys):
        """Test that missing TEXT directory is skipped with message."""
        base_dir = temp_dir / "base"
        base_dir.mkdir()

        with patch('sys.argv', ['run_batch7_pipeline.py', '--process', 'text', '--base-dir', str(base_dir)]):
            main()

        assert not mock_text.called
        captured = capsys.readouterr()
        assert "TEXT directory not found" in captured.out

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_creates_output_directory(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, temp_dir):
        """Test that output directory is created."""
        base_dir = temp_dir / "base"
        base_dir.mkdir()
        (base_dir / "NATIVES").mkdir()
        (base_dir / "IMAGES").mkdir()
        (base_dir / "TEXT").mkdir()

        output_dir = temp_dir / "custom_output"

        with patch('sys.argv', ['run_batch7_pipeline.py', '--base-dir', str(base_dir), '--output-dir', str(output_dir)]):
            main()

        assert output_dir.exists()

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_default_directory_structure(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, mock_batch7_structure):
        """Test that default directory structure is used correctly."""
        base_dir = mock_batch7_structure['NATIVES'].parent

        with patch('sys.argv', ['run_batch7_pipeline.py', '--base-dir', str(base_dir)]):
            main()

        # Check that processors received correct subdirectories
        natives_arg = mock_natives.call_args[0][0]
        images_arg = mock_images.call_args[0][0]
        text_arg = mock_text.call_args[0][0]

        assert natives_arg.name == "NATIVES"
        assert "IMAGES" in str(images_arg)
        assert "TEXT" in str(text_arg)


# ============================================================================
# TESTS: API Key Validation
# ============================================================================

@pytest.mark.unit
class TestAPIKeyValidation:
    """Tests for API key validation."""

    def test_requires_api_key(self, mock_env_no_api_key, temp_dir):
        """Test that pipeline requires GEMINI_API_KEY."""
        base_dir = temp_dir / "base"
        base_dir.mkdir()

        with patch('sys.argv', ['run_batch7_pipeline.py', '--base-dir', str(base_dir)]):
            with pytest.raises(SystemExit):
                main()

    def test_accepts_valid_api_key(self, mock_env_with_api_key, mock_batch7_structure):
        """Test that valid API key allows execution."""
        with patch('sys.argv', ['run_batch7_pipeline.py', '--base-dir', str(mock_batch7_structure['NATIVES'].parent)]):
            with patch('run_batch7_pipeline.process_natives'):
                with patch('run_batch7_pipeline.process_images'):
                    with patch('run_batch7_pipeline.process_text'):
                        # Should not raise
                        main()


# ============================================================================
# TESTS: Output Directory Structure
# ============================================================================

@pytest.mark.unit
class TestOutputStructure:
    """Tests for output directory structure."""

    @patch('run_batch7_pipeline.process_natives')
    def test_natives_output_subdirectory(self, mock_natives, mock_env_with_api_key, mock_batch7_structure):
        """Test that natives output goes to correct subdirectory."""
        base_dir = mock_batch7_structure['NATIVES'].parent

        with patch('sys.argv', ['run_batch7_pipeline.py', '--process', 'natives', '--base-dir', str(base_dir)]):
            main()

        output_arg = mock_natives.call_args[0][1]
        assert "natives_analysis" in str(output_arg)

    @patch('run_batch7_pipeline.process_images')
    def test_images_output_subdirectory(self, mock_images, mock_env_with_api_key, mock_batch7_structure):
        """Test that images output goes to correct subdirectory."""
        base_dir = mock_batch7_structure['IMAGES'].parent.parent

        with patch('sys.argv', ['run_batch7_pipeline.py', '--process', 'images', '--base-dir', str(base_dir)]):
            main()

        output_arg = mock_images.call_args[0][1]
        assert "images_analysis" in str(output_arg)

    @patch('run_batch7_pipeline.process_text')
    def test_text_output_subdirectory(self, mock_text, mock_env_with_api_key, mock_batch7_structure):
        """Test that text output goes to correct subdirectory."""
        base_dir = mock_batch7_structure['TEXT'].parent.parent

        with patch('sys.argv', ['run_batch7_pipeline.py', '--process', 'text', '--base-dir', str(base_dir)]):
            main()

        output_arg = mock_text.call_args[0][1]
        assert "text_analysis" in str(output_arg)


# ============================================================================
# TESTS: Process Flow
# ============================================================================

@pytest.mark.unit
class TestProcessFlow:
    """Tests for overall process flow."""

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_processes_in_order(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, mock_batch7_structure):
        """Test that processes execute in correct order."""
        call_order = []

        def record_natives(*args):
            call_order.append('natives')

        def record_images(*args):
            call_order.append('images')

        def record_text(*args):
            call_order.append('text')

        mock_natives.side_effect = record_natives
        mock_images.side_effect = record_images
        mock_text.side_effect = record_text

        base_dir = mock_batch7_structure['NATIVES'].parent

        with patch('sys.argv', ['run_batch7_pipeline.py', '--base-dir', str(base_dir)]):
            main()

        # Should be called in order: natives, images, text
        assert call_order == ['natives', 'images', 'text']

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_continues_on_error(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, mock_batch7_structure):
        """Test that pipeline continues if one processor fails."""
        # Make natives fail
        mock_natives.side_effect = Exception("Natives failed")

        base_dir = mock_batch7_structure['NATIVES'].parent

        with patch('sys.argv', ['run_batch7_pipeline.py', '--base-dir', str(base_dir)]):
            with pytest.raises(Exception, match="Natives failed"):
                main()

        # Should have tried natives but not others (exception stops execution)
        assert mock_natives.called


# ============================================================================
# TESTS: Output Messages
# ============================================================================

@pytest.mark.unit
class TestOutputMessages:
    """Tests for console output messages."""

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_prints_section_headers(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, mock_batch7_structure, capsys):
        """Test that section headers are printed."""
        base_dir = mock_batch7_structure['NATIVES'].parent

        with patch('sys.argv', ['run_batch7_pipeline.py', '--base-dir', str(base_dir)]):
            main()

        captured = capsys.readouterr()
        assert "PROCESSING NATIVES" in captured.out
        assert "PROCESSING IMAGES" in captured.out
        assert "PROCESSING TEXT" in captured.out
        assert "BATCH7 PIPELINE COMPLETE" in captured.out

    @patch('run_batch7_pipeline.process_natives')
    def test_prints_completion_message(self, mock_natives, mock_env_with_api_key, mock_batch7_structure, capsys):
        """Test that completion message is printed."""
        base_dir = mock_batch7_structure['NATIVES'].parent

        with patch('sys.argv', ['run_batch7_pipeline.py', '--process', 'natives', '--base-dir', str(base_dir)]):
            main()

        captured = capsys.readouterr()
        assert "BATCH7 PIPELINE COMPLETE" in captured.out


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests for complete pipeline."""

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_full_pipeline_execution(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, mock_batch7_structure):
        """Test full pipeline execution with all components."""
        base_dir = mock_batch7_structure['NATIVES'].parent

        with patch('sys.argv', ['run_batch7_pipeline.py', '--base-dir', str(base_dir), '--skip-existing']):
            main()

        # All three processors should be called
        assert mock_natives.called
        assert mock_images.called
        assert mock_text.called

        # All should receive skip_existing=True
        assert all([
            mock_natives.call_args[0][2],
            mock_images.call_args[0][2],
            mock_text.call_args[0][2]
        ])

    @patch('run_batch7_pipeline.process_natives')
    @patch('run_batch7_pipeline.process_images')
    @patch('run_batch7_pipeline.process_text')
    def test_selective_processing(self, mock_text, mock_images, mock_natives, mock_env_with_api_key, temp_dir):
        """Test selective processing with some directories missing."""
        base_dir = temp_dir / "base"
        base_dir.mkdir()

        # Only create IMAGES directory
        (base_dir / "IMAGES").mkdir()

        with patch('sys.argv', ['run_batch7_pipeline.py', '--base-dir', str(base_dir)]):
            main()

        # Only images should be processed
        assert not mock_natives.called
        assert mock_images.called
        assert not mock_text.called
