"""
Exemplo de uso do Step 02: Vision Pipeline

Demonstra uso programático do VisionProcessor para processar
páginas RASTER_NEEDED.
"""

from pathlib import Path
import logging

from src.config import VisionConfig, get_images_dir
from src.steps.step_02_vision import VisionProcessor


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def example_basic():
    """Exemplo básico: uso com configuração padrão."""
    print("\n" + "="*60)
    print("EXEMPLO 1: Uso Básico")
    print("="*60 + "\n")

    # Inputs
    layout_path = Path("outputs/exemplo_scan/layout.json")
    pdf_path = Path("test-documents/exemplo_scan.pdf")
    doc_id = "exemplo_scan"

    # Cria processor
    processor = VisionProcessor()

    # Processa
    print(f"Processando: {pdf_path}")
    results = processor.process(layout_path, pdf_path, doc_id)

    # Análise
    print(f"\nResultados:")
    print(f"  - Imagens geradas: {len(results)}")

    if results:
        total_pixels = sum(r.width * r.height for r in results)
        avg_mp = (total_pixels / len(results)) / 1_000_000
        print(f"  - Tamanho médio: {avg_mp:.1f} MP")
        print(f"\nDetalhes:")
        for r in results:
            size_mb = r.output_path.stat().st_size / (1024 * 1024)
            print(f"    Página {r.page_num:3d}: {r.width}x{r.height}px ({size_mb:.1f} MB)")
            print(f"      → {r.output_path}")


def example_custom_config():
    """Exemplo 2: Configuração customizada para scans antigos."""
    print("\n" + "="*60)
    print("EXEMPLO 2: Configuração Customizada (Scans Antigos)")
    print("="*60 + "\n")

    # Configuração para scans de baixa qualidade
    config = VisionConfig(
        render_dpi=400,         # Maior resolução
        denoise_strength=15,    # Denoise agressivo
        output_format="png"     # PNG lossless
    )

    processor = VisionProcessor(config)

    # Inputs
    layout_path = Path("outputs/scan_antigo/layout.json")
    pdf_path = Path("test-documents/scan_1995.pdf")
    doc_id = "scan_antigo"

    print(f"Configuração:")
    print(f"  - DPI: {config.render_dpi}")
    print(f"  - Denoise: {config.denoise_strength}")
    print(f"  - Formato: {config.output_format}")
    print()

    # Processa
    results = processor.process(layout_path, pdf_path, doc_id)

    print(f"\n{len(results)} imagens processadas com qualidade alta")


def example_performance_optimized():
    """Exemplo 3: Otimizado para performance (batch processing)."""
    print("\n" + "="*60)
    print("EXEMPLO 3: Otimizado para Performance")
    print("="*60 + "\n")

    # Configuração rápida
    config = VisionConfig(
        render_dpi=150,         # DPI mínimo
        denoise_strength=0,     # Sem denoise
        output_format="jpg",    # JPEG compacto
        jpeg_quality=85
    )

    processor = VisionProcessor(config)

    # Lista de documentos
    documents = [
        ("doc001", "outputs/doc001/layout.json", "inputs/doc001.pdf"),
        ("doc002", "outputs/doc002/layout.json", "inputs/doc002.pdf"),
        ("doc003", "outputs/doc003/layout.json", "inputs/doc003.pdf"),
    ]

    print(f"Processando {len(documents)} documentos em batch...")
    print(f"Configuração: DPI={config.render_dpi}, denoise=off, formato=JPG")
    print()

    total_images = 0
    for doc_id, layout_path, pdf_path in documents:
        try:
            results = processor.process(
                Path(layout_path),
                Path(pdf_path),
                doc_id
            )
            total_images += len(results)
            print(f"  ✓ {doc_id}: {len(results)} imagens")
        except Exception as e:
            print(f"  ✗ {doc_id}: Erro - {e}")

    print(f"\nTotal: {total_images} imagens processadas")


def example_inspect_layout():
    """Exemplo 4: Inspecionar layout antes de processar."""
    print("\n" + "="*60)
    print("EXEMPLO 4: Análise de Layout")
    print("="*60 + "\n")

    import json

    layout_path = Path("outputs/exemplo_scan/layout.json")

    # Carrega layout
    with open(layout_path) as f:
        layout = json.load(f)

    # Estatísticas
    total_pages = len(layout["pages"])
    native_pages = sum(1 for p in layout["pages"] if p["type"] == "NATIVE")
    raster_pages = sum(1 for p in layout["pages"] if p["type"] == "RASTER_NEEDED")
    pages_with_tarja = sum(1 for p in layout["pages"] if p.get("has_tarja", False))

    print(f"Documento: {layout.get('document_id', 'N/A')}")
    print(f"\nEstatísticas:")
    print(f"  - Total de páginas: {total_pages}")
    print(f"  - NATIVE (texto extraível): {native_pages}")
    print(f"  - RASTER_NEEDED (precisa OCR): {raster_pages}")
    print(f"  - Com tarja lateral: {pages_with_tarja}")

    # Detalhes das páginas RASTER_NEEDED
    if raster_pages > 0:
        print(f"\nPáginas que serão processadas pelo Step 02:")
        for page in layout["pages"]:
            if page["type"] == "RASTER_NEEDED":
                bbox = page["safe_bbox"]
                print(f"  - Página {page['page_num']:3d}: "
                      f"bbox={tuple(bbox)}, "
                      f"tarja={page.get('has_tarja', False)}, "
                      f"chars={page.get('text_chars', 0)}")

        # Estimativa de processamento
        avg_time_per_page = 1.0  # segundos
        estimated_time = raster_pages * avg_time_per_page
        print(f"\nTempo estimado: {estimated_time:.0f}s "
              f"({raster_pages} páginas × {avg_time_per_page}s)")
    else:
        print("\n⚠ Nenhuma página precisa de processamento (Step 02 não necessário)")


def example_error_handling():
    """Exemplo 5: Tratamento de erros robusto."""
    print("\n" + "="*60)
    print("EXEMPLO 5: Tratamento de Erros")
    print("="*60 + "\n")

    processor = VisionProcessor()

    # Teste 1: Layout inexistente
    print("Teste 1: Layout inexistente")
    try:
        processor.process(
            Path("outputs/missing/layout.json"),
            Path("test-documents/dummy.pdf"),
            "test"
        )
    except FileNotFoundError as e:
        print(f"  ✓ Erro capturado: {e}")

    # Teste 2: PDF inexistente
    print("\nTeste 2: PDF inexistente")
    try:
        processor.process(
            Path("outputs/exemplo_scan/layout.json"),
            Path("missing.pdf"),
            "test"
        )
    except FileNotFoundError as e:
        print(f"  ✓ Erro capturado: {e}")

    # Teste 3: Processamento parcial (continua em caso de erro)
    print("\nTeste 3: Processamento robusto")
    print("  (Continua processando mesmo se uma página falhar)")


if __name__ == "__main__":
    import sys

    examples = {
        "1": ("Uso Básico", example_basic),
        "2": ("Configuração Customizada", example_custom_config),
        "3": ("Performance Otimizada", example_performance_optimized),
        "4": ("Análise de Layout", example_inspect_layout),
        "5": ("Tratamento de Erros", example_error_handling),
    }

    if len(sys.argv) > 1 and sys.argv[1] in examples:
        name, func = examples[sys.argv[1]]
        func()
    else:
        print("Exemplos de uso do Step 02: Vision Pipeline")
        print("=" * 60)
        print("\nUso: python examples/step_02_example.py [numero]\n")
        print("Exemplos disponíveis:")
        for num, (name, _) in examples.items():
            print(f"  {num} - {name}")
        print("\nOu execute todos:")
        print("  python examples/step_02_example.py all")
        print()

        if len(sys.argv) > 1 and sys.argv[1] == "all":
            for _, func in examples.values():
                func()
