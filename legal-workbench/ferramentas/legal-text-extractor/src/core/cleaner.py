"""
Orquestrador principal de limpeza de documentos jurídicos.

Integra detector de sistemas, padrões de limpeza e normalização
para processar documentos jurídicos brasileiros.
"""

import re
from dataclasses import dataclass

from .detector import JudicialSystemDetector
from .normalizer import TextNormalizer
from .patterns import CleaningPattern, SystemPatterns


@dataclass
class CleaningStats:
    """Estatísticas de limpeza"""

    system: str
    system_name: str
    confidence: int
    original_length: int
    final_length: int
    reduction_pct: float
    patterns_removed: list[str]


@dataclass
class CleaningResult:
    """Resultado completo da limpeza"""

    text: str
    stats: CleaningStats


class DocumentCleaner:
    """
    Limpa documentos jurídicos removendo assinaturas e certificações.

    Pipeline:
    1. Detecta sistema judicial (auto ou manual)
    2. Aplica padrões específicos do sistema
    3. Aplica padrões universais
    4. Aplica blacklist customizada
    5. Normaliza texto final

    Example:
        >>> cleaner = DocumentCleaner()
        >>> result = cleaner.clean(pdf_text, system="auto")
        >>> print(f"Redução: {result.stats.reduction_pct:.1f}%")
        >>> print(result.text)
    """

    def __init__(self):
        """Inicializa cleaner com detector e normalizer"""
        self.detector = JudicialSystemDetector()
        self.normalizer = TextNormalizer()

    def clean(
        self,
        text: str,
        system: str | None = None,
        custom_blacklist: list[str] | None = None,
        aggressive: bool = False,
    ) -> CleaningResult:
        """
        Limpa texto do documento.

        Args:
            text: Texto original extraído do PDF
            system: Sistema judicial ('auto', 'PJE', 'ESAJ', etc.) ou None para auto-detect
            custom_blacklist: Lista de termos customizados a remover
            aggressive: Modo agressivo (não implementado ainda - reservado para futuro)

        Returns:
            CleaningResult com texto limpo e estatísticas

        Raises:
            ValueError: Se texto vazio ou sistema inválido

        Example:
            >>> cleaner = DocumentCleaner()
            >>> result = cleaner.clean(
            ...     text="Documento PJE com assinatura...",
            ...     system="auto",
            ...     custom_blacklist=["CONFIDENCIAL"]
            ... )
        """
        if not text:
            raise ValueError("Texto não pode ser vazio")

        if len(text) < 10:
            raise ValueError("Texto muito curto (mínimo 10 caracteres)")

        original_length = len(text)
        cleaned = text
        removed_patterns: list[str] = []

        # 1. Detecta sistema se necessário
        if system is None or system.lower() == "auto":
            detection = self.detector.detect_system(text)
            system_code = detection.system
            system_name = detection.name
            confidence = detection.confidence
        else:
            # Sistema especificado manualmente
            system_code = system.upper()
            system_info = self.detector.get_system_info(system_code)

            if system_info:
                system_name = system_info.name
                confidence = 100  # Manual = 100% confiança
            else:
                # Sistema inválido, usa genérico
                system_code = "GENERIC_JUDICIAL"
                system_name = "Sistema Judicial Genérico"
                confidence = 50

        # 2. Obtém padrões para o sistema detectado
        patterns = SystemPatterns.get_patterns(system_code)

        # 3. Aplica cada padrão
        for pattern in patterns:
            before = cleaned
            cleaned = pattern.regex.sub(pattern.replacement, cleaned)

            if before != cleaned:
                removed_patterns.append(pattern.description)

        # 4. Aplica blacklist customizada
        if custom_blacklist:
            for term in custom_blacklist:
                if not term or not term.strip():
                    continue

                try:
                    # Escapa caracteres especiais regex (trata como string literal)
                    escaped = re.escape(term)
                    regex = re.compile(escaped, re.IGNORECASE)

                    before = cleaned
                    cleaned = regex.sub('', cleaned)

                    if before != cleaned:
                        removed_patterns.append(f'Blacklist: "{term}"')

                except Exception as e:
                    # Ignora erros em termos da blacklist
                    pass

        # 5. Normaliza texto final
        cleaned = self.normalizer.normalize(cleaned)

        # 6. Calcula estatísticas
        final_length = len(cleaned)
        reduction_pct = ((original_length - final_length) / original_length) * 100

        stats = CleaningStats(
            system=system_code,
            system_name=system_name,
            confidence=confidence,
            original_length=original_length,
            final_length=final_length,
            reduction_pct=round(reduction_pct, 2),
            patterns_removed=removed_patterns,
        )

        return CleaningResult(text=cleaned, stats=stats)

    def clean_batch(
        self,
        texts: list[str],
        system: str | None = None,
        custom_blacklist: list[str] | None = None,
    ) -> list[CleaningResult]:
        """
        Limpa múltiplos textos com as mesmas configurações.

        Args:
            texts: Lista de textos a limpar
            system: Sistema judicial (aplicado a todos)
            custom_blacklist: Blacklist (aplicada a todos)

        Returns:
            Lista de CleaningResult
        """
        results = []
        for text in texts:
            try:
                result = self.clean(text, system=system, custom_blacklist=custom_blacklist)
                results.append(result)
            except ValueError as e:
                # Cria resultado vazio para textos inválidos
                results.append(
                    CleaningResult(
                        text="",
                        stats=CleaningStats(
                            system="ERROR",
                            system_name=str(e),
                            confidence=0,
                            original_length=len(text) if text else 0,
                            final_length=0,
                            reduction_pct=0.0,
                            patterns_removed=[],
                        ),
                    )
                )
        return results

    def get_supported_systems(self) -> list[dict]:
        """
        Lista todos os sistemas suportados.

        Returns:
            Lista de dicts com informações dos sistemas
        """
        return self.detector.list_supported_systems()

    def detect_only(self, text: str) -> dict:
        """
        Apenas detecta o sistema sem limpar.

        Args:
            text: Texto do documento

        Returns:
            Dict com system, name, confidence e details

        Example:
            >>> cleaner = DocumentCleaner()
            >>> info = cleaner.detect_only("Documento PJE...")
            >>> info['system']
            'PJE'
        """
        detection = self.detector.detect_system(text)
        return {
            "system": detection.system,
            "name": detection.name,
            "confidence": detection.confidence,
            "details": detection.details,
        }
