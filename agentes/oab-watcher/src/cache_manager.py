"""
CacheManager - Sistema de cache inteligente com SQLite + gzip
"""
import sqlite3
import json
import gzip
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Gerenciador de cache com SQLite, compressão gzip e TTL configurável.

    Features:
    - Compressão automática (gzip) para economizar espaço
    - TTL (Time To Live) configurável por item
    - Cleanup automático de itens expirados
    - Estatísticas de cache (hit/miss rate)
    - Thread-safe com context manager

    Exemplo:
        >>> cache = CacheManager(cache_dir=Path('./cache'), default_ttl_hours=24)
        >>> cache.set('busca_2025-11-07', data, ttl_hours=12)
        >>> cached = cache.get('busca_2025-11-07')
    """

    def __init__(
        self,
        cache_dir: Path,
        default_ttl_hours: int = 24,
        enable_compression: bool = True,
        auto_cleanup: bool = True
    ):
        """
        Inicializa o CacheManager.

        Args:
            cache_dir: Diretório onde o banco SQLite será criado
            default_ttl_hours: TTL padrão em horas (default: 24h)
            enable_compression: Se True, comprime dados com gzip (default: True)
            auto_cleanup: Se True, faz cleanup automático ao inicializar (default: True)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.cache_dir / "cache.db"
        self.default_ttl_hours = default_ttl_hours
        self.enable_compression = enable_compression

        # Estatísticas
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }

        # Inicializar banco
        self._init_db()

        # Cleanup inicial
        if auto_cleanup:
            self._cleanup_expired()

        logger.info(f"CacheManager inicializado: {self.db_path}")
        logger.info(f"Configuração: TTL={default_ttl_hours}h, Compressão={enable_compression}")

    def _init_db(self):
        """Cria tabela de cache se não existir."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    compressed INTEGER NOT NULL DEFAULT 1,
                    size_bytes INTEGER NOT NULL,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    last_accessed TEXT
                )
            """)

            # Índices para performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON cache(created_at)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager para conexão SQLite thread-safe."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get(self, key: str) -> Optional[Dict[Any, Any]]:
        """
        Recupera item do cache.

        Args:
            key: Chave do item

        Returns:
            Dict com dados ou None se não existir/expirado
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT value, compressed, expires_at, access_count
                FROM cache
                WHERE key = ?
            """, (key,))

            row = cursor.fetchone()

            if not row:
                self.stats['misses'] += 1
                logger.debug(f"Cache MISS: {key}")
                return None

            # Verificar expiração
            expires_at = datetime.fromisoformat(row['expires_at'])
            if datetime.now() >= expires_at:
                logger.debug(f"Cache EXPIRED: {key}")
                self._delete(key)
                self.stats['misses'] += 1
                self.stats['evictions'] += 1
                return None

            # Descomprimir se necessário
            value_blob = row['value']
            if row['compressed']:
                value_str = gzip.decompress(value_blob).decode('utf-8')
            else:
                value_str = value_blob.decode('utf-8')

            # Atualizar contadores de acesso
            conn.execute("""
                UPDATE cache
                SET access_count = ?,
                    last_accessed = ?
                WHERE key = ?
            """, (row['access_count'] + 1, datetime.now().isoformat(), key))
            conn.commit()

            self.stats['hits'] += 1
            logger.debug(f"Cache HIT: {key}")

            return json.loads(value_str)

    def set(
        self,
        key: str,
        value: Dict[Any, Any],
        ttl_hours: Optional[int] = None
    ) -> bool:
        """
        Armazena item no cache.

        Args:
            key: Chave do item
            value: Dados a armazenar (deve ser serializável em JSON)
            ttl_hours: TTL em horas (usa default se None)

        Returns:
            True se sucesso, False se erro
        """
        try:
            ttl = ttl_hours if ttl_hours is not None else self.default_ttl_hours

            # Serializar para JSON
            value_str = json.dumps(value, ensure_ascii=False)

            # Comprimir se habilitado
            if self.enable_compression:
                value_blob = gzip.compress(value_str.encode('utf-8'))
                compressed = 1
            else:
                value_blob = value_str.encode('utf-8')
                compressed = 0

            # Calcular timestamps
            now = datetime.now()
            expires_at = now + timedelta(hours=ttl)

            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache
                    (key, value, created_at, expires_at, compressed, size_bytes, access_count, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, 0, NULL)
                """, (
                    key,
                    value_blob,
                    now.isoformat(),
                    expires_at.isoformat(),
                    compressed,
                    len(value_blob)
                ))
                conn.commit()

            self.stats['sets'] += 1

            # Log com informações de compressão
            original_size = len(value_str.encode('utf-8'))
            cached_size = len(value_blob)
            ratio = (1 - cached_size / original_size) * 100 if original_size > 0 else 0

            logger.debug(
                f"Cache SET: {key} (TTL={ttl}h, "
                f"Original={original_size}B, Cached={cached_size}B, "
                f"Ratio={ratio:.1f}%)"
            )

            return True

        except Exception as e:
            logger.error(f"Erro ao salvar cache {key}: {e}", exc_info=True)
            return False

    def _delete(self, key: str) -> bool:
        """Deleta item do cache."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar cache {key}: {e}")
            return False

    def invalidate(self, key: str) -> bool:
        """
        Invalida item do cache (alias para _delete).

        Args:
            key: Chave do item

        Returns:
            True se deletado, False se erro
        """
        logger.info(f"Invalidando cache: {key}")
        return self._delete(key)

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalida todos os itens que correspondem ao pattern SQL LIKE.

        Args:
            pattern: Pattern SQL (ex: "busca_2025-11-%")

        Returns:
            Número de itens deletados
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM cache WHERE key LIKE ?
                """, (pattern,))
                deleted = cursor.rowcount
                conn.commit()

            logger.info(f"Invalidados {deleted} items com pattern: {pattern}")
            return deleted

        except Exception as e:
            logger.error(f"Erro ao invalidar pattern {pattern}: {e}")
            return 0

    def _cleanup_expired(self) -> int:
        """
        Remove itens expirados do cache.

        Returns:
            Número de itens removidos
        """
        try:
            now = datetime.now().isoformat()

            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM cache WHERE expires_at < ?
                """, (now,))
                deleted = cursor.rowcount
                conn.commit()

            if deleted > 0:
                logger.info(f"Cleanup: removidos {deleted} itens expirados")
                self.stats['evictions'] += deleted

            return deleted

        except Exception as e:
            logger.error(f"Erro no cleanup: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.

        Returns:
            Dict com estatísticas:
            - hits/misses/sets/evictions
            - hit_rate (%)
            - total_items
            - total_size_mb
            - oldest_item
            - most_accessed
        """
        with self._get_connection() as conn:
            # Estatísticas básicas
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_items,
                    SUM(size_bytes) as total_bytes,
                    MIN(created_at) as oldest,
                    MAX(access_count) as max_access
                FROM cache
            """)
            row = cursor.fetchone()

            total_items = row['total_items'] or 0
            total_bytes = row['total_bytes'] or 0
            oldest = row['oldest']

            # Item mais acessado
            cursor = conn.execute("""
                SELECT key, access_count
                FROM cache
                ORDER BY access_count DESC
                LIMIT 1
            """)
            most_accessed = cursor.fetchone()

            # Calcular hit rate
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

            return {
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'sets': self.stats['sets'],
                'evictions': self.stats['evictions'],
                'hit_rate': round(hit_rate, 2),
                'total_items': total_items,
                'total_size_mb': round(total_bytes / (1024 * 1024), 2),
                'oldest_item': oldest,
                'most_accessed': {
                    'key': most_accessed['key'] if most_accessed else None,
                    'count': most_accessed['access_count'] if most_accessed else 0
                }
            }

    def list_keys(self, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista chaves do cache com metadados.

        Args:
            pattern: Pattern SQL LIKE (opcional)

        Returns:
            Lista de dicts com: key, created_at, expires_at, size_bytes, access_count
        """
        with self._get_connection() as conn:
            if pattern:
                cursor = conn.execute("""
                    SELECT key, created_at, expires_at, size_bytes, access_count, last_accessed
                    FROM cache
                    WHERE key LIKE ?
                    ORDER BY created_at DESC
                """, (pattern,))
            else:
                cursor = conn.execute("""
                    SELECT key, created_at, expires_at, size_bytes, access_count, last_accessed
                    FROM cache
                    ORDER BY created_at DESC
                """)

            return [dict(row) for row in cursor.fetchall()]

    def clear_all(self) -> int:
        """
        Remove TODOS os itens do cache.

        Returns:
            Número de itens removidos
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM cache")
                deleted = cursor.rowcount
                conn.commit()

            logger.warning(f"Cache LIMPO: {deleted} itens removidos")
            self.stats['evictions'] += deleted

            return deleted

        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return 0
