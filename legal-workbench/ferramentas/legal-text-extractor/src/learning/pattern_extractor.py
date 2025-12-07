"""Extração de padrões de documentos validados"""
import re
import logging
from collections import Counter
from typing import Optional
from dataclasses import dataclass

from .schemas import ExtractionResult, ExtractedSection, ValidationStatus, SectionType
from .storage import LearningStorage

logger = logging.getLogger(__name__)


@dataclass
class SectionPattern:
    """Padrão identificado em um tipo de seção"""
    section_type: SectionType
    start_keywords: list[str]  # Palavras/frases que marcam início
    end_keywords: list[str]    # Palavras/frases que marcam fim
    common_markers: list[str]  # Marcadores comuns encontrados
    avg_length: int            # Comprimento médio (chars)
    confidence: float          # Confiança no padrão (baseado em frequency)


class PatternExtractor:
    """
    Extrai padrões de documentos validados para melhorar prompts.

    Analisa seções aprovadas e identifica:
    - Palavras-chave comuns no início/fim de seções
    - Marcadores estruturais frequentes
    - Comprimento médio de cada tipo de seção
    """

    def __init__(self, storage: Optional[LearningStorage] = None):
        """
        Inicializa extractor.

        Args:
            storage: LearningStorage instance (cria novo se None)
        """
        self.storage = storage or LearningStorage()
        logger.info("PatternExtractor initialized")

    def extract_patterns(
        self,
        min_samples: int = 3,
        min_confidence: float = 0.6
    ) -> list[SectionPattern]:
        """
        Extrai padrões de todas as extrações aprovadas.

        Args:
            min_samples: Número mínimo de amostras para criar padrão
            min_confidence: Confiança mínima para incluir padrão

        Returns:
            Lista de SectionPattern identificados
        """
        logger.info("Extracting patterns from approved extractions...")

        # Carregar todas as extrações aprovadas
        approved = self.storage.list_extractions(status=ValidationStatus.APPROVED)

        if not approved:
            logger.warning("No approved extractions found")
            return []

        # Agrupar seções por tipo
        sections_by_type: dict[SectionType, list[ExtractedSection]] = {}

        for extraction in approved:
            for section in extraction.predicted_sections:
                if section.type not in sections_by_type:
                    sections_by_type[section.type] = []
                sections_by_type[section.type].append(section)

        # Extrair padrões para cada tipo
        patterns = []

        for section_type, sections in sections_by_type.items():
            if len(sections) < min_samples:
                logger.debug(
                    f"Skipping {section_type.value}: insufficient samples "
                    f"({len(sections)} < {min_samples})"
                )
                continue

            pattern = self._extract_pattern_for_type(section_type, sections)

            if pattern.confidence >= min_confidence:
                patterns.append(pattern)
                logger.info(
                    f"Pattern extracted: {section_type.value} "
                    f"(samples={len(sections)}, confidence={pattern.confidence:.2f})"
                )

        return patterns

    def _extract_pattern_for_type(
        self,
        section_type: SectionType,
        sections: list[ExtractedSection]
    ) -> SectionPattern:
        """
        Extrai padrão para um tipo específico de seção.

        Args:
            section_type: Tipo da seção
            sections: Lista de seções desse tipo

        Returns:
            SectionPattern identificado
        """
        # Extrair início e fim de cada seção
        start_texts = [self._get_start_text(s.content) for s in sections]
        end_texts = [self._get_end_text(s.content) for s in sections]

        # Identificar palavras-chave comuns
        start_keywords = self._extract_common_keywords(start_texts, top_n=5)
        end_keywords = self._extract_common_keywords(end_texts, top_n=5)

        # Extrair marcadores (maiúsculas, pontuação especial, etc)
        markers = self._extract_markers(sections)

        # Calcular comprimento médio
        avg_length = sum(len(s.content) for s in sections) / len(sections)

        # Calcular confiança baseada em consistência
        confidence = self._calculate_pattern_confidence(sections, start_keywords, end_keywords)

        return SectionPattern(
            section_type=section_type,
            start_keywords=start_keywords,
            end_keywords=end_keywords,
            common_markers=markers,
            avg_length=int(avg_length),
            confidence=confidence
        )

    def _get_start_text(self, content: str, n_chars: int = 200) -> str:
        """Retorna primeiros n_chars do conteúdo"""
        return content[:n_chars].strip()

    def _get_end_text(self, content: str, n_chars: int = 200) -> str:
        """Retorna últimos n_chars do conteúdo"""
        return content[-n_chars:].strip()

    def _extract_common_keywords(self, texts: list[str], top_n: int = 5) -> list[str]:
        """
        Extrai palavras-chave mais comuns de uma lista de textos.

        Args:
            texts: Lista de textos
            top_n: Número de keywords a retornar

        Returns:
            Lista de keywords mais frequentes
        """
        # Tokenizar e contar palavras significativas (> 3 chars, sem stopwords)
        word_counter = Counter()

        stopwords = {
            'que', 'para', 'com', 'por', 'uma', 'dos', 'das', 'pela', 'pelo',
            'são', 'foi', 'ser', 'está', 'como', 'mais', 'aos', 'pelo', 'sua'
        }

        for text in texts:
            # Normalizar e tokenizar
            words = re.findall(r'\b[A-ZÀ-Ú][A-ZÀ-Ú]+\b|\b\w{4,}\b', text.lower())

            for word in words:
                if word not in stopwords and len(word) > 3:
                    word_counter[word] += 1

        # Retornar top N
        return [word for word, _ in word_counter.most_common(top_n)]

    def _extract_markers(self, sections: list[ExtractedSection]) -> list[str]:
        """
        Extrai marcadores estruturais comuns.

        Args:
            sections: Lista de seções

        Returns:
            Lista de marcadores encontrados
        """
        markers = []

        # Procurar por padrões comuns
        all_text = '\n'.join(s.content for s in sections)

        # Marcadores jurídicos comuns
        common_patterns = [
            r'EXCELENTÍSSIMO',
            r'Vistos.*relatados.*discutidos',
            r'Nestes termos.*pede deferimento',
            r'PROCURAÇÃO',
            r'OUTORGANTE:',
            r'I\s*-\s*DOS FATOS',
            r'DISPOSITIVO',
            r'SENTENÇA'
        ]

        for pattern in common_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                markers.append(pattern)

        return markers[:10]  # Limitar a 10 marcadores

    def _calculate_pattern_confidence(
        self,
        sections: list[ExtractedSection],
        start_keywords: list[str],
        end_keywords: list[str]
    ) -> float:
        """
        Calcula confiança no padrão baseado em consistência.

        Args:
            sections: Seções analisadas
            start_keywords: Keywords de início identificadas
            end_keywords: Keywords de fim identificadas

        Returns:
            Score de confiança (0.0-1.0)
        """
        if not sections:
            return 0.0

        # Componentes de confiança:
        # 1. Número de amostras (mais amostras = mais confiança)
        sample_score = min(1.0, len(sections) / 10.0)  # Max em 10 amostras

        # 2. Consistência de confidence scores
        avg_confidence = sum(s.confidence for s in sections) / len(sections)

        # 3. Presença de keywords
        keyword_score = (len(start_keywords) + len(end_keywords)) / 10.0  # Max 10 keywords

        # Média ponderada
        confidence = (
            0.4 * sample_score +
            0.4 * avg_confidence +
            0.2 * min(1.0, keyword_score)
        )

        return round(confidence, 2)
