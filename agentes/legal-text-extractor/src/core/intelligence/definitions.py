"""
Carregamento e gerenciamento da taxonomia legal.

Responsabilidades:
- Carregar legal_taxonomy.json
- Normalizar termos para matching case-insensitive
- Fornecer interface de consulta por categoria
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict


class CategoryDefinition(TypedDict):
    """Estrutura de uma categoria na taxonomia."""
    synonyms: list[str]
    header_patterns: list[str]
    footer_patterns: list[str]
    priority: int


@dataclass
class LegalTaxonomy:
    """Taxonomia de pecas processuais carregada em memoria."""

    version: str
    description: str
    sources: list[str]
    categories: dict[str, CategoryDefinition]

    # Cache de padroes compilados (lazy)
    _compiled_patterns: dict[str, re.Pattern] = field(default_factory=dict, repr=False)

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliza texto para matching robusto.

        - Remove acentos (NFKD)
        - Converte para uppercase
        - Remove espacos extras

        Args:
            text: Texto original

        Returns:
            Texto normalizado
        """
        # Remove acentos via decomposicao Unicode
        nfkd = unicodedata.normalize("NFKD", text)
        without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))

        # Uppercase e espacos normalizados
        normalized = " ".join(without_accents.upper().split())

        return normalized

    def get_category_pattern(self, category: str) -> re.Pattern:
        """
        Retorna regex compilado para uma categoria.

        Combina todos os sinonimos em um unico pattern com alternativas.
        Usa cache para evitar recompilacao.

        Args:
            category: Nome da categoria (ex: "PETICAO_INICIAL")

        Returns:
            Pattern compilado
        """
        if category not in self._compiled_patterns:
            if category not in self.categories:
                # Categoria invalida - retorna pattern que nunca casa
                self._compiled_patterns[category] = re.compile(r"(?!.)")
            else:
                synonyms = self.categories[category]["synonyms"]
                if not synonyms:
                    self._compiled_patterns[category] = re.compile(r"(?!.)")
                else:
                    # Normaliza todos os sinonimos e escapa caracteres especiais
                    normalized_synonyms = [
                        re.escape(self.normalize_text(s)) for s in synonyms
                    ]
                    # Cria alternativa: (TERMO1|TERMO2|TERMO3)
                    pattern_str = r"\b(" + "|".join(normalized_synonyms) + r")\b"
                    self._compiled_patterns[category] = re.compile(
                        pattern_str, re.IGNORECASE
                    )

        return self._compiled_patterns[category]

    def get_header_pattern(self, category: str) -> re.Pattern:
        """
        Retorna regex compilado para header patterns de uma categoria.

        Args:
            category: Nome da categoria

        Returns:
            Pattern compilado para headers
        """
        cache_key = f"{category}_header"
        if cache_key not in self._compiled_patterns:
            if category not in self.categories:
                self._compiled_patterns[cache_key] = re.compile(r"(?!.)")
            else:
                patterns = self.categories[category].get("header_patterns", [])
                if not patterns:
                    self._compiled_patterns[cache_key] = re.compile(r"(?!.)")
                else:
                    normalized = [
                        re.escape(self.normalize_text(p)) for p in patterns
                    ]
                    pattern_str = r"\b(" + "|".join(normalized) + r")\b"
                    self._compiled_patterns[cache_key] = re.compile(
                        pattern_str, re.IGNORECASE
                    )

        return self._compiled_patterns[cache_key]

    def get_footer_pattern(self, category: str) -> re.Pattern:
        """
        Retorna regex compilado para footer patterns de uma categoria.

        Args:
            category: Nome da categoria

        Returns:
            Pattern compilado para footers
        """
        cache_key = f"{category}_footer"
        if cache_key not in self._compiled_patterns:
            if category not in self.categories:
                self._compiled_patterns[cache_key] = re.compile(r"(?!.)")
            else:
                patterns = self.categories[category].get("footer_patterns", [])
                if not patterns:
                    self._compiled_patterns[cache_key] = re.compile(r"(?!.)")
                else:
                    normalized = [
                        re.escape(self.normalize_text(p)) for p in patterns
                    ]
                    pattern_str = r"\b(" + "|".join(normalized) + r")\b"
                    self._compiled_patterns[cache_key] = re.compile(
                        pattern_str, re.IGNORECASE
                    )

        return self._compiled_patterns[cache_key]

    def get_priority(self, category: str) -> int:
        """
        Retorna prioridade de uma categoria.

        Maior prioridade = mais especifico.

        Args:
            category: Nome da categoria

        Returns:
            Valor de prioridade (0-10)
        """
        if category not in self.categories:
            return 0
        return self.categories[category].get("priority", 0)

    def all_categories(self) -> list[str]:
        """Retorna lista de todas as categorias disponiveis."""
        return list(self.categories.keys())


class TaxonomyLoader:
    """Carregador de taxonomia a partir de arquivo JSON."""

    DEFAULT_PATH = Path(__file__).parent.parent.parent / "assets" / "legal_taxonomy.json"

    @classmethod
    def load(cls, path: Path | None = None) -> LegalTaxonomy:
        """
        Carrega taxonomia de arquivo JSON.

        Args:
            path: Caminho para o arquivo JSON. Se None, usa DEFAULT_PATH.

        Returns:
            Instancia de LegalTaxonomy

        Raises:
            FileNotFoundError: Se arquivo nao existe
            json.JSONDecodeError: Se JSON invalido
        """
        if path is None:
            path = cls.DEFAULT_PATH

        if not path.exists():
            raise FileNotFoundError(f"Arquivo de taxonomia nao encontrado: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return LegalTaxonomy(
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            sources=data.get("sources", []),
            categories=data.get("categories", {}),
        )

    @classmethod
    def load_or_default(cls, path: Path | None = None) -> LegalTaxonomy:
        """
        Carrega taxonomia ou retorna taxonomia minima em caso de erro.

        Args:
            path: Caminho para o arquivo JSON

        Returns:
            Instancia de LegalTaxonomy (pode ser minima se erro)
        """
        try:
            return cls.load(path)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[WARN] Falha ao carregar taxonomia: {e}")
            print("[WARN] Usando taxonomia minima (apenas INDETERMINADO)")
            return LegalTaxonomy(
                version="0.0.0",
                description="Taxonomia minima (fallback)",
                sources=[],
                categories={
                    "INDETERMINADO": {
                        "synonyms": [],
                        "header_patterns": [],
                        "footer_patterns": [],
                        "priority": 0,
                    }
                },
            )


# Instancia global para uso direto
_taxonomy_instance: LegalTaxonomy | None = None


def get_taxonomy() -> LegalTaxonomy:
    """
    Retorna instancia singleton da taxonomia.

    Carrega na primeira chamada e reutiliza nas subsequentes.

    Returns:
        Instancia de LegalTaxonomy
    """
    global _taxonomy_instance
    if _taxonomy_instance is None:
        _taxonomy_instance = TaxonomyLoader.load_or_default()
    return _taxonomy_instance


def reload_taxonomy(path: Path | None = None) -> LegalTaxonomy:
    """
    Forca recarga da taxonomia.

    Util para testes ou atualizacao em runtime.

    Args:
        path: Novo caminho para taxonomia

    Returns:
        Nova instancia de LegalTaxonomy
    """
    global _taxonomy_instance
    _taxonomy_instance = TaxonomyLoader.load_or_default(path)
    return _taxonomy_instance
