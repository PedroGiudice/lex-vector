"""Tests for integras_processor.py."""
import pytest
import hashlib
from pathlib import Path
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.integras_processor import (
    normalizar_metadados,
    html_para_texto,
    extrair_numero_processo,
    extrair_classe_processual,
    preparar_registro_integra,
    IntegrasProcessor,
)


class TestNormalizarMetadados:
    def test_normalizar_consolidado_mensal(self):
        """Consolidados usam epoch ms e campo 'ministro'."""
        raw = {
            "seqDocumento": 146211705,
            "dataPublicacao": 1646276400000,
            "tipoDocumento": "ACORDAO",
            "numeroRegistro": "202103353563",
            "processo": "AREsp 1996346    ",
            "dataRecebimento": 1634526000000,
            "dataDistribuicao": 1634785200000,
            "ministro": "LUIS FELIPE SALOMAO",
            "recurso": "AGRAVO INTERNO",
            "teor": "Concedendo",
            "descricaoMonocratica": None,
            "assuntos": "11806;11806"
        }
        result = normalizar_metadados(raw)
        assert result["seq_documento"] == 146211705
        assert result["data_publicacao"] == "2022-03-03"
        assert result["ministro"] == "LUIS FELIPE SALOMAO"
        assert result["numero_processo"] == "1996346"
        assert result["classe_processual"] == "AREsp"
        assert result["tipo_documento"] == "ACORDAO"
        assert result["numero_registro"] == "202103353563"
        assert result["recurso"] == "AGRAVO INTERNO"
        assert result["teor"] == "Concedendo"
        assert result["descricao_monocratica"] is None

    def test_normalizar_diario_recente(self):
        """Diarios recentes usam ISO e campo 'NM_MINISTRO'."""
        raw = {
            "SeqDocumento": 353186704,
            "dataPublicacao": "2026-01-22",
            "tipoDocumento": "DECISAO",
            "numeroRegistro": "202400836220",
            "processo": "AREsp 2591846",
            "NM_MINISTRO": "PAULO SERGIO DOMINGUES",
            "teor": "Nao Conhecendo",
            "assuntos": "9992, 10433"
        }
        result = normalizar_metadados(raw)
        assert result["seq_documento"] == 353186704
        assert result["data_publicacao"] == "2026-01-22"
        assert result["ministro"] == "PAULO SERGIO DOMINGUES"
        assert result["numero_processo"] == "2591846"
        assert result["classe_processual"] == "AREsp"

    def test_normalizar_assuntos_ponto_virgula(self):
        """Assuntos com separador ponto e virgula."""
        raw = {
            "seqDocumento": 1,
            "dataPublicacao": 1646276400000,
            "tipoDocumento": "DECISAO",
            "processo": "REsp 123",
            "ministro": "TESTE",
            "assuntos": "11806;11807;11808"
        }
        result = normalizar_metadados(raw)
        assert result["assuntos"] == ["11806", "11807", "11808"]

    def test_normalizar_assuntos_virgula(self):
        """Assuntos com separador virgula e espaco."""
        raw = {
            "SeqDocumento": 2,
            "dataPublicacao": "2026-01-01",
            "tipoDocumento": "ACORDAO",
            "processo": "HC 456",
            "NM_MINISTRO": "TESTE",
            "assuntos": "9992, 10433"
        }
        result = normalizar_metadados(raw)
        assert result["assuntos"] == ["9992", "10433"]

    def test_normalizar_assuntos_none(self):
        """Assuntos None deve retornar lista vazia."""
        raw = {
            "seqDocumento": 3,
            "dataPublicacao": 1646276400000,
            "tipoDocumento": "DECISAO",
            "processo": "REsp 789",
            "ministro": "TESTE",
            "assuntos": None
        }
        result = normalizar_metadados(raw)
        assert result["assuntos"] == []


class TestHtmlParaTexto:
    def test_converter_html_simples(self):
        html = "DECISAO<br>Trata-se de habeas corpus..."
        texto = html_para_texto(html)
        assert "<br>" not in texto
        assert "DECISAO" in texto
        assert "Trata-se" in texto

    def test_preservar_paragrafos(self):
        html = "Paragrafo 1<br><br>Paragrafo 2"
        texto = html_para_texto(html)
        assert "\n" in texto
        assert "Paragrafo 1" in texto
        assert "Paragrafo 2" in texto

    def test_remover_tags_html(self):
        html = "<p>Texto <b>negrito</b> e <i>italico</i></p>"
        texto = html_para_texto(html)
        assert "<p>" not in texto
        assert "<b>" not in texto
        assert "negrito" in texto
        assert "italico" in texto

    def test_preservar_entidades_html(self):
        html = "Art. 5&ordm; da CF&amp;88"
        texto = html_para_texto(html)
        assert "&ordm;" not in texto or "5" in texto
        assert "&amp;" not in texto

    def test_texto_vazio(self):
        assert html_para_texto("") == ""
        assert html_para_texto(None) == ""

    def test_texto_sem_html(self):
        """Texto sem tags HTML deve retornar intacto (com trim)."""
        texto = "Texto simples sem HTML"
        assert html_para_texto(texto).strip() == texto


class TestExtrairNumeroProcesso:
    def test_aresp(self):
        assert extrair_numero_processo("AREsp 2591846") == "2591846"

    def test_resp(self):
        assert extrair_numero_processo("REsp 1234567") == "1234567"

    def test_hc(self):
        assert extrair_numero_processo("HC 789012") == "789012"

    def test_com_espacos_extras(self):
        assert extrair_numero_processo("AREsp 1996346    ") == "1996346"

    def test_classe_aresp(self):
        assert extrair_classe_processual("AREsp 2591846") == "AREsp"

    def test_classe_resp(self):
        assert extrair_classe_processual("REsp 1234567") == "REsp"

    def test_classe_hc(self):
        assert extrair_classe_processual("HC 789012") == "HC"

    def test_processo_vazio(self):
        assert extrair_numero_processo("") == ""
        assert extrair_numero_processo(None) == ""

    def test_classe_vazia(self):
        assert extrair_classe_processual("") == ""
        assert extrair_classe_processual(None) == ""


class TestPrepararRegistroIntegra:
    def test_preparar_registro_completo(self):
        metadados = {
            "SeqDocumento": 353186704,
            "dataPublicacao": "2026-01-22",
            "tipoDocumento": "DECISAO",
            "numeroRegistro": "202400836220",
            "processo": "AREsp 2591846",
            "NM_MINISTRO": "PAULO SERGIO DOMINGUES",
            "teor": "Nao Conhecendo",
            "assuntos": "9992, 10433"
        }
        texto_html = "DECISAO<br>Trata-se de agravo..."

        registro = preparar_registro_integra(metadados, texto_html)

        assert registro["seq_documento"] == 353186704
        assert registro["numero_processo"] == "2591846"
        assert registro["classe_processual"] == "AREsp"
        assert registro["tipo_documento"] == "DECISAO"
        assert registro["ministro"] == "PAULO SERGIO DOMINGUES"
        assert "<br>" not in registro["texto_completo"]
        assert registro["hash_conteudo"] is not None
        assert len(registro["hash_conteudo"]) == 64  # SHA256
        assert registro["data_insercao"] is not None


class TestIntegrasProcessor:
    def test_processar_batch(self, tmp_path):
        """Testa processamento de batch com metadados e textos."""
        # Criar diretorio de textos com um arquivo
        textos_dir = tmp_path / "textos" / "20260122"
        textos_dir.mkdir(parents=True)
        (textos_dir / "353186704.txt").write_text(
            "DECISAO<br>Trata-se de agravo em recurso especial...", encoding="utf-8"
        )

        metadados = [{
            "SeqDocumento": 353186704,
            "dataPublicacao": "2026-01-22",
            "tipoDocumento": "DECISAO",
            "processo": "AREsp 2591846",
            "NM_MINISTRO": "TESTE",
            "teor": "Nao Conhecendo",
            "assuntos": "9992"
        }]

        processor = IntegrasProcessor()
        registros = processor.processar_batch(metadados, textos_dir)

        assert len(registros) == 1
        assert registros[0]["seq_documento"] == 353186704
        assert "<br>" not in registros[0]["texto_completo"]

    def test_processar_batch_texto_nao_encontrado(self, tmp_path):
        """Metadado sem texto correspondente deve ser ignorado."""
        textos_dir = tmp_path / "textos"
        textos_dir.mkdir(parents=True)

        metadados = [{
            "SeqDocumento": 999999999,
            "dataPublicacao": "2026-01-22",
            "tipoDocumento": "DECISAO",
            "processo": "REsp 123",
            "NM_MINISTRO": "TESTE",
            "assuntos": ""
        }]

        processor = IntegrasProcessor()
        registros = processor.processar_batch(metadados, textos_dir)

        assert len(registros) == 0
