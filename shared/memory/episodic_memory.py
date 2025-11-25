#!/usr/bin/env python3
"""
Sistema de memoria episodica para contexto entre sessoes.

Armazena conhecimento critico:
- Bugs resolvidos
- Workarounds de API
- Decisoes arquiteturais
- Padroes de solucao
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import json
import uuid


class MemoryType(Enum):
    """Tipos de memoria suportados."""

    BUG_RESOLUTION = "bug_resolution"
    API_WORKAROUND = "api_workaround"
    SOLUTION_PATTERN = "solution_pattern"
    ARCHITECTURAL_DECISION = "architectural_decision"
    ORCHESTRATION = "orchestration"
    PROJECT_CONTEXT = "project_context"
    TEST_RESULTS = "test_results"


@dataclass
class MemoryUnit:
    """Unidade de memoria com metadados."""

    type: str
    title: str
    content: str
    tags: list[str] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "context": self.context,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryUnit":
        """Cria instancia a partir de dicionario."""
        return cls(**data)


class EpisodicMemory:
    """Sistema de memoria episodica com persistencia JSON."""

    def __init__(self, memory_dir: Path, enable_embeddings: bool = False):
        """
        Inicializa sistema de memoria.

        Args:
            memory_dir: Diretorio para armazenar memorias
            enable_embeddings: Reservado para futuro suporte a embeddings
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memories_file = self.memory_dir / "memories.json"
        self.enable_embeddings = enable_embeddings
        self._memories: list[MemoryUnit] = []
        self._load()

    def _load(self) -> None:
        """Carrega memorias do arquivo JSON."""
        if self.memories_file.exists():
            with open(self.memories_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._memories = [MemoryUnit.from_dict(m) for m in data]

    def _save(self) -> None:
        """Persiste memorias no arquivo JSON."""
        with open(self.memories_file, "w", encoding="utf-8") as f:
            json.dump(
                [m.to_dict() for m in self._memories],
                f,
                indent=2,
                ensure_ascii=False,
            )

    def store(self, memory: MemoryUnit) -> str:
        """
        Armazena nova memoria.

        Args:
            memory: Unidade de memoria a armazenar

        Returns:
            ID da memoria armazenada
        """
        self._memories.append(memory)
        self._save()
        return memory.id

    def recall(
        self,
        tags: Optional[list[str]] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[MemoryUnit]:
        """
        Recupera memorias por tags e/ou tipo.

        Args:
            tags: Lista de tags para filtrar (OR logic)
            memory_type: Tipo de memoria para filtrar
            limit: Maximo de resultados

        Returns:
            Lista de memorias ordenadas por data (mais recente primeiro)
        """
        results = self._memories

        if memory_type:
            results = [m for m in results if m.type == memory_type]

        if tags:
            tags_set = set(t.lower() for t in tags)
            results = [
                m
                for m in results
                if tags_set.intersection(set(t.lower() for t in m.tags))
            ]

        # Ordenar por data (mais recente primeiro)
        results = sorted(results, key=lambda m: m.created_at, reverse=True)

        return results[:limit]

    def get_stats(self) -> dict:
        """
        Retorna estatisticas das memorias.

        Returns:
            Dicionario com total, tipos, tags mais frequentes
        """
        by_type: dict[str, int] = {}
        all_tags: list[str] = []

        for m in self._memories:
            by_type[m.type] = by_type.get(m.type, 0) + 1
            all_tags.extend(m.tags)

        tag_counts: dict[str, int] = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        top_tags = sorted(
            [{"tag": k, "count": v} for k, v in tag_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

        return {
            "total_memories": len(self._memories),
            "types_count": len(by_type),
            "by_type": by_type,
            "embeddings_enabled": self.enable_embeddings,
            "top_tags": top_tags,
        }

    def clear(self) -> None:
        """Remove todas as memorias."""
        self._memories = []
        self._save()
