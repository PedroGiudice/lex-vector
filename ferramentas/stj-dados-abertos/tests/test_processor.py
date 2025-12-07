"""
Testes unitários para processor.py (classificador de resultados).
"""
from __future__ import annotations

import pytest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.processor import (
    LegalResultClassifier,
    ResultadoJulgamento,
    processar_publicacao_stj,
    extrair_ementa,
    extrair_relator,
)


class TestResultadoJulgamentoEnum:
    """Testes do enum ResultadoJulgamento."""

    def test_enum_values(self):
        """Testa valores do enum."""
        assert ResultadoJulgamento.PROVIMENTO.value == "provimento"
        assert ResultadoJulgamento.PARCIAL_PROVIMENTO.value == "parcial_provimento"
        assert ResultadoJulgamento.DESPROVIMENTO.value == "desprovimento"
        assert ResultadoJulgamento.NAO_CONHECIDO.value == "nao_conhecido"
        assert ResultadoJulgamento.INDETERMINADO.value == "indeterminado"

    def test_enum_count(self):
        """Testa número de valores no enum."""
        assert len(ResultadoJulgamento) == 5


class TestLegalResultClassifierNormalization:
    """Testes de normalização de texto."""

    @pytest.fixture
    def classifier(self):
        """Fixture: classificador."""
        return LegalResultClassifier()

    def test_normalizar_lowercase(self, classifier):
        """Testa conversão para lowercase."""
        texto = "RECURSO ESPECIAL PROVIDO"
        resultado = classifier.normalizar_texto(texto)
        assert resultado == resultado.lower()

    def test_normalizar_remove_headers(self, classifier):
        """Testa remoção de headers."""
        texto = "SUPERIOR TRIBUNAL DE JUSTIÇA\nTERCEIRA TURMA\nRECURSO PROVIDO"
        resultado = classifier.normalizar_texto(texto)
        assert "superior tribunal" not in resultado
        assert "terceira turma" not in resultado
        assert "recurso provido" in resultado

    def test_normalizar_whitespace(self, classifier):
        """Testa padronização de espaços."""
        texto = "Recurso    especial     provido"
        resultado = classifier.normalizar_texto(texto)
        assert "  " not in resultado  # No double spaces
        assert resultado.strip() == resultado

    def test_normalizar_empty_string(self, classifier):
        """Testa string vazia."""
        assert classifier.normalizar_texto("") == ""
        assert classifier.normalizar_texto(None) == ""


class TestLegalResultClassifierExtraction:
    """Testes de extração de seções."""

    @pytest.fixture
    def classifier(self):
        """Fixture: classificador."""
        return LegalResultClassifier()

    def test_extrair_relatorio(self, classifier):
        """Testa extração de RELATÓRIO."""
        texto = """
        EMENTA: Teste de ementa.
        RELATÓRIO: Este é o relatório do caso.
        VOTO: Este é o voto do relator.
        """
        relatorio = classifier.extrair_relatorio(texto)
        assert "Este é o relatório do caso" in relatorio
        assert "VOTO" not in relatorio

    def test_extrair_voto(self, classifier):
        """Testa extração de VOTO."""
        texto = """
        RELATÓRIO: Este é o relatório.
        VOTO: Este é o voto do relator.
        DISPOSITIVO: Recurso provido.
        """
        voto = classifier.extrair_voto(texto)
        assert "Este é o voto do relator" in voto
        assert "DISPOSITIVO" not in voto

    def test_extrair_dispositivo(self, classifier):
        """Testa extração de DISPOSITIVO."""
        texto = """
        VOTO: Este é o voto.
        DISPOSITIVO: Recurso conhecido e provido.
        """
        dispositivo = classifier.extrair_dispositivo(texto)
        assert "Recurso conhecido e provido" in dispositivo

    def test_extrair_dispositivo_com_decisao(self, classifier):
        """Testa extração com palavra DECISÃO."""
        texto = """
        VOTO: Este é o voto.
        DECISÃO: Recurso não conhecido.
        """
        dispositivo = classifier.extrair_dispositivo(texto)
        assert "Recurso não conhecido" in dispositivo

    def test_extrair_dispositivo_com_acordao(self, classifier):
        """Testa extração com palavra ACÓRDÃO."""
        texto = """
        VOTO: Este é o voto.
        ACÓRDÃO: Recurso parcialmente provido.
        """
        dispositivo = classifier.extrair_dispositivo(texto)
        assert "Recurso parcialmente provido" in dispositivo

    def test_extrair_secao_vazia(self, classifier):
        """Testa extração quando seção não existe."""
        texto = "Texto sem seções estruturadas."
        assert classifier.extrair_relatorio(texto) == ""
        assert classifier.extrair_voto(texto) == ""
        assert classifier.extrair_dispositivo(texto) == ""


class TestLegalResultClassifierProvimento:
    """Testes de classificação: PROVIMENTO."""

    @pytest.fixture
    def classifier(self):
        """Fixture: classificador."""
        return LegalResultClassifier()

    def test_classificar_dar_provimento(self, classifier):
        """Testa 'dar provimento'."""
        assert classifier.classificar("Dar provimento ao recurso") == ResultadoJulgamento.PROVIMENTO

    def test_classificar_dou_provimento(self, classifier):
        """Testa 'dou provimento'."""
        assert classifier.classificar("Dou provimento ao recurso especial") == ResultadoJulgamento.PROVIMENTO

    def test_classificar_dei_provimento(self, classifier):
        """Testa 'dei provimento'."""
        assert classifier.classificar("Dei provimento ao recurso") == ResultadoJulgamento.PROVIMENTO

    def test_classificar_recurso_provido(self, classifier):
        """Testa 'recurso provido'."""
        assert classifier.classificar("Recurso conhecido e provido") == ResultadoJulgamento.PROVIMENTO

    def test_classificar_recurso_especial_provido(self, classifier):
        """Testa 'recurso especial provido'."""
        assert classifier.classificar("Recurso especial provido") == ResultadoJulgamento.PROVIMENTO

    def test_classificar_provido_o_recurso(self, classifier):
        """Testa 'provido o recurso'."""
        assert classifier.classificar("Provido o recurso especial") == ResultadoJulgamento.PROVIMENTO

    def test_classificar_dar_lhe_provimento(self, classifier):
        """Testa 'dar-lhe provimento'."""
        assert classifier.classificar("Dar-lhe provimento") == ResultadoJulgamento.PROVIMENTO


class TestLegalResultClassifierParcialProvimento:
    """Testes de classificação: PARCIAL_PROVIMENTO."""

    @pytest.fixture
    def classifier(self):
        """Fixture: classificador."""
        return LegalResultClassifier()

    def test_classificar_parcialmente_provido(self, classifier):
        """Testa 'parcialmente provido'."""
        assert classifier.classificar("Recurso parcialmente provido") == ResultadoJulgamento.PARCIAL_PROVIMENTO

    def test_classificar_parcial_provido(self, classifier):
        """Testa 'parcial provido'."""
        assert classifier.classificar("Recurso parcial provido") == ResultadoJulgamento.PARCIAL_PROVIMENTO

    def test_classificar_provido_em_parte(self, classifier):
        """Testa 'provido em parte'."""
        assert classifier.classificar("Recurso provido em parte") == ResultadoJulgamento.PARCIAL_PROVIMENTO

    def test_classificar_provido_parte(self, classifier):
        """Testa 'provido parte'."""
        assert classifier.classificar("Recurso provido parte") == ResultadoJulgamento.PARCIAL_PROVIMENTO

    def test_classificar_dar_parcial_provimento(self, classifier):
        """Testa 'dar parcial provimento'."""
        assert classifier.classificar("Dar parcial provimento ao recurso") == ResultadoJulgamento.PARCIAL_PROVIMENTO

    def test_classificar_parcial_provimento(self, classifier):
        """Testa 'parcial provimento'."""
        assert classifier.classificar("Parcial provimento ao recurso") == ResultadoJulgamento.PARCIAL_PROVIMENTO

    def test_parcial_antes_provimento(self, classifier):
        """
        Testa que PARCIAL_PROVIMENTO é detectado antes de PROVIMENTO.

        Importante: 'parcialmente provido' contém 'provido', então PARCIAL
        deve ser checado primeiro.
        """
        # Este texto contém patterns tanto de PARCIAL quanto de PROVIMENTO
        texto = "Recurso parcialmente provido"
        resultado = classifier.classificar(texto)
        # Deve ser PARCIAL (mais específico), não PROVIMENTO
        assert resultado == ResultadoJulgamento.PARCIAL_PROVIMENTO


class TestLegalResultClassifierDesprovimento:
    """Testes de classificação: DESPROVIMENTO."""

    @pytest.fixture
    def classifier(self):
        """Fixture: classificador."""
        return LegalResultClassifier()

    def test_classificar_nao_provido(self, classifier):
        """Testa 'não provido'."""
        assert classifier.classificar("Recurso não provido") == ResultadoJulgamento.DESPROVIMENTO

    def test_classificar_negar_provimento(self, classifier):
        """Testa 'negar provimento'."""
        assert classifier.classificar("Negar provimento ao recurso") == ResultadoJulgamento.DESPROVIMENTO

    def test_classificar_improvido(self, classifier):
        """Testa 'improvido'."""
        assert classifier.classificar("Recurso improvido") == ResultadoJulgamento.DESPROVIMENTO

    def test_classificar_desprovido(self, classifier):
        """Testa 'desprovido'."""
        assert classifier.classificar("Recurso desprovido") == ResultadoJulgamento.DESPROVIMENTO

    def test_classificar_negado_provimento(self, classifier):
        """Testa 'negado provimento'."""
        assert classifier.classificar("Negado provimento ao recurso") == ResultadoJulgamento.DESPROVIMENTO


class TestLegalResultClassifierNaoConhecido:
    """Testes de classificação: NAO_CONHECIDO."""

    @pytest.fixture
    def classifier(self):
        """Fixture: classificador."""
        return LegalResultClassifier()

    def test_classificar_nao_conhecido(self, classifier):
        """Testa 'não conhecido'."""
        assert classifier.classificar("Recurso não conhecido") == ResultadoJulgamento.NAO_CONHECIDO

    def test_classificar_nao_conhecer(self, classifier):
        """Testa 'não conhecer'."""
        assert classifier.classificar("Não conhecer do recurso") == ResultadoJulgamento.NAO_CONHECIDO

    def test_classificar_nao_conheceu(self, classifier):
        """Testa 'não conheceu'."""
        assert classifier.classificar("Não conheceu do recurso") == ResultadoJulgamento.NAO_CONHECIDO

    def test_classificar_recurso_especial_nao_conhecido(self, classifier):
        """Testa 'recurso especial não conhecido'."""
        assert classifier.classificar("Recurso especial não conhecido") == ResultadoJulgamento.NAO_CONHECIDO


class TestLegalResultClassifierIndeterminado:
    """Testes de classificação: INDETERMINADO."""

    @pytest.fixture
    def classifier(self):
        """Fixture: classificador."""
        return LegalResultClassifier()

    def test_classificar_texto_vazio(self, classifier):
        """Testa texto vazio."""
        assert classifier.classificar("") == ResultadoJulgamento.INDETERMINADO

    def test_classificar_texto_none(self, classifier):
        """Testa texto None."""
        assert classifier.classificar(None) == ResultadoJulgamento.INDETERMINADO

    def test_classificar_texto_sem_padroes(self, classifier):
        """Testa texto sem padrões conhecidos."""
        texto = "Este é um texto genérico sobre direito civil sem decisão clara."
        assert classifier.classificar(texto) == ResultadoJulgamento.INDETERMINADO


class TestLegalResultClassifierRealExamples:
    """Testes com exemplos reais de decisões do STJ."""

    @pytest.fixture
    def classifier(self):
        """Fixture: classificador."""
        return LegalResultClassifier()

    def test_exemplo_real_provimento(self, classifier):
        """Testa exemplo real de provimento."""
        texto = """
        SUPERIOR TRIBUNAL DE JUSTIÇA
        TERCEIRA TURMA
        RELATOR: MINISTRO PAULO DE TARSO SANSEVERINO

        DISPOSITIVO: Ante o exposto, conheço do recurso especial e DOU-LHE PROVIMENTO,
        para reformar o acórdão recorrido e julgar procedente o pedido.
        """
        assert classifier.classificar(texto) == ResultadoJulgamento.PROVIMENTO

    def test_exemplo_real_parcial_provimento(self, classifier):
        """Testa exemplo real de parcial provimento."""
        texto = """
        DECISÃO: Recurso especial conhecido e PARCIALMENTE PROVIDO, para reduzir
        o quantum indenizatório de R$ 50.000,00 para R$ 20.000,00.
        """
        assert classifier.classificar(texto) == ResultadoJulgamento.PARCIAL_PROVIMENTO

    def test_exemplo_real_desprovimento(self, classifier):
        """Testa exemplo real de desprovimento."""
        texto = """
        ACÓRDÃO: Vistos, relatados e discutidos os autos, acordam os Ministros da
        Segunda Turma do Superior Tribunal de Justiça, na conformidade dos votos,
        NEGAR PROVIMENTO ao recurso especial.
        """
        assert classifier.classificar(texto) == ResultadoJulgamento.DESPROVIMENTO

    def test_exemplo_real_nao_conhecido(self, classifier):
        """Testa exemplo real de não conhecido."""
        texto = """
        DISPOSITIVO: Ante o exposto, NÃO CONHEÇO do recurso especial, por falta
        de prequestionamento da matéria.
        """
        assert classifier.classificar(texto) == ResultadoJulgamento.NAO_CONHECIDO


class TestExtracaoHelpers:
    """Testes das funções auxiliares de extração."""

    def test_extrair_ementa_simples(self):
        """Testa extração de ementa simples."""
        texto = """
        EMENTA: RECURSO ESPECIAL. DIREITO CIVIL. RESPONSABILIDADE CIVIL.
        RELATÓRIO: O Ministro relator...
        """
        ementa = extrair_ementa(texto)
        assert "RECURSO ESPECIAL" in ementa
        assert "RELATÓRIO" not in ementa

    def test_extrair_ementa_vazia(self):
        """Testa texto sem ementa."""
        texto = "Texto sem seção de ementa."
        assert extrair_ementa(texto) == ""

    def test_extrair_relator_com_titulo(self):
        """Testa extração de relator com título."""
        texto = """
        RELATOR: MINISTRO PAULO DE TARSO SANSEVERINO
        EMENTA: Teste...
        """
        relator = extrair_relator(texto)
        assert "PAULO DE TARSO SANSEVERINO" in relator.upper()

    def test_extrair_relator_sem_ministro(self):
        """Testa extração sem palavra MINISTRO."""
        texto = """
        RELATOR: NANCY ANDRIGHI
        EMENTA: Teste...
        """
        relator = extrair_relator(texto)
        assert "NANCY ANDRIGHI" in relator.upper()

    def test_extrair_relator_vazio(self):
        """Testa texto sem relator."""
        texto = "Texto sem relator identificável."
        assert extrair_relator(texto) == ""


class TestProcessarPublicacaoSTJ:
    """Testes da função processar_publicacao_stj."""

    def test_processar_com_dispositivo_provimento(self):
        """Testa processamento com dispositivo indicando provimento."""
        json_data = {
            'processo': 'REsp 1234567/SP',
            'dataPublicacao': '2024-11-20T00:00:00',
            'dataJulgamento': '2024-11-15T00:00:00',
            'orgaoJulgador': 'Terceira Turma',
            'relator': 'Ministro Paulo de Tarso Sanseverino',
            'ementa': 'RECURSO ESPECIAL. DIREITO CIVIL.',
            'inteiro_teor': """
                EMENTA: RECURSO ESPECIAL. DIREITO CIVIL.
                RELATÓRIO: Trata-se de recurso...
                VOTO: Como relatado...
                DISPOSITIVO: Dar provimento ao recurso especial.
            """,
            'classe': 'REsp',
            'assuntos': ['Direito Civil'],
        }

        resultado = processar_publicacao_stj(json_data)

        assert resultado['numero_processo'] == 'REsp 1234567/SP'
        assert resultado['tribunal'] == 'STJ'
        assert resultado['resultado_julgamento'] == ResultadoJulgamento.PROVIMENTO.value
        assert resultado['ementa'] == 'RECURSO ESPECIAL. DIREITO CIVIL.'
        assert resultado['relator'] == 'Ministro Paulo de Tarso Sanseverino'

    def test_processar_fallback_ementa(self):
        """Testa fallback para ementa quando dispositivo não classifica."""
        json_data = {
            'processo': 'REsp 9999999/RJ',
            'dataPublicacao': '2024-11-20T00:00:00',
            'ementa': 'Recurso parcialmente provido.',
            'inteiro_teor': 'Texto genérico sem dispositivo claro.',
            'classe': 'REsp',
        }

        resultado = processar_publicacao_stj(json_data)

        # Deve classificar pela ementa (fallback)
        assert resultado['resultado_julgamento'] == ResultadoJulgamento.PARCIAL_PROVIMENTO.value

    def test_processar_indeterminado(self):
        """Testa classificação indeterminada."""
        json_data = {
            'processo': 'REsp 8888888/MG',
            'dataPublicacao': '2024-11-20T00:00:00',
            'ementa': 'Texto genérico sem padrões.',
            'inteiro_teor': 'Mais texto genérico.',
            'classe': 'REsp',
        }

        resultado = processar_publicacao_stj(json_data)

        assert resultado['resultado_julgamento'] == ResultadoJulgamento.INDETERMINADO.value

    def test_processar_com_timestamp(self):
        """Testa conversão de timestamp para ISO."""
        json_data = {
            'processo': 'REsp 5555555/RS',
            'dataPublicacao': 1700438400000,  # milliseconds
            'dataJulgamento': 1700352000000,
            'ementa': 'Teste.',
            'inteiro_teor': 'Teste.',
            'classe': 'REsp',
        }

        resultado = processar_publicacao_stj(json_data)

        # Deve ter convertido para ISO string
        assert isinstance(resultado['data_publicacao'], str)
        assert isinstance(resultado['data_julgamento'], str)
        assert 'T' in resultado['data_publicacao']  # ISO format

    def test_processar_decisao_monocratica(self):
        """Testa identificação de decisão monocrática."""
        json_data = {
            'processo': 'REsp 3333333/SP',
            'dataPublicacao': '2024-11-20T00:00:00',
            'ementa': 'Teste.',
            'inteiro_teor': 'DECISÃO MONOCRÁTICA: Este é o texto da decisão...',
            'classe': 'REsp',
        }

        resultado = processar_publicacao_stj(json_data)

        assert resultado['tipo_decisao'] == 'Decisão Monocrática'

    def test_processar_sem_inteiro_teor(self):
        """Testa processamento sem inteiro teor (concatena partes)."""
        json_data = {
            'processo': 'REsp 7777777/BA',
            'dataPublicacao': '2024-11-20T00:00:00',
            'ementa': 'EMENTA: Teste de ementa.',
            'relatorio': 'RELATÓRIO: Teste de relatório.',
            'voto': 'VOTO: Teste de voto.',
            'decisao': 'DECISÃO: Recurso provido.',
            'classe': 'REsp',
        }

        resultado = processar_publicacao_stj(json_data)

        # Deve ter concatenado as partes
        assert 'EMENTA:' in resultado['texto_integral']
        assert 'RELATÓRIO:' in resultado['texto_integral']
        assert 'VOTO:' in resultado['texto_integral']
        assert 'DECISÃO:' in resultado['texto_integral']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
