"""
Testes para Step 04 com Gemini.

Testes unitários não requerem Gemini CLI.
Testes de integração (marcados com @pytest.mark.integration) requerem Gemini CLI configurado.

Para rodar apenas testes unitários:
    pytest tests/test_step_04_gemini.py -v -k "not integration"

Para rodar todos os testes (requer Gemini):
    pytest tests/test_step_04_gemini.py -v
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

# Tenta importar os módulos - pode falhar se dependências não estão instaladas
try:
    from src.gemini import GeminiClient, GeminiConfig, GeminiResponse
    from src.gemini.prompts import (
        CLASSIFICATION_PROMPT,
        TAXONOMY_DESCRIPTION,
        build_classification_prompt,
        build_cleaning_prompt,
    )
    from src.gemini.schemas import (
        ClassificationResult,
        CleanedSection,
        CleaningResult,
        PecaType,
        SectionClassification,
    )

    IMPORTS_OK = True
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERROR = str(e)


# Skip all tests if imports fail
pytestmark = pytest.mark.skipif(
    not IMPORTS_OK, reason=f"Imports failed: {IMPORT_ERROR if not IMPORTS_OK else ''}"
)


class TestGeminiClient:
    """Testes do cliente Gemini."""

    def test_extract_json_from_code_block(self):
        """Testa extração de JSON de code blocks markdown."""
        text = """
        Aqui está o resultado:
        ```json
        {"key": "value", "number": 42}
        ```
        Fim.
        """
        result = GeminiClient._extract_json(text)
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["number"] == 42

    def test_extract_json_raw(self):
        """Testa extração de JSON sem code block."""
        text = 'Resultado: {"doc_id": "test", "sections": []} fim.'
        result = GeminiClient._extract_json(text)
        parsed = json.loads(result)
        assert parsed["doc_id"] == "test"

    def test_extract_json_with_array(self):
        """Testa extração de array JSON."""
        text = "Lista: [1, 2, 3] aqui."
        result = GeminiClient._extract_json(text)
        parsed = json.loads(result)
        assert parsed == [1, 2, 3]

    def test_extract_json_no_json(self):
        """Testa que texto sem JSON retorna original."""
        text = "Texto sem JSON"
        result = GeminiClient._extract_json(text)
        assert result == text

    def test_config_defaults(self):
        """Verifica configuração padrão."""
        config = GeminiConfig()
        assert config.model == "gemini-2.5-flash"
        assert config.timeout_seconds == 300
        assert config.max_retries == 2

    def test_response_success(self):
        """Testa criação de resposta de sucesso."""
        response = GeminiResponse(
            text='{"result": "ok"}',
            success=True,
            model_used="gemini-2.5-flash",
        )
        assert response.success
        assert response.error is None

    def test_response_failure(self):
        """Testa criação de resposta de erro."""
        response = GeminiResponse(
            text="",
            success=False,
            error="API timeout",
        )
        assert not response.success
        assert response.error == "API timeout"


class TestSchemas:
    """Testes dos schemas Pydantic."""

    def test_peca_type_enum_count(self):
        """Verifica que temos exatamente 12 categorias."""
        assert len(PecaType) == 12

    def test_peca_type_values(self):
        """Verifica que todos os valores esperados existem."""
        expected = [
            "PETICAO_INICIAL",
            "CONTESTACAO",
            "REPLICA",
            "DECISAO_JUDICIAL",
            "DESPACHO",
            "RECURSO",
            "PARECER_MP",
            "ATA_TERMO",
            "CERTIDAO",
            "ANEXOS",
            "CAPA_DADOS",
            "INDETERMINADO",
        ]
        actual = [p.value for p in PecaType]
        assert sorted(actual) == sorted(expected)

    def test_section_classification_valid(self):
        """Testa criação de SectionClassification válida."""
        section = SectionClassification(
            section_id=1,
            type=PecaType.PETICAO_INICIAL,
            title="Petição Inicial",
            start_page=1,
            end_page=10,
            confidence=0.95,
            reasoning="Começa com Excelentíssimo",
        )
        assert section.type == PecaType.PETICAO_INICIAL
        assert section.confidence == 0.95
        assert section.start_page == 1
        assert section.end_page == 10

    def test_section_classification_invalid_pages(self):
        """Testa validação de páginas (end < start)."""
        with pytest.raises(ValueError, match="end_page"):
            SectionClassification(
                section_id=1,
                type=PecaType.PETICAO_INICIAL,
                title="Test",
                start_page=10,
                end_page=5,  # Inválido
                confidence=0.9,
                reasoning="Test",
            )

    def test_section_classification_invalid_confidence(self):
        """Testa validação de confidence fora do range."""
        with pytest.raises(ValueError):
            SectionClassification(
                section_id=1,
                type=PecaType.PETICAO_INICIAL,
                title="Test",
                start_page=1,
                end_page=5,
                confidence=1.5,  # Inválido: > 1.0
                reasoning="Test",
            )

    def test_classification_result_valid(self):
        """Testa criação de ClassificationResult válido."""
        sections = [
            SectionClassification(
                section_id=1,
                type=PecaType.PETICAO_INICIAL,
                title="PI",
                start_page=1,
                end_page=5,
                confidence=0.9,
                reasoning="Test",
            ),
            SectionClassification(
                section_id=2,
                type=PecaType.CONTESTACAO,
                title="Contestação",
                start_page=6,
                end_page=10,
                confidence=0.85,
                reasoning="Test",
            ),
        ]
        result = ClassificationResult(
            doc_id="test",
            total_pages=10,
            total_sections=2,
            sections=sections,
            summary="Processo trabalhista",
        )
        assert result.total_sections == 2
        assert len(result.sections) == 2

    def test_classification_result_invalid_section_count(self):
        """Testa validação de total_sections inconsistente."""
        section = SectionClassification(
            section_id=1,
            type=PecaType.PETICAO_INICIAL,
            title="Test",
            start_page=1,
            end_page=5,
            confidence=0.9,
            reasoning="Test",
        )
        with pytest.raises(ValueError, match="total_sections"):
            ClassificationResult(
                doc_id="test",
                total_pages=10,
                total_sections=5,  # Inconsistente com 1 seção
                sections=[section],
                summary="Test",
            )

    def test_classification_result_non_sequential_ids(self):
        """Testa validação de section_ids não sequenciais."""
        sections = [
            SectionClassification(
                section_id=1,
                type=PecaType.PETICAO_INICIAL,
                title="PI",
                start_page=1,
                end_page=5,
                confidence=0.9,
                reasoning="Test",
            ),
            SectionClassification(
                section_id=3,  # Deveria ser 2
                type=PecaType.CONTESTACAO,
                title="Contestação",
                start_page=6,
                end_page=10,
                confidence=0.85,
                reasoning="Test",
            ),
        ]
        with pytest.raises(ValueError, match="sequenciais"):
            ClassificationResult(
                doc_id="test",
                total_pages=10,
                total_sections=2,
                sections=sections,
                summary="Test",
            )

    def test_cleaned_section_truncates_noise(self):
        """Testa que noise_removed é truncado para 5 items."""
        section = CleanedSection(
            section_id=1,
            type=PecaType.PETICAO_INICIAL,
            content="Texto limpo",
            noise_removed=["a", "b", "c", "d", "e", "f", "g", "h"],  # 8 items
        )
        assert len(section.noise_removed) == 5

    def test_cleaning_result_valid(self):
        """Testa criação de CleaningResult válido."""
        result = CleaningResult(
            doc_id="test",
            sections=[],
            total_chars_original=1000,
            total_chars_cleaned=800,
            reduction_percent=20.0,
        )
        assert result.reduction_percent == 20.0


class TestPrompts:
    """Testes dos prompts."""

    def test_classification_prompt_exists(self):
        """Verifica que CLASSIFICATION_PROMPT existe e não é vazio."""
        assert CLASSIFICATION_PROMPT
        assert len(CLASSIFICATION_PROMPT) > 1000

    def test_taxonomy_description_has_all_categories(self):
        """Verifica que taxonomia menciona todas as 12 categorias."""
        for peca in PecaType:
            assert peca.value in TAXONOMY_DESCRIPTION

    def test_build_classification_prompt_replaces_doc_id(self):
        """Testa que builder substitui doc_id."""
        prompt = build_classification_prompt("meu_documento_123")
        assert "meu_documento_123" in prompt

    def test_build_cleaning_prompt_includes_summary(self):
        """Testa que builder inclui resumo da classificação."""
        summary = "Seção 1: PETICAO_INICIAL (páginas 1-10)"
        prompt = build_cleaning_prompt(summary)
        assert "PETICAO_INICIAL" in prompt
        assert "1-10" in prompt


class TestBibliotecarioConfig:
    """Testes da configuração do Bibliotecário."""

    @pytest.fixture(autouse=True)
    def setup_import(self):
        """Setup import direto do módulo para evitar import via __init__."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "step_04_classify",
            Path(__file__).parent.parent / "src" / "steps" / "step_04_classify.py",
        )
        self.step04_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(self.step04_module)
            self.BibliotecarioConfig = self.step04_module.BibliotecarioConfig
            self.GeminiBibliotecario = self.step04_module.GeminiBibliotecario
        except Exception as e:
            pytest.skip(f"Could not import step_04_classify: {e}")

    def test_default_config(self):
        """Testa valores padrão da configuração."""
        config = self.BibliotecarioConfig()
        assert config.model == "gemini-2.5-flash"
        assert config.timeout_seconds == 300
        assert config.skip_cleaning is False
        assert config.generate_cleaned_md is True
        assert config.min_confidence == 0.3

    def test_custom_config(self):
        """Testa configuração customizada."""
        config = self.BibliotecarioConfig(
            model="gemini-2.5-pro",
            skip_cleaning=True,
            min_confidence=0.5,
        )
        assert config.model == "gemini-2.5-pro"
        assert config.skip_cleaning is True


class TestGeminiBibliotecario:
    """Testes do Bibliotecário (com mocks)."""

    @pytest.fixture(autouse=True)
    def setup_import(self):
        """Setup import direto do módulo."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "step_04_classify",
            Path(__file__).parent.parent / "src" / "steps" / "step_04_classify.py",
        )
        self.step04_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(self.step04_module)
            self.BibliotecarioConfig = self.step04_module.BibliotecarioConfig
            self.GeminiBibliotecario = self.step04_module.GeminiBibliotecario
        except Exception as e:
            pytest.skip(f"Could not import step_04_classify: {e}")

    def test_file_not_found(self, tmp_path):
        """Testa erro quando arquivo não existe."""
        config = self.BibliotecarioConfig()

        with patch.object(self.step04_module, "GeminiClient"):
            bibliotecario = self.GeminiBibliotecario(config=config)

            with pytest.raises(FileNotFoundError):
                bibliotecario.process(tmp_path / "nonexistent.md")

    def test_build_tagged_markdown(self):
        """Testa geração de markdown com tags semânticas."""

        # Classificação mock
        sections = [
            SectionClassification(
                section_id=1,
                type=PecaType.PETICAO_INICIAL,
                title="Petição Inicial",
                start_page=1,
                end_page=2,
                confidence=0.95,
                reasoning="Test",
            ),
        ]
        classification = ClassificationResult(
            doc_id="test",
            total_pages=2,
            total_sections=1,
            sections=sections,
            summary="Test",
        )

        original = """## [[PAGE_001]] [TYPE: NATIVE]
Conteúdo da página 1

## [[PAGE_002]] [TYPE: NATIVE]
Conteúdo da página 2
"""

        config = self.BibliotecarioConfig()
        with patch.object(self.step04_module, "GeminiClient"):
            bibliotecario = self.GeminiBibliotecario(config=config)
            result = bibliotecario._build_tagged_markdown(original, classification)

        assert "[SEMANTIC: PETICAO_INICIAL]" in result
        assert "[CONF: 0.95]" in result
        assert "SEÇÃO 1: PETICAO_INICIAL" in result


# =============================================================================
# Testes de Integração (requerem Gemini CLI)
# =============================================================================


@pytest.mark.integration
class TestIntegration:
    """
    Testes de integração que requerem Gemini CLI configurado.

    Para rodar: pytest tests/test_step_04_gemini.py -v -m integration
    """

    @pytest.fixture
    def sample_md(self, tmp_path):
        """Cria arquivo markdown de teste simples."""
        content = """## [[PAGE_001]] [TYPE: NATIVE]
EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA VARA DO TRABALHO

JOÃO DA SILVA, brasileiro, casado, portador do CPF nº 123.456.789-00,
vem respeitosamente à presença de Vossa Excelência propor a presente
RECLAMAÇÃO TRABALHISTA em face de EMPRESA XYZ LTDA.

DOS FATOS

O reclamante foi admitido pela reclamada em 01/01/2020 para exercer
a função de auxiliar administrativo, com salário de R$ 2.000,00.

## [[PAGE_002]] [TYPE: NATIVE]
DOS PEDIDOS

Ante o exposto, requer:

a) A procedência total dos pedidos;
b) A condenação da reclamada ao pagamento das verbas rescisórias;
c) Honorários advocatícios.

Nestes termos, pede deferimento.

São Paulo, 10 de dezembro de 2025.

ADVOGADO DA SILVA
OAB/SP 123.456
"""
        md_path = tmp_path / "test_doc" / "final.md"
        md_path.parent.mkdir(parents=True)
        md_path.write_text(content, encoding="utf-8")
        return md_path

    def test_gemini_cli_available(self):
        """Verifica que Gemini CLI está disponível."""
        try:
            client = GeminiClient()
            assert client is not None
        except RuntimeError as e:
            pytest.skip(f"Gemini CLI não disponível: {e}")

    def test_full_classification(self, sample_md):
        """Teste completo de classificação (requer Gemini)."""
        from src.steps.step_04_classify import BibliotecarioConfig, GeminiBibliotecario

        try:
            config = BibliotecarioConfig(skip_cleaning=True)
            bibliotecario = GeminiBibliotecario(config=config)

            result = bibliotecario.process(sample_md)

            # Verificações básicas
            assert result["classification"].total_sections >= 1
            assert (sample_md.parent / "semantic_structure.json").exists()
            assert (sample_md.parent / "final_tagged.md").exists()

            # Verifica que classificou como petição inicial
            types = [s.type for s in result["classification"].sections]
            assert PecaType.PETICAO_INICIAL in types

        except RuntimeError as e:
            if "Gemini" in str(e):
                pytest.skip(f"Gemini CLI não disponível: {e}")
            raise
