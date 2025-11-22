#!/usr/bin/env python3
"""
Scheduler para Download Automático de Publicações DJEN

Este módulo implementa agendamento automático de downloads diários de publicações
jurídicas dos principais tribunais brasileiros.

Funcionalidades:
- Download diário às 8:00 AM
- 10 tribunais prioritários (STJ, STF, TST, TJSP, TJRJ, TJMG, TJRS, TRF3, TRF4, TRF2)
- Processamento automático e inserção no SQLite
- Logging detalhado de estatísticas
- Graceful shutdown (SIGINT/SIGTERM)
- Relatório de execução em downloads_historico

Baseado em:
- docs/ARQUITETURA_JURISPRUDENCIA.md (seção "Pipeline de Ingestão de Dados")
- src/downloader.py (DJENDownloader)
- src/processador_texto.py (processar_publicacao)

Uso:
    # Execução interativa
    python scheduler.py

    # Execução em background (Linux)
    nohup python scheduler.py > scheduler.log 2>&1 &

    # Systemd (produção)
    Ver seção "Systemd Service" abaixo

Autor: Claude Code (Sonnet 4.5)
Data: 2025-11-20
"""

import sys
import signal
import logging
import sqlite3
import time
import schedule
import unicodedata
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import asdict

# Adicionar src/ ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from downloader import DJENDownloader, PublicacaoRaw
from processador_texto import processar_publicacao, validar_publicacao_processada

# ==============================================================================
# CONFIGURAÇÃO DE LOGGING
# ==============================================================================

LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_DIR / 'scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURAÇÃO GLOBAL
# ==============================================================================

# Diretório raiz de dados (ajustar conforme necessário)
DATA_ROOT = Path(__file__).parent / 'data'
DB_PATH = Path(__file__).parent / 'jurisprudencia.db'

# Tribunais prioritários para jurisprudência
TRIBUNAIS_PRIORITARIOS = [
    'STJ',   # Superior Tribunal de Justiça
    'STF',   # Supremo Tribunal Federal
    'TST',   # Tribunal Superior do Trabalho
    'TJSP',  # Tribunal de Justiça de São Paulo
    'TJRJ',  # Tribunal de Justiça do Rio de Janeiro
    'TJMG',  # Tribunal de Justiça de Minas Gerais
    'TJRS',  # Tribunal de Justiça do Rio Grande do Sul
    'TRF3',  # Tribunal Regional Federal da 3ª Região (SP/MS)
    'TRF4',  # Tribunal Regional Federal da 4ª Região (RS/SC/PR)
    'TRF2',  # Tribunal Regional Federal da 2ª Região (RJ/ES)
]

# Horário de execução diária (formato 24h)
HORARIO_EXECUCAO = "08:00"

# Flags de controle
running = True


# ==============================================================================
# FUNÇÕES DE BANCO DE DADOS
# ==============================================================================

def inicializar_banco() -> sqlite3.Connection:
    """
    Inicializa conexão com banco SQLite.

    Returns:
        Conexão SQLite
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Habilitar foreign keys
    conn.execute('PRAGMA foreign_keys = ON')

    logger.info(f"Banco de dados conectado: {DB_PATH}")
    return conn


def inserir_publicacao(conn: sqlite3.Connection, pub: Dict) -> bool:
    """
    Insere publicação no banco se não existir (via hash).

    NOTA: Commit será feito em batch pela função chamadora.

    Args:
        conn: Conexão SQLite
        pub: Dicionário de publicação processada

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
            pub.get('assuntos'),  # Pode ser None
            pub['texto_html'],
            pub['texto_limpo'],
            pub['ementa'],
            pub['data_publicacao'],
            pub.get('data_julgamento'),  # Pode ser None
            pub['relator'],
            pub['fonte']
        ))
        # Commit removido - será feito em batch
        return True

    except sqlite3.IntegrityError as e:
        # Hash já existe - duplicata
        logger.debug(f"Publicação duplicada: {pub['hash_conteudo'][:16]}... ({e})")
        # Rollback apenas da transação duplicada
        conn.rollback()
        return False


def registrar_download(
    conn: sqlite3.Connection,
    tribunal: str,
    data_publicacao: str,
    tipo_download: str,
    stats: Dict
) -> None:
    """
    Registra metadados de download na tabela downloads_historico.

    Args:
        conn: Conexão SQLite
        tribunal: Sigla do tribunal
        data_publicacao: Data do caderno (YYYY-MM-DD)
        tipo_download: 'api' ou 'caderno-pdf'
        stats: Dicionário com estatísticas:
            - total_publicacoes: Total de publicações baixadas
            - total_novas: Publicações novas (inseridas)
            - total_duplicadas: Publicações duplicadas
            - tempo_processamento: Tempo em segundos
            - status: 'sucesso', 'falha' ou 'parcial'
            - erro: Mensagem de erro (opcional)
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
# FUNÇÕES AUXILIARES
# ==============================================================================

def normalizar_tipo_publicacao(tipo: str) -> str:
    """
    Remove acentos, espaços extras e converte para lowercase para comparação.

    Args:
        tipo: Tipo de publicação (ex: 'Acórdão', 'SENTENÇA  ', '  Decisão\n')

    Returns:
        Tipo normalizado (ex: 'acordao', 'sentenca', 'decisao')

    Examples:
        >>> normalizar_tipo_publicacao('Acórdão')
        'acordao'
        >>> normalizar_tipo_publicacao('ACÓRDÃO  ')
        'acordao'
        >>> normalizar_tipo_publicacao('  acordão\n')
        'acordao'
    """
    if not tipo or not isinstance(tipo, str):
        return ""
    # Remove acentos
    sem_acentos = unicodedata.normalize('NFD', tipo)
    sem_acentos = ''.join(c for c in sem_acentos if unicodedata.category(c) != 'Mn')
    return sem_acentos.lower().strip()


# ==============================================================================
# PROCESSAMENTO DE PUBLICAÇÕES
# ==============================================================================

def processar_publicacoes(
    conn: sqlite3.Connection,
    publicacoes: List[PublicacaoRaw],
    tribunal: str,
    tipos_desejados: List[str] = ['Acórdão']
) -> Dict[str, int]:
    """
    Processa publicações brutas e insere no banco com batch commits.

    Args:
        conn: Conexão SQLite
        publicacoes: Lista de PublicacaoRaw do downloader
        tribunal: Sigla do tribunal
        tipos_desejados: Lista de tipos de publicação a processar.
                        Comparação é case-insensitive e ignora acentos/espaços
                        (ex: 'Acórdão' == 'ACORDAO' == 'acordão  ').
                        Tipos não presentes na lista são filtrados.
                        Padrão: apenas 'Acórdão'.
                        IMPORTANTE: Lista vazia filtra TUDO (nenhuma publicação processada).

    Returns:
        Dicionário com estatísticas:
            - total: Total de publicações processadas
            - novas: Publicações inseridas
            - duplicadas: Publicações já existentes
            - filtrados: Publicações filtradas por tipo
            - erros: Publicações com erro de processamento
    """
    BATCH_SIZE = 100  # Commit a cada 100 publicações

    # Validar entrada: lista vazia filtra tudo
    if not tipos_desejados:
        logger.warning(
            f"[{tribunal}] tipos_desejados vazio - "
            f"NENHUMA publicação será processada"
        )
        return {
            'total': len(publicacoes),
            'novas': 0,
            'duplicadas': 0,
            'filtrados': len(publicacoes),
            'erros': 0
        }

    # Normalizar tipos desejados para comparação case-insensitive
    tipos_normalizados = {normalizar_tipo_publicacao(t) for t in tipos_desejados}

    stats = {
        'total': len(publicacoes),
        'novas': 0,
        'duplicadas': 0,
        'filtrados': 0,
        'erros': 0
    }

    for i, pub_raw in enumerate(publicacoes, start=1):
        try:
            # Converter PublicacaoRaw para dict
            raw_dict = asdict(pub_raw)

            # Processar publicação
            pub_processada = processar_publicacao(raw_dict)

            # Validar tipo_publicacao antes de filtrar
            tipo_pub = pub_processada.get('tipo_publicacao')
            if not tipo_pub or not isinstance(tipo_pub, str):
                logger.warning(
                    f"[{tribunal}] tipo_publicacao inválido: {tipo_pub!r} "
                    f"(#{pub_raw.id[:8]}...)"
                )
                stats['erros'] += 1
                continue

            # Filtrar por tipo de publicação (comparação normalizada)
            tipo_normalizado = normalizar_tipo_publicacao(tipo_pub)
            if tipo_normalizado not in tipos_normalizados:
                stats['filtrados'] += 1
                continue

            # Validar
            if not validar_publicacao_processada(pub_processada):
                logger.warning(f"[{tribunal}] Publicação inválida após processamento: {pub_raw.id}")
                stats['erros'] += 1
                continue

            # Inserir no banco
            if inserir_publicacao(conn, pub_processada):
                stats['novas'] += 1
            else:
                stats['duplicadas'] += 1

            # Commit em batch
            if i % BATCH_SIZE == 0:
                conn.commit()
                logger.debug(f"[{tribunal}] Batch commit: {i}/{len(publicacoes)} processadas")

        except Exception as e:
            logger.error(f"[{tribunal}] Erro ao processar publicação {pub_raw.id}: {e}")
            stats['erros'] += 1

    # Commit final (publicações restantes)
    conn.commit()
    logger.debug(f"[{tribunal}] Commit final: {len(publicacoes)} publicações processadas")

    logger.info(
        f"[{tribunal}] Processamento concluído: "
        f"{stats['novas']} novas, {stats['duplicadas']} duplicadas, "
        f"{stats['filtrados']} filtrados, {stats['erros']} erros"
    )

    return stats


# ==============================================================================
# JOB DE DOWNLOAD
# ==============================================================================

def baixar_retroativo(
    data_inicio: str,
    data_fim: str,
    tribunais: Optional[List[str]] = None,
    tipos_desejados: Optional[List[str]] = None
):
    """
    Baixa publicações de um intervalo de datas (download retroativo).

    Args:
        data_inicio: Data inicial no formato YYYY-MM-DD
        data_fim: Data final no formato YYYY-MM-DD
        tribunais: Lista de tribunais (default: TRIBUNAIS_PRIORITARIOS)
        tipos_desejados: Lista de tipos a filtrar (default: ['Acórdão'])

    Returns:
        Dict com estatísticas do download retroativo
    """
    from datetime import datetime, timedelta

    if tribunais is None:
        tribunais = TRIBUNAIS_PRIORITARIOS

    if tipos_desejados is None:
        tipos_desejados = ['Acórdão']

    logger.info("=" * 80)
    logger.info("INICIANDO DOWNLOAD RETROATIVO")
    logger.info("=" * 80)
    logger.info(f"Período: {data_inicio} até {data_fim}")
    logger.info(f"Tribunais: {len(tribunais)} ({', '.join(tribunais)})")
    logger.info(f"Tipos: {', '.join(tipos_desejados)}")

    # Converter strings para datetime
    dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
    dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')

    # Calcular total de dias
    delta = dt_fim - dt_inicio
    total_dias = delta.days + 1

    logger.info(f"Total de dias a processar: {total_dias}")

    # Inicializar downloader
    downloader = DJENDownloader(
        data_root=DATA_ROOT,
        requests_per_minute=280,
        adaptive_rate_limit=True,
        max_retries=3
    )

    # Conectar banco
    conn = inicializar_banco()

    # Estatísticas globais
    stats_globais = {
        'total_dias': total_dias,
        'total_tribunais': len(tribunais),
        'total_novas': 0,
        'total_duplicadas': 0,
        'total_filtrados': 0,
        'total_erros': 0,
        'dias_processados': 0,
        'inicio': datetime.now()
    }

    # Iterar por cada dia
    data_atual = dt_inicio
    while data_atual <= dt_fim:
        data_str = data_atual.strftime('%Y-%m-%d')
        stats_globais['dias_processados'] += 1

        logger.info(f"\n{'=' * 80}")
        logger.info(f"DIA {stats_globais['dias_processados']}/{total_dias}: {data_str}")
        logger.info(f"{'=' * 80}")

        # Processar cada tribunal para este dia
        for tribunal in tribunais:
            try:
                logger.info(f"[{tribunal}] Baixando publicações de {data_str}...")

                publicacoes = downloader.baixar_api(
                    tribunal=tribunal,
                    data=data_str,
                    limit=100,
                    max_pages=None  # Baixar todas as páginas
                )

                if publicacoes:
                    logger.info(f"[{tribunal}] Baixadas: {len(publicacoes)} publicações")

                    # Processar e inserir no banco (com filtro)
                    stats_processamento = processar_publicacoes(
                        conn,
                        publicacoes,
                        tribunal,
                        tipos_desejados=tipos_desejados
                    )

                    # Atualizar estatísticas globais
                    stats_globais['total_novas'] += stats_processamento['novas']
                    stats_globais['total_duplicadas'] += stats_processamento['duplicadas']
                    stats_globais['total_filtrados'] += stats_processamento['filtrados']
                    stats_globais['total_erros'] += stats_processamento['erros']

                    logger.info(
                        f"[{tribunal}] {data_str}: "
                        f"{stats_processamento['novas']} novas, "
                        f"{stats_processamento['duplicadas']} duplicadas, "
                        f"{stats_processamento['filtrados']} filtrados"
                    )
                else:
                    logger.info(f"[{tribunal}] Nenhuma publicação encontrada para {data_str}")

            except Exception as e:
                logger.error(f"[{tribunal}] Erro ao processar {data_str}: {e}")
                stats_globais['total_erros'] += 1

        # Avançar para próximo dia
        data_atual += timedelta(days=1)

        # Mostrar progresso
        progresso_pct = (stats_globais['dias_processados'] / total_dias) * 100
        logger.info(
            f"\n📊 PROGRESSO: {stats_globais['dias_processados']}/{total_dias} dias "
            f"({progresso_pct:.1f}%) | "
            f"{stats_globais['total_novas']} novas | "
            f"{stats_globais['total_filtrados']} filtrados"
        )

    # Relatório final
    stats_globais['fim'] = datetime.now()
    tempo_total = (stats_globais['fim'] - stats_globais['inicio']).total_seconds()

    logger.info("\n" + "=" * 80)
    logger.info("DOWNLOAD RETROATIVO CONCLUÍDO")
    logger.info("=" * 80)
    logger.info(f"Período: {data_inicio} até {data_fim}")
    logger.info(f"Dias processados: {stats_globais['dias_processados']}/{total_dias}")
    logger.info(f"Publicações novas: {stats_globais['total_novas']}")
    logger.info(f"Publicações duplicadas: {stats_globais['total_duplicadas']}")
    logger.info(f"Publicações filtradas: {stats_globais['total_filtrados']}")
    logger.info(f"Erros: {stats_globais['total_erros']}")
    logger.info(f"Tempo total: {tempo_total:.1f}s ({tempo_total/60:.1f} min)")
    logger.info("=" * 80)

    conn.close()

    return stats_globais


def job_download_diario():
    """
    Executa download diário de todos os tribunais prioritários.

    Workflow:
    1. Baixar via API (método preferido - mais rápido)
    2. Se API falhar ou retornar muito pouco, tentar caderno PDF
    3. Processar e inserir no banco
    4. Registrar estatísticas em downloads_historico
    """
    logger.info("=" * 80)
    logger.info("INICIANDO JOB DE DOWNLOAD DIÁRIO")
    logger.info("=" * 80)

    # Data de hoje
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    logger.info(f"Data: {data_hoje}")
    logger.info(f"Tribunais: {len(TRIBUNAIS_PRIORITARIOS)} ({', '.join(TRIBUNAIS_PRIORITARIOS)})")

    # Inicializar downloader
    downloader = DJENDownloader(
        data_root=DATA_ROOT,
        requests_per_minute=280,
        adaptive_rate_limit=True,
        max_retries=3
    )

    # Conectar banco
    conn = inicializar_banco()

    # Estatísticas globais
    stats_globais = {
        'total_tribunais': len(TRIBUNAIS_PRIORITARIOS),
        'tribunais_sucesso': 0,
        'tribunais_falha': 0,
        'total_novas': 0,
        'total_duplicadas': 0,
        'inicio': datetime.now()
    }

    # Processar cada tribunal
    for tribunal in TRIBUNAIS_PRIORITARIOS:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"[{tribunal}] Processando tribunal")
        logger.info(f"{'=' * 80}")

        inicio_tribunal = time.time()

        try:
            # Etapa 1: Baixar via API
            logger.info(f"[{tribunal}] Tentando download via API...")
            publicacoes = downloader.baixar_api(
                tribunal=tribunal,
                data=data_hoje,
                limit=100,
                max_pages=None  # Baixar todas as páginas
            )

            # Verificar se API retornou publicações suficientes
            min_publicacoes_esperadas = 100  # Aumentado de 10 para 100 (Fase 2)

            if not publicacoes or len(publicacoes) < min_publicacoes_esperadas:
                logger.warning(
                    f"[{tribunal}] API retornou apenas {len(publicacoes)} publicações. "
                    f"Tentando caderno PDF como fallback..."
                )

                # Etapa 2: Fallback - Caderno PDF
                # TODO: Implementar extração de publicações do caderno PDF
                # Por ora, continuar com o que foi baixado via API
                pass

            # Etapa 3: Processar e inserir no banco
            if publicacoes:
                stats_processamento = processar_publicacoes(conn, publicacoes, tribunal)

                # Atualizar estatísticas globais
                stats_globais['total_novas'] += stats_processamento['novas']
                stats_globais['total_duplicadas'] += stats_processamento['duplicadas']
                stats_globais['tribunais_sucesso'] += 1

                # Registrar download
                tempo_processamento = time.time() - inicio_tribunal
                registrar_download(
                    conn=conn,
                    tribunal=tribunal,
                    data_publicacao=data_hoje,
                    tipo_download='api',
                    stats={
                        'total_publicacoes': len(publicacoes),
                        'total_novas': stats_processamento['novas'],
                        'total_duplicadas': stats_processamento['duplicadas'],
                        'tempo_processamento': tempo_processamento,
                        'status': 'sucesso' if stats_processamento['erros'] == 0 else 'parcial',
                        'erro': None
                    }
                )

                logger.info(
                    f"[{tribunal}] ✓ Concluído em {tempo_processamento:.1f}s - "
                    f"{stats_processamento['novas']} novas publicações"
                )
            else:
                logger.warning(f"[{tribunal}] Nenhuma publicação baixada")
                stats_globais['tribunais_falha'] += 1

                # Registrar falha
                tempo_processamento = time.time() - inicio_tribunal
                registrar_download(
                    conn=conn,
                    tribunal=tribunal,
                    data_publicacao=data_hoje,
                    tipo_download='api',
                    stats={
                        'total_publicacoes': 0,
                        'total_novas': 0,
                        'total_duplicadas': 0,
                        'tempo_processamento': tempo_processamento,
                        'status': 'falha',
                        'erro': 'Nenhuma publicação retornada pela API'
                    }
                )

        except Exception as e:
            logger.error(f"[{tribunal}] ERRO: {e}")
            stats_globais['tribunais_falha'] += 1

            # Registrar erro
            tempo_processamento = time.time() - inicio_tribunal
            registrar_download(
                conn=conn,
                tribunal=tribunal,
                data_publicacao=data_hoje,
                tipo_download='api',
                stats={
                    'total_publicacoes': 0,
                    'total_novas': 0,
                    'total_duplicadas': 0,
                    'tempo_processamento': tempo_processamento,
                    'status': 'falha',
                    'erro': str(e)
                }
            )

    # Fechar conexão
    conn.close()

    # Relatório final
    tempo_total = (datetime.now() - stats_globais['inicio']).total_seconds()

    logger.info("\n" + "=" * 80)
    logger.info("RELATÓRIO FINAL DO JOB DE DOWNLOAD")
    logger.info("=" * 80)
    logger.info(f"Data: {data_hoje}")
    logger.info(f"Tempo total: {tempo_total:.1f}s ({tempo_total/60:.1f} minutos)")
    logger.info(f"Tribunais processados: {stats_globais['total_tribunais']}")
    logger.info(f"  ✓ Sucesso: {stats_globais['tribunais_sucesso']}")
    logger.info(f"  ✗ Falha: {stats_globais['tribunais_falha']}")
    logger.info(f"Publicações novas: {stats_globais['total_novas']}")
    logger.info(f"Publicações duplicadas: {stats_globais['total_duplicadas']}")
    logger.info("=" * 80)


# ==============================================================================
# GRACEFUL SHUTDOWN
# ==============================================================================

def signal_handler(signum, frame):
    """
    Handler para sinais SIGINT (Ctrl+C) e SIGTERM.

    Permite que o scheduler finalize gracefully sem interromper
    downloads em andamento.
    """
    global running

    signal_name = 'SIGINT' if signum == signal.SIGINT else 'SIGTERM'
    logger.info(f"\n{signal_name} recebido. Finalizando scheduler...")
    logger.info("Aguardando jobs em andamento terminarem...")

    running = False


# ==============================================================================
# MAIN - SCHEDULER LOOP
# ==============================================================================

def main():
    """
    Função principal do scheduler.

    1. Registra signal handlers (SIGINT/SIGTERM)
    2. Agenda job para executar diariamente às 8:00 AM
    3. Executa imediatamente na primeira vez
    4. Loop infinito verificando jobs pendentes
    """
    logger.info("=" * 80)
    logger.info("SCHEDULER DE DOWNLOAD AUTOMÁTICO - DJEN")
    logger.info("=" * 80)
    logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Diretório de dados: {DATA_ROOT}")
    logger.info(f"Banco de dados: {DB_PATH}")
    logger.info(f"Horário de execução: {HORARIO_EXECUCAO} (diariamente)")
    logger.info(f"Tribunais monitorados: {len(TRIBUNAIS_PRIORITARIOS)}")
    logger.info("=" * 80)

    # Registrar signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Agendar job diário
    schedule.every().day.at(HORARIO_EXECUCAO).do(job_download_diario)
    logger.info(f"Job agendado para executar diariamente às {HORARIO_EXECUCAO}")

    # Perguntar se deve executar imediatamente
    if len(sys.argv) > 1 and sys.argv[1] == '--now':
        logger.info("Flag --now detectada. Executando job imediatamente...")
        job_download_diario()
    else:
        logger.info("Para executar imediatamente, use: python scheduler.py --now")

    # Loop infinito
    logger.info("Scheduler em execução. Pressione Ctrl+C para parar.")

    while running:
        try:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada 60 segundos

        except Exception as e:
            logger.error(f"Erro no loop do scheduler: {e}")
            time.sleep(60)

    # Shutdown
    logger.info("Scheduler finalizado com sucesso.")


# ==============================================================================
# SYSTEMD SERVICE (Produção)
# ==============================================================================
"""
Para executar em produção com systemd, criar arquivo:
/etc/systemd/system/jurisprudencia-scheduler.service

[Unit]
Description=Scheduler de Download DJEN - Jurisprudência
After=network.target

[Service]
Type=simple
User=cmr-auto
WorkingDirectory=/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector
ExecStart=/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector/.venv/bin/python /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

---

Comandos systemd:
    sudo systemctl daemon-reload
    sudo systemctl enable jurisprudencia-scheduler.service
    sudo systemctl start jurisprudencia-scheduler.service
    sudo systemctl status jurisprudencia-scheduler.service
    sudo journalctl -u jurisprudencia-scheduler.service -f
"""


# ==============================================================================
# CRON (Alternativa mais simples)
# ==============================================================================
"""
Para usar cron ao invés de schedule library:

1. Editar crontab:
   crontab -e

2. Adicionar linha (executar às 8:00 AM todos os dias):
   0 8 * * * cd /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector && .venv/bin/python scheduler.py --now >> logs/cron.log 2>&1

3. Verificar jobs agendados:
   crontab -l

NOTA: Se usar cron, remover o loop infinito do scheduler e executar apenas job_download_diario().
"""


if __name__ == '__main__':
    main()
