"""
Standalone test for validation functions (no dependencies).

Copy-paste validation functions here for isolated testing.
"""


def validate_cpf(cpf: str) -> bool:
    """Validate Brazilian CPF using checksum algorithm."""
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
    """Validate Brazilian CNPJ using checksum algorithm."""
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


def parse_brazilian_currency(value_str: str):
    """Parse Brazilian currency format to float."""
    try:
        cleaned = value_str.replace(".", "").replace(",", ".")
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


# ============================================================================
# Tests
# ============================================================================

def test_cpf():
    print("\n=== CPF Validation Tests ===")

    valid = ["11144477735", "52998224725"]
    for cpf in valid:
        result = validate_cpf(cpf)
        print(f"  {'✓' if result else '✗'} {cpf}: {result}")
        assert result

    invalid = ["11111111111", "12345678901", "123456789"]
    for cpf in invalid:
        result = validate_cpf(cpf)
        print(f"  {'✓' if not result else '✗'} {cpf}: {result} (invalid)")
        assert not result

    print("  All CPF tests passed!")


def test_cnpj():
    print("\n=== CNPJ Validation Tests ===")

    valid = ["11222333000181", "06990590000123"]
    for cnpj in valid:
        result = validate_cnpj(cnpj)
        print(f"  {'✓' if result else '✗'} {cnpj}: {result}")
        assert result

    invalid = ["11111111111111", "12345678000191", "1234567"]
    for cnpj in invalid:
        result = validate_cnpj(cnpj)
        print(f"  {'✓' if not result else '✗'} {cnpj}: {result} (invalid)")
        assert not result

    print("  All CNPJ tests passed!")


def test_currency():
    print("\n=== Currency Parsing Tests ===")

    tests = [
        ("1.000,00", 1000.0),
        ("10.000,50", 10000.5),
        ("1000,00", 1000.0),
        ("1000", 1000.0),
        ("1.234.567,89", 1234567.89),
    ]

    for input_str, expected in tests:
        result = parse_brazilian_currency(input_str)
        print(f"  {'✓' if result == expected else '✗'} '{input_str}' -> {result}")
        assert result == expected

    print("  All currency tests passed!")


if __name__ == "__main__":
    print("="*70)
    print("VALIDATION FUNCTION TESTS")
    print("="*70)

    test_cpf()
    test_cnpj()
    test_currency()

    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED")
    print("="*70)
