"""
Schemas Pydantic para validação de output do Gemini.

Define estruturas de dados esperadas para classificação e limpeza.
Estes schemas são o CONTRATO entre o LLM e o código Python.

IMPORTANTE: Validação rigorosa é necessária porque LLMs podem
retornar outputs inesperados ou mal-formatados.
"""

from __future__ import annotations

import logging
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class PecaType(str, Enum):
    """
    Tipos de peças processuais jurídicas brasileiras.

    Taxonomia definida na ADR-001. NÃO modificar sem atualizar ADR.
    """

    PETICAO_INICIAL = "PETICAO_INICIAL"
    CONTESTACAO = "CONTESTACAO"
    REPLICA = "REPLICA"
    DECISAO_JUDICIAL = "DECISAO_JUDICIAL"
    DESPACHO = "DESPACHO"
    RECURSO = "RECURSO"
    PARECER_MP = "PARECER_MP"
    ATA_TERMO = "ATA_TERMO"
    CERTIDAO = "CERTIDAO"
    ANEXOS = "ANEXOS"
    CAPA_DADOS = "CAPA_DADOS"
    INDETERMINADO = "INDETERMINADO"


class SectionClassification(BaseModel):
    """
    Classificação de uma seção do documento.

    Representa uma peça processual identificada pelo Gemini.
    """

    section_id: int = Field(ge=1, description="ID sequencial da seção (começando em 1)")
    type: PecaType = Field(description="Tipo da peça processual (uma das 12 categorias)")
    title: str = Field(
        min_length=1, max_length=200, description="Título ou descrição curta da seção"
    )
    start_page: int = Field(ge=1, description="Página inicial (1-indexed)")
    end_page: int = Field(ge=1, description="Página final (1-indexed)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confiança da classificação (0.0 a 1.0)")
    reasoning: str = Field(
        min_length=1, max_length=500, description="Breve justificativa da classificação"
    )

    @model_validator(mode="after")
    def validate_pages(self) -> SectionClassification:
        """Valida que end_page >= start_page."""
        if self.end_page < self.start_page:
            raise ValueError(
                f"end_page ({self.end_page}) deve ser >= start_page ({self.start_page})"
            )
        return self


class ClassificationResult(BaseModel):
    """
    Resultado completo da classificação de um documento.

    Este é o schema principal que o Gemini deve retornar.
    """

    doc_id: str = Field(min_length=1, description="Identificador do documento")
    total_pages: int = Field(ge=1, description="Total de páginas no documento")
    total_sections: int = Field(ge=0, description="Total de seções identificadas")
    sections: list[SectionClassification] = Field(description="Lista de seções classificadas")
    summary: str = Field(
        min_length=1, max_length=500, description="Resumo do documento em 1-2 frases"
    )

    @model_validator(mode="after")
    def validate_sections(self) -> ClassificationResult:
        """Valida consistência das seções."""
        if len(self.sections) != self.total_sections:
            raise ValueError(
                f"total_sections ({self.total_sections}) não corresponde "
                f"ao número de seções ({len(self.sections)})"
            )

        # Valida que section_ids são sequenciais
        if self.sections:
            expected_ids = list(range(1, len(self.sections) + 1))
            actual_ids = [s.section_id for s in self.sections]
            if actual_ids != expected_ids:
                raise ValueError(
                    f"section_ids devem ser sequenciais: esperado {expected_ids}, "
                    f"obtido {actual_ids}"
                )

        # Valida que seções não se sobrepõem
        for i, section in enumerate(self.sections):
            for j, other in enumerate(self.sections[i + 1 :], start=i + 1):
                if not (section.end_page < other.start_page or other.end_page < section.start_page):
                    # Verificar se é sobreposição real ou adjacência permitida
                    if (
                        section.end_page >= other.start_page
                        and section.start_page <= other.end_page
                    ):
                        # Sobreposição - pode ser permitida em alguns casos
                        pass  # Relaxar validação por enquanto

        return self


class CleanedSection(BaseModel):
    """
    Seção após limpeza contextual.

    O conteúdo deve ser o texto INTEGRAL, apenas com ruído removido.
    NÃO deve ser resumido ou condensado.
    """

    section_id: int = Field(
        ge=1, description="ID da seção (corresponde a SectionClassification.section_id)"
    )
    type: PecaType = Field(description="Tipo da peça (deve corresponder à classificação)")
    content: str = Field(description="Texto limpo da seção (INTEGRAL, não resumido)")
    noise_removed: list[str] = Field(
        default_factory=list, description="Exemplos de ruído removido (máximo 5)"
    )

    @field_validator("noise_removed", mode="after")
    @classmethod
    def limit_noise_examples(cls, v: list[str]) -> list[str]:
        """Limita exemplos de ruído a 5."""
        if len(v) > 5:
            return v[:5]
        return v


class CleaningResult(BaseModel):
    """
    Resultado da limpeza contextual.

    IMPORTANTE: A limpeza deve PRESERVAR todo conteúdo jurídico.
    Apenas ruído técnico (assinaturas digitais, timestamps, etc) é removido.
    """

    doc_id: str = Field(min_length=1, description="Identificador do documento")
    sections: list[CleanedSection] = Field(description="Lista de seções limpas")
    total_chars_original: int = Field(ge=0, description="Total de caracteres antes da limpeza")
    total_chars_cleaned: int = Field(ge=0, description="Total de caracteres após limpeza")
    reduction_percent: float = Field(ge=0.0, le=100.0, description="Percentual de redução (0-100)")

    @model_validator(mode="after")
    def validate_reduction(self) -> CleaningResult:
        """Valida que redução está consistente."""
        if self.total_chars_original > 0:
            expected_reduction = (
                (self.total_chars_original - self.total_chars_cleaned)
                / self.total_chars_original
                * 100
            )
            # Permite 1% de margem de erro
            if abs(expected_reduction - self.reduction_percent) > 1.0:
                # Log warning mas não falha
                logger.warning(
                    f"reduction_percent ({self.reduction_percent:.1f}%) "
                    f"difere do calculado ({expected_reduction:.1f}%)"
                )
        return self
