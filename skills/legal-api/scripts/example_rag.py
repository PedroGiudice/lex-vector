#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) Implementation Example

Demonstrates:
- Embedding generation (Portuguese-optimized models)
- Cosine similarity search
- Chunking for long texts
- Integration with SQLite database

Usage:
    python example_rag.py --db publicacoes.db --query "responsabilidade civil dano moral"
"""

import argparse
import sqlite3
import numpy as np
from typing import List, Dict, Tuple, Optional


class SimpleEmbedder:
    """
    Simplified embedder for demonstration.

    In production, use:
    - sentence-transformers/paraphrase-multilingual-mpnet-base-v2
    - neuralmind/bert-base-portuguese-cased
    - multilingual-e5-small

    This example uses TF-IDF for simplicity (no external dependencies).
    """

    def __init__(self):
        self.vocabulary = {}
        self.idf = {}
        self.dimension = 300  # Simulated embedding dimension

    def fit(self, texts: List[str]):
        """Build vocabulary and IDF from corpus"""
        from collections import Counter
        import math

        # Build vocabulary
        all_words = []
        doc_word_sets = []
        for text in texts:
            words = text.lower().split()
            all_words.extend(words)
            doc_word_sets.append(set(words))

        # Create vocabulary
        word_counts = Counter(all_words)
        self.vocabulary = {word: idx for idx, word in enumerate(word_counts.keys())}

        # Calculate IDF
        num_docs = len(texts)
        for word in self.vocabulary:
            doc_count = sum(1 for doc_words in doc_word_sets if word in doc_words)
            self.idf[word] = math.log(num_docs / (1 + doc_count))

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for text (TF-IDF representation)"""
        from collections import Counter

        # Tokenize
        words = text.lower().split()
        word_counts = Counter(words)

        # Create sparse vector
        vector = np.zeros(len(self.vocabulary))
        for word, count in word_counts.items():
            if word in self.vocabulary:
                idx = self.vocabulary[word]
                tf = count / len(words) if words else 0
                vector[idx] = tf * self.idf.get(word, 0)

        # Pad/truncate to fixed dimension
        if len(vector) < self.dimension:
            vector = np.pad(vector, (0, self.dimension - len(vector)))
        else:
            vector = vector[:self.dimension]

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.astype(np.float32)


class RAGSearchEngine:
    """RAG search engine for legal publications"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.embedder = SimpleEmbedder()

    def indexar_publicacoes(self, limit: Optional[int] = None):
        """
        Generate embeddings for all publications without them.

        In production:
        - Use batch processing
        - Save embeddings to database
        - Use GPU acceleration
        """
        cursor = self.conn.cursor()

        # Get publications without embeddings
        query = """
        SELECT id, texto_limpo, ementa
        FROM publicacoes
        WHERE id NOT IN (SELECT publicacao_id FROM embeddings)
        """
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        publications = cursor.fetchall()

        if not publications:
            print("✅ All publications already indexed")
            return

        print(f"📚 Indexing {len(publications)} publications...")

        # Fit embedder on corpus
        texts = [pub['texto_limpo'] or pub['ementa'] or "" for pub in publications]
        self.embedder.fit(texts)

        # Generate and store embeddings
        for i, pub in enumerate(publications):
            text = pub['texto_limpo'] or pub['ementa'] or ""
            embedding = self.embedder.embed(text)

            # Store in database
            cursor.execute("""
            INSERT OR REPLACE INTO embeddings (publicacao_id, embedding, dimensao, modelo)
            VALUES (?, ?, ?, ?)
            """, (pub['id'], embedding.tobytes(), len(embedding), 'simple-tfidf'))

            if (i + 1) % 100 == 0:
                self.conn.commit()
                print(f"  Indexed {i + 1}/{len(publications)}")

        self.conn.commit()
        print(f"✅ Indexing complete!")

    def buscar_similares(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.3,
        filters: Optional[Dict] = None
    ) -> List[Tuple[str, float, Dict]]:
        """
        Search for similar publications using cosine similarity.

        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Minimum similarity score (0.0 to 1.0)
            filters: Optional filters (tribunal, tipo_publicacao, etc)

        Returns:
            List of tuples (publicacao_id, similarity_score, metadata)
        """
        # Generate query embedding
        # First need to fit on existing data
        cursor = self.conn.cursor()
        cursor.execute("SELECT texto_limpo FROM publicacoes LIMIT 1000")
        sample_texts = [row['texto_limpo'] for row in cursor.fetchall() if row['texto_limpo']]
        self.embedder.fit(sample_texts)

        query_embedding = self.embedder.embed(query)

        # Build SQL with filters
        where_clauses = []
        params = []

        if filters:
            if 'tribunal' in filters:
                where_clauses.append("p.tribunal = ?")
                params.append(filters['tribunal'])
            if 'tipo_publicacao' in filters:
                where_clauses.append("p.tipo_publicacao = ?")
                params.append(filters['tipo_publicacao'])

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Get all embeddings with metadata
        query_sql = f"""
        SELECT
            e.publicacao_id,
            e.embedding,
            p.numero_processo_fmt,
            p.tribunal,
            p.tipo_publicacao,
            p.ementa,
            p.data_publicacao
        FROM embeddings e
        JOIN publicacoes p ON e.publicacao_id = p.id
        {where_sql}
        """

        cursor.execute(query_sql, params)

        # Calculate similarities
        results = []
        for row in cursor.fetchall():
            # Deserialize embedding
            embedding_bytes = row['embedding']
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)

            # Cosine similarity
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )

            if similarity >= threshold:
                metadata = {
                    'numero_processo': row['numero_processo_fmt'],
                    'tribunal': row['tribunal'],
                    'tipo': row['tipo_publicacao'],
                    'ementa': row['ementa'],
                    'data': row['data_publicacao']
                }
                results.append((row['publicacao_id'], float(similarity), metadata))

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def print_results(self, results: List[Tuple[str, float, Dict]]):
        """Pretty-print search results"""
        if not results:
            print("\n❌ No results found")
            return

        print(f"\n📊 Found {len(results)} results:")
        print("=" * 80)

        for i, (pub_id, score, metadata) in enumerate(results, 1):
            print(f"\n#{i} | Similarity: {score:.3f}")
            print(f"Processo: {metadata.get('numero_processo', 'N/A')}")
            print(f"Tribunal: {metadata.get('tribunal', 'N/A')}")
            print(f"Tipo: {metadata.get('tipo', 'N/A')}")
            print(f"Data: {metadata.get('data', 'N/A')}")

            ementa = metadata.get('ementa')
            if ementa:
                preview = ementa[:200] + "..." if len(ementa) > 200 else ementa
                print(f"Ementa: {preview}")

            print("-" * 80)

    def create_embeddings_table(self):
        """Create embeddings table if it doesn't exist"""
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            publicacao_id TEXT PRIMARY KEY,
            embedding BLOB NOT NULL,
            dimensao INTEGER NOT NULL,
            modelo TEXT NOT NULL,
            FOREIGN KEY (publicacao_id) REFERENCES publicacoes(id) ON DELETE CASCADE
        )
        """)
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='RAG Search Example for Legal Publications'
    )
    parser.add_argument('--db', required=True, help='SQLite database path')
    parser.add_argument('--query', required=True, help='Search query')
    parser.add_argument('--tribunal', help='Filter by tribunal (optional)')
    parser.add_argument('--tipo', help='Filter by type (optional)')
    parser.add_argument('--top-k', type=int, default=10, help='Number of results')
    parser.add_argument('--index', action='store_true',
                        help='Index publications before searching')

    args = parser.parse_args()

    print(f"🔍 RAG Search Example")
    print(f"Database: {args.db}")
    print(f"Query: {args.query}")

    rag = RAGSearchEngine(args.db)

    try:
        # Create embeddings table if needed
        rag.create_embeddings_table()

        # Index if requested
        if args.index:
            rag.indexar_publicacoes(limit=1000)

        # Build filters
        filters = {}
        if args.tribunal:
            filters['tribunal'] = args.tribunal
        if args.tipo:
            filters['tipo_publicacao'] = args.tipo

        # Search
        print(f"\n🔎 Searching...")
        results = rag.buscar_similares(
            query=args.query,
            top_k=args.top_k,
            threshold=0.3,
            filters=filters if filters else None
        )

        # Display results
        rag.print_results(results)

    finally:
        rag.close()


if __name__ == '__main__':
    main()
