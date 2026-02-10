import pytest
from fastapi.testclient import TestClient
from api.main import app
import os
import io
import json

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ledes-converter"


def test_invalid_file_extension():
    """Test rejection of non-DOCX files."""
    response = client.post(
        "/convert/docx-to-ledes",
        files={"file": ("test.pdf", b"fake content", "application/pdf")}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_empty_file():
    """Test rejection of empty files."""
    response = client.post(
        "/convert/docx-to-ledes",
        files={"file": ("test.docx", b"", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]


def test_file_too_large():
    """Test rejection of files exceeding size limit."""
    # Create a file larger than 10MB
    large_content = b"x" * (11 * 1024 * 1024)
    response = client.post(
        "/convert/docx-to-ledes",
        files={"file": ("large.docx", large_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert response.status_code == 413
    assert "too large" in response.json()["detail"]

def test_convert_docx_to_ledes_success():
    # Path to the sample file
    sample_file = "tests/fixtures/sample.docx"
    
    if not os.path.exists(sample_file):
        pytest.skip(f"Sample file not found at {sample_file}")

    with open(sample_file, "rb") as f:
        response = client.post(
            "/convert/docx-to-ledes",
            files={
                "file": (
                    "sample.docx",
                    f.read(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "ledes_content" in data
    
    # Check extracted content validation
    extracted = data["extracted_data"]
    assert extracted["client_id"] == "SALESFORCE"
    assert extracted["invoice_number"] == "4432"
    # Format might vary depending on locale parsing, but let's check basic structure
    assert extracted["invoice_total"] == 9900.0
    assert len(extracted["line_items"]) > 0
    
    # Check first line item description
    first_item = extracted["line_items"][0]
    assert "Draft and file a Special Appeal" in first_item["description"]
    assert first_item["amount"] == 1200.0

    # Check LEDES content format (Pipe delimited)
    ledes_lines = data["ledes_content"].split('\n')
    assert len(ledes_lines) > 1
    assert "INVOICE_DATE|INVOICE_NUMBER|CLIENT_ID|LAW_FIRM_ID" in ledes_lines[0] # Header check
    assert "SALESFORCE" in ledes_lines[1] # Client ID check
    assert "LITIGATION-BRAZIL" in ledes_lines[1] # Matter ID check
    assert "9900.00" in ledes_lines[1] # Total check


def test_convert_with_config():
    """Test conversion with custom LEDES configuration."""
    sample_file = "tests/fixtures/sample.docx"

    if not os.path.exists(sample_file):
        pytest.skip(f"Sample file not found at {sample_file}")

    config_data = {
        "law_firm_id": "ACME-LAW-001",
        "law_firm_name": "ACME Legal Services",
        "client_id": "CLIENT-XYZ-789",
        "client_name": "XYZ Corporation",
        "matter_id": "MATTER-ABC-123",
        "matter_name": "Contract Dispute 2024"
    }

    with open(sample_file, "rb") as f:
        response = client.post(
            "/convert/docx-to-ledes",
            files={
                "file": (
                    "sample.docx",
                    f.read(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            data={"config": json.dumps(config_data)}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Verify config values override defaults
    extracted = data["extracted_data"]
    assert extracted["client_id"] == "CLIENT-XYZ-789"
    assert extracted["matter_id"] == "MATTER-ABC-123"

    # Check LEDES content includes law_firm_id
    ledes_lines = data["ledes_content"].split('\n')
    assert "LAW_FIRM_ID" in ledes_lines[0] # Header
    assert "ACME-LAW-001" in ledes_lines[1] # First data line should have law_firm_id
    assert "CLIENT-XYZ-789" in ledes_lines[1]
    assert "MATTER-ABC-123" in ledes_lines[1]


def test_convert_with_invalid_config_json():
    """Test conversion with malformed JSON config."""
    sample_file = "tests/fixtures/sample.docx"

    if not os.path.exists(sample_file):
        pytest.skip(f"Sample file not found at {sample_file}")

    with open(sample_file, "rb") as f:
        response = client.post(
            "/convert/docx-to-ledes",
            files={
                "file": (
                    "sample.docx",
                    f.read(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            data={"config": "invalid json {"}
        )

    assert response.status_code == 400
    assert "Invalid JSON" in response.json()["detail"]


def test_convert_with_missing_required_config_fields():
    """Test conversion with incomplete config (missing required fields)."""
    sample_file = "tests/fixtures/sample.docx"

    if not os.path.exists(sample_file):
        pytest.skip(f"Sample file not found at {sample_file}")

    # Missing required fields: law_firm_name, matter_id
    incomplete_config = {
        "law_firm_id": "ACME-LAW-001",
        "client_id": "CLIENT-XYZ-789"
    }

    with open(sample_file, "rb") as f:
        response = client.post(
            "/convert/docx-to-ledes",
            files={
                "file": (
                    "sample.docx",
                    f.read(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            data={"config": json.dumps(incomplete_config)}
        )

    assert response.status_code == 400
    assert "Invalid config data" in response.json()["detail"]


def test_ledes_1998b_format_compliance():
    """
    Test that generated LEDES output complies with LEDES 1998B specification:
    - Line 1: LEDES1998B[]
    - Line 2: Header with 24 ALL CAPS field names ending with []
    - Lines 3+: Data rows with 24 fields each ending with []
    - Pipe-delimited
    """
    sample_file = "tests/fixtures/sample.docx"

    if not os.path.exists(sample_file):
        pytest.skip(f"Sample file not found at {sample_file}")

    config_data = {
        "law_firm_id": "ACME-LAW-001",
        "law_firm_name": "ACME Legal Services",
        "client_id": "CLIENT-XYZ-789",
        "matter_id": "MATTER-ABC-123",
        "client_matter_id": "CLT-MTR-456"
    }

    with open(sample_file, "rb") as f:
        response = client.post(
            "/convert/docx-to-ledes",
            files={
                "file": (
                    "sample.docx",
                    f.read(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            data={"config": json.dumps(config_data)}
        )

    assert response.status_code == 200
    data = response.json()
    ledes_lines = data["ledes_content"].split('\n')

    # Test 1: First line must be LEDES1998B[]
    assert ledes_lines[0] == "LEDES1998B[]", "Line 1 must be LEDES1998B[]"

    # Test 2: Second line is header with 24 fields
    header = ledes_lines[1]
    assert header.endswith("[]"), "Header must end with []"
    header_fields = header[:-2].split('|')  # Remove [] and split
    assert len(header_fields) == 24, f"Header must have 24 fields, got {len(header_fields)}"

    # Test 3: Verify exact field order from spec
    expected_fields = [
        "INVOICE_DATE", "INVOICE_NUMBER", "CLIENT_ID", "LAW_FIRM_MATTER_ID", "INVOICE_TOTAL",
        "BILLING_START_DATE", "BILLING_END_DATE", "INVOICE_DESCRIPTION", "LINE_ITEM_NUMBER",
        "EXP/FEE/INV_ADJ_TYPE", "LINE_ITEM_NUMBER_OF_UNITS", "LINE_ITEM_ADJUSTMENT_AMOUNT",
        "LINE_ITEM_TOTAL", "LINE_ITEM_DATE", "LINE_ITEM_TASK_CODE", "LINE_ITEM_EXPENSE_CODE",
        "LINE_ITEM_ACTIVITY_CODE", "TIMEKEEPER_ID", "LINE_ITEM_DESCRIPTION", "LAW_FIRM_ID",
        "LINE_ITEM_UNIT_COST", "TIMEKEEPER_NAME", "TIMEKEEPER_CLASSIFICATION", "CLIENT_MATTER_ID"
    ]
    assert header_fields == expected_fields, "Header fields must match spec exactly"

    # Test 4: All data rows must have 24 fields and end with []
    for i, line in enumerate(ledes_lines[2:], start=3):
        assert line.endswith("[]"), f"Line {i} must end with []"
        data_fields = line[:-2].split('|')  # Remove [] and split
        assert len(data_fields) == 24, f"Line {i} must have 24 fields, got {len(data_fields)}"

    # Test 5: Verify config values appear in correct positions
    first_data_line = ledes_lines[2][:-2].split('|')
    assert first_data_line[2] == "CLIENT-XYZ-789", "CLIENT_ID should be in position 3"
    assert first_data_line[3] == "MATTER-ABC-123", "LAW_FIRM_MATTER_ID should be in position 4"
    assert first_data_line[19] == "ACME-LAW-001", "LAW_FIRM_ID should be in position 20"
    assert first_data_line[23] == "CLT-MTR-456", "CLIENT_MATTER_ID should be in position 24"

    # Test 6: Verify EXP/FEE/INV_ADJ_TYPE is "F" (Fee)
    assert first_data_line[9] == "F", "EXP/FEE/INV_ADJ_TYPE should be 'F' for fees"

    print("\n=== LEDES 1998B Format Sample ===")
    print("\n".join(ledes_lines[:4]))  # Print first 4 lines for visual verification


def test_ledes_ascii_and_special_char_sanitization():
    """
    Test that LEDES output sanitizes non-ASCII characters and reserved characters.

    LEDES 1998B Requirements:
    - ASCII encoding only
    - No pipe characters (|) in field values
    - No bracket characters ([]) in field values
    """
    from api.main import sanitize_ledes_field, format_ledes_currency

    # Test ASCII-only enforcement
    assert sanitize_ledes_field("Hello café") == "Hello caf"  # é removed
    assert sanitize_ledes_field("São Paulo") == "So Paulo"  # ã removed
    assert sanitize_ledes_field("Test™") == "Test"  # ™ removed

    # Test pipe character removal
    assert sanitize_ledes_field("Amount | Total") == "Amount  Total"
    assert sanitize_ledes_field("A|B|C") == "ABC"

    # Test bracket character removal
    assert sanitize_ledes_field("Test [note]") == "Test note"
    assert sanitize_ledes_field("Amount []") == "Amount "

    # Test combined issues
    assert sanitize_ledes_field("São Paulo | Brazil [2024]") == "So Paulo  Brazil 2024"

    # Test currency formatting
    assert format_ledes_currency(1234.56) == "1234.56"
    assert format_ledes_currency(0.5) == "0.50"
    assert format_ledes_currency(99999999999999.99) == "99999999999999.99"  # Max valid

    # Test currency limit (14 digits before decimal)
    assert format_ledes_currency(999999999999999.99) == ""  # 15 digits, exceeds limit

    # Test negative amounts
    assert format_ledes_currency(-100.00) == ""  # Negative not allowed