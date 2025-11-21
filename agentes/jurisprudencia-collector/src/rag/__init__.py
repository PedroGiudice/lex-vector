"""
Módulo RAG (Retrieval-Augmented Generation)

Sistema de busca semântica para jurisprudência usando embeddings transformer
e similaridade de cosseno.

Componentes:
- Embedder: Geração de embeddings usando BERT português
- Chunker: Divisão de textos longos em chunks sobrepostos
- SemanticSearch: Busca por similaridade de cosseno

Exemplo de uso completo:
    from src.rag import Embedder, Chunker, SemanticSearch

    # 1. Gerar embeddings
    embedder = Embedder(modelo='neuralmind/bert-base-portuguese-cased')
    embedding = embedder.encode("Texto de publicação jurídica")

    # 2. Dividir texto longo
    chunker = Chunker(tamanho_chunk=500, overlap=50)
    chunks = chunker.dividir_texto("Texto muito longo...")

    # 3. Buscar publicações similares
    search = SemanticSearch(db_path="jurisprudencia.db")
    resultados = search.buscar(embedding, top_k=10)
"""

from .embedder import Embedder
from .chunker import Chunker, Chunk
from .search import SemanticSearch

__all__ = [
    'Embedder',
    'Chunker',
    'Chunk',
    'SemanticSearch'
]

__version__ = '1.0.0'
