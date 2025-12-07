#!/usr/bin/env python3
"""
Demonstração de uso das extraction engines.

Mostra como usar cada engine individualmente e o EngineSelector automático.
"""

import sys
from pathlib import Path

# Adiciona src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.engines import (
    PDFPlumberEngine,
    TesseractEngine,
    MarkerEngine,
    EngineSelector,
)


def demo_pdfplumber(pdf_path: Path):
    """Demonstra uso do PDFPlumber."""
    print("\n" + "="*60)
    print("DEMO: PDFPlumber Engine")
    print("="*60)

    engine = PDFPlumberEngine()

    if not engine.is_available():
        print("✗ PDFPlumber não disponível")
        return

    print(f"✓ Engine: {engine}")
    print(f"  RAM mínima: {engine.min_ram_gb}GB")

    try:
        result = engine.extract(pdf_path)
        print(f"\n✓ Extração bem-sucedida:")
        print(f"  Páginas: {result.pages}")
        print(f"  Caracteres: {len(result.text)}")
        print(f"  Confiança: {result.confidence:.2f}")
        print(f"  Engine: {result.engine_used}")
        print(f"\nPrimeiros 200 caracteres:")
        print(result.text[:200])
    except Exception as e:
        print(f"✗ Erro: {e}")


def demo_tesseract(pdf_path: Path):
    """Demonstra uso do Tesseract OCR."""
    print("\n" + "="*60)
    print("DEMO: Tesseract Engine")
    print("="*60)

    engine = TesseractEngine(lang="por", psm=3, dpi=300)

    if not engine.is_available():
        print("✗ Tesseract não disponível")
        print("  Instale com: sudo apt install tesseract-ocr tesseract-ocr-por")
        return

    print(f"✓ Engine: {engine}")
    print(f"  RAM mínima: {engine.min_ram_gb}GB")
    print(f"  Idioma: {engine.lang}")
    print(f"  PSM: {engine.psm}")
    print(f"  DPI: {engine.dpi}")

    try:
        print("\n⏳ Processando (pode demorar alguns segundos)...")
        result = engine.extract(pdf_path)
        print(f"\n✓ OCR bem-sucedido:")
        print(f"  Páginas: {result.pages}")
        print(f"  Caracteres: {len(result.text)}")
        print(f"  Confiança média: {result.confidence:.2f}")
        print(f"  Confiança OCR: {result.metadata.get('avg_confidence_pct', 0):.1f}%")
        print(f"\nPrimeiros 200 caracteres:")
        print(result.text[:200])
    except Exception as e:
        print(f"✗ Erro: {e}")


def demo_marker(pdf_path: Path):
    """Demonstra uso do Marker (se disponível)."""
    print("\n" + "="*60)
    print("DEMO: Marker Engine")
    print("="*60)

    engine = MarkerEngine()

    if not engine.is_available():
        ok, reason = engine.check_resources()
        print(f"✗ Marker não disponível: {reason}")
        print("\nMarker é opcional e requer:")
        print("  - Sistema com >= 8GB RAM disponível")
        print("  - pip install marker-pdf")
        return

    print(f"✓ Engine: {engine}")
    print(f"  RAM mínima: {engine.min_ram_gb}GB")

    try:
        result = engine.extract(pdf_path)
        print(f"\n✓ Extração ML bem-sucedida:")
        print(f"  Páginas: {result.pages}")
        print(f"  Caracteres: {len(result.text)}")
        print(f"  Confiança: {result.confidence:.2f}")
    except NotImplementedError as e:
        print(f"⚠ Marker ainda é um stub: {e}")
    except Exception as e:
        print(f"✗ Erro: {e}")


def demo_selector(pdf_path: Path):
    """Demonstra uso do EngineSelector automático."""
    print("\n" + "="*60)
    print("DEMO: EngineSelector (Automático)")
    print("="*60)

    selector = EngineSelector()

    print(f"✓ Selector criado")
    print(f"  Engines registradas: {list(selector.engines.keys())}")

    # Engines disponíveis
    available = selector.get_available_engines()
    print(f"  Engines disponíveis: {[e.name for e in available]}")

    # Análise do PDF
    print(f"\n📄 Analisando PDF...")
    analysis = selector.analyze_pdf(pdf_path)
    print(f"  Páginas: {analysis['pages']}")
    print(f"  Texto nativo: {analysis['native_text_ratio']:.0%}")
    print(f"  Caracteres/página: {analysis['avg_chars_per_page']:.0f}")

    # Seleção automática
    selected = selector.select_engine(pdf_path)
    if selected:
        print(f"\n🎯 Engine selecionada: {selected.name}")
    else:
        print(f"\n✗ Nenhuma engine disponível")
        return

    # Extração com fallback
    try:
        print(f"\n⏳ Extraindo com fallback automático...")
        result = selector.extract_with_fallback(pdf_path, max_retries=3)
        print(f"\n✓ Extração bem-sucedida:")
        print(f"  Engine usada: {result.engine_used}")
        print(f"  Páginas: {result.pages}")
        print(f"  Caracteres: {len(result.text)}")
        print(f"  Confiança: {result.confidence:.2f}")
        print(f"\nPrimeiros 200 caracteres:")
        print(result.text[:200])
    except Exception as e:
        print(f"✗ Todas as engines falharam: {e}")


def main():
    """Executa todas as demos."""
    # PDF de exemplo (substitua pelo caminho real)
    pdf_path = Path("inputs/exemplo.pdf")

    if not pdf_path.exists():
        print("="*60)
        print("ERRO: PDF de exemplo não encontrado")
        print("="*60)
        print(f"Esperado em: {pdf_path.absolute()}")
        print("\nPara testar, coloque um PDF em 'inputs/exemplo.pdf'")
        print("ou modifique a variável 'pdf_path' neste script.")
        return 1

    print("="*60)
    print("EXTRACTION ENGINES - DEMONSTRAÇÃO")
    print("="*60)
    print(f"PDF: {pdf_path.name}")

    # Demos individuais
    demo_pdfplumber(pdf_path)
    demo_tesseract(pdf_path)
    demo_marker(pdf_path)

    # Demo selector (recomendado)
    demo_selector(pdf_path)

    print("\n" + "="*60)
    print("DEMONSTRAÇÃO CONCLUÍDA")
    print("="*60)
    print("\nRecomendação: Use EngineSelector para seleção automática")
    print("com fallback inteligente entre engines.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
