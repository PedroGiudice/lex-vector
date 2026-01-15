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
    parse_data_publicacao,
    parse_data_decisao,
)


class TestDateParsers:
    """Testes para funcoes de parse de data CKAN."""

    def test_parse_data_publicacao_formato_padrao(self):
        """Formato 'DJE        DATA:DD/MM/YYYY'."""
        assert parse_data_publicacao("DJE        DATA:25/05/2022") == "2022-05-25"
        assert parse_data_publicacao("DJE        DATA:01/12/2024") == "2024-12-01"

    def test_parse_data_publicacao_variantes(self):
        """Variantes possiveis do prefixo."""
        assert parse_data_publicacao("DJEN       DATA:12/11/2025") == "2025-11-12"
        assert parse_data_publicacao("DJE DATA:01/01/2023") == "2023-01-01"

    def test_parse_data_publicacao_invalido(self):
        """Formatos invalidos retornam None."""
        assert parse_data_publicacao("") is None
        assert parse_data_publicacao("2022-05-25") is None
        assert parse_data_publicacao("DATA:invalido") is None
        assert parse_data_publicacao(None) is None

    def test_parse_data_decisao_formato_padrao(self):
        """Formato 'YYYYMMDD'."""
        assert parse_data_decisao("20220523") == "2022-05-23"
        assert parse_data_decisao("20241231") == "2024-12-31"

    def test_parse_data_decisao_invalido(self):
        """Formatos invalidos retornam None."""
        assert parse_data_decisao("") is None
        assert parse_data_decisao("2022-05-23") is None
        assert parse_data_decisao("202205") is None
        assert parse_data_decisao(None) is None


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
            'numeroProcesso': '1234567',
            'dataPublicacao': 'DJE        DATA:20/11/2024',
            'dataDecisao': '20241115',
            'nomeOrgaoJulgador': 'TERCEIRA TURMA',
            'ministroRelator': 'PAULO DE TARSO SANSEVERINO',
            'ementa': 'RECURSO ESPECIAL. DIREITO CIVIL.',
            'decisao': """
                EMENTA: RECURSO ESPECIAL. DIREITO CIVIL.
                RELATORIO: Trata-se de recurso...
                VOTO: Como relatado...
                DISPOSITIVO: Dar provimento ao recurso especial.
            """,
            'siglaClasse': 'REsp',
            'tipoDeDecisao': 'ACORDAO',
            'assuntos': ['Direito Civil'],
        }

        resultado = processar_publicacao_stj(json_data)

        assert resultado['numero_processo'] == '1234567'
        assert resultado['tribunal'] == 'STJ'
        assert resultado['resultado_julgamento'] == ResultadoJulgamento.PROVIMENTO.value
        assert resultado['ementa'] == 'RECURSO ESPECIAL. DIREITO CIVIL.'
        assert resultado['relator'] == 'PAULO DE TARSO SANSEVERINO'

    def test_processar_fallback_ementa(self):
        """Testa fallback para ementa quando dispositivo nao classifica."""
        json_data = {
            'numeroProcesso': '9999999',
            'dataPublicacao': 'DJE        DATA:20/11/2024',
            'ementa': 'Recurso parcialmente provido.',
            'decisao': 'Texto generico sem dispositivo claro.',
            'siglaClasse': 'REsp',
            'tipoDeDecisao': 'ACORDAO',
        }

        resultado = processar_publicacao_stj(json_data)

        # Deve classificar pela ementa (fallback)
        assert resultado['resultado_julgamento'] == ResultadoJulgamento.PARCIAL_PROVIMENTO.value

    def test_processar_indeterminado(self):
        """Testa classificacao indeterminada."""
        json_data = {
            'numeroProcesso': '8888888',
            'dataPublicacao': 'DJE        DATA:20/11/2024',
            'ementa': 'Texto generico sem padroes.',
            'decisao': 'Mais texto generico.',
            'siglaClasse': 'REsp',
            'tipoDeDecisao': 'ACORDAO',
        }

        resultado = processar_publicacao_stj(json_data)

        assert resultado['resultado_julgamento'] == ResultadoJulgamento.INDETERMINADO.value

    def test_processar_datas_parseadas(self):
        """Testa parsing de datas no formato CKAN."""
        json_data = {
            'numeroProcesso': '5555555',
            'dataPublicacao': 'DJE        DATA:20/11/2024',
            'dataDecisao': '20241118',
            'ementa': 'Teste.',
            'decisao': 'Teste.',
            'siglaClasse': 'REsp',
            'tipoDeDecisao': 'ACORDAO',
        }

        resultado = processar_publicacao_stj(json_data)

        # Datas devem estar no formato ISO
        assert resultado['data_publicacao'] == '2024-11-20'
        assert resultado['data_julgamento'] == '2024-11-18'

    def test_processar_tipo_decisao_do_ckan(self):
        """Testa que tipo_decisao vem do campo tipoDeDecisao do CKAN."""
        json_data = {
            'numeroProcesso': '3333333',
            'dataPublicacao': 'DJE        DATA:20/11/2024',
            'ementa': 'Teste.',
            'decisao': 'Este eh o texto da decisao...',
            'siglaClasse': 'REsp',
            'tipoDeDecisao': 'DECISAO MONOCRATICA',
        }

        resultado = processar_publicacao_stj(json_data)

        assert resultado['tipo_decisao'] == 'DECISAO MONOCRATICA'

    def test_processar_sem_campo_decisao(self):
        """Testa processamento sem campo decisao (concatena partes)."""
        json_data = {
            'numeroProcesso': '7777777',
            'dataPublicacao': 'DJE        DATA:20/11/2024',
            'ementa': 'EMENTA: Teste de ementa.',
            'relatorio': 'RELATORIO: Teste de relatorio.',
            'voto': 'VOTO: Teste de voto.',
            'siglaClasse': 'REsp',
            'tipoDeDecisao': 'ACORDAO',
        }

        resultado = processar_publicacao_stj(json_data)

        # Deve ter concatenado as partes (quando decisao esta vazio)
        assert 'EMENTA:' in resultado['texto_integral']
        assert 'RELATORIO:' in resultado['texto_integral']
        assert 'VOTO:' in resultado['texto_integral']


class TestProcessadorCKAN:
    """Testes com dados reais do CKAN."""

    @pytest.fixture
    def json_ckan_real(self):
        """Amostra real de JSON do CKAN STJ."""
        return {
            "id": "000815399",
            "numeroProcesso": "1424080",
            "numeroRegistro": "201304043911",
            "siglaClasse": "EDcl no AgInt nos EDcl no REsp",
            "descricaoClasse": "EMBARGOS DE DECLARACAO...",
            "nomeOrgaoJulgador": "PRIMEIRA TURMA",
            "ministroRelator": "REGINA HELENA COSTA",
            "dataPublicacao": "DJE        DATA:25/05/2022",
            "ementa": "PROCESSUAL CIVIL. ADMINISTRATIVO...",
            "tipoDeDecisao": "ACORDAO",
            "dataDecisao": "20220523",
            "decisao": "Vistos e relatados estes autos, recurso conhecido e provido."
        }

    def test_processa_json_ckan_completo(self, json_ckan_real):
        """Deve processar JSON CKAN sem erros."""
        resultado = processar_publicacao_stj(json_ckan_real)

        assert resultado['numero_processo'] == "1424080"
        assert resultado['orgao_julgador'] == "PRIMEIRA TURMA"
        assert resultado['relator'] == "REGINA HELENA COSTA"
        assert resultado['data_publicacao'] == "2022-05-25"
        assert resultado['data_julgamento'] == "2022-05-23"
        assert resultado['tipo_decisao'] == "ACORDAO"
        assert resultado['classe_processual'] == "EDcl no AgInt nos EDcl no REsp"
        assert "Vistos e relatados" in resultado['texto_integral']

    def test_processa_json_ckan_campos_principais(self, json_ckan_real):
        """Verifica mapeamento correto dos campos CKAN."""
        resultado = processar_publicacao_stj(json_ckan_real)

        # Campos estruturais
        assert resultado['tribunal'] == 'STJ'
        assert resultado['fonte'] == 'STJ-Dados-Abertos'
        assert 'id' in resultado
        assert 'hash_conteudo' in resultado

    def test_processa_json_ckan_datas_parseadas(self, json_ckan_real):
        """Verifica parsing correto de datas CKAN."""
        resultado = processar_publicacao_stj(json_ckan_real)

        # Datas devem estar no formato ISO
        assert resultado['data_publicacao'] == "2022-05-25"
        assert resultado['data_julgamento'] == "2022-05-23"

    def test_processa_json_ckan_sem_campos_opcionais(self):
        """Testa JSON minimo do CKAN."""
        json_minimo = {
            "numeroProcesso": "123456",
            "ementa": "Teste.",
            "tipoDeDecisao": "ACORDAO",
        }

        resultado = processar_publicacao_stj(json_minimo)

        assert resultado['numero_processo'] == "123456"
        assert resultado['tipo_decisao'] == "ACORDAO"
        assert resultado['data_publicacao'] is None
        assert resultado['data_julgamento'] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
