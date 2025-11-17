#!/usr/bin/env python3
"""
Busca OAB 129021/SP em TODOS os 65 tribunais
Data: últimos 7 dias úteis
"""
import requests
import json
import zipfile
import io
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Todos os 65 tribunais
ALL_TRIBUNALS = [
    # Tribunais Superiores
    "STF", "STJ", "TST", "TSE", "STM",
    # TRFs
    "TRF1", "TRF2", "TRF3", "TRF4", "TRF5", "TRF6",
    # TJsEstado
    "TJSP", "TJRJ", "TJMG", "TJRS", "TJPR", "TJSC", "TJDF", "TJBA", "TJCE",
    "TJPE", "TJES", "TJGO", "TJPB", "TJMS", "TJMT", "TJRN", "TJAL", "TJSE",
    "TJPI", "TJRO", "TJAM", "TJAC", "TJAP", "TJMA", "TJPA", "TJTO", "TJRR",
    # TRTs
    "TRT1", "TRT2", "TRT3", "TRT4", "TRT5", "TRT6", "TRT7", "TRT8", "TRT9",
    "TRT10", "TRT11", "TRT12", "TRT13", "TRT14", "TRT15", "TRT16", "TRT17",
    "TRT18", "TRT19", "TRT20", "TRT21", "TRT22", "TRT23", "TRT24",
]

def buscar_oab_tribunal_data(tribunal: str, data: str, target_oabs: list) -> dict:
    """Busca OAB em um tribunal/data específicos"""
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/E"

    try:
        resp = requests.get(url, timeout=10)

        if resp.status_code == 404:
            return {'tribunal': tribunal, 'data': data, 'status': 'sem_publicacoes', 'matches': []}

        resp.raise_for_status()
        api_data = resp.json()

        if api_data.get('status') != 'Processado':
            return {'tribunal': tribunal, 'data': data, 'status': 'nao_processado', 'matches': []}

        # Baixar ZIP
        s3_url = api_data['url']
        s3_resp = requests.get(s3_url, timeout=20)
        s3_resp.raise_for_status()

        # Extrair JSONs
        zip_data = io.BytesIO(s3_resp.content)
        all_items = []

        with zipfile.ZipFile(zip_data) as zf:
            for filename in zf.namelist():
                if filename.endswith('.json'):
                    content = zf.read(filename).decode('utf-8')
                    parsed = json.loads(content)
                    all_items.extend(parsed.get('items', []))

        # Buscar OABs
        matches = []
        for item in all_items:
            advs = item.get('destinatarioadvogados', [])
            for adv_entry in advs:
                adv = adv_entry.get('advogado', {})
                numero_raw = adv.get('numero_oab', '')
                uf = adv.get('uf_oab', '')

                # Normalizar
                numero = numero_raw.replace('N', '').strip()

                # Verificar match
                for target_num, target_uf in target_oabs:
                    if numero == target_num and uf == target_uf:
                        matches.append({
                            'tribunal': tribunal,
                            'data': data,
                            'processo': item.get('numeroprocessocommascara', 'N/A'),
                            'tipo': item.get('tipoComunicacao', 'N/A'),
                            'orgao': item.get('nomeOrgao', 'N/A'),
                            'advogado': adv.get('nome', 'N/A'),
                            'oab': f"{numero}/{uf}"
                        })
                        break

        return {
            'tribunal': tribunal,
            'data': data,
            'status': 'ok',
            'total': len(all_items),
            'matches': matches
        }

    except Exception as e:
        return {
            'tribunal': tribunal,
            'data': data,
            'status': f'erro: {str(e)[:30]}',
            'matches': []
        }


def main():
    """Busca massiva em todos os tribunais"""
    print("=" * 80)
    print("BUSCA MASSIVA: OAB 129021/SP e 120210/SP em TODOS os 65 tribunais")
    print("=" * 80)

    # OABs alvo
    target_oabs = [
        ("129021", "SP"),
        ("120210", "SP")
    ]

    # Últimos 7 dias úteis
    hoje = datetime.now()
    datas = []
    for i in range(1, 15):
        data = hoje - timedelta(days=i)
        if data.weekday() < 5:  # Seg-Sex
            datas.append(data.strftime('%Y-%m-%d'))
        if len(datas) >= 7:
            break

    print(f"\n🎯 OABs: {', '.join([f'{n}/{u}' for n, u in target_oabs])}")
    print(f"🏛️  Tribunais: {len(ALL_TRIBUNALS)}")
    print(f"📅 Datas: {len(datas)} ({datas[0]} até {datas[-1]})")
    print(f"📊 Total de buscas: {len(ALL_TRIBUNALS) * len(datas)}")

    print("\n⏳ INICIANDO BUSCA PARALELA...\n")

    # Executar em paralelo
    all_matches = []
    completed = 0
    total_pubs = 0
    tribunais_com_publicacoes = set()

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for tribunal in ALL_TRIBUNALS:
            for data in datas:
                future = executor.submit(buscar_oab_tribunal_data, tribunal, data, target_oabs)
                futures.append(future)

        for future in as_completed(futures):
            resultado = future.result()
            completed += 1

            # Progress
            if completed % 50 == 0 or completed == len(futures):
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (len(futures) - completed) / rate if rate > 0 else 0
                print(f"   Progresso: {completed}/{len(futures)} ({completed*100//len(futures)}%) | "
                      f"Taxa: {rate:.1f} buscas/s | ETA: {eta/60:.1f}min")

            # Processar resultado
            if resultado['status'] == 'ok':
                total_pubs += resultado['total']
                tribunais_com_publicacoes.add(resultado['tribunal'])

                if resultado['matches']:
                    all_matches.extend(resultado['matches'])
                    print(f"\n   🎉 MATCH! {resultado['tribunal']} - {resultado['data']}: "
                          f"{len(resultado['matches'])} publicação(ões)")

    # Resultados finais
    elapsed_total = time.time() - start_time

    print("\n" + "=" * 80)
    print("RESULTADOS FINAIS")
    print("=" * 80)
    print(f"Tempo total: {elapsed_total/60:.2f} minutos")
    print(f"Buscas realizadas: {completed}")
    print(f"Tribunais com publicações: {len(tribunais_com_publicacoes)}")
    print(f"Publicações processadas: {total_pubs:,}")
    print(f"Matches encontrados: {len(all_matches)}")
    print("=" * 80)

    if all_matches:
        print(f"\n✅ OAB ENCONTRADA! Detalhes:\n")
        for i, match in enumerate(all_matches, 1):
            print(f"{i}. {match['tribunal']} - {match['data']}")
            print(f"   Processo: {match['processo']}")
            print(f"   Tipo: {match['tipo']}")
            print(f"   Órgão: {match['orgao']}")
            print(f"   Advogado: {match['advogado']}")
            print(f"   OAB: {match['oab']}")
            print()

        # Salvar
        output = f"oab_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(all_matches, f, indent=2, ensure_ascii=False)
        print(f"💾 Resultados salvos: {output}")

    else:
        print(f"\n❌ NENHUMA PUBLICAÇÃO ENCONTRADA")
        print(f"\n📊 Tribunais verificados: {ALL_TRIBUNALS[:10]}... (+{len(ALL_TRIBUNALS)-10})")
        print(f"📊 Tribunais com publicações: {sorted(list(tribunais_com_publicacoes))}")
        print(f"📊 Total de publicações processadas: {total_pubs:,}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Busca interrompida")
    except Exception as e:
        print(f"\n\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
