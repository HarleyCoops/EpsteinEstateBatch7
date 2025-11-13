"""
Pytest configuration and shared fixtures for BATCH7 pipeline tests.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest
from PIL import Image
import pandas as pd


# ============================================================================
# DIRECTORY FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_batch7_structure(temp_dir):
    """Create a mock BATCH7 directory structure."""
    structure = {
        'NATIVES': temp_dir / 'NATIVES',
        'IMAGES': temp_dir / 'IMAGES' / '001',
        'TEXT': temp_dir / 'TEXT' / '001',
        'output': temp_dir / 'output',
        'output_natives': temp_dir / 'output' / 'natives_analysis',
        'output_text': temp_dir / 'output' / 'text_analysis',
        'output_letters': temp_dir / 'output' / 'text_analysis' / 'letters',
    }

    for path in structure.values():
        path.mkdir(parents=True, exist_ok=True)

    return structure


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_excel_data():
    """Sample Excel data as DataFrame."""
    return pd.DataFrame({
        'Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'Date': ['2024-01-15', '2024-02-20', '2024-03-10'],
        'Amount': [1000.00, 2500.50, 750.25],
        'Document': ['HOUSE_OVERSIGHT_010477', 'HOUSE_OVERSIGHT_010478', 'HOUSE_OVERSIGHT_010479']
    })


@pytest.fixture
def sample_excel_file(temp_dir, sample_excel_data):
    """Create a sample Excel file."""
    excel_path = temp_dir / 'sample_document.xlsx'
    sample_excel_data.to_excel(excel_path, index=False, engine='openpyxl')
    return excel_path


@pytest.fixture
def sample_image_file(temp_dir):
    """Create a sample image file."""
    img_path = temp_dir / 'HOUSE_OVERSIGHT_010477.jpg'
    img = Image.new('RGB', (800, 600), color='white')
    img.save(img_path)
    return img_path


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file."""
    text_path = temp_dir / 'HOUSE_OVERSIGHT_010477.txt'
    content = """
    Date: January 15, 2024
    From: John Doe
    To: Jane Smith

    Subject: Important Document

    This is a sample document for testing purposes.
    It contains multiple lines of text with various entities.

    Reference: HOUSE_OVERSIGHT_010477
    """
    text_path.write_text(content.strip())
    return text_path


# ============================================================================
# LLM MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm_response_natives():
    """Mock LLM response for natives (Excel) processing."""
    return {
        "structure_analysis": {
            "num_worksheets": 1,
            "worksheet_names": ["Sheet1"],
            "total_rows": 3,
            "total_columns": 4,
            "headers": ["Name", "Date", "Amount", "Document"],
            "data_types": {
                "Name": "text",
                "Date": "date",
                "Amount": "currency",
                "Document": "text"
            },
            "quality_assessment": "High quality structured data"
        },
        "data_extraction": {
            "records": [
                {
                    "Name": "John Doe",
                    "Date": "2024-01-15",
                    "Amount": 1000.00,
                    "Document": "HOUSE_OVERSIGHT_010477"
                },
                {
                    "Name": "Jane Smith",
                    "Date": "2024-02-20",
                    "Amount": 2500.50,
                    "Document": "HOUSE_OVERSIGHT_010478"
                },
                {
                    "Name": "Bob Johnson",
                    "Date": "2024-03-10",
                    "Amount": 750.25,
                    "Document": "HOUSE_OVERSIGHT_010479"
                }
            ]
        },
        "entity_identification": {
            "people": [
                {"name": "John Doe", "confidence": 0.95},
                {"name": "Jane Smith", "confidence": 0.95},
                {"name": "Bob Johnson", "confidence": 0.95}
            ],
            "organizations": [],
            "locations": [],
            "dates": ["2024-01-15", "2024-02-20", "2024-03-10"]
        },
        "relationship_mapping": {
            "connections": [
                {
                    "entity1": "John Doe",
                    "entity2": "HOUSE_OVERSIGHT_010477",
                    "relationship_type": "associated_with",
                    "confidence": 0.9
                }
            ]
        },
        "provenance": {
            "source_file": "sample_document.xlsx",
            "processing_date": "2024-01-15",
            "HOUSE_OVERSIGHT_IDs": ["HOUSE_OVERSIGHT_010477", "HOUSE_OVERSIGHT_010478", "HOUSE_OVERSIGHT_010479"]
        }
    }


@pytest.fixture
def mock_llm_response_images():
    """Mock LLM response for image processing."""
    return {
        "ocr_extraction": {
            "typed_text": "HOUSE OVERSIGHT COMMITTEE\nDocument Number: HOUSE_OVERSIGHT_010477",
            "handwritten_text": "Signature: John Doe",
            "printed_text": "Date: January 15, 2024",
            "confidence_scores": {
                "typed": 0.95,
                "handwritten": 0.75,
                "printed": 0.90
            }
        },
        "visual_analysis": {
            "image_type": "document_scan",
            "layout": "letter_format",
            "quality": "high",
            "orientation": "portrait",
            "color_mode": "color"
        },
        "structured_data": {
            "document_number": "HOUSE_OVERSIGHT_010477",
            "date": "2024-01-15",
            "names": ["John Doe"],
            "organizations": ["House Oversight Committee"]
        },
        "context_analysis": {
            "document_type": "official_letter",
            "sender": "House Oversight Committee",
            "recipient": "Unknown",
            "subject": "Document Review"
        },
        "provenance": {
            "source_file": "HOUSE_OVERSIGHT_010477.jpg",
            "processing_date": "2024-01-15",
            "HOUSE_OVERSIGHT_ID": "HOUSE_OVERSIGHT_010477"
        }
    }


@pytest.fixture
def mock_llm_response_text():
    """Mock LLM response for text processing."""
    return {
        "content_extraction": {
            "main_text": "This is a sample document for testing purposes.",
            "metadata": {
                "date": "2024-01-15",
                "sender": "John Doe",
                "recipient": "Jane Smith",
                "subject": "Important Document"
            }
        },
        "entity_identification": {
            "people": ["John Doe", "Jane Smith"],
            "organizations": [],
            "dates": ["2024-01-15"],
            "document_ids": ["HOUSE_OVERSIGHT_010477"]
        },
        "narrative_analysis": {
            "document_type": "letter",
            "tone": "formal",
            "key_topics": ["document review", "testing"]
        },
        "provenance": {
            "source_file": "HOUSE_OVERSIGHT_010477.txt",
            "processing_date": "2024-01-15",
            "HOUSE_OVERSIGHT_ID": "HOUSE_OVERSIGHT_010477"
        }
    }


@pytest.fixture
def mock_llm_response_grouping():
    """Mock LLM response for text grouping."""
    return {
        "stories": [
            {
                "story_id": "S0001",
                "title": "Document Review Correspondence",
                "pages": ["HOUSE_OVERSIGHT_010477", "HOUSE_OVERSIGHT_010478"],
                "participants": ["John Doe", "Jane Smith"],
                "date_range": "2024-01-15 to 2024-02-20",
                "summary": "Exchange of documents regarding review process",
                "confidence": 0.9
            }
        ]
    }


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client."""
    mock_client = Mock()
    mock_model = Mock()
    mock_response = Mock()

    # Setup response chain
    mock_response.text = json.dumps({"mock": "response"})
    mock_model.generate_content.return_value = mock_response
    mock_client.return_value = mock_model

    return mock_client


# ============================================================================
# ENVIRONMENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_env_with_api_key(monkeypatch):
    """Set mock GEMINI_API_KEY environment variable."""
    monkeypatch.setenv('GEMINI_API_KEY', 'test-api-key-12345')
    return 'test-api-key-12345'


@pytest.fixture
def mock_env_no_api_key(monkeypatch):
    """Remove GEMINI_API_KEY from environment."""
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)


# ============================================================================
# JSON SCHEMA FIXTURES
# ============================================================================

@pytest.fixture
def expected_natives_schema():
    """Expected JSON schema for natives processing output."""
    return {
        "required_keys": [
            "structure_analysis",
            "data_extraction",
            "entity_identification",
            "relationship_mapping",
            "provenance"
        ],
        "structure_analysis_keys": [
            "num_worksheets",
            "worksheet_names",
            "total_rows",
            "total_columns",
            "headers"
        ],
        "provenance_keys": [
            "source_file",
            "processing_date",
            "HOUSE_OVERSIGHT_IDs"
        ]
    }


@pytest.fixture
def expected_images_schema():
    """Expected JSON schema for image processing output."""
    return {
        "required_keys": [
            "ocr_extraction",
            "visual_analysis",
            "structured_data",
            "context_analysis",
            "provenance"
        ],
        "ocr_keys": [
            "typed_text",
            "handwritten_text",
            "printed_text",
            "confidence_scores"
        ],
        "provenance_keys": [
            "source_file",
            "processing_date",
            "HOUSE_OVERSIGHT_ID"
        ]
    }


@pytest.fixture
def expected_text_schema():
    """Expected JSON schema for text processing output."""
    return {
        "required_keys": [
            "content_extraction",
            "entity_identification",
            "narrative_analysis",
            "provenance"
        ],
        "provenance_keys": [
            "source_file",
            "processing_date",
            "HOUSE_OVERSIGHT_ID"
        ]
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_json_schema(data, schema):
    """Validate JSON data against expected schema."""
    for key in schema.get("required_keys", []):
        assert key in data, f"Missing required key: {key}"

    if "provenance_keys" in schema:
        assert "provenance" in data
        for key in schema["provenance_keys"]:
            assert key in data["provenance"], f"Missing provenance key: {key}"

    return True


def create_mock_llm_response(text_content):
    """Create a mock LLM response object."""
    mock_response = Mock()
    mock_response.text = text_content
    return mock_response
