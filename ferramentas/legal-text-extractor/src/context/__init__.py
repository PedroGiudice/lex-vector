"""
Context Store - Sistema de aprendizado de padrões

Aprende padrões visuais/estruturais ao processar documentos e sugere
otimizações para processamento futuro.

Princípios:
1. Similaridade, não identidade - Sugere, não determina
2. Engine-aware - Engine inferior não sobrescreve superior
3. Feedback loop - Aprende com acertos e erros

Usage:
    from src.context import ContextStore, PatternHint, ObservationResult

    # Inicializa store
    store = ContextStore(db_path=Path("data/context.db"))

    # Cria/recupera caso
    caso = store.get_or_create_caso(numero_cnj="...", sistema="pje")

    # Busca padrão similar antes de processar
    hint = store.find_similar_pattern(
        caso_id=caso.id,
        signature_vector=[0.1, 0.2, ...],
        pattern_type=PatternType.HEADER
    )

    # Usa hint (se disponível)
    if hint and hint.should_use:
        engine = hint.suggested_engine
        bbox = hint.suggested_bbox
        # ... processa com sugestões

    # Aprende com resultado
    store.learn_from_page(
        caso_id=caso.id,
        signature=SignatureVector(features=[...], hash="..."),
        result=ObservationResult(...),
        hint=hint  # Opcional
    )
"""

from .models import (
    Caso,
    ObservedPattern,
    Divergence,
    PatternHint,
    ObservationResult,
    EngineType,
    PatternType,
    SignatureVector,
    EngineQuality,
)

from .store import ContextStore, ENGINE_QUALITY
from .signature import (
    compute_signature,
    compute_signature_from_layout,
    infer_pattern_type,
    PageSignatureInput,
)

__all__ = [
    # Main store
    "ContextStore",
    "ENGINE_QUALITY",

    # Data models
    "Caso",
    "ObservedPattern",
    "Divergence",
    "PatternHint",
    "ObservationResult",
    "SignatureVector",
    "EngineQuality",

    # Enums
    "EngineType",
    "PatternType",

    # Signature computation
    "compute_signature",
    "compute_signature_from_layout",
    "infer_pattern_type",
    "PageSignatureInput",
]
