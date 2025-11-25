"""
Detector de boundaries entre documentos genericos.

PRINCIPIOS DE SEGURANCA:
1. BOUNDARY = INICIO do proximo documento (nunca fim do atual)
2. PRESERVAR CONTEXTO - Incluir linhas antes do match
3. CONFIDENCE ALTA - So separa quando muito confiante
4. VALIDACAO DUPLA - Confirma antes de separar

Este modulo NAO modifica texto - apenas DETECTA onde estao os boundaries.
A separacao efetiva e feita pelo chamador.

Referencia: docs/ARCHITECTURE_PRINCIPLES.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TypedDict

from .boundary_config import BoundaryConfig, BoundaryPattern, get_conservative_config


class BoundaryMatch(TypedDict):
    """Resultado de um match de boundary."""

    pattern_id: str
    document_type: str
    line_number: int  # Linha onde o boundary foi detectado (1-indexed)
    confidence: float
    matched_text: str
    context_start: int  # Linha onde o documento deve COMECAR (pode ser antes do match)


class BoundaryResult(TypedDict):
    """Resultado da deteccao de boundaries em um bloco de texto."""

    total_boundaries: int
    boundaries: list[BoundaryMatch]
    segments: list[dict]  # Lista de {start_line, end_line, document_type}


@dataclass
class BoundaryDetector:
    """
    Detector de boundaries entre documentos genericos.

    USO:
        detector = BoundaryDetector()
        result = detector.detect(texto)

        for segment in result["segments"]:
            print(f"Documento {segment['document_type']}: linhas {segment['start_line']}-{segment['end_line']}")

    CUIDADO:
        Este detector e CONSERVADOR por design.
        Preferimos NAO detectar um boundary real (falso negativo)
        do que detectar um boundary falso (falso positivo) e CORTAR um documento.
    """

    config: BoundaryConfig = None

    def __post_init__(self) -> None:
        """Inicializa com config padrao se nenhuma fornecida."""
        if self.config is None:
            self.config = get_conservative_config()

    def detect(self, text: str) -> BoundaryResult:
        """
        Detecta boundaries em um bloco de texto.

        Args:
            text: Texto completo a analisar

        Returns:
            BoundaryResult com boundaries detectados e segmentos

        IMPORTANTE:
            - Linha 1 e sempre o inicio do primeiro documento
            - Boundaries indicam onde COMECA o proximo documento
            - O fim de um documento e a linha antes do proximo boundary
        """
        if not self.config.enabled:
            # Boundary detection desabilitado - retorna texto como bloco unico
            lines = text.split("\n")
            return BoundaryResult(
                total_boundaries=0,
                boundaries=[],
                segments=[{
                    "start_line": 1,
                    "end_line": len(lines),
                    "document_type": "UNKNOWN",
                    "confidence": 1.0,
                }],
            )

        # Encontra todos os matches
        matches = self._find_all_matches(text)

        # Filtra por confidence minima
        filtered_matches = [
            m for m in matches
            if m["confidence"] >= self.config.min_confidence
        ]

        # Remove duplicatas proximas (mesmo documento detectado multiplas vezes)
        deduplicated = self._deduplicate_matches(filtered_matches)

        # Constroi segmentos
        segments = self._build_segments(text, deduplicated)

        return BoundaryResult(
            total_boundaries=len(deduplicated),
            boundaries=deduplicated,
            segments=segments,
        )

    def _find_all_matches(self, text: str) -> list[BoundaryMatch]:
        """
        Encontra todos os matches de patterns no texto.

        NOTA: Patterns sao aplicados linha por linha para garantir
        que requires_line_start funcione corretamente.
        """
        matches: list[BoundaryMatch] = []
        lines = text.split("\n")
        patterns = self.config.get_patterns_for_class()

        for line_num, line in enumerate(lines, start=1):
            # Pula linhas vazias ou muito curtas
            if len(line.strip()) < 3:
                continue

            for pattern in patterns:
                match = self._try_pattern(pattern, line, line_num)
                if match:
                    matches.append(match)

        # Ordena por linha
        matches.sort(key=lambda m: m["line_number"])

        return matches

    def _try_pattern(
        self,
        pattern: BoundaryPattern,
        line: str,
        line_num: int,
    ) -> BoundaryMatch | None:
        """
        Tenta aplicar um pattern a uma linha.

        Returns:
            BoundaryMatch se casou, None caso contrario
        """
        # Normaliza linha para matching
        normalized = line.strip()

        # Tenta o match
        match = pattern.regex.search(normalized)
        if not match:
            return None

        # Verifica se requires_line_start
        if pattern.requires_line_start and match.start() > 0:
            # Pattern requer inicio de linha mas match nao esta no inicio
            return None

        # Calcula context_start (linha onde documento deve comecar)
        context_start = max(1, line_num - pattern.context_lines_before)

        return BoundaryMatch(
            pattern_id=pattern.id,
            document_type=pattern.document_type,
            line_number=line_num,
            confidence=pattern.confidence_base,
            matched_text=match.group(0)[:50],  # Limita tamanho
            context_start=context_start,
        )

    def _deduplicate_matches(
        self,
        matches: list[BoundaryMatch],
        min_gap: int = 3,
    ) -> list[BoundaryMatch]:
        """
        Remove matches duplicados muito proximos.

        Se dois matches estao a menos de min_gap linhas de distancia,
        mantemos apenas o de maior confidence.

        Args:
            matches: Lista de matches ordenada por linha
            min_gap: Distancia minima em linhas entre boundaries

        Returns:
            Lista filtrada de matches
        """
        if not matches:
            return []

        result: list[BoundaryMatch] = []
        last_match: BoundaryMatch | None = None

        for match in matches:
            if last_match is None:
                result.append(match)
                last_match = match
                continue

            gap = match["line_number"] - last_match["line_number"]

            if gap < min_gap:
                # Matches muito proximos - manter o de maior confidence
                if match["confidence"] > last_match["confidence"]:
                    result[-1] = match
                    last_match = match
            else:
                # Gap suficiente - adicionar
                result.append(match)
                last_match = match

        return result

    def _build_segments(
        self,
        text: str,
        boundaries: list[BoundaryMatch],
    ) -> list[dict]:
        """
        Constroi segmentos a partir dos boundaries detectados.

        Cada segmento representa um documento individual.

        REGRA FUNDAMENTAL:
        - Segmento N termina na linha ANTES do boundary N+1
        - Isso evita cortar conteudo no meio
        """
        lines = text.split("\n")
        total_lines = len(lines)

        if not boundaries:
            # Sem boundaries - documento unico
            return [{
                "start_line": 1,
                "end_line": total_lines,
                "document_type": "UNKNOWN",
                "confidence": 1.0,
            }]

        segments: list[dict] = []

        # Primeiro segmento: linha 1 ate antes do primeiro boundary
        first_boundary = boundaries[0]
        if first_boundary["context_start"] > 1:
            # Ha conteudo antes do primeiro boundary detectado
            segments.append({
                "start_line": 1,
                "end_line": first_boundary["context_start"] - 1,
                "document_type": "UNKNOWN",  # Nao sabemos o tipo
                "confidence": 0.5,  # Baixa confidence
            })

        # Segmentos intermediarios
        for i, boundary in enumerate(boundaries):
            # Inicio do segmento atual
            start = boundary["context_start"]

            # Fim do segmento: linha antes do proximo boundary, ou fim do texto
            if i + 1 < len(boundaries):
                end = boundaries[i + 1]["context_start"] - 1
            else:
                end = total_lines

            # Valida que segmento tem pelo menos 1 linha
            if end >= start:
                segments.append({
                    "start_line": start,
                    "end_line": end,
                    "document_type": boundary["document_type"],
                    "confidence": boundary["confidence"],
                })

        return segments

    def detect_in_pages(
        self,
        pages: list[dict],
    ) -> list[dict]:
        """
        Detecta boundaries em uma lista de paginas.

        Util para processar output do segmenter existente.

        Args:
            pages: Lista de dicts com "page_num", "content", etc.

        Returns:
            Lista de paginas com boundaries anotados
        """
        result = []

        for page in pages:
            content = page.get("content", "")
            page_result = self.detect(content)

            # Copia dados originais e adiciona boundaries
            annotated = dict(page)
            annotated["boundaries"] = page_result["boundaries"]
            annotated["boundary_count"] = page_result["total_boundaries"]

            result.append(annotated)

        return result


# ============================================================================
# FUNCOES DE CONVENIENCIA
# ============================================================================


def detect_boundaries_conservative(text: str) -> BoundaryResult:
    """
    Detecta boundaries com configuracao CONSERVADORA (padrao recomendado).

    Use quando nao tem certeza do tipo de documento.
    Preferira NAO separar sobre separar incorretamente.
    """
    detector = BoundaryDetector(config=get_conservative_config())
    return detector.detect(text)


def has_boundary_markers(text: str) -> bool:
    """
    Verifica rapidamente se texto contem marcadores de boundary.

    Util para decidir se vale a pena rodar deteccao completa.
    NAO garante que boundaries serao detectados (confidence pode ser baixa).
    """
    # Patterns rapidos para checagem inicial
    quick_patterns = [
        r"^(DOC|DOCUMENTO|ANEXO)\s*[.:]?\s*\d+",
        r"^PROCURA[CÇ][AÃ]O",
        r"^CONTRATO\s+",
        r"^NOTA\s+FISCAL",
        r"^COMPROVANTE\s+DE",
    ]

    combined = re.compile(
        "|".join(quick_patterns),
        re.IGNORECASE | re.MULTILINE,
    )

    return bool(combined.search(text))
