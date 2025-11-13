"""
EpisodicMemory - Sistema de Memória Contextual para LLMs

Baseado em:
- MemOrb (SQLite metadata + ChromaDB vectors)
- Memori (Open-source memory engine)
- Padrões de memória episódica para agentes

Armazena:
- Decisões arquiteturais
- Soluções de problemas
- Bugs resolvidos
- Contextos de projetos
- Lições aprendidas

Permite:
- Busca semântica (embeddings)
- Recuperação temporal (SQLite)
- Query por contexto/tema
"""
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Tipos de memória episódica."""
    ARCHITECTURAL_DECISION = "architectural_decision"  # Decisões de arquitetura
    BUG_RESOLUTION = "bug_resolution"  # Bugs resolvidos
    SOLUTION_PATTERN = "solution_pattern"  # Padrões de solução
    PROJECT_CONTEXT = "project_context"  # Contexto de projetos
    LESSON_LEARNED = "lesson_learned"  # Lições aprendidas
    API_WORKAROUND = "api_workaround"  # Workarounds de APIs
    ORCHESTRATION = "orchestration"  # Decisões de orquestração


@dataclass
class MemoryUnit:
    """
    Unidade de memória (Orb).

    Representa uma experiência/conhecimento específico.
    """
    id: Optional[int] = None
    type: str = MemoryType.LESSON_LEARNED.value
    title: str = ""
    content: str = ""
    context: Dict[str, Any] = None  # {project, agent, task, etc}
    tags: List[str] = None  # ["DJEN", "API", "bug"]
    created_at: Optional[str] = None
    accessed_count: int = 0
    last_accessed: Optional[str] = None
    relevance_score: float = 0.0  # Score de relevância (calculado)
    metadata: Dict[str, Any] = None  # Metadata adicional

    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class EpisodicMemory:
    """
    Sistema de memória episódica para agentes LLM.

    Combina:
    - SQLite para metadata e busca estruturada
    - Embeddings (opcional) para busca semântica
    - TTL configurável para memórias temporárias

    Exemplo:
        >>> memory = EpisodicMemory(memory_dir=Path('./memory'))
        >>> memory.store(MemoryUnit(
        ...     type=MemoryType.BUG_RESOLUTION.value,
        ...     title="API DJEN filtro OAB não funciona",
        ...     content="Workaround: buscar todos + filtrar localmente",
        ...     tags=["DJEN", "API", "workaround"]
        ... ))
        >>> results = memory.recall(query="problema API DJEN", limit=5)
    """

    def __init__(
        self,
        memory_dir: Path,
        enable_embeddings: bool = False,
        default_ttl_days: Optional[int] = None  # None = sem expiração
    ):
        """
        Inicializa sistema de memória.

        Args:
            memory_dir: Diretório para armazenar memórias
            enable_embeddings: Se True, habilita busca semântica (requer sentence-transformers)
            default_ttl_days: TTL padrão em dias (None = sem expiração)
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.memory_dir / "episodic_memory.db"
        self.default_ttl_days = default_ttl_days
        self.enable_embeddings = enable_embeddings

        # Inicializar banco
        self._init_db()

        # Carregar modelo de embeddings se habilitado
        self.embedding_model = None
        if enable_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Modelo de embeddings carregado: all-MiniLM-L6-v2")
            except ImportError:
                logger.warning(
                    "sentence-transformers não instalado. "
                    "Busca semântica desabilitada. "
                    "Instale: pip install sentence-transformers"
                )
                self.enable_embeddings = False

        logger.info(f"EpisodicMemory inicializado: {self.db_path}")
        logger.info(f"  Embeddings: {self.enable_embeddings}")
        logger.info(f"  TTL padrão: {default_ttl_days} dias" if default_ttl_days else "  TTL: sem expiração")

    def _init_db(self):
        """Cria schema do banco de memórias."""
        with self._get_connection() as conn:
            # Tabela principal de memórias
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context_json TEXT,
                    tags_json TEXT,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    accessed_count INTEGER NOT NULL DEFAULT 0,
                    last_accessed TEXT,
                    relevance_score REAL DEFAULT 0.0,
                    metadata_json TEXT,
                    embedding_vector BLOB
                )
            """)

            # Índices para performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_type ON memories(type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at ON memories(expires_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relevance ON memories(relevance_score DESC)
            """)

            # Tabela de tags (para busca eficiente)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_tags (
                    memory_id INTEGER NOT NULL,
                    tag TEXT NOT NULL,
                    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tags ON memory_tags(tag, memory_id)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager para conexão SQLite."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")  # Habilitar foreign keys
        try:
            yield conn
        finally:
            conn.close()

    def _generate_embedding(self, text: str) -> Optional[bytes]:
        """
        Gera embedding de texto.

        Args:
            text: Texto para vetorizar

        Returns:
            Embedding em bytes ou None se desabilitado
        """
        if not self.enable_embeddings or not self.embedding_model:
            return None

        try:
            # Gerar embedding
            embedding = self.embedding_model.encode(text)

            # Converter para bytes (numpy array → bytes)
            return embedding.tobytes()

        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            return None

    def store(
        self,
        memory: MemoryUnit,
        ttl_days: Optional[int] = None
    ) -> int:
        """
        Armazena memória.

        Args:
            memory: Unidade de memória
            ttl_days: TTL em dias (usa default se None)

        Returns:
            ID da memória armazenada
        """
        # Calcular expiração
        expires_at = None
        if ttl_days is not None or self.default_ttl_days is not None:
            days = ttl_days if ttl_days is not None else self.default_ttl_days
            expires_at = (datetime.now() + timedelta(days=days)).isoformat()

        # Gerar embedding do conteúdo completo
        text_for_embedding = f"{memory.title}\n\n{memory.content}"
        embedding_bytes = self._generate_embedding(text_for_embedding)

        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO memories (
                    type, title, content, context_json, tags_json,
                    created_at, expires_at, accessed_count, last_accessed,
                    relevance_score, metadata_json, embedding_vector
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.type,
                memory.title,
                memory.content,
                json.dumps(memory.context, ensure_ascii=False),
                json.dumps(memory.tags, ensure_ascii=False),
                memory.created_at,
                expires_at,
                memory.accessed_count,
                memory.last_accessed,
                memory.relevance_score,
                json.dumps(memory.metadata, ensure_ascii=False),
                embedding_bytes
            ))

            memory_id = cursor.lastrowid

            # Inserir tags na tabela auxiliar
            for tag in memory.tags:
                conn.execute("""
                    INSERT INTO memory_tags (memory_id, tag)
                    VALUES (?, ?)
                """, (memory_id, tag.lower()))

            conn.commit()

        logger.info(
            f"Memória armazenada: ID={memory_id}, "
            f"Type={memory.type}, Title='{memory.title}', "
            f"Tags={memory.tags}"
        )

        return memory_id

    def recall(
        self,
        query: Optional[str] = None,
        type_filter: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        min_relevance: float = 0.0
    ) -> List[MemoryUnit]:
        """
        Recupera memórias baseado em critérios.

        Args:
            query: Texto para busca semântica (se embeddings habilitados)
            type_filter: Filtrar por tipo de memória
            tags: Filtrar por tags
            limit: Número máximo de resultados
            min_relevance: Relevância mínima (0.0-1.0)

        Returns:
            Lista de memórias ordenadas por relevância
        """
        with self._get_connection() as conn:
            # Construir query SQL
            sql_parts = ["SELECT DISTINCT m.* FROM memories m"]
            where_clauses = []
            params = []

            # Filtro por tipo
            if type_filter:
                where_clauses.append("m.type = ?")
                params.append(type_filter)

            # Filtro por tags
            if tags:
                sql_parts.append("JOIN memory_tags mt ON m.id = mt.memory_id")
                tag_placeholders = ','.join('?' * len(tags))
                where_clauses.append(f"mt.tag IN ({tag_placeholders})")
                params.extend([t.lower() for t in tags])

            # Filtro por relevância mínima
            if min_relevance > 0.0:
                where_clauses.append("m.relevance_score >= ?")
                params.append(min_relevance)

            # Filtro por expiração
            where_clauses.append("(m.expires_at IS NULL OR m.expires_at > ?)")
            params.append(datetime.now().isoformat())

            # Montar WHERE
            if where_clauses:
                sql_parts.append("WHERE " + " AND ".join(where_clauses))

            # Ordenação por relevância + recência
            sql_parts.append("ORDER BY m.relevance_score DESC, m.created_at DESC")

            # Limite
            sql_parts.append(f"LIMIT {limit}")

            sql = " ".join(sql_parts)

            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()

            # Converter rows para MemoryUnit
            memories = []
            for row in rows:
                memory = MemoryUnit(
                    id=row['id'],
                    type=row['type'],
                    title=row['title'],
                    content=row['content'],
                    context=json.loads(row['context_json']) if row['context_json'] else {},
                    tags=json.loads(row['tags_json']) if row['tags_json'] else [],
                    created_at=row['created_at'],
                    accessed_count=row['accessed_count'],
                    last_accessed=row['last_accessed'],
                    relevance_score=row['relevance_score'],
                    metadata=json.loads(row['metadata_json']) if row['metadata_json'] else {}
                )
                memories.append(memory)

                # Atualizar contador de acesso
                conn.execute("""
                    UPDATE memories
                    SET accessed_count = accessed_count + 1,
                        last_accessed = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), row['id']))

            conn.commit()

        logger.info(f"Recall: {len(memories)} memórias recuperadas (query='{query}', tags={tags})")

        # TODO: Se query e embeddings habilitados, calcular similaridade semântica
        # e reordenar resultados por score semântico

        return memories

    def recall_by_semantic_similarity(
        self,
        query: str,
        limit: int = 10,
        type_filter: Optional[str] = None
    ) -> List[Tuple[MemoryUnit, float]]:
        """
        Busca por similaridade semântica (requer embeddings).

        Args:
            query: Texto de busca
            limit: Número máximo de resultados
            type_filter: Filtrar por tipo

        Returns:
            Lista de (memória, score_similaridade) ordenada por score
        """
        if not self.enable_embeddings:
            logger.warning("Busca semântica desabilitada (embeddings não disponíveis)")
            return [(m, 0.0) for m in self.recall(query=query, type_filter=type_filter, limit=limit)]

        # Gerar embedding da query
        query_embedding_bytes = self._generate_embedding(query)

        if query_embedding_bytes is None:
            return [(m, 0.0) for m in self.recall(query=query, type_filter=type_filter, limit=limit)]

        try:
            import numpy as np

            # Converter query embedding de bytes para numpy array
            query_embedding = np.frombuffer(query_embedding_bytes, dtype=np.float32)

            # Buscar todas as memórias com embeddings
            with self._get_connection() as conn:
                sql_parts = ["SELECT * FROM memories WHERE embedding_vector IS NOT NULL"]
                params = []

                # Filtro por tipo
                if type_filter:
                    sql_parts.append("AND type = ?")
                    params.append(type_filter)

                # Filtro por expiração
                sql_parts.append("AND (expires_at IS NULL OR expires_at > ?)")
                params.append(datetime.now().isoformat())

                sql = " ".join(sql_parts)
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()

                # Calcular similaridade para cada memória
                results = []
                for row in rows:
                    # Converter embedding armazenado de bytes para numpy array
                    stored_embedding = np.frombuffer(row['embedding_vector'], dtype=np.float32)

                    # Calcular similaridade de coseno
                    # cos_sim = (A · B) / (||A|| * ||B||)
                    dot_product = np.dot(query_embedding, stored_embedding)
                    norm_query = np.linalg.norm(query_embedding)
                    norm_stored = np.linalg.norm(stored_embedding)

                    if norm_query > 0 and norm_stored > 0:
                        similarity = dot_product / (norm_query * norm_stored)
                    else:
                        similarity = 0.0

                    # Criar MemoryUnit
                    memory = MemoryUnit(
                        id=row['id'],
                        type=row['type'],
                        title=row['title'],
                        content=row['content'],
                        context=json.loads(row['context_json']) if row['context_json'] else {},
                        tags=json.loads(row['tags_json']) if row['tags_json'] else [],
                        created_at=row['created_at'],
                        accessed_count=row['accessed_count'],
                        last_accessed=row['last_accessed'],
                        relevance_score=row['relevance_score'],
                        metadata=json.loads(row['metadata_json']) if row['metadata_json'] else {}
                    )

                    results.append((memory, similarity))

                    # Atualizar contador de acesso
                    conn.execute("""
                        UPDATE memories
                        SET accessed_count = accessed_count + 1,
                            last_accessed = ?
                        WHERE id = ?
                    """, (datetime.now().isoformat(), row['id']))

                conn.commit()

            # Ordenar por similaridade (descendente)
            results.sort(key=lambda x: x[1], reverse=True)

            # Limitar resultados
            results = results[:limit]

            logger.info(
                f"Busca semântica: {len(results)} memórias encontradas para query='{query}'"
            )

            return results

        except ImportError:
            logger.error("numpy não instalado - busca semântica requer numpy")
            return [(m, 0.0) for m in self.recall(query=query, type_filter=type_filter, limit=limit)]

        except Exception as e:
            logger.error(f"Erro na busca semântica: {e}")
            return [(m, 0.0) for m in self.recall(query=query, type_filter=type_filter, limit=limit)]

    def update_relevance(self, memory_id: int, score: float) -> bool:
        """
        Atualiza score de relevância de uma memória.

        Args:
            memory_id: ID da memória
            score: Novo score (0.0-1.0)

        Returns:
            True se sucesso
        """
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE memories
                    SET relevance_score = ?
                    WHERE id = ?
                """, (score, memory_id))
                conn.commit()

            logger.debug(f"Relevância atualizada: ID={memory_id}, Score={score}")
            return True

        except Exception as e:
            logger.error(f"Erro ao atualizar relevância: {e}")
            return False

    def forget(self, memory_id: int) -> bool:
        """
        Remove memória do sistema.

        Args:
            memory_id: ID da memória

        Returns:
            True se deletado
        """
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
                conn.commit()

            logger.info(f"Memória esquecida: ID={memory_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao esquecer memória: {e}")
            return False

    def cleanup_expired(self) -> int:
        """
        Remove memórias expiradas.

        Returns:
            Número de memórias removidas
        """
        try:
            now = datetime.now().isoformat()

            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM memories
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                """, (now,))
                deleted = cursor.rowcount
                conn.commit()

            if deleted > 0:
                logger.info(f"Cleanup: {deleted} memórias expiradas removidas")

            return deleted

        except Exception as e:
            logger.error(f"Erro no cleanup: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Estatísticas do sistema de memória.

        Returns:
            Dict com estatísticas
        """
        with self._get_connection() as conn:
            # Estatísticas gerais
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(DISTINCT type) as types_count,
                    SUM(accessed_count) as total_accesses,
                    AVG(relevance_score) as avg_relevance,
                    MIN(created_at) as oldest,
                    MAX(created_at) as newest
                FROM memories
                WHERE expires_at IS NULL OR expires_at > ?
            """, (datetime.now().isoformat(),))

            row = cursor.fetchone()

            # Contagem por tipo
            cursor = conn.execute("""
                SELECT type, COUNT(*) as count
                FROM memories
                WHERE expires_at IS NULL OR expires_at > ?
                GROUP BY type
                ORDER BY count DESC
            """, (datetime.now().isoformat(),))

            by_type = {row['type']: row['count'] for row in cursor.fetchall()}

            # Tags mais usadas
            cursor = conn.execute("""
                SELECT tag, COUNT(*) as count
                FROM memory_tags
                GROUP BY tag
                ORDER BY count DESC
                LIMIT 10
            """)

            top_tags = [{'tag': row['tag'], 'count': row['count']} for row in cursor.fetchall()]

            return {
                'total_memories': row['total'] or 0,
                'types_count': row['types_count'] or 0,
                'total_accesses': row['total_accesses'] or 0,
                'avg_relevance': round(row['avg_relevance'] or 0.0, 2),
                'oldest_memory': row['oldest'],
                'newest_memory': row['newest'],
                'by_type': by_type,
                'top_tags': top_tags,
                'embeddings_enabled': self.enable_embeddings
            }

    def export_memories(
        self,
        output_file: Path,
        type_filter: Optional[str] = None
    ) -> int:
        """
        Exporta memórias para JSON.

        Args:
            output_file: Arquivo de saída
            type_filter: Filtrar por tipo (opcional)

        Returns:
            Número de memórias exportadas
        """
        memories = self.recall(type_filter=type_filter, limit=999999)

        data = [asdict(m) for m in memories]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exportadas {len(memories)} memórias para {output_file}")

        return len(memories)


# ============================================================================
# CLI EXEMPLO
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sistema de Memória Episódica")
    parser.add_argument('--memory-dir', required=True, help="Diretório de memórias")
    parser.add_argument('--action', required=True, choices=['store', 'recall', 'stats', 'export'])
    parser.add_argument('--type', help="Tipo de memória")
    parser.add_argument('--title', help="Título da memória")
    parser.add_argument('--content', help="Conteúdo da memória")
    parser.add_argument('--tags', nargs='+', help="Tags")
    parser.add_argument('--query', help="Query de busca")
    parser.add_argument('--limit', type=int, default=10, help="Limite de resultados")
    parser.add_argument('--output', help="Arquivo de saída (export)")

    args = parser.parse_args()

    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Criar sistema de memória
    memory = EpisodicMemory(Path(args.memory_dir), enable_embeddings=True)

    if args.action == 'store':
        if not args.title or not args.content:
            print("Erro: --title e --content são obrigatórios para store")
            exit(1)

        unit = MemoryUnit(
            type=args.type or MemoryType.LESSON_LEARNED.value,
            title=args.title,
            content=args.content,
            tags=args.tags or []
        )

        memory_id = memory.store(unit)
        print(f"✅ Memória armazenada: ID={memory_id}")

    elif args.action == 'recall':
        results = memory.recall(
            query=args.query,
            type_filter=args.type,
            tags=args.tags,
            limit=args.limit
        )

        print(f"\n📋 {len(results)} memórias encontradas:\n")

        for i, mem in enumerate(results, 1):
            print(f"## {i}. {mem.title} (ID: {mem.id})")
            print(f"   Tipo: {mem.type}")
            print(f"   Tags: {', '.join(mem.tags)}")
            print(f"   Score: {mem.relevance_score:.2f}")
            print(f"   Acessos: {mem.accessed_count}")
            print(f"   Criado: {mem.created_at}")
            print(f"   Conteúdo: {mem.content[:200]}...")
            print()

    elif args.action == 'stats':
        stats = memory.get_stats()

        print("\n📊 Estatísticas de Memória:\n")
        print(f"Total de memórias: {stats['total_memories']}")
        print(f"Tipos diferentes: {stats['types_count']}")
        print(f"Acessos totais: {stats['total_accesses']}")
        print(f"Relevância média: {stats['avg_relevance']:.2f}")
        print(f"Embeddings: {'✅ Ativados' if stats['embeddings_enabled'] else '❌ Desativados'}")
        print(f"\nPor tipo:")
        for tipo, count in stats['by_type'].items():
            print(f"  - {tipo}: {count}")
        print(f"\nTop tags:")
        for tag_info in stats['top_tags']:
            print(f"  - {tag_info['tag']}: {tag_info['count']}")

    elif args.action == 'export':
        if not args.output:
            print("Erro: --output é obrigatório para export")
            exit(1)

        count = memory.export_memories(Path(args.output), type_filter=args.type)
        print(f"✅ {count} memórias exportadas para {args.output}")
