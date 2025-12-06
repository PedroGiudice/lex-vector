"""
Text normalization utilities for Brazilian legal documents.
Handles names, addresses, documents (CPF/CNPJ), and special characters.

This module provides deterministic text normalization for:
- Whitespace anomalies (multiple spaces, NBSP, tabs)
- Case normalization (Title Case with Brazilian rules)
- Address formatting (logradouro expansions, number indicators)
- Document formatting (CPF, CNPJ, CEP, OAB)
- Punctuation normalization
"""

import re
import unicodedata
from typing import Any, Callable, Dict, Optional

# === CONSTANTS ===

# Connectives that stay lowercase in Brazilian names (except at start)
LOWERCASE_CONNECTIVES = frozenset({
    'da', 'de', 'do', 'das', 'dos', 'e', 'del', 'di', 'della', 'van', 'von'
})

# Abbreviations that stay uppercase
UPPERCASE_ABBREVIATIONS = frozenset({
    'LTDA', 'S/A', 'SA', 'ME', 'EPP', 'EIRELI', 'CIA', 'CIA.',
    'SS', 'S.S.', 'S/S', 'SIMPLES'
})

# Roman numerals regex - matches valid Roman numerals I through MMMCMXCIX
ROMAN_NUMERAL_PATTERN = re.compile(
    r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$',
    re.IGNORECASE
)

# Address type expansions (tuple of pattern, replacement)
# Order matters - longer patterns first to avoid partial matches
ADDRESS_EXPANSIONS = [
    (r'\bAV\.?\s+', 'Avenida '),
    (r'\bTV\.?\s+', 'Travessa '),
    (r'\bAL\.?\s+', 'Alameda '),
    (r'\bPÇA?\.?\s+', 'Praça '),
    (r'\bPCA\.?\s+', 'Praça '),
    (r'\bLGO?\.?\s+', 'Largo '),
    (r'\bVL\.?\s+', 'Vila '),
    (r'\bESTR?\.?\s+', 'Estrada '),
    (r'\bROD\.?\s+', 'Rodovia '),
    (r'\bR\.?\s+', 'Rua '),  # Must come after longer patterns
]

# Honorific patterns (pattern, replacement function or string)
HONORIFIC_PATTERNS = [
    (r'\bDRA\.?\s+', 'Dra. '),
    (r'\bDR\.?\s+', 'Dr. '),
    (r'\bSRA\.?\s+', 'Sra. '),
    (r'\bSR\.?\s+', 'Sr. '),
    (r'\bPROFA\.?\s+', 'Profa. '),
    (r'\bPROF\.?\s+', 'Prof. '),
    (r'\bENGº?\.?\s+', 'Eng. '),
    (r'\bARQ\.?\s+', 'Arq. '),
    (r'\bADV\.?\s+', 'Adv. '),
]


# === WHITESPACE FUNCTIONS ===

def normalize_whitespace(text: Optional[str]) -> Optional[str]:
    """
    Remove extra whitespace, normalize to single spaces.
    Handles: leading/trailing, multiple spaces, NBSP, tabs.

    Args:
        text: Input string or None

    Returns:
        Normalized string with single spaces, or None if input is None

    Examples:
        >>> normalize_whitespace("  João Silva  ")
        'João Silva'
        >>> normalize_whitespace("Rua  das   Flores")
        'Rua das Flores'
        >>> normalize_whitespace("João\\u00a0Silva")  # NBSP
        'João Silva'
        >>> normalize_whitespace(" \\t Maria  ")
        'Maria'
    """
    if text is None:
        return None
    if not isinstance(text, str):
        text = str(text)

    # Replace non-breaking space (U+00A0) and tabs with regular space
    text = text.replace('\u00a0', ' ').replace('\t', ' ')
    # Collapse multiple spaces to single
    text = re.sub(r' +', ' ', text)
    # Strip leading/trailing
    return text.strip()


# === NAME FUNCTIONS ===

def is_roman_numeral(word: str) -> bool:
    """
    Check if word is a valid Roman numeral (I through MMMCMXCIX).

    Args:
        word: Word to check

    Returns:
        True if valid Roman numeral, False otherwise

    Examples:
        >>> is_roman_numeral("II")
        True
        >>> is_roman_numeral("XIV")
        True
        >>> is_roman_numeral("IIII")
        False
        >>> is_roman_numeral("ABC")
        False
    """
    if not word:
        return False
    # Filter out empty matches (regex matches empty string for all optional groups)
    if not word.strip():
        return False
    return bool(ROMAN_NUMERAL_PATTERN.match(word))


def normalize_name(text: Optional[str]) -> Optional[str]:
    """
    Normalize Brazilian person/company name to proper title case.

    Rules:
        - Connectives (da, de, do, etc.) stay lowercase (except at start)
        - Abbreviations (LTDA, S/A, etc.) stay uppercase
        - Roman numerals stay uppercase
        - Ordinals (1º, 2ª) preserved as-is
        - Everything else: Title Case

    Args:
        text: Name to normalize

    Returns:
        Normalized name or None if input is None

    Examples:
        >>> normalize_name("MARIA DA SILVA")
        'Maria da Silva'
        >>> normalize_name("joao de souza")
        'João de Souza'
        >>> normalize_name("empresa teste ltda")
        'Empresa Teste LTDA'
        >>> normalize_name("papa joao paulo ii")
        'Papa Joao Paulo II'
    """
    if text is None:
        return None

    text = normalize_whitespace(text)
    if not text:
        return text

    words = text.split()
    result = []

    for i, word in enumerate(words):
        word_upper = word.upper()
        word_lower = word.lower()

        # Check for uppercase abbreviations (LTDA, S/A, etc.)
        if word_upper in UPPERCASE_ABBREVIATIONS:
            result.append(word_upper)

        # Check for connectives (da, de, do, etc.) - NOT at start
        # NOTE: Must check connectives BEFORE Roman numerals (di, del are both)
        elif word_lower in LOWERCASE_CONNECTIVES and i > 0:
            result.append(word_lower)

        # Check for Roman numerals (but not connectives)
        elif is_roman_numeral(word) and word_lower not in LOWERCASE_CONNECTIVES:
            result.append(word.upper())

        # Check for ordinals (1º, 2ª, 10º)
        elif re.match(r'^\d+[ºª]$', word):
            result.append(word)

        # Check for already formatted abbreviations with period
        elif re.match(r'^[A-Z]{1,3}\.$', word):
            result.append(word)

        # Default: Capitalize first letter, lowercase rest
        else:
            result.append(word.capitalize())

    return ' '.join(result)


def normalize_honorific(text: Optional[str]) -> Optional[str]:
    """
    Normalize honorific titles in text.

    Args:
        text: Text containing honorifics

    Returns:
        Text with normalized honorifics or None if input is None

    Examples:
        >>> normalize_honorific("DR JOÃO")
        'Dr. JOÃO'
        >>> normalize_honorific("DRA MARIA")
        'Dra. MARIA'
        >>> normalize_honorific("SR CARLOS")
        'Sr. CARLOS'
    """
    if text is None:
        return None

    text = normalize_whitespace(text)
    if not text:
        return text

    # Apply honorific expansions
    for pattern, replacement in HONORIFIC_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


# === ADDRESS FUNCTIONS ===

def normalize_address(text: Optional[str]) -> Optional[str]:
    """
    Normalize Brazilian address format.

    Operations:
        1. Expand abbreviations (R. → Rua, AV. → Avenida)
        2. Standardize number indicator (N., N°, Nº → nº)
        3. Standardize apartment/block (AP. → Apto., BL. → Bloco)
        4. Standardize "without number" (S/N → s/nº)
        5. Apply name normalization for proper casing

    Args:
        text: Address to normalize

    Returns:
        Normalized address or None if input is None

    Examples:
        >>> normalize_address("R. DAS FLORES")
        'Rua das Flores'
        >>> normalize_address("AV BRASIL N 500")
        'Avenida Brasil nº 500'
    """
    if text is None:
        return None

    text = normalize_whitespace(text)
    if not text:
        return text

    # Apply address type expansions
    for pattern, replacement in ADDRESS_EXPANSIONS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # S/N variations → s/nº (MUST be before number indicator standardization)
    text = re.sub(r'\bS/?N[ºo]?\b', 's/nº', text, flags=re.IGNORECASE)
    text = re.sub(r'\bS\.\s*N\.', 's/nº', text, flags=re.IGNORECASE)
    text = re.sub(r'\bS\s+N\b', 's/nº', text, flags=re.IGNORECASE)

    # Number indicator standardization (various forms → "nº ")
    text = re.sub(r'\b[Nn][°ºoO.]?\s*', 'nº ', text)
    text = re.sub(r'\bNUM\.?\s*', 'nº ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNO\.?\s*', 'nº ', text, flags=re.IGNORECASE)

    # Apartment/Unit standardization
    text = re.sub(r'\bAPTO?\.?\s*', 'Apto. ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAPT\.?\s*', 'Apto. ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAP\.?\s*', 'Apto. ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bBLOCO\s+', 'Bloco ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bBL\.?\s*', 'Bloco ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSL\.?\s*', 'Sala ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSALA\s+', 'Sala ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bCJ\.?\s*', 'Conjunto ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bCONJ\.?\s*', 'Conjunto ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bLJ\.?\s*', 'Loja ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bLOJA\s+', 'Loja ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSOB\.?\s*', 'Sobreloja ', text, flags=re.IGNORECASE)

    # Clean up multiple spaces that may have been introduced
    text = normalize_whitespace(text)

    # Apply proper casing while preserving special tokens
    parts = text.split()
    result = []
    for part in parts:
        part_lower = part.lower()
        # Preserve lowercase tokens
        if part_lower in ('nº', 's/nº'):
            result.append(part_lower)
        elif part_lower in LOWERCASE_CONNECTIVES:
            result.append(part_lower)
        # Numbers stay as-is
        elif part[0].isdigit():
            result.append(part)
        # Already properly formatted (Apto., Bloco, etc.)
        elif part in ('Apto.', 'Bloco', 'Sala', 'Conjunto', 'Loja', 'Sobreloja',
                      'Rua', 'Avenida', 'Travessa', 'Alameda', 'Praça', 'Largo',
                      'Vila', 'Estrada', 'Rodovia'):
            result.append(part)
        # Capitalize others
        elif part.islower() or part.isupper():
            result.append(part.capitalize())
        else:
            result.append(part)

    return ' '.join(result)


# === DOCUMENT FORMATTING FUNCTIONS ===

def format_cpf(cpf: Optional[str]) -> Optional[str]:
    """
    Format CPF to standard format: 123.456.789-01

    Accepts any input, extracts digits, formats if valid.
    Returns original if not exactly 11 digits.

    Args:
        cpf: CPF string (formatted or unformatted)

    Returns:
        Formatted CPF or original if invalid

    Examples:
        >>> format_cpf("12345678901")
        '123.456.789-01'
        >>> format_cpf("123.456.789-01")
        '123.456.789-01'
        >>> format_cpf("invalid")
        'invalid'
    """
    if cpf is None:
        return None

    # Extract only digits
    digits = re.sub(r'\D', '', str(cpf))

    # Must be exactly 11 digits
    if len(digits) != 11:
        return cpf  # Return original if invalid

    # Format: 000.000.000-00
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def format_cnpj(cnpj: Optional[str]) -> Optional[str]:
    """
    Format CNPJ to standard format: 12.345.678/0001-99

    Accepts any input, extracts digits, formats if valid.
    Returns original if not exactly 14 digits.

    Args:
        cnpj: CNPJ string (formatted or unformatted)

    Returns:
        Formatted CNPJ or original if invalid

    Examples:
        >>> format_cnpj("12345678000199")
        '12.345.678/0001-99'
        >>> format_cnpj("12.345.678/0001-99")
        '12.345.678/0001-99'
    """
    if cnpj is None:
        return None

    # Extract only digits
    digits = re.sub(r'\D', '', str(cnpj))

    # Must be exactly 14 digits
    if len(digits) != 14:
        return cnpj  # Return original if invalid

    # Format: 00.000.000/0000-00
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def format_cep(cep: Optional[str]) -> Optional[str]:
    """
    Format CEP to standard format: 01310-100

    Args:
        cep: CEP string (formatted or unformatted)

    Returns:
        Formatted CEP or original if invalid

    Examples:
        >>> format_cep("01310100")
        '01310-100'
        >>> format_cep("01310 100")
        '01310-100'
        >>> format_cep("01310-100")
        '01310-100'
    """
    if cep is None:
        return None

    # Zero-pad if input is numeric (int) and 7 digits (missing leading zero)
    if isinstance(cep, int):
        cep_str = str(cep).zfill(8)
    else:
        cep_str = str(cep)

    # Extract only digits
    digits = re.sub(r'\D', '', cep_str)

    # Must be exactly 8 digits
    if len(digits) != 8:
        return cep  # Return original if invalid

    # Format: 00000-000
    return f"{digits[:5]}-{digits[5:]}"


def format_oab(oab: Optional[str]) -> Optional[str]:
    """
    Format OAB registration to standard format: OAB/UF 000.000

    Args:
        oab: OAB string in various formats

    Returns:
        Formatted OAB or original if cannot parse

    Examples:
        >>> format_oab("123456SP")
        'OAB/SP 123.456'
        >>> format_oab("123456/SP")
        'OAB/SP 123.456'
        >>> format_oab("OAB/SP 123456")
        'OAB/SP 123.456'
    """
    if oab is None:
        return None

    oab_str = str(oab).upper().strip()

    # Try pattern: digits + UF
    match = re.match(r'^(\d+)\s*/?([A-Z]{2})$', oab_str)
    if match:
        number, uf = match.groups()
    else:
        # Try pattern: OAB/UF + digits
        match = re.match(r'^OAB\s*/?([A-Z]{2})\s*(\d+)$', oab_str)
        if match:
            uf, number = match.groups()
        else:
            # Try pattern: UF + digits
            match = re.match(r'^([A-Z]{2})\s*/?(\d+)$', oab_str)
            if match:
                uf, number = match.groups()
            else:
                return oab  # Return original if can't parse

    # Format number with dot separator for thousands
    number = number.lstrip('0') or '0'
    if len(number) > 3:
        formatted_number = f"{number[:-3]}.{number[-3:]}"
    else:
        formatted_number = number

    return f"OAB/{uf} {formatted_number}"


# === PUNCTUATION FUNCTIONS ===

def normalize_punctuation(text: Optional[str]) -> Optional[str]:
    """
    Fix common punctuation issues.

    Operations:
        - Remove space before punctuation
        - Add space after punctuation (if missing)
        - Collapse multiple punctuation (except ellipsis)
        - Standardize quotation marks

    Args:
        text: Text to normalize

    Returns:
        Text with normalized punctuation or None if input is None

    Examples:
        >>> normalize_punctuation("texto .")
        'texto.'
        >>> normalize_punctuation("texto.Outro")
        'texto. Outro'
        >>> normalize_punctuation("texto..")
        'texto.'
    """
    if text is None:
        return None

    text = str(text)

    # Remove space before punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)

    # Collapse multiple punctuation (preserve ...)
    text = re.sub(r'\.{4,}', '...', text)  # 4+ dots → ellipsis
    text = re.sub(r'(?<!\.)\.\.(?!\.)', '.', text)  # exactly 2 dots → 1
    text = re.sub(r',+', ',', text)
    text = re.sub(r';+', ';', text)
    text = re.sub(r':+', ':', text)

    # Add space after punctuation if followed by letter (not for abbreviations)
    # But skip things like "Dr.", "nº", etc.
    text = re.sub(r'([.,;:!?])([A-ZÀ-Ú])', r'\1 \2', text)

    # Standardize quotes to straight double quotes
    # Curly/smart double quotes: " " « »
    text = text.replace('\u201c', '"')  # Left double quotation mark
    text = text.replace('\u201d', '"')  # Right double quotation mark
    text = text.replace('\u00ab', '"')  # Left-pointing double angle quotation mark
    text = text.replace('\u00bb', '"')  # Right-pointing double angle quotation mark

    # Smart single quotes: ' '
    text = text.replace('\u2018', "'")  # Left single quotation mark
    text = text.replace('\u2019', "'")  # Right single quotation mark

    return text


# === COMPOSITE FUNCTIONS ===

def normalize_all(data: Dict[str, Any], field_types: Dict[str, str]) -> Dict[str, Any]:
    """
    Normalize all fields in a dictionary based on their types.

    Args:
        data: Dictionary with field values
        field_types: Dictionary mapping field names to types:
            - 'name': Apply normalize_name
            - 'address': Apply normalize_address
            - 'cpf': Apply format_cpf
            - 'cnpj': Apply format_cnpj
            - 'cep': Apply format_cep
            - 'oab': Apply format_oab
            - 'text': Apply normalize_whitespace + normalize_punctuation
            - 'raw': No normalization (preserve as-is)

    Returns:
        New dictionary with normalized values

    Examples:
        >>> data = {"nome": "MARIA DA SILVA", "cpf": "12345678901"}
        >>> types = {"nome": "name", "cpf": "cpf"}
        >>> normalize_all(data, types)
        {'nome': 'Maria da Silva', 'cpf': '123.456.789-01'}
    """
    result = {}

    normalizers: Dict[str, Callable[[Any], Any]] = {
        'name': normalize_name,
        'address': normalize_address,
        'cpf': format_cpf,
        'cnpj': format_cnpj,
        'cep': format_cep,
        'oab': format_oab,
        'text': lambda x: normalize_punctuation(normalize_whitespace(x)),
        'raw': lambda x: x,  # No-op
    }

    for field, value in data.items():
        field_type = field_types.get(field, 'text')  # Default to text normalization
        normalizer = normalizers.get(field_type, normalizers['text'])

        if value is not None:
            result[field] = normalizer(value)
        else:
            result[field] = None

    return result
