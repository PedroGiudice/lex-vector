# tests/test_pattern_detector.py
import pytest
from src.pattern_detector import PatternDetector

def test_detect_cpf_formatted():
    """Detector should find formatted CPF patterns."""
    text = "O cliente João, CPF 123.456.789-01, solicita..."
    detector = PatternDetector()
    matches = detector.detect_all(text)

    assert len(matches) >= 1
    cpf_match = next((m for m in matches if m['type'] == 'cpf'), None)
    assert cpf_match is not None
    assert cpf_match['value'] == '123.456.789-01'
    assert cpf_match['start'] == 20  # "O cliente João, CPF " = 20 chars
    assert cpf_match['end'] == 34    # 20 + 14 = 34

def test_detect_cpf_unformatted():
    """Detector should find unformatted CPF patterns."""
    text = "CPF: 12345678901"
    detector = PatternDetector()
    matches = detector.detect_all(text)

    cpf_match = next((m for m in matches if m['type'] == 'cpf'), None)
    assert cpf_match is not None
    assert cpf_match['value'] == '12345678901'

def test_detect_cnpj():
    """Detector should find CNPJ patterns."""
    text = "Empresa XPTO, CNPJ 12.345.678/0001-99"
    detector = PatternDetector()
    matches = detector.detect_all(text)

    cnpj_match = next((m for m in matches if m['type'] == 'cnpj'), None)
    assert cnpj_match is not None

def test_detect_oab():
    """Detector should find OAB patterns."""
    text = "Advogado inscrito na OAB/SP 123.456"
    detector = PatternDetector()
    matches = detector.detect_all(text)

    oab_match = next((m for m in matches if m['type'] == 'oab'), None)
    assert oab_match is not None

def test_detect_currency():
    """Detector should find Brazilian currency values."""
    text = "O valor de R$ 1.234,56 será pago"
    detector = PatternDetector()
    matches = detector.detect_all(text)

    currency_match = next((m for m in matches if m['type'] == 'valor'), None)
    assert currency_match is not None
    assert 'R$' in currency_match['value'] or '1.234,56' in currency_match['value']

def test_detect_cep():
    """Detector should find CEP patterns."""
    text = "CEP 01310-100, São Paulo"
    detector = PatternDetector()
    matches = detector.detect_all(text)

    cep_match = next((m for m in matches if m['type'] == 'cep'), None)
    assert cep_match is not None

def test_suggest_field_name():
    """Detector should suggest appropriate Jinja2 field names."""
    detector = PatternDetector()

    assert detector.suggest_field_name('cpf', '123.456.789-01') == 'cpf'
    assert detector.suggest_field_name('cnpj', '12.345.678/0001-99') == 'cnpj'
    assert detector.suggest_field_name('valor', 'R$ 1.234,56') == 'valor'
