#!/usr/bin/env python3
"""
Teste rápido do step_01_layout.py

Valida o algoritmo de histograma de densidade e detecção de tarjas.
"""

import sys
from pathlib import Path

# Adiciona src ao PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importa diretamente do módulo (evita __init__.py que pode ter dependências não instaladas)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "step_01_layout",
    project_root / "src" / "steps" / "step_01_layout.py"
)
step_01_module = importlib.util.module_from_spec(spec)

# Importa config antes (necessário para o módulo)
from src.config import PageType

# Executa o módulo
spec.loader.exec_module(step_01_module)
LayoutAnalyzer = step_01_module.LayoutAnalyzer


def test_forscher_pdf():
    """Testa PDF sem tarjas (maioria das páginas)."""
    pdf_path = project_root / "test-documents" / "Forscher x Salesforce - íntegra 25.09.2025.PDF"

    if not pdf_path.exists():
        print(f"⚠️  PDF não encontrado: {pdf_path}")
        return

    analyzer = LayoutAnalyzer()
    layout = analyzer.analyze(pdf_path)

    # Validações
    assert layout["total_pages"] == 82, "Deveria ter 82 páginas"

    # Maioria deveria ser NATIVE (texto extraível)
    native_count = sum(1 for p in layout["pages"] if p["type"] == PageType.NATIVE)
    assert native_count > 70, f"Deveria ter >70 páginas NATIVE, obteve {native_count}"

    # Algumas páginas com tarja
    tarja_count = sum(1 for p in layout["pages"] if p["has_tarja"])
    print(f"✅ Forscher PDF: {native_count}/82 NATIVE, {tarja_count} com tarja")


def test_pje_pdf():
    """Testa PDF do PJe (100% tarjas, mix NATIVE/RASTER)."""
    pdf_path = project_root / "test-documents" / "1057607-11.2024.8.26.0002.pdf"

    if not pdf_path.exists():
        print(f"⚠️  PDF não encontrado: {pdf_path}")
        return

    analyzer = LayoutAnalyzer()
    layout = analyzer.analyze(pdf_path)

    # Validações
    assert layout["total_pages"] == 291, "Deveria ter 291 páginas"

    # 100% deveria ter tarja (PJe)
    tarja_count = sum(1 for p in layout["pages"] if p["has_tarja"])
    assert tarja_count == 291, f"Todas páginas deveriam ter tarja, obteve {tarja_count}/291"

    # Mix de NATIVE e RASTER_NEEDED
    native_count = sum(1 for p in layout["pages"] if p["type"] == PageType.NATIVE)
    raster_count = sum(1 for p in layout["pages"] if p["type"] == PageType.RASTER_NEEDED)

    assert native_count > 0, "Deveria ter algumas páginas NATIVE"
    assert raster_count > 0, "Deveria ter algumas páginas RASTER_NEEDED"

    # Validar safe_bbox foi ajustado (maioria das páginas)
    pages_with_reduced_bbox = 0
    for page in layout["pages"]:
        if page["has_tarja"]:
            assert "tarja_x_cut" in page, "Página com tarja deveria ter tarja_x_cut"
            # Conta quantas páginas tiveram safe_bbox reduzido
            if page["safe_bbox"][2] < 500:
                pages_with_reduced_bbox += 1

    # Maioria deveria ter bbox reduzido
    assert pages_with_reduced_bbox > 250, f"Maioria deveria ter bbox reduzido, obteve {pages_with_reduced_bbox}/291"

    print(f"✅ PJe PDF: {native_count} NATIVE, {raster_count} RASTER_NEEDED, {tarja_count}/291 com tarja")


def test_histogram_algorithm():
    """Testa algoritmo de histograma isoladamente."""
    analyzer = LayoutAnalyzer()

    # Mock de chars concentrados nos últimos 20% da largura
    page_width = 500.0
    chars = [
        {"x0": 410, "x1": 420, "top": 100},  # Na zona de tarja (>400)
        {"x0": 420, "x1": 430, "top": 200},
        {"x0": 430, "x1": 440, "top": 300},
        {"x0": 440, "x1": 450, "top": 400},
        {"x0": 450, "x1": 460, "top": 500},
        # Poucos chars na área útil
        {"x0": 50, "x1": 60, "top": 100},
        {"x0": 100, "x1": 110, "top": 200},
    ]

    has_tarja, x_cut = analyzer._detect_tarja(chars, page_width)

    # Com 5/7 chars na zona de tarja (71%), deveria detectar
    assert has_tarja, "Deveria detectar tarja com densidade alta"
    assert x_cut is not None, "Deveria retornar x_cut"
    assert x_cut == page_width * 0.8, f"x_cut deveria ser 80% da largura (400), obteve {x_cut}"

    print(f"✅ Algoritmo de histograma: tarja detectada em x={x_cut}")


if __name__ == "__main__":
    print("🧪 Testando step_01_layout.py\n")

    try:
        test_histogram_algorithm()
        test_forscher_pdf()
        test_pje_pdf()
        print("\n✅ Todos os testes passaram!")
    except AssertionError as e:
        print(f"\n❌ Falha: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
