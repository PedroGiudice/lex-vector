#!/usr/bin/env python3
"""
Testes para o sistema de memoria episodica.
"""
import sys
from pathlib import Path
import tempfile
import shutil

import pytest

# Adicionar shared ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.memory import EpisodicMemory, MemoryUnit, MemoryType


@pytest.fixture
def temp_memory_dir():
    """Cria diretorio temporario para testes."""
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path
    shutil.rmtree(dir_path)


class TestMemoryUnit:
    """Testes para MemoryUnit."""

    def test_create_memory_unit(self):
        """Testa criacao de unidade de memoria."""
        unit = MemoryUnit(
            type=MemoryType.BUG_RESOLUTION.value,
            title="Test Bug",
            content="Bug description",
            tags=["test", "bug"],
        )

        assert unit.type == "bug_resolution"
        assert unit.title == "Test Bug"
        assert unit.content == "Bug description"
        assert unit.tags == ["test", "bug"]
        assert unit.id is not None
        assert unit.created_at is not None

    def test_to_dict_and_from_dict(self):
        """Testa serializacao e desserializacao."""
        unit = MemoryUnit(
            type="test",
            title="Test",
            content="Content",
            tags=["tag1"],
            context={"key": "value"},
        )

        data = unit.to_dict()
        restored = MemoryUnit.from_dict(data)

        assert restored.id == unit.id
        assert restored.type == unit.type
        assert restored.title == unit.title
        assert restored.content == unit.content
        assert restored.tags == unit.tags
        assert restored.context == unit.context


class TestEpisodicMemory:
    """Testes para EpisodicMemory."""

    def test_store_and_recall(self, temp_memory_dir):
        """Testa armazenamento e recuperacao por tags."""
        memory = EpisodicMemory(temp_memory_dir)

        unit = MemoryUnit(
            type=MemoryType.BUG_RESOLUTION.value,
            title="Test Bug",
            content="Bug description",
            tags=["test", "bug"],
        )

        memory_id = memory.store(unit)
        assert memory_id is not None

        recalled = memory.recall(tags=["test"])
        assert len(recalled) == 1
        assert recalled[0].title == "Test Bug"

    def test_recall_by_type(self, temp_memory_dir):
        """Testa recuperacao por tipo."""
        memory = EpisodicMemory(temp_memory_dir)

        memory.store(
            MemoryUnit(
                type=MemoryType.BUG_RESOLUTION.value,
                title="Bug",
                content="...",
                tags=[],
            )
        )
        memory.store(
            MemoryUnit(
                type=MemoryType.SOLUTION_PATTERN.value,
                title="Solution",
                content="...",
                tags=[],
            )
        )

        bugs = memory.recall(memory_type=MemoryType.BUG_RESOLUTION.value)
        assert len(bugs) == 1
        assert bugs[0].title == "Bug"

    def test_recall_combined_filters(self, temp_memory_dir):
        """Testa recuperacao com filtros combinados."""
        memory = EpisodicMemory(temp_memory_dir)

        memory.store(
            MemoryUnit(
                type=MemoryType.BUG_RESOLUTION.value,
                title="API Bug",
                content="...",
                tags=["api"],
            )
        )
        memory.store(
            MemoryUnit(
                type=MemoryType.BUG_RESOLUTION.value,
                title="UI Bug",
                content="...",
                tags=["ui"],
            )
        )
        memory.store(
            MemoryUnit(
                type=MemoryType.SOLUTION_PATTERN.value,
                title="API Solution",
                content="...",
                tags=["api"],
            )
        )

        # Filtrar por tipo E tag
        api_bugs = memory.recall(
            tags=["api"], memory_type=MemoryType.BUG_RESOLUTION.value
        )
        assert len(api_bugs) == 1
        assert api_bugs[0].title == "API Bug"

    def test_persistence(self, temp_memory_dir):
        """Testa persistencia entre instancias."""
        # Store
        memory1 = EpisodicMemory(temp_memory_dir)
        memory1.store(
            MemoryUnit(
                type="test", title="Persistent", content="data", tags=["persist"]
            )
        )

        # Reload
        memory2 = EpisodicMemory(temp_memory_dir)
        recalled = memory2.recall(tags=["persist"])
        assert len(recalled) == 1
        assert recalled[0].title == "Persistent"

    def test_stats(self, temp_memory_dir):
        """Testa estatisticas."""
        memory = EpisodicMemory(temp_memory_dir)
        memory.store(
            MemoryUnit(type="bug", title="A", content="...", tags=["api", "djen"])
        )
        memory.store(MemoryUnit(type="bug", title="B", content="...", tags=["api"]))
        memory.store(
            MemoryUnit(type="solution", title="C", content="...", tags=["windows"])
        )

        stats = memory.get_stats()
        assert stats["total_memories"] == 3
        assert stats["by_type"]["bug"] == 2
        assert stats["by_type"]["solution"] == 1
        assert stats["embeddings_enabled"] is False

        # Verificar top tags
        api_tag = next((t for t in stats["top_tags"] if t["tag"] == "api"), None)
        assert api_tag is not None
        assert api_tag["count"] == 2

    def test_clear(self, temp_memory_dir):
        """Testa limpeza de memorias."""
        memory = EpisodicMemory(temp_memory_dir)
        memory.store(MemoryUnit(type="test", title="A", content="...", tags=[]))
        memory.store(MemoryUnit(type="test", title="B", content="...", tags=[]))

        assert memory.get_stats()["total_memories"] == 2

        memory.clear()

        assert memory.get_stats()["total_memories"] == 0

    def test_recall_limit(self, temp_memory_dir):
        """Testa limite de resultados."""
        memory = EpisodicMemory(temp_memory_dir)

        for i in range(20):
            memory.store(
                MemoryUnit(
                    type="test", title=f"Memory {i}", content="...", tags=["all"]
                )
            )

        recalled = memory.recall(tags=["all"], limit=5)
        assert len(recalled) == 5

    def test_recall_case_insensitive_tags(self, temp_memory_dir):
        """Testa busca case-insensitive por tags."""
        memory = EpisodicMemory(temp_memory_dir)
        memory.store(
            MemoryUnit(type="test", title="Test", content="...", tags=["DJEN", "API"])
        )

        # Buscar com case diferente
        recalled = memory.recall(tags=["djen", "api"])
        assert len(recalled) == 1


class TestMemoryType:
    """Testes para MemoryType enum."""

    def test_all_types_defined(self):
        """Verifica que todos os tipos esperados existem."""
        expected = [
            "bug_resolution",
            "api_workaround",
            "solution_pattern",
            "architectural_decision",
            "orchestration",
            "project_context",
            "test_results",
        ]

        for tipo in expected:
            assert hasattr(MemoryType, tipo.upper())
