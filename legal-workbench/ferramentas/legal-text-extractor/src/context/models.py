"""
Data models for Context Store
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EngineType(str, Enum):
    """Tipos de engines disponíveis"""
    MARKER = "marker"
    PDFPLUMBER = "pdfplumber"
    TESSERACT = "tesseract"


class PatternType(str, Enum):
    """Tipos de padrões observáveis"""
    HEADER = "header"
    FOOTER = "footer"
    TABLE = "table"
    TEXT_BLOCK = "text_block"
    IMAGE = "image"
    SIGNATURE = "signature"
    STAMP = "stamp"
    UNKNOWN = "unknown"


@dataclass
class Caso:
    """Representa um caso (processo judicial)"""
    numero_cnj: str
    sistema: str  # 'pje', 'eproc', 'tucujuris', etc
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SignatureVector:
    """Vetor de assinatura para um padrão"""
    features: List[float]  # Features normalizadas
    hash: str  # MD5 hash do vetor

    def __post_init__(self):
        """Valida vetor"""
        if not self.features:
            raise ValueError("Feature vector cannot be empty")
        if len(self.features) > 100:
            raise ValueError(f"Feature vector too large: {len(self.features)} > 100")


@dataclass
class ObservedPattern:
    """Padrão observado durante processamento"""
    caso_id: int
    pattern_type: PatternType
    signature_hash: str
    signature_vector: List[float]
    first_seen_page: int
    last_seen_page: int
    created_by_engine: EngineType
    engine_quality_score: float

    # Opcionais
    id: Optional[int] = None
    occurrence_count: int = 1
    avg_confidence: Optional[float] = None
    divergence_count: int = 0
    deprecated: bool = False
    suggested_bbox: Optional[List[float]] = None
    suggested_engine: Optional[EngineType] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Valida dados"""
        if not 0.0 <= self.engine_quality_score <= 1.0:
            raise ValueError(f"Invalid quality score: {self.engine_quality_score}")
        if self.avg_confidence is not None and not 0.0 <= self.avg_confidence <= 1.0:
            raise ValueError(f"Invalid confidence: {self.avg_confidence}")
        if self.suggested_bbox and len(self.suggested_bbox) != 4:
            raise ValueError(f"Invalid bbox: {self.suggested_bbox}")


@dataclass
class Divergence:
    """Divergência entre expectativa e realidade"""
    pattern_id: int
    page_num: int
    expected_confidence: float
    actual_confidence: float
    engine_used: EngineType

    id: Optional[int] = None
    reason: Optional[str] = None
    recorded_at: Optional[datetime] = None

    def __post_init__(self):
        """Valida dados"""
        if not 0.0 <= self.expected_confidence <= 1.0:
            raise ValueError(f"Invalid expected confidence: {self.expected_confidence}")
        if not 0.0 <= self.actual_confidence <= 1.0:
            raise ValueError(f"Invalid actual confidence: {self.actual_confidence}")

    @property
    def divergence_magnitude(self) -> float:
        """Magnitude da divergência (sempre positiva)"""
        return abs(self.expected_confidence - self.actual_confidence)


@dataclass
class PatternHint:
    """Sugestão baseada em padrões similares"""
    pattern_id: int
    similarity: float  # 0.0 a 1.0
    suggested_bbox: Optional[List[float]]
    suggested_engine: Optional[EngineType]
    confidence: float  # Confiança na sugestão
    created_by_engine: EngineType

    # Metadados do padrão
    pattern_type: PatternType = PatternType.UNKNOWN
    occurrence_count: int = 1
    avg_confidence: Optional[float] = None

    def __post_init__(self):
        """Valida dados"""
        if not 0.0 <= self.similarity <= 1.0:
            raise ValueError(f"Invalid similarity: {self.similarity}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Invalid confidence: {self.confidence}")
        if self.suggested_bbox and len(self.suggested_bbox) != 4:
            raise ValueError(f"Invalid bbox: {self.suggested_bbox}")

    @property
    def should_use(self) -> bool:
        """Indica se a sugestão deve ser usada"""
        return self.similarity >= 0.85 and self.confidence >= 0.7


@dataclass
class ObservationResult:
    """Resultado de uma observação (processamento de página)"""
    page_num: int
    engine_used: EngineType
    confidence: float
    text_length: int

    # Opcionais
    bbox: Optional[List[float]] = None
    pattern_type: PatternType = PatternType.UNKNOWN
    processing_time_ms: Optional[int] = None
    success: bool = True

    def __post_init__(self):
        """Valida dados"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Invalid confidence: {self.confidence}")
        if self.text_length < 0:
            raise ValueError(f"Invalid text_length: {self.text_length}")
        if self.bbox and len(self.bbox) != 4:
            raise ValueError(f"Invalid bbox: {self.bbox}")


@dataclass
class EngineQuality:
    """Métricas de qualidade por engine"""
    engine: EngineType
    total_patterns: int
    avg_confidence: float
    total_occurrences: int
    deprecated_count: int

    @property
    def reliability_score(self) -> float:
        """Score de confiabilidade (0.0 a 1.0)"""
        if self.total_patterns == 0:
            return 0.0
        deprecation_rate = self.deprecated_count / self.total_patterns
        # Combina confiança média com taxa de depreciação invertida
        return (self.avg_confidence * 0.7) + ((1.0 - deprecation_rate) * 0.3)
