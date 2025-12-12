"""
Pattern Detector for Template Creation.

Automatically detects Brazilian legal patterns (CPF, CNPJ, OAB, CEP, currency)
in text and suggests Jinja2 field replacements.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PatternMatch:
    """Represents a detected pattern match."""
    type: str
    value: str
    start: int
    end: int
    suggested_field: str
    filter: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'value': self.value,
            'start': self.start,
            'end': self.end,
            'suggested_field': self.suggested_field,
            'filter': self.filter
        }


class PatternDetector:
    """
    Detects Brazilian legal document patterns in text.

    Supported patterns:
    - CPF (formatted and unformatted)
    - CNPJ (formatted and unformatted)
    - OAB registration numbers
    - CEP (postal codes)
    - Currency values (R$)
    - Dates (DD/MM/YYYY)
    - Phone numbers
    """

    # Pattern definitions with corresponding Jinja2 filters
    # Order matters: more specific patterns should come first
    PATTERNS = {
        'cpf': {
            # CPF: XXX.XXX.XXX-XX (formatted) or XXXXXXXXXXX (unformatted)
            'regex': r'(?<!\d)(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})(?!\d)',
            'filter': 'cpf',
            'description': 'CPF (Cadastro de Pessoa Física)'
        },
        'cnpj': {
            # CNPJ: XX.XXX.XXX/XXXX-XX (formatted) or XXXXXXXXXXXXXX (unformatted)
            'regex': r'(?<!\d)(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})(?!\d)',
            'filter': 'cnpj',
            'description': 'CNPJ (Cadastro Nacional de Pessoa Jurídica)'
        },
        'oab': {
            # OAB/SP 123.456 or SP 123456 or 123.456/SP
            'regex': r'OAB[/\s]*[A-Z]{2}\s*\d{1,6}\.?\d{0,3}|\d{1,6}\.?\d{0,3}\s*/?\s*[A-Z]{2}',
            'filter': 'oab',
            'description': 'Registro OAB'
        },
        'cep': {
            # CEP: XXXXX-XXX or XXXXXXXX
            'regex': r'(?<!\d)(\d{5}-\d{3}|\d{8})(?!\d)',
            'filter': 'cep',
            'description': 'CEP (Código de Endereçamento Postal)'
        },
        'valor': {
            'regex': r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}',
            'filter': 'valor',
            'description': 'Valor monetário'
        },
        'data': {
            'regex': r'\d{2}/\d{2}/\d{4}',
            'filter': 'data',
            'description': 'Data (DD/MM/YYYY)'
        },
        'telefone': {
            'regex': r'\(?\d{2}\)?\s*\d{4,5}-?\d{4}',
            'filter': 'telefone',
            'description': 'Telefone'
        }
    }

    def __init__(self, patterns: Optional[Dict] = None):
        """
        Initialize detector with optional custom patterns.

        Args:
            patterns: Dict of pattern definitions to override/extend defaults
        """
        self.patterns = {**self.PATTERNS}
        if patterns:
            self.patterns.update(patterns)

    def detect_pattern(self, text: str, pattern_type: str) -> List[PatternMatch]:
        """
        Detect all occurrences of a specific pattern type.

        Args:
            text: Text to search
            pattern_type: Type of pattern to detect (e.g., 'cpf', 'cnpj')

        Returns:
            List of PatternMatch objects
        """
        if pattern_type not in self.patterns:
            raise ValueError(f"Unknown pattern type: {pattern_type}")

        pattern_def = self.patterns[pattern_type]
        regex = pattern_def['regex']
        matches = []

        for match in re.finditer(regex, text, re.IGNORECASE):
            matches.append(PatternMatch(
                type=pattern_type,
                value=match.group(0),
                start=match.start(),
                end=match.end(),
                suggested_field=self.suggest_field_name(pattern_type, match.group(0)),
                filter=pattern_def['filter']
            ))

        return matches

    def detect_all(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect all supported patterns in text.

        Args:
            text: Text to search

        Returns:
            List of match dicts sorted by position
        """
        all_matches = []

        for pattern_type in self.patterns:
            matches = self.detect_pattern(text, pattern_type)
            all_matches.extend([m.to_dict() for m in matches])

        # Sort by start position
        all_matches.sort(key=lambda x: x['start'])

        # Remove overlapping matches (keep first/longer)
        filtered = []
        last_end = -1
        for match in all_matches:
            if match['start'] >= last_end:
                filtered.append(match)
                last_end = match['end']

        return filtered

    def suggest_field_name(self, pattern_type: str, value: str) -> str:
        """
        Suggest a Jinja2 field name for a detected pattern.

        Args:
            pattern_type: Type of pattern
            value: Matched value

        Returns:
            Suggested field name (e.g., 'cpf', 'cnpj_empresa')
        """
        # Base field name is the pattern type
        return pattern_type

    def get_jinja_replacement(self, match: Dict[str, Any]) -> str:
        """
        Get Jinja2 replacement string for a match.

        Args:
            match: Match dict from detect_all()

        Returns:
            Jinja2 variable string (e.g., '{{ cpf | cpf }}')
        """
        field = match['suggested_field']
        filter_name = match['filter']
        return f"{{{{ {field} | {filter_name} }}}}"

    def apply_detections(self, text: str, matches: List[Dict[str, Any]]) -> str:
        """
        Replace detected patterns with Jinja2 variables.

        Args:
            text: Original text
            matches: List of matches to replace

        Returns:
            Text with patterns replaced by Jinja2 variables
        """
        # Sort matches by position (reverse order for safe replacement)
        sorted_matches = sorted(matches, key=lambda x: x['start'], reverse=True)

        result = text
        for match in sorted_matches:
            replacement = self.get_jinja_replacement(match)
            result = result[:match['start']] + replacement + result[match['end']:]

        return result
