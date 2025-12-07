# Context Store

Sistema de aprendizado de padrões para o Legal Text Extractor.

## Quick Start

```python
from pathlib import Path
from src.context import (
    ContextStore,
    SignatureVector,
    ObservationResult,
    EngineType,
    PatternType,
)

# Initialize
store = ContextStore(db_path=Path("data/context.db"))

# Create caso
caso = store.get_or_create_caso(
    numero_cnj="0000001-12.2024.5.01.0001",
    sistema="pje"
)

# Find similar pattern
hint = store.find_similar_pattern(
    caso_id=caso.id,
    signature_vector=[0.1, 0.2, 0.3, ...],
)

# Use hint if available
if hint and hint.should_use:
    engine = hint.suggested_engine
    bbox = hint.suggested_bbox

# Learn from result
store.learn_from_page(
    caso_id=caso.id,
    signature=SignatureVector(features=[...], hash="..."),
    result=ObservationResult(...),
    hint=hint
)
```

## Files

- `schema.sql` - SQLite database schema
- `models.py` - Data models and enums
- `store.py` - ContextStore implementation
- `__init__.py` - Public API exports

## Documentation

Full documentation at: `../../docs/CONTEXT_STORE.md`

## Tests

```bash
pytest tests/test_context_store.py -v
```

## Example

```bash
python examples/context_store_example.py
```

## Principles

1. **Similarity, not identity** - Uses cosine similarity (threshold=0.85)
2. **Engine-aware** - Inferior engines don't overwrite superior ones
3. **Feedback loop** - Learns from successes and failures, auto-deprecates unreliable patterns

## Performance

- `get_or_create_caso()`: O(1) - <1ms
- `find_similar_pattern()`: O(n) - <10ms (n<100)
- `learn_from_page()`: O(1) - <5ms

## Status

✅ Production-ready (2025-11-29)
