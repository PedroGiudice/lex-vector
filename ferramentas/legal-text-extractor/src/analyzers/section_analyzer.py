"""Análise de seções usando Claude SDK com rate limiting e retry logic"""
import os
import re
import json
import time
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from anthropic import Anthropic, RateLimitError, APIError
from pydantic import ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from .schemas import ClaudeAnalysisResponse, SectionMetadata
from ..learning.prompt_versioner import PromptVersioner
from ..learning.ab_tester import ABTester
from ..learning.storage import LearningStorage
from ..learning.schemas import ExtractionResult, ExtractedSection, SectionType

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Section:
    """Seção identificada em documento jurídico"""
    type: str  # "petição inicial", "contestação", "sentença", etc
    content: str
    start_pos: int
    end_pos: int
    confidence: float  # 0-1


class SectionAnalyzer:
    """
    Analisa e separa seções de documentos jurídicos usando Claude SDK.

    Features:
    - Rate limiting automático (20 req/min)
    - Retry logic com exponential backoff
    - Error handling robusto
    - JSON parsing com validação Pydantic
    - Template-based prompts
    """

    # API limits
    MAX_TOKENS_INPUT = 100000  # Claude Sonnet 4 limit
    MAX_TOKENS_OUTPUT = 4096
    RATE_LIMIT_RPM = 20  # requests per minute

    # Paths
    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
    SECTION_SEPARATOR_TEMPLATE = PROMPTS_DIR / "section_separator.txt"

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        model: str = "claude-sonnet-4-20250514",
        enable_learning: bool = True,
        enable_ab_testing: bool = False,
        ab_test_id: Optional[str] = None
    ):
        """
        Inicializa o analisador de seções.

        Args:
            api_key: Chave API do Anthropic (usa ANTHROPIC_API_KEY se None)
            max_retries: Número máximo de tentativas em caso de erro
            retry_delay: Delay base entre retries (em segundos)
            model: Modelo Claude a ser usado
            enable_learning: Se True, salva resultados para learning system
            enable_ab_testing: Se True, participa de teste A/B
            ab_test_id: ID do teste A/B (se enable_ab_testing=True)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY não encontrada. "
                "Configure via env ou passe como parâmetro."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.model = model

        # Rate limiting state
        self._last_request_time: Optional[float] = None
        self._min_request_interval = 60.0 / self.RATE_LIMIT_RPM  # 3 seconds

        # Learning system integration
        self.enable_learning = enable_learning
        self.enable_ab_testing = enable_ab_testing
        self.ab_test_id = ab_test_id

        if enable_learning:
            self.versioner = PromptVersioner()
            self.storage = LearningStorage()
            logger.info("Learning system enabled")

        if enable_ab_testing:
            if not ab_test_id:
                raise ValueError("ab_test_id required when enable_ab_testing=True")
            self.ab_tester = ABTester()
            logger.info(f"A/B testing enabled: test_id={ab_test_id}")

        # Load prompt template on initialization
        self._prompt_template = self._load_prompt_template()

        logger.info(
            f"SectionAnalyzer initialized: model={model}, "
            f"max_retries={max_retries}, rate_limit={self.RATE_LIMIT_RPM} rpm, "
            f"learning={enable_learning}, ab_testing={enable_ab_testing}"
        )

    def _load_prompt_template(self) -> str:
        """
        Carrega template de prompt do arquivo ou versioner.

        Returns:
            Template string com placeholder {text}

        Raises:
            FileNotFoundError: Se template não encontrado
        """
        # Se learning system habilitado, tentar carregar de versioner
        if self.enable_learning:
            try:
                prompt_version = self._get_prompt_version()
                if prompt_version:
                    logger.info(
                        f"Using versioned prompt: {prompt_version.version_id} "
                        f"(status={prompt_version.status})"
                    )
                    return prompt_version.content
            except Exception as e:
                logger.warning(f"Failed to load versioned prompt: {e}, falling back to file")

        # Fallback: carregar de arquivo
        if not self.SECTION_SEPARATOR_TEMPLATE.exists():
            raise FileNotFoundError(
                f"Prompt template não encontrado: {self.SECTION_SEPARATOR_TEMPLATE}"
            )

        template = self.SECTION_SEPARATOR_TEMPLATE.read_text(encoding='utf-8')
        logger.debug(f"Prompt template carregado de arquivo: {len(template)} chars")
        return template

    def _get_prompt_version(self) -> Optional:
        """
        Obtém versão do prompt a usar (considerando A/B testing).

        Returns:
            PromptVersion ou None
        """
        if not self.enable_learning:
            return None

        # Se A/B testing habilitado e há documento atual, usar versão do teste
        if self.enable_ab_testing and self.ab_test_id:
            # Nota: document_id deve ser definido antes de chamar analyze()
            if hasattr(self, '_current_document_id') and self._current_document_id:
                version_id = self.ab_tester.get_version_for_document(
                    self.ab_test_id,
                    self._current_document_id
                )
                if version_id:
                    return self.versioner.load_version(version_id)

        # Fallback: versão ativa
        return self.versioner.get_active_version()

    def _rate_limit(self) -> None:
        """
        Implementa rate limiting básico.
        Aguarda tempo mínimo entre requests para não ultrapassar limite.
        """
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_request_interval:
                sleep_time = self._min_request_interval - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self._last_request_time = time.time()

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _call_claude_with_retry(self, prompt: str) -> str:
        """
        Chama Claude API com retry logic automático.

        Args:
            prompt: Prompt completo para enviar ao Claude

        Returns:
            Resposta em texto do Claude

        Raises:
            RateLimitError: Se limite de rate excedido após retries
            APIError: Se erro de API persistir após retries
        """
        self._rate_limit()

        logger.debug(f"Calling Claude API: prompt_length={len(prompt)} chars")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.MAX_TOKENS_OUTPUT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # Deterministic for consistency
            )

            response_text = message.content[0].text
            logger.debug(f"Claude API response: length={len(response_text)} chars")

            return response_text

        except RateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            raise
        except APIError as e:
            logger.error(f"API error: {e}")
            raise

    def _parse_claude_response(self, response: str) -> ClaudeAnalysisResponse:
        """
        Parse e valida resposta JSON do Claude usando Pydantic.

        Args:
            response: Texto de resposta do Claude (esperado JSON)

        Returns:
            ClaudeAnalysisResponse validado

        Raises:
            ValueError: Se JSON inválido ou validação falhar
        """
        # Extrair JSON da resposta (Claude pode adicionar texto ao redor)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError(f"Nenhum JSON encontrado na resposta do Claude: {response[:200]}...")

        json_str = json_match.group(0)

        try:
            data = json.loads(json_str)
            validated = ClaudeAnalysisResponse(**data)
            logger.debug(f"JSON parsed successfully: {len(validated.sections)} sections")
            return validated

        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {e}") from e
        except ValidationError as e:
            raise ValueError(f"Validação Pydantic falhou: {e}") from e

    def _find_text_position(self, full_text: str, marker: str, from_start: bool = True) -> int:
        """
        Encontra posição de um marker no texto.

        Args:
            full_text: Texto completo do documento
            marker: Marker a ser encontrado (pode estar truncado)
            from_start: Se True, busca do início; se False, busca do fim

        Returns:
            Posição do marker no texto (-1 se não encontrado)
        """
        # Normalizar: remover espaços extras, quebras de linha múltiplas
        marker_clean = re.sub(r'\s+', ' ', marker.strip())
        text_clean = re.sub(r'\s+', ' ', full_text)

        # Tentar match exato primeiro
        pos = text_clean.find(marker_clean)
        if pos != -1:
            return pos

        # Se não encontrar, tentar match fuzzy (primeiras palavras)
        words = marker_clean.split()[:5]  # Usar primeiras 5 palavras
        partial_marker = ' '.join(words)

        pos = text_clean.find(partial_marker)
        if pos != -1:
            logger.debug(f"Marker found using partial match: {partial_marker[:50]}...")
            return pos

        logger.warning(f"Marker not found in text: {marker[:50]}...")
        return -1

    def _extract_section_text(
        self,
        full_text: str,
        section_meta: SectionMetadata
    ) -> tuple[str, int, int]:
        """
        Extrai texto de uma seção baseado nos markers.

        Args:
            full_text: Texto completo do documento
            section_meta: Metadados da seção (com start_marker e end_marker)

        Returns:
            Tupla (content, start_pos, end_pos)
        """
        start_pos = self._find_text_position(full_text, section_meta.start_marker, from_start=True)
        end_pos = self._find_text_position(full_text, section_meta.end_marker, from_start=False)

        # Fallback: se não encontrar markers, usar documento inteiro
        if start_pos == -1:
            start_pos = 0
            logger.warning("Start marker não encontrado, usando início do documento")

        if end_pos == -1:
            end_pos = len(full_text)
            logger.warning("End marker não encontrado, usando fim do documento")
        else:
            # Incluir o end_marker na seção
            end_pos += len(section_meta.end_marker)

        content = full_text[start_pos:end_pos]
        return content, start_pos, end_pos

    def analyze(
        self,
        text: str,
        document_id: Optional[str] = None
    ) -> list[Section]:
        """
        Analisa texto e identifica seções de peças processuais.

        Args:
            text: Texto limpo do documento (já processado por cleaner)
            document_id: ID único do documento (para learning/A/B testing)

        Returns:
            Lista de Section identificadas, ordenadas por posição

        Raises:
            ValueError: Se texto vazio ou parsing falhar
            APIError: Se erro persistente na API
        """
        if not text or not text.strip():
            raise ValueError("Texto vazio fornecido para análise")

        # Gerar document_id se não fornecido
        if document_id is None:
            import hashlib
            from datetime import datetime
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            document_id = f"doc_{timestamp}_{text_hash}"

        # Armazenar para uso em _get_prompt_version()
        self._current_document_id = document_id

        logger.info(f"Analyzing document {document_id}: {len(text)} chars")

        # 1. Obter versão do prompt (pode ser de A/B test)
        prompt_version_id = "v1"  # default
        if self.enable_learning:
            prompt_version = self._get_prompt_version()
            if prompt_version:
                prompt_version_id = prompt_version.version_id
                # Atualizar template se mudou
                self._prompt_template = prompt_version.content

        # 2. Construir prompt a partir do template
        prompt = self._prompt_template.format(text=text)

        # 3. Chamar Claude API
        response = self._call_claude_with_retry(prompt)

        # 4. Parse JSON response
        parsed = self._parse_claude_response(response)

        # 5. Converter metadados para Section objects
        sections: list[Section] = []

        for section_meta in parsed.sections:
            content, start_pos, end_pos = self._extract_section_text(text, section_meta)

            section = Section(
                type=section_meta.type,
                content=content,
                start_pos=start_pos,
                end_pos=end_pos,
                confidence=section_meta.confidence
            )
            sections.append(section)

        # 6. Ordenar por posição no documento
        sections.sort(key=lambda s: s.start_pos)

        # 7. Log extraction result para learning system
        if self.enable_learning:
            self._log_extraction_result(
                document_id=document_id,
                text=text,
                sections=sections,
                prompt_version=prompt_version_id
            )

        logger.info(f"Analysis complete: {len(sections)} sections identified")
        return sections

    def _log_extraction_result(
        self,
        document_id: str,
        text: str,
        sections: list[Section],
        prompt_version: str
    ) -> None:
        """
        Salva resultado da extração para learning system.

        Args:
            document_id: ID do documento
            text: Texto analisado
            sections: Seções extraídas
            prompt_version: Versão do prompt usada
        """
        try:
            # Converter Section para ExtractedSection
            extracted_sections = [
                ExtractedSection(
                    type=self._map_section_type(s.type),
                    content=s.content,
                    start_pos=s.start_pos,
                    end_pos=s.end_pos,
                    confidence=s.confidence
                )
                for s in sections
            ]

            # Criar ExtractionResult
            extraction_result = ExtractionResult(
                document_id=document_id,
                predicted_sections=extracted_sections,
                document_length=len(text),
                prompt_version=prompt_version,
                model=self.model
            )

            # Salvar
            self.storage.save_extraction_result(extraction_result)

            # Se A/B testing habilitado, registrar no teste
            if self.enable_ab_testing and self.ab_test_id:
                self.ab_tester.record_result(
                    test_id=self.ab_test_id,
                    document_id=document_id,
                    extraction_result=extraction_result
                )

            logger.debug(f"Extraction result logged: {document_id}")

        except Exception as e:
            logger.error(f"Failed to log extraction result: {e}")

    def _map_section_type(self, type_str: str) -> SectionType:
        """
        Mapeia string de tipo para SectionType enum.

        Args:
            type_str: String de tipo (ex: "petição inicial")

        Returns:
            SectionType correspondente
        """
        # Normalizar: remover acentos, lowercase, substituir espaços por _
        import unicodedata
        normalized = unicodedata.normalize('NFKD', type_str)
        normalized = normalized.encode('ASCII', 'ignore').decode('ASCII')
        normalized = normalized.lower().replace(' ', '_')

        # Tentar mapear para enum
        try:
            return SectionType(normalized)
        except ValueError:
            # Fallback: OUTRO
            logger.warning(f"Unknown section type '{type_str}', using OUTRO")
            return SectionType.OUTRO
