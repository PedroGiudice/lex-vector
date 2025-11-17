#!/usr/bin/env python3
"""
Exemplo de Uso Completo - Filtro OAB Profissional

Este script demonstra como usar o sistema de filtro OAB para encontrar
publicações relevantes em cadernos judiciais.

Execute com: python exemplo_filtro_oab.py <dir_com_pdfs>

Author: Claude Code (Development Agent)
Version: 1.0.0
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Importar componentes do filtro OAB
from src import (
    OABFilter,
    ResultExporter,
    ParallelProcessor,
)


def main():
    """Entry point do exemplo."""

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    print("\n" + "=" * 70)
    print("FILTRO OAB PROFISSIONAL - Exemplo de Uso Completo")
    print("=" * 70)

    # Verificar argumentos
    if len(sys.argv) < 2:
        print("\nUso: python exemplo_filtro_oab.py <dir_com_pdfs>")
        print("\nExemplo:")
        print("  python exemplo_filtro_oab.py ~/Downloads/cadernos_djen")
        sys.exit(1)

    pdf_dir = Path(sys.argv[1])

    if not pdf_dir.exists():
        print(f"\n❌ Erro: Diretório não encontrado: {pdf_dir}")
        sys.exit(1)

    # Listar PDFs
    pdf_paths = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_paths:
        print(f"\n❌ Erro: Nenhum PDF encontrado em {pdf_dir}")
        sys.exit(1)

    print(f"\n✓ Encontrados {len(pdf_paths)} PDFs em {pdf_dir}")

    # OABs de interesse (CUSTOMIZE AQUI)
    target_oabs = [
        ('123456', 'SP'),  # Exemplo 1
        ('789012', 'RJ'),  # Exemplo 2
        # Adicione suas OABs aqui
    ]

    print(f"\n✓ Buscando {len(target_oabs)} OABs:")
    for num, uf in target_oabs:
        print(f"  - {num}/{uf}")

    # PASSO 1: Criar filtro OAB
    print("\n" + "-" * 70)
    print("PASSO 1: Inicializando Filtro OAB")
    print("-" * 70)

    cache_dir = pdf_dir / ".cache" / "oab_filter"
    cache_dir.mkdir(parents=True, exist_ok=True)

    oab_filter = OABFilter(
        cache_dir=cache_dir,
        enable_ocr=False,  # Desabilitar OCR (lento)
        max_age_days=30,  # Cache válido por 30 dias
        compress_cache=True  # Comprimir cache para economizar espaço
    )

    print(f"✓ Cache configurado em: {cache_dir}")

    # PASSO 2: Executar filtro
    print("\n" + "-" * 70)
    print("PASSO 2: Processando PDFs")
    print("-" * 70)

    # Opção A: Processamento sequencial (mais simples)
    if len(pdf_paths) <= 5:
        print("\nProcessamento SEQUENCIAL (poucos PDFs)...\n")

        matches = oab_filter.filter_by_oabs(
            pdf_paths=pdf_paths,
            target_oabs=target_oabs,
            min_score=0.5,  # Score mínimo 0.5
            use_cache=True,
            sort_by_score=True
        )

    # Opção B: Processamento paralelo (para muitos PDFs)
    else:
        print(f"\nProcessamento PARALELO ({len(pdf_paths)} PDFs)...\n")

        processor = ParallelProcessor(
            max_workers=4,  # 4 processos paralelos
            show_progress=True
        )

        matches, results = processor.process_batch(
            pdf_paths=pdf_paths,
            target_oabs=target_oabs,
            filter_func=oab_filter.filter_single_pdf,
            min_score=0.5,
            use_cache=True
        )

        # Exibir estatísticas de processamento
        stats = processor.get_processing_stats(results)
        print(f"\n📊 Estatísticas de Processamento:")
        print(f"   PDFs processados: {stats['successful']}/{stats['total_pdfs']}")
        print(f"   Taxa de sucesso: {stats['success_rate']:.1%}")
        print(f"   Tempo total: {stats['total_processing_time_seconds']:.1f}s")
        print(f"   Throughput: {stats['throughput_pdfs_per_second']:.1f} PDFs/s")

    # PASSO 3: Exibir resultados
    print("\n" + "-" * 70)
    print("PASSO 3: Resultados")
    print("-" * 70)

    if not matches:
        print("\n⚠️  Nenhuma publicação relevante encontrada.")
        print("\nSugestões:")
        print("  - Verifique se as OABs estão corretas")
        print("  - Reduza o min_score (ex: 0.3)")
        print("  - Verifique se os PDFs contêm as OABs buscadas")
        sys.exit(0)

    print(f"\n✅ Encontradas {len(matches)} publicações relevantes!\n")

    # Exibir top 10
    print("Top 10 publicações por score:\n")
    for i, match in enumerate(matches[:10], 1):
        print(f"{i}. [{match.score_relevancia:.2f}] "
              f"{match.tribunal} - {match.data_publicacao} - "
              f"OAB {match.oab_numero}/{match.oab_uf}")
        print(f"   Tipo: {match.tipo_ato or 'N/A'}")
        print(f"   Menções: {match.total_mencoes}")
        if match.requer_revisao_manual:
            print(f"   ⚠️  Requer revisão manual")
        print()

    # PASSO 4: Exportar resultados
    print("\n" + "-" * 70)
    print("PASSO 4: Exportando Resultados")
    print("-" * 70)

    output_dir = pdf_dir / "resultados_oab"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    exporter = ResultExporter(
        group_by_tribunal=True,
        group_by_oab=True
    )

    # JSON (completo, estruturado)
    json_file = output_dir / f"results_{timestamp}.json"
    exporter.export_json(matches, json_file)
    print(f"✓ JSON: {json_file}")

    # Markdown (leitura humana)
    md_file = output_dir / f"results_{timestamp}.md"
    exporter.export_markdown(matches, md_file, include_toc=True)
    print(f"✓ Markdown: {md_file}")

    # TXT (simples)
    txt_file = output_dir / f"results_{timestamp}.txt"
    exporter.export_txt(matches, txt_file, simple_format=False)
    print(f"✓ TXT: {txt_file}")

    # HTML (visualização)
    html_file = output_dir / f"results_{timestamp}.html"
    exporter.export_html(matches, html_file, include_stats=True)
    print(f"✓ HTML: {html_file}")

    # Excel (opcional)
    try:
        xlsx_file = output_dir / f"results_{timestamp}.xlsx"
        exporter.export_excel(matches, xlsx_file, include_context=True)
        print(f"✓ Excel: {xlsx_file}")
    except ImportError:
        print("⚠️  Excel não exportado (openpyxl não instalado)")

    # PASSO 5: Estatísticas de cache
    print("\n" + "-" * 70)
    print("PASSO 5: Estatísticas de Cache")
    print("-" * 70)

    cache_stats = oab_filter.get_cache_stats()
    print(f"\n{cache_stats}")

    # Resumo final
    print("\n" + "=" * 70)
    print("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO")
    print("=" * 70)
    print(f"\n📂 Resultados exportados em: {output_dir}")
    print(f"📊 Total de publicações: {len(matches)}")
    print(f"🏛️  Tribunais: {len(set(m.tribunal for m in matches))}")
    print(f"⚖️  OABs encontradas: {len(set((m.oab_numero, m.oab_uf) for m in matches))}")

    # Distribuição por tribunal
    print("\n📈 Distribuição por Tribunal:")
    from collections import Counter
    tribunal_counts = Counter(m.tribunal for m in matches)
    for tribunal, count in tribunal_counts.most_common(10):
        print(f"   {tribunal}: {count}")

    # Distribuição por OAB
    print("\n📈 Distribuição por OAB:")
    oab_counts = Counter((m.oab_numero, m.oab_uf) for m in matches)
    for (num, uf), count in oab_counts.most_common(10):
        print(f"   {num}/{uf}: {count}")

    print("\n💡 Dica: Abra o arquivo HTML para visualização interativa!")
    print(f"   firefox {html_file}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
