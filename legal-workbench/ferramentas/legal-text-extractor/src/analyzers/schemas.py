"""Pydantic schemas para validação de responses da API Claude"""
from typing import Literal
from pydantic import BaseModel, Field, field_validator


# Tipos válidos de seções (sincronizado com prompt template)
SectionType = Literal[
    "petição_inicial",
    "contestação",
    "réplica",
    "sentença",
    "acórdão",
    "despacho",
    "decisão_interlocutória",
    "parecer_mp",
    "laudo_pericial",
    "ata_audiência",
    "procuração",
    "substabelecimento",
    "contrato",
    "documento_fiscal",
    "correspondência",
    "outro"
]


class SectionMetadata(BaseModel):
    """Metadados de uma seção identificada pelo Claude"""

    type: SectionType = Field(
        ...,
        description="Tipo da seção jurídica"
    )

    start_marker: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Texto que marca o início da seção (primeiras ~50 chars)"
    )

    end_marker: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Texto que marca o fim da seção (últimas ~50 chars)"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Nível de confiança na identificação (0.0 a 1.0)"
    )

    summary: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Resumo em 1 linha do conteúdo da seção"
    )

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Valida que confidence está no range correto"""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Confidence deve estar entre 0.0 e 1.0, recebido: {v}")
        return v

    @field_validator('start_marker', 'end_marker')
    @classmethod
    def validate_marker_not_empty(cls, v: str) -> str:
        """Valida que markers não são vazios ou só whitespace"""
        if not v.strip():
            raise ValueError("Marker não pode ser vazio ou apenas whitespace")
        return v.strip()


class ClaudeAnalysisResponse(BaseModel):
    """Schema de resposta completa do Claude para análise de seções"""

    sections: list[SectionMetadata] = Field(
        ...,
        min_length=1,
        description="Lista de seções identificadas no documento"
    )

    @field_validator('sections')
    @classmethod
    def validate_sections_not_empty(cls, v: list[SectionMetadata]) -> list[SectionMetadata]:
        """Valida que há pelo menos uma seção identificada"""
        if not v:
            raise ValueError("Deve haver pelo menos uma seção identificada")
        return v

    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
                "sections": [
                    {
                        "type": "petição_inicial",
                        "start_marker": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ...",
                        "end_marker": "...Nestes termos, pede deferimento.",
                        "confidence": 0.95,
                        "summary": "Petição inicial de ação de cobrança"
                    },
                    {
                        "type": "procuração",
                        "start_marker": "PROCURAÇÃO\n\nOUTORGANTE: João...",
                        "end_marker": "...poderes de representação.",
                        "confidence": 1.0,
                        "summary": "Procuração ad judicia do autor"
                    }
                ]
            }
        }
