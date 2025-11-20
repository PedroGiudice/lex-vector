#!/usr/bin/env python3
"""
Teste de Performance do Sistema RAG

Mede tempo de processamento para:
1. Geração de embeddings (single + batch)
2. Chunking de textos longos
3. Busca semântica
4. Operações de serialização/deserialização

Uso:
    python teste_performance_rag.py --num-textos 100 --modelo neuralmind/bert-base-portuguese-cased
"""

import sys
import time
import logging
from pathlib import Path
from typing import List, Dict
import argparse
import numpy as np
from dataclasses import dataclass

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rag import Embedder, Chunker

# Configurar logging
logging.basicConfig(
    level=logging.WARNING,  # Suprimir logs detalhados durante benchmark
    format='%(asctime)s - %(levelname)s - %(message)s'
)


@dataclass
class BenchmarkResult:
    """Resultado de um benchmark."""
    nome: str
    tempo_total_s: float
    num_operacoes: int
    tempo_medio_s: float
    throughput: float  # operações/segundo
    metadata: Dict = None


def gerar_texto_exemplo(tamanho_chars: int = 2000) -> str:
    """
    Gera texto de exemplo simulando publicação jurídica.

    Args:
        tamanho_chars: Tamanho aproximado do texto

    Returns:
        Texto simulado
    """
    template = """
    APELAÇÃO CÍVEL. DIREITO CIVIL. RESPONSABILIDADE CIVIL. DANOS MORAIS E MATERIAIS.

    Trata-se de recurso de apelação interposto contra sentença que julgou procedente
    pedido de indenização por danos morais e materiais decorrentes de acidente de trânsito.

    A parte autora alega ter sofrido prejuízos materiais no valor de R$ 15.000,00 e
    danos morais em razão de lesões corporais causadas pelo acidente.

    O réu sustenta ausência de culpa e inexistência de nexo causal entre sua conduta
    e os danos alegados pela parte autora.

    A prova pericial constatou lesões compatíveis com o acidente, restando demonstrado
    o nexo causal e a responsabilidade do réu pelo evento danoso.

    Ante o exposto, NEGO PROVIMENTO ao recurso, mantendo a sentença por seus próprios
    fundamentos. Condenação em honorários recursais.
    """

    # Repetir template até atingir tamanho desejado
    repeticoes = (tamanho_chars // len(template)) + 1
    texto = template * repeticoes

    return texto[:tamanho_chars]


def benchmark_encoding_single(embedder: Embedder, num_textos: int) -> BenchmarkResult:
    """
    Benchmark: encoding de textos individuais (chamadas sequenciais).

    Args:
        embedder: Instância do Embedder
        num_textos: Número de textos para processar

    Returns:
        BenchmarkResult com métricas
    """
    print(f"\n[1/6] Benchmark: Encoding Single ({num_textos} textos)...")

    textos = [gerar_texto_exemplo(2000) for _ in range(num_textos)]

    start_time = time.time()

    for texto in textos:
        embedder.encode(texto, normalizar=True, mostrar_tempo=False)

    elapsed = time.time() - start_time

    return BenchmarkResult(
        nome="Encoding Single",
        tempo_total_s=elapsed,
        num_operacoes=num_textos,
        tempo_medio_s=elapsed / num_textos,
        throughput=num_textos / elapsed,
        metadata={"tamanho_texto_chars": 2000}
    )


def benchmark_encoding_batch(embedder: Embedder, num_textos: int) -> BenchmarkResult:
    """
    Benchmark: encoding de textos em batch.

    Args:
        embedder: Instância do Embedder
        num_textos: Número de textos para processar

    Returns:
        BenchmarkResult com métricas
    """
    print(f"[2/6] Benchmark: Encoding Batch ({num_textos} textos)...")

    textos = [gerar_texto_exemplo(2000) for _ in range(num_textos)]

    start_time = time.time()

    embedder.encode_batch(textos, batch_size=32, normalizar=True, mostrar_progresso=False)

    elapsed = time.time() - start_time

    return BenchmarkResult(
        nome="Encoding Batch",
        tempo_total_s=elapsed,
        num_operacoes=num_textos,
        tempo_medio_s=elapsed / num_textos,
        throughput=num_textos / elapsed,
        metadata={"tamanho_texto_chars": 2000, "batch_size": 32}
    )


def benchmark_chunking(chunker: Chunker, num_textos: int) -> BenchmarkResult:
    """
    Benchmark: chunking de textos longos.

    Args:
        chunker: Instância do Chunker
        num_textos: Número de textos para processar

    Returns:
        BenchmarkResult com métricas
    """
    print(f"[3/6] Benchmark: Chunking ({num_textos} textos)...")

    textos = [gerar_texto_exemplo(10000) for _ in range(num_textos)]  # Textos longos

    start_time = time.time()

    total_chunks = 0
    for texto in textos:
        chunks = chunker.dividir_texto(texto, estrategia="paragrafo")
        total_chunks += len(chunks)

    elapsed = time.time() - start_time

    return BenchmarkResult(
        nome="Chunking",
        tempo_total_s=elapsed,
        num_operacoes=num_textos,
        tempo_medio_s=elapsed / num_textos,
        throughput=num_textos / elapsed,
        metadata={
            "tamanho_texto_chars": 10000,
            "total_chunks_gerados": total_chunks,
            "chunks_por_texto": total_chunks / num_textos
        }
    )


def benchmark_serialization(embedder: Embedder, num_embeddings: int) -> BenchmarkResult:
    """
    Benchmark: serialização e deserialização de embeddings.

    Args:
        embedder: Instância do Embedder
        num_embeddings: Número de embeddings para processar

    Returns:
        BenchmarkResult com métricas
    """
    print(f"[4/6] Benchmark: Serialização ({num_embeddings} embeddings)...")

    # Gerar embeddings
    embeddings = []
    for _ in range(num_embeddings):
        emb = np.random.rand(embedder.dimensao).astype(np.float32)
        emb = emb / np.linalg.norm(emb)
        embeddings.append(emb)

    # Serializar
    start_time = time.time()

    blobs = [embedder.serializar_embedding(emb) for emb in embeddings]

    serialize_time = time.time() - start_time

    # Desserializar
    start_time = time.time()

    embeddings_restaurados = [
        Embedder.desserializar_embedding(blob, embedder.dimensao)
        for blob in blobs
    ]

    deserialize_time = time.time() - start_time

    total_time = serialize_time + deserialize_time

    return BenchmarkResult(
        nome="Serialização + Desserialização",
        tempo_total_s=total_time,
        num_operacoes=num_embeddings * 2,  # serialize + deserialize
        tempo_medio_s=total_time / (num_embeddings * 2),
        throughput=(num_embeddings * 2) / total_time,
        metadata={
            "serialize_time_s": serialize_time,
            "deserialize_time_s": deserialize_time,
            "tamanho_blob_bytes": len(blobs[0])
        }
    )


def benchmark_cosine_similarity(embedder: Embedder, num_comparacoes: int) -> BenchmarkResult:
    """
    Benchmark: cálculo de similaridade de cosseno.

    Args:
        embedder: Instância do Embedder
        num_comparacoes: Número de comparações para realizar

    Returns:
        BenchmarkResult com métricas
    """
    print(f"[5/6] Benchmark: Similaridade de Cosseno ({num_comparacoes} comparações)...")

    # Gerar embeddings
    query_embedding = np.random.rand(embedder.dimensao).astype(np.float32)
    query_embedding = query_embedding / np.linalg.norm(query_embedding)

    db_embeddings = []
    for _ in range(num_comparacoes):
        emb = np.random.rand(embedder.dimensao).astype(np.float32)
        emb = emb / np.linalg.norm(emb)
        db_embeddings.append(emb)

    # Calcular similaridade
    start_time = time.time()

    for db_emb in db_embeddings:
        _ = np.dot(query_embedding, db_emb)

    elapsed = time.time() - start_time

    return BenchmarkResult(
        nome="Similaridade de Cosseno",
        tempo_total_s=elapsed,
        num_operacoes=num_comparacoes,
        tempo_medio_s=elapsed / num_comparacoes,
        throughput=num_comparacoes / elapsed,
        metadata={"dimensao": embedder.dimensao}
    )


def benchmark_end_to_end(embedder: Embedder, chunker: Chunker, num_publicacoes: int) -> BenchmarkResult:
    """
    Benchmark: processamento end-to-end (chunking + encoding).

    Args:
        embedder: Instância do Embedder
        chunker: Instância do Chunker
        num_publicacoes: Número de publicações para processar

    Returns:
        BenchmarkResult com métricas
    """
    print(f"[6/6] Benchmark: End-to-End ({num_publicacoes} publicações)...")

    textos = [gerar_texto_exemplo(8000) for _ in range(num_publicacoes)]

    start_time = time.time()

    total_chunks = 0
    for texto in textos:
        # Dividir em chunks
        chunks = chunker.dividir_texto(texto, estrategia="paragrafo")
        total_chunks += len(chunks)

        # Gerar embeddings (batch)
        textos_chunks = [c.texto for c in chunks]
        embedder.encode_batch(textos_chunks, batch_size=16, normalizar=True, mostrar_progresso=False)

    elapsed = time.time() - start_time

    return BenchmarkResult(
        nome="End-to-End (chunking + encoding)",
        tempo_total_s=elapsed,
        num_operacoes=num_publicacoes,
        tempo_medio_s=elapsed / num_publicacoes,
        throughput=num_publicacoes / elapsed,
        metadata={
            "tamanho_texto_chars": 8000,
            "total_chunks": total_chunks,
            "chunks_por_publicacao": total_chunks / num_publicacoes
        }
    )


def exibir_resultados(resultados: List[BenchmarkResult], info_modelo: Dict):
    """
    Exibe resultados dos benchmarks formatados.

    Args:
        resultados: Lista de BenchmarkResults
        info_modelo: Informações do modelo
    """
    print("\n" + "=" * 90)
    print("RESULTADOS DOS BENCHMARKS")
    print("=" * 90)

    print(f"\nModelo: {info_modelo['modelo']}")
    print(f"Dimensão: {info_modelo['dimensao']}")
    print(f"Device: {info_modelo['device']}")

    print("\n" + "-" * 90)
    print(f"{'Benchmark':<40} {'Tempo Total':<15} {'Ops':<10} {'Média/Op':<15} {'Throughput':<15}")
    print("-" * 90)

    for resultado in resultados:
        print(
            f"{resultado.nome:<40} "
            f"{resultado.tempo_total_s:>10.2f}s     "
            f"{resultado.num_operacoes:>5}     "
            f"{resultado.tempo_medio_s*1000:>10.1f}ms     "
            f"{resultado.throughput:>10.1f} ops/s"
        )

    print("-" * 90)

    # Detalhar metadata
    print("\nDetalhes:")
    for resultado in resultados:
        if resultado.metadata:
            print(f"\n{resultado.nome}:")
            for k, v in resultado.metadata.items():
                if isinstance(v, float):
                    print(f"  {k}: {v:.4f}")
                else:
                    print(f"  {k}: {v}")

    # Estimativa para 100 publicações
    print("\n" + "=" * 90)
    print("ESTIMATIVA PARA 100 PUBLICAÇÕES")
    print("=" * 90)

    # Pegar benchmark end-to-end
    end_to_end = next((r for r in resultados if "End-to-End" in r.nome), None)
    if end_to_end:
        tempo_100_pub = (100 / end_to_end.throughput)
        print(f"Tempo estimado: {tempo_100_pub:.2f}s ({tempo_100_pub/60:.2f} minutos)")
        print(f"Throughput: {end_to_end.throughput:.2f} publicações/segundo")

        if end_to_end.metadata:
            chunks_por_pub = end_to_end.metadata.get('chunks_por_publicacao', 0)
            print(f"Chunks por publicação: {chunks_por_pub:.1f}")
            print(f"Total de chunks (100 pub): {int(100 * chunks_por_pub)}")


def main():
    """Função principal - executa benchmarks."""
    parser = argparse.ArgumentParser(description="Teste de Performance do Sistema RAG")
    parser.add_argument(
        "--num-textos",
        type=int,
        default=100,
        help="Número de textos para processar (padrão: 100)"
    )
    parser.add_argument(
        "--modelo",
        type=str,
        default="neuralmind/bert-base-portuguese-cased",
        help="Modelo de embeddings"
    )

    args = parser.parse_args()

    print("=" * 90)
    print("TESTE DE PERFORMANCE DO SISTEMA RAG")
    print("=" * 90)
    print(f"\nModelo: {args.modelo}")
    print(f"Número de textos: {args.num_textos}")

    # Inicializar componentes
    print("\nInicializando componentes...")
    embedder = Embedder(modelo=args.modelo)
    chunker = Chunker(tamanho_chunk=500, overlap=50)

    info_modelo = embedder.info_modelo()
    print(f"Modelo carregado: {info_modelo['modelo']} (dimensão={info_modelo['dimensao']})")
    print(f"Device: {info_modelo['device']}")

    # Executar benchmarks
    resultados = []

    resultados.append(benchmark_encoding_single(embedder, args.num_textos))
    resultados.append(benchmark_encoding_batch(embedder, args.num_textos))
    resultados.append(benchmark_chunking(chunker, args.num_textos))
    resultados.append(benchmark_serialization(embedder, args.num_textos))
    resultados.append(benchmark_cosine_similarity(embedder, args.num_textos * 10))
    resultados.append(benchmark_end_to_end(embedder, chunker, min(args.num_textos, 50)))

    # Exibir resultados
    exibir_resultados(resultados, info_modelo)


if __name__ == "__main__":
    main()
