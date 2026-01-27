"""
Detector de boundaries entre secoes de autos processuais.

Herda abordagem conservadora do boundary_detector.py:
- BOUNDARY = INICIO da proxima secao
- PRESERVAR CONTEXTO
- CONFIDENCE ALTA para separar
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from .peca_patterns import SecaoPatternConfig, SecaoType, get_default_config


class SecaoBoundary(TypedDict):
    """Resultado de um match de boundary."""

    pattern_id: str
    secao_type: str  # SecaoType.value
    line_number: int
    char_position: int
    confidence: float
    matched_text: str


class SecaoDetectionResult(TypedDict):
    """Resultado da deteccao de boundaries."""

    total_boundaries: int
    boundaries: list[SecaoBoundary]


@dataclass
class SecaoDetector:
    """
    Detector de boundaries entre secoes de autos.

    Principios:
    1. Boundaries indicam INICIO da proxima secao
    2. Conservador: na duvida, NAO separa
    3. Retorna boundaries ordenados por posicao
    """

    config: SecaoPatternConfig = None

    def __post_init__(self) -> None:
        if self.config is None:
            self.config = get_default_config()

    def detect(self, text: str) -> SecaoDetectionResult:
        """
        Detecta boundaries no texto.

        Args:
            text: Texto completo do documento

        Returns:
            SecaoDetectionResult com boundaries ordenados
        """
        if not self.config.enabled:
            return {"total_boundaries": 0, "boundaries": []}

        boundaries: list[SecaoBoundary] = []
        lines = text.split("\n")

        current_char_pos = 0
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()

            for pattern in self.config.patterns:
                match = pattern.regex.search(line if not pattern.requires_line_start else line_stripped)

                if match and pattern.confidence_base >= self.config.min_confidence:
                    boundary: SecaoBoundary = {
                        "pattern_id": pattern.id,
                        "secao_type": pattern.secao_type.value,
                        "line_number": line_num,
                        "char_position": current_char_pos + match.start(),
                        "confidence": pattern.confidence_base,
                        "matched_text": match.group(0)[:100],  # Limita tamanho
                    }
                    boundaries.append(boundary)
                    break  # Um pattern por linha

            current_char_pos += len(line) + 1  # +1 para \n

        # Ordenar por posicao e remover duplicatas proximas (< 50 chars)
        boundaries = self._deduplicate_boundaries(boundaries)

        return {
            "total_boundaries": len(boundaries),
            "boundaries": boundaries,
        }

    def _deduplicate_boundaries(self, boundaries: list[SecaoBoundary]) -> list[SecaoBoundary]:
        """
        Remove boundaries duplicados ou muito proximos.

        Se dois boundaries estao a menos de 50 chars, mantem o de maior confidence.
        """
        if not boundaries:
            return []

        # Ordenar por posicao
        sorted_boundaries = sorted(boundaries, key=lambda b: b["char_position"])

        deduplicated = [sorted_boundaries[0]]
        for boundary in sorted_boundaries[1:]:
            last = deduplicated[-1]
            distance = boundary["char_position"] - last["char_position"]

            if distance < 50:
                # Muito proximo - manter o de maior confidence
                if boundary["confidence"] > last["confidence"]:
                    deduplicated[-1] = boundary
            else:
                deduplicated.append(boundary)

        return deduplicated

    def detect_with_segments(self, text: str) -> tuple[SecaoDetectionResult, list[dict]]:
        """
        Detecta boundaries e retorna segmentos de texto.

        Returns:
            Tuple de (detection_result, segments)
            Cada segment tem: start_pos, end_pos, secao_type, content
        """
        result = self.detect(text)
        boundaries = result["boundaries"]

        if not boundaries:
            # Documento inteiro como uma secao
            return result, [
                {
                    "start_pos": 0,
                    "end_pos": len(text),
                    "secao_type": SecaoType.OUTRO.value,
                    "confidence": 0.5,
                    "content": text.strip(),
                }
            ]

        segments = []

        # Primeiro segmento (antes do primeiro boundary) - so se tiver conteudo
        first_content = text[: boundaries[0]["char_position"]].strip()
        if first_content and len(first_content) > 10:  # Ignora preambulos vazios
            segments.append({
                "start_pos": 0,
                "end_pos": boundaries[0]["char_position"],
                "secao_type": SecaoType.OUTRO.value,
                "confidence": 0.5,
                "content": first_content,
            })

        # Segmentos entre boundaries
        for i, boundary in enumerate(boundaries):
            start = boundary["char_position"]
            end = boundaries[i + 1]["char_position"] if i + 1 < len(boundaries) else len(text)

            segments.append({
                "start_pos": start,
                "end_pos": end,
                "secao_type": boundary["secao_type"],
                "confidence": boundary["confidence"],
                "content": text[start:end].strip(),
                "pattern_matched": boundary["pattern_id"],
                "matched_text": boundary["matched_text"],
            })

        return result, segments
