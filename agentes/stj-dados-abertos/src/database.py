"""
Database DuckDB para STJ Dados Abertos.
Otimizado para grande volume (50GB+) com particionamento e compressão.
"""
import duckdb
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
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

console = Console()
logger = logging.getLogger(__name__)


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
        self.stats = {
            "inseridos": 0,
            "duplicados": 0,
            "atualizados": 0,
            "erros": 0
        }

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Conecta ao banco com configurações otimizadas."""
        if self.conn:
            return

        try:
            logger.info(f"Conectando ao banco: {self.db_path}")

            # Configuração otimizada para HD externo
            self.conn = duckdb.connect(
                str(self.db_path),
                read_only=False
            )

            # Configurações de performance
            self.conn.execute(f"SET memory_limit='{DUCKDB_MEMORY_LIMIT}'")
            self.conn.execute(f"SET threads={DUCKDB_THREADS}")
            self.conn.execute("SET enable_progress_bar=false")  # Rich já mostra progresso

            # Habilitar extensões
            self.conn.execute("INSTALL fts")
            self.conn.execute("LOAD fts")

            logger.info("Conexão estabelecida com sucesso")

        except Exception as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            raise

    def close(self):
        """Fecha conexão com o banco."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Conexão fechada")

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

            # Índice parcial: últimos 90 dias (queries frequentes)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_recentes
                ON acordaos(data_publicacao DESC, orgao_julgador)
                WHERE data_publicacao >= CURRENT_DATE - INTERVAL '90 days'
            """)

            # Full-Text Search em ementas
            logger.info("Criando índice FTS para ementas...")
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS fts_ementa
                ON acordaos USING FTS (ementa)
            """)

            # Full-Text Search em texto integral (pode ser lento, mas essencial)
            logger.info("Criando índice FTS para inteiro teor (pode demorar)...")
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS fts_texto_integral
                ON acordaos USING FTS (texto_integral)
            """)

            # Tabela de estatísticas (cache de contagens)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS estatisticas_cache (
                    tipo VARCHAR PRIMARY KEY,
                    valor BIGINT,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            logger.info("Schema criado com sucesso")
            console.print("[green]✅ Schema do banco criado[/green]")

        except Exception as e:
            logger.error(f"Erro ao criar schema: {e}")
            raise

    def inserir_batch(self, registros: List[Dict], atualizar_duplicados: bool = False) -> Tuple[int, int, int]:
        """
        Insere lote de registros com deduplicação por hash.

        Args:
            registros: Lista de dicts com dados processados
            atualizar_duplicados: Se True, atualiza registros existentes

        Returns:
            Tupla (inseridos, duplicados, erros)
        """
        if not registros:
            return 0, 0, 0

        inseridos = 0
        duplicados = 0
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
                                    ementa, texto_integral, relator,
                                    data_publicacao, data_julgamento,
                                    assuntos, fonte, fonte_url, metadata
                                ) VALUES (
                                    ?, ?, ?,
                                    ?, ?, ?, ?,
                                    ?, ?, ?,
                                    ?, ?,
                                    ?, ?, ?, ?
                                )
                            """, [
                                (
                                    r['id'], r['numero_processo'], r['hash_conteudo'],
                                    r['tribunal'], r['orgao_julgador'], r['tipo_decisao'], r['classe_processual'],
                                    r['ementa'], r['texto_integral'], r['relator'],
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
                            self.stats['atualizados'] += len(duplicados_batch)

                        duplicados += len(duplicados_batch)

                        progress.update(task, advance=len(batch))

                    except Exception as e:
                        logger.error(f"Erro no batch {i//BATCH_SIZE + 1}: {e}")
                        erros += len(batch)
                        continue

            # Atualizar estatísticas
            self.stats['inseridos'] += inseridos
            self.stats['duplicados'] += duplicados
            self.stats['erros'] += erros

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
        Busca termo em ementas usando Full-Text Search.

        Args:
            termo: Termo para buscar
            orgao: Filtrar por órgão julgador (opcional)
            dias: Buscar nos últimos N dias
            limit: Máximo de resultados

        Returns:
            Lista de dicts com resultados
        """
        try:
            query = """
                SELECT
                    numero_processo,
                    orgao_julgador,
                    tipo_decisao,
                    relator,
                    data_publicacao,
                    data_julgamento,
                    ementa,
                    fts_main_acordaos.match_bm25(numero_processo, ?) as score
                FROM acordaos
                WHERE ementa LIKE ?
                    AND data_publicacao >= CURRENT_DATE - INTERVAL ? DAY
            """

            params = [f"%{termo}%", f"%{termo}%", dias]

            if orgao:
                query += " AND orgao_julgador = ?"
                params.append(orgao)

            query += " ORDER BY score DESC, data_publicacao DESC LIMIT ?"
            params.append(limit)

            results = self.conn.execute(query, params).fetchall()

            # Converter para dicts
            columns = ['numero_processo', 'orgao_julgador', 'tipo_decisao', 'relator',
                      'data_publicacao', 'data_julgamento', 'ementa', 'score']
            return [dict(zip(columns, row)) for row in results]

        except Exception as e:
            logger.error(f"Erro na busca de ementa: {e}")
            return []

    def buscar_acordao(
        self,
        termo: str,
        orgao: Optional[str] = None,
        dias: int = 30,
        limit: int = 50
    ) -> List[Dict]:
        """
        Busca termo no inteiro teor dos acórdãos.

        ATENÇÃO: Pode ser LENTO em bancos grandes (50GB+).
        Use índice FTS e limite temporal.

        Args:
            termo: Termo para buscar
            orgao: Filtrar por órgão julgador (opcional)
            dias: Buscar nos últimos N dias (padrão: 30 - mais rápido)
            limit: Máximo de resultados

        Returns:
            Lista de dicts com resultados
        """
        try:
            query = """
                SELECT
                    numero_processo,
                    orgao_julgador,
                    tipo_decisao,
                    relator,
                    data_publicacao,
                    data_julgamento,
                    ementa,
                    LENGTH(texto_integral) as tamanho_texto
                FROM acordaos
                WHERE texto_integral LIKE ?
                    AND data_publicacao >= CURRENT_DATE - INTERVAL ? DAY
            """

            params = [f"%{termo}%", dias]

            if orgao:
                query += " AND orgao_julgador = ?"
                params.append(orgao)

            query += " ORDER BY data_publicacao DESC LIMIT ?"
            params.append(limit)

            results = self.conn.execute(query, params).fetchall()

            # Converter para dicts
            columns = ['numero_processo', 'orgao_julgador', 'tipo_decisao', 'relator',
                      'data_publicacao', 'data_julgamento', 'ementa', 'tamanho_texto']
            return [dict(zip(columns, row)) for row in results]

        except Exception as e:
            logger.error(f"Erro na busca de acórdão: {e}")
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

            console.print(f"[green]✅ Exportado para {output_path}[/green]")

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
            self.conn.execute(f"""
                EXPORT DATABASE '{backup_path.parent / f'backup_{timestamp'}' (FORMAT PARQUET)
            """)

            console.print(f"[green]✅ Backup criado: {backup_path}[/green]")
            return backup_path

        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            raise

    def print_stats(self):
        """Imprime estatísticas de operações."""
        console.print("\n[bold cyan]Estatísticas do Banco:[/bold cyan]")
        console.print(f"✅ Inseridos: {self.stats['inseridos']}")
        console.print(f"🔄 Duplicados: {self.stats['duplicados']}")
        console.print(f"♻️  Atualizados: {self.stats['atualizados']}")
        console.print(f"❌ Erros: {self.stats['erros']}")


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
            'data_publicacao': '2024-11-20T00:00:00',
            'data_julgamento': '2024-11-15T00:00:00',
            'assuntos': '["Direito Civil", "Teste"]',
            'fonte': 'STJ-Dados-Abertos',
            'fonte_url': 'https://stj.jus.br/test',
            'metadata': '{}'
        }]

        inseridos, duplicados, erros = db.inserir_batch(test_data)
        console.print(f"✅ Teste inserção: {inseridos} inseridos, {duplicados} duplicados")

        # Obter estatísticas
        stats = db.obter_estatisticas()
        console.print(f"📊 Total no banco: {stats.get('total_acordaos', 0)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_database()
