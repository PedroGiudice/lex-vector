"""Testes para os endpoints novos do LEDES Converter (matters CRUD, validate, batch)
e para a extracao de task/activity codes no ledes_generator."""

import json
import os

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.ledes_generator import extract_ledes_data, generate_ledes_1998b


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_LEDES = (
    "LEDES1998B[]\n"
    "INVOICE_DATE|INVOICE_NUMBER|CLIENT_ID|LAW_FIRM_MATTER_ID|INVOICE_TOTAL|"
    "BILLING_START_DATE|BILLING_END_DATE|INVOICE_DESCRIPTION|LINE_ITEM_NUMBER|"
    "EXP/FEE/INV_ADJ_TYPE|LINE_ITEM_NUMBER_OF_UNITS|LINE_ITEM_ADJUSTMENT_AMOUNT|"
    "LINE_ITEM_TOTAL|LINE_ITEM_DATE|LINE_ITEM_TASK_CODE|LINE_ITEM_EXPENSE_CODE|"
    "LINE_ITEM_ACTIVITY_CODE|TIMEKEEPER_ID|LINE_ITEM_DESCRIPTION|LAW_FIRM_ID|"
    "LINE_ITEM_UNIT_COST|TIMEKEEPER_NAME|TIMEKEEPER_CLASSIFICATION|CLIENT_MATTER_ID[]\n"
    "20260115|4432|Salesforce|LS-2020-05805|1200.00|20260101|20260131|"
    "Legal Services|1|F|4.00||1200.00|20260115|L510||A103|CMR|"
    "Draft appeal|SF004554|300.00|RODRIGUES CARLOS|PARTNR|CLT-001[]"
)

SAMPLE_MATTER = {
    "matter_name": "Test Matter Generator",
    "matter_id": "LS-TEST-001",
    "client_matter_id": "CLT-GEN-001",
    "client_id": "TestCorp",
    "client_name": "Test Corporation",
    "law_firm_id": "TF001",
    "law_firm_name": "Test Firm LLP",
    "timekeeper_id": "TK01",
    "timekeeper_name": "DOE, JANE",
    "timekeeper_classification": "ASSOC",
    "unit_cost": 250.0,
    "default_task_code": "L510",
    "default_activity_code": "A103",
}


def _cleanup_matter(name: str) -> None:
    """Remove matter de teste se existir (ignora 404)."""
    client.delete(f"/matters/{name}")


# ---------------------------------------------------------------------------
# 1. extract_ledes_data retorna task_code e activity_code
# ---------------------------------------------------------------------------


class TestExtractWithTaskCodes:
    """Verifica que extract_ledes_data() retorna task_code e activity_code."""

    def test_draft_special_appeal(self) -> None:
        text = "Draft and file a Special Appeal US $1200"
        data = extract_ledes_data(text)

        assert len(data["line_items"]) == 1
        item = data["line_items"][0]
        assert item["task_code"] == "L510"
        assert item["activity_code"] == "A103"
        assert item["amount"] == 1200.0
        assert "Special Appeal" in item["description"]

    def test_multiple_items_have_codes(self) -> None:
        text = (
            "Draft and file a Special Appeal US $1200\n"
            "Settlement conference preparation US $800\n"
        )
        data = extract_ledes_data(text)

        assert len(data["line_items"]) == 2
        # Primeiro item: appeal + draft
        assert data["line_items"][0]["task_code"] == "L510"
        assert data["line_items"][0]["activity_code"] == "A103"
        # Segundo item: settlement + communication
        assert data["line_items"][1]["task_code"] == "L160"

    def test_no_match_returns_empty_codes(self) -> None:
        text = "Office supplies US $50"
        data = extract_ledes_data(text)

        assert len(data["line_items"]) == 1
        item = data["line_items"][0]
        assert item["task_code"] == ""
        assert item["activity_code"] == ""


# ---------------------------------------------------------------------------
# 2. generate_ledes_1998b inclui task codes no output
# ---------------------------------------------------------------------------


class TestGenerateIncludesTaskCodes:
    """Verifica que generate_ledes_1998b() coloca task/activity codes no LEDES."""

    def test_task_code_in_output(self) -> None:
        data = {
            "invoice_date": "20260115",
            "invoice_number": "9999",
            "client_id": "TESTCLIENT",
            "matter_id": "TEST-MATTER",
            "invoice_total": 1200.0,
            "line_items": [
                {
                    "description": "Draft appeal brief",
                    "amount": 1200.0,
                    "task_code": "L510",
                    "activity_code": "A103",
                }
            ],
        }
        ledes = generate_ledes_1998b(data)
        lines = ledes.split("\n")

        assert lines[0] == "LEDES1998B[]"
        # Header (line index 1), data row (line index 2)
        data_row = lines[2]
        fields = data_row.rstrip("[]").split("|")

        # Campo 15 = LINE_ITEM_TASK_CODE (indice 14)
        assert fields[14] == "L510"
        # Campo 17 = LINE_ITEM_ACTIVITY_CODE (indice 16)
        assert fields[16] == "A103"

    def test_empty_codes_when_unclassified(self) -> None:
        data = {
            "invoice_date": "20260115",
            "invoice_number": "9998",
            "client_id": "TESTCLIENT",
            "matter_id": "TEST-MATTER",
            "invoice_total": 50.0,
            "line_items": [
                {
                    "description": "Misc expense",
                    "amount": 50.0,
                    "task_code": "",
                    "activity_code": "",
                }
            ],
        }
        ledes = generate_ledes_1998b(data)
        lines = ledes.split("\n")
        fields = lines[2].rstrip("[]").split("|")

        assert fields[14] == ""
        assert fields[16] == ""


# ---------------------------------------------------------------------------
# 3. POST /validate
# ---------------------------------------------------------------------------


class TestValidateEndpoint:
    """Testa o endpoint POST /validate com conteudo valido e invalido."""

    def test_valid_ledes_content(self) -> None:
        response = client.post("/validate", data={"ledes_content": VALID_LEDES})

        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is True
        assert body["error_count"] == 0

    def test_invalid_first_line(self) -> None:
        bad_content = VALID_LEDES.replace("LEDES1998B[]", "WRONGHEADER[]", 1)
        response = client.post("/validate", data={"ledes_content": bad_content})

        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert body["error_count"] >= 1
        messages = [i["message"] for i in body["issues"]]
        assert any("Line 1 must be" in m for m in messages)

    def test_missing_required_field(self) -> None:
        # Remove INVOICE_NUMBER (segundo campo da data row)
        bad_content = VALID_LEDES.replace("|4432|", "||", 1)
        response = client.post("/validate", data={"ledes_content": bad_content})

        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert any(
            "INVOICE_NUMBER" in i["message"]
            for i in body["issues"]
            if i["severity"] == "error"
        )

    def test_non_ascii_in_data(self) -> None:
        bad_content = VALID_LEDES.replace("Draft appeal", "Draft apela\u00e7\u00e3o")
        response = client.post("/validate", data={"ledes_content": bad_content})

        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert any(
            "Non-ASCII" in i["message"]
            for i in body["issues"]
            if i["severity"] == "error"
        )


# ---------------------------------------------------------------------------
# 4. Matters CRUD via endpoints
# ---------------------------------------------------------------------------


class TestMattersCrud:
    """Testa GET/POST/PUT/DELETE /matters via endpoints HTTP."""

    def setup_method(self) -> None:
        _cleanup_matter(SAMPLE_MATTER["matter_name"])

    def teardown_method(self) -> None:
        _cleanup_matter(SAMPLE_MATTER["matter_name"])

    def test_list_matters(self) -> None:
        response = client.get("/matters")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        # O store faz seed com 3 matters
        assert len(body) >= 3

    def test_create_matter(self) -> None:
        response = client.post("/matters", json=SAMPLE_MATTER)
        assert response.status_code == 201
        body = response.json()
        assert body["matter_name"] == SAMPLE_MATTER["matter_name"]
        assert body["matter_id"] == "LS-TEST-001"
        assert body["unit_cost"] == 250.0
        assert body["created_at"] != ""

    def test_create_duplicate_returns_409(self) -> None:
        client.post("/matters", json=SAMPLE_MATTER)
        response = client.post("/matters", json=SAMPLE_MATTER)
        assert response.status_code == 409

    def test_get_matter(self) -> None:
        client.post("/matters", json=SAMPLE_MATTER)
        name = SAMPLE_MATTER["matter_name"]
        response = client.get(f"/matters/{name}")
        assert response.status_code == 200
        assert response.json()["matter_id"] == "LS-TEST-001"

    def test_get_nonexistent_returns_404(self) -> None:
        response = client.get("/matters/Nonexistent-XYZ-999")
        assert response.status_code == 404

    def test_update_matter(self) -> None:
        client.post("/matters", json=SAMPLE_MATTER)
        name = SAMPLE_MATTER["matter_name"]

        updated_data = {**SAMPLE_MATTER, "unit_cost": 500.0}
        response = client.put(f"/matters/{name}", json=updated_data)
        assert response.status_code == 200
        assert response.json()["unit_cost"] == 500.0

    def test_update_nonexistent_returns_404(self) -> None:
        response = client.put("/matters/Nonexistent-XYZ-999", json=SAMPLE_MATTER)
        assert response.status_code == 404

    def test_delete_matter(self) -> None:
        client.post("/matters", json=SAMPLE_MATTER)
        name = SAMPLE_MATTER["matter_name"]

        response = client.delete(f"/matters/{name}")
        assert response.status_code == 204

        # Confirma que foi removido
        response = client.get(f"/matters/{name}")
        assert response.status_code == 404

    def test_delete_nonexistent_returns_404(self) -> None:
        response = client.delete("/matters/Nonexistent-XYZ-999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# 5. POST /convert/batch
# ---------------------------------------------------------------------------


class TestBatchEndpoint:
    """Testa POST /convert/batch (requer DOCX reais -- skip se indisponivel)."""

    SAMPLE_FILE = "tests/fixtures/sample.docx"

    def test_batch_skips_without_fixture(self) -> None:
        if not os.path.exists(self.SAMPLE_FILE):
            pytest.skip("sample.docx nao disponivel para teste de batch")

        with open(self.SAMPLE_FILE, "rb") as f:
            content = f.read()

        response = client.post(
            "/convert/batch",
            files=[
                ("files", ("invoice1.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
                ("files", ("invoice2.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ],
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert body["successful"] + body["failed"] == 2

    def test_batch_rejects_non_docx(self) -> None:
        response = client.post(
            "/convert/batch",
            files=[
                ("files", ("bad.txt", b"not a docx", "text/plain")),
            ],
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["failed"] == 1
        assert body["results"][0]["status"] == "error"
        assert "Invalid file type" in body["results"][0]["error"]

    def test_batch_rejects_empty_file(self) -> None:
        response = client.post(
            "/convert/batch",
            files=[
                ("files", ("empty.docx", b"", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ],
        )
        assert response.status_code == 200
        body = response.json()
        assert body["failed"] == 1
        assert "Empty file" in body["results"][0]["error"]


# ---------------------------------------------------------------------------
# 6. Conversao com matter_name no config
# ---------------------------------------------------------------------------


class TestConvertWithMatterName:
    """Verifica que o endpoint de conversao aceita matter_name no config JSON."""

    SAMPLE_FILE = "tests/fixtures/sample.docx"

    def test_convert_with_matter_name(self) -> None:
        if not os.path.exists(self.SAMPLE_FILE):
            pytest.skip("sample.docx nao disponivel")

        # Usa um dos matters do seed
        config_data = {"matter_name": "CMR General Litigation Matters"}

        with open(self.SAMPLE_FILE, "rb") as f:
            response = client.post(
                "/convert/docx-to-ledes",
                files={
                    "file": (
                        "sample.docx",
                        f.read(),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                },
                data={"config": json.dumps(config_data)},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        # O matter "CMR General Litigation Matters" tem law_firm_id="SF004554"
        assert "SF004554" in body["ledes_content"]

    def test_convert_with_nonexistent_matter_name(self) -> None:
        if not os.path.exists(self.SAMPLE_FILE):
            pytest.skip("sample.docx nao disponivel")

        config_data = {"matter_name": "MATTER-QUE-NAO-EXISTE"}

        with open(self.SAMPLE_FILE, "rb") as f:
            response = client.post(
                "/convert/docx-to-ledes",
                files={
                    "file": (
                        "sample.docx",
                        f.read(),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                },
                data={"config": json.dumps(config_data)},
            )

        assert response.status_code == 404
        assert "Matter not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 7. POST /convert/structured
# ---------------------------------------------------------------------------


class TestConvertStructured:
    """Testa POST /convert/structured com dados de formulario."""

    def test_basic_structured_conversion(self) -> None:
        payload = {
            "matter_name": "CMR General Litigation Matters",
            "invoice_number": "INV-2026-001",
            "invoice_date": "20260115",
            "billing_start_date": "20260101",
            "billing_end_date": "20260131",
            "line_items": [
                {"description": "Draft appeal brief", "amount": 1200.0},
                {"description": "Settlement negotiation meeting", "amount": 800.0},
            ],
        }
        response = client.post("/convert/structured", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["filename"] == "structured-input"
        assert "LEDES1998B[]" in body["ledes_content"]
        # Matter config applied
        assert "SF004554" in body["ledes_content"]
        # Total calculated from items
        assert body["extracted_data"]["invoice_total"] == 2000.0
        assert len(body["extracted_data"]["line_items"]) == 2

    def test_auto_classifies_task_codes(self) -> None:
        payload = {
            "matter_name": "CMR General Litigation Matters",
            "invoice_number": "INV-2026-002",
            "invoice_date": "20260115",
            "line_items": [
                {"description": "Draft appeal brief", "amount": 500.0},
            ],
        }
        response = client.post("/convert/structured", json=payload)

        assert response.status_code == 200
        items = response.json()["extracted_data"]["line_items"]
        assert items[0]["task_code"] == "L510"
        assert items[0]["activity_code"] == "A103"

    def test_explicit_codes_override_auto(self) -> None:
        payload = {
            "matter_name": "CMR General Litigation Matters",
            "invoice_number": "INV-2026-003",
            "invoice_date": "20260115",
            "line_items": [
                {
                    "description": "Draft appeal brief",
                    "amount": 500.0,
                    "task_code": "L100",
                    "activity_code": "A101",
                },
            ],
        }
        response = client.post("/convert/structured", json=payload)

        assert response.status_code == 200
        items = response.json()["extracted_data"]["line_items"]
        assert items[0]["task_code"] == "L100"
        assert items[0]["activity_code"] == "A101"

    def test_nonexistent_matter_returns_404(self) -> None:
        payload = {
            "matter_name": "MATTER-QUE-NAO-EXISTE",
            "invoice_number": "INV-X",
            "invoice_date": "20260115",
            "line_items": [{"description": "Test", "amount": 100.0}],
        }
        response = client.post("/convert/structured", json=payload)
        assert response.status_code == 404

    def test_empty_line_items_rejected(self) -> None:
        payload = {
            "matter_name": "CMR General Litigation Matters",
            "invoice_number": "INV-X",
            "invoice_date": "20260115",
            "line_items": [],
        }
        response = client.post("/convert/structured", json=payload)
        assert response.status_code == 422

    def test_ledes_output_has_24_fields(self) -> None:
        payload = {
            "matter_name": "CMR General Litigation Matters",
            "invoice_number": "INV-2026-004",
            "invoice_date": "20260115",
            "line_items": [
                {"description": "Legal research on precedents", "amount": 750.0},
            ],
        }
        response = client.post("/convert/structured", json=payload)
        assert response.status_code == 200

        ledes = response.json()["ledes_content"]
        lines = ledes.strip().split("\n")
        assert lines[0] == "LEDES1998B[]"
        data_row = lines[2]
        fields = data_row.rstrip("[]").split("|")
        assert len(fields) == 24


# ---------------------------------------------------------------------------
# 8. POST /convert/text-to-ledes
# ---------------------------------------------------------------------------


class TestConvertTextToLedes:
    """Testa POST /convert/text-to-ledes com texto colado."""

    def test_basic_text_conversion(self) -> None:
        payload = {
            "text": (
                "Invoice # 5500\n"
                "Date of Issuance: January 15, 2026\n"
                "Draft appeal motion US $1200\n"
                "Settlement conference US $800\n"
                "Total Gross Amount: US $2000\n"
            ),
            "matter_name": "CMR General Litigation Matters",
        }
        response = client.post("/convert/text-to-ledes", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["filename"] == "text-input"
        assert "LEDES1998B[]" in body["ledes_content"]
        assert body["extracted_data"]["invoice_number"] == "5500"
        assert len(body["extracted_data"]["line_items"]) == 2
        # Matter config applied
        assert "SF004554" in body["ledes_content"]

    def test_text_without_matter(self) -> None:
        payload = {
            "text": (
                "Invoice # 5501\n"
                "Draft brief US $500\n"
            ),
        }
        response = client.post("/convert/text-to-ledes", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert len(body["extracted_data"]["line_items"]) == 1

    def test_text_no_line_items_returns_400(self) -> None:
        payload = {
            "text": "This text has no invoice items at all.",
        }
        response = client.post("/convert/text-to-ledes", json=payload)
        assert response.status_code == 400
        assert "No line items" in response.json()["detail"]

    def test_nonexistent_matter_returns_404(self) -> None:
        payload = {
            "text": "Draft brief US $500\n",
            "matter_name": "MATTER-QUE-NAO-EXISTE",
        }
        response = client.post("/convert/text-to-ledes", json=payload)
        assert response.status_code == 404

    def test_extracts_task_codes_from_text(self) -> None:
        payload = {
            "text": "Draft appeal brief US $1200\n",
        }
        response = client.post("/convert/text-to-ledes", json=payload)

        assert response.status_code == 200
        items = response.json()["extracted_data"]["line_items"]
        assert items[0]["task_code"] == "L510"
        assert items[0]["activity_code"] == "A103"

    def test_returns_extracted_data_for_form(self) -> None:
        payload = {
            "text": (
                "Invoice # 7700\n"
                "Date of Issuance: March 10, 2026\n"
                "Research jurisprudence US $600\n"
                "Total Gross Amount: US $600\n"
            ),
        }
        response = client.post("/convert/text-to-ledes", json=payload)

        assert response.status_code == 200
        data = response.json()["extracted_data"]
        assert data["invoice_number"] == "7700"
        assert data["invoice_date"] == "20260310"
        assert data["invoice_total"] == 600.0


def test_extract_invoice_number_colon_hash():
    """CMR-38: Invoice: #4170 format must be captured."""
    text = "Invoice: #4170\nProvide general legal advice US $2,000"
    data = extract_ledes_data(text)
    assert data["invoice_number"] == "4170"


def test_extract_billing_period_from_description():
    """CMR-39: Billing period should be inferred from line item description."""
    text = "Invoice: #4170\nDate of Issuance: February 3, 2026\nProvide general legal advice for September 2025 US $2,000\nTotal Gross Amount: US $2,000"
    data = extract_ledes_data(text)
    assert data["billing_start_date"] == "20250901"
    assert data["billing_end_date"] == "20250930"


def test_extract_billing_period_january():
    """CMR-39: January billing period."""
    text = "Provide general legal advice for January 2026 US $2,000"
    data = extract_ledes_data(text)
    assert data["billing_start_date"] == "20260101"
    assert data["billing_end_date"] == "20260131"


def test_extract_billing_period_february():
    """CMR-39: February in non-leap year."""
    text = "Provide general legal advice for February 2025 US $2,000"
    data = extract_ledes_data(text)
    assert data["billing_start_date"] == "20250201"
    assert data["billing_end_date"] == "20250228"


def test_extract_invoice_description_from_matter():
    """CMR-40: Extract description from Matter field."""
    text = "Matter: Brazil Employment Advice\nProvide general legal advice for September 2025 US $2,000"
    data = extract_ledes_data(text)
    assert data["invoice_description"] == "Brazil Employment Advice"


def test_extract_invoice_description_from_services():
    """CMR-40: Extract from 'Description of Services' field."""
    text = "Description of Services Rendered to Salesforce Tecnologia Ltda. - General Employment Advice\nProvide general legal advice US $2,000"
    data = extract_ledes_data(text)
    assert "General Employment Advice" in data["invoice_description"]


def test_client_matter_id_fallback_to_matter_id():
    """CMR-43: When client_matter_id is empty, use matter_id as fallback."""
    data = {
        "invoice_date": "20260203", "invoice_number": "4170",
        "client_id": "Salesforce", "matter_id": "LS-2025-22672",
        "client_matter_id": "", "invoice_total": 2000.0,
        "law_firm_id": "SF004554", "timekeeper_id": "CMR",
        "timekeeper_name": "RODRIGUES", "timekeeper_classification": "PARTNR",
        "unit_cost": 300.0,
        "line_items": [{"description": "Advice", "amount": 2000.0, "task_code": "L110", "activity_code": "A106"}],
    }
    ledes = generate_ledes_1998b(data)
    data_line = ledes.strip().split("\n")[2]
    fields = data_line.rstrip("[]").split("|")
    assert fields[23] == "LS-2025-22672"
