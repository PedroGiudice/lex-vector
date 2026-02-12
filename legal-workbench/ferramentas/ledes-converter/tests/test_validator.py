"""Tests for LEDES 1998B validator."""

import pytest
from api.ledes_validator import validate_ledes_1998b, ValidationIssue


# --- Helpers ---

VALID_HEADER = (
    "INVOICE_DATE|INVOICE_NUMBER|CLIENT_ID|LAW_FIRM_MATTER_ID|INVOICE_TOTAL|"
    "BILLING_START_DATE|BILLING_END_DATE|INVOICE_DESCRIPTION|LINE_ITEM_NUMBER|"
    "EXP/FEE/INV_ADJ_TYPE|LINE_ITEM_NUMBER_OF_UNITS|LINE_ITEM_ADJUSTMENT_AMOUNT|"
    "LINE_ITEM_TOTAL|LINE_ITEM_DATE|LINE_ITEM_TASK_CODE|LINE_ITEM_EXPENSE_CODE|"
    "LINE_ITEM_ACTIVITY_CODE|TIMEKEEPER_ID|LINE_ITEM_DESCRIPTION|LAW_FIRM_ID|"
    "LINE_ITEM_UNIT_COST|TIMEKEEPER_NAME|TIMEKEEPER_CLASSIFICATION|CLIENT_MATTER_ID[]"
)

VALID_DATA_ROW = (
    "20260115|4432|Salesforce|LS-2020-05805|1200.00|20260101|20260131|"
    "Legal Services|1|F|4.00||1200.00|20260115|L510||A103|CMR|"
    "Draft appeal|SF004554|300.00|RODRIGUES CARLOS|PARTNR|CLT-001[]"
)


def _build_ledes(*data_rows: str) -> str:
    """Monta um arquivo LEDES completo com as data rows fornecidas."""
    lines = ["LEDES1998B[]", VALID_HEADER]
    lines.extend(data_rows)
    return "\n".join(lines)


def _valid_ledes() -> str:
    """Retorna um arquivo LEDES 1998B valido."""
    return _build_ledes(VALID_DATA_ROW)


# --- Tests ---


class TestValidLedes:
    def test_valid_ledes(self):
        """Arquivo valido retorna lista vazia de issues."""
        issues = validate_ledes_1998b(_valid_ledes())
        errors = [i for i in issues if i.severity == "error"]
        assert errors == [], f"Expected no errors, got: {errors}"


class TestFirstLine:
    def test_invalid_first_line(self):
        """Primeira linha diferente de 'LEDES1998B[]' gera erro."""
        content = "WRONG_HEADER[]\n" + VALID_HEADER + "\n" + VALID_DATA_ROW
        issues = validate_ledes_1998b(content)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) >= 1
        assert any("Line 1 must be" in e.message for e in errors)
        assert errors[0].line == 1


class TestHeader:
    def test_wrong_header_field_count(self):
        """Header com numero incorreto de campos gera erro."""
        bad_header = "INVOICE_DATE|INVOICE_NUMBER|CLIENT_ID[]"
        content = f"LEDES1998B[]\n{bad_header}\n{VALID_DATA_ROW}"
        issues = validate_ledes_1998b(content)
        errors = [i for i in issues if i.severity == "error"]
        assert any("Header must have 24 fields" in e.message for e in errors)

    def test_wrong_header_field_order(self):
        """Header com campos fora de ordem gera erro."""
        # Troca INVOICE_NUMBER com CLIENT_ID
        swapped_header = (
            "INVOICE_DATE|CLIENT_ID|INVOICE_NUMBER|LAW_FIRM_MATTER_ID|INVOICE_TOTAL|"
            "BILLING_START_DATE|BILLING_END_DATE|INVOICE_DESCRIPTION|LINE_ITEM_NUMBER|"
            "EXP/FEE/INV_ADJ_TYPE|LINE_ITEM_NUMBER_OF_UNITS|LINE_ITEM_ADJUSTMENT_AMOUNT|"
            "LINE_ITEM_TOTAL|LINE_ITEM_DATE|LINE_ITEM_TASK_CODE|LINE_ITEM_EXPENSE_CODE|"
            "LINE_ITEM_ACTIVITY_CODE|TIMEKEEPER_ID|LINE_ITEM_DESCRIPTION|LAW_FIRM_ID|"
            "LINE_ITEM_UNIT_COST|TIMEKEEPER_NAME|TIMEKEEPER_CLASSIFICATION|CLIENT_MATTER_ID[]"
        )
        content = f"LEDES1998B[]\n{swapped_header}\n{VALID_DATA_ROW}"
        issues = validate_ledes_1998b(content)
        errors = [i for i in issues if i.severity == "error"]
        assert any("Header field 2" in e.message for e in errors)
        assert any("Header field 3" in e.message for e in errors)


class TestDataRows:
    def test_data_row_field_count(self):
        """Data row com numero incorreto de campos gera erro."""
        bad_row = "20260115|4432|Salesforce[]"
        content = _build_ledes(bad_row)
        issues = validate_ledes_1998b(content)
        errors = [i for i in issues if i.severity == "error"]
        assert any("Data row must have 24 fields" in e.message for e in errors)

    def test_line_not_ending_with_brackets(self):
        """Linha sem [] no final gera erro."""
        row_no_brackets = VALID_DATA_ROW.rstrip("[]")
        content = _build_ledes(row_no_brackets)
        issues = validate_ledes_1998b(content)
        errors = [i for i in issues if i.severity == "error"]
        assert any("Data line must end with '[]'" in e.message for e in errors)


class TestDateValidation:
    def test_invalid_date_format(self):
        """Data que nao e YYYYMMDD gera erro."""
        # Substitui INVOICE_DATE (campo 0) por formato invalido
        bad_row = VALID_DATA_ROW.replace("20260115|4432", "2026-01-15|4432", 1)
        content = _build_ledes(bad_row)
        issues = validate_ledes_1998b(content)
        errors = [i for i in issues if i.severity == "error"]
        date_errors = [e for e in errors if "YYYYMMDD" in e.message]
        assert len(date_errors) >= 1
        assert any("INVOICE_DATE" in e.field_name for e in date_errors)


class TestCurrencyValidation:
    def test_invalid_currency_format(self):
        """Moeda sem formato correto gera erro."""
        # Substitui INVOICE_TOTAL (1200.00) por formato invalido
        bad_row = (
            "20260115|4432|Salesforce|LS-2020-05805|$1,200|20260101|20260131|"
            "Legal Services|1|F|4.00||1200.00|20260115|L510||A103|CMR|"
            "Draft appeal|SF004554|300.00|RODRIGUES CARLOS|PARTNR|CLT-001[]"
        )
        content = _build_ledes(bad_row)
        issues = validate_ledes_1998b(content)
        errors = [i for i in issues if i.severity == "error"]
        currency_errors = [e for e in errors if "Currency field" in e.message]
        assert len(currency_errors) >= 1
        assert any("INVOICE_TOTAL" in e.message for e in currency_errors)


class TestAsciiValidation:
    def test_non_ascii_characters(self):
        """Caracteres nao-ASCII em valores geram erro."""
        bad_row = (
            "20260115|4432|Salesforce|LS-2020-05805|1200.00|20260101|20260131|"
            "Legal Services|1|F|4.00||1200.00|20260115|L510||A103|CMR|"
            "Recurso Especial Sao Paulo|SF004554|300.00|RODRIGUES CARLOS|PARTNR|CLT-001[]"
        )
        # Inserir caractere nao-ASCII na descricao
        bad_row = bad_row.replace("Sao Paulo", "S\u00e3o Paulo")
        content = _build_ledes(bad_row)
        issues = validate_ledes_1998b(content)
        errors = [i for i in issues if i.severity == "error"]
        ascii_errors = [e for e in errors if "Non-ASCII" in e.message]
        assert len(ascii_errors) >= 1
        assert any("LINE_ITEM_DESCRIPTION" in e.field_name for e in ascii_errors)


class TestBracketsInValues:
    def test_brackets_in_values(self):
        """Colchetes em valores de campos geram erro."""
        bad_row = (
            "20260115|4432|Salesforce|LS-2020-05805|1200.00|20260101|20260131|"
            "Legal [Services]|1|F|4.00||1200.00|20260115|L510||A103|CMR|"
            "Draft appeal|SF004554|300.00|RODRIGUES CARLOS|PARTNR|CLT-001[]"
        )
        content = _build_ledes(bad_row)
        issues = validate_ledes_1998b(content)
        errors = [i for i in issues if i.severity == "error"]
        bracket_errors = [e for e in errors if "Bracket" in e.message]
        assert len(bracket_errors) >= 1


class TestRequiredFields:
    def test_required_fields_empty(self):
        """Campos obrigatorios vazios geram erro."""
        # INVOICE_NUMBER (campo 1) vazio
        bad_row = (
            "20260115||Salesforce|LS-2020-05805|1200.00|20260101|20260131|"
            "Legal Services|1|F|4.00||1200.00|20260115|L510||A103|CMR|"
            "Draft appeal|SF004554|300.00|RODRIGUES CARLOS|PARTNR|CLT-001[]"
        )
        content = _build_ledes(bad_row)
        issues = validate_ledes_1998b(content)
        errors = [i for i in issues if i.severity == "error"]
        required_errors = [e for e in errors if "Required field" in e.message]
        assert len(required_errors) >= 1
        assert any("INVOICE_NUMBER" in e.message for e in required_errors)


class TestTaskCodes:
    def test_empty_task_code_warning(self):
        """Task code vazio gera warning."""
        # LINE_ITEM_TASK_CODE (campo 14) vazio
        row_empty_task = (
            "20260115|4432|Salesforce|LS-2020-05805|1200.00|20260101|20260131|"
            "Legal Services|1|F|4.00||1200.00|20260115|||A103|CMR|"
            "Draft appeal|SF004554|300.00|RODRIGUES CARLOS|PARTNR|CLT-001[]"
        )
        content = _build_ledes(row_empty_task)
        issues = validate_ledes_1998b(content)
        warnings = [i for i in issues if i.severity == "warning"]
        assert any("Task code is empty" in w.message for w in warnings)

    def test_unknown_task_code_warning(self):
        """Task code desconhecido gera warning."""
        # Substitui L510 por ZZZZ
        bad_row = VALID_DATA_ROW.replace("|L510|", "|ZZZZ|")
        content = _build_ledes(bad_row)
        issues = validate_ledes_1998b(content)
        warnings = [i for i in issues if i.severity == "warning"]
        assert any("Unknown task code" in w.message for w in warnings)
        assert any("ZZZZ" in w.message for w in warnings)


class TestEdgeCases:
    def test_empty_content(self):
        """Conteudo vazio gera erro na primeira linha."""
        issues = validate_ledes_1998b("")
        assert len(issues) >= 1
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) >= 1

    def test_multiple_issues(self):
        """Arquivo com multiplos problemas retorna todos."""
        # Linha 1 errada + data row com campo obrigatorio vazio + moeda invalida
        bad_content = "\n".join([
            "WRONG[]",
            VALID_HEADER,
            # INVOICE_NUMBER vazio, INVOICE_TOTAL invalido, task code desconhecido
            "20260115||Salesforce|LS-2020-05805|bad_money|20260101|20260131|"
            "Legal Services|1|F|4.00||1200.00|20260115|ZZZZ||A103|CMR|"
            "Draft appeal|SF004554|300.00|RODRIGUES CARLOS|PARTNR|CLT-001[]",
        ])
        issues = validate_ledes_1998b(bad_content)
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]

        # Deve ter pelo menos: first line error + required field + currency format
        assert len(errors) >= 3
        assert len(warnings) >= 1  # Unknown task code

        # Verifica que diferentes tipos de issue estao presentes
        messages = " ".join(e.message for e in errors)
        assert "Line 1 must be" in messages
        assert "Required field" in messages
        assert "Currency field" in messages
