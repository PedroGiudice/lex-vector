"""
Testes para deteccao de boundaries entre documentos.

FILOSOFIA DOS TESTES:
1. FALSO NEGATIVO > FALSO POSITIVO
   - Preferimos NAO detectar um boundary real
   - Do que detectar errado e CORTAR um documento

2. Testes de PRESERVACAO sao mais importantes que testes de DETECCAO
   - Garantir que nada foi cortado e prioritario
   - Deteccao correta e secundario

Referencia: docs/ARCHITECTURE_PRINCIPLES.md
"""

from __future__ import annotations

import pytest

from src.core.intelligence.boundary_config import (
    BoundaryConfig,
    BoundaryPattern,
    DocumentClass,
    get_conservative_config,
    get_disabled_config,
    get_formal_document_config,
    get_compact_document_config,
)
from src.core.intelligence.boundary_detector import (
    BoundaryDetector,
    detect_boundaries_conservative,
    has_boundary_markers,
)


# =============================================================================
# FIXTURES DE TESTE
# =============================================================================


TEXTO_SEM_BOUNDARIES = """
Este e um texto simples sem nenhum marcador de boundary.
Ele deve ser tratado como um unico documento.
Nenhuma separacao deve ocorrer.
Fim do texto.
"""

TEXTO_COM_DOC_NUMERADO = """
Primeira parte do documento principal.

DOC. 1

Este e o primeiro anexo numerado.
Contem informacoes importantes.

DOC. 2

Este e o segundo anexo.
Tambem contem informacoes.
"""

TEXTO_COM_PROCURACAO = """
Peticao inicial aqui.
Muitas paginas de argumentacao.
Nestes termos, pede deferimento.

PROCURACAO AD JUDICIA

Pelo presente instrumento particular de procuracao,
o outorgante nomeia e constitui seu bastante procurador
o advogado abaixo qualificado.

Poderes: Para o foro em geral.
"""

TEXTO_MULTIPLOS_BOUNDARIES = """
Parte inicial sem tipo definido.

DOC. 1 - Contrato

CONTRATO DE PRESTACAO DE SERVICOS

Pelo presente instrumento particular, as partes
acordam os seguintes termos:

Clausula 1 - Objeto
Clausula 2 - Prazo
Clausula 3 - Valor

DOC. 2 - Procuracao

PROCURACAO AD JUDICIA

Poderes especiais para representar em juizo.
"""

TEXTO_COM_BOLETO = """
Dados do processo judicial.

BOLETO BANCARIO

Beneficiario: Empresa XYZ
Valor: R$ 1.000,00
Vencimento: 25/11/2025
Codigo de barras: 12345.67890 12345.678901 12345.678901 1 12340000100000
"""


# =============================================================================
# TESTES DE CONFIGURACAO
# =============================================================================


class TestBoundaryConfig:
    """Testes para BoundaryConfig."""

    def test_config_padrao_e_conservadora(self):
        """Config padrao deve ter confidence alta (conservadora)."""
        config = get_conservative_config()
        assert config.min_confidence >= 0.8
        assert config.enabled is True

    def test_config_disabled_nao_detecta(self):
        """Config disabled deve impedir qualquer deteccao."""
        config = get_disabled_config()
        assert config.enabled is False

    def test_config_formal_menos_restritiva(self):
        """Config formal pode ter confidence menor."""
        formal = get_formal_document_config()
        conserv = get_conservative_config()
        assert formal.min_confidence <= conserv.min_confidence

    def test_config_compact_mais_restritiva(self):
        """Config compact deve ser mais restritiva."""
        compact = get_compact_document_config()
        conserv = get_conservative_config()
        assert compact.min_confidence >= conserv.min_confidence

    def test_adjust_for_margin_estreita(self):
        """Margens estreitas devem aumentar threshold."""
        config = BoundaryConfig()
        original_confidence = config.min_confidence

        config.adjust_for_margin(0.02)  # 2% margem (muito estreita)

        assert config.document_class == DocumentClass.COMPACT
        assert config.min_confidence >= original_confidence

    def test_adjust_for_margin_larga(self):
        """Margens largas podem relaxar threshold."""
        config = BoundaryConfig()

        config.adjust_for_margin(0.20)  # 20% margem (larga)

        assert config.document_class == DocumentClass.FORMAL

    def test_patterns_default_existem(self):
        """Config deve ter patterns padrao."""
        config = BoundaryConfig()
        assert len(config.patterns) > 0

    def test_add_pattern_custom(self):
        """Deve permitir adicionar pattern customizado."""
        import re

        config = BoundaryConfig()
        initial_count = len(config.patterns)

        custom = BoundaryPattern(
            id="custom_test",
            regex=re.compile(r"^CUSTOM PATTERN", re.IGNORECASE),
            description="Pattern de teste",
            document_type="CUSTOM",
            confidence_base=0.9,
        )
        config.add_pattern(custom)

        assert len(config.patterns) == initial_count + 1


# =============================================================================
# TESTES DE DETECCAO
# =============================================================================


class TestBoundaryDetector:
    """Testes para BoundaryDetector."""

    def test_texto_sem_boundaries_retorna_unico_segmento(self):
        """Texto sem marcadores deve retornar um unico segmento."""
        detector = BoundaryDetector()
        result = detector.detect(TEXTO_SEM_BOUNDARIES)

        assert result["total_boundaries"] == 0
        assert len(result["segments"]) == 1
        assert result["segments"][0]["document_type"] == "UNKNOWN"

    def test_detecta_doc_numerado(self):
        """Deve detectar marcadores DOC. X."""
        detector = BoundaryDetector()
        result = detector.detect(TEXTO_COM_DOC_NUMERADO)

        assert result["total_boundaries"] >= 2  # DOC. 1 e DOC. 2

        # Verifica que boundaries tem tipo correto
        doc_types = [b["document_type"] for b in result["boundaries"]]
        assert "ANEXO_NUMERADO" in doc_types

    def test_detecta_procuracao(self):
        """Deve detectar inicio de procuracao."""
        detector = BoundaryDetector()
        result = detector.detect(TEXTO_COM_PROCURACAO)

        assert result["total_boundaries"] >= 1

        # Verifica tipo
        doc_types = [b["document_type"] for b in result["boundaries"]]
        assert "PROCURACAO" in doc_types

    def test_detecta_multiplos_boundaries(self):
        """Deve detectar multiplos boundaries em sequencia."""
        detector = BoundaryDetector()
        result = detector.detect(TEXTO_MULTIPLOS_BOUNDARIES)

        # Deve detectar DOC. 1, CONTRATO, DOC. 2, PROCURACAO
        assert result["total_boundaries"] >= 2

    def test_segmentos_nao_sobrepoem(self):
        """Segmentos nao devem ter sobreposicao de linhas."""
        detector = BoundaryDetector()
        result = detector.detect(TEXTO_MULTIPLOS_BOUNDARIES)

        for i in range(len(result["segments"]) - 1):
            current = result["segments"][i]
            next_seg = result["segments"][i + 1]

            # Fim do atual deve ser antes do inicio do proximo
            assert current["end_line"] < next_seg["start_line"]

    def test_segmentos_cobrem_todo_texto(self):
        """Segmentos devem cobrir todas as linhas do texto."""
        detector = BoundaryDetector()
        result = detector.detect(TEXTO_MULTIPLOS_BOUNDARIES)

        lines = TEXTO_MULTIPLOS_BOUNDARIES.split("\n")
        total_lines = len(lines)

        # Primeiro segmento comeca em 1
        first = result["segments"][0]
        assert first["start_line"] == 1

        # Ultimo segmento termina na ultima linha
        last = result["segments"][-1]
        assert last["end_line"] == total_lines

    def test_config_disabled_retorna_unico_segmento(self):
        """Com config disabled, deve retornar sempre um segmento."""
        config = get_disabled_config()
        detector = BoundaryDetector(config=config)

        result = detector.detect(TEXTO_MULTIPLOS_BOUNDARIES)

        assert result["total_boundaries"] == 0
        assert len(result["segments"]) == 1


# =============================================================================
# TESTES DE PRESERVACAO (MAIS IMPORTANTES!)
# =============================================================================


class TestPreservacao:
    """
    Testes que garantem que NENHUM CONTEUDO e perdido.

    Estes sao os testes mais criticos - boundaries mal configurados
    podem LITERALMENTE comer pedacos de documento.
    """

    def test_todo_conteudo_preservado_sem_boundaries(self):
        """Sem boundaries, todo conteudo deve estar no segmento unico."""
        detector = BoundaryDetector()
        result = detector.detect(TEXTO_SEM_BOUNDARIES)

        lines = TEXTO_SEM_BOUNDARIES.split("\n")
        segment = result["segments"][0]

        # Segmento deve incluir todas as linhas
        segment_line_count = segment["end_line"] - segment["start_line"] + 1
        assert segment_line_count == len(lines)

    def test_todo_conteudo_preservado_com_boundaries(self):
        """Com boundaries, soma dos segmentos deve cobrir tudo."""
        detector = BoundaryDetector()
        result = detector.detect(TEXTO_MULTIPLOS_BOUNDARIES)

        lines = TEXTO_MULTIPLOS_BOUNDARIES.split("\n")
        total_lines = len(lines)

        # Calcula total de linhas cobertas pelos segmentos
        covered_lines = set()
        for seg in result["segments"]:
            for line in range(seg["start_line"], seg["end_line"] + 1):
                covered_lines.add(line)

        # Todas as linhas de 1 a total_lines devem estar cobertas
        expected_lines = set(range(1, total_lines + 1))
        assert covered_lines == expected_lines, (
            f"Linhas faltando: {expected_lines - covered_lines}"
        )

    def test_nenhuma_linha_em_multiplos_segmentos(self):
        """Nenhuma linha pode pertencer a mais de um segmento."""
        detector = BoundaryDetector()
        result = detector.detect(TEXTO_MULTIPLOS_BOUNDARIES)

        line_to_segment: dict[int, int] = {}

        for seg_idx, seg in enumerate(result["segments"]):
            for line in range(seg["start_line"], seg["end_line"] + 1):
                if line in line_to_segment:
                    pytest.fail(
                        f"Linha {line} em segmentos {line_to_segment[line]} e {seg_idx}"
                    )
                line_to_segment[line] = seg_idx

    def test_texto_reconstruido_igual_original(self):
        """
        TESTE CRITICO: Texto reconstruido dos segmentos deve ser igual ao original.

        Este teste garante que podemos separar e depois juntar sem perda.
        """
        detector = BoundaryDetector()
        texto_original = TEXTO_MULTIPLOS_BOUNDARIES
        result = detector.detect(texto_original)

        lines = texto_original.split("\n")

        # Reconstroi texto a partir dos segmentos
        reconstructed_lines = []
        for seg in result["segments"]:
            # Linhas sao 1-indexed, lista e 0-indexed
            seg_lines = lines[seg["start_line"] - 1 : seg["end_line"]]
            reconstructed_lines.extend(seg_lines)

        # Compara
        reconstructed = "\n".join(reconstructed_lines)
        assert reconstructed == texto_original


# =============================================================================
# TESTES DE FUNCOES DE CONVENIENCIA
# =============================================================================


class TestFuncoesConveniencia:
    """Testes para funcoes auxiliares."""

    def test_detect_boundaries_conservative(self):
        """Funcao de conveniencia deve usar config conservadora."""
        result = detect_boundaries_conservative(TEXTO_COM_PROCURACAO)

        assert result["total_boundaries"] >= 1

    def test_has_boundary_markers_positivo(self):
        """Deve detectar presenca de marcadores."""
        assert has_boundary_markers(TEXTO_COM_DOC_NUMERADO) is True
        assert has_boundary_markers(TEXTO_COM_PROCURACAO) is True

    def test_has_boundary_markers_negativo(self):
        """Deve retornar False sem marcadores."""
        assert has_boundary_markers(TEXTO_SEM_BOUNDARIES) is False


# =============================================================================
# TESTES DE EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Testes para casos especiais."""

    def test_texto_vazio(self):
        """Texto vazio deve retornar segmento vazio."""
        detector = BoundaryDetector()
        result = detector.detect("")

        assert result["total_boundaries"] == 0
        assert len(result["segments"]) == 1

    def test_texto_uma_linha(self):
        """Texto com uma linha deve funcionar."""
        detector = BoundaryDetector()
        result = detector.detect("Uma unica linha")

        assert result["total_boundaries"] == 0
        assert result["segments"][0]["start_line"] == 1
        assert result["segments"][0]["end_line"] == 1

    def test_boundary_na_primeira_linha(self):
        """Boundary na primeira linha deve funcionar."""
        texto = "DOC. 1\nConteudo do documento"
        detector = BoundaryDetector()
        result = detector.detect(texto)

        # Primeiro segmento deve comecar na linha 1
        assert result["segments"][0]["start_line"] == 1

    def test_boundary_na_ultima_linha(self):
        """Boundary na ultima linha deve criar segmento minimo."""
        texto = "Conteudo inicial\nMais conteudo\nDOC. 1"
        detector = BoundaryDetector()
        result = detector.detect(texto)

        # Ultimo segmento deve terminar na linha 3
        last = result["segments"][-1]
        assert last["end_line"] == 3

    def test_boundaries_consecutivos(self):
        """Boundaries em linhas consecutivas devem ser deduplicados."""
        texto = "DOC. 1\nDOC. 2\nConteudo"
        detector = BoundaryDetector()
        result = detector.detect(texto)

        # Deve manter apenas um (deduplicacao por proximidade)
        # ou ambos se config permitir
        assert result["total_boundaries"] <= 2


# =============================================================================
# RUNNER
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
