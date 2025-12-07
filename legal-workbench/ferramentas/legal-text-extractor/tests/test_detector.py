"""Testes para detector de sistema judicial"""
import pytest
from src.core.detector import JudicialSystemDetector


class TestJudicialSystemDetector:
    """Test suite para detecção de sistemas judiciais"""

    @pytest.fixture
    def detector(self):
        """Cria instância do detector"""
        return JudicialSystemDetector()

    def test_detect_pje(self, detector):
        """Testa detecção de PJE"""
        text = """
        Processo Judicial Eletrônico - PJE
        Documento assinado por JUIZ FEDERAL e certificado digitalmente por ICP-Brasil
        Resolução CNJ 281/2019
        Este documento foi gerado pelo usuário 123.456.789-00
        """
        result = detector.detect_system(text)
        assert result.system == "PJE"
        assert result.confidence > 40

    def test_detect_esaj(self, detector):
        """Testa detecção de ESAJ"""
        text = """
        e-SAJ - Sistema de Automação da Justiça
        Portal e-SAJ - Conferência de documento digital
        Softplan Planejamento e Sistemas
        tjsp.jus.br/esaj
        """
        result = detector.detect_system(text)
        assert result.system == "ESAJ"
        assert result.confidence > 40

    def test_detect_stf(self, detector):
        """Testa detecção de STF"""
        text = """
        Supremo Tribunal Federal
        e-STF - Peticionamento eletrônico
        portal.stf.jus.br
        Resolução STF 693
        """
        result = detector.detect_system(text)
        assert result.system == "STF"
        assert result.confidence > 40

    def test_detect_stj(self, detector):
        """Testa detecção de STJ"""
        text = """
        Superior Tribunal de Justiça
        e-STJ - Central do Processo Eletrônico
        www.stj.jus.br
        Autentique em: https://www.stj.jus.br/validar
        """
        result = detector.detect_system(text)
        assert result.system == "STJ"
        assert result.confidence > 40

    def test_detect_eproc(self, detector):
        """Testa detecção de EPROC"""
        text = """
        EPROC - Sistema de Processo Eletrônico
        trf4.jus.br/eproc
        Assinatura destacada arquivo .p7s
        CAdES-BES
        """
        result = detector.detect_system(text)
        assert result.system == "EPROC"
        assert result.confidence > 40

    def test_detect_projudi(self, detector):
        """Testa detecção de PROJUDI"""
        text = """
        PROJUDI - Processo Judicial Digital
        tjpr.jus.br/projudi
        Assinador Livre versão 1.5
        Universidade Federal de Campina Grande
        """
        result = detector.detect_system(text)
        assert result.system == "PROJUDI"
        assert result.confidence > 40

    def test_detect_generic_icp_brasil(self, detector):
        """Testa fallback para genérico com ICP-Brasil"""
        text = """
        Documento judicial assinado digitalmente
        Certificado digital ICP-Brasil
        AC SERASA RFB
        Padrão PAdES de assinatura
        """
        result = detector.detect_system(text)
        assert result.system == "GENERIC_JUDICIAL"
        assert result.confidence >= 50

    def test_detect_unknown(self, detector):
        """Testa fallback para desconhecido"""
        text = "Documento genérico sem padrões judiciais identificáveis."
        result = detector.detect_system(text)
        assert result.system == "UNKNOWN"
        assert result.confidence == 0

    def test_detect_short_text(self, detector):
        """Testa texto muito curto"""
        text = "PJE"  # Menos de 100 caracteres
        result = detector.detect_system(text)
        assert result.system == "UNKNOWN"
        assert "Texto muito curto" in result.details.get("reason", "")

    def test_list_supported_systems(self, detector):
        """Testa listagem de sistemas suportados"""
        systems = detector.list_supported_systems()
        assert len(systems) == 6
        codes = [s["code"] for s in systems]
        assert "PJE" in codes
        assert "ESAJ" in codes
        assert "STF" in codes
        assert "STJ" in codes
        assert "EPROC" in codes
        assert "PROJUDI" in codes

    def test_get_system_info(self, detector):
        """Testa obtenção de informações do sistema"""
        info = detector.get_system_info("PJE")
        assert info is not None
        assert info.code == "PJE"
        assert "Processo Judicial Eletrônico" in info.name
