"""
Módulo de Busca Semântica por Similaridade

Implementa busca por similaridade de cosseno entre embeddings de consulta
e embeddings armazenados no banco de dados SQLite. Suporta filtros por
tribunal, data, tipo de publicação, etc.

Estratégia:
- Similaridade de cosseno (threshold 0.7 padrão)
- Busca em embeddings de publicações completas ou chunks
- Filtros opcionais (tribunal, data, tipo)
- Ranking por score de similaridade

Uso:
    from src.rag.search import SemanticSearch

    search = SemanticSearch(db_path="jurisprudencia.db")
    resultados = search.buscar("responsabilidade civil acidente", top_k=10)
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
import sqlite3
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SemanticSearch:
    """
    Sistema de busca semântica usando similaridade de cosseno.

    Attributes:
        db_path: Caminho para banco SQLite
        threshold_similaridade: Threshold mínimo para retornar resultado (0.0-1.0)
    """

    def __init__(
        self,
        db_path: str,
        threshold_similaridade: float = 0.7
    ):
        """
        Inicializa sistema de busca semântica.

        Args:
            db_path: Caminho para arquivo SQLite
            threshold_similaridade: Score mínimo para retornar resultado (padrão: 0.7)

        Raises:
            ValueError: Threshold inválido
            FileNotFoundError: Banco de dados não encontrado
        """
        if not 0.0 <= threshold_similaridade <= 1.0:
            raise ValueError("threshold_similaridade deve estar entre 0.0 e 1.0")

        db_path_obj = Path(db_path)
        if not db_path_obj.exists():
            raise FileNotFoundError(f"Banco de dados não encontrado: {db_path}")

        self.db_path = db_path
        self.threshold_similaridade = threshold_similaridade

        logger.info(
            f"SemanticSearch inicializado: {db_path} (threshold={threshold_similaridade})"
        )

    def buscar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filtros: Optional[Dict] = None,
        incluir_chunks: bool = False
    ) -> List[Dict]:
        """
        Busca publicações semanticamente similares à query.

        Args:
            query_embedding: Embedding da consulta (numpy array normalizado)
            top_k: Número máximo de resultados a retornar
            filtros: Filtros opcionais:
                - tribunal: str ou List[str] (ex: "TJSP", ["STJ", "STF"])
                - tipo_publicacao: str ou List[str]
                - data_inicio: str (YYYY-MM-DD)
                - data_fim: str (YYYY-MM-DD)
            incluir_chunks: Se True, busca também em chunks (textos divididos)

        Returns:
            Lista de dicts ordenada por similaridade (maior→menor):
                {
                    'publicacao_id': str,
                    'score_similaridade': float,
                    'numero_processo_fmt': str,
                    'tribunal': str,
                    'tipo_publicacao': str,
                    'data_publicacao': str,
                    'ementa': str,
                    'texto_limpo': str (preview 500 chars),
                    'chunk_index': int (se incluir_chunks=True)
                }

        Raises:
            ValueError: Query embedding inválido
        """
        # Validar query embedding
        if query_embedding.ndim != 1:
            raise ValueError("query_embedding deve ser 1D array")

        if not np.isclose(np.linalg.norm(query_embedding), 1.0, atol=1e-5):
            logger.warning("query_embedding não normalizado, normalizando...")
            query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Conectar ao banco
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Retornar rows como dicts
        cursor = conn.cursor()

        try:
            # Buscar embeddings de publicações
            resultados = []

            # Query SQL base
            sql_base = """
                SELECT
                    e.publicacao_id,
                    e.embedding,
                    e.dimensao,
                    p.numero_processo_fmt,
                    p.tribunal,
                    p.tipo_publicacao,
                    p.data_publicacao,
                    p.ementa,
                    p.texto_limpo,
                    p.relator,
                    p.orgao_julgador
                FROM embeddings e
                INNER JOIN publicacoes p ON e.publicacao_id = p.id
            """

            # Adicionar filtros
            where_clauses = []
            params = []

            if filtros:
                if 'tribunal' in filtros:
                    tribunais = filtros['tribunal']
                    if isinstance(tribunais, str):
                        tribunais = [tribunais]
                    placeholders = ','.join(['?'] * len(tribunais))
                    where_clauses.append(f"p.tribunal IN ({placeholders})")
                    params.extend(tribunais)

                if 'tipo_publicacao' in filtros:
                    tipos = filtros['tipo_publicacao']
                    if isinstance(tipos, str):
                        tipos = [tipos]
                    placeholders = ','.join(['?'] * len(tipos))
                    where_clauses.append(f"p.tipo_publicacao IN ({placeholders})")
                    params.extend(tipos)

                if 'data_inicio' in filtros:
                    where_clauses.append("p.data_publicacao >= ?")
                    params.append(filtros['data_inicio'])

                if 'data_fim' in filtros:
                    where_clauses.append("p.data_publicacao <= ?")
                    params.append(filtros['data_fim'])

            # Montar query completa
            if where_clauses:
                sql_completa = sql_base + " WHERE " + " AND ".join(where_clauses)
            else:
                sql_completa = sql_base

            # Executar query
            cursor.execute(sql_completa, params)
            rows = cursor.fetchall()

            logger.info(f"Encontrados {len(rows)} embeddings no banco")

            # Calcular similaridade para cada embedding
            for row in rows:
                # Desserializar embedding
                blob = row['embedding']
                dimensao = row['dimensao']
                db_embedding = np.frombuffer(blob, dtype=np.float32)

                # Verificar dimensão compatível
                if len(query_embedding) != dimensao:
                    logger.warning(
                        f"Dimensões incompatíveis: query={len(query_embedding)}, "
                        f"db={dimensao}, publicacao_id={row['publicacao_id']}"
                    )
                    continue

                # Calcular similaridade de cosseno
                score = self._similaridade_cosseno(query_embedding, db_embedding)

                # Filtrar por threshold
                if score < self.threshold_similaridade:
                    continue

                # Montar resultado
                resultado = {
                    'publicacao_id': row['publicacao_id'],
                    'score_similaridade': float(score),
                    'numero_processo_fmt': row['numero_processo_fmt'],
                    'tribunal': row['tribunal'],
                    'tipo_publicacao': row['tipo_publicacao'],
                    'data_publicacao': row['data_publicacao'],
                    'ementa': row['ementa'] or '',
                    'texto_preview': (row['texto_limpo'] or '')[:500] + '...',
                    'relator': row['relator'],
                    'orgao_julgador': row['orgao_julgador'],
                    'chunk_index': None  # Null para publicação completa
                }

                resultados.append(resultado)

            # Buscar em chunks se solicitado
            if incluir_chunks:
                resultados_chunks = self._buscar_em_chunks(
                    query_embedding, filtros, cursor
                )
                resultados.extend(resultados_chunks)

            # Ordenar por similaridade (maior primeiro)
            resultados.sort(key=lambda x: x['score_similaridade'], reverse=True)

            # Limitar a top_k
            resultados = resultados[:top_k]

            logger.info(
                f"Busca concluída: {len(resultados)} resultados "
                f"(threshold={self.threshold_similaridade})"
            )

            return resultados

        finally:
            conn.close()

    def buscar_similar_por_id(
        self,
        publicacao_id: str,
        top_k: int = 10,
        excluir_propria: bool = True
    ) -> List[Dict]:
        """
        Busca publicações similares a uma publicação específica.

        Args:
            publicacao_id: ID da publicação de referência
            top_k: Número de resultados
            excluir_propria: Se True, exclui a própria publicação dos resultados

        Returns:
            Lista de publicações similares

        Raises:
            ValueError: publicacao_id não encontrado
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Buscar embedding da publicação
            cursor.execute(
                "SELECT embedding, dimensao FROM embeddings WHERE publicacao_id = ?",
                (publicacao_id,)
            )
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"Publicação {publicacao_id} não possui embedding")

            # Desserializar embedding
            blob = row['embedding']
            dimensao = row['dimensao']
            query_embedding = np.frombuffer(blob, dtype=np.float32)

            # Realizar busca
            resultados = self.buscar(
                query_embedding=query_embedding,
                top_k=top_k + 1 if excluir_propria else top_k,
                filtros=None,
                incluir_chunks=False
            )

            # Excluir própria publicação se solicitado
            if excluir_propria:
                resultados = [
                    r for r in resultados
                    if r['publicacao_id'] != publicacao_id
                ]

            return resultados[:top_k]

        finally:
            conn.close()

    def _buscar_em_chunks(
        self,
        query_embedding: np.ndarray,
        filtros: Optional[Dict],
        cursor: sqlite3.Cursor
    ) -> List[Dict]:
        """
        Busca em embeddings de chunks (textos divididos).

        Args:
            query_embedding: Embedding da query
            filtros: Filtros aplicados
            cursor: Cursor SQLite

        Returns:
            Lista de resultados de chunks
        """
        sql_base = """
            SELECT
                ce.chunk_id,
                ce.embedding,
                ce.dimensao,
                c.publicacao_id,
                c.chunk_index,
                c.texto,
                p.numero_processo_fmt,
                p.tribunal,
                p.tipo_publicacao,
                p.data_publicacao,
                p.ementa
            FROM chunks_embeddings ce
            INNER JOIN chunks c ON ce.chunk_id = c.id
            INNER JOIN publicacoes p ON c.publicacao_id = p.id
        """

        # Aplicar mesmos filtros
        where_clauses = []
        params = []

        if filtros:
            if 'tribunal' in filtros:
                tribunais = filtros['tribunal']
                if isinstance(tribunais, str):
                    tribunais = [tribunais]
                placeholders = ','.join(['?'] * len(tribunais))
                where_clauses.append(f"p.tribunal IN ({placeholders})")
                params.extend(tribunais)

            if 'tipo_publicacao' in filtros:
                tipos = filtros['tipo_publicacao']
                if isinstance(tipos, str):
                    tipos = [tipos]
                placeholders = ','.join(['?'] * len(tipos))
                where_clauses.append(f"p.tipo_publicacao IN ({placeholders})")
                params.extend(tipos)

            if 'data_inicio' in filtros:
                where_clauses.append("p.data_publicacao >= ?")
                params.append(filtros['data_inicio'])

            if 'data_fim' in filtros:
                where_clauses.append("p.data_publicacao <= ?")
                params.append(filtros['data_fim'])

        if where_clauses:
            sql_completa = sql_base + " WHERE " + " AND ".join(where_clauses)
        else:
            sql_completa = sql_base

        cursor.execute(sql_completa, params)
        rows = cursor.fetchall()

        logger.info(f"Encontrados {len(rows)} chunk embeddings")

        resultados = []
        for row in rows:
            blob = row['embedding']
            dimensao = row['dimensao']
            db_embedding = np.frombuffer(blob, dtype=np.float32)

            if len(query_embedding) != dimensao:
                continue

            score = self._similaridade_cosseno(query_embedding, db_embedding)

            if score < self.threshold_similaridade:
                continue

            resultado = {
                'publicacao_id': row['publicacao_id'],
                'score_similaridade': float(score),
                'numero_processo_fmt': row['numero_processo_fmt'],
                'tribunal': row['tribunal'],
                'tipo_publicacao': row['tipo_publicacao'],
                'data_publicacao': row['data_publicacao'],
                'ementa': row['ementa'] or '',
                'texto_preview': row['texto'][:500] + '...',
                'relator': None,
                'orgao_julgador': None,
                'chunk_index': row['chunk_index']
            }

            resultados.append(resultado)

        return resultados

    def _similaridade_cosseno(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calcula similaridade de cosseno entre dois embeddings.

        Args:
            embedding1: Primeiro embedding (normalizado)
            embedding2: Segundo embedding (normalizado)

        Returns:
            Similaridade de cosseno (0.0 a 1.0)
        """
        # Para vetores normalizados, cosseno = dot product
        return float(np.dot(embedding1, embedding2))

    def estatisticas_busca(
        self,
        resultados: List[Dict]
    ) -> Dict:
        """
        Calcula estatísticas sobre resultados de busca.

        Args:
            resultados: Lista de resultados retornados por buscar()

        Returns:
            Dict com estatísticas:
                - total_resultados: int
                - score_medio: float
                - score_max/min: float
                - tribunais_encontrados: List[str]
                - tipos_encontrados: List[str]
        """
        if not resultados:
            return {
                "total_resultados": 0,
                "score_medio": 0.0,
                "score_max": 0.0,
                "score_min": 0.0,
                "tribunais_encontrados": [],
                "tipos_encontrados": []
            }

        scores = [r['score_similaridade'] for r in resultados]
        tribunais = list(set(r['tribunal'] for r in resultados))
        tipos = list(set(r['tipo_publicacao'] for r in resultados))

        return {
            "total_resultados": len(resultados),
            "score_medio": sum(scores) / len(scores),
            "score_max": max(scores),
            "score_min": min(scores),
            "tribunais_encontrados": sorted(tribunais),
            "tipos_encontrados": sorted(tipos)
        }

    def buscar_hibrida(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        peso_semantico: float = 0.7,
        filtros: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Busca híbrida: combina busca semântica + busca textual (FTS5).

        Args:
            query_text: Texto da consulta (para FTS5)
            query_embedding: Embedding da consulta (para similaridade)
            top_k: Número de resultados
            peso_semantico: Peso da busca semântica (0.0-1.0). Ex: 0.7 = 70% semântico + 30% textual
            filtros: Filtros opcionais

        Returns:
            Lista combinada e re-ranqueada de resultados
        """
        # Busca semântica
        resultados_semanticos = self.buscar(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Buscar mais para combinar
            filtros=filtros,
            incluir_chunks=False
        )

        # Busca textual (FTS5)
        resultados_textuais = self._buscar_textual(query_text, top_k * 2, filtros)

        # Combinar scores
        # Criar dict: publicacao_id -> scores
        scores_combinados = {}

        for r in resultados_semanticos:
            pub_id = r['publicacao_id']
            scores_combinados[pub_id] = {
                'score_semantico': r['score_similaridade'],
                'score_textual': 0.0,
                'dados': r
            }

        for r in resultados_textuais:
            pub_id = r['publicacao_id']
            if pub_id in scores_combinados:
                scores_combinados[pub_id]['score_textual'] = r['score_textual']
            else:
                scores_combinados[pub_id] = {
                    'score_semantico': 0.0,
                    'score_textual': r['score_textual'],
                    'dados': r
                }

        # Calcular score final: weighted average
        peso_textual = 1.0 - peso_semantico

        resultados_finais = []
        for pub_id, scores in scores_combinados.items():
            score_final = (
                scores['score_semantico'] * peso_semantico +
                scores['score_textual'] * peso_textual
            )

            resultado = scores['dados'].copy()
            resultado['score_final'] = score_final
            resultado['score_semantico'] = scores['score_semantico']
            resultado['score_textual'] = scores['score_textual']

            resultados_finais.append(resultado)

        # Ordenar por score final
        resultados_finais.sort(key=lambda x: x['score_final'], reverse=True)

        return resultados_finais[:top_k]

    def _buscar_textual(
        self,
        query: str,
        top_k: int,
        filtros: Optional[Dict]
    ) -> List[Dict]:
        """
        Busca textual usando FTS5 (Full-Text Search).

        Args:
            query: Texto da consulta
            top_k: Número de resultados
            filtros: Filtros opcionais

        Returns:
            Lista de resultados com score_textual normalizado (0.0-1.0)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Query FTS5 com ranking (BM25)
            sql = """
                SELECT
                    p.id AS publicacao_id,
                    p.numero_processo_fmt,
                    p.tribunal,
                    p.tipo_publicacao,
                    p.data_publicacao,
                    p.ementa,
                    p.texto_limpo,
                    bm25(publicacoes_fts) AS score_bm25
                FROM publicacoes_fts
                INNER JOIN publicacoes p ON publicacoes_fts.rowid = p.rowid
                WHERE publicacoes_fts MATCH ?
            """

            where_clauses = []
            params = [query]

            if filtros:
                if 'tribunal' in filtros:
                    tribunais = filtros['tribunal']
                    if isinstance(tribunais, str):
                        tribunais = [tribunais]
                    placeholders = ','.join(['?'] * len(tribunais))
                    where_clauses.append(f"p.tribunal IN ({placeholders})")
                    params.extend(tribunais)

                if 'tipo_publicacao' in filtros:
                    tipos = filtros['tipo_publicacao']
                    if isinstance(tipos, str):
                        tipos = [tipos]
                    placeholders = ','.join(['?'] * len(tipos))
                    where_clauses.append(f"p.tipo_publicacao IN ({placeholders})")
                    params.extend(tipos)

            if where_clauses:
                sql += " AND " + " AND ".join(where_clauses)

            sql += " ORDER BY score_bm25 LIMIT ?"
            params.append(top_k)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # Normalizar BM25 scores para 0.0-1.0
            if rows:
                scores = [abs(row['score_bm25']) for row in rows]
                max_score = max(scores)
                min_score = min(scores)
                range_score = max_score - min_score if max_score != min_score else 1.0

            resultados = []
            for row in rows:
                score_normalizado = (abs(row['score_bm25']) - min_score) / range_score

                resultado = {
                    'publicacao_id': row['publicacao_id'],
                    'score_textual': float(score_normalizado),
                    'score_similaridade': 0.0,  # Placeholder
                    'numero_processo_fmt': row['numero_processo_fmt'],
                    'tribunal': row['tribunal'],
                    'tipo_publicacao': row['tipo_publicacao'],
                    'data_publicacao': row['data_publicacao'],
                    'ementa': row['ementa'] or '',
                    'texto_preview': (row['texto_limpo'] or '')[:500] + '...',
                    'relator': None,
                    'orgao_julgador': None,
                    'chunk_index': None
                }

                resultados.append(resultado)

            return resultados

        finally:
            conn.close()


# Exemplo de uso
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("TESTE DE BUSCA SEMÂNTICA")
    print("=" * 80)

    # Nota: Este exemplo assume que o banco já tem embeddings populados
    # Para teste completo, executar após popular banco com embeddings

    # Simular query embedding (normalmente viria do Embedder)
    query_embedding_fake = np.random.rand(768).astype(np.float32)
    query_embedding_fake = query_embedding_fake / np.linalg.norm(query_embedding_fake)

    print(f"\nQuery embedding shape: {query_embedding_fake.shape}")
    print(f"Query embedding normalizado: {np.linalg.norm(query_embedding_fake):.4f}")

    # Teste de similaridade de cosseno
    search = SemanticSearch(db_path="jurisprudencia.db", threshold_similaridade=0.7)

    emb1 = np.array([1.0, 0.0, 0.0])
    emb2 = np.array([0.5, 0.866, 0.0])  # 60 graus
    emb3 = np.array([0.0, 1.0, 0.0])    # 90 graus

    print("\nTestes de similaridade:")
    print(f"  cosseno([1,0,0], [1,0,0]): {search._similaridade_cosseno(emb1, emb1):.4f}")
    print(f"  cosseno([1,0,0], [0.5,0.866,0]): {search._similaridade_cosseno(emb1, emb2):.4f}")
    print(f"  cosseno([1,0,0], [0,1,0]): {search._similaridade_cosseno(emb1, emb3):.4f}")

    print("\n✅ Módulo search.py carregado com sucesso!")
