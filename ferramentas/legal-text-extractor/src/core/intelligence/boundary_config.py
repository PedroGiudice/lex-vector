"""
Configuracao de boundaries para deteccao de documentos genericos.

ATENCAO: Boundaries mal configurados podem CORTAR documentos.
Este modulo foi projetado com principios CONSERVADORES:

1. NA DUVIDA, NAO SEPARAR - Melhor documento grande que incompleto
2. BOUNDARY = INICIO - Detectamos onde comeca, nao onde termina
3. CONFIDENCE ALTO - So separa quando MUITO confiante (>= 0.8)
4. PRESERVAR CONTEXTO - Nunca cortar no meio de paragrafo

Referencia: docs/ARCHITECTURE_PRINCIPLES.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Pattern


class DocumentClass(Enum):
    """Classes de documentos por caracteristicas fisicas."""

    # Documentos formais com margens largas (contratos, procuracoes)
    FORMAL = "formal"

    # Documentos compactos com margens estreitas (boletos, comprovantes)
    COMPACT = "compact"

    # Documentos mistos ou desconhecidos
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BoundaryPattern:
    """
    Padrao individual para deteccao de boundary.

    Attributes:
        id: Identificador unico do padrao
        regex: Expressao regular compilada
        description: Descricao legivel do padrao
        document_type: Tipo de documento que este padrao indica
        confidence_base: Confianca base quando pattern casa (0.0-1.0)
        requires_line_start: Se True, pattern deve estar no inicio da linha
        context_lines_before: Linhas a preservar ANTES do match (seguranca)
    """

    id: str
    regex: Pattern
    description: str
    document_type: str
    confidence_base: float = 0.7
    requires_line_start: bool = True
    context_lines_before: int = 0  # Conservador: nao cortar contexto


@dataclass
class BoundaryConfig:
    """
    Configuracao adaptavel para deteccao de boundaries em documentos.

    PRINCIPIO FUNDAMENTAL:
    - Boundaries sao detectados pelo INICIO do proximo documento
    - NUNCA pelo fim do documento atual
    - Isso evita cortar assinaturas, rodapes, clausulas finais

    Attributes:
        min_confidence: Confianca minima para considerar boundary (ALTO = 0.8)
        document_class: Classe de documento para ajustar sensibilidade
        enabled: Se False, nao detecta boundaries (tudo e um unico bloco)
    """

    min_confidence: float = 0.8  # CONSERVADOR: so separa quando muito confiante
    document_class: DocumentClass = DocumentClass.UNKNOWN
    enabled: bool = True

    # Patterns de INICIO de documento (NUNCA de fim)
    _patterns: list[BoundaryPattern] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Inicializa patterns padrao se nenhum foi fornecido."""
        if not self._patterns:
            self._patterns = self._get_default_patterns()

    @staticmethod
    def _get_default_patterns() -> list[BoundaryPattern]:
        """
        Retorna patterns padrao CONSERVADORES para deteccao de boundaries.

        CUIDADO: Cada pattern aqui pode potencialmente SEPARAR documentos.
        Patterns muito genericos vao causar fragmentacao excessiva.
        Patterns muito especificos vao perder boundaries reais.

        Estrategia: Preferir FALSO NEGATIVO (nao separar) a FALSO POSITIVO (separar errado)
        """
        return [
            # ================================================================
            # PROCURACOES - Alta confianca (formato muito padronizado)
            # ================================================================
            BoundaryPattern(
                id="procuracao_ad_judicia",
                regex=re.compile(
                    r"^PROCURA[CÇ][AÃ]O\s+AD\s+JUDICIA",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Inicio de procuracao ad judicia",
                document_type="PROCURACAO",
                confidence_base=0.9,  # Alta - formato muito especifico
                requires_line_start=True,
                context_lines_before=0,
            ),
            BoundaryPattern(
                id="instrumento_mandato",
                regex=re.compile(
                    r"^INSTRUMENTO\s+(PARTICULAR\s+)?DE\s+MANDATO",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Inicio de instrumento de mandato",
                document_type="PROCURACAO",
                confidence_base=0.9,
                requires_line_start=True,
                context_lines_before=0,
            ),
            # ================================================================
            # CONTRATOS - Alta confianca
            # ================================================================
            BoundaryPattern(
                id="contrato_prestacao",
                regex=re.compile(
                    r"^CONTRATO\s+DE\s+PRESTA[CÇ][AÃ]O\s+DE\s+SERVI[CÇ]OS?",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Inicio de contrato de prestacao de servicos",
                document_type="CONTRATO",
                confidence_base=0.9,
                requires_line_start=True,
                context_lines_before=0,
            ),
            BoundaryPattern(
                id="contrato_social",
                regex=re.compile(
                    r"^CONTRATO\s+SOCIAL",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Inicio de contrato social",
                document_type="CONTRATO",
                confidence_base=0.9,
                requires_line_start=True,
                context_lines_before=0,
            ),
            BoundaryPattern(
                id="instrumento_particular",
                regex=re.compile(
                    r"^INSTRUMENTO\s+PARTICULAR",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Inicio de instrumento particular",
                document_type="CONTRATO",
                confidence_base=0.85,
                requires_line_start=True,
                context_lines_before=0,
            ),
            # ================================================================
            # NOTAS FISCAIS - Media-alta confianca
            # ================================================================
            BoundaryPattern(
                id="nota_fiscal_eletronica",
                regex=re.compile(
                    r"^(DANFE|NF-?E|NOTA\s+FISCAL\s+ELETR[OÔ]NICA)",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Inicio de nota fiscal eletronica",
                document_type="NOTA_FISCAL",
                confidence_base=0.85,
                requires_line_start=True,
                context_lines_before=0,
            ),
            BoundaryPattern(
                id="nota_fiscal_servico",
                regex=re.compile(
                    r"^NOTA\s+FISCAL\s+DE\s+SERVI[CÇ]O",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Inicio de nota fiscal de servico",
                document_type="NOTA_FISCAL",
                confidence_base=0.85,
                requires_line_start=True,
                context_lines_before=0,
            ),
            # ================================================================
            # COMPROVANTES - Media confianca (mais variacao)
            # ================================================================
            BoundaryPattern(
                id="comprovante_pagamento",
                regex=re.compile(
                    r"^COMPROVANTE\s+DE\s+(PAGAMENTO|TRANSFER[EÊ]NCIA|DEP[OÓ]SITO)",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Inicio de comprovante bancario",
                document_type="COMPROVANTE",
                confidence_base=0.8,
                requires_line_start=True,
                context_lines_before=0,
            ),
            # ================================================================
            # BOLETOS - Media confianca
            # ================================================================
            BoundaryPattern(
                id="boleto_bancario",
                regex=re.compile(
                    r"^(BOLETO\s+BANC[AÁ]RIO|FICHA\s+DE\s+COMPENSA[CÇ][AÃ]O)",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Inicio de boleto bancario",
                document_type="BOLETO",
                confidence_base=0.8,
                requires_line_start=True,
                context_lines_before=0,
            ),
            # ================================================================
            # MARCADORES EXPLICITOS - Alta confianca
            # ================================================================
            BoundaryPattern(
                id="doc_numerado",
                regex=re.compile(
                    r"^(DOC|DOCUMENTO)\s*[.:]?\s*\d+\s*$",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Marcador explicito de documento numerado",
                document_type="ANEXO_NUMERADO",
                confidence_base=0.85,
                requires_line_start=True,
                context_lines_before=0,
            ),
            BoundaryPattern(
                id="anexo_numerado",
                regex=re.compile(
                    r"^ANEXO\s*[IVX\d]+\s*[-:]?\s*",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Marcador explicito de anexo numerado",
                document_type="ANEXO_NUMERADO",
                confidence_base=0.85,
                requires_line_start=True,
                context_lines_before=0,
            ),
        ]

    @property
    def patterns(self) -> list[BoundaryPattern]:
        """Retorna lista de patterns ativos."""
        return self._patterns

    def add_pattern(self, pattern: BoundaryPattern) -> None:
        """
        Adiciona um pattern customizado.

        CUIDADO: Patterns muito genericos vao fragmentar documentos!
        """
        self._patterns.append(pattern)

    def get_patterns_for_class(self) -> list[BoundaryPattern]:
        """
        Retorna patterns filtrados pela classe de documento.

        Para documentos COMPACT (margens estreitas), usamos patterns
        mais especificos para evitar falsos positivos.
        """
        if self.document_class == DocumentClass.COMPACT:
            # Para documentos compactos, so patterns de alta confianca
            return [p for p in self._patterns if p.confidence_base >= 0.85]
        return self._patterns

    def adjust_for_margin(self, margin_ratio: float) -> None:
        """
        Ajusta configuracao baseado na razao de margem detectada.

        Args:
            margin_ratio: Proporcao de margem (0.0 = sem margem, 0.2 = 20% margem)
        """
        if margin_ratio < 0.05:
            # Margens muito estreitas - ser mais conservador
            self.document_class = DocumentClass.COMPACT
            self.min_confidence = 0.85  # Aumenta threshold
        elif margin_ratio > 0.15:
            # Margens largas - documento formal
            self.document_class = DocumentClass.FORMAL
            self.min_confidence = 0.75  # Pode relaxar um pouco
        else:
            self.document_class = DocumentClass.UNKNOWN
            self.min_confidence = 0.8  # Padrao conservador


# ============================================================================
# CONFIGURACOES PRE-DEFINIDAS
# ============================================================================


def get_conservative_config() -> BoundaryConfig:
    """
    Retorna configuracao CONSERVADORA (padrao recomendado).

    Prioriza NAO SEPARAR sobre separar incorretamente.
    Use quando nao tem certeza do tipo de documento.
    """
    return BoundaryConfig(
        min_confidence=0.85,
        document_class=DocumentClass.UNKNOWN,
        enabled=True,
    )


def get_formal_document_config() -> BoundaryConfig:
    """
    Retorna configuracao para documentos formais (contratos, procuracoes).

    Margens largas, formatacao padronizada.
    """
    return BoundaryConfig(
        min_confidence=0.75,
        document_class=DocumentClass.FORMAL,
        enabled=True,
    )


def get_compact_document_config() -> BoundaryConfig:
    """
    Retorna configuracao para documentos compactos (boletos, comprovantes).

    Margens estreitas, mais ruido visual.
    """
    return BoundaryConfig(
        min_confidence=0.9,  # MUITO conservador
        document_class=DocumentClass.COMPACT,
        enabled=True,
    )


def get_disabled_config() -> BoundaryConfig:
    """
    Retorna configuracao com boundary detection DESABILITADO.

    Use quando quer tratar todo o bloco ANEXOS como documento unico.
    """
    return BoundaryConfig(
        min_confidence=1.0,  # Impossivel atingir
        document_class=DocumentClass.UNKNOWN,
        enabled=False,
    )
