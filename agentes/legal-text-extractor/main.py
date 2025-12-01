"""
Legal Text Extractor - Sistema de Extração de Texto Jurídico

Entry point e API principal do sistema.
"""
import logging
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from src.extractors.text_extractor import TextExtractor
from src.extractors.ocr_extractor import OCRExtractor
from src.core.cleaner import DocumentCleaner
from src.exporters.text import TextExporter
from src.exporters.markdown import MarkdownExporter
from src.exporters.json import JSONExporter

# Configurar logging
logger = logging.getLogger(__name__)


@dataclass
class Section:
    """Seção de documento (estrutura simples sem dependência de SDK)"""
    type: str
    content: str
    start_pos: int
    end_pos: int
    confidence: float


@dataclass
class ExtractionResult:
    """Resultado completo da extração"""
    text: str
    sections: list[Section]
    system: str
    system_name: str
    confidence: int
    original_length: int
    final_length: int
    reduction_pct: float
    patterns_removed: list[str]


class LegalTextExtractor:
    """
    Sistema de extração de texto jurídico.

    Combina extração de texto e limpeza semântica.
    """

    def __init__(self):
        self.text_extractor = TextExtractor()
        self.ocr_extractor = OCRExtractor()
        self.cleaner = DocumentCleaner()
        self.txt_exporter = TextExporter()
        self.md_exporter = MarkdownExporter()
        self.json_exporter = JSONExporter()

    def process_pdf(
        self,
        pdf_path: Path | str,
        system: str | None = None,
        blacklist: list[str] | None = None,
        output_format: str = "text"  # "text", "markdown", "json"
    ) -> ExtractionResult:
        """
        Processa PDF completo.

        Args:
            pdf_path: Caminho do PDF
            system: Sistema judicial (None = auto-detect)
            blacklist: Termos customizados a remover
            output_format: Formato de saída ("text", "markdown", "json")

        Returns:
            ExtractionResult com texto limpo e metadados
        """
        start_time = time.time()
        pdf_path = Path(pdf_path)

        logger.info(f"=== PROCESSANDO: {pdf_path.name} ===")
        logger.info(f"Tamanho do arquivo: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB")

        # 1. Extrai texto
        logger.info("1/2 Extraindo texto do PDF...")
        extract_start = time.time()

        if self.text_extractor.is_scanned(pdf_path):
            logger.warning("PDF escaneado detectado - OCR não implementado (Fase 2)")
            raise NotImplementedError("OCR not implemented yet (Fase 2)")

        raw_text = self.text_extractor.extract(pdf_path)
        extract_time = time.time() - extract_start

        logger.info(f"✓ Texto extraído: {len(raw_text):,} caracteres ({extract_time:.2f}s)")

        # 2. Limpa texto
        logger.info("2/2 Limpando documento...")
        clean_start = time.time()

        cleaning_result = self.cleaner.clean(
            text=raw_text,
            system=system,
            custom_blacklist=blacklist
        )
        clean_time = time.time() - clean_start

        logger.info(f"✓ Sistema detectado: {cleaning_result.stats.system_name} "
                   f"({cleaning_result.stats.confidence}% confiança)")
        logger.info(f"✓ Redução: {cleaning_result.stats.reduction_pct:.1f}% "
                   f"({cleaning_result.stats.original_length:,} → {cleaning_result.stats.final_length:,} chars)")
        logger.info(f"✓ Padrões removidos: {len(cleaning_result.stats.patterns_removed)} ({clean_time:.2f}s)")

        # Cria seção única para o documento
        sections = [Section(
            type="documento_completo",
            content=cleaning_result.text,
            start_pos=0,
            end_pos=len(cleaning_result.text),
            confidence=1.0
        )]

        # Retorna resultado
        total_time = time.time() - start_time
        logger.info(f"=== CONCLUÍDO: {total_time:.2f}s total "
                   f"(extração: {extract_time:.2f}s, limpeza: {clean_time:.2f}s) ===\n")

        return ExtractionResult(
            text=cleaning_result.text,
            sections=sections,
            system=cleaning_result.stats.system,
            system_name=cleaning_result.stats.system_name,
            confidence=cleaning_result.stats.confidence,
            original_length=cleaning_result.stats.original_length,
            final_length=cleaning_result.stats.final_length,
            reduction_pct=cleaning_result.stats.reduction_pct,
            patterns_removed=cleaning_result.stats.patterns_removed
        )

    def save(self, result: ExtractionResult, output_path: Path | str, format: str = "text"):
        """
        Salva resultado em arquivo.

        Args:
            result: ExtractionResult
            output_path: Caminho de saída
            format: "text", "markdown" ou "json"
        """
        output_path = Path(output_path)

        metadata = {
            "system": result.system,
            "system_name": result.system_name,
            "confidence": result.confidence,
            "reduction_pct": result.reduction_pct,
            "patterns_removed_count": len(result.patterns_removed)
        }

        if format == "text":
            # Cria CleaningResult temporário para compatibilidade com TextExporter
            from src.core.cleaner import CleaningResult, CleaningStats
            cleaning_result = CleaningResult(
                text=result.text,
                stats=CleaningStats(
                    system=result.system,
                    system_name=result.system_name,
                    confidence=result.confidence,
                    original_length=result.original_length,
                    final_length=result.final_length,
                    reduction_pct=result.reduction_pct,
                    patterns_removed=result.patterns_removed
                )
            )
            self.txt_exporter.export(cleaning_result, output_path)
        elif format == "markdown":
            self.md_exporter.export(result.sections, output_path, metadata)
        elif format == "json":
            self.json_exporter.export(result.sections, output_path, metadata)
        else:
            raise ValueError(f"Unknown format: {format}")


# CLI básico (para testes)
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <pdf_file>")
        sys.exit(1)

    # Configurar logging (console + arquivo)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"extraction_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logger.info(f"Log salvo em: {log_file}")

    pdf_file = Path(sys.argv[1])

    extractor = LegalTextExtractor()
    result = extractor.process_pdf(pdf_file, separate_sections=False)

    print(f"\n{'='*60}")
    print(f"RESULTADO - {pdf_file.name}")
    print(f"{'='*60}")
    print(f"Sistema: {result.system_name} ({result.confidence}%)")
    print(f"Redução: {result.reduction_pct:.1f}%")
    print(f"Seções: {len(result.sections)}")
    print(f"\nTexto limpo ({result.final_length} caracteres):")
    print(result.text[:500] + "...")
    print(f"\n{'='*60}")
    print(f"Log completo salvo em: {log_file}")
    print(f"{'='*60}")
