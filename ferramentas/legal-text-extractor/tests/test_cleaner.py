"""Testes para limpeza de documentos"""
import pytest
from src.core.cleaner import DocumentCleaner


class TestDocumentCleaner:
    """Test suite para limpeza de documentos"""

    @pytest.fixture
    def cleaner(self):
        """Cria instância do cleaner"""
        return DocumentCleaner()

    def test_remove_headers(self, cleaner):
        """Testa remoção de cabeçalhos"""
        text = "Página 1 de 10\nConteúdo importante\nPágina 2 de 10"
        result = cleaner.clean(text)
        assert "Página" not in result.text
        assert "Conteúdo importante" in result.text

    def test_remove_footers(self, cleaner):
        """Testa remoção de assinaturas digitais (padrão completo)"""
        text = "Texto importante do documento\nAssinado digitalmente por: JUIZ FEDERAL FULANO DE TAL\nMais texto do documento aqui"
        result = cleaner.clean(text)
        # O padrão exige "assinado digitalmente por:" seguido de 5-100 chars
        assert "JUIZ FEDERAL FULANO DE TAL" not in result.text
        assert "Texto importante" in result.text
        assert "Mais texto" in result.text

    def test_statistics(self, cleaner):
        """Testa estatísticas de limpeza"""
        text = "A" * 1000 + "\nPágina 1 de 10\n" + "B" * 500
        result = cleaner.clean(text)
        assert result.stats.original_length > result.stats.final_length
        assert result.stats.reduction_pct > 0
