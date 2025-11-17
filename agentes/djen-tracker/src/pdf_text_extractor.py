"""
PDF Text Extractor com Multi-Strategy Fallback

Implementa extração robusta de texto de PDFs com múltiplas estratégias:
1. pdfplumber (melhor para publicações judiciais)
2. PyPDF2 (fallback geral)
3. OCR com pytesseract (fallback para PDFs escaneados)

Author: Claude Code (Development Agent)
Version: 1.0.0
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


logger = logging.getLogger(__name__)


class ExtractionStrategy(Enum):
    """Estratégias de extração disponíveis."""
    PDFPLUMBER = "pdfplumber"
    PYPDF2 = "pypdf2"
    OCR = "ocr"
    FAILED = "failed"


@dataclass
class ExtractionResult:
    """Resultado de extração de texto."""
    text: str
    strategy: ExtractionStrategy
    page_count: int
    char_count: int
    success: bool
    error_message: Optional[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PDFTextExtractor:
    """
    Extrator robusto de texto de PDFs com fallback inteligente.

    Tenta múltiplas estratégias em ordem de eficiência:
    1. pdfplumber - Melhor para PDFs nativos com formatação
    2. PyPDF2 - Fallback para PDFs simples
    3. OCR - Último recurso para PDFs escaneados (marcado para revisão manual)

    Attributes:
        enable_ocr: Se True, habilita OCR como última tentativa
        ocr_lang: Idioma para OCR (default: 'por' para português)
        max_file_size_mb: Tamanho máximo de arquivo para processar
    """

    def __init__(
        self,
        enable_ocr: bool = False,
        ocr_lang: str = 'por',
        max_file_size_mb: int = 100
    ):
        """
        Inicializa PDFTextExtractor.

        Args:
            enable_ocr: Habilita OCR como fallback
            ocr_lang: Idioma para OCR ('por', 'eng', etc)
            max_file_size_mb: Tamanho máximo de arquivo em MB
        """
        self.enable_ocr = enable_ocr
        self.ocr_lang = ocr_lang
        self.max_file_size_mb = max_file_size_mb

        # Verificar bibliotecas disponíveis
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Verifica e registra bibliotecas disponíveis."""
        self.has_pdfplumber = False
        self.has_pypdf2 = False
        self.has_ocr = False

        try:
            import pdfplumber
            self.has_pdfplumber = True
            logger.debug("pdfplumber disponível")
        except ImportError:
            logger.warning("pdfplumber não instalado (pip install pdfplumber)")

        try:
            from PyPDF2 import PdfReader
            self.has_pypdf2 = True
            logger.debug("PyPDF2 disponível")
        except ImportError:
            logger.warning("PyPDF2 não instalado (pip install PyPDF2)")

        if self.enable_ocr:
            try:
                from PIL import Image
                import pytesseract
                self.has_ocr = True
                logger.debug("OCR disponível (pytesseract)")
            except ImportError:
                logger.warning(
                    "OCR não disponível (pip install pytesseract pillow)"
                )

        if not (self.has_pdfplumber or self.has_pypdf2):
            raise RuntimeError(
                "Nenhuma biblioteca de PDF disponível. "
                "Instale pdfplumber ou PyPDF2."
            )

    def validate_pdf(self, pdf_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Valida PDF antes de processar.

        Args:
            pdf_path: Path para arquivo PDF

        Returns:
            (valid: bool, error_message: Optional[str])
        """
        if not pdf_path.exists():
            return False, f"Arquivo não encontrado: {pdf_path}"

        if not pdf_path.is_file():
            return False, f"Path não é um arquivo: {pdf_path}"

        if pdf_path.suffix.lower() != '.pdf':
            return False, f"Arquivo não é PDF: {pdf_path}"

        # Verificar tamanho
        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            return False, (
                f"Arquivo muito grande: {size_mb:.1f}MB "
                f"(máximo: {self.max_file_size_mb}MB)"
            )

        # Verificar se arquivo está corrompido (básico)
        try:
            with open(pdf_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    return False, "Arquivo corrompido (header inválido)"
        except Exception as e:
            return False, f"Erro ao ler arquivo: {e}"

        return True, None

    def extract(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrai texto de PDF usando fallback inteligente.

        Args:
            pdf_path: Path para arquivo PDF

        Returns:
            ExtractionResult com texto extraído e metadados
        """
        logger.info(f"Extraindo texto de: {pdf_path.name}")

        # Validar PDF
        valid, error = self.validate_pdf(pdf_path)
        if not valid:
            logger.error(f"PDF inválido: {error}")
            return ExtractionResult(
                text="",
                strategy=ExtractionStrategy.FAILED,
                page_count=0,
                char_count=0,
                success=False,
                error_message=error
            )

        # Tentar estratégias em ordem
        strategies = []
        if self.has_pdfplumber:
            strategies.append(self._extract_pdfplumber)
        if self.has_pypdf2:
            strategies.append(self._extract_pypdf2)
        if self.enable_ocr and self.has_ocr:
            strategies.append(self._extract_ocr)

        for strategy_func in strategies:
            try:
                result = strategy_func(pdf_path)
                if result.success and result.char_count > 50:
                    logger.info(
                        f"Extração bem-sucedida com {result.strategy.value}: "
                        f"{result.char_count} chars, {result.page_count} páginas"
                    )
                    return result
                else:
                    logger.warning(
                        f"{result.strategy.value} retornou pouco texto "
                        f"({result.char_count} chars)"
                    )
            except Exception as e:
                logger.error(f"Erro em {strategy_func.__name__}: {e}")
                continue

        # Todas estratégias falharam
        logger.error(f"Todas estratégias falharam para {pdf_path.name}")
        return ExtractionResult(
            text="",
            strategy=ExtractionStrategy.FAILED,
            page_count=0,
            char_count=0,
            success=False,
            error_message="Todas estratégias de extração falharam"
        )

    def _extract_pdfplumber(self, pdf_path: Path) -> ExtractionResult:
        """Extrai usando pdfplumber."""
        import pdfplumber

        logger.debug(f"Tentando pdfplumber em {pdf_path.name}")

        text_parts = []
        page_count = 0

        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)

            for i, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(f"Erro na página {i+1}: {e}")
                    continue

        full_text = '\n\n'.join(text_parts)
        char_count = len(full_text)

        return ExtractionResult(
            text=full_text,
            strategy=ExtractionStrategy.PDFPLUMBER,
            page_count=page_count,
            char_count=char_count,
            success=True,
            metadata={'pages_extracted': len(text_parts)}
        )

    def _extract_pypdf2(self, pdf_path: Path) -> ExtractionResult:
        """Extrai usando PyPDF2."""
        from PyPDF2 import PdfReader

        logger.debug(f"Tentando PyPDF2 em {pdf_path.name}")

        text_parts = []
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)

        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            except Exception as e:
                logger.warning(f"Erro na página {i+1}: {e}")
                continue

        full_text = '\n\n'.join(text_parts)
        char_count = len(full_text)

        return ExtractionResult(
            text=full_text,
            strategy=ExtractionStrategy.PYPDF2,
            page_count=page_count,
            char_count=char_count,
            success=True,
            metadata={'pages_extracted': len(text_parts)}
        )

    def _extract_ocr(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrai usando OCR (pytesseract).

        ATENÇÃO: OCR é lento e deve ser usado apenas como último recurso.
        """
        from PIL import Image
        import pytesseract
        from pdf2image import convert_from_path

        logger.debug(f"Tentando OCR em {pdf_path.name}")
        logger.warning("OCR habilitado - processamento será LENTO")

        try:
            # Converter PDF para imagens (limitar a 10 páginas para não travar)
            images = convert_from_path(pdf_path, first_page=1, last_page=10)
            page_count = len(images)

            text_parts = []
            for i, image in enumerate(images):
                try:
                    text = pytesseract.image_to_string(
                        image,
                        lang=self.ocr_lang
                    )
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(f"Erro OCR na página {i+1}: {e}")
                    continue

            full_text = '\n\n'.join(text_parts)
            char_count = len(full_text)

            return ExtractionResult(
                text=full_text,
                strategy=ExtractionStrategy.OCR,
                page_count=page_count,
                char_count=char_count,
                success=True,
                metadata={
                    'ocr_lang': self.ocr_lang,
                    'pages_extracted': len(text_parts),
                    'warning': 'Requer revisão manual (OCR pode ter erros)'
                }
            )

        except ImportError:
            logger.error("pdf2image não instalado (pip install pdf2image)")
            return ExtractionResult(
                text="",
                strategy=ExtractionStrategy.OCR,
                page_count=0,
                char_count=0,
                success=False,
                error_message="pdf2image não disponível"
            )
        except Exception as e:
            logger.error(f"Erro em OCR: {e}")
            return ExtractionResult(
                text="",
                strategy=ExtractionStrategy.OCR,
                page_count=0,
                char_count=0,
                success=False,
                error_message=str(e)
            )

    @staticmethod
    def calculate_hash(pdf_path: Path) -> str:
        """
        Calcula hash SHA256 de arquivo PDF.

        Args:
            pdf_path: Path para arquivo PDF

        Returns:
            Hash hexadecimal do arquivo
        """
        hasher = hashlib.sha256()

        with open(pdf_path, 'rb') as f:
            # Ler em chunks de 64KB
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)

        return hasher.hexdigest()


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Uso: python pdf_text_extractor.py <arquivo.pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    extractor = PDFTextExtractor(enable_ocr=False)
    result = extractor.extract(pdf_path)

    if result.success:
        print(f"\nExtração bem-sucedida!")
        print(f"Estratégia: {result.strategy.value}")
        print(f"Páginas: {result.page_count}")
        print(f"Caracteres: {result.char_count}")
        print(f"\nPrimeiros 500 caracteres:")
        print("=" * 70)
        print(result.text[:500])
        print("=" * 70)
    else:
        print(f"\nErro: {result.error_message}")
        sys.exit(1)
