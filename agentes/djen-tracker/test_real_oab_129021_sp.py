#!/usr/bin/env python3
"""
Teste REAL com OAB 129021/SP - Busca nos últimos 7 dias

Executa busca real na API DJEN e filtra por OAB 129021/SP ou 120210/SP.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from src import OABFilter, ContinuousDownloader
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Executa teste real end-to-end"""
    print("=" * 80)
    print("TESTE REAL: Busca OAB 129021/SP e 120210/SP nos últimos 7 dias")
    print("=" * 80)

    # Config
    config_file = Path(__file__).parent / "config.json"
    with open(config_file) as f:
        config = json.load(f)

    # Diretórios temporários para teste
    temp_root = Path(__file__).parent / "temp_test_real"
    temp_root.mkdir(exist_ok=True)

    config['paths']['data_root'] = str(temp_root)
    config['tribunais']['modo'] = 'prioritarios'  # Só tribunais importantes para teste rápido

    print(f"\nDiretório temporário: {temp_root}")
    print(f"Tribunais: {config['tribunais']['prioritarios'][:5]}...")

    # Inicializar downloader
    downloader = ContinuousDownloader(config)

    # Datas para testar (últimos 7 dias, só dias úteis)
    hoje = datetime.now()
    datas = []
    for i in range(1, 15):  # 14 dias para pegar pelo menos 7 úteis
        data = hoje - timedelta(days=i)
        if data.weekday() < 5:  # Segunda a sexta
            datas.append(data.strftime('%Y-%m-%d'))
        if len(datas) >= 7:
            break

    print(f"\nDatas a testar: {datas[0]} até {datas[-1]} ({len(datas)} dias úteis)")

    # Executar downloads
    print("\n" + "=" * 80)
    print("FASE 1: Download de cadernos")
    print("=" * 80)

    total_sucessos = 0
    for data in datas:
        print(f"\n🔍 Baixando cadernos de {data}...")
        resultado = downloader.run_once(data=data, parallel=False)  # Sequencial para teste
        total_sucessos += resultado['sucessos']

        print(f"   Sucessos: {resultado['sucessos']} | Falhas: {resultado['falhas']}")

        if total_sucessos > 0:
            print(f"   ✅ {total_sucessos} caderno(s) baixado(s) - prosseguindo para filtragem")
            break

    if total_sucessos == 0:
        print("\n⚠️  Nenhum caderno baixado (404 em todas as datas)")
        print("   Isso pode indicar:")
        print("   1. Restrição geográfica (IP não-brasileiro)")
        print("   2. Sem publicações no período testado")
        print("   3. API temporariamente indisponível")
        print("\n📝 Para teste completo, executar de IP brasileiro ou VPN")
        sys.exit(0)

    # Filtrar por OAB
    print("\n" + "=" * 80)
    print("FASE 2: Filtro por OAB 129021/SP e 120210/SP")
    print("=" * 80)

    cache_dir = temp_root / "cache"
    oab_filter = OABFilter(cache_dir=cache_dir)

    # Encontrar PDFs baixados
    cadernos_dir = temp_root / "cadernos"
    pdfs = list(cadernos_dir.rglob("*.pdf"))

    print(f"\n📄 PDFs encontrados: {len(pdfs)}")

    if not pdfs:
        print("⚠️  Nenhum PDF para processar")
        sys.exit(0)

    # Filtrar por OABs alvo
    target_oabs = [
        ("129021", "SP"),
        ("120210", "SP")
    ]

    print(f"\n🎯 OABs alvo: {' e '.join([f'{num}/{uf}' for num, uf in target_oabs])}")
    print(f"\n⏳ Processando {len(pdfs)} PDF(s)...")

    matches = oab_filter.filter_by_oabs(
        pdf_paths=pdfs,
        target_oabs=target_oabs,
        min_score=0.3
    )

    # Resultados
    print("\n" + "=" * 80)
    print("RESULTADOS")
    print("=" * 80)

    if matches:
        print(f"\n✅ {len(matches)} publicação(ões) encontrada(s)!\n")

        for i, match in enumerate(matches, 1):
            print(f"{i}. OAB {match.oab_numero}/{match.oab_uf}")
            print(f"   Tribunal: {match.tribunal}")
            print(f"   Data: {match.data_publicacao}")
            print(f"   Score: {match.score_relevancia:.2f}")
            print(f"   Tipo: {match.tipo_ato or 'N/A'}")
            print(f"   Contexto: {match.texto_contexto[:80]}...")
            print()

        # Exportar resultados
        output_json = temp_root / f"matches_oab_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        from src.result_exporter import ResultExporter
        exporter = ResultExporter()
        exporter.export_json(matches, output_json)

        print(f"📊 Resultados exportados: {output_json}")

    else:
        print("\n❌ Nenhuma publicação encontrada")
        print(f"   OABs buscadas: 129021/SP, 120210/SP")
        print(f"   PDFs processados: {len(pdfs)}")
        print(f"   Datas: {datas[0]} até {datas[-1]}")
        print("\n💡 Possíveis razões:")
        print("   1. OABs não mencionadas nos cadernos baixados")
        print("   2. Formato de OAB diferente no texto")
        print("   3. Período sem publicações para essas OABs")

    print("\n" + "=" * 80)
    print("TESTE CONCLUÍDO")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
