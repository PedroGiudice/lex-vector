"""
Marker Engine - High-quality PDF extraction with layout preservation.

Marker is the PRIMARY and ONLY extraction engine for this system.
It handles both native PDFs and scanned documents automatically.

Key capabilities (from research):
- Text-first: Extracts native PDF text via pdftext, only uses OCR when needed
- Layout detection: Surya models detect structure (columns, tables, headers)
- Automatic OCR: Falls back to Surya OCR when page quality is poor

Configuration optimizations applied:
- disable_image_extraction: Reduces output from 80MB to ~1MB (no base64 bloat)
- paginate_output: Preserves page references for citation
- drop_repeated_text: Removes repeated headers/footers

REQUIREMENTS:
- High RAM: ~10GB minimum (WSL2 or native)
- GPU: Optional but recommended for speed
- Dependencies: marker-pdf package
"""

import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

try:
    import marker
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False

from .base import ExtractionEngine, ExtractionResult


logger = logging.getLogger(__name__)


@dataclass
class MarkerConfig:
    """Configuration for Marker extraction."""

    # Output format
    output_format: str = "markdown"
    paginate_output: bool = True

    # Image handling - CRITICAL for file size
    disable_image_extraction: bool = True

    # Text cleaning
    disable_links: bool = True
    drop_repeated_text: bool = True

    # Headers/footers - REMOVE BOTH (pure noise in legal docs)
    # Headers: logos, "Poder Judiciário", repeated case numbers
    # Footers: page numbers, system timestamps, signatures
    keep_pageheader_in_output: bool = False
    keep_pagefooter_in_output: bool = False

    # OCR control (let Marker decide automatically)
    force_ocr: bool = False
    strip_existing_ocr: bool = False

    # LLM enhancement (disabled by default - Step 04 handles this)
    use_llm: bool = False


class MarkerEngine(ExtractionEngine):
    """
    Primary extraction engine using Marker.

    Características:
    - Pesado: ~10GB RAM mínimo
    - Inteligente: Detecta automaticamente se página precisa OCR
    - Preciso: Preserva layout, tabelas, estrutura
    - Output: Markdown limpo com paginação

    Requisitos:
    1. Instalar marker-pdf: pip install marker-pdf
    2. Sistema com >= 10GB RAM disponível
    3. (Opcional) GPU para aceleração

    Example:
        >>> engine = MarkerEngine()
        >>> if engine.is_available():
        ...     result = engine.extract(Path("document.pdf"))
        ...     print(result.text)
    """

    name = "marker"
    min_ram_gb = 10.0
    dependencies = ["marker"]

    def __init__(
        self,
        config: Optional[MarkerConfig] = None,
        use_gpu: bool = False,
        low_memory_mode: bool = False,
    ):
        """
        Inicializa Marker engine.

        Args:
            config: Configuração customizada (usa defaults otimizados se None)
            use_gpu: Usar GPU se disponível (padrão: False)
            low_memory_mode: Ignorar verificação de RAM (use com cautela)
        """
        self.config = config or MarkerConfig()
        self.use_gpu = use_gpu
        self._models = None
        self._converter = None

        # Low memory mode bypasses RAM check
        if low_memory_mode:
            self._skip_ram_check = True
            logger.warning(
                "⚠️  LOW MEMORY MODE: RAM check bypassed. "
                "System may become slow or unresponsive for large PDFs."
            )

    def is_available(self) -> bool:
        """
        Verifica se Marker está disponível.

        Returns:
            True se marker-pdf está instalado E RAM >= 10GB
        """
        if not MARKER_AVAILABLE:
            logger.warning("marker-pdf não está instalado. Instale com: pip install marker-pdf")
            return False

        # Check RAM requirement
        ok, reason = self.check_resources()
        if not ok:
            logger.warning(f"Marker indisponível: {reason}")
        return ok

    def _init_converter(self):
        """Inicializa converter com configuração otimizada (lazy loading)."""
        if self._converter is not None:
            return

        logger.info("Marker: Carregando modelos (primeira execução é mais lenta)...")

        # Build config dict from MarkerConfig
        config_dict = {
            "output_format": self.config.output_format,
            "paginate_output": self.config.paginate_output,
            "disable_image_extraction": self.config.disable_image_extraction,
            "disable_links": self.config.disable_links,
            "drop_repeated_text": self.config.drop_repeated_text,
            "keep_pageheader_in_output": self.config.keep_pageheader_in_output,
            "keep_pagefooter_in_output": self.config.keep_pagefooter_in_output,
        }

        if self.config.force_ocr:
            config_dict["force_ocr"] = True

        if self.config.strip_existing_ocr:
            config_dict["strip_existing_ocr"] = True

        if self.config.use_llm:
            config_dict["use_llm"] = True

        # Create config parser and models
        config_parser = ConfigParser(config_dict)
        self._models = create_model_dict()

        # Create converter with optimized config
        self._converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=self._models,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
        )

        logger.info("Marker: Modelos carregados com sucesso")

    def extract(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrai texto de PDF usando Marker.

        Args:
            pdf_path: Caminho para arquivo PDF

        Returns:
            ExtractionResult com texto extraído e metadados

        Raises:
            RuntimeError: Se Marker não estiver disponível
        """
        if not self.is_available():
            raise RuntimeError("Marker não está disponível. Verifique instalação e RAM.")

        # Initialize converter (lazy loading)
        self._init_converter()

        logger.info(f"Marker: Processando {pdf_path.name}...")

        # Convert PDF
        rendered = self._converter(str(pdf_path))

        # Extract text and metadata
        full_text = rendered.markdown

        # Get page stats for debugging/monitoring
        page_stats = []
        if hasattr(rendered, 'metadata') and rendered.metadata:
            page_stats = rendered.metadata.get('page_stats', [])

        # Count pages and extraction methods
        pages = len(page_stats) if page_stats else 0
        native_pages = sum(1 for p in page_stats if p.get('text_extraction_method') == 'pdftext')
        ocr_pages = sum(1 for p in page_stats if p.get('text_extraction_method') == 'surya')

        logger.info(f"Marker: Extração concluída")
        logger.info(f"  - Total: {len(full_text):,} caracteres, {pages} páginas")
        logger.info(f"  - Método: {native_pages} páginas nativas, {ocr_pages} páginas OCR")

        return ExtractionResult(
            text=full_text,
            pages=pages,
            engine_used=self.name,
            confidence=0.95,
            metadata={
                "markdown": full_text,
                "page_stats": page_stats,
                "native_pages": native_pages,
                "ocr_pages": ocr_pages,
                "config": {
                    "disable_image_extraction": self.config.disable_image_extraction,
                    "paginate_output": self.config.paginate_output,
                    "drop_repeated_text": self.config.drop_repeated_text,
                }
            },
        )

    def extract_with_options(
        self,
        pdf_path: Path,
        force_ocr: bool = False,
        keep_images: bool = False,
        use_llm: bool = False,
    ) -> ExtractionResult:
        """
        Extrai PDF com opções customizadas (para casos especiais).

        Args:
            pdf_path: Caminho do PDF
            force_ocr: Forçar OCR em todas as páginas
            keep_images: Manter imagens (aumenta muito o tamanho)
            use_llm: Usar LLM para melhorar tabelas/formulários

        Returns:
            ExtractionResult
        """
        # Create temporary config with overrides
        custom_config = MarkerConfig(
            output_format=self.config.output_format,
            paginate_output=self.config.paginate_output,
            disable_image_extraction=not keep_images,
            disable_links=self.config.disable_links,
            drop_repeated_text=self.config.drop_repeated_text,
            keep_pageheader_in_output=self.config.keep_pageheader_in_output,
            keep_pagefooter_in_output=self.config.keep_pagefooter_in_output,
            force_ocr=force_ocr,
            use_llm=use_llm,
        )

        # Create new engine with custom config
        custom_engine = MarkerEngine(config=custom_config, use_gpu=self.use_gpu)
        return custom_engine.extract(pdf_path)
