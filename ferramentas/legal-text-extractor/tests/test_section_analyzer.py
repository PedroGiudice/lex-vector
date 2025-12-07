"""Testes para análise de seções"""
import pytest
from src.analyzers.section_analyzer import SectionAnalyzer, Section


# Skip todos os testes desta classe - SectionAnalyzer depende de API Claude
# Decisão arquitetural: pipeline deve ser 100% local (Python/OpenCV/Tesseract)
# Ver: docs/session-memories/session-memory-2025-11-24-legal-text-extractor-refatoracao-pipeline.md
@pytest.mark.skip(reason="SectionAnalyzer usa Claude API - descartado por decisão arquitetural (custo proibitivo)")
class TestSectionAnalyzer:
    """Test suite para análise de seções (LEGACY - usa Claude API)"""

    @pytest.fixture
    def analyzer(self):
        """Cria instância do analyzer"""
        return SectionAnalyzer()

    def test_analyze_returns_sections(self, analyzer):
        """Testa que analyze retorna lista de Section"""
        text = "Petição inicial\nConteúdo da petição"
        sections = analyzer.analyze(text)
        assert isinstance(sections, list)
        assert len(sections) > 0
        assert all(isinstance(s, Section) for s in sections)

    def test_section_has_required_fields(self, analyzer):
        """Testa que Section tem todos os campos"""
        text = "Documento"
        sections = analyzer.analyze(text)
        section = sections[0]
        assert hasattr(section, "type")
        assert hasattr(section, "content")
        assert hasattr(section, "start_pos")
        assert hasattr(section, "end_pos")
        assert hasattr(section, "confidence")

    def test_single_section_fallback(self, analyzer):
        """Testa fallback para seção única"""
        text = "Documento simples"
        sections = analyzer.analyze(text)
        assert len(sections) == 1
        assert sections[0].type == "documento_completo"
        assert sections[0].content == text
