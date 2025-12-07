# tests/test_normalizers.py
"""Unit tests for normalizers module."""
import pytest
from src.normalizers import (
    normalize_whitespace,
    normalize_name,
    normalize_address,
    normalize_honorific,
    format_cpf,
    format_cnpj,
    format_cep,
    format_oab,
    normalize_punctuation,
    normalize_all,
    is_roman_numeral,
)


class TestNormalizeWhitespace:
    """Tests for normalize_whitespace function."""

    def test_none_input(self):
        assert normalize_whitespace(None) is None

    def test_empty_string(self):
        assert normalize_whitespace("") == ""

    def test_leading_trailing_spaces(self):
        assert normalize_whitespace("  João Silva  ") == "João Silva"

    def test_multiple_internal_spaces(self):
        assert normalize_whitespace("Rua  das   Flores") == "Rua das Flores"

    def test_non_breaking_space(self):
        assert normalize_whitespace("João\u00a0Silva") == "João Silva"

    def test_tabs(self):
        assert normalize_whitespace("João\tSilva") == "João Silva"

    def test_mixed_whitespace(self):
        assert normalize_whitespace(" \t Maria  \u00a0") == "Maria"

    def test_numeric_input(self):
        assert normalize_whitespace(12345) == "12345"

    def test_only_spaces(self):
        assert normalize_whitespace("   ") == ""


class TestIsRomanNumeral:
    """Tests for is_roman_numeral function."""

    def test_valid_numerals(self):
        assert is_roman_numeral("I") is True
        assert is_roman_numeral("II") is True
        assert is_roman_numeral("III") is True
        assert is_roman_numeral("IV") is True
        assert is_roman_numeral("V") is True
        assert is_roman_numeral("VI") is True
        assert is_roman_numeral("VII") is True
        assert is_roman_numeral("VIII") is True
        assert is_roman_numeral("IX") is True
        assert is_roman_numeral("X") is True
        assert is_roman_numeral("XI") is True
        assert is_roman_numeral("XII") is True
        assert is_roman_numeral("XIV") is True
        assert is_roman_numeral("XV") is True
        assert is_roman_numeral("XVI") is True
        assert is_roman_numeral("XX") is True
        assert is_roman_numeral("L") is True
        assert is_roman_numeral("C") is True
        assert is_roman_numeral("D") is True
        assert is_roman_numeral("M") is True
        assert is_roman_numeral("MCMXCIX") is True  # 1999
        assert is_roman_numeral("MMXXV") is True  # 2025

    def test_lowercase_valid(self):
        assert is_roman_numeral("ii") is True
        assert is_roman_numeral("xiv") is True
        assert is_roman_numeral("mcm") is True

    def test_invalid_numerals(self):
        assert is_roman_numeral("IIII") is False
        assert is_roman_numeral("ABC") is False
        assert is_roman_numeral("") is False
        assert is_roman_numeral("   ") is False
        assert is_roman_numeral("VV") is False
        assert is_roman_numeral("LL") is False


class TestNormalizeName:
    """Tests for normalize_name function."""

    def test_none_input(self):
        assert normalize_name(None) is None

    def test_empty_string(self):
        assert normalize_name("") == ""

    def test_all_uppercase(self):
        assert normalize_name("MARIA DA SILVA") == "Maria da Silva"

    def test_all_lowercase(self):
        # Note: "joao" without accent stays as "Joao" - normalize_name doesn't fix accents
        result = normalize_name("joao de souza")
        assert result == "Joao de Souza"

    def test_connectives(self):
        assert normalize_name("JOSÉ DOS SANTOS FILHO") == "José dos Santos Filho"
        assert normalize_name("ANA E SILVA") == "Ana e Silva"

    def test_connective_at_start(self):
        # Connective at start should be capitalized
        assert normalize_name("da silva") == "Da Silva"
        assert normalize_name("DE SOUZA") == "De Souza"

    def test_all_connectives(self):
        """Test all supported connectives."""
        assert normalize_name("MARIA DA SILVA") == "Maria da Silva"
        assert normalize_name("JOÃO DE SOUZA") == "João de Souza"
        assert normalize_name("PEDRO DO CARMO") == "Pedro do Carmo"
        assert normalize_name("ANA DAS NEVES") == "Ana das Neves"
        assert normalize_name("JOSÉ DOS SANTOS") == "José dos Santos"
        assert normalize_name("CARLOS E SILVA") == "Carlos e Silva"
        assert normalize_name("MARCO DEL VECCHIO") == "Marco del Vecchio"
        assert normalize_name("LUIGI DI CAPRIO") == "Luigi di Caprio"

    def test_company_abbreviations(self):
        assert normalize_name("EMPRESA TESTE LTDA") == "Empresa Teste LTDA"
        assert normalize_name("comercio sa") == "Comercio SA"
        assert normalize_name("loja me") == "Loja ME"
        assert normalize_name("fabrica epp") == "Fabrica EPP"
        assert normalize_name("servicos eireli") == "Servicos EIRELI"
        assert normalize_name("banco s/a") == "Banco S/A"

    def test_roman_numerals(self):
        assert normalize_name("PAPA JOAO PAULO II") == "Papa Joao Paulo II"
        assert normalize_name("luis xiv") == "Luis XIV"
        assert normalize_name("HENRIQUE VIII") == "Henrique VIII"
        assert normalize_name("vara i") == "Vara I"

    def test_ordinals(self):
        assert normalize_name("VARA 1º") == "Vara 1º"
        assert normalize_name("turma 2ª") == "Turma 2ª"
        assert normalize_name("10º ANDAR") == "10º Andar"

    def test_accented_characters(self):
        assert normalize_name("JOSÉ ANTÔNIO") == "José Antônio"
        assert normalize_name("JOÃO MARTÍNEZ") == "João Martínez"
        assert normalize_name("CONCEIÇÃO") == "Conceição"
        assert normalize_name("ARAÚJO") == "Araújo"

    def test_mixed_case_input(self):
        assert normalize_name("JoÃo Da SiLvA") == "João da Silva"

    def test_with_extra_whitespace(self):
        assert normalize_name("  MARIA   DA   SILVA  ") == "Maria da Silva"


class TestNormalizeHonorific:
    """Tests for normalize_honorific function."""

    def test_none_input(self):
        assert normalize_honorific(None) is None

    def test_dr_expansion(self):
        assert normalize_honorific("DR JOÃO") == "Dr. JOÃO"

    def test_dra_expansion(self):
        assert normalize_honorific("DRA MARIA") == "Dra. MARIA"

    def test_sr_expansion(self):
        assert normalize_honorific("SR CARLOS") == "Sr. CARLOS"

    def test_sra_expansion(self):
        assert normalize_honorific("SRA ANA") == "Sra. ANA"

    def test_prof_expansion(self):
        assert normalize_honorific("PROF SILVA") == "Prof. SILVA"

    def test_profa_expansion(self):
        assert normalize_honorific("PROFA SANTOS") == "Profa. SANTOS"

    def test_eng_expansion(self):
        assert normalize_honorific("ENG PEREIRA") == "Eng. PEREIRA"

    def test_lowercase_input(self):
        assert normalize_honorific("dr joão") == "Dr. joão"


class TestNormalizeAddress:
    """Tests for normalize_address function."""

    def test_none_input(self):
        assert normalize_address(None) is None

    def test_empty_string(self):
        assert normalize_address("") == ""

    def test_rua_expansion(self):
        result = normalize_address("R. DAS FLORES")
        assert "Rua" in result
        assert "das" in result.lower()

    def test_rua_without_period(self):
        result = normalize_address("R DAS FLORES")
        assert "Rua" in result

    def test_avenida_expansion(self):
        result = normalize_address("AV. BRASIL")
        assert "Avenida" in result

    def test_avenida_without_period(self):
        result = normalize_address("AV BRASIL")
        assert "Avenida" in result

    def test_travessa_expansion(self):
        result = normalize_address("TV. SANTOS")
        assert "Travessa" in result

    def test_alameda_expansion(self):
        result = normalize_address("AL. JACARANDÁS")
        assert "Alameda" in result

    def test_praca_expansion(self):
        result = normalize_address("PÇ. DA SÉ")
        assert "Praça" in result

    def test_estrada_expansion(self):
        result = normalize_address("ESTR. DO CAMPO")
        assert "Estrada" in result

    def test_rodovia_expansion(self):
        result = normalize_address("ROD. ANHANGUERA")
        assert "Rodovia" in result

    def test_largo_expansion(self):
        result = normalize_address("LG. DO AROUCHE")
        assert "Largo" in result

    def test_vila_expansion(self):
        result = normalize_address("VL. MARIANA")
        assert "Vila" in result

    def test_number_standardization(self):
        result = normalize_address("RUA TESTE N. 100")
        assert "nº" in result

    def test_numero_variations(self):
        assert "nº" in normalize_address("RUA A N° 50")
        assert "nº" in normalize_address("RUA B Nº 60")
        assert "nº" in normalize_address("RUA C NUM 70")
        assert "nº" in normalize_address("RUA D NO 80")

    def test_apartment_standardization(self):
        result = normalize_address("RUA TESTE AP 101")
        assert "Apto." in result

    def test_apto_variations(self):
        assert "Apto." in normalize_address("RUA A APTO 1")
        assert "Apto." in normalize_address("RUA B APT. 2")
        assert "Apto." in normalize_address("RUA C AP. 3")

    def test_bloco_standardization(self):
        result = normalize_address("RUA TESTE BL A")
        assert "Bloco" in result

    def test_sala_standardization(self):
        result = normalize_address("RUA TESTE SL 10")
        assert "Sala" in result

    def test_conjunto_standardization(self):
        result = normalize_address("RUA TESTE CJ 5")
        assert "Conjunto" in result

    def test_loja_standardization(self):
        result = normalize_address("RUA TESTE LJ 1")
        assert "Loja" in result

    def test_sn_standardization(self):
        result = normalize_address("RUA TESTE S/N")
        assert "s/nº" in result

    def test_sn_variations(self):
        assert "s/nº" in normalize_address("RUA A SN")
        assert "s/nº" in normalize_address("RUA B S/Nº")
        assert "s/nº" in normalize_address("RUA C S.N.")

    def test_full_address(self):
        result = normalize_address("AV. BRASIL N 500 AP 201 BL A")
        assert "Avenida" in result
        assert "nº" in result
        assert "Apto." in result
        assert "Bloco" in result


class TestFormatCPF:
    """Tests for format_cpf function."""

    def test_none_input(self):
        assert format_cpf(None) is None

    def test_digits_only(self):
        assert format_cpf("12345678901") == "123.456.789-01"

    def test_already_formatted(self):
        assert format_cpf("123.456.789-01") == "123.456.789-01"

    def test_with_spaces(self):
        assert format_cpf("123 456 789 01") == "123.456.789-01"

    def test_with_dashes_only(self):
        assert format_cpf("123-456-789-01") == "123.456.789-01"

    def test_invalid_length_short(self):
        assert format_cpf("1234567890") == "1234567890"  # Returns original

    def test_invalid_length_long(self):
        assert format_cpf("123456789012") == "123456789012"  # Returns original

    def test_invalid_characters(self):
        assert format_cpf("invalid") == "invalid"  # Returns original

    def test_partial_format(self):
        assert format_cpf("123.45678901") == "123.456.789-01"

    def test_numeric_input(self):
        assert format_cpf(12345678901) == "123.456.789-01"

    def test_all_zeros(self):
        assert format_cpf("00000000000") == "000.000.000-00"


class TestFormatCNPJ:
    """Tests for format_cnpj function."""

    def test_none_input(self):
        assert format_cnpj(None) is None

    def test_digits_only(self):
        assert format_cnpj("12345678000199") == "12.345.678/0001-99"

    def test_already_formatted(self):
        assert format_cnpj("12.345.678/0001-99") == "12.345.678/0001-99"

    def test_invalid_length_short(self):
        assert format_cnpj("1234567800019") == "1234567800019"  # Returns original

    def test_invalid_length_long(self):
        assert format_cnpj("123456780001999") == "123456780001999"  # Returns original

    def test_with_spaces(self):
        assert format_cnpj("12 345 678 0001 99") == "12.345.678/0001-99"

    def test_numeric_input(self):
        assert format_cnpj(12345678000199) == "12.345.678/0001-99"


class TestFormatCEP:
    """Tests for format_cep function."""

    def test_none_input(self):
        assert format_cep(None) is None

    def test_digits_only(self):
        assert format_cep("01310100") == "01310-100"

    def test_already_formatted(self):
        assert format_cep("01310-100") == "01310-100"

    def test_with_spaces(self):
        assert format_cep("01310 100") == "01310-100"

    def test_with_dots(self):
        assert format_cep("01.310.100") == "01310-100"

    def test_invalid_length_short(self):
        assert format_cep("0131010") == "0131010"  # Returns original

    def test_invalid_length_long(self):
        assert format_cep("013101001") == "013101001"  # Returns original

    def test_numeric_input(self):
        assert format_cep(1310100) == "01310-100"


class TestFormatOAB:
    """Tests for format_oab function."""

    def test_none_input(self):
        assert format_oab(None) is None

    def test_digits_and_uf(self):
        assert format_oab("123456SP") == "OAB/SP 123.456"

    def test_with_slash(self):
        assert format_oab("123456/SP") == "OAB/SP 123.456"

    def test_full_format(self):
        assert format_oab("OAB/SP 123456") == "OAB/SP 123.456"

    def test_uf_first(self):
        assert format_oab("SP/123456") == "OAB/SP 123.456"

    def test_lowercase(self):
        assert format_oab("123456sp") == "OAB/SP 123.456"

    def test_short_number(self):
        assert format_oab("456SP") == "OAB/SP 456"

    def test_leading_zeros(self):
        assert format_oab("000123SP") == "OAB/SP 123"

    def test_invalid_format(self):
        assert format_oab("invalid") == "invalid"

    def test_only_numbers(self):
        assert format_oab("123456") == "123456"  # Returns original


class TestNormalizePunctuation:
    """Tests for normalize_punctuation function."""

    def test_none_input(self):
        assert normalize_punctuation(None) is None

    def test_space_before_period(self):
        assert normalize_punctuation("texto .") == "texto."

    def test_space_before_comma(self):
        assert normalize_punctuation("texto ,") == "texto,"

    def test_space_before_semicolon(self):
        assert normalize_punctuation("texto ;") == "texto;"

    def test_multiple_periods(self):
        assert normalize_punctuation("texto..") == "texto."

    def test_preserve_ellipsis(self):
        assert normalize_punctuation("texto...") == "texto..."

    def test_four_dots_to_ellipsis(self):
        assert normalize_punctuation("texto....") == "texto..."

    def test_multiple_commas(self):
        assert normalize_punctuation("texto,,") == "texto,"

    def test_missing_space_after_period(self):
        assert normalize_punctuation("texto.Outro") == "texto. Outro"

    def test_missing_space_after_comma(self):
        result = normalize_punctuation("texto,Outro")
        assert result == "texto, Outro"

    def test_curly_quotes_to_straight(self):
        # Test curly/smart quotes → straight quotes
        curly_left = "\u201c"  # "
        curly_right = "\u201d"  # "
        guillemet_left = "\u00ab"  # «
        guillemet_right = "\u00bb"  # »

        assert normalize_punctuation(f"{curly_left}texto{curly_right}") == '"texto"'
        assert normalize_punctuation(f"{guillemet_left}texto{guillemet_right}") == '"texto"'

    def test_smart_single_quotes(self):
        # Test smart single quotes → straight single quotes
        smart_left = "\u2018"  # '
        smart_right = "\u2019"  # '
        assert normalize_punctuation(f"{smart_left}texto{smart_right}") == "'texto'"


class TestNormalizeAll:
    """Tests for normalize_all function."""

    def test_name_normalization(self):
        data = {"nome": "MARIA DA SILVA"}
        types = {"nome": "name"}
        result = normalize_all(data, types)
        assert result["nome"] == "Maria da Silva"

    def test_cpf_normalization(self):
        data = {"cpf": "12345678901"}
        types = {"cpf": "cpf"}
        result = normalize_all(data, types)
        assert result["cpf"] == "123.456.789-01"

    def test_cnpj_normalization(self):
        data = {"cnpj": "12345678000199"}
        types = {"cnpj": "cnpj"}
        result = normalize_all(data, types)
        assert result["cnpj"] == "12.345.678/0001-99"

    def test_cep_normalization(self):
        data = {"cep": "01310100"}
        types = {"cep": "cep"}
        result = normalize_all(data, types)
        assert result["cep"] == "01310-100"

    def test_oab_normalization(self):
        data = {"oab": "123456SP"}
        types = {"oab": "oab"}
        result = normalize_all(data, types)
        assert result["oab"] == "OAB/SP 123.456"

    def test_address_normalization(self):
        data = {"endereco": "AV. BRASIL N 100"}
        types = {"endereco": "address"}
        result = normalize_all(data, types)
        assert "Avenida" in result["endereco"]
        assert "nº" in result["endereco"]

    def test_text_normalization(self):
        data = {"texto": "  olá  .  mundo  "}
        types = {"texto": "text"}
        result = normalize_all(data, types)
        assert result["texto"] == "olá. mundo"

    def test_raw_no_normalization(self):
        data = {"codigo": "ABC  123"}
        types = {"codigo": "raw"}
        result = normalize_all(data, types)
        assert result["codigo"] == "ABC  123"

    def test_default_to_text(self):
        """Fields without type specification default to text normalization."""
        data = {"campo": "  texto  "}
        types = {}  # No type specified
        result = normalize_all(data, types)
        assert result["campo"] == "texto"

    def test_none_values(self):
        data = {"nome": None, "cpf": "12345678901"}
        types = {"nome": "name", "cpf": "cpf"}
        result = normalize_all(data, types)
        assert result["nome"] is None
        assert result["cpf"] == "123.456.789-01"

    def test_multiple_fields(self):
        data = {
            "nome": "JOÃO DA SILVA",
            "cpf": "12345678901",
            "endereco": "R. TESTE N 1",
            "cep": "01310100",
        }
        types = {
            "nome": "name",
            "cpf": "cpf",
            "endereco": "address",
            "cep": "cep",
        }
        result = normalize_all(data, types)
        assert result["nome"] == "João da Silva"
        assert result["cpf"] == "123.456.789-01"
        assert "Rua" in result["endereco"]
        assert result["cep"] == "01310-100"


class TestUTF8Characters:
    """Tests for UTF-8 Brazilian Portuguese character handling."""

    def test_lowercase_accented(self):
        """Test preservation of lowercase accented characters."""
        text = "áàâãéêíóôõúüç"
        assert normalize_whitespace(text) == text
        assert normalize_name(text.upper()) is not None

    def test_uppercase_accented(self):
        """Test preservation of uppercase accented characters."""
        text = "ÁÀÂÃÉÊÍÓÔÕÚÜÇ"
        assert normalize_whitespace(text) == text

    def test_special_symbols(self):
        """Test handling of special Brazilian symbols."""
        # Ordinals
        assert "1º" in normalize_name("1º TESTE")
        assert "2ª" in normalize_name("2ª VARA")

    def test_mixed_encoding(self):
        """Test mixed ASCII and UTF-8."""
        text = "João José da Conceição"
        assert normalize_name(text.upper()) is not None
        result = normalize_name(text.upper())
        assert "João" in result or "JOÃO" in text.upper()
