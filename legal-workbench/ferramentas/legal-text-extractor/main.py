"""
Legal Text Extractor - Sistema de Extracao de Texto Juridico

Entry point e API principal do sistema.

Architecture (Marker-only):
- MarkerEngine: Unico engine de extracao
  - Detecta automaticamente se precisa OCR
  - Preserva layout e estrutura
  - Output otimizado (sem imagens base64)

Pipeline:
1. Marker extrai texto (decide internamente nativo vs OCR)
2. DocumentCleaner remove artefatos de sistemas judiciais
3. (Futuro) Step 04 - Bibliotecario classifica secoes via LLM

Performance Monitoring (2026-01-17):
- Sentry v8 com spans detalhados em cada fase
- Logging granular para diagnosticar "travamento em 10%"
- Track de memoria para identificar OOM issues

Environment Variables:
- SENTRY_DSN: Sentry Data Source Name (opcional)
- LTE_DEBUG: Set to "1" for verbose logging
- ENVIRONMENT: development/staging/production
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.core.cleaner import DocumentCleaner
from src.engines.marker_engine import MarkerConfig, MarkerEngine
from src.exporters.json import JSONExporter
from src.exporters.markdown import MarkdownExporter
from src.exporters.text import TextExporter

# Initialize monitoring FIRST (before other imports that might fail)
from src.monitoring import (
    capture_exception,
    init_monitoring,
    set_extraction_context,
    start_span,
    track_memory,
    track_progress,
)

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
    engine_used: str = "marker"
    native_pages: int = 0
    ocr_pages: int = 0


class LegalTextExtractor:
    """
    Sistema de extração de texto jurídico.

    Pipeline simplificada (Marker-only):
    1. Marker extrai texto (detecta automaticamente nativo vs OCR)
    2. DocumentCleaner remove artefatos de sistemas judiciais
    3. Output em formato configurável (text/markdown/json)

    O Marker é inteligente o suficiente para:
    - Usar texto nativo quando disponível (rápido)
    - Aplicar OCR apenas quando necessário (páginas escaneadas)
    - Preservar layout, tabelas e estrutura

    Example:
        >>> extractor = LegalTextExtractor()
        >>> result = extractor.process_pdf("processo.pdf")
        >>> print(f"Extraído: {result.final_length} caracteres")
        >>> print(f"Páginas nativas: {result.native_pages}, OCR: {result.ocr_pages}")
    """

    def __init__(
        self,
        marker_config: MarkerConfig | None = None,
        low_memory_mode: bool = False,
    ):
        """
        Inicializa o extrator.

        Args:
            marker_config: Configuração customizada do Marker (opcional)
            low_memory_mode: Ignorar verificação de RAM (use com cautela).
                            Útil para sistemas com <10GB RAM + swap disponível.
        """
        self.marker_engine = MarkerEngine(
            config=marker_config,
            low_memory_mode=low_memory_mode,
        )
        self.cleaner = DocumentCleaner()
        self.txt_exporter = TextExporter()
        self.md_exporter = MarkdownExporter()
        self.json_exporter = JSONExporter()
        self.low_memory_mode = low_memory_mode

    def process_pdf(
        self,
        pdf_path: Path | str,
        system: str | None = None,
        blacklist: list[str] | None = None,
        output_format: str = "text",  # "text", "markdown", "json"
        force_ocr: bool = False,
    ) -> ExtractionResult:
        """
        Processa PDF completo.

        Args:
            pdf_path: Caminho do PDF
            system: Sistema judicial (None = auto-detect)
            blacklist: Termos customizados a remover
            output_format: Formato de saida ("text", "markdown", "json")
            force_ocr: Forcar OCR em todas as paginas (raramente necessario)

        Returns:
            ExtractionResult com texto limpo e metadados
        """
        start_time = time.time()
        pdf_path = Path(pdf_path)

        # Set context for Sentry
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        set_extraction_context(str(pdf_path), file_size_mb)

        logger.info("=" * 70)
        logger.info(f"INICIANDO EXTRACAO: {pdf_path.name}")
        logger.info(f"Tamanho: {file_size_mb:.2f} MB | force_ocr: {force_ocr}")
        logger.info("=" * 70)

        track_memory("process_pdf.start")

        with start_span(
            "lte.process_pdf",
            f"Process PDF: {pdf_path.name}",
            file_size_mb=round(file_size_mb, 2),
            force_ocr=force_ocr,
        ) as process_span:
            try:
                # 1. Verifica disponibilidade do Marker
                with start_span("lte.check_marker", "Check Marker availability"):
                    track_progress(1, 4, "extracao")
                    if not self.marker_engine.is_available():
                        ok, reason = self.marker_engine.check_resources()
                        raise RuntimeError(f"Marker nao disponivel: {reason}")
                    logger.info("[1/4] Marker disponivel")

                # 2. Extrai texto usando Marker
                with start_span(
                    "lte.extract_text", "Extract text with Marker", force_ocr=force_ocr
                ) as extract_span:
                    track_progress(2, 4, "extracao")
                    logger.info("[2/4] Extraindo texto com Marker...")
                    track_memory("process_pdf.before_extract")

                    extract_start = time.time()

                    if force_ocr:
                        engine_result = self.marker_engine.extract_with_options(
                            pdf_path, force_ocr=True
                        )
                    else:
                        engine_result = self.marker_engine.extract(pdf_path)

                    raw_text = engine_result.text
                    extract_time = time.time() - extract_start

                    # Get extraction stats
                    native_pages = engine_result.metadata.get("native_pages", 0)
                    ocr_pages = engine_result.metadata.get("ocr_pages", 0)

                    extract_span.set_data("extract_time_seconds", round(extract_time, 2))
                    extract_span.set_data("text_length", len(raw_text))
                    extract_span.set_data("native_pages", native_pages)
                    extract_span.set_data("ocr_pages", ocr_pages)

                    logger.info(f"  Texto extraido: {len(raw_text):,} chars ({extract_time:.1f}s)")
                    logger.info(f"  Paginas: {native_pages} nativas + {ocr_pages} OCR")

                track_memory("process_pdf.after_extract")

                # 3. Limpa texto (remove artefatos de sistemas judiciais)
                with start_span("lte.clean_text", "Clean document text") as clean_span:
                    track_progress(3, 4, "extracao")
                    logger.info("[3/4] Limpando documento...")

                    clean_start = time.time()
                    cleaning_result = self.cleaner.clean(
                        text=raw_text, system=system, custom_blacklist=blacklist
                    )
                    clean_time = time.time() - clean_start

                    clean_span.set_data("clean_time_seconds", round(clean_time, 2))
                    clean_span.set_data("system_detected", cleaning_result.stats.system_name)
                    clean_span.set_data("reduction_pct", cleaning_result.stats.reduction_pct)
                    clean_span.set_data(
                        "patterns_removed", len(cleaning_result.stats.patterns_removed)
                    )

                    logger.info(
                        f"  Sistema: {cleaning_result.stats.system_name} "
                        f"({cleaning_result.stats.confidence}% confianca)"
                    )
                    logger.info(
                        f"  Reducao: {cleaning_result.stats.reduction_pct:.1f}% "
                        f"({cleaning_result.stats.original_length:,} -> "
                        f"{cleaning_result.stats.final_length:,} chars)"
                    )

                # 4. Cria resultado final
                with start_span("lte.finalize", "Finalize extraction result"):
                    track_progress(4, 4, "extracao")
                    logger.info("[4/4] Finalizando resultado...")

                    sections = [
                        Section(
                            type="documento_completo",
                            content=cleaning_result.text,
                            start_pos=0,
                            end_pos=len(cleaning_result.text),
                            confidence=1.0,
                        )
                    ]

                total_time = time.time() - start_time
                process_span.set_data("total_time_seconds", round(total_time, 2))
                process_span.set_data("success", True)

                track_memory("process_pdf.complete")

                logger.info("=" * 70)
                logger.info(f"EXTRACAO CONCLUIDA: {pdf_path.name}")
                logger.info(f"  Tempo total: {total_time:.1f}s")
                logger.info(f"  Texto final: {cleaning_result.stats.final_length:,} chars")
                logger.info(
                    f"  Velocidade: {(native_pages + ocr_pages) / total_time:.1f} pags/s"
                    if total_time > 0
                    else ""
                )
                logger.info("=" * 70)

                return ExtractionResult(
                    text=cleaning_result.text,
                    sections=sections,
                    system=cleaning_result.stats.system,
                    system_name=cleaning_result.stats.system_name,
                    confidence=cleaning_result.stats.confidence,
                    original_length=cleaning_result.stats.original_length,
                    final_length=cleaning_result.stats.final_length,
                    reduction_pct=cleaning_result.stats.reduction_pct,
                    patterns_removed=cleaning_result.stats.patterns_removed,
                    engine_used="marker",
                    native_pages=native_pages,
                    ocr_pages=ocr_pages,
                )

            except Exception as e:
                process_span.set_data("success", False)
                process_span.set_data("error", str(e))
                capture_exception(e, pdf_path=str(pdf_path), file_size_mb=file_size_mb)
                logger.error(f"ERRO na extracao: {e}")
                raise

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
            "patterns_removed_count": len(result.patterns_removed),
            "engine_used": result.engine_used,
            "native_pages": result.native_pages,
            "ocr_pages": result.ocr_pages,
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
                    patterns_removed=result.patterns_removed,
                ),
            )
            self.txt_exporter.export(cleaning_result, output_path)
        elif format == "markdown":
            self.md_exporter.export(result.sections, output_path, metadata)
        elif format == "json":
            self.json_exporter.export(result.sections, output_path, metadata)
        else:
            raise ValueError(f"Unknown format: {format}")


# CLI basico (para testes)
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Legal Text Extractor - CLI")
        print()
        print("Usage: python main.py <pdf_file> [options]")
        print()
        print("Options:")
        print("  --force-ocr    Force OCR on all pages (rarely needed)")
        print("  --debug        Enable verbose debug logging")
        print()
        print("Environment Variables:")
        print("  SENTRY_DSN     Sentry Data Source Name (for error tracking)")
        print("  LTE_DEBUG=1    Enable verbose logging")
        print()
        print("Example:")
        print("  python main.py processo.pdf")
        print("  python main.py scanned_doc.pdf --force-ocr")
        print("  LTE_DEBUG=1 python main.py processo.pdf")
        sys.exit(1)

    # Parse arguments
    pdf_file = Path(sys.argv[1])
    force_ocr = "--force-ocr" in sys.argv
    debug_mode = "--debug" in sys.argv or os.getenv("LTE_DEBUG", "0") == "1"

    if debug_mode:
        os.environ["LTE_DEBUG"] = "1"

    # Initialize monitoring (Sentry + logging)
    init_monitoring("legal-text-extractor")

    # Configure file logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"extraction_{timestamp}.log"

    # Add file handler for persistent logging
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )
    logging.getLogger().addHandler(file_handler)

    logger.info(f"Log salvo em: {log_file}")
    logger.info(f"Debug mode: {debug_mode}")

    try:
        with start_span("lte.cli", f"CLI extraction: {pdf_file.name}"):
            extractor = LegalTextExtractor()
            result = extractor.process_pdf(pdf_file, force_ocr=force_ocr)

        print(f"\n{'=' * 60}")
        print(f"RESULTADO - {pdf_file.name}")
        print(f"{'=' * 60}")
        print(f"Engine: {result.engine_used}")
        print(f"Paginas: {result.native_pages} nativas + {result.ocr_pages} OCR")
        print(f"Sistema: {result.system_name} ({result.confidence}%)")
        print(f"Reducao: {result.reduction_pct:.1f}%")
        print(f"Secoes: {len(result.sections)}")
        print(f"\nTexto limpo ({result.final_length:,} caracteres):")
        print(result.text[:500] + "..." if len(result.text) > 500 else result.text)
        print(f"\n{'=' * 60}")
        print(f"Log completo salvo em: {log_file}")
        print(f"{'=' * 60}")

    except Exception as e:
        logger.exception(f"Erro fatal: {e}")
        capture_exception(e, pdf_path=str(pdf_file))
        print(f"\nERRO: {e}")
        print(f"Verifique o log em: {log_file}")
        sys.exit(1)
