"""
LEDES 1998B output validator.

Validates generated LEDES content for specification compliance,
reporting errors and warnings with precise location (line and field).
"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

LEDES_HEADER_FIELDS = [
    "INVOICE_DATE", "INVOICE_NUMBER", "CLIENT_ID", "LAW_FIRM_MATTER_ID", "INVOICE_TOTAL",
    "BILLING_START_DATE", "BILLING_END_DATE", "INVOICE_DESCRIPTION", "LINE_ITEM_NUMBER",
    "EXP/FEE/INV_ADJ_TYPE", "LINE_ITEM_NUMBER_OF_UNITS", "LINE_ITEM_ADJUSTMENT_AMOUNT",
    "LINE_ITEM_TOTAL", "LINE_ITEM_DATE", "LINE_ITEM_TASK_CODE", "LINE_ITEM_EXPENSE_CODE",
    "LINE_ITEM_ACTIVITY_CODE", "TIMEKEEPER_ID", "LINE_ITEM_DESCRIPTION", "LAW_FIRM_ID",
    "LINE_ITEM_UNIT_COST", "TIMEKEEPER_NAME", "TIMEKEEPER_CLASSIFICATION", "CLIENT_MATTER_ID",
]

# Campos obrigatorios (nao podem ser vazios em data rows)
REQUIRED_FIELDS = {
    "INVOICE_DATE", "INVOICE_NUMBER", "CLIENT_ID", "LAW_FIRM_MATTER_ID",
    "INVOICE_TOTAL", "LINE_ITEM_NUMBER", "EXP/FEE/INV_ADJ_TYPE",
    "LINE_ITEM_TOTAL", "LINE_ITEM_DATE", "LAW_FIRM_ID",
}

# Campos de data (devem estar no formato YYYYMMDD)
DATE_FIELDS = {"INVOICE_DATE", "BILLING_START_DATE", "BILLING_END_DATE", "LINE_ITEM_DATE"}

# Campos de moeda (devem ter formato numerico com 2 decimais)
CURRENCY_FIELDS = {"INVOICE_TOTAL", "LINE_ITEM_TOTAL", "LINE_ITEM_UNIT_COST", "LINE_ITEM_ADJUSTMENT_AMOUNT"}

# Task codes UTBMS conhecidos
KNOWN_TASK_CODES = {"L100", "L120", "L160", "L210", "L250", "L310", "L510"}
KNOWN_ACTIVITY_CODES = {"A101", "A102", "A103", "A104", "A106", "A107"}


@dataclass
class ValidationIssue:
    line: int
    field: int          # 1-indexed, 0 se nao aplicavel
    field_name: str     # nome do campo ou '' se generico
    severity: str       # "error" | "warning"
    message: str


def validate_ledes_1998b(content: str) -> list[ValidationIssue]:
    """Valida um arquivo LEDES 1998B completo."""
    issues: list[ValidationIssue] = []
    lines = content.split("\n")

    if not lines:
        issues.append(ValidationIssue(0, 0, "", "error", "Empty content"))
        return issues

    # 1. Linha 1 = "LEDES1998B[]"
    if lines[0] != "LEDES1998B[]":
        issues.append(ValidationIssue(1, 0, "", "error",
            f"Line 1 must be 'LEDES1998B[]', got '{lines[0]}'"))

    if len(lines) < 2:
        issues.append(ValidationIssue(1, 0, "", "error", "Missing header line"))
        return issues

    # 2. Header com 24 campos na ordem correta
    header_line = lines[1]
    if not header_line.endswith("[]"):
        issues.append(ValidationIssue(2, 0, "", "error", "Header line must end with '[]'"))
    else:
        header_content = header_line[:-2]  # Remove []
        header_fields = header_content.split("|")
        if len(header_fields) != 24:
            issues.append(ValidationIssue(2, 0, "", "error",
                f"Header must have 24 fields, got {len(header_fields)}"))
        elif header_fields != LEDES_HEADER_FIELDS:
            for i, (got, expected) in enumerate(zip(header_fields, LEDES_HEADER_FIELDS)):
                if got != expected:
                    issues.append(ValidationIssue(2, i + 1, expected, "error",
                        f"Header field {i+1}: expected '{expected}', got '{got}'"))

    # 3-10. Validar cada data row
    for line_num, line in enumerate(lines[2:], start=3):
        if not line.strip():
            continue

        # 4. Linha termina com []
        if not line.endswith("[]"):
            issues.append(ValidationIssue(line_num, 0, "", "error",
                "Data line must end with '[]'"))
            continue

        row_content = line[:-2]  # Remove []
        fields = row_content.split("|")

        # 3. Exatamente 24 campos
        if len(fields) != 24:
            issues.append(ValidationIssue(line_num, 0, "", "error",
                f"Data row must have 24 fields, got {len(fields)}"))
            continue

        for i, value in enumerate(fields):
            field_name = LEDES_HEADER_FIELDS[i] if i < len(LEDES_HEADER_FIELDS) else f"field_{i}"

            # 7. ASCII-only
            if value and not value.isascii():
                issues.append(ValidationIssue(line_num, i + 1, field_name, "error",
                    f"Non-ASCII characters in '{field_name}'"))

            # 8. Sem pipes/colchetes nos valores (exceto delimitadores)
            if "[" in value or "]" in value:
                issues.append(ValidationIssue(line_num, i + 1, field_name, "error",
                    f"Bracket characters in '{field_name}' value"))

            # 9. Campos obrigatorios nao vazios
            if field_name in REQUIRED_FIELDS and not value.strip():
                issues.append(ValidationIssue(line_num, i + 1, field_name, "error",
                    f"Required field '{field_name}' is empty"))

            # 5. Datas no formato YYYYMMDD
            if field_name in DATE_FIELDS and value.strip():
                if not re.match(r"^\d{8}$", value):
                    issues.append(ValidationIssue(line_num, i + 1, field_name, "error",
                        f"Date field '{field_name}' must be YYYYMMDD, got '{value}'"))

            # 6. Moeda com max 14 digitos + 2 decimais
            if field_name in CURRENCY_FIELDS and value.strip():
                if not re.match(r"^\d{1,14}\.\d{2}$", value):
                    issues.append(ValidationIssue(line_num, i + 1, field_name, "error",
                        f"Currency field '{field_name}' must be up to 14 digits with 2 decimals, got '{value}'"))

            # 10. Task codes conhecidos (warning se vazio)
            if field_name == "LINE_ITEM_TASK_CODE":
                if not value.strip():
                    issues.append(ValidationIssue(line_num, i + 1, field_name, "warning",
                        "Task code is empty"))
                elif value not in KNOWN_TASK_CODES:
                    issues.append(ValidationIssue(line_num, i + 1, field_name, "warning",
                        f"Unknown task code '{value}'"))

            if field_name == "LINE_ITEM_ACTIVITY_CODE":
                if not value.strip():
                    issues.append(ValidationIssue(line_num, i + 1, field_name, "warning",
                        "Activity code is empty"))
                elif value not in KNOWN_ACTIVITY_CODES:
                    issues.append(ValidationIssue(line_num, i + 1, field_name, "warning",
                        f"Unknown activity code '{value}'"))

    return issues
