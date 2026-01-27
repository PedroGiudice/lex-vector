"""
Testes para SecaoDetector e HeuristicSectionAnalyzer.
"""

import pytest

from src.core.intelligence.peca_patterns import SecaoPatternConfig, SecaoType, get_default_config
from src.core.intelligence.secao_detector import SecaoDetector
from src.analyzers.heuristic_section_analyzer import HeuristicSectionAnalyzer
from src.analyzers.output_schemas import OutputFormat


class TestSecaoDetector:
    """Testes para SecaoDetector."""

    @pytest.fixture
    def detector(self):
        return SecaoDetector(config=get_default_config())

    def test_detect_peticao_inicial(self, detector):
        """Texto com enderecamento deve detectar PETICAO."""
        text = """
EXCELENTISSIMO SENHOR DOUTOR JUIZ DE DIREITO

Fulano de Tal vem propor a presente acao.
"""
        result = detector.detect(text)
        assert result["total_boundaries"] == 1
        assert result["boundaries"][0]["secao_type"] == "peticao"
        assert result["boundaries"][0]["confidence"] >= 0.80

    def test_detect_contestacao(self, detector):
        """Texto com CONTESTACAO deve detectar PETICAO (manifestacao da parte)."""
        text = """
CONTESTACAO

O requerido vem apresentar sua defesa.

EM PRELIMINAR
Alega ilegitimidade.
"""
        result = detector.detect(text)
        assert result["total_boundaries"] == 1
        assert result["boundaries"][0]["secao_type"] == "peticao"

    def test_detect_sentenca(self, detector):
        """Texto com SENTENCA deve detectar DECISAO."""
        text = """
SENTENCA

Vistos e examinados os autos.

JULGO PROCEDENTE o pedido.

P.R.I.
"""
        result = detector.detect(text)
        assert result["total_boundaries"] == 1
        assert result["boundaries"][0]["secao_type"] == "decisao"
        assert result["boundaries"][0]["confidence"] >= 0.90

    def test_detect_multiple_boundaries(self, detector):
        """Documento com multiplas pecas deve detectar os principais."""
        text = """
EXCELENTISSIMO SENHOR DOUTOR JUIZ

Peticao inicial aqui.

CONTESTACAO

Defesa aqui.

SENTENCA

Decisao aqui.
"""
        result = detector.detect(text)
        # Comportamento conservador: pode agrupar secoes proximas
        assert result["total_boundaries"] >= 2
        types = [b["secao_type"] for b in result["boundaries"]]
        assert "peticao" in types
        assert "decisao" in types

    def test_detect_with_segments(self, detector):
        """detect_with_segments deve retornar segmentos corretos."""
        text = """
EXCELENTISSIMO SENHOR DOUTOR JUIZ

Conteudo da peticao.

SENTENCA

Conteudo da sentenca.
"""
        _, segments = detector.detect_with_segments(text)
        assert len(segments) >= 2

        # Verificar que cada segmento tem conteudo
        for seg in segments:
            assert "content" in seg
            assert "secao_type" in seg
            assert "confidence" in seg

    def test_disabled_config(self):
        """Com config desabilitada, nao deve detectar boundaries."""
        from src.core.intelligence.peca_patterns import get_disabled_config

        detector = SecaoDetector(config=get_disabled_config())
        text = """
EXCELENTISSIMO SENHOR DOUTOR JUIZ

Texto aqui.

SENTENCA

Mais texto.
"""
        result = detector.detect(text)
        assert result["total_boundaries"] == 0


class TestHeuristicSectionAnalyzer:
    """Testes para HeuristicSectionAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        return HeuristicSectionAnalyzer()

    def test_analyze_simple_document(self, analyzer):
        """Documento simples deve ser analisado corretamente."""
        text = """
EXCELENTISSIMO SENHOR DOUTOR JUIZ

Peticao inicial de cobranca.

DOS PEDIDOS
Requer a procedencia.
"""
        doc = analyzer.analyze(text, document_id="test_001")
        assert doc.metadata.doc_id == "test_001"
        assert doc.metadata.total_secoes >= 1
        assert len(doc.secoes) >= 1

    def test_analyze_multi_section_document(self, analyzer):
        """Documento com multiplas secoes deve ser separado."""
        text = """
EXCELENTISSIMO SENHOR DOUTOR JUIZ

Peticao inicial.

CONTESTACAO

Defesa do reu.

SENTENCA

JULGO PROCEDENTE.
"""
        doc = analyzer.analyze(text, document_id="test_002", sistema="PJE")
        assert doc.metadata.sistema == "PJE"
        # Comportamento conservador: pode agrupar secoes proximas
        assert doc.metadata.total_secoes >= 2

        tipos = [s.tipo.value for s in doc.secoes]
        assert "peticao" in tipos
        assert "decisao" in tipos

    def test_to_markdown_xml(self, analyzer):
        """Output Markdown+XML deve ter formato correto."""
        text = """
SENTENCA

JULGO PROCEDENTE o pedido.
"""
        doc = analyzer.analyze(text, document_id="test_003")
        output = doc.to_markdown_xml()

        # Verificar YAML frontmatter
        assert output.startswith("---")
        assert "doc_id: test_003" in output
        assert "total_secoes:" in output

        # Verificar tags XML
        assert '<secao tipo="decisao"' in output
        assert "</secao>" in output

    def test_to_json_structured(self, analyzer):
        """Output JSON deve ter estrutura correta."""
        text = """
SENTENCA

JULGO PROCEDENTE.
"""
        doc = analyzer.analyze(text, document_id="test_004")
        json_output = doc.to_json_structured()

        assert "metadata" in json_output
        assert "secoes" in json_output
        assert "summary" in json_output
        assert json_output["metadata"]["doc_id"] == "test_004"

    def test_analyze_to_format_markdown_xml(self, analyzer):
        """analyze_to_format com MARKDOWN_XML deve funcionar."""
        text = "SENTENCA\n\nJULGO PROCEDENTE."
        output = analyzer.analyze_to_format(
            text,
            output_format=OutputFormat.MARKDOWN_XML,
            document_id="test_005"
        )
        assert "---" in output
        assert "<secao" in output

    def test_analyze_to_format_json(self, analyzer):
        """analyze_to_format com JSON deve funcionar."""
        text = "SENTENCA\n\nJULGO PROCEDENTE."
        output = analyzer.analyze_to_format(
            text,
            output_format=OutputFormat.JSON,
            document_id="test_006"
        )
        import json
        parsed = json.loads(output)
        assert "metadata" in parsed
        assert "secoes" in parsed

    def test_analyze_legacy_compatibility(self, analyzer):
        """analyze_legacy deve retornar list[Section]."""
        text = """
EXCELENTISSIMO SENHOR DOUTOR JUIZ

Peticao inicial.

SENTENCA

Decisao.
"""
        sections = analyzer.analyze_legacy(text, document_id="test_007")
        assert isinstance(sections, list)
        assert len(sections) >= 2

        # Verificar que e Section do modulo legado
        for section in sections:
            assert hasattr(section, "type")
            assert hasattr(section, "content")
            assert hasattr(section, "start_pos")
            assert hasattr(section, "end_pos")
            assert hasattr(section, "confidence")
