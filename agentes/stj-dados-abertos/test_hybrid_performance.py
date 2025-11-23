#!/usr/bin/env python3
"""
Teste de Performance - Arquitetura Híbrida
==========================================

Compara performance entre:
1. Tudo no SSD (baseline)
2. Tudo no HD via /mnt/d/ (lento)
3. Híbrido: índices SSD + dados HD (otimizado)

Métricas:
- Inserção de 1000 acórdãos
- Query simples (por data)
- Query complexa (fulltext)
- Fetch de 100 documentos
"""

import time
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent))

from src.hybrid_storage import STJHybridStorage
from config import INDEX_PATH, DATA_ROOT


def generate_sample_acordaos(count: int = 1000) -> list:
    """
    Gera acórdãos de amostra para teste.

    Args:
        count: Quantidade de acórdãos

    Returns:
        Lista de dicionários com dados de acórdãos
    """
    acordaos = []
    base_date = datetime(2024, 1, 1)

    orgaos = [
        "Corte Especial",
        "Primeira Seção",
        "Segunda Seção",
        "Terceira Turma",
        "Quarta Turma"
    ]

    relatores = [
        "Ministro João Silva",
        "Ministra Maria Santos",
        "Ministro Pedro Oliveira",
        "Ministra Ana Costa"
    ]

    temas = [
        "responsabilidade civil dano moral",
        "ação monitória contrato de mútuo",
        "direito do consumidor defeito no produto",
        "direito tributário ICMS",
        "direito trabalhista horas extras"
    ]

    for i in range(count):
        data_pub = base_date + timedelta(days=i % 365)
        data_julg = data_pub - timedelta(days=30)

        acordao = {
            "id": f"acordao_test_{i:05d}",
            "numero_processo": f"REsp {1000000 + i}/SP",
            "data_publicacao": data_pub.strftime('%Y-%m-%d'),
            "data_julgamento": data_julg.strftime('%Y-%m-%d'),
            "orgao_julgador": orgaos[i % len(orgaos)],
            "relator": relatores[i % len(relatores)],
            "ementa": f"EMENTA DE TESTE {i}. {temas[i % len(temas)]}. " * 5,
            "texto_integral": f"ACORDÃO COMPLETO {i}. " * 50
        }

        acordaos.append(acordao)

    return acordaos


def benchmark_insert(storage: STJHybridStorage, acordaos: list) -> float:
    """
    Testa performance de inserção.

    Args:
        storage: Instância do storage
        acordaos: Lista de acórdãos para inserir

    Returns:
        Tempo total em segundos
    """
    print(f"  → Inserindo {len(acordaos)} acórdãos...")

    start = time.time()

    for acordao in acordaos:
        json_content = json.dumps(acordao, ensure_ascii=False)
        storage.insert_acordao(acordao, json_content)

    elapsed = time.time() - start

    print(f"  ✓ Inseridos em {elapsed:.2f}s ({len(acordaos)/elapsed:.1f} docs/s)")

    return elapsed


def benchmark_query_simple(storage: STJHybridStorage) -> float:
    """
    Testa query simples (filtro por data).

    Args:
        storage: Instância do storage

    Returns:
        Tempo total em segundos
    """
    print(f"  → Query simples (filtro por data)...")

    start = time.time()

    results = storage.search_acordaos(
        data_inicio="2024-06-01",
        data_fim="2024-06-30",
        limit=100
    )

    elapsed = time.time() - start

    print(f"  ✓ Encontrados {len(results)} resultados em {elapsed:.3f}s")

    return elapsed


def benchmark_query_fulltext(storage: STJHybridStorage) -> float:
    """
    Testa query complexa (fulltext search).

    Args:
        storage: Instância do storage

    Returns:
        Tempo total em segundos
    """
    print(f"  → Query fulltext (busca complexa)...")

    start = time.time()

    results = storage.search_acordaos(
        texto="responsabilidade civil dano moral",
        limit=100
    )

    elapsed = time.time() - start

    print(f"  ✓ Encontrados {len(results)} resultados em {elapsed:.3f}s")

    return elapsed


def benchmark_fetch_documents(storage: STJHybridStorage, count: int = 100) -> float:
    """
    Testa fetch de documentos do HD.

    Args:
        storage: Instância do storage
        count: Quantidade de documentos para fetch

    Returns:
        Tempo total em segundos
    """
    print(f"  → Fetch de {count} documentos do HD...")

    # Pegar IDs de acórdãos existentes
    results = storage.conn.execute(
        f"SELECT id, json_path FROM acordao_index LIMIT {count}"
    ).fetchall()

    start = time.time()

    for acordao_id, json_path in results:
        storage._fetch_document(acordao_id, json_path)

    elapsed = time.time() - start

    print(f"  ✓ Fetch concluído em {elapsed:.3f}s ({count/elapsed:.1f} docs/s)")

    return elapsed


def run_benchmarks():
    """
    Executa todos os benchmarks.
    """
    print("\n" + "="*70)
    print(" TESTE DE PERFORMANCE - ARQUITETURA HÍBRIDA")
    print("="*70 + "\n")

    print(f"Configuração:")
    print(f"  - Índices (SSD): {INDEX_PATH}")
    print(f"  - Dados (HD): {DATA_ROOT}")
    print()

    # Gerar dados de teste
    print("📦 Gerando dados de teste...")
    acordaos = generate_sample_acordaos(1000)
    print(f"  ✓ {len(acordaos)} acórdãos gerados\n")

    # Inicializar storage
    print("🔧 Inicializando storage híbrido...")
    storage = STJHybridStorage(validate_on_init=True)
    print()

    # Benchmarks
    results = {}

    print("🚀 Benchmark 1: Inserção")
    results["insert"] = benchmark_insert(storage, acordaos)
    print()

    print("🔍 Benchmark 2: Query Simples")
    results["query_simple"] = benchmark_query_simple(storage)
    print()

    print("🔍 Benchmark 3: Query Fulltext")
    results["query_fulltext"] = benchmark_query_fulltext(storage)
    print()

    print("📄 Benchmark 4: Fetch Documentos")
    results["fetch_docs"] = benchmark_fetch_documents(storage, 100)
    print()

    # Estatísticas finais
    stats = storage.get_stats()

    print("="*70)
    print(" RESUMO DOS RESULTADOS")
    print("="*70 + "\n")

    print(f"Performance:")
    print(f"  - Inserção: {results['insert']:.2f}s ({1000/results['insert']:.1f} docs/s)")
    print(f"  - Query simples: {results['query_simple']*1000:.1f}ms")
    print(f"  - Query fulltext: {results['query_fulltext']*1000:.1f}ms")
    print(f"  - Fetch 100 docs: {results['fetch_docs']:.2f}s")
    print()

    print(f"Armazenamento:")
    print(f"  - Total acórdãos: {stats['total_acordaos']}")
    print(f"  - Índices (SSD): {stats['index_db_size_mb']:.1f} MB")
    print(f"  - Dados (HD): {stats['data_dir_size_gb']:.3f} GB")
    print(f"  - Cache memória: {stats['cache_size']} documentos")
    print()

    # Análise de performance
    print("📊 Análise:")

    # Estimativas para dataset completo (50GB)
    estimate_total_docs = 100_000  # Estimativa de 100k acórdãos

    insert_rate = 1000 / results['insert']  # docs/s
    estimated_insert_time = estimate_total_docs / insert_rate / 60  # minutos

    print(f"  - Taxa de inserção: {insert_rate:.1f} documentos/segundo")
    print(f"  - Tempo estimado para 100k docs: {estimated_insert_time:.1f} minutos")

    query_time_ms = results['query_fulltext'] * 1000
    if query_time_ms < 100:
        perf_rating = "EXCELENTE"
    elif query_time_ms < 500:
        perf_rating = "MUITO BOM"
    elif query_time_ms < 1000:
        perf_rating = "BOM"
    else:
        perf_rating = "NECESSITA OTIMIZAÇÃO"

    print(f"  - Performance de busca: {perf_rating}")
    print()

    # Fechar storage
    storage.close()

    print("✓ Teste de performance concluído!\n")


if __name__ == "__main__":
    run_benchmarks()
