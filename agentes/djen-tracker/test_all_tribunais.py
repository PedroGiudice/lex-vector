#!/usr/bin/env python3
"""
Test Script - Download de TODOS os tribunais brasileiros

Testa o downloader com 5 tribunais diferentes para validar:
1. Lista completa de tribunais funciona
2. Rate limiting está adequado
3. Download funciona para diferentes tipos de tribunais
4. Estatísticas estão corretas

Modo de uso:
    python test_all_tribunais.py
"""
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Usar import relativo para src
from src import ContinuousDownloader
from src.tribunais import get_all_tribunais, get_stats


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_all_tribunais.log')
    ]
)
logger = logging.getLogger(__name__)


def load_test_config():
    """Carrega config de teste (5 tribunais)."""
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Override para teste com 5 tribunais de tipos diferentes
    config['tribunais']['modo'] = 'prioritarios'
    config['tribunais']['prioritarios'] = [
        'STF',    # Superior
        'TJSP',   # Estadual
        'TRF3',   # Federal
        'TRT2',   # Trabalho
        'TJMSP'   # Militar
    ]

    # Ajustar rate limiting para teste mais rápido
    config['rate_limiting']['delay_between_requests_seconds'] = 1

    # Auto-detect data root
    if config['paths']['data_root'] == 'auto-detect':
        # WSL2
        config['paths']['data_root'] = Path.home() / 'claude-work' / 'data' / 'djen-tracker'

    return config


def test_modo_all():
    """Testa modo 'all' (todos os tribunais)."""
    logger.info("\n" + "="*70)
    logger.info("TESTE 1: Modo ALL (lista completa)")
    logger.info("="*70)

    config = load_test_config()
    config['tribunais']['modo'] = 'all'

    downloader = ContinuousDownloader(config)

    # Verificar que lista tem 65 tribunais
    assert len(downloader.tribunais_ativos) == 65, \
        f"Esperado 65 tribunais, encontrado {len(downloader.tribunais_ativos)}"

    logger.info(f"✓ Lista completa: {len(downloader.tribunais_ativos)} tribunais")

    # Mostrar estatísticas
    stats = get_stats()
    logger.info(f"✓ Estatísticas: {stats}")


def test_modo_prioritarios():
    """Testa modo 'prioritarios' (5 tribunais de tipos diferentes)."""
    logger.info("\n" + "="*70)
    logger.info("TESTE 2: Modo PRIORITARIOS (5 tribunais)")
    logger.info("="*70)

    config = load_test_config()
    downloader = ContinuousDownloader(config)

    # Verificar que lista tem 5 tribunais
    assert len(downloader.tribunais_ativos) == 5, \
        f"Esperado 5 tribunais, encontrado {len(downloader.tribunais_ativos)}"

    logger.info(f"✓ Lista prioritários: {downloader.tribunais_ativos}")

    # Verificar que são os esperados
    esperados = {'STF', 'TJSP', 'TRF3', 'TRT2', 'TJMSP'}
    ativos = set(downloader.tribunais_ativos)
    assert ativos == esperados, f"Lista diferente: {ativos} != {esperados}"

    logger.info(f"✓ Tribunais corretos: {', '.join(downloader.tribunais_ativos)}")


def test_download_real():
    """Testa download real de 5 tribunais."""
    logger.info("\n" + "="*70)
    logger.info("TESTE 3: Download REAL (5 tribunais)")
    logger.info("="*70)

    config = load_test_config()
    downloader = ContinuousDownloader(config)

    # Usar data recente (ontem ou hoje)
    data_teste = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    logger.info(f"Data de teste: {data_teste}")
    logger.info(f"Tribunais: {', '.join(downloader.tribunais_ativos)}")

    # Executar um ciclo
    resultado = downloader.run_once(data=data_teste)

    logger.info(f"\nResultado do ciclo:")
    logger.info(f"  Total: {resultado['total']}")
    logger.info(f"  Sucessos: {resultado['sucessos']}")
    logger.info(f"  Falhas: {resultado['falhas']}")
    logger.info(f"  Duplicatas: {resultado['duplicatas']}")

    # Validar que pelo menos tentou baixar
    assert resultado['total'] >= 5, \
        f"Esperado pelo menos 5 tentativas, teve {resultado['total']}"

    logger.info(f"✓ Download executado: {resultado['total']} tentativas")

    # Mostrar estatísticas do rate limiter
    rate_stats = downloader.rate_limiter.get_stats()
    logger.info(f"\nRate Limiter:")
    logger.info(f"  Requisições último minuto: {rate_stats['requests_last_minute']}")
    logger.info(f"  Intervalo médio: {rate_stats['average_interval']}s")
    logger.info(f"  Backoff level: {rate_stats['backoff_level']}")


def test_tribunais_module():
    """Testa módulo tribunais.py."""
    logger.info("\n" + "="*70)
    logger.info("TESTE 4: Módulo tribunais.py")
    logger.info("="*70)

    from src.tribunais import (
        get_all_tribunais,
        get_siglas,
        get_count,
        get_stats,
        validate_sigla,
        get_tribunais_prioritarios
    )

    # Total
    assert get_count() == 65, f"Esperado 65, encontrado {get_count()}"
    logger.info(f"✓ Total: {get_count()} tribunais")

    # Siglas
    siglas = get_siglas()
    assert len(siglas) == 65, f"Esperado 65 siglas, encontrado {len(siglas)}"
    logger.info(f"✓ Siglas: {len(siglas)} válidas")

    # Validação
    assert validate_sigla('STF') == True
    assert validate_sigla('INVALID') == False
    logger.info(f"✓ Validação funcionando")

    # Prioritários
    prioritarios = get_tribunais_prioritarios()
    assert len(prioritarios) > 0, "Lista de prioritários vazia"
    logger.info(f"✓ Prioritários: {len(prioritarios)} tribunais")

    # Estatísticas
    stats = get_stats()
    assert stats['total'] == 65
    assert stats['superiores'] == 5
    assert stats['estaduais'] == 27
    assert stats['federais'] == 6
    assert stats['trabalho'] == 24
    assert stats['militares'] == 3
    logger.info(f"✓ Estatísticas corretas: {stats}")


def main():
    """Executa todos os testes."""
    logger.info("\n" + "#"*70)
    logger.info("TESTE: Download de TODOS os tribunais brasileiros")
    logger.info("#"*70)

    try:
        # Teste 1: Modo all
        test_modo_all()

        # Teste 2: Modo prioritarios
        test_modo_prioritarios()

        # Teste 3: Download real
        test_download_real()

        # Teste 4: Módulo tribunais
        test_tribunais_module()

        logger.info("\n" + "#"*70)
        logger.info("✓ TODOS OS TESTES PASSARAM")
        logger.info("#"*70)

        return 0

    except AssertionError as e:
        logger.error(f"\n✗ TESTE FALHOU: {e}")
        return 1

    except Exception as e:
        logger.error(f"\n✗ ERRO INESPERADO: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
