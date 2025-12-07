"""
Módulo de integração com o Legal Text Extractor.

Este módulo é apenas um WRAPPER - toda a lógica de extração está em:
ferramentas/legal-text-extractor/

NÃO reimplementa nada, apenas importa e usa os módulos existentes.
"""

import sys
import logging
from pathlib import Path
from typing import Callable
from dataclasses import dataclass

# Adiciona o legal-text-extractor ao path
# De: legal-extractor-cli/src/legal_extractor_cli/extractor.py
# Para: ferramentas/legal-text-extractor/
EXTRACTOR_PATH = Path(__file__).parent.parent.parent.parent / "ferramentas" / "legal-text-extractor"
if str(EXTRACTOR_PATH) not in sys.path:
    sys.path.insert(0, str(EXTRACTOR_PATH))

logger = logging.getLogger(__name__)


@dataclass
class ExtractionProgress:
    """Progress update durante extração."""
    stage: str  # "layout", "vision", "extract", "clean"
    page: int
    total_pages: int
    message: str
    percentage: float


@dataclass
class ExtractionSummary:
    """Resumo da extração completa."""
    success: bool
    total_pages: int
    native_pages: int
    raster_pages: int
    engine_used: str
    output_path: Path | None
    error: str | None = None
    processing_time_s: float = 0.0
    final_text_length: int = 0
    reduction_pct: float = 0.0


def get_system_info() -> dict:
    """Retorna informações do sistema para seleção de engine."""
    import psutil
    import platform
    import socket

    total_ram = psutil.virtual_memory().total / (1024**3)
    available_ram = psutil.virtual_memory().available / (1024**3)

    # Detecta máquina pelo hostname
    hostname = socket.gethostname().lower()
    is_work_pc = "work" in hostname or total_ram >= 14  # 16GB indica PC trabalho

    return {
        "hostname": hostname,
        "total_ram_gb": round(total_ram, 1),
        "available_ram_gb": round(available_ram, 1),
        "platform": platform.system(),
        "is_work_pc": is_work_pc,
        "marker_available": available_ram >= 4.0,  # Marker precisa ~4GB
    }


def check_tesseract() -> bool:
    """Verifica se Tesseract está instalado."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def check_marker() -> bool:
    """Verifica se Marker está disponível."""
    try:
        from marker.converters.pdf import PdfConverter
        return True
    except ImportError:
        return False


def run_extraction(
    pdf_path: Path,
    output_dir: Path | None = None,
    system: str | None = None,
    progress_callback: Callable[[ExtractionProgress], None] | None = None,
) -> ExtractionSummary:
    """
    Executa extração completa de um PDF.

    Esta função é um WRAPPER que chama os módulos do legal-text-extractor.

    Args:
        pdf_path: Caminho do PDF a extrair
        output_dir: Diretório de saída (padrão: outputs/{doc_id}/)
        system: Sistema judicial forçado (PJE, ESAJ, etc.) ou None para auto
        progress_callback: Callback para atualizações de progresso

    Returns:
        ExtractionSummary com resultados
    """
    import time
    start_time = time.time()

    # Valida arquivo
    pdf_path = Path(pdf_path).resolve()
    if not pdf_path.exists():
        return ExtractionSummary(
            success=False,
            total_pages=0,
            native_pages=0,
            raster_pages=0,
            engine_used="none",
            output_path=None,
            error=f"Arquivo não encontrado: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        return ExtractionSummary(
            success=False,
            total_pages=0,
            native_pages=0,
            raster_pages=0,
            engine_used="none",
            output_path=None,
            error=f"Arquivo não é PDF: {pdf_path}"
        )

    def emit_progress(stage: str, page: int, total: int, msg: str, pct: float):
        if progress_callback:
            progress_callback(ExtractionProgress(
                stage=stage,
                page=page,
                total_pages=total,
                message=msg,
                percentage=pct
            ))

    try:
        # Importa módulos do extrator DIRETAMENTE (sem main.py que puxa anthropic)
        from src.steps.step_01_layout import LayoutAnalyzer
        from src.extractors.text_extractor import TextExtractor
        from src.core.cleaner import DocumentCleaner
        from src.config import PageType, get_output_dir

        # Define output dir
        doc_id = pdf_path.stem
        if output_dir is None:
            output_dir = get_output_dir(doc_id)
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        # === ESTÁGIO 1: Layout Analysis ===
        emit_progress("layout", 0, 0, "Analisando estrutura do PDF...", 0.1)

        analyzer = LayoutAnalyzer()
        layout = analyzer.analyze(pdf_path)

        total_pages = layout["total_pages"]
        native_count = sum(1 for p in layout["pages"] if p["type"] == PageType.NATIVE)
        raster_count = sum(1 for p in layout["pages"] if p["type"] == "RASTER_NEEDED")

        emit_progress("layout", total_pages, total_pages, f"Layout: {total_pages} páginas", 0.2)

        # Salva layout.json
        layout_path = output_dir / "layout.json"
        analyzer.save(layout, layout_path)

        # === ESTÁGIO 2: Extração ===
        emit_progress("extract", 0, total_pages, "Iniciando extração de texto...", 0.3)

        text_extractor = TextExtractor()
        cleaner = DocumentCleaner()

        # Emite progresso por página
        for i, page_data in enumerate(layout["pages"], 1):
            page_type = page_data["type"]
            engine = page_data.get("recommended_engine", "pdfplumber")
            emit_progress(
                "extract",
                i,
                total_pages,
                f"Página {i}/{total_pages} ({page_type} → {engine})",
                0.3 + (i / total_pages) * 0.5
            )

        # Verifica se é PDF escaneado
        if text_extractor.is_scanned(pdf_path):
            return ExtractionSummary(
                success=False,
                total_pages=total_pages,
                native_pages=native_count,
                raster_pages=raster_count,
                engine_used="none",
                output_path=None,
                error="PDF escaneado detectado. OCR ainda não implementado nesta versão."
            )

        # Extrai texto (pdfplumber)
        raw_text = text_extractor.extract(pdf_path)
        original_length = len(raw_text)

        emit_progress("clean", total_pages, total_pages, "Limpando texto...", 0.8)

        # Limpa texto
        cleaning_result = cleaner.clean(
            text=raw_text,
            system=system,
            custom_blacklist=None
        )

        # Determina engine usado
        engines_used = set(p.get("recommended_engine", "pdfplumber") for p in layout["pages"])
        engine_str = "+".join(sorted(engines_used))

        # Salva resultado
        output_path = output_dir / "final.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(cleaning_result.text, encoding="utf-8")

        emit_progress("clean", total_pages, total_pages, "Extração concluída!", 1.0)

        processing_time = time.time() - start_time

        return ExtractionSummary(
            success=True,
            total_pages=total_pages,
            native_pages=native_count,
            raster_pages=raster_count,
            engine_used=engine_str,
            output_path=output_path,
            processing_time_s=round(processing_time, 2),
            final_text_length=cleaning_result.stats.final_length,
            reduction_pct=cleaning_result.stats.reduction_pct,
        )

    except NotImplementedError as e:
        # OCR não implementado ainda
        return ExtractionSummary(
            success=False,
            total_pages=0,
            native_pages=0,
            raster_pages=0,
            engine_used="none",
            output_path=None,
            error=f"OCR não implementado: {e}. Este PDF contém páginas escaneadas."
        )

    except Exception as e:
        logger.exception("Erro na extração")
        return ExtractionSummary(
            success=False,
            total_pages=0,
            native_pages=0,
            raster_pages=0,
            engine_used="none",
            output_path=None,
            error=str(e)
        )
