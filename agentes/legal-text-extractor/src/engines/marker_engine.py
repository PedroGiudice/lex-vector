"""
Marker Engine - High-quality PDF extraction with layout preservation.

Marker is a powerful engine for PDF conversion that:
- Preserves document layout and structure
- Handles complex PDFs (multi-column, tables, images)
- Outputs markdown with formatting

REQUIREMENTS:
- High RAM: ~10GB minimum (WSL2 or native)
- GPU: Optional but recommended for speed
- Dependencies: marker-pdf package
"""

import logging
from pathlib import Path

try:
    import marker
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False

from .base import ExtractionEngine, ExtractionResult


logger = logging.getLogger(__name__)


class MarkerEngine(ExtractionEngine):
    """
    High-quality extraction engine using Marker.

    Características:
    - Pesado: ~10GB RAM mínimo
    - Lento mas preciso: Análise profunda de layout
    - Suporta: Tabelas, colunas, imagens, formatação complexa
    - Output: Markdown com estrutura preservada

    Requisitos:
    1. Instalar marker-pdf: pip install marker-pdf
    2. Sistema com >= 10GB RAM disponível
    3. (Opcional) GPU para aceleração

    Example:
        >>> engine = MarkerEngine()
        >>> if engine.is_available():
        ...     result = engine.extract(Path("complex_document.pdf"))
        ...     print(result.metadata['markdown'])
    """

    name = "marker"
    min_ram_gb = 10.0
    dependencies = ["marker"]

    def __init__(self, use_gpu: bool = False):
        """
        Inicializa Marker engine.

        Args:
            use_gpu: Usar GPU se disponível (padrão: False)
        """
        self.use_gpu = use_gpu

    def is_available(self) -> bool:
        """
        Verifica se Marker está disponível.

        Returns:
            True se marker-pdf está instalado E RAM >= 10GB
        """
        if not MARKER_AVAILABLE:
            return False

        # Check RAM requirement
        ok, reason = self.check_resources()
        return ok

    def extract(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrai texto de PDF usando Marker.

        Args:
            pdf_path: Caminho para arquivo PDF

        Returns:
            ExtractionResult com texto extraído e metadados
        """
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict

        logger.info(f"Marker: Carregando modelos...")
        models = create_model_dict()

        logger.info(f"Marker: Convertendo {pdf_path.name}...")
        converter = PdfConverter(artifact_dict=models)
        rendered = converter(str(pdf_path))

        full_text = rendered.markdown
        pages = len(rendered.pages) if hasattr(rendered, 'pages') else 0

        logger.info(f"Marker: Extração concluída - {len(full_text)} chars, {pages} páginas")

        return ExtractionResult(
            text=full_text,
            pages=pages,
            engine_used=self.name,
            confidence=0.95,
            metadata={
                "markdown": full_text,
            },
        )
