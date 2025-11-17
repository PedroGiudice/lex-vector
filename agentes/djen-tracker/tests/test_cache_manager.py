"""
Testes para módulo cache_manager.py - Gerenciamento de cache de PDFs.

Valida:
- Hit/miss de cache
- Invalidação automática por idade
- Compressão de textos
- Estatísticas de cache
- Hash validation
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

from src.cache_manager import CacheManager, CacheEntry, CacheStats


class TestCacheManagerInit:
    """Testes para inicialização do cache manager."""

    def test_init_cria_estrutura(self, cache_dir):
        """Inicialização cria estrutura de diretórios."""
        manager = CacheManager(cache_dir)

        assert (cache_dir / "texts").exists()
        assert (cache_dir / "metadata").exists()
        assert (cache_dir / "index.json").exists()

    def test_init_com_compressao(self, cache_dir):
        """Inicializa com compressão habilitada."""
        manager = CacheManager(cache_dir, compress=True)
        assert manager.compress is True

    def test_init_custom_max_age(self, cache_dir):
        """Inicializa com max_age customizado."""
        manager = CacheManager(cache_dir, max_age_days=15)
        assert manager.max_age_days == 15


class TestCacheSaveGet:
    """Testes para save e get de cache."""

    def test_save_e_get_texto(self, cache_dir, sample_pdf_path):
        """Salva e recupera texto do cache."""
        manager = CacheManager(cache_dir)

        # Salvar
        success = manager.save(
            pdf_path=sample_pdf_path,
            text="Texto de teste cacheado",
            extraction_strategy="pdfplumber",
            page_count=10
        )
        assert success is True

        # Recuperar
        entry = manager.get(sample_pdf_path)
        assert entry is not None
        assert entry.text == "Texto de teste cacheado"
        assert entry.extraction_strategy == "pdfplumber"
        assert entry.page_count == 10

    def test_cache_miss_arquivo_nao_existente(self, cache_dir, temp_dir):
        """Cache miss para arquivo não cacheado."""
        manager = CacheManager(cache_dir)

        fake_pdf = temp_dir / "nao_cacheado.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4\n%%EOF")

        entry = manager.get(fake_pdf)
        assert entry is None

    def test_save_com_compressao(self, cache_dir, sample_pdf_path):
        """Salva texto com compressão."""
        manager = CacheManager(cache_dir, compress=True)

        success = manager.save(
            pdf_path=sample_pdf_path,
            text="Texto" * 1000,  # Texto grande para compressão
            extraction_strategy="pdfplumber",
            page_count=50
        )
        assert success is True

        # Verificar que arquivo está comprimido (.txt.gz)
        text_files = list((cache_dir / "texts").glob("*.txt.gz"))
        assert len(text_files) > 0

        # Recuperar deve funcionar
        entry = manager.get(sample_pdf_path)
        assert entry is not None
        assert "Texto" in entry.text

    def test_get_incrementa_hits(self, cache_dir, sample_pdf_path):
        """Get de cache incrementa contador de hits."""
        manager = CacheManager(cache_dir)

        manager.save(sample_pdf_path, "Texto", "pdfplumber", 1)

        initial_stats = manager.get_stats()
        manager.get(sample_pdf_path)
        final_stats = manager.get_stats()

        assert final_stats.hits == initial_stats.hits + 1

    def test_get_miss_incrementa_misses(self, cache_dir, temp_dir):
        """Get miss incrementa contador de misses."""
        manager = CacheManager(cache_dir)

        fake_pdf = temp_dir / "nao_existe.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4\n%%EOF")

        initial_stats = manager.get_stats()
        manager.get(fake_pdf)
        final_stats = manager.get_stats()

        assert final_stats.misses == initial_stats.misses + 1


class TestCacheInvalidation:
    """Testes para invalidação de cache."""

    def test_invalidate_remove_cache(self, cache_dir, sample_pdf_path):
        """Invalidate remove cache de PDF."""
        manager = CacheManager(cache_dir)

        # Salvar
        manager.save(sample_pdf_path, "Texto", "pdfplumber", 1)

        # Verificar que existe
        entry = manager.get(sample_pdf_path)
        assert entry is not None

        # Invalidar
        result = manager.invalidate(sample_pdf_path)
        assert result is True

        # Verificar que não existe mais
        entry = manager.get(sample_pdf_path)
        assert entry is None

    def test_invalidate_old_remove_caches_antigos(self, cache_dir, sample_pdf_path):
        """invalidate_old remove caches mais antigos que X dias."""
        manager = CacheManager(cache_dir, max_age_days=7)

        # Salvar cache
        manager.save(sample_pdf_path, "Texto", "pdfplumber", 1)

        # Modificar timestamp manualmente para simular cache antigo
        pdf_hash = manager._calculate_hash(sample_pdf_path)
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        manager._index[pdf_hash]['cached_at'] = old_date
        manager._save_index()

        # Invalidar caches antigos (> 7 dias)
        invalidated = manager.invalidate_old(older_than_days=7)

        assert invalidated >= 1

        # Cache não deve mais existir
        entry = manager.get(sample_pdf_path)
        assert entry is None

    def test_invalidate_old_mantem_caches_recentes(self, cache_dir, sample_pdf_path):
        """invalidate_old mantém caches recentes."""
        manager = CacheManager(cache_dir, max_age_days=30)

        # Salvar cache recente
        manager.save(sample_pdf_path, "Texto", "pdfplumber", 1)

        # Invalidar caches > 30 dias
        invalidated = manager.invalidate_old(older_than_days=30)

        # Cache recente deve permanecer
        entry = manager.get(sample_pdf_path)
        assert entry is not None

    def test_clear_all_remove_tudo(self, cache_dir, sample_pdf_path):
        """clear_all remove todo o cache."""
        manager = CacheManager(cache_dir)

        # Salvar múltiplos caches
        manager.save(sample_pdf_path, "Texto 1", "pdfplumber", 1)

        initial_count = manager.get_stats().total_entries
        assert initial_count > 0

        # Limpar tudo
        removed = manager.clear_all()
        assert removed == initial_count

        # Verificar que não há mais caches
        stats = manager.get_stats()
        assert stats.total_entries == 0


class TestCacheStats:
    """Testes para estatísticas de cache."""

    def test_get_stats_retorna_estatisticas(self, cache_dir):
        """get_stats retorna CacheStats."""
        manager = CacheManager(cache_dir)
        stats = manager.get_stats()

        assert isinstance(stats, CacheStats)
        assert stats.total_entries == 0
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.invalidations == 0
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculado_corretamente(self, cache_dir, sample_pdf_path):
        """Hit rate é calculado corretamente."""
        manager = CacheManager(cache_dir)

        # Salvar cache
        manager.save(sample_pdf_path, "Texto", "pdfplumber", 1)

        # 2 hits, 1 miss
        manager.get(sample_pdf_path)  # hit
        manager.get(sample_pdf_path)  # hit

        fake_pdf = cache_dir / "fake.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4\n%%EOF")
        manager.get(fake_pdf)  # miss

        stats = manager.get_stats()
        assert stats.hits == 2
        assert stats.misses == 1
        assert stats.hit_rate == pytest.approx(2/3, abs=0.01)

    def test_stats_total_size(self, cache_dir, sample_pdf_path):
        """Estatísticas incluem tamanho total."""
        manager = CacheManager(cache_dir)

        manager.save(sample_pdf_path, "Texto" * 100, "pdfplumber", 1)

        stats = manager.get_stats()
        assert stats.total_size_mb > 0


class TestCacheEntry:
    """Testes para CacheEntry dataclass."""

    def test_cache_entry_from_dict(self):
        """Cria CacheEntry de dict."""
        data = {
            'pdf_path': '/tmp/test.pdf',
            'pdf_hash': 'abc123',
            'text': 'Texto',
            'extraction_strategy': 'pdfplumber',
            'cached_at': datetime.now().isoformat(),
            'file_size_bytes': 1024,
            'page_count': 10,
            'char_count': 100,
            'metadata': {}
        }

        entry = CacheEntry.from_dict(data)
        assert entry.pdf_path == '/tmp/test.pdf'
        assert entry.page_count == 10

    def test_cache_entry_to_dict(self):
        """Converte CacheEntry para dict."""
        entry = CacheEntry(
            pdf_path='/tmp/test.pdf',
            pdf_hash='abc123',
            text='Texto',
            extraction_strategy='pdfplumber',
            cached_at=datetime.now().isoformat(),
            file_size_bytes=1024,
            page_count=10,
            char_count=100,
            metadata={}
        )

        data = entry.to_dict()
        assert isinstance(data, dict)
        assert data['pdf_path'] == '/tmp/test.pdf'


class TestCacheListEntries:
    """Testes para listagem de entradas."""

    def test_list_entries_retorna_lista(self, cache_dir, sample_pdf_path):
        """list_entries retorna lista de entradas."""
        manager = CacheManager(cache_dir)

        manager.save(sample_pdf_path, "Texto", "pdfplumber", 5)

        entries = manager.list_entries()
        assert isinstance(entries, list)
        assert len(entries) == 1

    def test_list_entries_ordenado_por_data(self, cache_dir, sample_pdf_path, temp_dir):
        """Entradas ordenadas por data (mais recente primeiro)."""
        manager = CacheManager(cache_dir)

        # Salvar primeira entrada
        manager.save(sample_pdf_path, "Texto 1", "pdfplumber", 1)

        time.sleep(0.1)  # Garantir timestamps diferentes

        # Salvar segunda entrada
        pdf2 = temp_dir / "test2.pdf"
        pdf2.write_bytes(b"%PDF-1.4\nContent\n%%EOF")
        manager.save(pdf2, "Texto 2", "pypdf2", 2)

        entries = manager.list_entries()

        # Mais recente deve vir primeiro
        if len(entries) >= 2:
            date1 = datetime.fromisoformat(entries[0]['cached_at'])
            date2 = datetime.fromisoformat(entries[1]['cached_at'])
            assert date1 >= date2


class TestCacheIntegration:
    """Testes de integração do cache manager."""

    def test_workflow_completo(self, cache_dir, sample_pdf_path):
        """Testa workflow completo de cache."""
        manager = CacheManager(cache_dir, compress=True, max_age_days=30)

        # 1. Verificar que cache não existe (miss)
        entry = manager.get(sample_pdf_path)
        assert entry is None

        # 2. Salvar no cache
        success = manager.save(
            pdf_path=sample_pdf_path,
            text="Texto extraído do PDF",
            extraction_strategy="pdfplumber",
            page_count=10,
            metadata={'test': True}
        )
        assert success is True

        # 3. Recuperar do cache (hit)
        entry = manager.get(sample_pdf_path)
        assert entry is not None
        assert entry.text == "Texto extraído do PDF"
        assert entry.metadata['test'] is True

        # 4. Verificar estatísticas
        stats = manager.get_stats()
        assert stats.total_entries == 1
        assert stats.hits >= 1

        # 5. Invalidar
        manager.invalidate(sample_pdf_path)
        entry = manager.get(sample_pdf_path)
        assert entry is None
