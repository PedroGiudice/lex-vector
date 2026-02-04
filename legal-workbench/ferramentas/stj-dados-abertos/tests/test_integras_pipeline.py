"""
Integration tests for the integras pipeline.

Tests the full workflow: CKAN -> Download -> Extract -> Process -> DuckDB
Also tests correlation between espelhos (acordaos) and integras,
progress resume, and cross-dataset deduplication.
"""
from __future__ import annotations

import json
import zipfile
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.integras_downloader import IntegrasDownloader, DownloadProgress
from src.integras_processor import (
    IntegrasProcessor,
    normalizar_metadados,
    html_para_texto,
    preparar_registro_integra,
)
from src.database import STJDatabase


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def integras_env(tmp_path):
    """Ambiente completo para testes de integras: diretorios + DB."""
    staging = tmp_path / "staging"
    textos = tmp_path / "textos"
    metadata = tmp_path / "metadata"
    progress_file = tmp_path / ".progress.json"
    db_path = tmp_path / "test.duckdb"

    staging.mkdir()
    textos.mkdir()
    metadata.mkdir()

    with STJDatabase(db_path) as db:
        db.criar_schema()

    return {
        "staging": staging,
        "textos": textos,
        "metadata": metadata,
        "progress_file": progress_file,
        "db_path": db_path,
        "tmp_path": tmp_path,
    }


@pytest.fixture
def sample_metadados_diarios():
    """Metadados de integras (formato diario recente)."""
    return [
        {
            "SeqDocumento": 353186704,
            "dataPublicacao": "2026-01-22",
            "tipoDocumento": "DECISAO",
            "numeroRegistro": "202400836220",
            "processo": "AREsp 2591846",
            "NM_MINISTRO": "PAULO SERGIO DOMINGUES",
            "teor": "Nao Conhecendo",
            "assuntos": "9992, 10433",
        },
        {
            "SeqDocumento": 353186705,
            "dataPublicacao": "2026-01-22",
            "tipoDocumento": "ACORDAO",
            "numeroRegistro": "202400836221",
            "processo": "REsp 1234567",
            "NM_MINISTRO": "NANCY ANDRIGHI",
            "teor": "Concedendo",
            "assuntos": "11806",
        },
    ]


@pytest.fixture
def sample_metadados_consolidado():
    """Metadados de integras (formato consolidado mensal com epoch ms)."""
    return [
        {
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
            "assuntos": "11806;11806",
        },
    ]


def _criar_zip_com_textos(zip_path: Path, textos: dict[int, str]):
    """Helper: cria ZIP com arquivos {SeqDocumento}.txt."""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w") as zf:
        for seq, html in textos.items():
            zf.writestr(f"{seq}.txt", html)


# ============================================================================
# Pipeline Completo: Extract -> Process -> Insert -> Query
# ============================================================================


class TestIntegrasPipeline:
    """Pipeline completo: simula ZIP+JSON -> extract -> process -> DuckDB."""

    def test_extract_process_insert_query(
        self, integras_env, sample_metadados_diarios
    ):
        """
        Pipeline completo com dados diarios.

        1. Cria ZIP com textos
        2. Escreve JSON de metadados
        3. Extrai ZIP
        4. Processa batch (HTML->texto + normalizacao)
        5. Insere no DuckDB
        6. Consulta e verifica
        """
        env = integras_env
        date_key = "20260122"

        # 1. Criar ZIP com textos para cada SeqDocumento
        zip_path = env["staging"] / f"{date_key}.zip"
        _criar_zip_com_textos(zip_path, {
            353186704: "DECISAO<br>Trata-se de agravo em recurso especial...<br>Nao conheco.",
            353186705: "<p>ACORDAO</p><p>Trata-se de recurso especial interposto...</p>",
        })

        # 2. Escrever JSON de metadados
        meta_path = env["metadata"] / f"metadados{date_key}.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(sample_metadados_diarios, f, ensure_ascii=False)

        # 3. Extrair ZIP
        downloader = IntegrasDownloader(
            env["staging"], env["textos"], env["metadata"], env["progress_file"]
        )
        dest_dir = env["textos"] / date_key
        extracted = downloader.extract_zip(zip_path, dest_dir)

        assert len(extracted) == 2
        assert (dest_dir / "353186704.txt").exists()
        assert (dest_dir / "353186705.txt").exists()

        # 4. Processar batch
        processor = IntegrasProcessor()
        registros = processor.processar_batch(sample_metadados_diarios, env["textos"])

        assert len(registros) == 2
        assert processor.processados == 2
        assert processor.erros == 0
        assert processor.sem_texto == 0

        # Verificar normalizacao
        reg_decisao = next(r for r in registros if r["seq_documento"] == 353186704)
        assert reg_decisao["tipo_documento"] == "DECISAO"
        assert reg_decisao["numero_processo"] == "2591846"
        assert reg_decisao["classe_processual"] == "AREsp"
        assert reg_decisao["ministro"] == "PAULO SERGIO DOMINGUES"
        assert "<br>" not in reg_decisao["texto_completo"]
        assert "agravo" in reg_decisao["texto_completo"]

        # 5. Inserir no DuckDB
        with STJDatabase(env["db_path"]) as db:
            inseridos, duplicados, erros = db.inserir_integras_batch(registros)

            assert inseridos == 2
            assert duplicados == 0
            assert erros == 0

            # 6. Consultar e verificar
            stats = db.estatisticas_integras()
            assert stats["total_integras"] == 2
            assert "DECISAO" in stats["por_tipo"]
            assert "ACORDAO" in stats["por_tipo"]

            # Buscar por processo
            resultado = db.buscar_por_processo("2591846")
            assert len(resultado["integras"]) == 1
            assert resultado["integras"][0]["numero_processo"] == "2591846"

    def test_pipeline_consolidado_mensal(
        self, integras_env, sample_metadados_consolidado
    ):
        """Pipeline com dados consolidados (epoch ms, campos diferentes)."""
        env = integras_env
        date_key = "202203"

        # Criar ZIP
        zip_path = env["staging"] / f"{date_key}.zip"
        _criar_zip_com_textos(zip_path, {
            146211705: "ACORDAO<br>Vistos, relatados e discutidos os autos...",
        })

        # JSON de metadados
        meta_path = env["metadata"] / f"metadados{date_key}.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(sample_metadados_consolidado, f)

        # Extrair
        downloader = IntegrasDownloader(
            env["staging"], env["textos"], env["metadata"], env["progress_file"]
        )
        dest_dir = env["textos"] / date_key
        downloader.extract_zip(zip_path, dest_dir)

        # Processar
        processor = IntegrasProcessor()
        registros = processor.processar_batch(
            sample_metadados_consolidado, env["textos"]
        )

        assert len(registros) == 1
        reg = registros[0]
        assert reg["seq_documento"] == 146211705
        assert reg["data_publicacao"] == "2022-03-03"
        assert reg["ministro"] == "LUIS FELIPE SALOMAO"
        assert reg["numero_processo"] == "1996346"
        assert reg["classe_processual"] == "AREsp"

        # Inserir e verificar
        with STJDatabase(env["db_path"]) as db:
            inseridos, _, _ = db.inserir_integras_batch(registros)
            assert inseridos == 1


# ============================================================================
# Correlacao Espelhos <-> Integras
# ============================================================================


class TestCorrelacaoEspelhosIntegras:
    """Testa correlacao entre espelhos (acordaos) e integras via numero_processo."""

    def test_buscar_processo_com_ambos(self, integras_env):
        """
        Insere espelho + integra do mesmo processo e verifica correlacao.
        """
        env = integras_env

        with STJDatabase(env["db_path"]) as db:
            # Inserir espelho (tabela acordaos)
            espelho = {
                "id": "uuid-correlacao-1",
                "numero_processo": "2591846",
                "hash_conteudo": "hash-espelho-2591846",
                "tribunal": "STJ",
                "orgao_julgador": "Terceira Turma",
                "tipo_decisao": "ACORDAO",
                "classe_processual": "AREsp",
                "ementa": "RECURSO ESPECIAL. DIREITO CIVIL.",
                "texto_integral": "Texto do espelho...",
                "relator": "PAULO SERGIO DOMINGUES",
                "resultado_julgamento": "provimento",
                "data_publicacao": "2026-01-22T00:00:00",
                "data_julgamento": "2026-01-20T00:00:00",
                "assuntos": '["Direito Civil"]',
                "fonte": "STJ-Dados-Abertos",
                "fonte_url": "https://stj.jus.br/test",
                "metadata": "{}",
            }
            db.inserir_batch([espelho])

            # Inserir integra (tabela integras)
            integra = {
                "seq_documento": 353186704,
                "numero_processo": "2591846",
                "classe_processual": "AREsp",
                "numero_registro": "202400836220",
                "hash_conteudo": "hash-integra-353186704",
                "tipo_documento": "DECISAO",
                "ministro": "PAULO SERGIO DOMINGUES",
                "teor": "Nao Conhecendo",
                "descricao_monocratica": None,
                "texto_completo": "Texto completo da integra...",
                "data_publicacao": "2026-01-22",
                "data_recebimento": None,
                "data_distribuicao": None,
                "data_insercao": datetime.now().isoformat(),
                "assuntos": '["9992", "10433"]',
            }
            db.inserir_integras_batch([integra])

            # Busca unificada
            resultado = db.buscar_por_processo("2591846")

            assert len(resultado["acordaos"]) == 1
            assert len(resultado["integras"]) == 1
            assert resultado["acordaos"][0]["numero_processo"] == "2591846"
            assert resultado["integras"][0]["numero_processo"] == "2591846"
            assert resultado["integras"][0]["ministro"] == "PAULO SERGIO DOMINGUES"

    def test_buscar_processo_sem_integra(self, integras_env):
        """Espelho sem integra correspondente deve retornar apenas acordaos."""
        env = integras_env

        with STJDatabase(env["db_path"]) as db:
            espelho = {
                "id": "uuid-sem-integra",
                "numero_processo": "9999999",
                "hash_conteudo": "hash-sem-integra",
                "tribunal": "STJ",
                "orgao_julgador": "Primeira Turma",
                "tipo_decisao": "ACORDAO",
                "classe_processual": "REsp",
                "ementa": "SEM INTEGRA.",
                "texto_integral": "Apenas espelho.",
                "relator": "TESTE",
                "resultado_julgamento": "provimento",
                "data_publicacao": "2026-01-22T00:00:00",
                "data_julgamento": "2026-01-20T00:00:00",
                "assuntos": "[]",
                "fonte": "STJ-Dados-Abertos",
                "fonte_url": "",
                "metadata": "{}",
            }
            db.inserir_batch([espelho])

            resultado = db.buscar_por_processo("9999999")
            assert len(resultado["acordaos"]) >= 1
            assert len(resultado["integras"]) == 0


# ============================================================================
# Progress Resume
# ============================================================================


class TestProgressResume:
    """Testa retomada de download apos interrupcao."""

    def test_resume_apos_interrupcao(self, integras_env):
        """Simula interrupcao e retomada verificando progresso persistido."""
        env = integras_env

        # Simular primeira execucao: completar 2 de 4
        progress1 = DownloadProgress(env["progress_file"])
        progress1.mark_completed("20260120")
        progress1.mark_completed("20260121")

        # Simular nova execucao (nova instancia lendo do disco)
        progress2 = DownloadProgress(env["progress_file"])
        assert progress2.is_completed("20260120")
        assert progress2.is_completed("20260121")
        assert not progress2.is_completed("20260122")
        assert not progress2.is_completed("20260123")
        assert progress2.total_completed == 2

    def test_download_all_skips_completed(self, integras_env):
        """download_all deve pular pares ja completados."""
        env = integras_env

        # Pre-marcar como completado
        progress = DownloadProgress(env["progress_file"])
        progress.mark_completed("20260120")

        downloader = IntegrasDownloader(
            env["staging"], env["textos"], env["metadata"], env["progress_file"]
        )

        # Criar pares: 1 ja completado, 0 novos (sem URLs reais)
        pairs = [
            {
                "zip_url": "https://fake/20260120.zip",
                "zip_name": "20260120.zip",
                "meta_url": "https://fake/metadados20260120.json",
                "meta_name": "metadados20260120.json",
                "date_key": "20260120",
            },
        ]

        result = downloader.download_all(pairs, force=False)
        assert result["skipped"] == 1
        assert result["completed"] == 0
        assert result["errors"] == 0


# ============================================================================
# Deduplicacao Cross-Dataset
# ============================================================================


class TestDeduplicacaoCrossDataset:
    """Testa que o mesmo documento nao gera duplicata na tabela integras."""

    def test_mesmo_seq_documento_nao_duplica(self, integras_env):
        """Inserir mesmo SeqDocumento duas vezes deve ser idempotente."""
        env = integras_env

        registro = {
            "seq_documento": 353186704,
            "numero_processo": "2591846",
            "classe_processual": "AREsp",
            "numero_registro": "202400836220",
            "hash_conteudo": "hash-dedup-test",
            "tipo_documento": "DECISAO",
            "ministro": "TESTE",
            "teor": "Nao Conhecendo",
            "texto_completo": "Texto completo...",
            "data_publicacao": "2026-01-22",
            "data_insercao": datetime.now().isoformat(),
            "assuntos": "[]",
        }

        with STJDatabase(env["db_path"]) as db:
            ins1, dup1, err1 = db.inserir_integras_batch([registro])
            assert ins1 == 1
            assert dup1 == 0

            ins2, dup2, err2 = db.inserir_integras_batch([registro])
            assert ins2 == 0
            assert dup2 == 1

            stats = db.estatisticas_integras()
            assert stats["total_integras"] == 1

    def test_batch_misto_novos_e_duplicados(self, integras_env):
        """Batch com registros novos e duplicados deve tratar corretamente."""
        env = integras_env

        registros_batch1 = [
            {
                "seq_documento": 100,
                "numero_processo": "111",
                "hash_conteudo": "hash-100",
                "tipo_documento": "DECISAO",
                "texto_completo": "Texto 100",
                "data_publicacao": "2026-01-22",
                "data_insercao": datetime.now().isoformat(),
                "assuntos": "[]",
            },
            {
                "seq_documento": 200,
                "numero_processo": "222",
                "hash_conteudo": "hash-200",
                "tipo_documento": "ACORDAO",
                "texto_completo": "Texto 200",
                "data_publicacao": "2026-01-22",
                "data_insercao": datetime.now().isoformat(),
                "assuntos": "[]",
            },
        ]

        registros_batch2 = [
            registros_batch1[0],  # Duplicata do 100
            {
                "seq_documento": 300,
                "numero_processo": "333",
                "hash_conteudo": "hash-300",
                "tipo_documento": "DECISAO",
                "texto_completo": "Texto 300",
                "data_publicacao": "2026-01-23",
                "data_insercao": datetime.now().isoformat(),
                "assuntos": "[]",
            },
        ]

        with STJDatabase(env["db_path"]) as db:
            ins1, dup1, _ = db.inserir_integras_batch(registros_batch1)
            assert ins1 == 2
            assert dup1 == 0

            ins2, dup2, _ = db.inserir_integras_batch(registros_batch2)
            assert ins2 == 1
            assert dup2 == 1

            stats = db.estatisticas_integras()
            assert stats["total_integras"] == 3
