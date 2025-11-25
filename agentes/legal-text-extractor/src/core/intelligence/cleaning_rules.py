"""
Padroes regex para limpeza avancada de texto juridico.

Baseado em:
- legalnlp (Felipe Maia Polo)
- verbose-correct-doodle (legado interno)
- Padroes TJSP/PJe

Responsabilidades:
- Definir padroes de limpeza categorizados
- Fornecer interface de aplicacao de regras
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


# =============================================================================
# PADROES DE LIMPEZA
# =============================================================================

CLEANING_PATTERNS: dict[str, dict[str, str | Callable[[re.Match], str]]] = {
    # -------------------------------------------------------------------------
    # REMOCAO DE RUIDO
    # -------------------------------------------------------------------------
    "remove_page_numbers": {
        "pattern": r"\n\s*\d{1,4}\s*\n",
        "replacement": "\n",
        "description": "Remove numeros de pagina isolados",
    },
    "remove_empty_lines_excess": {
        "pattern": r"\n{3,}",
        "replacement": "\n\n",
        "description": "Reduz multiplas linhas vazias para no maximo 2",
    },
    "remove_header_noise": {
        "pattern": r"^(Documento assinado digitalmente|Assinado eletronicamente|Certificado por).*$",
        "replacement": "",
        "description": "Remove cabecalhos de assinatura digital",
        "flags": re.MULTILINE | re.IGNORECASE,
    },
    "remove_footer_noise": {
        "pattern": r"(Pagina \d+ de \d+|Página \d+ de \d+|fls?\.\s*\d+).*$",
        "replacement": "",
        "description": "Remove rodapes de paginacao",
        "flags": re.MULTILINE | re.IGNORECASE,
    },

    # -------------------------------------------------------------------------
    # CORRECAO DE QUEBRAS
    # -------------------------------------------------------------------------
    "fix_hyphenated_words": {
        "pattern": r"(\w+)-\s*\n\s*(\w+)",
        "replacement": r"\1\2",
        "description": "Junta palavras hifenizadas na quebra de linha",
    },
    "fix_broken_sentences": {
        "pattern": r"([a-zA-Z,;])\s*\n\s*([a-z])",
        "replacement": r"\1 \2",
        "description": "Junta sentencas quebradas incorretamente",
    },

    # -------------------------------------------------------------------------
    # NORMALIZACAO DE FORMATOS JURIDICOS
    # -------------------------------------------------------------------------
    "normalize_cnj": {
        "pattern": r"(\d{7})-?(\d{2})\.?(\d{4})\.?(\d)\.?(\d{2})\.?(\d{4})",
        "replacement": r"\1-\2.\3.\4.\5.\6",
        "description": "Normaliza numero CNJ para formato padrao",
    },
    "normalize_oab": {
        "pattern": r"(OAB|Inscri[cç][aã]o)\s*[/.:]*\s*([A-Z]{2})?\s*[/.:]*\s*(\d+)",
        "replacement": r"OAB/\2 \3",
        "description": "Normaliza numero OAB",
        "flags": re.IGNORECASE,
    },

    # -------------------------------------------------------------------------
    # MASCARAMENTO (PRIVACIDADE)
    # -------------------------------------------------------------------------
    "mask_cpf": {
        "pattern": r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
        "replacement": "[CPF]",
        "description": "Mascara CPF",
    },
    "mask_cnpj": {
        "pattern": r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}",
        "replacement": "[CNPJ]",
        "description": "Mascara CNPJ",
    },
    "mask_email": {
        "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "replacement": "[EMAIL]",
        "description": "Mascara email",
    },
    "mask_phone": {
        "pattern": r"\(?\d{2}\)?\s*\d{4,5}-?\d{4}",
        "replacement": "[TELEFONE]",
        "description": "Mascara telefone",
    },

    # -------------------------------------------------------------------------
    # NORMALIZACAO DE ESPACAMENTO
    # -------------------------------------------------------------------------
    "normalize_spaces": {
        "pattern": r"[ \t]+",
        "replacement": " ",
        "description": "Normaliza espacos multiplos",
    },
    "trim_lines": {
        "pattern": r"^[ \t]+|[ \t]+$",
        "replacement": "",
        "description": "Remove espacos no inicio/fim de linhas",
        "flags": re.MULTILINE,
    },

    # -------------------------------------------------------------------------
    # LIMPEZA DE CARACTERES ESPECIAIS
    # -------------------------------------------------------------------------
    "remove_control_chars": {
        "pattern": r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
        "replacement": "",
        "description": "Remove caracteres de controle",
    },
    "normalize_quotes": {
        "pattern": r"[""„‟]",
        "replacement": '"',
        "description": "Normaliza aspas para ASCII",
    },
    "normalize_apostrophe": {
        "pattern": r"[''‚‛]",
        "replacement": "'",
        "description": "Normaliza apostrofos para ASCII",
    },
    "normalize_dashes": {
        "pattern": r"[–—―]",
        "replacement": "-",
        "description": "Normaliza tracos longos para hifen",
    },
}

# Regras que NAO devem ser aplicadas por padrao (requerem opt-in)
OPTIONAL_RULES = {"mask_cpf", "mask_cnpj", "mask_email", "mask_phone"}

# Ordem de aplicacao das regras (importante para evitar conflitos)
RULE_ORDER = [
    # Primeiro: remover ruido
    "remove_control_chars",
    "remove_header_noise",
    "remove_footer_noise",
    "remove_page_numbers",
    # Segundo: corrigir quebras
    "fix_hyphenated_words",
    "fix_broken_sentences",
    # Terceiro: normalizar
    "normalize_cnj",
    "normalize_oab",
    "normalize_quotes",
    "normalize_apostrophe",
    "normalize_dashes",
    # Quarto: espacamento
    "normalize_spaces",
    "trim_lines",
    "remove_empty_lines_excess",
    # Ultimo: mascaramento (opcional)
    # "mask_cpf", "mask_cnpj", "mask_email", "mask_phone"
]


@dataclass
class CleaningRule:
    """Uma regra de limpeza individual."""

    name: str
    pattern: re.Pattern
    replacement: str | Callable[[re.Match], str]
    description: str

    def apply(self, text: str) -> str:
        """Aplica a regra ao texto."""
        if callable(self.replacement):
            return self.pattern.sub(self.replacement, text)
        return self.pattern.sub(self.replacement, text)


class CleaningRules:
    """Gerenciador de regras de limpeza."""

    def __init__(
        self,
        include_optional: bool = False,
        custom_rules: dict[str, dict] | None = None,
    ):
        """
        Inicializa gerenciador de regras.

        Args:
            include_optional: Se True, inclui regras de mascaramento
            custom_rules: Regras adicionais personalizadas
        """
        self.rules: dict[str, CleaningRule] = {}
        self._compile_rules(include_optional, custom_rules)

    def _compile_rules(
        self,
        include_optional: bool,
        custom_rules: dict[str, dict] | None,
    ) -> None:
        """Compila todas as regras em objetos CleaningRule."""
        # Regras padrao
        for name, rule_def in CLEANING_PATTERNS.items():
            # Pula regras opcionais se nao solicitadas
            if not include_optional and name in OPTIONAL_RULES:
                continue

            flags = rule_def.get("flags", 0)
            pattern = re.compile(rule_def["pattern"], flags)
            replacement = rule_def["replacement"]
            description = rule_def.get("description", "")

            self.rules[name] = CleaningRule(
                name=name,
                pattern=pattern,
                replacement=replacement,
                description=description,
            )

        # Regras customizadas
        if custom_rules:
            for name, rule_def in custom_rules.items():
                flags = rule_def.get("flags", 0)
                pattern = re.compile(rule_def["pattern"], flags)
                replacement = rule_def["replacement"]
                description = rule_def.get("description", "")

                self.rules[name] = CleaningRule(
                    name=name,
                    pattern=pattern,
                    replacement=replacement,
                    description=description,
                )

    def apply_all(self, text: str) -> str:
        """
        Aplica todas as regras na ordem correta.

        Args:
            text: Texto original

        Returns:
            Texto limpo
        """
        result = text
        for rule_name in RULE_ORDER:
            if rule_name in self.rules:
                result = self.rules[rule_name].apply(result)
        return result

    def apply_specific(self, text: str, rule_names: list[str]) -> str:
        """
        Aplica regras especificas.

        Args:
            text: Texto original
            rule_names: Lista de nomes de regras a aplicar

        Returns:
            Texto limpo
        """
        result = text
        for name in rule_names:
            if name in self.rules:
                result = self.rules[name].apply(result)
        return result

    def get_rule(self, name: str) -> CleaningRule | None:
        """Retorna uma regra pelo nome."""
        return self.rules.get(name)

    def list_rules(self) -> list[str]:
        """Lista todas as regras disponiveis."""
        return list(self.rules.keys())
