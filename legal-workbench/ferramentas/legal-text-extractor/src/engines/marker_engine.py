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

Performance Monitoring (2026-01-17):
- Sentry v8 spans track each phase (model loading, conversion, cleanup)
- Memory tracking helps diagnose OOM issues
- The "10% hang" typically occurs during create_model_dict() - model loading

REQUIREMENTS:
- High RAM: ~10GB minimum (WSL2 or native)
- GPU: Optional but recommended for speed
- Dependencies: marker-pdf package
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path

try:
    import marker
    from marker.config.parser import ConfigParser
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict

    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False

from .base import ExtractionEngine, ExtractionResult

# Import monitoring (graceful fallback if not available)
try:
    from ..monitoring import start_span, track_memory, track_progress

    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

    # Fallback implementations
    from contextlib import contextmanager

    @contextmanager
    def start_span(op, description=None, **data):
        yield type("MockSpan", (), {"set_data": lambda s, k, v: None})()

    def track_memory(context=""):
        pass

    def track_progress(current, total, operation=""):
        pass


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
        config: MarkerConfig | None = None,
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
        """
        Inicializa converter com configuracao otimizada (lazy loading).

        NOTA: Este metodo e onde ocorre o "travamento em 10%".
        O create_model_dict() carrega modelos pesados (Surya, Texify).
        Spans detalhados ajudam a identificar exatamente onde trava.
        """
        if self._converter is not None:
            return

        init_start = time.time()
        logger.info("=" * 60)
        logger.info("Marker: INICIANDO CARREGAMENTO DE MODELOS")
        logger.info("  (Primeira execucao pode demorar varios minutos)")
        logger.info("=" * 60)

        track_memory("marker.init_start")

        # Build config dict from MarkerConfig
        with start_span("marker.build_config", "Building configuration dict") as span:
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

            span.set_data("config_keys", list(config_dict.keys()))
            logger.info(f"  Config: {len(config_dict)} opcoes definidas")

        # Create config parser
        with start_span("marker.config_parser", "Creating ConfigParser") as span:
            logger.info("[1/4] Criando ConfigParser...")
            config_parser = ConfigParser(config_dict)
            span.set_data("status", "success")
            logger.info("  ConfigParser criado")

        track_memory("marker.after_config_parser")

        # CRITICAL: This is where the "10% hang" typically occurs
        # Models are downloaded/loaded from disk here
        with start_span(
            "marker.create_model_dict", "Loading ML models (Surya, Texify) - THIS IS THE SLOW PART"
        ) as span:
            logger.info("[2/4] Carregando modelos ML (Surya, Texify)...")
            logger.info("  ATENCAO: Este passo pode demorar 1-5 minutos na primeira vez")
            logger.info("  (Modelos sao baixados/carregados do disco)")

            model_start = time.time()
            self._models = create_model_dict()
            model_time = time.time() - model_start

            span.set_data("model_count", len(self._models) if self._models else 0)
            span.set_data("load_time_seconds", round(model_time, 2))

            if self._models:
                model_names = list(self._models.keys())
                logger.info(f"  Modelos carregados ({model_time:.1f}s): {model_names}")
                span.set_data("model_names", model_names)
            else:
                logger.warning("  AVISO: Nenhum modelo carregado!")

        track_memory("marker.after_model_load")

        # Get processors
        with start_span("marker.get_processors", "Getting processor list") as span:
            logger.info("[3/4] Obtendo lista de processadores...")
            processor_list = config_parser.get_processors()
            renderer = config_parser.get_renderer()
            span.set_data("processor_count", len(processor_list) if processor_list else 0)
            logger.info(f"  Processadores: {len(processor_list) if processor_list else 0}")

        # Create converter
        with start_span("marker.create_converter", "Creating PdfConverter") as span:
            logger.info("[4/4] Criando PdfConverter...")
            self._converter = PdfConverter(
                config=config_parser.generate_config_dict(),
                artifact_dict=self._models,
                processor_list=processor_list,
                renderer=renderer,
            )
            span.set_data("status", "success")

        track_memory("marker.init_complete")

        total_time = time.time() - init_start
        logger.info("=" * 60)
        logger.info(f"Marker: MODELOS CARREGADOS COM SUCESSO ({total_time:.1f}s)")
        logger.info("=" * 60)

    def extract(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrai texto de PDF usando Marker.

        Args:
            pdf_path: Caminho para arquivo PDF

        Returns:
            ExtractionResult com texto extraido e metadados

        Raises:
            RuntimeError: Se Marker nao estiver disponivel
        """
        extract_start = time.time()

        with start_span(
            "marker.extract", f"Extract PDF: {pdf_path.name}", pdf_name=pdf_path.name
        ) as extract_span:
            # Check availability
            with start_span("marker.check_available", "Checking Marker availability"):
                if not self.is_available():
                    raise RuntimeError("Marker nao esta disponivel. Verifique instalacao e RAM.")

            track_memory("marker.extract_start")

            # Initialize converter (lazy loading) - this is where 10% hang occurs
            with start_span("marker.init", "Initialize converter (model loading)"):
                self._init_converter()

            # Get file info for context
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            logger.info(f"Marker: Processando {pdf_path.name} ({file_size_mb:.2f} MB)...")
            extract_span.set_data("file_size_mb", round(file_size_mb, 2))

            track_memory("marker.before_convert")

            # Convert PDF - the main processing
            with start_span(
                "marker.convert",
                "PDF conversion (layout + text extraction)",
                file_size_mb=round(file_size_mb, 2),
            ) as convert_span:
                logger.info("  Convertendo PDF (layout detection + text extraction)...")
                convert_start = time.time()

                rendered = self._converter(str(pdf_path))

                convert_time = time.time() - convert_start
                convert_span.set_data("convert_time_seconds", round(convert_time, 2))
                logger.info(f"  Conversao concluida em {convert_time:.1f}s")

            track_memory("marker.after_convert")

            # Extract text and metadata
            with start_span("marker.extract_metadata", "Extracting text and metadata") as meta_span:
                full_text = rendered.markdown

                # Get page stats for debugging/monitoring
                page_stats = []
                if hasattr(rendered, "metadata") and rendered.metadata:
                    page_stats = rendered.metadata.get("page_stats", [])

                # Count pages and extraction methods
                pages = len(page_stats) if page_stats else 0
                native_pages = sum(
                    1 for p in page_stats if p.get("text_extraction_method") == "pdftext"
                )
                ocr_pages = sum(1 for p in page_stats if p.get("text_extraction_method") == "surya")

                meta_span.set_data("page_count", pages)
                meta_span.set_data("native_pages", native_pages)
                meta_span.set_data("ocr_pages", ocr_pages)
                meta_span.set_data("text_length", len(full_text))

            total_time = time.time() - extract_start
            extract_span.set_data("total_time_seconds", round(total_time, 2))

            logger.info("=" * 50)
            logger.info(f"Marker: EXTRACAO CONCLUIDA ({total_time:.1f}s)")
            logger.info(f"  - Arquivo: {pdf_path.name} ({file_size_mb:.2f} MB)")
            logger.info(f"  - Texto: {len(full_text):,} caracteres")
            logger.info(f"  - Paginas: {pages} total ({native_pages} nativas, {ocr_pages} OCR)")
            logger.info(
                f"  - Velocidade: {pages / total_time:.1f} pags/s" if total_time > 0 else ""
            )
            logger.info("=" * 50)

            track_memory("marker.extract_complete")

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
                    "extraction_time_seconds": round(total_time, 2),
                    "file_size_mb": round(file_size_mb, 2),
                    "config": {
                        "disable_image_extraction": self.config.disable_image_extraction,
                        "paginate_output": self.config.paginate_output,
                        "drop_repeated_text": self.config.drop_repeated_text,
                    },
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
