"""
Litigation Data Extraction Script (Production-Ready).

This script extracts structured litigation data from Trello cards, including:
- Brazilian identifiers (CPF, CNPJ) with validation
- Personal data (names, phone, email)
- Financial values (Brazilian currency format)
- Case numbers and custom field data

Features:
- Robust regex parsing with Brazilian format support
- CPF/CNPJ validation (checksum algorithm)
- Graceful error handling with detailed error reports
- Progress indicators for large datasets
- Separated clean/error outputs

Usage:
    python examples/extract_litigation_data.py "Board Name" [--list "List Name"] [--output output/]

Requirements:
    - .env file with TRELLO_API_KEY and TRELLO_API_TOKEN
    - Target board with litigation data cards
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Add src to path to import models and client
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import EnvironmentSettings
from trello_client import TrelloClient, TrelloAPIError


# ============================================================================
# Regex Patterns for Description Parsing
# ============================================================================

REGEX_PATTERNS = {
    # Brazilian CPF: 123.456.789-00 or 12345678900
    "cpf": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",

    # Brazilian CNPJ: 12.345.678/0001-90 or 12345678000190
    "cnpj": r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",

    # Money values: R$ 1.000,00 or R$ 1000,00 (Brazilian format)
    # Captures with or without thousands separators, comma as decimal
    "currency": r"R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?|[0-9]+(?:,[0-9]{2})?)",

    # Names (after "Nome:" or "Réu:" or "Autor:")
    "name": r"(?:Nome|Réu|Autor|Cliente):\s*(.+?)(?:\n|$)",

    # Phone numbers: (11) 98765-4321 or 11987654321
    "phone": r"\(?(\d{2})\)?\s*9?\d{4}-?\d{4}",

    # Email addresses
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",

    # Case numbers (CNJ format)
    "case_number": r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}",
}


# ============================================================================
# Validation Functions (CPF/CNPJ Checksum)
# ============================================================================

def validate_cpf(cpf: str) -> bool:
    """
    Validate Brazilian CPF using checksum algorithm.

    Args:
        cpf: 11-digit CPF string (digits only)

    Returns:
        True if valid, False otherwise
    """
    if len(cpf) != 11 or not cpf.isdigit():
        return False

    # Known invalid patterns
    if cpf == cpf[0] * 11:
        return False

    # Calculate first check digit
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = 11 - (sum1 % 11)
    digit1 = 0 if digit1 >= 10 else digit1

    # Calculate second check digit
    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = 11 - (sum2 % 11)
    digit2 = 0 if digit2 >= 10 else digit2

    return cpf[-2:] == f"{digit1}{digit2}"


def validate_cnpj(cnpj: str) -> bool:
    """
    Validate Brazilian CNPJ using checksum algorithm.

    Args:
        cnpj: 14-digit CNPJ string (digits only)

    Returns:
        True if valid, False otherwise
    """
    if len(cnpj) != 14 or not cnpj.isdigit():
        return False

    # Known invalid patterns
    if cnpj == cnpj[0] * 14:
        return False

    # Calculate first check digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
    digit1 = 11 - (sum1 % 11)
    digit1 = 0 if digit1 >= 10 else digit1

    # Calculate second check digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
    digit2 = 11 - (sum2 % 11)
    digit2 = 0 if digit2 >= 10 else digit2

    return cnpj[-2:] == f"{digit1}{digit2}"


# ============================================================================
# Data Extraction Functions
# ============================================================================

def parse_brazilian_currency(value_str: str) -> Optional[float]:
    """
    Parse Brazilian currency format to float.

    Handles formats:
    - R$ 1.000,00 (thousands with dot, decimal with comma)
    - R$ 1000,00 (no thousands separator)
    - R$ 1.000 (no decimal)
    - R$ 1000 (plain integer)

    Args:
        value_str: Currency string with Brazilian format

    Returns:
        Float value or None if parsing fails
    """
    try:
        # Remove thousands separators (dots) then convert comma to period
        cleaned = value_str.replace(".", "").replace(",", ".")
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def extract_from_description(description: str) -> dict[str, Any]:
    """
    Extract structured data from card description using regex.

    Safely handles extraction failures and preserves raw values when
    parsing fails.

    Args:
        description: Card description text

    Returns:
        Dictionary with extracted fields (keys only present if found)
    """
    data = {}

    if not description:
        return data

    # Extract CPF
    try:
        cpf_match = re.search(REGEX_PATTERNS["cpf"], description)
        if cpf_match:
            data["cpf"] = re.sub(r"[.-]", "", cpf_match.group(0))
    except Exception as e:
        print(f"Warning: CPF extraction failed: {e}", file=sys.stderr)

    # Extract CNPJ
    try:
        cnpj_match = re.search(REGEX_PATTERNS["cnpj"], description)
        if cnpj_match:
            data["cnpj"] = re.sub(r"[./-]", "", cnpj_match.group(0))
    except Exception as e:
        print(f"Warning: CNPJ extraction failed: {e}", file=sys.stderr)

    # Extract name
    try:
        name_match = re.search(REGEX_PATTERNS["name"], description, re.IGNORECASE)
        if name_match:
            data["name"] = name_match.group(1).strip()
    except Exception as e:
        print(f"Warning: Name extraction failed: {e}", file=sys.stderr)

    # Extract currency value (Brazilian format)
    try:
        currency_match = re.search(REGEX_PATTERNS["currency"], description)
        if currency_match:
            value_str = currency_match.group(1)
            parsed_value = parse_brazilian_currency(value_str)
            if parsed_value is not None:
                data["claim_value"] = parsed_value
            else:
                # Preserve raw value if parsing failed
                data["claim_value_raw"] = value_str
    except Exception as e:
        print(f"Warning: Currency extraction failed: {e}", file=sys.stderr)

    # Extract phone
    try:
        phone_match = re.search(REGEX_PATTERNS["phone"], description)
        if phone_match:
            data["phone"] = re.sub(r"[()-\s]", "", phone_match.group(0))
    except Exception as e:
        print(f"Warning: Phone extraction failed: {e}", file=sys.stderr)

    # Extract email
    try:
        email_match = re.search(REGEX_PATTERNS["email"], description)
        if email_match:
            data["email"] = email_match.group(0).lower()
    except Exception as e:
        print(f"Warning: Email extraction failed: {e}", file=sys.stderr)

    # Extract case number
    try:
        case_match = re.search(REGEX_PATTERNS["case_number"], description)
        if case_match:
            data["case_number"] = case_match.group(0)
    except Exception as e:
        print(f"Warning: Case number extraction failed: {e}", file=sys.stderr)

    return data


def extract_custom_fields(custom_field_items: list) -> dict[str, Any]:
    """
    Extract structured data from custom field items.

    Safely handles various custom field types with error tolerance.

    Args:
        custom_field_items: List of CustomFieldItem objects

    Returns:
        Dictionary with custom field values (field_id -> value)
    """
    data = {}

    for item in custom_field_items:
        try:
            field_id = item.id_custom_field
            value_dict = item.value

            # Extract value based on type
            if "text" in value_dict:
                data[field_id] = value_dict["text"]
            elif "number" in value_dict:
                # Ensure we get numeric value
                try:
                    data[field_id] = float(value_dict["number"])
                except (ValueError, TypeError):
                    data[field_id] = value_dict["number"]
            elif "date" in value_dict:
                data[field_id] = value_dict["date"]
            elif "checked" in value_dict:
                # Convert string to boolean
                data[field_id] = value_dict["checked"] == "true"
            elif "option" in value_dict:
                data[field_id] = value_dict["option"]
        except Exception as e:
            print(f"Warning: Failed to extract custom field {item.id}: {e}", file=sys.stderr)
            continue

    return data


def validate_record(record: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate extracted record has required fields and valid formats.

    Performs comprehensive validation including:
    - Required field presence
    - Format validation (length)
    - Checksum validation (CPF/CNPJ)

    Args:
        record: Extracted data dictionary (description_data only)

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check for at least one identifier (CPF or CNPJ)
    if not record.get("cpf") and not record.get("cnpj"):
        errors.append("Missing identifier: need CPF or CNPJ")

    # Check for name
    if not record.get("name"):
        errors.append("Missing name field")

    # Validate CPF if present
    if record.get("cpf"):
        cpf = record["cpf"]
        if len(cpf) != 11:
            errors.append(f"Invalid CPF length: {cpf} (expected 11 digits)")
        elif not validate_cpf(cpf):
            errors.append(f"Invalid CPF checksum: {cpf}")

    # Validate CNPJ if present
    if record.get("cnpj"):
        cnpj = record["cnpj"]
        if len(cnpj) != 14:
            errors.append(f"Invalid CNPJ length: {cnpj} (expected 14 digits)")
        elif not validate_cnpj(cnpj):
            errors.append(f"Invalid CNPJ checksum: {cnpj}")

    # Validate email format (basic)
    if record.get("email"):
        email = record["email"]
        if "@" not in email or "." not in email.split("@")[-1]:
            errors.append(f"Invalid email format: {email}")

    # Validate phone (basic - should have 10-11 digits)
    if record.get("phone"):
        phone = record["phone"]
        if not phone.isdigit() or len(phone) not in [10, 11]:
            errors.append(f"Invalid phone format: {phone} (expected 10-11 digits)")

    return (len(errors) == 0, errors)


# ============================================================================
# Main Extraction Pipeline
# ============================================================================

async def extract_litigation_data(
    board_name: str,
    list_name: Optional[str] = None,
    output_dir: str = "output"
) -> dict[str, Any]:
    """
    Extract litigation data from Trello board.

    Args:
        board_name: Name of board to extract from (case-insensitive)
        list_name: Optional list name to filter by
        output_dir: Output directory for JSON files

    Returns:
        Dictionary with extraction stats
    """
    print(f"\n🔍 Starting litigation data extraction...\n")

    # Load environment settings
    try:
        settings = EnvironmentSettings()
    except Exception as e:
        print(f"❌ Failed to load environment settings: {e}")
        print("💡 Make sure .env file exists with TRELLO_API_KEY and TRELLO_API_TOKEN")
        sys.exit(1)

    # Initialize client
    async with TrelloClient(settings) as client:
        # Validate credentials
        try:
            user_info = await client.validate_credentials()
            print(f"✓ Authenticated as {user_info.get('fullName')}\n")
        except TrelloAPIError as e:
            print(f"❌ Authentication failed: {e}")
            sys.exit(1)

        # Find target board
        print(f"📋 Searching for board: '{board_name}'...")
        boards = await client.get_all_boards()
        target_board = None

        for board in boards:
            if board.name.lower() == board_name.lower():
                target_board = board
                break

        if not target_board:
            available_boards = [b.name for b in boards]
            print(f"❌ Board '{board_name}' not found")
            print(f"📋 Available boards: {', '.join(available_boards)}")
            sys.exit(1)

        print(f"✓ Found board: {target_board.name} (ID: {target_board.id})\n")

        # Fetch cards with custom fields
        print(f"📥 Fetching cards with custom fields...")
        cards = await client.get_board_cards_with_custom_fields(
            board_id=target_board.id,
            card_status="open"
        )

        print(f"✓ Found {len(cards)} open cards\n")

        # Filter by list if specified
        if list_name:
            # Get board structure to find list ID
            structure = await client.get_board_structure(target_board.id)
            target_list = structure.get_list_by_name(list_name)

            if not target_list:
                available_lists = [lst.name for lst in structure.lists]
                print(f"❌ List '{list_name}' not found")
                print(f"📋 Available lists: {', '.join(available_lists)}")
                sys.exit(1)

            cards = [c for c in cards if c.id_list == target_list.id]
            print(f"🔍 Filtered to {len(cards)} cards in list '{list_name}'\n")

        # Extract data from each card
        print(f"⚙️  Extracting data from {len(cards)} cards...")
        print(f"{'='*70}\n")

        valid_records = []
        error_records = []

        for i, card in enumerate(cards, 1):
            # Progress indicator with percentage
            progress_pct = (i / len(cards)) * 100
            card_name_truncated = card.name[:50] + "..." if len(card.name) > 50 else card.name
            print(f"[{i:3d}/{len(cards)}] ({progress_pct:5.1f}%) {card_name_truncated}")

            try:
                # Extract from description
                desc_data = extract_from_description(card.desc)

                # Extract from custom fields
                custom_data = extract_custom_fields(card.custom_field_items)

                # Combine data
                record = {
                    "card_id": card.id,
                    "card_name": card.name,
                    "card_url": card.url,
                    "list_id": card.id_list,
                    "labels": [lbl.name for lbl in card.labels],
                    "due_date": card.due,
                    "description_data": desc_data,
                    "custom_fields": custom_data,
                    "extracted_at": datetime.utcnow().isoformat(),
                }

                # Validate record (only description data)
                is_valid, errors = validate_record(desc_data)

                if is_valid:
                    valid_records.append(record)
                    print(f"            Status: ✓ VALID")
                else:
                    record["validation_errors"] = errors
                    error_records.append(record)
                    print(f"            Status: ⚠ INVALID - {'; '.join(errors)}")

            except Exception as e:
                # Graceful error handling - log and continue
                print(f"            Status: ✗ ERROR - {e}", file=sys.stderr)
                error_records.append({
                    "card_id": card.id,
                    "card_name": card.name,
                    "card_url": card.url,
                    "extraction_error": str(e),
                    "extracted_at": datetime.utcnow().isoformat(),
                })

            # Add spacing every 10 cards for readability
            if i % 10 == 0 and i < len(cards):
                print()

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*70}")
        print("💾 Writing output files...")
        print(f"{'='*70}\n")

        # Write valid records
        valid_file = output_path / "litigation_dataset_clean.json"
        try:
            with open(valid_file, "w", encoding="utf-8") as f:
                json.dump(valid_records, f, indent=2, ensure_ascii=False)
            print(f"✓ Valid records:  {valid_file} ({len(valid_records)} records)")
        except Exception as e:
            print(f"✗ Failed to write valid records: {e}", file=sys.stderr)

        # Write error records if any
        if error_records:
            error_file = output_path / "litigation_dataset_errors.json"
            try:
                with open(error_file, "w", encoding="utf-8") as f:
                    json.dump(error_records, f, indent=2, ensure_ascii=False)
                print(f"⚠  Error records:  {error_file} ({len(error_records)} records)")
            except Exception as e:
                print(f"✗ Failed to write error records: {e}", file=sys.stderr)
        else:
            print("✓ No errors - all cards processed successfully!")

        # Calculate stats
        total_cards = len(cards)
        success_rate = (len(valid_records) / total_cards * 100) if total_cards > 0 else 0

        stats = {
            "board_name": target_board.name,
            "board_id": target_board.id,
            "total_cards": total_cards,
            "valid_records": len(valid_records),
            "error_records": len(error_records),
            "success_rate": success_rate,
            "extraction_timestamp": datetime.utcnow().isoformat(),
        }

        # Display summary
        print(f"\n{'='*70}")
        print("📊 EXTRACTION SUMMARY")
        print(f"{'='*70}")
        print(f"Board:           {stats['board_name']}")
        print(f"Board ID:        {stats['board_id']}")
        print(f"Total cards:     {stats['total_cards']}")
        print(f"Valid records:   {stats['valid_records']} ({success_rate:.1f}%)")
        print(f"Error records:   {stats['error_records']} ({100-success_rate:.1f}%)")
        print(f"Timestamp:       {stats['extraction_timestamp']}")
        print(f"{'='*70}\n")

        return stats


# ============================================================================
# CLI Entry Point
# ============================================================================

async def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract litigation data from Trello boards"
    )
    parser.add_argument(
        "board_name",
        help="Name of Trello board to extract from"
    )
    parser.add_argument(
        "--list",
        dest="list_name",
        help="Optional: Filter by list name"
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: output/)"
    )

    args = parser.parse_args()

    try:
        await extract_litigation_data(
            board_name=args.board_name,
            list_name=args.list_name,
            output_dir=args.output
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Extraction cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
