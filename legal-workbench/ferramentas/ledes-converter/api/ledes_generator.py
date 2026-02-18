"""
LEDES 1998B generator - pure functions for LEDES format generation.

This module contains all functions related to parsing invoice data
and generating LEDES 1998B compliant output. No FastAPI dependencies.
"""

import logging
import re
import calendar
from datetime import datetime

from .task_codes import classify_task_code, classify_activity_code

logger = logging.getLogger(__name__)

# Constants
MAX_DESCRIPTION_LENGTH = 500
MAX_LINE_ITEMS = 1000


def sanitize_string(value: str, max_length: int = MAX_DESCRIPTION_LENGTH) -> str:
    """Sanitize and truncate string values."""
    if not value:
        return ""
    # Remove control characters and excessive whitespace
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned[:max_length]


def sanitize_ledes_field(value: str, max_length: int = MAX_DESCRIPTION_LENGTH) -> str:
    """
    Sanitize field values for LEDES format compliance.

    LEDES 1998B Requirements:
    - ASCII encoding only (non-ASCII chars removed)
    - No pipe characters (field delimiter)
    - No brackets (line terminator chars)
    - Control characters removed
    """
    if not value:
        return ""

    # First apply general sanitization
    cleaned = sanitize_string(value, max_length)

    # Remove pipe and bracket characters (LEDES reserved chars)
    cleaned = cleaned.replace('|', '').replace('[', '').replace(']', '')

    # Ensure ASCII-only by removing non-ASCII characters
    cleaned = cleaned.encode('ascii', errors='ignore').decode('ascii')

    return cleaned


def parse_currency(value_str: str | None) -> float:
    """Parse currency string to float, removing symbols and formatting."""
    if not value_str:
        return 0.0
    # Remove 'US $', '$', ',', ' ' and other non-numeric chars except '.'
    clean_val = re.sub(r'[^\d.]', '', value_str)
    try:
        return float(clean_val)
    except ValueError:
        return 0.0


def format_ledes_currency(amount: float) -> str:
    """
    Format currency for LEDES 1998B compliance.

    LEDES 1998B Requirements:
    - Up to 14 digits before decimal point
    - Exactly 2 digits after decimal point
    - No currency symbols, commas, or spaces
    - Returns empty string if amount exceeds specification limits
    """
    if amount < 0:
        return ""  # LEDES doesn't support negative amounts in standard fields

    # Format with 2 decimal places
    formatted = f"{amount:.2f}"

    # Check if integer part exceeds 14 digits
    integer_part = formatted.split('.')[0]
    if len(integer_part) > 14:
        logger.warning(f"Currency amount {amount} exceeds LEDES 14-digit limit")
        return ""  # Or could raise exception depending on requirements

    return formatted


def format_date_ledes(date_str: str) -> str:
    """Convert date string to LEDES format (YYYYMMDD)."""
    try:
        # Assuming format "Month DD, YYYY" e.g., "December 15, 2025"
        dt = datetime.strptime(date_str, "%B %d, %Y")
        return dt.strftime("%Y%m%d")
    except ValueError:
        return ""


def infer_billing_period(text: str) -> tuple[str, str]:
    """Infer billing start/end dates from month/year references in text."""
    month_pattern = re.compile(
        r"(January|February|March|April|May|June|July|August|September|October|November|December"
        r"|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})",
        re.IGNORECASE,
    )
    match = month_pattern.search(text)
    if not match:
        return ("", "")

    month_str = match.group(1)
    year = int(match.group(2))

    month_names = {
        "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
        "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
        "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9,
        "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
    }
    month_num = month_names.get(month_str.lower())
    if not month_num:
        return ("", "")

    last_day = calendar.monthrange(year, month_num)[1]
    return (f"{year:04d}{month_num:02d}01", f"{year:04d}{month_num:02d}{last_day:02d}")


def extract_ledes_data(text: str) -> dict:
    """Extract invoice data from text content with validation."""
    data = {
        "invoice_date": "",
        "invoice_number": "",
        "client_id": "SALESFORCE",  # Placeholder based on template analysis
        "matter_id": "LITIGATION-BRAZIL",  # Placeholder
        "invoice_total": 0.0,
        "invoice_description": "",
        "line_items": []
    }

    # Regex patterns (case-insensitive, multiple variants for robustness)
    date_pattern = re.compile(
        r"(?:Date\s*(?:of\s*)?Issuance|Invoice\s*Date|Data\s*de\s*Emiss[aã]o)\s*:?\s*(.*)",
        re.IGNORECASE,
    )
    invoice_num_pattern = re.compile(
        r"(?:Invoice\s*(?:#|No\.?|Number)?|Nota\s*Fiscal\s*(?:#|No\.?)?)\s*:?\s*#?\s*(\d+)",
        re.IGNORECASE,
    )
    total_pattern = re.compile(
        r"(?:Total\s*(?:Gross\s*)?Amount|Valor\s*Total|Grand\s*Total)\s*:?\s*(?:US\s*)?\$?\s*([\d,]+\.?\d*)",
        re.IGNORECASE,
    )
    matter_pattern = re.compile(
        r"^Matter\s*:\s*(.+)",
        re.IGNORECASE,
    )
    services_pattern = re.compile(
        r"Description\s+of\s+Services.*?[-\u2013]\s*(.+)",
        re.IGNORECASE,
    )

    # Line items pattern - matches "description US $amount" or "description R$ amount"
    line_item_pattern = re.compile(r"(.*?)\s*(?:US\s*\$|R\$)\s*([\d,]+(?:\.\d{2})?)(?:\s|$)")

    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract Header Info
        date_match = date_pattern.search(line)
        if date_match:
            raw_date = date_match.group(1).strip()
            data["invoice_date"] = format_date_ledes(sanitize_string(raw_date, 50))

        inv_num_match = invoice_num_pattern.search(line)
        if inv_num_match:
            data["invoice_number"] = sanitize_string(inv_num_match.group(1).strip(), 50)

        total_match = total_pattern.search(line)
        if total_match:
            data["invoice_total"] = parse_currency(total_match.group(1))

        if not data["invoice_description"]:
            matter_match = matter_pattern.search(line)
            if matter_match:
                data["invoice_description"] = sanitize_string(matter_match.group(1).strip(), 200)

            services_match = services_pattern.search(line)
            if services_match:
                data["invoice_description"] = sanitize_string(services_match.group(1).strip(), 200)

        # Extract Line Items (with limit to prevent DoS)
        if len(data["line_items"]) >= MAX_LINE_ITEMS:
            logger.warning(f"Reached max line items limit ({MAX_LINE_ITEMS})")
            break

        if "Total Gross Amount" not in line:
            item_match = line_item_pattern.search(line)
            if item_match:
                desc = sanitize_string(item_match.group(1).strip())
                amount = parse_currency(item_match.group(2))

                # Filter out likely false positives
                if desc and amount > 0:
                    data["line_items"].append({
                        "description": desc,
                        "amount": amount,
                        "task_code": classify_task_code(desc),
                        "activity_code": classify_activity_code(desc),
                    })

    # Infer billing period from line item descriptions if not already set
    if not data.get("billing_start_date"):
        for item in data["line_items"]:
            start, end = infer_billing_period(item["description"])
            if start:
                data["billing_start_date"] = start
                data["billing_end_date"] = end
                break

    return data


def generate_ledes_1998b(data: dict) -> str:
    """
    Generate LEDES 1998B format from extracted data.

    LEDES 1998B Specification Compliance:
    - Line 1: LEDES1998B[] identifier
    - Line 2: Header with 24 ALL CAPS field names
    - Lines 3+: Data rows with 24 fields each
    - Every line ends with []
    - Pipe-delimited (|)
    - ASCII encoding only
    - Currency: max 14 digits before decimal, 2 after
    - Date: YYYYMMDD format
    - No pipe or bracket characters in field values
    """
    # Line 1: LEDES 1998B identifier
    lines = ["LEDES1998B[]"]

    # Line 2: Header with exactly 24 fields in specification order
    header = (
        "INVOICE_DATE|INVOICE_NUMBER|CLIENT_ID|LAW_FIRM_MATTER_ID|INVOICE_TOTAL|"
        "BILLING_START_DATE|BILLING_END_DATE|INVOICE_DESCRIPTION|LINE_ITEM_NUMBER|"
        "EXP/FEE/INV_ADJ_TYPE|LINE_ITEM_NUMBER_OF_UNITS|LINE_ITEM_ADJUSTMENT_AMOUNT|"
        "LINE_ITEM_TOTAL|LINE_ITEM_DATE|LINE_ITEM_TASK_CODE|LINE_ITEM_EXPENSE_CODE|"
        "LINE_ITEM_ACTIVITY_CODE|TIMEKEEPER_ID|LINE_ITEM_DESCRIPTION|LAW_FIRM_ID|"
        "LINE_ITEM_UNIT_COST|TIMEKEEPER_NAME|TIMEKEEPER_CLASSIFICATION|CLIENT_MATTER_ID[]"
    )
    lines.append(header)

    # Extract config values with defaults
    billing_start = data.get("billing_start_date", "")
    billing_end = data.get("billing_end_date", "")
    timekeeper_id = data.get("timekeeper_id", "")
    timekeeper_name = data.get("timekeeper_name", "")
    timekeeper_class = data.get("timekeeper_classification", "")
    unit_cost = data.get("unit_cost", 0)
    invoice_desc = data.get("invoice_description", "Legal Services")

    # Data rows: Each line item becomes a row with 24 fields
    for i, item in enumerate(data["line_items"], 1):
        # Calculate units if unit_cost is provided
        units = ""
        if unit_cost and unit_cost > 0:
            calculated_units = item['amount'] / unit_cost
            units = f"{calculated_units:.2f}"

        row = [
            sanitize_ledes_field(data["invoice_date"], 8),           # 1. INVOICE_DATE
            sanitize_ledes_field(data["invoice_number"], 50),        # 2. INVOICE_NUMBER
            sanitize_ledes_field(data["client_id"], 100),            # 3. CLIENT_ID
            sanitize_ledes_field(data["matter_id"], 100),            # 4. LAW_FIRM_MATTER_ID
            format_ledes_currency(data['invoice_total']),            # 5. INVOICE_TOTAL
            sanitize_ledes_field(billing_start, 8),                  # 6. BILLING_START_DATE
            sanitize_ledes_field(billing_end, 8),                    # 7. BILLING_END_DATE
            sanitize_ledes_field(invoice_desc, 100),                 # 8. INVOICE_DESCRIPTION
            str(i),                                                  # 9. LINE_ITEM_NUMBER
            "F",                                                     # 10. EXP/FEE/INV_ADJ_TYPE (F=Fee)
            units,                                                   # 11. LINE_ITEM_NUMBER_OF_UNITS
            "",                                                      # 12. LINE_ITEM_ADJUSTMENT_AMOUNT
            format_ledes_currency(item['amount']),                   # 13. LINE_ITEM_TOTAL
            sanitize_ledes_field(data["invoice_date"], 8),           # 14. LINE_ITEM_DATE
            item.get("task_code", ""),                               # 15. LINE_ITEM_TASK_CODE
            "",                                                      # 16. LINE_ITEM_EXPENSE_CODE
            item.get("activity_code", ""),                           # 17. LINE_ITEM_ACTIVITY_CODE
            sanitize_ledes_field(timekeeper_id, 20),                 # 18. TIMEKEEPER_ID
            sanitize_ledes_field(item["description"], 500),          # 19. LINE_ITEM_DESCRIPTION
            sanitize_ledes_field(data.get("law_firm_id", ""), 50),   # 20. LAW_FIRM_ID
            format_ledes_currency(unit_cost) if unit_cost else "",   # 21. LINE_ITEM_UNIT_COST
            sanitize_ledes_field(timekeeper_name, 50),               # 22. TIMEKEEPER_NAME
            sanitize_ledes_field(timekeeper_class, 10),              # 23. TIMEKEEPER_CLASSIFICATION
            sanitize_ledes_field(data.get("client_matter_id") or data.get("matter_id", ""), 50) # 24. CLIENT_MATTER_ID
        ]

        lines.append("|".join(row) + "[]")

    return "\n".join(lines)
