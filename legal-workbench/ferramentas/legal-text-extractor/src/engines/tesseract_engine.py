"""
Tesseract OCR Engine - Extração via OCR para PDFs escaneados.

Engine para PDFs que não possuem texto nativo (imagens escaneadas).
Usa pytesseract + opencv para pré-processamento e extração OCR.

Reutiliza lógica do step_02_vision.py para processamento de imagens.
"""

import logging
from pathlib import Path
import tempfile

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    from pdf2image import convert_from_path
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from .base import ExtractionEngine, ExtractionResult

logger = logging.getLogger(__name__)


class TesseractEngine(ExtractionEngine):
    """
    Engine de extração usando Tesseract OCR.

    Características:
    - Moderada: ~1.0GB RAM
    - Média velocidade: Requer conversão PDF→imagem + OCR
    - Suporta: PDFs escaneados (sem texto nativo)

    Requer: tesseract-ocr, pytesseract, opencv, pdf2image

    Example:
        >>> engine = TesseractEngine(lang="por", psm=3)
        >>> if engine.is_available():
        ...     result = engine.extract(Path("scanned.pdf"))
        ...     print(f"OCR confidence: {result.confidence:.2f}")
    """

    name = "tesseract"
    min_ram_gb = 1.0
    dependencies = ["pytesseract", "PIL", "cv2", "pdf2image"]

    def __init__(
        self,
        lang: str = "por",
        psm: int = 3,
        dpi: int = 300,
        denoise: bool = True,
    ):
        """
        Inicializa Tesseract engine.

        Args:
            lang: Idioma para OCR (padrão: "por" - português)
            psm: Page Segmentation Mode (padrão: 3 - automático)
            dpi: DPI para conversão PDF→imagem (padrão: 300)
            denoise: Aplicar denoising em imagens (padrão: True)
        """
        self.lang = lang
        self.psm = psm
        self.dpi = dpi
        self.denoise = denoise

    def is_available(self) -> bool:
        """
        Verifica se Tesseract e dependências estão disponíveis.

        Returns:
            True se tesseract executável e bibliotecas estão instalados
        """
        if not TESSERACT_AVAILABLE:
            return False

        # Testa se Tesseract executável está acessível
        try:
            pytesseract.get_tesseract_version()
            return True
        except pytesseract.TesseractNotFoundError:
            return False

    def extract(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrai texto de PDF escaneado usando Tesseract OCR.

        Pipeline:
        1. Converte PDF → imagens (pdf2image)
        2. Pré-processa imagens (opencv): grayscale, denoise, threshold
        3. Executa OCR (pytesseract) em cada página
        4. Agrega resultados com confiança média

        Args:
            pdf_path: Caminho para arquivo PDF

        Returns:
            ExtractionResult com texto OCR e confiança média

        Raises:
            FileNotFoundError: Se PDF não existir
            RuntimeError: Se Tesseract não estiver disponível ou houver erro
        """
        if not self.is_available():
            raise RuntimeError(
                "Tesseract não está disponível. Instale com:\n"
                "  sudo apt install tesseract-ocr tesseract-ocr-por\n"
                "  pip install pytesseract opencv-python-headless pdf2image"
            )

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        try:
            logger.info(
                f"Extraindo texto via Tesseract OCR: {pdf_path.name} "
                f"(lang={self.lang}, psm={self.psm}, dpi={self.dpi})"
            )

            # Converte PDF para imagens
            images = convert_from_path(pdf_path, dpi=self.dpi)
            pages = len(images)

            logger.info(f"PDF convertido: {pages} páginas @ {self.dpi} DPI")

            # Processa cada página
            text_parts = []
            confidences = []
            total_chars = 0

            for page_num, image in enumerate(images, start=1):
                # Pré-processamento (similar a step_02_vision.py)
                processed_image = self._preprocess_image(image)

                # OCR com dados de confiança
                ocr_data = pytesseract.image_to_data(
                    processed_image,
                    lang=self.lang,
                    config=f"--psm {self.psm}",
                    output_type=pytesseract.Output.DICT,
                )

                # Extrai texto
                page_text = pytesseract.image_to_string(
                    processed_image,
                    lang=self.lang,
                    config=f"--psm {self.psm}",
                )

                # Calcula confiança da página (média dos valores > 0)
                page_confidences = [
                    float(conf) for conf in ocr_data["conf"] if int(conf) > 0
                ]
                page_confidence = (
                    sum(page_confidences) / len(page_confidences)
                    if page_confidences
                    else 0.0
                )

                if page_text.strip():
                    text_parts.append(page_text)
                    confidences.append(page_confidence)
                    total_chars += len(page_text)

                    logger.debug(
                        f"Página {page_num}/{pages}: "
                        f"{len(page_text)} chars, "
                        f"conf={page_confidence:.1f}%"
                    )
                else:
                    logger.warning(f"Página {page_num} retornou texto vazio após OCR")

            # Agrega resultados
            full_text = "\n\n".join(text_parts)
            avg_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )
            # Normaliza de 0-100% para 0.0-1.0
            normalized_confidence = avg_confidence / 100.0

            logger.info(
                f"OCR concluído: {pages} páginas, "
                f"{total_chars} caracteres, "
                f"confiança média={normalized_confidence:.2f}"
            )

            return ExtractionResult(
                text=full_text,
                pages=pages,
                engine_used=self.name,
                confidence=normalized_confidence,
                metadata={
                    "total_chars": total_chars,
                    "avg_chars_per_page": total_chars / pages if pages > 0 else 0,
                    "avg_confidence_pct": avg_confidence,
                    "lang": self.lang,
                    "psm": self.psm,
                    "dpi": self.dpi,
                    "pages_with_text": len(text_parts),
                },
            )

        except pytesseract.TesseractNotFoundError:
            raise RuntimeError(
                "Tesseract não encontrado. Instale com: "
                "sudo apt install tesseract-ocr tesseract-ocr-por"
            )
        except Exception as e:
            logger.error(f"Erro ao extrair PDF via Tesseract OCR: {e}")
            raise RuntimeError(f"Falha na extração com Tesseract: {e}") from e

    def _preprocess_image(self, image: "Image.Image") -> "np.ndarray":
        """
        Pré-processa imagem para melhorar qualidade OCR.

        Pipeline (baseado em step_02_vision.py):
        1. Converte PIL Image → numpy array
        2. Grayscale
        3. Denoising (opcional)
        4. Binarização (Otsu threshold)

        Args:
            image: PIL Image da página

        Returns:
            Numpy array com imagem processada
        """
        # PIL → numpy → BGR (opencv format)
        img_array = np.array(image)
        if len(img_array.shape) == 2:
            # Já é grayscale
            gray = img_array
        else:
            # Converte RGB/RGBA → BGR → Grayscale
            if img_array.shape[2] == 4:  # RGBA
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
            else:  # RGB
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)

        # Denoising (reduz ruído de scan)
        if self.denoise:
            gray = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)

        # Binarização adaptativa (melhora contraste)
        binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        return binary
