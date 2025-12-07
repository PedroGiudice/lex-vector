"""
Example: Context Store Usage

Demonstra como usar o ContextStore para aprender padrões
durante processamento de documentos.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.context import (
    ContextStore,
    SignatureVector,
    ObservationResult,
    EngineType,
    PatternType,
)


def main():
    # Inicializa store
    db_path = Path("data/context_example.db")
    store = ContextStore(db_path=db_path)

    print(f"✓ ContextStore initialized at {db_path}")

    # Cria caso
    caso = store.get_or_create_caso(
        numero_cnj="0000001-12.2024.5.01.0001",
        sistema="pje"
    )
    print(f"✓ Caso created: {caso.numero_cnj} (id={caso.id})")

    # Simula processamento de primeira página
    print("\n--- Processing Page 1 (first time) ---")

    signature1 = SignatureVector(
        features=[0.1, 0.2, 0.3, 0.8, 0.9],
        hash="abc123"
    )

    result1 = ObservationResult(
        page_num=1,
        engine_used=EngineType.MARKER,
        confidence=0.95,
        text_length=1500,
        pattern_type=PatternType.HEADER,
        bbox=[0, 0, 100, 50],
    )

    # Busca padrão similar (primeira vez = não encontra)
    hint = store.find_similar_pattern(
        caso_id=caso.id,
        signature_vector=signature1.features,
        pattern_type=PatternType.HEADER,
    )

    if hint:
        print(f"Found similar pattern (similarity={hint.similarity:.3f})")
    else:
        print("No similar pattern found (expected - first page)")

    # Aprende com resultado
    pattern_id = store.learn_from_page(
        caso_id=caso.id,
        signature=signature1,
        result=result1,
    )
    print(f"✓ Learned pattern {pattern_id}")

    # Simula processamento de página similar (mesma estrutura)
    print("\n--- Processing Page 2 (similar to page 1) ---")

    signature2 = SignatureVector(
        features=[0.11, 0.21, 0.29, 0.81, 0.89],  # Muito similar ao anterior
        hash="def456"
    )

    # Agora deve encontrar padrão similar
    hint = store.find_similar_pattern(
        caso_id=caso.id,
        signature_vector=signature2.features,
        pattern_type=PatternType.HEADER,
    )

    if hint:
        print(f"✓ Found similar pattern (similarity={hint.similarity:.3f})")
        print(f"  - Suggested engine: {hint.suggested_engine}")
        print(f"  - Suggested bbox: {hint.suggested_bbox}")
        print(f"  - Confidence: {hint.confidence:.3f}")
        print(f"  - Should use? {hint.should_use}")
    else:
        print("No similar pattern found")

    # Processa usando sugestão
    result2 = ObservationResult(
        page_num=2,
        engine_used=hint.suggested_engine if hint else EngineType.PDFPLUMBER,
        confidence=0.93,  # Próximo da expectativa
        text_length=1480,
        pattern_type=PatternType.HEADER,
        bbox=hint.suggested_bbox if hint else None,
    )

    pattern_id2 = store.learn_from_page(
        caso_id=caso.id,
        signature=signature2,
        result=result2,
        hint=hint,  # Passa hint para feedback loop
    )
    print(f"✓ Learned pattern {pattern_id2}")

    # Simula divergência (resultado muito diferente)
    print("\n--- Processing Page 3 (divergence test) ---")

    signature3 = SignatureVector(
        features=[0.12, 0.22, 0.28, 0.79, 0.91],  # Similar
        hash="ghi789"
    )

    hint3 = store.find_similar_pattern(
        caso_id=caso.id,
        signature_vector=signature3.features,
        pattern_type=PatternType.HEADER,
    )

    # Resultado ruim (confiança muito baixa)
    result3 = ObservationResult(
        page_num=3,
        engine_used=EngineType.TESSERACT,  # Engine inferior
        confidence=0.45,  # Divergência significativa!
        text_length=200,
        pattern_type=PatternType.HEADER,
    )

    pattern_id3 = store.learn_from_page(
        caso_id=caso.id,
        signature=signature3,
        result=result3,
        hint=hint3,
    )
    print(f"✓ Recorded divergence for pattern {pattern_id3}")

    # Estatísticas
    print("\n--- Engine Statistics ---")
    stats = store.get_engine_stats()
    for stat in stats:
        print(f"{stat.engine.value}:")
        print(f"  - Total patterns: {stat.total_patterns}")
        print(f"  - Avg confidence: {stat.avg_confidence:.3f}")
        print(f"  - Reliability score: {stat.reliability_score:.3f}")
        print(f"  - Deprecated: {stat.deprecated_count}")

    # Contagem de padrões
    active = store.get_pattern_count(caso.id, deprecated=False)
    deprecated = store.get_pattern_count(caso.id, deprecated=True)
    print(f"\nPatterns for caso {caso.id}: {active} active, {deprecated} deprecated")

    print("\n✓ Example completed successfully!")
    print(f"\nDatabase saved to: {db_path.absolute()}")


if __name__ == "__main__":
    main()
