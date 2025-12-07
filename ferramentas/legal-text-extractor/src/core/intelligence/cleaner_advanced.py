"""
Limpeza avancada de texto juridico.

Orquestra as regras de limpeza e fornece interface de alto nivel
para processamento de documentos.

Baseado em:
- legalnlp (Felipe Maia Polo)
- verbose-correct-doodle (legado interno)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import TypedDict

from .cleaning_rules import CleaningRules, RULE_ORDER


class CleaningStats(TypedDict):
    """Estatisticas de limpeza."""

    original_length: int
    final_length: int
    reduction_percent: float
    rules_applied: int
    patterns_matched: dict[str, int]


@dataclass
class AdvancedCleaner:
    """
    Limpador avancado de texto juridico.

    Aplica sequencia de regras de limpeza com tracking de estatisticas.
    """

    # Configuracoes
    include_masking: bool = False  # Se True, mascara CPF/CNPJ/etc
    preserve_structure: bool = True  # Se True, preserva quebras de paragrafo

    # Regras compiladas (lazy)
    _rules: CleaningRules | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Inicializa regras de limpeza."""
        self._rules = CleaningRules(include_optional=self.include_masking)

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """
        Normaliza caracteres Unicode problematicos.

        Args:
            text: Texto original

        Returns:
            Texto com Unicode normalizado
        """
        # Normaliza para NFC (composed form)
        normalized = unicodedata.normalize("NFC", text)

        # Substitui caracteres Unicode problematicos
        replacements = {
            "\u00a0": " ",  # Non-breaking space
            "\u200b": "",  # Zero-width space
            "\u200c": "",  # Zero-width non-joiner
            "\u200d": "",  # Zero-width joiner
            "\ufeff": "",  # BOM
            "\u2028": "\n",  # Line separator
            "\u2029": "\n\n",  # Paragraph separator
        }

        for old, new in replacements.items():
            normalized = normalized.replace(old, new)

        return normalized

    @staticmethod
    def fix_encoding_issues(text: str) -> str:
        """
        Corrige problemas comuns de encoding.

        Args:
            text: Texto com possiveis problemas de encoding

        Returns:
            Texto corrigido
        """
        # Padroes comuns de encoding corrompido
        fixes = {
            "Ã¡": "á",
            "Ã©": "é",
            "Ã­": "í",
            "Ã³": "ó",
            "Ãº": "ú",
            "Ã£": "ã",
            "Ãµ": "õ",
            "Ã§": "ç",
            "Ã": "í",  # Caso especial
            "Â": "",  # Artefato de double-encoding
        }

        result = text
        for wrong, correct in fixes.items():
            result = result.replace(wrong, correct)

        return result

    def clean_page(self, text: str, track_stats: bool = False) -> str | tuple[str, CleaningStats]:
        """
        Limpa uma pagina de texto.

        Args:
            text: Texto da pagina
            track_stats: Se True, retorna estatisticas

        Returns:
            Texto limpo (e stats se solicitado)
        """
        original_length = len(text)
        patterns_matched: dict[str, int] = {}

        # Passo 1: Normalizacao Unicode
        result = self.normalize_unicode(text)

        # Passo 2: Correcao de encoding
        result = self.fix_encoding_issues(result)

        # Passo 3: Aplicar regras de limpeza
        rules_applied = 0
        for rule_name in RULE_ORDER:
            rule = self._rules.get_rule(rule_name)
            if rule is None:
                continue

            # Conta matches antes de aplicar
            matches = len(rule.pattern.findall(result))
            if matches > 0:
                patterns_matched[rule_name] = matches
                rules_applied += 1

            result = rule.apply(result)

        # Passo 4: Preservar estrutura se configurado
        if self.preserve_structure:
            # Garante que paragrafos mantenham separacao
            result = re.sub(r"\n{3,}", "\n\n", result)
        else:
            # Colapsa tudo em um unico bloco
            result = re.sub(r"\n+", " ", result)
            result = re.sub(r"\s+", " ", result)

        # Passo 5: Trim final
        result = result.strip()

        if track_stats:
            final_length = len(result)
            reduction = (
                (original_length - final_length) / original_length * 100
                if original_length > 0
                else 0.0
            )
            stats = CleaningStats(
                original_length=original_length,
                final_length=final_length,
                reduction_percent=round(reduction, 2),
                rules_applied=rules_applied,
                patterns_matched=patterns_matched,
            )
            return result, stats

        return result

    def clean_document(
        self, pages: list[str], track_stats: bool = False
    ) -> list[str] | tuple[list[str], list[CleaningStats]]:
        """
        Limpa multiplas paginas de um documento.

        Args:
            pages: Lista de textos de paginas
            track_stats: Se True, retorna estatisticas por pagina

        Returns:
            Lista de paginas limpas (e stats se solicitado)
        """
        if track_stats:
            cleaned_pages = []
            all_stats = []
            for page in pages:
                cleaned, stats = self.clean_page(page, track_stats=True)
                cleaned_pages.append(cleaned)
                all_stats.append(stats)
            return cleaned_pages, all_stats
        else:
            return [self.clean_page(page) for page in pages]

    def clean_markdown(self, markdown_content: str) -> str:
        """
        Limpa documento markdown preservando estrutura de paginas.

        Args:
            markdown_content: Conteudo do final.md

        Returns:
            Markdown com conteudo limpo
        """
        # Pattern para identificar headers de pagina
        page_pattern = re.compile(
            r"(##\s*\[\[PAGE_\d+\]\]\s*\[TYPE:\s*\w+\])",
            re.IGNORECASE,
        )

        # Divide em partes (header + conteudo)
        parts = page_pattern.split(markdown_content)

        result_parts = []
        for i, part in enumerate(parts):
            if page_pattern.match(part):
                # E um header de pagina - preserva intacto
                result_parts.append(part)
            else:
                # E conteudo - aplica limpeza
                cleaned = self.clean_page(part)
                result_parts.append(cleaned)

        return "\n".join(result_parts)

    def get_summary_stats(self, stats_list: list[CleaningStats]) -> dict:
        """
        Calcula estatisticas agregadas de limpeza.

        Args:
            stats_list: Lista de stats por pagina

        Returns:
            Dicionario com estatisticas agregadas
        """
        if not stats_list:
            return {
                "total_pages": 0,
                "total_original_chars": 0,
                "total_final_chars": 0,
                "avg_reduction_percent": 0.0,
                "total_rules_applied": 0,
                "most_common_patterns": [],
            }

        total_original = sum(s["original_length"] for s in stats_list)
        total_final = sum(s["final_length"] for s in stats_list)
        total_rules = sum(s["rules_applied"] for s in stats_list)

        # Agrega patterns matched
        pattern_counts: dict[str, int] = {}
        for stats in stats_list:
            for pattern, count in stats["patterns_matched"].items():
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + count

        # Ordena por frequencia
        sorted_patterns = sorted(
            pattern_counts.items(), key=lambda x: x[1], reverse=True
        )

        return {
            "total_pages": len(stats_list),
            "total_original_chars": total_original,
            "total_final_chars": total_final,
            "avg_reduction_percent": round(
                (total_original - total_final) / total_original * 100
                if total_original > 0
                else 0.0,
                2,
            ),
            "total_rules_applied": total_rules,
            "most_common_patterns": sorted_patterns[:10],
        }
