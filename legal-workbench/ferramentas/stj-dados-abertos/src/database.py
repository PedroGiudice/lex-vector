"""
Database DuckDB para STJ Dados Abertos.
Otimizado para grande volume (50GB+) com particionamento e compressão.
Gold Standard FTS configuration with thread-safety.
"""
from __future__ import annotations

import duckdb
import logging
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Final
from datetime import datetime

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    DATABASE_PATH,
    DATABASE_BACKUP_DIR,
    BATCH_SIZE,
    DUCKDB_MEMORY_LIMIT,
    DUCKDB_THREADS
)

# Gold Standard: Portuguese legal stopwords
STOPWORDS_JURIDICO: Final[list[str]] = [
    # Standard Portuguese
    'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um',
    'para', 'com', 'uma', 'os', 'no', 'se', 'na',
    # Legal connectives (high frequency, low signal)
    'portanto', 'destarte', 'outrossim', 'ademais',
    'mormente', 'deveras', 'conforme', 'sendo', 'assim',
]

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class DatabaseStats:
    """Statistics from database operations."""
    inseridos: int = 0
    duplicados: int = 0
    atualizados: int = 0
    erros: int = 0


class STJDatabase:
    """
    Gerenciador de banco DuckDB para acórdãos do STJ.

    Características:
    - WAL mode para performance em HD externo
    - Particionamento por ano/mês
    - Compressão ZSTD em texto_integral
    - Full-text search via FTS5
    - Índices parciais para queries frequentes
    - Batch insert com deduplicação por hash
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        self.stats = DatabaseStats()
        self._lock = threading.Lock()
        self._local = threading.local()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Conecta ao banco com configurações otimizadas (Gold Standard WSL2)."""
        if self.conn:
            return

        try:
            with self._lock:
                logger.info(f"Conectando ao banco: {self.db_path}")

                # Configuração otimizada para HD externo
                self.conn = duckdb.connect(
                    str(self.db_path),
                    read_only=False
                )

                # Gold Standard WSL2 configuration
                self.conn.execute(f"SET memory_limit = '{DUCKDB_MEMORY_LIMIT}'")
                self.conn.execute(f"SET threads = {DUCKDB_THREADS}")
                self.conn.execute("SET wal_autocheckpoint = '256MB'")
                self.conn.execute("SET preserve_insertion_order = false")
                self.conn.execute("SET enable_progress_bar = false")  # Rich já mostra progresso

                # Habilitar extensões
                self.conn.execute("INSTALL fts")
                self.conn.execute("LOAD fts")

                logger.info("Conexão estabelecida com sucesso (WAL mode)")

        except Exception as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            raise

    def close(self):
        """Fecha conexão com o banco."""
        if self.conn:
            with self._lock:
                self.conn.close()
                self.conn = None
                logger.info("Conexão fechada")

    @contextmanager
    def cursor(self):
        """Context manager for isolated cursor operations (thread-safe)."""
        with self._lock:
            cursor = self.conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def criar_schema(self):
        """
        Cria tabelas e índices do schema STJ.

        DECISÃO DE DESIGN:
        - Não particionar por ano/mês inicialmente (premature optimization)
        - DuckDB já comprime muito bem (ZSTD padrão)
        - Índices parciais para queries frequentes (últimos 90 dias)
        """
        try:
            logger.info("Criando schema do banco...")

            # Tabela de stopwords jurídicas
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS stopwords_juridico (
                    stopword VARCHAR PRIMARY KEY
                )
            """)

            # Inserir stopwords se tabela estiver vazia
            count = self.conn.execute("SELECT COUNT(*) FROM stopwords_juridico").fetchone()[0]
            if count == 0:
                logger.info(f"Inserindo {len(STOPWORDS_JURIDICO)} stopwords jurídicas...")
                self.conn.executemany(
                    "INSERT INTO stopwords_juridico VALUES (?)",
                    [(word,) for word in STOPWORDS_JURIDICO]
                )

            # Tabela principal de acórdãos
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS acordaos (
                    id VARCHAR PRIMARY KEY,
                    numero_processo VARCHAR NOT NULL,
                    hash_conteudo VARCHAR UNIQUE NOT NULL,

                    -- Classificação
                    tribunal VARCHAR DEFAULT 'STJ',
                    orgao_julgador VARCHAR NOT NULL,
                    tipo_decisao VARCHAR,  -- 'Acórdão' ou 'Decisão Monocrática'
                    classe_processual VARCHAR,

                    -- Conteúdo
                    ementa TEXT,
                    texto_integral TEXT,  -- Comprimido automaticamente por DuckDB
                    relator VARCHAR,
                    resultado_julgamento VARCHAR,  -- Resultado do julgamento

                    -- Datas
                    data_publicacao TIMESTAMP,
                    data_julgamento TIMESTAMP,
                    data_insercao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    -- Metadata
                    assuntos TEXT,  -- JSON array
                    fonte VARCHAR DEFAULT 'STJ-Dados-Abertos',
                    fonte_url VARCHAR,
                    metadata TEXT  -- JSON com campos extras
                )
            """)

            # Índices para queries comuns
            logger.info("Criando índices...")

            # Índice principal por hash (deduplicação)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_hash
                ON acordaos(hash_conteudo)
            """)

            # Índice por número de processo (busca específica)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processo
                ON acordaos(numero_processo)
            """)

            # Índice por órgão julgador (filtros)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_orgao
                ON acordaos(orgao_julgador)
            """)

            # Índice composto para queries temporais
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_data_publicacao
                ON acordaos(data_publicacao DESC, orgao_julgador)
            """)

            # Note: DuckDB doesn't support partial indexes (WHERE clause)
            # Índice parcial: últimos 90 dias (queries frequentes)
            # REMOVED: DuckDB não suporta partial indexes yet

            # Full-Text Search (Gold Standard configuration)
            # Um unico indice com ambos os campos (ementa + texto_integral)
            logger.info("Criando indice FTS para ementa e texto_integral (Portuguese stemmer + stopwords juridicas)...")
            try:
                self.conn.execute("""
                    PRAGMA create_fts_index(
                        'acordaos', 'id', 'ementa', 'texto_integral',
                        stemmer = 'portuguese',
                        stopwords = 'stopwords_juridico',
                        strip_accents = 1,
                        lower = 1,
                        overwrite = 1
                    )
                """)
                logger.info("Indice FTS criado com sucesso")
            except Exception as e:
                logger.warning(f"FTS index creation warning (may already exist): {e}")

            # Tabela de estatísticas (cache de contagens)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS estatisticas_cache (
                    tipo VARCHAR PRIMARY KEY,
                    valor BIGINT,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabela de integras (decisoes terminativas + acordaos com texto completo)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS integras (
                    seq_documento BIGINT PRIMARY KEY,
                    numero_processo VARCHAR NOT NULL,
                    classe_processual VARCHAR,
                    numero_registro VARCHAR,
                    hash_conteudo VARCHAR UNIQUE NOT NULL,

                    -- Classificacao
                    tipo_documento VARCHAR NOT NULL,
                    ministro VARCHAR,
                    teor VARCHAR,
                    descricao_monocratica TEXT,
                    recurso VARCHAR,

                    -- Conteudo
                    texto_completo TEXT NOT NULL,

                    -- Datas
                    data_publicacao DATE,
                    data_recebimento DATE,
                    data_distribuicao DATE,
                    data_insercao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    -- Metadata
                    assuntos TEXT
                )
            """)

            # Indices para integras
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_integras_processo ON integras(numero_processo)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_integras_tipo ON integras(tipo_documento)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_integras_ministro ON integras(ministro)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_integras_data_pub ON integras(data_publicacao DESC)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_integras_hash ON integras(hash_conteudo)")

            logger.info("Schema criado com sucesso")
            console.print("[green][OK] Schema do banco criado[/green]")

        except Exception as e:
            logger.error(f"Erro ao criar schema: {e}")
            raise

    def inserir_batch(self, registros: List[Dict], atualizar_duplicados: bool = False) -> Tuple[int, int, int]:
        """
        Insere lote de registros com deduplicacao por hash.

        Args:
            registros: Lista de dicts com dados processados
            atualizar_duplicados: Se True, atualiza registros existentes

        Returns:
            Tupla (inseridos, duplicados, erros)
        """
        if not registros:
            return 0, 0, 0

        # FASE 1: Deduplicar registros de entrada (mesmo acordao pode estar em multiplos arquivos)
        registros_unicos = {}
        duplicados_entrada = 0
        for r in registros:
            h = r['hash_conteudo']
            if h not in registros_unicos:
                registros_unicos[h] = r
            else:
                duplicados_entrada += 1

        if duplicados_entrada > 0:
            logger.info(f"Deduplicacao de entrada: {duplicados_entrada} duplicatas removidas, {len(registros_unicos)} unicos")

        registros = list(registros_unicos.values())

        inseridos = 0
        duplicados = duplicados_entrada  # Contar duplicatas de entrada
        erros = 0

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Inserindo {len(registros)} registros...",
                    total=len(registros)
                )

                # Processar em batches
                for i in range(0, len(registros), BATCH_SIZE):
                    batch = registros[i:i + BATCH_SIZE]

                    try:
                        # Verificar quais hashes já existem
                        hashes = [r['hash_conteudo'] for r in batch]
                        placeholders = ','.join(['?' for _ in hashes])

                        existing_hashes = set(
                            row[0] for row in self.conn.execute(
                                f"SELECT hash_conteudo FROM acordaos WHERE hash_conteudo IN ({placeholders})",
                                hashes
                            ).fetchall()
                        )

                        # Separar novos e duplicados
                        novos = [r for r in batch if r['hash_conteudo'] not in existing_hashes]
                        duplicados_batch = [r for r in batch if r['hash_conteudo'] in existing_hashes]

                        # Inserir novos
                        if novos:
                            self.conn.executemany("""
                                INSERT INTO acordaos (
                                    id, numero_processo, hash_conteudo,
                                    tribunal, orgao_julgador, tipo_decisao, classe_processual,
                                    ementa, texto_integral, relator, resultado_julgamento,
                                    data_publicacao, data_julgamento,
                                    assuntos, fonte, fonte_url, metadata
                                ) VALUES (
                                    ?, ?, ?,
                                    ?, ?, ?, ?,
                                    ?, ?, ?, ?,
                                    ?, ?,
                                    ?, ?, ?, ?
                                )
                            """, [
                                (
                                    r['id'], r['numero_processo'], r['hash_conteudo'],
                                    r['tribunal'], r['orgao_julgador'], r['tipo_decisao'], r['classe_processual'],
                                    r['ementa'], r['texto_integral'], r['relator'], r.get('resultado_julgamento'),
                                    r['data_publicacao'], r['data_julgamento'],
                                    r['assuntos'], r['fonte'], r['fonte_url'], r['metadata']
                                )
                                for r in novos
                            ])
                            inseridos += len(novos)

                        # Atualizar duplicados se solicitado
                        if atualizar_duplicados and duplicados_batch:
                            for reg in duplicados_batch:
                                self.conn.execute("""
                                    UPDATE acordaos SET
                                        ementa = ?,
                                        texto_integral = ?,
                                        relator = ?,
                                        data_publicacao = ?,
                                        data_julgamento = ?
                                    WHERE hash_conteudo = ?
                                """, (
                                    reg['ementa'], reg['texto_integral'], reg['relator'],
                                    reg['data_publicacao'], reg['data_julgamento'],
                                    reg['hash_conteudo']
                                ))
                            self.stats.atualizados += len(duplicados_batch)

                        duplicados += len(duplicados_batch)

                        progress.update(task, advance=len(batch))

                    except Exception as e:
                        logger.error(f"Erro no batch {i//BATCH_SIZE + 1}: {e}")
                        erros += len(batch)
                        continue

            # Atualizar estatísticas
            self.stats.inseridos += inseridos
            self.stats.duplicados += duplicados
            self.stats.erros += erros

            logger.info(f"Batch inserido: {inseridos} novos, {duplicados} duplicados, {erros} erros")
            return inseridos, duplicados, erros

        except Exception as e:
            logger.error(f"Erro ao inserir batch: {e}")
            raise

    def buscar_ementa(
        self,
        termo: str,
        orgao: Optional[str] = None,
        dias: int = 365,
        limit: int = 100
    ) -> List[Dict]:
        """
        Busca termo em ementas usando Full-Text Search (BM25).

        Args:
            termo: Termo para buscar (suporta stemming portugues)
            orgao: Filtrar por orgao julgador (opcional)
            dias: Buscar nos ultimos N dias
            limit: Maximo de resultados

        Returns:
            Lista de dicts com resultados ordenados por relevancia
        """
        try:
            # Usar FTS com BM25 para ranking por relevancia
            # fields := 'ementa' para buscar apenas na ementa
            query = f"""
                SELECT
                    id,
                    numero_processo,
                    orgao_julgador,
                    tipo_decisao,
                    relator,
                    data_publicacao,
                    data_julgamento,
                    ementa,
                    resultado_julgamento,
                    score
                FROM (
                    SELECT *,
                        fts_main_acordaos.match_bm25(id, ?, fields := 'ementa') AS score
                    FROM acordaos
                    WHERE data_publicacao >= CURRENT_DATE - INTERVAL '{dias} DAY'
            """

            params = [termo]

            if orgao:
                query += " AND orgao_julgador = ?"
                params.append(orgao)

            query += """
                ) sq
                WHERE score IS NOT NULL
                ORDER BY score DESC
                LIMIT ?
            """
            params.append(limit)

            results = self.conn.execute(query, params).fetchall()

            # Converter para dicts
            columns = ['id', 'numero_processo', 'orgao_julgador', 'tipo_decisao', 'relator',
                      'data_publicacao', 'data_julgamento', 'ementa', 'resultado_julgamento', 'score']
            return [dict(zip(columns, row)) for row in results]

        except Exception as e:
            logger.error(f"Erro na busca de ementa: {e}")
            return []

    def buscar_acordao(
        self,
        termo: str,
        orgao: Optional[str] = None,
        dias: int = 365,
        limit: int = 100
    ) -> List[Dict]:
        """
        Busca termo no inteiro teor dos acordaos usando Full-Text Search (BM25).

        Args:
            termo: Termo para buscar (suporta stemming portugues)
            orgao: Filtrar por orgao julgador (opcional)
            dias: Buscar nos ultimos N dias
            limit: Maximo de resultados

        Returns:
            Lista de dicts com resultados ordenados por relevancia
        """
        try:
            # Usar FTS com BM25 para ranking por relevancia
            # fields := 'texto_integral' para buscar no inteiro teor
            query = f"""
                SELECT
                    id,
                    numero_processo,
                    orgao_julgador,
                    tipo_decisao,
                    relator,
                    data_publicacao,
                    data_julgamento,
                    ementa,
                    resultado_julgamento,
                    LENGTH(texto_integral) as tamanho_texto,
                    score
                FROM (
                    SELECT *,
                        fts_main_acordaos.match_bm25(id, ?, fields := 'texto_integral') AS score
                    FROM acordaos
                    WHERE data_publicacao >= CURRENT_DATE - INTERVAL '{dias} DAY'
            """

            params = [termo]

            if orgao:
                query += " AND orgao_julgador = ?"
                params.append(orgao)

            query += """
                ) sq
                WHERE score IS NOT NULL
                ORDER BY score DESC
                LIMIT ?
            """
            params.append(limit)

            results = self.conn.execute(query, params).fetchall()

            # Converter para dicts
            columns = ['id', 'numero_processo', 'orgao_julgador', 'tipo_decisao', 'relator',
                      'data_publicacao', 'data_julgamento', 'ementa', 'resultado_julgamento', 'tamanho_texto', 'score']
            return [dict(zip(columns, row)) for row in results]

        except Exception as e:
            logger.error(f"Erro na busca de acordao: {e}")
            return []

    def obter_estatisticas(self) -> Dict:
        """
        Obtém estatísticas do banco.

        Returns:
            Dict com contagens e métricas
        """
        try:
            stats = {}

            # Total de acórdãos
            stats['total_acordaos'] = self.conn.execute(
                "SELECT COUNT(*) FROM acordaos"
            ).fetchone()[0]

            # Por órgão julgador
            stats['por_orgao'] = dict(
                self.conn.execute("""
                    SELECT orgao_julgador, COUNT(*)
                    FROM acordaos
                    GROUP BY orgao_julgador
                    ORDER BY COUNT(*) DESC
                """).fetchall()
            )

            # Por tipo de decisão
            stats['por_tipo'] = dict(
                self.conn.execute("""
                    SELECT tipo_decisao, COUNT(*)
                    FROM acordaos
                    GROUP BY tipo_decisao
                """).fetchall()
            )

            # Período coberto
            periodo = self.conn.execute("""
                SELECT
                    MIN(data_publicacao) as mais_antigo,
                    MAX(data_publicacao) as mais_recente
                FROM acordaos
            """).fetchone()

            stats['periodo'] = {
                'mais_antigo': periodo[0],
                'mais_recente': periodo[1]
            }

            # Tamanho do banco
            stats['tamanho_db_mb'] = self.db_path.stat().st_size / (1024 * 1024)

            # Últimos 30 dias
            stats['ultimos_30_dias'] = self.conn.execute("""
                SELECT COUNT(*) FROM acordaos
                WHERE data_publicacao >= CURRENT_DATE - INTERVAL '30 days'
            """).fetchone()[0]

            return stats

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    def get_dataframe(self, query: str, params: Optional[list] = None) -> pd.DataFrame:
        """
        Execute query and return pandas DataFrame.

        Args:
            query: SQL query to execute
            params: Optional query parameters

        Returns:
            pandas DataFrame with query results
        """
        try:
            if params:
                return self.conn.execute(query, params).df()
            else:
                return self.conn.execute(query).df()
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            raise

    def rebuild_fts_index(self):
        """
        Rebuild FTS index after INSERT/UPDATE/DELETE operations.
        DuckDB FTS requires manual rebuild after data modifications.
        """
        try:
            logger.info("Reconstruindo indice FTS...")

            # Recriar indice FTS com ambos os campos (Gold Standard configuration)
            self.conn.execute("""
                PRAGMA create_fts_index(
                    'acordaos', 'id', 'ementa', 'texto_integral',
                    stemmer = 'portuguese',
                    stopwords = 'stopwords_juridico',
                    strip_accents = 1,
                    lower = 1,
                    overwrite = 1
                )
            """)

            console.print("[green]Indice FTS reconstruido[/green]")
            logger.info("Indice FTS reconstruido com sucesso")

        except Exception as e:
            logger.error(f"Erro ao reconstruir indice FTS: {e}")
            raise

    def rebuild_fts_integras(self):
        """Rebuild FTS index para tabela integras."""
        try:
            logger.info("Criando/reconstruindo indice FTS para integras...")
            self.conn.execute("""
                PRAGMA create_fts_index(
                    'integras', 'seq_documento', 'texto_completo',
                    stemmer = 'portuguese',
                    stopwords = 'stopwords_juridico',
                    strip_accents = 1,
                    lower = 1,
                    overwrite = 1
                )
            """)
            logger.info("Indice FTS integras criado")
        except Exception as e:
            logger.warning(f"FTS integras warning: {e}")

    def inserir_integras_batch(self, registros: list[dict]) -> tuple[int, int, int]:
        """Insere batch de integras com deduplicacao por seq_documento."""
        if not registros:
            return 0, 0, 0

        inseridos = 0
        duplicados = 0
        erros = 0

        try:
            for i in range(0, len(registros), BATCH_SIZE):
                batch = registros[i:i + BATCH_SIZE]

                # Verificar quais seq_documento ja existem
                seqs = [r['seq_documento'] for r in batch]
                placeholders = ','.join(['?' for _ in seqs])
                existing = set(
                    row[0] for row in self.conn.execute(
                        f"SELECT seq_documento FROM integras WHERE seq_documento IN ({placeholders})",
                        seqs
                    ).fetchall()
                )

                novos = [r for r in batch if r['seq_documento'] not in existing]
                duplicados += len(batch) - len(novos)

                if novos:
                    self.conn.executemany("""
                        INSERT INTO integras (
                            seq_documento, numero_processo, classe_processual,
                            numero_registro, hash_conteudo,
                            tipo_documento, ministro, teor,
                            descricao_monocratica, recurso,
                            texto_completo,
                            data_publicacao, data_recebimento, data_distribuicao,
                            data_insercao, assuntos
                        ) VALUES (
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?,
                            ?,
                            ?, ?, ?,
                            ?, ?
                        )
                    """, [
                        (
                            r['seq_documento'], r['numero_processo'], r.get('classe_processual'),
                            r.get('numero_registro'), r['hash_conteudo'],
                            r['tipo_documento'], r.get('ministro'), r.get('teor'),
                            r.get('descricao_monocratica'), r.get('recurso'),
                            r['texto_completo'],
                            r.get('data_publicacao'), r.get('data_recebimento'), r.get('data_distribuicao'),
                            r.get('data_insercao'), r.get('assuntos', '[]'),
                        )
                        for r in novos
                    ])
                    inseridos += len(novos)

        except Exception as e:
            logger.error(f"Erro ao inserir integras: {e}")
            erros += len(registros) - inseridos - duplicados

        return inseridos, duplicados, erros

    def buscar_integras(
        self,
        termo: str,
        tipo: str = None,
        dias: int = 365,
        limit: int = 20
    ) -> list[dict]:
        """FTS no texto_completo das integras."""
        try:
            query = f"""
                SELECT
                    seq_documento, numero_processo, classe_processual,
                    tipo_documento, ministro, teor,
                    data_publicacao,
                    LEFT(texto_completo, 200) as preview,
                    score
                FROM (
                    SELECT *,
                        fts_main_integras.match_bm25(seq_documento, ?) AS score
                    FROM integras
                    WHERE data_publicacao >= CURRENT_DATE - INTERVAL '{dias} DAY'
            """
            params = [termo]

            if tipo:
                query += " AND tipo_documento = ?"
                params.append(tipo)

            query += """
                ) sq
                WHERE score IS NOT NULL
                ORDER BY score DESC
                LIMIT ?
            """
            params.append(limit)

            results = self.conn.execute(query, params).fetchall()
            columns = ['seq_documento', 'numero_processo', 'classe_processual',
                       'tipo_documento', 'ministro', 'teor',
                       'data_publicacao', 'preview', 'score']
            return [dict(zip(columns, row)) for row in results]

        except Exception as e:
            logger.error(f"Erro na busca de integras: {e}")
            return []

    def buscar_por_processo(self, numero_processo: str) -> dict:
        """
        Busca unificada: retorna espelho (acordao) + integra(s) do mesmo processo.
        """
        resultado = {'numero_processo': numero_processo, 'acordaos': [], 'integras': []}

        try:
            # Buscar nos espelhos (acordaos)
            acordaos = self.conn.execute(
                "SELECT * FROM acordaos WHERE numero_processo LIKE ?",
                [f'%{numero_processo}%']
            ).fetchall()
            if acordaos:
                cols = [desc[0] for desc in self.conn.execute("SELECT * FROM acordaos LIMIT 0").description]
                resultado['acordaos'] = [dict(zip(cols, row)) for row in acordaos]
        except Exception:
            pass

        try:
            # Buscar nas integras
            integras = self.conn.execute(
                "SELECT * FROM integras WHERE numero_processo = ?",
                [numero_processo]
            ).fetchall()
            if integras:
                cols = [desc[0] for desc in self.conn.execute("SELECT * FROM integras LIMIT 0").description]
                resultado['integras'] = [dict(zip(cols, row)) for row in integras]
        except Exception:
            pass

        return resultado

    def estatisticas_integras(self) -> dict:
        """Estatisticas da tabela integras."""
        try:
            stats = {}
            stats['total_integras'] = self.conn.execute(
                "SELECT COUNT(*) FROM integras"
            ).fetchone()[0]

            stats['por_tipo'] = dict(
                self.conn.execute("""
                    SELECT tipo_documento, COUNT(*)
                    FROM integras
                    GROUP BY tipo_documento
                    ORDER BY COUNT(*) DESC
                """).fetchall()
            )

            stats['por_ministro_top10'] = dict(
                self.conn.execute("""
                    SELECT ministro, COUNT(*)
                    FROM integras
                    WHERE ministro IS NOT NULL
                    GROUP BY ministro
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """).fetchall()
            )

            periodo = self.conn.execute("""
                SELECT MIN(data_publicacao), MAX(data_publicacao)
                FROM integras
            """).fetchone()
            stats['periodo'] = {
                'mais_antigo': periodo[0],
                'mais_recente': periodo[1]
            }

            return stats
        except Exception as e:
            logger.error(f"Erro ao obter estatisticas de integras: {e}")
            return {}

    def exportar_csv(self, query: str, output_path: Path):
        """
        Exporta resultados de query para CSV.

        Args:
            query: Query SQL para exportar
            output_path: Caminho do arquivo CSV
        """
        try:
            logger.info(f"Exportando para: {output_path}")

            self.conn.execute(f"""
                COPY ({query})
                TO '{output_path}'
                (HEADER, DELIMITER ',')
            """)

            console.print(f"[green][OK] Exportado para {output_path}[/green]")

        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            raise

    def backup(self) -> Path:
        """
        Cria backup do banco.

        Returns:
            Path do arquivo de backup
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = DATABASE_BACKUP_DIR / f"stj_backup_{timestamp}.duckdb"

            logger.info(f"Criando backup: {backup_path}")

            # DuckDB: EXPORT DATABASE
            backup_dir = backup_path.parent / f'backup_{timestamp}'
            self.conn.execute(f"""
                EXPORT DATABASE '{backup_dir}' (FORMAT PARQUET)
            """)

            console.print(f"[green][OK] Backup criado: {backup_path}[/green]")
            return backup_path

        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            raise

    def print_stats(self):
        """Imprime estatísticas de operações."""
        console.print("\n[bold cyan]Estatísticas do Banco:[/bold cyan]")
        console.print(f"[OK] Inseridos: {self.stats.inseridos}")
        console.print(f"🔄 Duplicados: {self.stats.duplicados}")
        console.print(f"♻️  Atualizados: {self.stats.atualizados}")
        console.print(f"[ERRO] Erros: {self.stats.erros}")


def test_database():
    """Teste do módulo de database."""
    console.print("[bold green]Teste: Database STJ[/bold green]")

    with STJDatabase() as db:
        # Criar schema
        db.criar_schema()

        # Inserir dados de teste
        test_data = [{
            'id': '550e8400-e29b-41d4-a716-446655440000',
            'numero_processo': 'REsp 1234567/SP',
            'hash_conteudo': 'abc123def456',
            'tribunal': 'STJ',
            'orgao_julgador': 'Terceira Turma',
            'tipo_decisao': 'Acórdão',
            'classe_processual': 'REsp',
            'ementa': 'TESTE. EMENTA DE TESTE.',
            'texto_integral': 'Texto completo do acórdão de teste...',
            'relator': 'Ministro Teste',
            'resultado_julgamento': 'Recurso provido',
            'data_publicacao': '2024-11-20T00:00:00',
            'data_julgamento': '2024-11-15T00:00:00',
            'assuntos': '["Direito Civil", "Teste"]',
            'fonte': 'STJ-Dados-Abertos',
            'fonte_url': 'https://stj.jus.br/test',
            'metadata': '{}'
        }]

        inseridos, duplicados, erros = db.inserir_batch(test_data)
        console.print(f"[OK] Teste inserção: {inseridos} inseridos, {duplicados} duplicados")

        # Obter estatísticas
        stats = db.obter_estatisticas()
        console.print(f" Total no banco: {stats.get('total_acordaos', 0)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_database()
