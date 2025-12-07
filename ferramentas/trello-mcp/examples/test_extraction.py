"""
Test script for litigation data extraction functions.

Tests:
- CPF validation (valid/invalid checksums)
- CNPJ validation (valid/invalid checksums)
- Brazilian currency parsing
- Record validation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import validation functions
from extract_litigation_data import (
    validate_cpf,
    validate_cnpj,
    parse_brazilian_currency,
    validate_record,
)


def test_cpf_validation():
    """Test CPF validation with known valid/invalid values."""
    print("\n=== Testing CPF Validation ===")

    # Valid CPFs
    valid_cpfs = [
        "11144477735",  # Valid CPF
        "52998224725",  # Valid CPF
    ]

    for cpf in valid_cpfs:
        result = validate_cpf(cpf)
        status = "✓" if result else "✗"
        print(f"{status} {cpf}: {result}")
        assert result, f"Expected {cpf} to be valid"

    # Invalid CPFs
    invalid_cpfs = [
        "11111111111",  # All same digits
        "12345678901",  # Invalid checksum
        "123456789",    # Too short
    ]

    for cpf in invalid_cpfs:
        result = validate_cpf(cpf)
        status = "✓" if not result else "✗"
        print(f"{status} {cpf}: {result} (should be False)")
        assert not result, f"Expected {cpf} to be invalid"

    print("All CPF tests passed!\n")


def test_cnpj_validation():
    """Test CNPJ validation with known valid/invalid values."""
    print("=== Testing CNPJ Validation ===")

    # Valid CNPJs
    valid_cnpjs = [
        "11222333000181",  # Valid CNPJ
        "06990590000123",  # Valid CNPJ
    ]

    for cnpj in valid_cnpjs:
        result = validate_cnpj(cnpj)
        status = "✓" if result else "✗"
        print(f"{status} {cnpj}: {result}")
        assert result, f"Expected {cnpj} to be valid"

    # Invalid CNPJs
    invalid_cnpjs = [
        "11111111111111",  # All same digits
        "12345678000195",  # Invalid checksum
        "123456789",       # Too short
    ]

    for cnpj in invalid_cnpjs:
        result = validate_cnpj(cnpj)
        status = "✓" if not result else "✗"
        print(f"{status} {cnpj}: {result} (should be False)")
        assert not result, f"Expected {cnpj} to be invalid"

    print("All CNPJ tests passed!\n")


def test_currency_parsing():
    """Test Brazilian currency format parsing."""
    print("=== Testing Currency Parsing ===")

    test_cases = [
        ("1.000,00", 1000.0),
        ("10.000,50", 10000.5),
        ("1000,00", 1000.0),
        ("1000", 1000.0),
        ("1.234.567,89", 1234567.89),
        ("500", 500.0),
    ]

    for input_str, expected in test_cases:
        result = parse_brazilian_currency(input_str)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_str}' -> {result} (expected {expected})")
        assert result == expected, f"Expected {expected}, got {result}"

    print("All currency tests passed!\n")


def test_record_validation():
    """Test record validation logic."""
    print("=== Testing Record Validation ===")

    # Valid record
    valid_record = {
        "cpf": "11144477735",
        "name": "João Silva",
        "email": "joao@example.com",
        "phone": "11987654321",
    }

    is_valid, errors = validate_record(valid_record)
    print(f"Valid record: {is_valid} (errors: {errors})")
    assert is_valid, f"Expected valid record, got errors: {errors}"

    # Invalid record - missing identifier
    invalid_record_1 = {
        "name": "Maria Santos",
    }

    is_valid, errors = validate_record(invalid_record_1)
    print(f"Missing identifier: {is_valid} (errors: {errors})")
    assert not is_valid, "Expected invalid due to missing identifier"

    # Invalid record - bad CPF checksum
    invalid_record_2 = {
        "cpf": "12345678901",  # Invalid checksum
        "name": "Pedro Oliveira",
    }

    is_valid, errors = validate_record(invalid_record_2)
    print(f"Invalid CPF: {is_valid} (errors: {errors})")
    assert not is_valid, "Expected invalid due to bad CPF"

    print("All validation tests passed!\n")


if __name__ == "__main__":
    try:
        test_cpf_validation()
        test_cnpj_validation()
        test_currency_parsing()
        test_record_validation()

        print("="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
