"""
Configuracao de padroes para organizacao de autos processuais.

OBJETIVO: Organizar documentos para facilitar compreensao por LLMs.
NAO E classificacao juridica precisa - e organizacao estrutural.

Categorias simples:
- PETICAO: manifestacoes das partes (inicial, contestacao, replica, recursos)
- DOCUMENTOS: anexos, procuracoes, comprovantes
- DECISAO: pronunciamentos judiciais (despachos, decisoes, sentencas, acordaos)
- PARECER: manifestacoes de terceiros (MP, peritos)
- ATA: registros de audiencias

Principios CONSERVADORES:
1. NA DUVIDA, NAO SEPARAR
2. BOUNDARY = INICIO da proxima secao
3. Preferir falso negativo a falso positivo
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Pattern


class SecaoType(Enum):
    """Tipos de secao para organizacao de autos (simplificado)."""

    PETICAO = "peticao"          # Manifestacoes das partes
    DOCUMENTOS = "documentos"    # Anexos e comprovantes
    DECISAO = "decisao"          # Pronunciamentos judiciais
    PARECER = "parecer"          # MP, peritos, terceiros
    ATA = "ata"                  # Audiencias
    OUTRO = "outro"              # Nao identificado


@dataclass(frozen=True)
class SecaoPattern:
    """
    Padrao para deteccao de inicio de secao.

    Attributes:
        id: Identificador unico
        regex: Expressao regular compilada
        description: Descricao legivel
        secao_type: Tipo de secao
        confidence_base: Confianca quando pattern casa (0.0-1.0)
        requires_line_start: Se True, deve estar no inicio da linha
    """

    id: str
    regex: Pattern
    description: str
    secao_type: SecaoType
    confidence_base: float = 0.8
    requires_line_start: bool = True


@dataclass
class SecaoPatternConfig:
    """
    Configuracao para organizacao de autos em secoes.

    Attributes:
        min_confidence: Confianca minima para criar boundary
        enabled: Se False, retorna documento como secao unica
    """

    min_confidence: float = 0.75
    enabled: bool = True
    _patterns: list[SecaoPattern] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self._patterns:
            self._patterns = self._get_default_patterns()

    @staticmethod
    def _get_default_patterns() -> list[SecaoPattern]:
        """
        Patterns para organizacao de autos.

        Focado em ORGANIZACAO, nao classificacao juridica detalhada.
        """
        return [
            # ================================================================
            # PETICAO - Manifestacoes das partes
            # ================================================================
            SecaoPattern(
                id="peticao_enderecamento",
                regex=re.compile(
                    r"^EXCELENT[ÍI]SSIM[OA]\s+SENHOR",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Enderecamento de peticao",
                secao_type=SecaoType.PETICAO,
                confidence_base=0.90,
            ),
            SecaoPattern(
                id="peticao_contestacao",
                regex=re.compile(
                    r"^CONTESTA[CÇ][AÃ]O",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Contestacao",
                secao_type=SecaoType.PETICAO,
                confidence_base=0.92,
            ),
            SecaoPattern(
                id="peticao_replica",
                regex=re.compile(
                    r"^R[EÉ]PLICA",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Replica",
                secao_type=SecaoType.PETICAO,
                confidence_base=0.90,
            ),
            SecaoPattern(
                id="peticao_recurso",
                regex=re.compile(
                    r"^(?:APELA[CÇ][AÃ]O|AGRAVO|EMBARGOS|RECURSO|RAZ[OÕ]ES|CONTRARRAZ[OÕ]ES)",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Recurso ou razoes",
                secao_type=SecaoType.PETICAO,
                confidence_base=0.88,
            ),
            SecaoPattern(
                id="peticao_manifestacao",
                regex=re.compile(
                    r"^(?:MANIFESTA[CÇ][AÃ]O|PETI[CÇ][AÃ]O)",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Manifestacao ou peticao generica",
                secao_type=SecaoType.PETICAO,
                confidence_base=0.85,
            ),
            # ================================================================
            # DOCUMENTOS - Anexos e comprovantes
            # ================================================================
            SecaoPattern(
                id="doc_procuracao",
                regex=re.compile(
                    r"^(?:PROCURA[CÇ][AÃ]O|INSTRUMENTO\s+(?:PARTICULAR\s+)?DE\s+MANDATO)",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Procuracao",
                secao_type=SecaoType.DOCUMENTOS,
                confidence_base=0.90,
            ),
            SecaoPattern(
                id="doc_contrato",
                regex=re.compile(
                    r"^CONTRATO",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Contrato",
                secao_type=SecaoType.DOCUMENTOS,
                confidence_base=0.85,
            ),
            SecaoPattern(
                id="doc_anexo",
                regex=re.compile(
                    r"^(?:ANEXO|DOC(?:UMENTO)?)\s*[.:IVX\d]+",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Anexo ou documento numerado",
                secao_type=SecaoType.DOCUMENTOS,
                confidence_base=0.85,
            ),
            SecaoPattern(
                id="doc_comprovante",
                regex=re.compile(
                    r"^COMPROVANTE",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Comprovante",
                secao_type=SecaoType.DOCUMENTOS,
                confidence_base=0.82,
            ),
            SecaoPattern(
                id="doc_nota_fiscal",
                regex=re.compile(
                    r"^(?:NOTA\s+FISCAL|DANFE|NF-?E)",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Nota fiscal",
                secao_type=SecaoType.DOCUMENTOS,
                confidence_base=0.85,
            ),
            # ================================================================
            # DECISAO - Pronunciamentos judiciais
            # ================================================================
            SecaoPattern(
                id="decisao_sentenca",
                regex=re.compile(
                    r"^SENTEN[CÇ]A",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Sentenca",
                secao_type=SecaoType.DECISAO,
                confidence_base=0.95,
            ),
            SecaoPattern(
                id="decisao_acordao",
                regex=re.compile(
                    r"^AC[OÓ]RD[AÃ]O",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Acordao",
                secao_type=SecaoType.DECISAO,
                confidence_base=0.95,
            ),
            SecaoPattern(
                id="decisao_despacho",
                regex=re.compile(
                    r"^DESPACHO",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Despacho",
                secao_type=SecaoType.DECISAO,
                confidence_base=0.90,
            ),
            SecaoPattern(
                id="decisao_interlocutoria",
                regex=re.compile(
                    r"^DECIS[AÃ]O(?:\s+INTERLOCUT[OÓ]RIA)?",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Decisao",
                secao_type=SecaoType.DECISAO,
                confidence_base=0.88,
            ),
            SecaoPattern(
                id="decisao_vistos",
                regex=re.compile(
                    r"^Vistos(?:\s+e\s+examinados)?[.,]",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Vistos (abertura de decisao)",
                secao_type=SecaoType.DECISAO,
                confidence_base=0.82,
            ),
            # ================================================================
            # PARECER - MP, peritos, terceiros
            # ================================================================
            SecaoPattern(
                id="parecer_titulo",
                regex=re.compile(
                    r"^PARECER",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Parecer",
                secao_type=SecaoType.PARECER,
                confidence_base=0.90,
            ),
            SecaoPattern(
                id="parecer_laudo",
                regex=re.compile(
                    r"^LAUDO\s+(?:PERICIAL|T[EÉ]CNICO)",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Laudo pericial",
                secao_type=SecaoType.PARECER,
                confidence_base=0.90,
            ),
            SecaoPattern(
                id="parecer_mp",
                regex=re.compile(
                    r"^(?:PROMO[CÇ][AÃ]O|MANIFESTA[CÇ][AÃ]O)\s+(?:DO\s+)?MINIST[EÉ]RIO\s+P[UÚ]BLICO",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Manifestacao do MP",
                secao_type=SecaoType.PARECER,
                confidence_base=0.88,
            ),
            # ================================================================
            # ATA - Audiencias
            # ================================================================
            SecaoPattern(
                id="ata_audiencia",
                regex=re.compile(
                    r"^(?:ATA|TERMO)\s+DE\s+AUDI[EÊ]NCIA",
                    re.IGNORECASE | re.MULTILINE,
                ),
                description="Ata de audiencia",
                secao_type=SecaoType.ATA,
                confidence_base=0.92,
            ),
        ]

    @property
    def patterns(self) -> list[SecaoPattern]:
        """Retorna lista de patterns ativos."""
        return self._patterns

    def get_patterns_by_type(self, secao_type: SecaoType) -> list[SecaoPattern]:
        """Retorna patterns filtrados por tipo."""
        return [p for p in self._patterns if p.secao_type == secao_type]


# ============================================================================
# CONFIGURACOES PRE-DEFINIDAS
# ============================================================================


def get_default_config() -> SecaoPatternConfig:
    """Configuracao padrao (conservadora)."""
    return SecaoPatternConfig(min_confidence=0.80, enabled=True)


def get_disabled_config() -> SecaoPatternConfig:
    """Deteccao desabilitada - documento como secao unica."""
    return SecaoPatternConfig(min_confidence=1.0, enabled=False)
