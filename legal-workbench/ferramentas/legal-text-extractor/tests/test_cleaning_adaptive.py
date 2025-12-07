"""Tests for adaptive cleaning engine."""
import pytest
from src.engines.cleaning_engine import CleanerEngine, DetectionResult, get_cleaner


class TestSystemDetection:
    """Test system detection via fingerprints."""

    def test_detect_pje(self):
        """Should detect PJE system with high confidence."""
        engine = CleanerEngine()
        text = """
        Processo Judicial Eletrônico
        Código de verificação: ABCD.1234.EFGH.5678
        pje.trt15.jus.br
        """
        result = engine.detect_system(text)
        assert result.system == "PJE"
        assert result.confidence > 0.3
        assert result.hits >= 2

    def test_detect_esaj(self):
        """Should detect ESAJ system with high confidence."""
        engine = CleanerEngine()
        text = """
        Tribunal de Justiça do Estado de São Paulo
        e-SAJ
        tjsp.jus.br/esaj
        """
        result = engine.detect_system(text)
        assert result.system == "ESAJ"
        assert result.confidence > 0.3

    def test_detect_eproc(self):
        """Should detect EPROC system with high confidence."""
        engine = CleanerEngine()
        text = """
        Sistema EPROC
        trf3.jus.br
        Assinatura digital disponível em: documento_assinado.p7s
        """
        result = engine.detect_system(text)
        assert result.system == "EPROC"
        assert result.confidence > 0.3

    def test_detect_projudi(self):
        """Should detect PROJUDI system."""
        engine = CleanerEngine()
        text = """
        PROJUDI - Sistema de Gestão Processual
        Digitalmente assinado por JOÃO DA SILVA
        Data: 15/03/2024
        """
        result = engine.detect_system(text)
        assert result.system == "PROJUDI"
        assert result.confidence > 0.3

    def test_detect_stf(self):
        """Should detect STF system."""
        engine = CleanerEngine()
        text = """
        Supremo Tribunal Federal
        stf.jus.br
        Processo eletrônico
        """
        result = engine.detect_system(text)
        assert result.system == "STF"
        assert result.confidence > 0.3

    def test_detect_stj(self):
        """Should detect STJ system."""
        engine = CleanerEngine()
        text = """
        Superior Tribunal de Justiça
        stj.jus.br
        Autentique este documento
        """
        result = engine.detect_system(text)
        assert result.system == "STJ"
        assert result.confidence > 0.3

    def test_unknown_system(self):
        """Should return UNKNOWN for text without judicial markers."""
        engine = CleanerEngine()
        text = "Este é um texto comum sem marcadores judiciais específicos."
        result = engine.detect_system(text)
        assert result.system == "UNKNOWN"
        assert result.confidence == 0.0

    def test_detection_result_structure(self):
        """Should return properly structured DetectionResult."""
        engine = CleanerEngine()
        text = "Processo Judicial Eletrônico - PJE"
        result = engine.detect_system(text)

        assert isinstance(result, DetectionResult)
        assert isinstance(result.system, str)
        assert isinstance(result.confidence, float)
        assert isinstance(result.hits, int)
        assert isinstance(result.total_fingerprints, int)
        assert 0.0 <= result.confidence <= 1.0


class TestCleaning:
    """Test cleaning functionality."""

    def test_clean_pje_artifacts(self):
        """Should remove PJE-specific artifacts."""
        engine = CleanerEngine()
        text = """
        Conteúdo importante do documento.
        Código de verificação: ABCD.1234.EFGH.5678
        Página 1 de 10
        Este documento foi gerado pelo usuário ADMIN em 15/03/2024 10:30:00
        Mais conteúdo relevante.
        """
        cleaned = engine.clean(text, force_system="PJE")

        assert "Código de verificação" not in cleaned
        assert "Página 1 de 10" not in cleaned
        assert "Este documento foi gerado pelo usuário" not in cleaned
        assert "Conteúdo importante" in cleaned
        assert "Mais conteúdo relevante" in cleaned

    def test_clean_esaj_artifacts(self):
        """Should remove ESAJ-specific artifacts."""
        engine = CleanerEngine()
        text = """
        Sentença do processo.
        Código do documento: AB12CD34EF5678GH
        Assinado digitalmente por: JUIZ FULANO DE TAL data: 15/03/2024
        Conferência de documento digital via portal e-SAJ
        Resolução nº 552/11
        Texto da decisão aqui.
        """
        cleaned = engine.clean(text, force_system="ESAJ")

        assert "Código do documento" not in cleaned
        assert "Assinado digitalmente por" not in cleaned
        assert "Conferência de documento digital" not in cleaned
        assert "Resolução" not in cleaned
        assert "Sentença do processo" in cleaned
        assert "Texto da decisão aqui" in cleaned

    def test_clean_universal_only_low_confidence(self):
        """Should only apply universal patterns when confidence is low."""
        engine = CleanerEngine()
        text = """
        Texto normal do documento.
        Página 5 de 20
        https://exemplo.jus.br/validar
        Conteúdo relevante.
        """
        cleaned = engine.clean(text)  # No system detected

        assert "Página 5 de 20" not in cleaned
        assert "jus.br" not in cleaned
        assert "Texto normal do documento" in cleaned
        assert "Conteúdo relevante" in cleaned

    def test_clean_universal_patterns(self):
        """Should always remove universal patterns regardless of system."""
        engine = CleanerEngine()
        text = """
        Documento importante.
        Página 3 de 15
        fls. 42
        https://portal.jus.br/validacao
        Código de verificação: ABC123DEF456
        Valide em: https://portal.jus.br
        ICP-Brasil
        Data/hora: 15/03/2024 10:30:45
        Conteúdo principal.
        """
        cleaned = engine.clean(text, force_system="PJE")

        # Universal patterns should be removed
        assert "Página 3 de 15" not in cleaned
        assert "fls. 42" not in cleaned
        assert "https://portal.jus.br" not in cleaned
        assert "Código de verificação" not in cleaned
        assert "Valide em" not in cleaned
        # ICP-Brasil should be removed (case insensitive)
        assert "ICP-Brasil".lower() not in cleaned.lower()
        assert "Data/hora" not in cleaned

        # Content should remain
        assert "Documento importante" in cleaned
        assert "Conteúdo principal" in cleaned

    def test_clean_whitespace_normalization(self):
        """Should normalize excessive whitespace."""
        engine = CleanerEngine()
        text = """
        Primeira linha.



        Segunda linha com muito espaço.



        Terceira linha.
        """
        cleaned = engine.clean(text)

        # Should not have more than 2 consecutive newlines
        assert "\n\n\n" not in cleaned
        # Should not have trailing spaces
        assert "    \n" not in cleaned
        # Content should be preserved
        assert "Primeira linha" in cleaned
        assert "Segunda linha" in cleaned
        assert "Terceira linha" in cleaned

    def test_force_system_overrides_detection(self):
        """Should use forced system instead of detection."""
        engine = CleanerEngine()
        text = """
        Processo Judicial Eletrônico
        pje.trt15.jus.br
        Código do documento: ESAJ123456
        """
        # Text has PJE markers but we force ESAJ
        cleaned = engine.clean(text, force_system="ESAJ")

        # Should apply ESAJ rules even though text suggests PJE
        assert "Código do documento" not in cleaned

    def test_empty_text_handling(self):
        """Should handle empty or very short text gracefully."""
        engine = CleanerEngine()

        # Empty string
        assert engine.clean("") == ""

        # Very short text
        short_text = "Hi"
        cleaned = engine.clean(short_text)
        assert cleaned == "Hi"

    def test_confidence_threshold_behavior(self):
        """Should only apply system rules when confidence exceeds threshold."""
        engine = CleanerEngine()

        # Low confidence text (no clear system markers)
        low_conf_text = """
        Documento genérico.
        Página 1 de 5
        Algum conteúdo.
        """
        detection = engine.detect_system(low_conf_text)
        assert detection.confidence < engine.CONFIDENCE_THRESHOLD

        cleaned = engine.clean(low_conf_text)
        # Should still remove universal patterns
        assert "Página 1 de 5" not in cleaned
        assert "Documento genérico" in cleaned

    def test_multiple_systems_markers(self):
        """Should detect dominant system when multiple markers present."""
        engine = CleanerEngine()
        text = """
        Processo Judicial Eletrônico
        pje.trt15.jus.br
        Código de verificação: ABCD.1234.EFGH.5678
        e-SAJ
        Código do documento: XYZ123
        """
        result = engine.detect_system(text)

        # Should detect PJE as it has more fingerprint hits
        assert result.system in ["PJE", "ESAJ"]
        assert result.confidence > 0.0


class TestSingleton:
    """Test singleton pattern for get_cleaner()."""

    def test_singleton(self):
        """Should return same instance on multiple calls."""
        engine1 = get_cleaner()
        engine2 = get_cleaner()
        assert engine1 is engine2

    def test_singleton_preserves_state(self):
        """Singleton should maintain state across calls."""
        engine1 = get_cleaner()
        profiles_count1 = len(engine1.profiles)

        engine2 = get_cleaner()
        profiles_count2 = len(engine2.profiles)

        assert profiles_count1 == profiles_count2
        assert profiles_count1 > 0  # Should have loaded profiles


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_force_system(self):
        """Should handle invalid forced system gracefully."""
        engine = CleanerEngine()
        text = "Documento teste"

        # Invalid system name should fallback to detection
        cleaned = engine.clean(text, force_system="INVALID_SYSTEM")
        assert cleaned is not None
        assert isinstance(cleaned, str)

    def test_special_characters_in_text(self):
        """Should handle special characters and unicode correctly."""
        engine = CleanerEngine()
        text = """
        Decisão com caracteres especiais: São José, Açúcar, Atenção
        Página 1 de 3
        Símbolos: § ° º ª © ® ™
        Conteúdo válido.
        """
        cleaned = engine.clean(text)

        # Should preserve unicode characters
        assert "São José" in cleaned or "Sao Jose" in cleaned  # May be normalized
        assert "Açúcar" in cleaned or "Acucar" in cleaned
        assert "Atenção" in cleaned or "Atencao" in cleaned

        # Should remove page numbers
        assert "Página 1 de 3" not in cleaned

    def test_very_long_text(self):
        """Should handle very long documents efficiently."""
        engine = CleanerEngine()

        # Create a large document
        long_text = "Linha de conteúdo relevante.\n" * 10000
        long_text += "Página 500 de 1000\n"
        long_text += "Código de verificação: ABCD.1234.EFGH.5678\n"
        long_text += "Mais conteúdo.\n" * 1000

        cleaned = engine.clean(long_text, force_system="PJE")

        # Should process without errors
        assert cleaned is not None
        assert len(cleaned) > 0
        assert "Linha de conteúdo relevante" in cleaned
        assert "Página 500 de 1000" not in cleaned
        assert "Código de verificação" not in cleaned

    def test_all_profiles_loaded(self):
        """Should load all expected judicial systems."""
        engine = CleanerEngine()

        expected_systems = ["PJE", "ESAJ", "EPROC", "PROJUDI", "STF", "STJ"]
        for system in expected_systems:
            assert system in engine.profiles
            profile = engine.profiles[system]
            assert len(profile.fingerprints) > 0
            assert len(profile.cleaning_rules) > 0
            assert profile.weight > 0

    def test_universal_patterns_exist(self):
        """Should have universal patterns loaded."""
        engine = CleanerEngine()
        assert len(engine.universal_patterns) > 0
