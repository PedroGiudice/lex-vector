"""Extrator OCR (Fase 2 - Placeholder)"""
from pathlib import Path


class OCRExtractor:
    """OCR para PDFs escaneados (FASE 2 - NÃO IMPLEMENTADO)"""

    def extract(self, pdf_path: Path) -> str:
        """Placeholder"""
        raise NotImplementedError(
            "OCR extraction not implemented yet (Fase 2). "
            "Use TextExtractor for PDFs with text layer."
        )
