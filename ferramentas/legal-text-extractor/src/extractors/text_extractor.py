"""Extrator de texto usando pdfplumber"""
import pdfplumber
from pathlib import Path


class TextExtractor:
    """Extrai texto de PDFs com camada de texto"""

    def extract(self, pdf_path: Path) -> str:
        """
        Extrai texto de PDF usando pdfplumber.

        Args:
            pdf_path: Caminho do PDF

        Returns:
            Texto extraído
        """
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)

            return "\n\n".join(pages_text)

    def is_scanned(self, pdf_path: Path) -> bool:
        """
        Detecta se PDF é escaneado (sem texto).

        Returns:
            True se escaneado, False se tem texto
        """
        with pdfplumber.open(pdf_path) as pdf:
            # Testa primeira página
            if len(pdf.pages) > 0:
                text = pdf.pages[0].extract_text()
                # Se tem menos de 50 caracteres, provavelmente é escaneado
                return not text or len(text.strip()) < 50
        return True
