"""
PDFPlumber Engine - Extração de texto nativo de PDFs.

Engine leve e rápida para PDFs com texto extraível (não escaneados).
Usa pdfplumber para extração direta de caracteres nativos.
"""

import logging
from pathlib import Path

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from .base import ExtractionEngine, ExtractionResult

logger = logging.getLogger(__name__)


class PDFPlumberEngine(ExtractionEngine):
    """
    Engine de extração usando pdfplumber.

    Características:
    - Leve: ~0.5GB RAM
    - Rápida: Extração direta sem OCR
    - Limitações: Apenas PDFs com texto nativo (não escaneados)

    Sempre disponível se pdfplumber estiver instalado.

    Example:
        >>> engine = PDFPlumberEngine()
        >>> if engine.is_available():
        ...     result = engine.extract(Path("document.pdf"))
        ...     print(f"Extracted {len(result.text)} chars")
    """

    name = "pdfplumber"
    min_ram_gb = 0.5
    dependencies = ["pdfplumber"]

    def is_available(self) -> bool:
        """
        Verifica se pdfplumber está disponível.

        Returns:
            True se pdfplumber está instalado
        """
        return PDFPLUMBER_AVAILABLE

    def extract(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrai texto nativo de PDF usando pdfplumber.

        Args:
            pdf_path: Caminho para arquivo PDF

        Returns:
            ExtractionResult com texto extraído

        Raises:
            FileNotFoundError: Se PDF não existir
            RuntimeError: Se pdfplumber não estiver disponível ou houver erro
        """
        if not self.is_available():
            raise RuntimeError(
                "pdfplumber não está disponível. "
                "Instale com: pip install pdfplumber"
            )

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        try:
            logger.info(f"Extraindo texto via pdfplumber: {pdf_path.name}")

            with pdfplumber.open(pdf_path) as pdf:
                pages = len(pdf.pages)
                text_parts = []
                total_chars = 0

                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()

                    if page_text:
                        text_parts.append(page_text)
                        total_chars += len(page_text)
                    else:
                        logger.warning(
                            f"Página {page_num} retornou texto vazio "
                            "(pode ser escaneada)"
                        )

                # Junta todas as páginas com separador
                full_text = "\n\n".join(text_parts)

                # Calcula confiança baseada na densidade de caracteres
                avg_chars_per_page = total_chars / pages if pages > 0 else 0
                confidence = min(1.0, avg_chars_per_page / 2000)  # ~2000 chars/page = 100%

                logger.info(
                    f"Extração concluída: {pages} páginas, "
                    f"{total_chars} caracteres, "
                    f"confiança={confidence:.2f}"
                )

                return ExtractionResult(
                    text=full_text,
                    pages=pages,
                    engine_used=self.name,
                    confidence=confidence,
                    metadata={
                        "total_chars": total_chars,
                        "avg_chars_per_page": avg_chars_per_page,
                        "empty_pages": pages - len(text_parts),
                    },
                )

        except Exception as e:
            logger.error(f"Erro ao extrair PDF via pdfplumber: {e}")
            raise RuntimeError(f"Falha na extração com pdfplumber: {e}") from e
