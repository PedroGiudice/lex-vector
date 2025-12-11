"""
Legal Text Extractor - Sistema de Extração de Texto Jurídico

Entry point e API principal do sistema.

Architecture (Marker-only):
- MarkerEngine: Único engine de extração
  - Detecta automaticamente se precisa OCR
  - Preserva layout e estrutura
  - Output otimizado (sem imagens base64)

Pipeline:
1. Marker extrai texto (decide internamente nativo vs OCR)
2. DocumentCleaner remove artefatos de sistemas judiciais
3. (Futuro) Step 04 - Bibliotecário classifica seções via LLM
"""
import logging
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from src.engines.marker_engine import MarkerEngine, MarkerConfig
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
            output_format: Formato de saída ("text", "markdown", "json")
            force_ocr: Forçar OCR em todas as páginas (raramente necessário)

        Returns:
            ExtractionResult com texto limpo e metadados
        """
        start_time = time.time()
        pdf_path = Path(pdf_path)

        logger.info(f"=== PROCESSANDO: {pdf_path.name} ===")
        logger.info(f"Tamanho do arquivo: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB")

        # 1. Verifica disponibilidade do Marker
        if not self.marker_engine.is_available():
            ok, reason = self.marker_engine.check_resources()
            raise RuntimeError(f"Marker não disponível: {reason}")

        # 2. Extrai texto usando Marker
        logger.info("1/2 Extraindo texto com Marker...")
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
        native_pages = engine_result.metadata.get('native_pages', 0)
        ocr_pages = engine_result.metadata.get('ocr_pages', 0)

        logger.info(f"✓ Texto extraído: {len(raw_text):,} caracteres ({extract_time:.2f}s)")
        logger.info(f"  Páginas: {native_pages} nativas + {ocr_pages} OCR")

        # 3. Limpa texto (remove artefatos de sistemas judiciais)
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

        # Cria seção única para o documento (Step 04 fará classificação semântica)
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
            patterns_removed=cleaning_result.stats.patterns_removed,
            engine_used="marker",
            native_pages=native_pages,
            ocr_pages=ocr_pages,
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
        print("Usage: python main.py <pdf_file> [--force-ocr]")
        print()
        print("Options:")
        print("  --force-ocr    Force OCR on all pages (rarely needed)")
        print()
        print("Example:")
        print("  python main.py processo.pdf")
        print("  python main.py scanned_doc.pdf --force-ocr")
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
    force_ocr = "--force-ocr" in sys.argv

    extractor = LegalTextExtractor()
    result = extractor.process_pdf(pdf_file, force_ocr=force_ocr)

    print(f"\n{'='*60}")
    print(f"RESULTADO - {pdf_file.name}")
    print(f"{'='*60}")
    print(f"Engine: {result.engine_used}")
    print(f"Páginas: {result.native_pages} nativas + {result.ocr_pages} OCR")
    print(f"Sistema: {result.system_name} ({result.confidence}%)")
    print(f"Redução: {result.reduction_pct:.1f}%")
    print(f"Seções: {len(result.sections)}")
    print(f"\nTexto limpo ({result.final_length:,} caracteres):")
    print(result.text[:500] + "..." if len(result.text) > 500 else result.text)
    print(f"\n{'='*60}")
    print(f"Log completo salvo em: {log_file}")
    print(f"{'='*60}")
