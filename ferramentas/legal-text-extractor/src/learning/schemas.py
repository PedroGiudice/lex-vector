"""Pydantic schemas para o sistema de aprendizado"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ValidationStatus(str, Enum):
    """Status de validação humana"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIAL = "partial"  # Algumas seções corretas, outras erradas


class SectionType(str, Enum):
    """Tipos de seções jurídicas"""
    PETICAO_INICIAL = "petição_inicial"
    CONTESTACAO = "contestação"
    REPLICA = "réplica"
    SENTENCA = "sentença"
    ACORDAO = "acórdão"
    DESPACHO = "despacho"
    DECISAO_INTERLOCUTORIA = "decisão_interlocutória"
    PARECER_MP = "parecer_mp"
    LAUDO_PERICIAL = "laudo_pericial"
    ATA_AUDIENCIA = "ata_audiência"
    PROCURACAO = "procuração"
    SUBSTABELECIMENTO = "substabelecimento"
    CONTRATO = "contrato"
    DOCUMENTO_FISCAL = "documento_fiscal"
    CORRESPONDENCIA = "correspondência"
    OUTRO = "outro"


class ExtractedSection(BaseModel):
    """Seção extraída pelo sistema"""
    type: SectionType
    content: str = Field(..., min_length=1)
    start_pos: int = Field(..., ge=0)
    end_pos: int = Field(..., ge=0)
    confidence: float = Field(..., ge=0.0, le=1.0)

    # Metadados adicionais do Claude
    start_marker: Optional[str] = None
    end_marker: Optional[str] = None
    summary: Optional[str] = None

    @field_validator('end_pos')
    @classmethod
    def validate_positions(cls, v: int, info) -> int:
        """Valida que end_pos >= start_pos"""
        if 'start_pos' in info.data and v < info.data['start_pos']:
            raise ValueError(f"end_pos ({v}) deve ser >= start_pos ({info.data['start_pos']})")
        return v


class GroundTruthSection(BaseModel):
    """Seção ground truth (validada por humano)"""
    type: SectionType
    start_pos: int = Field(..., ge=0)
    end_pos: int = Field(..., ge=0)
    notes: Optional[str] = Field(None, description="Notas do validador humano")


class ExtractionResult(BaseModel):
    """Resultado completo de uma extração (predicted + ground truth)"""

    # Identificação
    document_id: str = Field(..., description="ID único do documento")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    # Resultado da extração
    predicted_sections: list[ExtractedSection] = Field(default_factory=list)

    # Ground truth (preenchido após validação humana)
    ground_truth_sections: Optional[list[GroundTruthSection]] = None
    validation_status: ValidationStatus = ValidationStatus.PENDING
    validated_at: Optional[datetime] = None
    validator_notes: Optional[str] = None

    # Metadados do documento
    document_length: int = Field(..., ge=0, description="Tamanho do documento em chars")
    prompt_version: str = Field(default="v1", description="Versão do prompt usado")
    model: str = Field(default="claude-sonnet-4-20250514")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_2025-01-15_001",
                "extracted_at": "2025-01-15T10:30:00Z",
                "predicted_sections": [
                    {
                        "type": "petição_inicial",
                        "content": "EXCELENTÍSSIMO SENHOR...",
                        "start_pos": 0,
                        "end_pos": 1500,
                        "confidence": 0.95
                    }
                ],
                "validation_status": "approved",
                "document_length": 2500
            }
        }


class FewShotExample(BaseModel):
    """Exemplo few-shot para melhorar prompts"""

    # Identificação
    example_id: str = Field(..., description="ID único do exemplo")
    source_document_id: str = Field(..., description="Documento de origem")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Conteúdo do exemplo
    section_type: SectionType
    input_text: str = Field(..., min_length=50, max_length=5000,
                           description="Texto exemplo (truncado se necessário)")
    expected_output: dict = Field(..., description="Output esperado (JSON)")

    # Qualidade
    quality_score: float = Field(..., ge=0.0, le=1.0,
                                 description="Score de qualidade (baseado em confidence e validação)")
    usage_count: int = Field(default=0, ge=0,
                            description="Quantas vezes foi usado em prompts")
    success_rate: Optional[float] = Field(None, ge=0.0, le=1.0,
                                         description="Taxa de sucesso quando usado")

    # Metadados
    tags: list[str] = Field(default_factory=list,
                           description="Tags para filtragem (ex: 'complex', 'multi-page')")

    @field_validator('input_text')
    @classmethod
    def truncate_if_needed(cls, v: str) -> str:
        """Trunca texto se muito longo"""
        max_len = 5000
        if len(v) > max_len:
            return v[:max_len] + "..."
        return v


class PerformanceMetrics(BaseModel):
    """Métricas de performance de um batch de extrações"""

    # Identificação
    batch_id: str = Field(..., description="ID do batch de testes")
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    # Métricas globais
    total_documents: int = Field(..., ge=0)
    total_sections_predicted: int = Field(..., ge=0)
    total_sections_ground_truth: int = Field(..., ge=0)

    # Métricas de classificação
    true_positives: int = Field(..., ge=0, description="Seções corretamente identificadas")
    false_positives: int = Field(..., ge=0, description="Seções identificadas incorretamente")
    false_negatives: int = Field(..., ge=0, description="Seções não identificadas")

    # Métricas calculadas
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    f1_score: float = Field(..., ge=0.0, le=1.0)

    # Breakdown por tipo de seção
    per_type_metrics: Optional[dict[str, dict]] = Field(
        None,
        description="Métricas detalhadas por tipo de seção"
    )

    # Metadados
    prompt_version: str = Field(default="v1")
    average_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    @classmethod
    def calculate(
        cls,
        batch_id: str,
        predicted: list[ExtractedSection],
        ground_truth: list[GroundTruthSection],
        prompt_version: str = "v1"
    ) -> "PerformanceMetrics":
        """
        Calcula métricas a partir de predicted vs ground truth.

        Implementação simplificada: considera match se tipo e posição aproximada coincidem.
        """
        # Matching simples: considera TP se tipo coincide e há overlap de posições
        tp = 0
        matched_gt = set()

        for pred in predicted:
            for i, gt in enumerate(ground_truth):
                if i in matched_gt:
                    continue

                # Verifica se tipo coincide
                if pred.type.value != gt.type.value:
                    continue

                # Verifica se há overlap de posições (overlap > 50%)
                overlap_start = max(pred.start_pos, gt.start_pos)
                overlap_end = min(pred.end_pos, gt.end_pos)
                overlap = max(0, overlap_end - overlap_start)

                pred_len = pred.end_pos - pred.start_pos
                gt_len = gt.end_pos - gt.start_pos

                if overlap > 0.5 * min(pred_len, gt_len):
                    tp += 1
                    matched_gt.add(i)
                    break

        fp = len(predicted) - tp
        fn = len(ground_truth) - tp

        # Calcular precision, recall, F1
        precision = tp / len(predicted) if predicted else 0.0
        recall = tp / len(ground_truth) if ground_truth else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        avg_confidence = sum(s.confidence for s in predicted) / len(predicted) if predicted else 0.0

        return cls(
            batch_id=batch_id,
            total_documents=1,  # Para batch de 1 documento
            total_sections_predicted=len(predicted),
            total_sections_ground_truth=len(ground_truth),
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=precision,
            recall=recall,
            f1_score=f1,
            prompt_version=prompt_version,
            average_confidence=avg_confidence
        )
