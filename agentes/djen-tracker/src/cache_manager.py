"""
Cache Manager com Hash Validation e Automatic Invalidation

Gerencia cache de textos extraídos de PDFs com:
- Hash SHA256 para validação de mudanças
- Metadata tracking (timestamps, estratégias de extração)
- Invalidação automática por idade
- Estatísticas de cache hit/miss
- Compressão opcional para economizar espaço

Author: Claude Code (Development Agent)
Version: 1.0.0
"""

import json
import gzip
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Representa uma entrada no cache."""
    pdf_path: str
    pdf_hash: str
    text: str
    extraction_strategy: str
    cached_at: str  # ISO format
    file_size_bytes: int
    page_count: int
    char_count: int
    metadata: Dict

    @classmethod
    def from_dict(cls, data: dict) -> 'CacheEntry':
        """Cria CacheEntry de dicionário."""
        return cls(**data)

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return asdict(self)


@dataclass
class CacheStats:
    """Estatísticas de cache."""
    total_entries: int
    total_size_mb: float
    hits: int
    misses: int
    invalidations: int
    hit_rate: float

    def __str__(self) -> str:
        return (
            f"Cache Stats:\n"
            f"  Entries: {self.total_entries}\n"
            f"  Size: {self.total_size_mb:.1f} MB\n"
            f"  Hits: {self.hits}\n"
            f"  Misses: {self.misses}\n"
            f"  Invalidations: {self.invalidations}\n"
            f"  Hit Rate: {self.hit_rate:.1%}"
        )


class CacheManager:
    """
    Gerenciador de cache para textos extraídos de PDFs.

    Estrutura do cache:
    cache_dir/
        index.json          # Índice de todas entradas
        texts/              # Textos cacheados
            <hash>.txt      # Texto extraído (opcionalmente comprimido)
        metadata/           # Metadata de cada entrada
            <hash>.json

    Attributes:
        cache_dir: Diretório raiz do cache
        compress: Se True, comprime textos com gzip
        max_age_days: Idade máxima de cache (invalidação automática)
    """

    def __init__(
        self,
        cache_dir: Path,
        compress: bool = False,
        max_age_days: int = 30
    ):
        """
        Inicializa CacheManager.

        Args:
            cache_dir: Diretório para armazenar cache
            compress: Comprimir textos com gzip
            max_age_days: Invalidar cache mais antigo que X dias
        """
        self.cache_dir = Path(cache_dir)
        self.compress = compress
        self.max_age_days = max_age_days

        # Criar estrutura de diretórios
        self.texts_dir = self.cache_dir / "texts"
        self.metadata_dir = self.cache_dir / "metadata"
        self.index_file = self.cache_dir / "index.json"

        self.texts_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Estatísticas
        self._stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0
        }

        # Carregar índice
        self._index = self._load_index()

        logger.info(
            f"CacheManager inicializado: {cache_dir} "
            f"(compress={compress}, max_age={max_age_days}d)"
        )

    def _load_index(self) -> Dict[str, dict]:
        """Carrega índice de cache."""
        if not self.index_file.exists():
            logger.debug("Índice de cache não encontrado, criando novo")
            return {}

        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            logger.debug(f"Índice carregado: {len(index)} entradas")
            return index
        except Exception as e:
            logger.error(f"Erro ao carregar índice: {e}")
            return {}

    def _save_index(self) -> None:
        """Salva índice de cache."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, indent=2, ensure_ascii=False)
            logger.debug(f"Índice salvo: {len(self._index)} entradas")
        except Exception as e:
            logger.error(f"Erro ao salvar índice: {e}")

    def _calculate_hash(self, pdf_path: Path) -> str:
        """
        Calcula hash SHA256 de arquivo PDF.

        Args:
            pdf_path: Path para PDF

        Returns:
            Hash hexadecimal
        """
        hasher = hashlib.sha256()

        try:
            with open(pdf_path, 'rb') as f:
                # Ler em chunks de 64KB
                for chunk in iter(lambda: f.read(65536), b''):
                    hasher.update(chunk)

            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Erro ao calcular hash de {pdf_path}: {e}")
            raise

    def _get_cache_paths(self, pdf_hash: str) -> Tuple[Path, Path]:
        """
        Retorna paths para texto e metadata no cache.

        Args:
            pdf_hash: Hash do PDF

        Returns:
            (text_path, metadata_path)
        """
        text_ext = '.txt.gz' if self.compress else '.txt'
        text_path = self.texts_dir / f"{pdf_hash}{text_ext}"
        metadata_path = self.metadata_dir / f"{pdf_hash}.json"

        return text_path, metadata_path

    def _is_expired(self, cached_at: str) -> bool:
        """
        Verifica se cache está expirado.

        Args:
            cached_at: Timestamp ISO format

        Returns:
            True se expirado
        """
        try:
            cached_time = datetime.fromisoformat(cached_at)
            age = datetime.now() - cached_time
            return age > timedelta(days=self.max_age_days)
        except Exception as e:
            logger.warning(f"Erro ao verificar expiração: {e}")
            return True  # Assume expirado se erro

    def get(self, pdf_path: Path) -> Optional[CacheEntry]:
        """
        Recupera texto do cache se disponível e válido.

        Args:
            pdf_path: Path para arquivo PDF

        Returns:
            CacheEntry se cache válido, None caso contrário
        """
        try:
            # Calcular hash do PDF
            pdf_hash = self._calculate_hash(pdf_path)

            # Verificar se está no índice
            if pdf_hash not in self._index:
                logger.debug(f"Cache MISS: {pdf_path.name} (não indexado)")
                self._stats['misses'] += 1
                return None

            # Verificar expiração
            entry_data = self._index[pdf_hash]
            if self._is_expired(entry_data['cached_at']):
                logger.debug(
                    f"Cache MISS: {pdf_path.name} (expirado, "
                    f">{self.max_age_days}d)"
                )
                self.invalidate(pdf_path)
                self._stats['misses'] += 1
                return None

            # Carregar texto
            text_path, metadata_path = self._get_cache_paths(pdf_hash)

            if not text_path.exists():
                logger.warning(
                    f"Cache MISS: {pdf_path.name} (texto não encontrado)"
                )
                # Remover do índice pois está inconsistente
                del self._index[pdf_hash]
                self._save_index()
                self._stats['misses'] += 1
                return None

            # Ler texto
            if self.compress:
                with gzip.open(text_path, 'rt', encoding='utf-8') as f:
                    text = f.read()
            else:
                with open(text_path, 'r', encoding='utf-8') as f:
                    text = f.read()

            # Criar CacheEntry
            entry = CacheEntry(
                pdf_path=str(pdf_path),
                pdf_hash=pdf_hash,
                text=text,
                extraction_strategy=entry_data['extraction_strategy'],
                cached_at=entry_data['cached_at'],
                file_size_bytes=entry_data['file_size_bytes'],
                page_count=entry_data['page_count'],
                char_count=entry_data['char_count'],
                metadata=entry_data.get('metadata', {})
            )

            logger.debug(f"Cache HIT: {pdf_path.name}")
            self._stats['hits'] += 1
            return entry

        except Exception as e:
            logger.error(f"Erro ao recuperar cache de {pdf_path}: {e}")
            self._stats['misses'] += 1
            return None

    def save(
        self,
        pdf_path: Path,
        text: str,
        extraction_strategy: str,
        page_count: int,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Salva texto no cache.

        Args:
            pdf_path: Path para arquivo PDF
            text: Texto extraído
            extraction_strategy: Estratégia usada (pdfplumber, pypdf2, ocr)
            page_count: Número de páginas
            metadata: Metadata adicional

        Returns:
            True se salvou com sucesso
        """
        try:
            # Calcular hash
            pdf_hash = self._calculate_hash(pdf_path)

            # Preparar paths
            text_path, metadata_path = self._get_cache_paths(pdf_hash)

            # Salvar texto
            if self.compress:
                with gzip.open(text_path, 'wt', encoding='utf-8') as f:
                    f.write(text)
            else:
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text)

            # Preparar entry
            entry_data = {
                'pdf_path': str(pdf_path),
                'pdf_hash': pdf_hash,
                'extraction_strategy': extraction_strategy,
                'cached_at': datetime.now().isoformat(),
                'file_size_bytes': pdf_path.stat().st_size,
                'page_count': page_count,
                'char_count': len(text),
                'metadata': metadata or {}
            }

            # Salvar metadata
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(entry_data, f, indent=2, ensure_ascii=False)

            # Atualizar índice
            self._index[pdf_hash] = entry_data
            self._save_index()

            logger.debug(
                f"Cache SAVE: {pdf_path.name} "
                f"({len(text)} chars, {extraction_strategy})"
            )
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar cache de {pdf_path}: {e}")
            return False

    def invalidate(self, pdf_path: Path) -> bool:
        """
        Invalida cache de um PDF específico.

        Args:
            pdf_path: Path para arquivo PDF

        Returns:
            True se invalidou
        """
        try:
            pdf_hash = self._calculate_hash(pdf_path)

            if pdf_hash not in self._index:
                logger.debug(f"Cache não existe para {pdf_path.name}")
                return False

            # Remover arquivos
            text_path, metadata_path = self._get_cache_paths(pdf_hash)

            if text_path.exists():
                text_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()

            # Remover do índice
            del self._index[pdf_hash]
            self._save_index()

            self._stats['invalidations'] += 1
            logger.debug(f"Cache invalidado: {pdf_path.name}")
            return True

        except Exception as e:
            logger.error(f"Erro ao invalidar cache de {pdf_path}: {e}")
            return False

    def invalidate_old(self, older_than_days: Optional[int] = None) -> int:
        """
        Invalida cache mais antigo que X dias.

        Args:
            older_than_days: Dias (default: self.max_age_days)

        Returns:
            Número de entradas invalidadas
        """
        if older_than_days is None:
            older_than_days = self.max_age_days

        cutoff = datetime.now() - timedelta(days=older_than_days)
        invalidated = 0

        # Iterar sobre cópia do índice (pois vamos modificar)
        for pdf_hash, entry_data in list(self._index.items()):
            try:
                cached_time = datetime.fromisoformat(entry_data['cached_at'])

                if cached_time < cutoff:
                    # Remover arquivos
                    text_path, metadata_path = self._get_cache_paths(pdf_hash)

                    if text_path.exists():
                        text_path.unlink()
                    if metadata_path.exists():
                        metadata_path.unlink()

                    # Remover do índice
                    del self._index[pdf_hash]
                    invalidated += 1

            except Exception as e:
                logger.warning(f"Erro ao invalidar {pdf_hash}: {e}")
                continue

        # Salvar índice atualizado
        if invalidated > 0:
            self._save_index()
            self._stats['invalidations'] += invalidated
            logger.info(
                f"Invalidados {invalidated} caches mais antigos que "
                f"{older_than_days} dias"
            )

        return invalidated

    def clear_all(self) -> int:
        """
        Limpa todo o cache.

        Returns:
            Número de entradas removidas
        """
        count = len(self._index)

        # Remover todos arquivos
        for pdf_hash in self._index.keys():
            text_path, metadata_path = self._get_cache_paths(pdf_hash)

            if text_path.exists():
                text_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()

        # Limpar índice
        self._index = {}
        self._save_index()

        logger.info(f"Cache completamente limpo: {count} entradas removidas")
        return count

    def get_stats(self) -> CacheStats:
        """
        Retorna estatísticas de cache.

        Returns:
            CacheStats com métricas
        """
        total_entries = len(self._index)

        # Calcular tamanho total
        total_size = 0
        for text_file in self.texts_dir.glob('*'):
            if text_file.is_file():
                total_size += text_file.stat().st_size

        total_size_mb = total_size / (1024 * 1024)

        # Hit rate
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (
            self._stats['hits'] / total_requests
            if total_requests > 0
            else 0.0
        )

        return CacheStats(
            total_entries=total_entries,
            total_size_mb=total_size_mb,
            hits=self._stats['hits'],
            misses=self._stats['misses'],
            invalidations=self._stats['invalidations'],
            hit_rate=hit_rate
        )

    def list_entries(self) -> List[Dict]:
        """
        Lista todas entradas do cache.

        Returns:
            Lista de dicts com info de cada entrada
        """
        entries = []

        for pdf_hash, entry_data in self._index.items():
            entries.append({
                'hash': pdf_hash,
                'pdf_path': entry_data['pdf_path'],
                'cached_at': entry_data['cached_at'],
                'strategy': entry_data['extraction_strategy'],
                'pages': entry_data['page_count'],
                'chars': entry_data['char_count'],
                'size_kb': entry_data['file_size_bytes'] / 1024
            })

        # Ordenar por data (mais recente primeiro)
        entries.sort(key=lambda e: e['cached_at'], reverse=True)

        return entries


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Criar cache manager
    cache_dir = Path("/tmp/djen_cache_test")
    manager = CacheManager(cache_dir, compress=True, max_age_days=30)

    print("\n" + "=" * 70)
    print("CACHE MANAGER - Exemplo de Uso")
    print("=" * 70)

    # Simular salvamento
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])

        # Tentar recuperar
        print(f"\nTentando recuperar cache de {pdf_path.name}...")
        entry = manager.get(pdf_path)

        if entry:
            print(f"Cache HIT!")
            print(f"  Estratégia: {entry.extraction_strategy}")
            print(f"  Páginas: {entry.page_count}")
            print(f"  Caracteres: {entry.char_count}")
            print(f"  Cacheado em: {entry.cached_at}")
        else:
            print("Cache MISS - Simulando extração...")
            texto_fake = "Texto extraído do PDF (exemplo)" * 100

            manager.save(
                pdf_path=pdf_path,
                text=texto_fake,
                extraction_strategy="pdfplumber",
                page_count=10,
                metadata={'test': True}
            )
            print("Texto salvo no cache!")

    # Estatísticas
    print("\n" + "=" * 70)
    stats = manager.get_stats()
    print(stats)

    # Listar entradas
    print("\n" + "=" * 70)
    print("ENTRADAS NO CACHE")
    print("=" * 70)
    entries = manager.list_entries()
    for entry in entries[:5]:  # Mostrar apenas 5
        print(f"\n{entry['pdf_path']}")
        print(f"  Cached: {entry['cached_at']}")
        print(f"  Strategy: {entry['strategy']}")
        print(f"  Pages: {entry['pages']}, Chars: {entry['chars']}")
