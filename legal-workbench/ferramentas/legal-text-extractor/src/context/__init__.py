"""
Context Store - Sistema de aprendizado de padrões

Aprende padrões visuais/estruturais ao processar documentos e sugere
otimizacoes para processamento futuro.

Principios:
1. Similaridade, nao identidade - Sugere, nao determina
2. Engine-aware - Engine inferior nao sobrescreve superior
3. Feedback loop - Aprende com acertos e erros
4. Global learning - Aprende entre casos diferentes (v2.0)

Usage:
    from src.context import ContextStore, PatternHint, ObservationResult

    # Inicializa store
    store = ContextStore(db_path=Path("data/context.db"))

    # Cria/recupera caso
    caso = store.get_or_create_caso(numero_cnj="...", sistema="pje")

    # Busca hint de engine (GLOBAL - busca em todos os casos)
    hint = store.get_engine_hint_for_signature(
        signature_vector=[0.1, 0.2, ...],
        pattern_type=PatternType.HEADER,
        caso_id=caso.id  # Opcional, prioriza caso especifico
    )

    # Usa hint (se disponivel)
    if hint and hint.should_use:
        engine = hint.suggested_engine
        bbox = hint.suggested_bbox
        # ... processa com sugestoes

    # Aprende com resultado
    store.learn_from_page(
        caso_id=caso.id,
        signature=SignatureVector(features=[...], hash="..."),
        result=ObservationResult(...),
        hint=hint  # Opcional
    )

    # Consulta melhor engine para tipo de padrao (baseado em historico)
    best_engine = store.get_best_engine_for_pattern_type(PatternType.TABLE)
"""

from .models import (
    Caso,
    Divergence,
    EngineQuality,
    EngineType,
    ObservationResult,
    ObservedPattern,
    PatternHint,
    PatternType,
    SignatureVector,
)
from .signature import (
    PageSignatureInput,
    compute_signature,
    compute_signature_from_layout,
    infer_pattern_type,
)
from .store import ENGINE_QUALITY, ContextStore

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
