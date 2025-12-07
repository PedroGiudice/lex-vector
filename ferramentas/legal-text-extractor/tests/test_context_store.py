"""
Unit tests for Context Store

Testa o sistema de aprendizado que armazena padrões bem-sucedidos de extração
e usa similaridade para aplicá-los em novos documentos.
"""
import pytest
import tempfile
from pathlib import Path
import sys

# Setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.context import (
    ContextStore,
    SignatureVector,
    ObservationResult,
    EngineType,
    PatternType,
    ENGINE_QUALITY,
)


@pytest.fixture
def temp_db():
    """Creates temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def store(temp_db):
    """Creates ContextStore instance"""
    return ContextStore(db_path=temp_db)


class TestContextStore:
    """Test suite for ContextStore"""

    def test_init_creates_schema(self, store, temp_db):
        """Test that initialization creates schema"""
        assert temp_db.exists()
        # Verify tables exist by trying to query
        assert store.get_pattern_count(1, deprecated=False) == 0

    def test_get_or_create_caso(self, store):
        """Test caso creation and retrieval"""
        # Create new caso
        caso1 = store.get_or_create_caso(
            numero_cnj="0000001-12.2024.5.01.0001",
            sistema="pje"
        )
        assert caso1.id is not None
        assert caso1.numero_cnj == "0000001-12.2024.5.01.0001"
        assert caso1.sistema == "pje"

        # Retrieve existing caso
        caso2 = store.get_or_create_caso(
            numero_cnj="0000001-12.2024.5.01.0001",
            sistema="pje"
        )
        assert caso2.id == caso1.id

    def test_find_similar_pattern_empty(self, store):
        """Test finding pattern in empty database"""
        caso = store.get_or_create_caso("0000001", "pje")

        hint = store.find_similar_pattern(
            caso_id=caso.id,
            signature_vector=[0.1, 0.2, 0.3],
        )

        assert hint is None

    def test_learn_and_find_pattern(self, store):
        """Test learning pattern and finding it later"""
        caso = store.get_or_create_caso("0000001", "pje")

        # Learn from first page
        signature1 = SignatureVector(
            features=[0.1, 0.2, 0.3, 0.4, 0.5],
            hash="abc123"
        )

        result1 = ObservationResult(
            page_num=1,
            engine_used=EngineType.MARKER,
            confidence=0.95,
            text_length=1000,
            pattern_type=PatternType.HEADER,
            bbox=[0, 0, 100, 50],
        )

        pattern_id = store.learn_from_page(
            caso_id=caso.id,
            signature=signature1,
            result=result1,
        )

        assert pattern_id is not None

        # Find similar pattern
        signature2 = SignatureVector(
            features=[0.11, 0.21, 0.29, 0.41, 0.51],  # Very similar
            hash="def456"
        )

        hint = store.find_similar_pattern(
            caso_id=caso.id,
            signature_vector=signature2.features,
            pattern_type=PatternType.HEADER,
        )

        assert hint is not None
        assert hint.similarity >= store.SIMILARITY_THRESHOLD
        assert hint.suggested_engine == EngineType.MARKER
        assert hint.suggested_bbox == [0, 0, 100, 50]

    def test_cosine_similarity(self, store):
        """Test cosine similarity calculation"""
        # Identical vectors
        assert store._cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)

        # Orthogonal vectors
        assert store._cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)

        # Similar vectors
        sim = store._cosine_similarity([1, 1], [1.1, 0.9])
        assert 0.99 < sim < 1.0

    def test_engine_aware_update(self, store):
        """Test that inferior engine doesn't overwrite superior"""
        caso = store.get_or_create_caso("0000001", "pje")

        # Create pattern with MARKER (quality=1.0)
        signature = SignatureVector(features=[0.1, 0.2], hash="abc")
        result_marker = ObservationResult(
            page_num=1,
            engine_used=EngineType.MARKER,
            confidence=0.95,
            text_length=1000,
            pattern_type=PatternType.TEXT_BLOCK,
        )

        pattern_id = store.learn_from_page(caso.id, signature, result_marker)

        # Try to update with TESSERACT (quality=0.7)
        result_tesseract = ObservationResult(
            page_num=2,
            engine_used=EngineType.TESSERACT,
            confidence=0.6,
            text_length=900,
            pattern_type=PatternType.TEXT_BLOCK,
        )

        should_update = store.should_update_pattern(pattern_id, result_tesseract)
        assert should_update is False  # Inferior engine should not update

        # Update with PDFPLUMBER (quality=0.9)
        result_pdfplumber = ObservationResult(
            page_num=3,
            engine_used=EngineType.PDFPLUMBER,
            confidence=0.9,
            text_length=950,
            pattern_type=PatternType.TEXT_BLOCK,
        )

        should_update = store.should_update_pattern(pattern_id, result_pdfplumber)
        assert should_update is False  # Still inferior to MARKER

    def test_divergence_recording(self, store):
        """Test divergence detection and recording"""
        caso = store.get_or_create_caso("0000001", "pje")

        # Create initial pattern
        signature1 = SignatureVector(features=[0.5, 0.5], hash="abc")
        result1 = ObservationResult(
            page_num=1,
            engine_used=EngineType.MARKER,
            confidence=0.9,
            text_length=1000,
            pattern_type=PatternType.HEADER,
        )

        pattern_id = store.learn_from_page(caso.id, signature1, result1)

        # Get hint
        hint = store.find_similar_pattern(caso.id, [0.51, 0.49])

        # Process with divergence (low confidence)
        signature2 = SignatureVector(features=[0.51, 0.49], hash="def")
        result2 = ObservationResult(
            page_num=2,
            engine_used=EngineType.MARKER,
            confidence=0.4,  # Much lower than expected (0.9)
            text_length=500,
            pattern_type=PatternType.HEADER,
        )

        store.learn_from_page(caso.id, signature2, result2, hint=hint)

        # Verify divergence was recorded (checking via deprecation would require 3 divergences)
        # For now, we just verify the pattern still exists
        assert store.get_pattern_count(caso.id, deprecated=False) >= 1

    def test_pattern_deprecation(self, store):
        """Test that patterns deprecate after 3 divergences"""
        caso = store.get_or_create_caso("0000001", "pje")

        # Create pattern
        signature = SignatureVector(features=[0.5, 0.5], hash="abc")
        result = ObservationResult(
            page_num=1,
            engine_used=EngineType.MARKER,
            confidence=0.9,
            text_length=1000,
            pattern_type=PatternType.HEADER,
        )

        pattern_id = store.learn_from_page(caso.id, signature, result)

        # Record 3 divergences manually
        import sqlite3
        with sqlite3.connect(store.db_path) as conn:
            cursor = conn.cursor()
            for i in range(3):
                cursor.execute(
                    """
                    INSERT INTO divergences
                    (pattern_id, page_num, expected_confidence, actual_confidence, engine_used)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (pattern_id, i+2, 0.9, 0.4, EngineType.MARKER.value)
                )
            conn.commit()

        # Verify pattern was deprecated by trigger
        deprecated = store.get_pattern_count(caso.id, deprecated=True)
        assert deprecated == 1

    def test_engine_stats(self, store):
        """Test engine statistics calculation"""
        caso = store.get_or_create_caso("0000001", "pje")

        # Create patterns with different engines
        for engine in [EngineType.MARKER, EngineType.PDFPLUMBER, EngineType.TESSERACT]:
            signature = SignatureVector(
                features=[0.1, 0.2],
                hash=f"hash_{engine.value}"
            )
            result = ObservationResult(
                page_num=1,
                engine_used=engine,
                confidence=0.8,
                text_length=1000,
                pattern_type=PatternType.TEXT_BLOCK,
            )
            store.learn_from_page(caso.id, signature, result)

        stats = store.get_engine_stats()
        assert len(stats) == 3

        # Verify all engines present
        engine_names = {s.engine for s in stats}
        assert engine_names == {EngineType.MARKER, EngineType.PDFPLUMBER, EngineType.TESSERACT}


class TestModels:
    """Test data models"""

    def test_signature_vector_validation(self):
        """Test SignatureVector validation"""
        # Valid vector
        sig = SignatureVector(features=[0.1, 0.2, 0.3], hash="abc")
        assert sig.features == [0.1, 0.2, 0.3]

        # Empty vector should raise
        with pytest.raises(ValueError):
            SignatureVector(features=[], hash="abc")

        # Too large vector should raise
        with pytest.raises(ValueError):
            SignatureVector(features=[0.1] * 101, hash="abc")

    def test_observation_result_validation(self):
        """Test ObservationResult validation"""
        # Valid result
        result = ObservationResult(
            page_num=1,
            engine_used=EngineType.MARKER,
            confidence=0.9,
            text_length=1000,
        )
        assert result.page_num == 1

        # Invalid confidence
        with pytest.raises(ValueError):
            ObservationResult(
                page_num=1,
                engine_used=EngineType.MARKER,
                confidence=1.5,  # > 1.0
                text_length=1000,
            )

        # Invalid text_length
        with pytest.raises(ValueError):
            ObservationResult(
                page_num=1,
                engine_used=EngineType.MARKER,
                confidence=0.9,
                text_length=-1,  # Negative
            )

    def test_pattern_hint_should_use(self):
        """Test PatternHint.should_use property"""
        from src.context import PatternHint

        # Good hint
        hint = PatternHint(
            pattern_id=1,
            similarity=0.9,
            suggested_bbox=None,
            suggested_engine=None,
            confidence=0.85,
            created_by_engine=EngineType.MARKER,
        )
        assert hint.should_use is True

        # Low similarity
        hint2 = PatternHint(
            pattern_id=1,
            similarity=0.5,  # Too low
            suggested_bbox=None,
            suggested_engine=None,
            confidence=0.85,
            created_by_engine=EngineType.MARKER,
        )
        assert hint2.should_use is False

        # Low confidence
        hint3 = PatternHint(
            pattern_id=1,
            similarity=0.9,
            suggested_bbox=None,
            suggested_engine=None,
            confidence=0.5,  # Too low
            created_by_engine=EngineType.MARKER,
        )
        assert hint3.should_use is False

    def test_engine_quality_constants(self):
        """Test ENGINE_QUALITY constants"""
        assert ENGINE_QUALITY[EngineType.MARKER] == 1.0
        assert ENGINE_QUALITY[EngineType.PDFPLUMBER] == 0.9
        assert ENGINE_QUALITY[EngineType.TESSERACT] == 0.7

        # Verify ordering
        assert ENGINE_QUALITY[EngineType.MARKER] > ENGINE_QUALITY[EngineType.PDFPLUMBER]
        assert ENGINE_QUALITY[EngineType.PDFPLUMBER] > ENGINE_QUALITY[EngineType.TESSERACT]


class TestContextStoreLegacyCompat:
    """Tests for compatibility with legacy mock implementation"""

    @pytest.fixture
    def store(self):
        """Fixture que cria ContextStore temporário."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_context.db"
            yield ContextStore(db_path)

    def test_inferior_engine_no_overwrite(self, store):
        """Tesseract não sobrescreve padrão criado por Marker."""
        caso = store.get_or_create_caso("abc123", "pje")

        # Marker cria padrão (qualidade 1.0)
        sig1 = SignatureVector(features=[0.5, 0.5], hash="abc")
        result1 = ObservationResult(
            page_num=1,
            engine_used=EngineType.MARKER,
            confidence=0.95,
            text_length=1000,
            pattern_type=PatternType.HEADER,
        )
        pattern_id = store.learn_from_page(caso.id, sig1, result1)

        # Tesseract tenta sobrescrever (qualidade 0.7)
        result2 = ObservationResult(
            page_num=1,
            engine_used=EngineType.TESSERACT,
            confidence=0.80,
            text_length=900,
            pattern_type=PatternType.HEADER,
        )

        should_update = store.should_update_pattern(pattern_id, result2)
        assert should_update is False  # Tesseract não sobrescreve Marker

    def test_superior_engine_overwrites_inferior(self, store):
        """Engine superior PODE sobrescrever engine inferior."""
        caso = store.get_or_create_caso("abc123", "pje")

        # Tesseract cria padrão (qualidade 0.7)
        sig1 = SignatureVector(features=[0.5, 0.5], hash="abc")
        result1 = ObservationResult(
            page_num=1,
            engine_used=EngineType.TESSERACT,
            confidence=0.80,
            text_length=900,
            pattern_type=PatternType.HEADER,
        )
        pattern_id = store.learn_from_page(caso.id, sig1, result1)

        # Marker pode sobrescrever (qualidade 1.0 > 0.7)
        result2 = ObservationResult(
            page_num=1,
            engine_used=EngineType.MARKER,
            confidence=0.95,
            text_length=1000,
            pattern_type=PatternType.HEADER,
        )

        should_update = store.should_update_pattern(pattern_id, result2)
        assert should_update is True  # Marker pode sobrescrever Tesseract


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
