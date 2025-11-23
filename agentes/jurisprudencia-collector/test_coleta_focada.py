#!/usr/bin/env python3
"""
Teste Focado de Coleta - STJ e TJSP 2ª Instância

Script de teste para validar coleta de publicações de tribunais específicos.

Uso:
    python test_coleta_focada.py
"""

import sys
import sqlite3
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import asdict

# Adicionar src/ ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from downloader import DJENDownloader, PublicacaoRaw
from processador_texto import processar_publicacao, validar_publicacao_processada

# ==============================================================================
# CONFIGURAÇÃO DE LOGGING
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURAÇÃO DO TESTE
# ==============================================================================

# Diretórios
DATA_ROOT = Path(__file__).parent / 'test_data'
DB_PATH = Path(__file__).parent / 'jurisprudencia_teste_focado.db'

# Tribunais a testar
TRIBUNAIS_TESTE = [
    {
        'tribunal': 'STJ',
        'descricao': 'STJ - Superior Tribunal de Justiça',
        'instancia': 'superior'
    },
    {
        'tribunal': 'TJSP',
        'descricao': 'TJSP - 2ª Instância',
        'instancia': '2'
    }
]

# ==============================================================================
# FUNÇÕES DE BANCO DE DADOS
# ==============================================================================

def inicializar_banco() -> sqlite3.Connection:
    """
    Inicializa banco de teste (cria se não existir).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')

    # Criar tabela se não existir
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS publicacoes (
            id                  TEXT PRIMARY KEY,
            hash_conteudo       TEXT NOT NULL UNIQUE,
            numero_processo     TEXT,
            numero_processo_fmt TEXT,
            tribunal            TEXT NOT NULL,
            orgao_julgador      TEXT,
            tipo_publicacao     TEXT NOT NULL,
            classe_processual   TEXT,
            assuntos            TEXT,
            texto_html          TEXT NOT NULL,
            texto_limpo         TEXT NOT NULL,
            ementa              TEXT,
            data_publicacao     TEXT NOT NULL,
            data_julgamento     TEXT,
            relator             TEXT,
            fonte               TEXT NOT NULL,
            data_insercao       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_publicacoes_processo ON publicacoes(numero_processo);
        CREATE INDEX IF NOT EXISTS idx_publicacoes_tribunal ON publicacoes(tribunal);
        CREATE INDEX IF NOT EXISTS idx_publicacoes_data_pub ON publicacoes(data_publicacao);
        CREATE INDEX IF NOT EXISTS idx_publicacoes_tipo ON publicacoes(tipo_publicacao);
        CREATE INDEX IF NOT EXISTS idx_publicacoes_hash ON publicacoes(hash_conteudo);

        CREATE TABLE IF NOT EXISTS downloads_historico (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            tribunal            TEXT NOT NULL,
            data_publicacao     TEXT NOT NULL,
            tipo_download       TEXT NOT NULL,
            total_publicacoes   INTEGER NOT NULL DEFAULT 0,
            total_novas         INTEGER NOT NULL DEFAULT 0,
            total_duplicadas    INTEGER NOT NULL DEFAULT 0,
            tempo_processamento REAL NOT NULL DEFAULT 0.0,
            status              TEXT NOT NULL,
            erro                TEXT,
            data_execucao       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    logger.info(f"Banco de dados inicializado: {DB_PATH}")
    return conn


def inserir_publicacao(conn: sqlite3.Connection, pub: Dict) -> bool:
    """
    Insere publicação no banco se não existir (via hash).

    Returns:
        True se foi nova inserção, False se duplicata
    """
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO publicacoes (
                id, hash_conteudo, numero_processo, numero_processo_fmt,
                tribunal, orgao_julgador, tipo_publicacao, classe_processual,
                assuntos, texto_html, texto_limpo, ementa,
                data_publicacao, data_julgamento, relator, fonte
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pub['id'],
            pub['hash_conteudo'],
            pub['numero_processo'],
            pub['numero_processo_fmt'],
            pub['tribunal'],
            pub['orgao_julgador'],
            pub['tipo_publicacao'],
            pub['classe_processual'],
            pub.get('assuntos'),
            pub['texto_html'],
            pub['texto_limpo'],
            pub['ementa'],
            pub['data_publicacao'],
            pub.get('data_julgamento'),
            pub['relator'],
            pub['fonte']
        ))
        conn.commit()
        return True

    except sqlite3.IntegrityError as e:
        logger.debug(f"Publicação duplicada: {pub['hash_conteudo'][:16]}...")
        return False


def registrar_download(
    conn: sqlite3.Connection,
    tribunal: str,
    data_publicacao: str,
    tipo_download: str,
    stats: Dict
) -> None:
    """
    Registra metadados de download.
    """
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO downloads_historico (
                tribunal, data_publicacao, tipo_download,
                total_publicacoes, total_novas, total_duplicadas,
                tempo_processamento, status, erro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tribunal,
            data_publicacao,
            tipo_download,
            stats.get('total_publicacoes', 0),
            stats.get('total_novas', 0),
            stats.get('total_duplicadas', 0),
            stats.get('tempo_processamento', 0.0),
            stats.get('status', 'sucesso'),
            stats.get('erro')
        ))
        conn.commit()
        logger.debug(f"[{tribunal}] Registro de download salvo")

    except Exception as e:
        logger.error(f"[{tribunal}] Erro ao registrar download: {e}")


# ==============================================================================
# PROCESSAMENTO
# ==============================================================================

def processar_publicacoes(
    conn: sqlite3.Connection,
    publicacoes: List[PublicacaoRaw],
    tribunal: str
) -> Dict[str, int]:
    """
    Processa publicações brutas e insere no banco.

    Returns:
        Estatísticas de processamento
    """
    stats = {
        'total': len(publicacoes),
        'novas': 0,
        'duplicadas': 0,
        'erros': 0,
        'acordaos': 0,
        'decisoes': 0,
        'intimacoes': 0
    }

    for pub_raw in publicacoes:
        try:
            # Converter para dict
            raw_dict = asdict(pub_raw)

            # Processar
            pub_processada = processar_publicacao(raw_dict)

            # Validar
            if not validar_publicacao_processada(pub_processada):
                logger.warning(f"[{tribunal}] Publicação inválida: {pub_raw.id}")
                stats['erros'] += 1
                continue

            # Contar por tipo
            tipo = pub_processada['tipo_publicacao']
            if tipo == 'Acórdão':
                stats['acordaos'] += 1
            elif tipo == 'Decisão':
                stats['decisoes'] += 1
            elif tipo == 'Intimação':
                stats['intimacoes'] += 1

            # Inserir
            if inserir_publicacao(conn, pub_processada):
                stats['novas'] += 1
            else:
                stats['duplicadas'] += 1

        except Exception as e:
            logger.error(f"[{tribunal}] Erro ao processar {pub_raw.id}: {e}")
            stats['erros'] += 1

    return stats


# ==============================================================================
# TESTE PRINCIPAL
# ==============================================================================

def executar_teste():
    """
    Executa teste de coleta focada.
    """
    logger.info("=" * 80)
    logger.info("TESTE FOCADO DE COLETA - STJ E TJSP 2ª INSTÂNCIA")
    logger.info("=" * 80)

    # Data de hoje
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    logger.info(f"Data: {data_hoje}")
    logger.info(f"Tribunais: {len(TRIBUNAIS_TESTE)}")

    # Inicializar downloader
    downloader = DJENDownloader(
        data_root=DATA_ROOT,
        requests_per_minute=30,
        delay_seconds=2.0,
        max_retries=3
    )

    # Conectar banco
    conn = inicializar_banco()

    # Estatísticas globais
    stats_globais = {
        'total_tribunais': len(TRIBUNAIS_TESTE),
        'tribunais_sucesso': 0,
        'tribunais_falha': 0,
        'total_publicacoes': 0,
        'total_novas': 0,
        'total_duplicadas': 0,
        'total_acordaos': 0,
        'total_decisoes': 0,
        'total_intimacoes': 0,
        'inicio': datetime.now()
    }

    # Processar cada tribunal
    for idx, config in enumerate(TRIBUNAIS_TESTE, 1):
        tribunal = config['tribunal']
        descricao = config['descricao']
        instancia = config['instancia']

        logger.info(f"\n{'=' * 80}")
        logger.info(f"[{idx}/{len(TRIBUNAIS_TESTE)}] {descricao}")
        logger.info(f"Instância: {instancia}")
        logger.info(f"{'=' * 80}")

        inicio_tribunal = time.time()

        try:
            # Baixar via API
            logger.info(f"[{tribunal}] Baixando publicações via API...")
            publicacoes = downloader.baixar_api(
                tribunal=tribunal,
                data=data_hoje,
                limit=100,
                max_pages=2  # Limitar a 2 páginas para teste
            )

            logger.info(f"[{tribunal}] {len(publicacoes)} publicações baixadas")

            if publicacoes:
                # Processar
                stats_proc = processar_publicacoes(conn, publicacoes, tribunal)

                # Atualizar globais
                stats_globais['total_publicacoes'] += len(publicacoes)
                stats_globais['total_novas'] += stats_proc['novas']
                stats_globais['total_duplicadas'] += stats_proc['duplicadas']
                stats_globais['total_acordaos'] += stats_proc['acordaos']
                stats_globais['total_decisoes'] += stats_proc['decisoes']
                stats_globais['total_intimacoes'] += stats_proc['intimacoes']
                stats_globais['tribunais_sucesso'] += 1

                # Registrar
                tempo_processamento = time.time() - inicio_tribunal
                registrar_download(
                    conn=conn,
                    tribunal=f"{tribunal}:{instancia}",
                    data_publicacao=data_hoje,
                    tipo_download='api',
                    stats={
                        'total_publicacoes': len(publicacoes),
                        'total_novas': stats_proc['novas'],
                        'total_duplicadas': stats_proc['duplicadas'],
                        'tempo_processamento': tempo_processamento,
                        'status': 'sucesso' if stats_proc['erros'] == 0 else 'parcial',
                        'erro': None
                    }
                )

                # Log detalhado
                logger.info(f"[{tribunal}] Processamento concluído em {tempo_processamento:.1f}s")
                logger.info(f"  ├─ Novas: {stats_proc['novas']}")
                logger.info(f"  ├─ Duplicadas: {stats_proc['duplicadas']}")
                logger.info(f"  ├─ Acórdãos: {stats_proc['acordaos']}")
                logger.info(f"  ├─ Decisões: {stats_proc['decisoes']}")
                logger.info(f"  ├─ Intimações: {stats_proc['intimacoes']}")
                logger.info(f"  └─ Erros: {stats_proc['erros']}")

            else:
                logger.warning(f"[{tribunal}] Nenhuma publicação baixada")
                stats_globais['tribunais_falha'] += 1

        except Exception as e:
            logger.error(f"[{tribunal}] ERRO: {e}")
            stats_globais['tribunais_falha'] += 1

    # Fechar conexão
    conn.close()

    # Relatório final
    tempo_total = (datetime.now() - stats_globais['inicio']).total_seconds()

    logger.info("\n" + "=" * 80)
    logger.info("RELATÓRIO FINAL DO TESTE")
    logger.info("=" * 80)
    logger.info(f"Tempo total: {tempo_total:.1f}s ({tempo_total/60:.1f} minutos)")
    logger.info(f"Tribunais testados: {stats_globais['total_tribunais']}")
    logger.info(f"  ✓ Sucesso: {stats_globais['tribunais_sucesso']}")
    logger.info(f"  ✗ Falha: {stats_globais['tribunais_falha']}")
    logger.info("")
    logger.info(f"Publicações baixadas: {stats_globais['total_publicacoes']}")
    logger.info(f"  ├─ Novas no banco: {stats_globais['total_novas']}")
    logger.info(f"  └─ Duplicadas: {stats_globais['total_duplicadas']}")
    logger.info("")
    logger.info("Distribuição por tipo:")
    logger.info(f"  ├─ Acórdãos: {stats_globais['total_acordaos']} ({stats_globais['total_acordaos']/max(stats_globais['total_publicacoes'],1)*100:.1f}%)")
    logger.info(f"  ├─ Decisões: {stats_globais['total_decisoes']} ({stats_globais['total_decisoes']/max(stats_globais['total_publicacoes'],1)*100:.1f}%)")
    logger.info(f"  └─ Intimações: {stats_globais['total_intimacoes']} ({stats_globais['total_intimacoes']/max(stats_globais['total_publicacoes'],1)*100:.1f}%)")
    logger.info("")
    logger.info(f"Banco de dados: {DB_PATH}")
    logger.info("=" * 80)

    # Consultas de validação
    logger.info("\n" + "=" * 80)
    logger.info("VALIDAÇÃO DOS DADOS")
    logger.info("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total no banco
    cursor.execute("SELECT COUNT(*) FROM publicacoes")
    total_banco = cursor.fetchone()[0]
    logger.info(f"Total de publicações no banco: {total_banco}")

    # Por tribunal
    cursor.execute("SELECT tribunal, COUNT(*) FROM publicacoes GROUP BY tribunal")
    for row in cursor.fetchall():
        logger.info(f"  ├─ {row[0]}: {row[1]}")

    # Por tipo
    cursor.execute("SELECT tipo_publicacao, COUNT(*) FROM publicacoes GROUP BY tipo_publicacao")
    logger.info("\nPor tipo:")
    for row in cursor.fetchall():
        logger.info(f"  ├─ {row[0]}: {row[1]}")

    # Ementas extraídas
    cursor.execute("SELECT COUNT(*) FROM publicacoes WHERE ementa IS NOT NULL AND ementa != ''")
    ementas = cursor.fetchone()[0]
    logger.info(f"\nEmentas extraídas: {ementas}/{total_banco} ({ementas/max(total_banco,1)*100:.1f}%)")

    # Relatores extraídos
    cursor.execute("SELECT COUNT(*) FROM publicacoes WHERE relator IS NOT NULL AND relator != ''")
    relatores = cursor.fetchone()[0]
    logger.info(f"Relatores extraídos: {relatores}/{total_banco} ({relatores/max(total_banco,1)*100:.1f}%)")

    conn.close()

    logger.info("=" * 80)
    logger.info("✅ TESTE CONCLUÍDO")
    logger.info("=" * 80)


if __name__ == '__main__':
    executar_teste()
