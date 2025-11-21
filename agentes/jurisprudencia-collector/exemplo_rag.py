#!/usr/bin/env python3
"""
Exemplo Completo de Uso do Sistema RAG

Demonstra o fluxo completo:
1. Geração de embeddings para publicações
2. Armazenamento no SQLite
3. Busca semântica por similaridade
4. Busca híbrida (semântica + textual)

Uso:
    python exemplo_rag.py --db jurisprudencia.db --query "responsabilidade civil"
"""

import sys
import time
import logging
from pathlib import Path
from typing import List, Dict
import sqlite3
import argparse
import numpy as np

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rag import Embedder, Chunker, SemanticSearch

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def processar_publicacao_completa(
    texto: str,
    publicacao_id: str,
    embedder: Embedder,
    db_path: str
) -> Dict:
    """
    Processa uma publicação completa: gera embedding e armazena no DB.

    Args:
        texto: Texto completo da publicação
        publicacao_id: UUID da publicação
        embedder: Instância do Embedder
        db_path: Caminho para banco SQLite

    Returns:
        Dict com resultado do processamento
    """
    start_time = time.time()

    # Gerar embedding
    logger.info(f"Gerando embedding para publicacao_id={publicacao_id[:8]}...")
    embedding = embedder.encode(texto, normalizar=True, mostrar_tempo=True)

    # Serializar para BLOB
    blob = embedder.serializar_embedding(embedding)

    # Inserir no banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO embeddings
            (publicacao_id, embedding, dimensao, modelo, versao_modelo, data_criacao)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                publicacao_id,
                blob,
                embedder.dimensao,
                embedder.modelo_nome,
                None
            )
        )
        conn.commit()
        logger.info(f"Embedding armazenado com sucesso!")

    except Exception as e:
        logger.error(f"Erro ao armazenar embedding: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()

    elapsed = time.time() - start_time

    return {
        "publicacao_id": publicacao_id,
        "dimensao": embedder.dimensao,
        "tamanho_blob_bytes": len(blob),
        "tempo_processamento_s": elapsed
    }


def processar_publicacao_longa(
    texto: str,
    publicacao_id: str,
    embedder: Embedder,
    chunker: Chunker,
    db_path: str
) -> Dict:
    """
    Processa publicação longa: divide em chunks e gera embeddings para cada chunk.

    Args:
        texto: Texto completo da publicação
        publicacao_id: UUID da publicação
        embedder: Instância do Embedder
        chunker: Instância do Chunker
        db_path: Caminho para banco SQLite

    Returns:
        Dict com resultado do processamento
    """
    start_time = time.time()

    # Dividir em chunks
    logger.info(f"Dividindo texto em chunks (publicacao_id={publicacao_id[:8]}...)")
    chunks_metadata = chunker.dividir_com_metadata(
        texto=texto,
        publicacao_id=publicacao_id,
        estrategia="paragrafo"
    )

    logger.info(f"Texto dividido em {len(chunks_metadata)} chunks")

    # Extrair textos dos chunks para batch processing
    textos_chunks = [c['texto'] for c in chunks_metadata]

    # Gerar embeddings em batch
    logger.info("Gerando embeddings para todos os chunks...")
    embeddings = embedder.encode_batch(
        textos_chunks,
        batch_size=32,
        normalizar=True,
        mostrar_progresso=True
    )

    # Inserir no banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Inserir chunks
        for chunk_meta in chunks_metadata:
            cursor.execute(
                """
                INSERT OR REPLACE INTO chunks
                (id, publicacao_id, chunk_index, texto, tamanho_tokens)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    chunk_meta['id'],
                    chunk_meta['publicacao_id'],
                    chunk_meta['chunk_index'],
                    chunk_meta['texto'],
                    chunk_meta['tamanho_tokens']
                )
            )

        # Inserir embeddings dos chunks
        for i, (chunk_meta, embedding) in enumerate(zip(chunks_metadata, embeddings)):
            blob = embedder.serializar_embedding(embedding)

            cursor.execute(
                """
                INSERT OR REPLACE INTO chunks_embeddings
                (chunk_id, embedding, dimensao, modelo, data_criacao)
                VALUES (?, ?, ?, ?, datetime('now'))
                """,
                (
                    chunk_meta['id'],
                    blob,
                    embedder.dimensao,
                    embedder.modelo_nome
                )
            )

        conn.commit()
        logger.info(f"Chunks e embeddings armazenados com sucesso!")

    except Exception as e:
        logger.error(f"Erro ao armazenar chunks: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()

    elapsed = time.time() - start_time

    return {
        "publicacao_id": publicacao_id,
        "total_chunks": len(chunks_metadata),
        "dimensao": embedder.dimensao,
        "tempo_processamento_s": elapsed
    }


def buscar_publicacoes(
    query_text: str,
    embedder: Embedder,
    search: SemanticSearch,
    top_k: int = 10,
    filtros: Dict = None,
    modo: str = "semantico"
) -> List[Dict]:
    """
    Realiza busca semântica de publicações.

    Args:
        query_text: Texto da consulta
        embedder: Instância do Embedder
        search: Instância do SemanticSearch
        top_k: Número de resultados
        filtros: Filtros opcionais (tribunal, data, tipo)
        modo: Tipo de busca ('semantico', 'hibrido')

    Returns:
        Lista de resultados
    """
    logger.info(f"Processando consulta: '{query_text}'")

    # Gerar embedding da query
    query_embedding = embedder.encode(query_text, normalizar=True, mostrar_tempo=True)

    # Buscar
    if modo == "semantico":
        logger.info("Executando busca semântica...")
        resultados = search.buscar(
            query_embedding=query_embedding,
            top_k=top_k,
            filtros=filtros,
            incluir_chunks=False
        )

    elif modo == "hibrido":
        logger.info("Executando busca híbrida (semântica + textual)...")
        resultados = search.buscar_hibrida(
            query_text=query_text,
            query_embedding=query_embedding,
            top_k=top_k,
            peso_semantico=0.7,
            filtros=filtros
        )

    else:
        raise ValueError(f"Modo inválido: {modo}")

    return resultados


def exibir_resultados(resultados: List[Dict]):
    """
    Exibe resultados de busca formatados.

    Args:
        resultados: Lista de resultados retornados pela busca
    """
    print("\n" + "=" * 80)
    print(f"RESULTADOS DA BUSCA ({len(resultados)} publicações)")
    print("=" * 80)

    for i, resultado in enumerate(resultados, 1):
        print(f"\n{i}. {resultado['numero_processo_fmt'] or 'N/A'}")
        print(f"   Tribunal: {resultado['tribunal']} | Tipo: {resultado['tipo_publicacao']}")
        print(f"   Data: {resultado['data_publicacao']}")
        print(f"   Score: {resultado['score_similaridade']:.4f}", end='')

        if 'score_final' in resultado:
            print(f" (semântico: {resultado['score_semantico']:.4f}, textual: {resultado['score_textual']:.4f})")
        else:
            print()

        if resultado.get('ementa'):
            ementa_preview = resultado['ementa'][:200] + '...' if len(resultado['ementa']) > 200 else resultado['ementa']
            print(f"   Ementa: {ementa_preview}")

        if resultado.get('chunk_index') is not None:
            print(f"   [Chunk {resultado['chunk_index']}]")

    # Estatísticas
    search = SemanticSearch(db_path="jurisprudencia.db")
    stats = search.estatisticas_busca(resultados)

    print("\n" + "=" * 80)
    print("ESTATÍSTICAS")
    print("=" * 80)
    print(f"Total de resultados: {stats['total_resultados']}")
    print(f"Score médio: {stats['score_medio']:.4f}")
    print(f"Score máximo: {stats['score_max']:.4f}")
    print(f"Score mínimo: {stats['score_min']:.4f}")
    print(f"Tribunais: {', '.join(stats['tribunais_encontrados'])}")
    print(f"Tipos: {', '.join(stats['tipos_encontrados'])}")


def main():
    """Função principal - exemplo de uso."""
    parser = argparse.ArgumentParser(description="Sistema RAG para Jurisprudência")
    parser.add_argument("--db", type=str, default="jurisprudencia.db", help="Caminho para banco SQLite")
    parser.add_argument("--query", type=str, help="Texto da consulta")
    parser.add_argument("--top-k", type=int, default=10, help="Número de resultados")
    parser.add_argument("--tribunal", type=str, help="Filtrar por tribunal (ex: TJSP)")
    parser.add_argument("--modo", choices=["semantico", "hibrido"], default="semantico", help="Modo de busca")
    parser.add_argument("--modelo", type=str, default="neuralmind/bert-base-portuguese-cased", help="Modelo de embeddings")

    args = parser.parse_args()

    # Inicializar componentes
    logger.info(f"Inicializando sistema RAG (modelo={args.modelo})...")

    embedder = Embedder(modelo=args.modelo)
    chunker = Chunker(tamanho_chunk=500, overlap=50)
    search = SemanticSearch(db_path=args.db, threshold_similaridade=0.7)

    logger.info("Sistema inicializado com sucesso!")
    print("\n" + embedder.info_modelo().__str__())

    # Se query fornecida, realizar busca
    if args.query:
        filtros = {}
        if args.tribunal:
            filtros['tribunal'] = args.tribunal

        resultados = buscar_publicacoes(
            query_text=args.query,
            embedder=embedder,
            search=search,
            top_k=args.top_k,
            filtros=filtros or None,
            modo=args.modo
        )

        exibir_resultados(resultados)

    else:
        print("\n⚠️  Nenhuma query fornecida. Use --query para realizar busca.")
        print("\nExemplo:")
        print('  python exemplo_rag.py --query "responsabilidade civil acidente" --top-k 5')


if __name__ == "__main__":
    main()
