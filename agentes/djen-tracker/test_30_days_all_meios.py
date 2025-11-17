#!/usr/bin/env python3
"""
BUSCA DEFINITIVA: OAB 129021/SP
- 30 dias úteis
- Todos os meios (E, I, R)
- Tribunal TJSP
"""
import requests
import json
import zipfile
import io
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def buscar_oab(tribunal: str, data: str, meio: str, target_num: str, target_uf: str):
    """Busca OAB em tribunal/data/meio específicos"""
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/{meio}"

    try:
        resp = requests.get(url, timeout=10)

        if resp.status_code == 404:
            return None  # Sem dados

        resp.raise_for_status()
        api_data = resp.json()

        if api_data.get('status') != 'Processado':
            return None

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

        # Buscar OAB (flexível - COMEÇA com target_num)
        matches = []
        for item in all_items:
            advs = item.get('destinatarioadvogados', [])
            for adv_entry in advs:
                adv = adv_entry.get('advogado', {})
                numero_raw = adv.get('numero_oab', '')
                uf = adv.get('uf_oab', '')

                # BUSCA FLEXÍVEL - começa com target_num
                if numero_raw.startswith(target_num) and uf == target_uf:
                    matches.append({
                        'tribunal': tribunal,
                        'data': data,
                        'meio': meio,
                        'processo': item.get('numeroprocessocommascara', 'N/A'),
                        'tipo': item.get('tipoComunicacao', 'N/A'),
                        'orgao': item.get('nomeOrgao', 'N/A'),
                        'advogado': adv.get('nome', 'N/A'),
                        'oab': f"{numero_raw}/{uf}"
                    })
                    break  # Só 1 match por publicação

        return {
            'tribunal': tribunal,
            'data': data,
            'meio': meio,
            'total': len(all_items),
            'matches': matches
        }

    except Exception:
        return None


def main():
    """Busca definitiva"""
    print("=" * 80)
    print("BUSCA DEFINITIVA: OAB 129021/SP - 30 dias + todos os meios")
    print("=" * 80)

    tribunal = "TJSP"
    target_num = "129021"
    target_uf = "SP"
    meios = ['E', 'I', 'R']  # Eletrônico, Intimação, Outros

    # Últimos 30 dias úteis
    hoje = datetime.now()
    datas = []
    for i in range(1, 60):  # 60 dias para pegar 30 úteis
        data = hoje - timedelta(days=i)
        if data.weekday() < 5:  # Seg-Sex
            datas.append(data.strftime('%Y-%m-%d'))
        if len(datas) >= 30:
            break

    print(f"\n🏛️  Tribunal: {tribunal}")
    print(f"🎯 OAB: {target_num}/{target_uf}")
    print(f"📅 Período: {datas[0]} até {datas[-1]} (30 dias úteis)")
    print(f"📡 Meios: {meios}")
    print(f"📊 Total de buscas: {len(datas) * len(meios)}")

    print("\n⏳ INICIANDO BUSCA PARALELA...\n")

    all_matches = []
    completed = 0
    total_pubs = 0

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for data in datas:
            for meio in meios:
                future = executor.submit(buscar_oab, tribunal, data, meio, target_num, target_uf)
                futures.append((future, data, meio))

        for future, data, meio in futures:
            completed += 1
            resultado = future.result()

            # Progress
            if completed % 10 == 0 or completed == len(futures):
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (len(futures) - completed) / rate if rate > 0 else 0
                print(f"   {completed}/{len(futures)} ({completed*100//len(futures)}%) | "
                      f"{rate:.1f} buscas/s | ETA: {eta/60:.1f}min", end='\r')

            # Processar
            if resultado:
                total_pubs += resultado['total']

                if resultado['matches']:
                    all_matches.extend(resultado['matches'])
                    print(f"\n   🎉 MATCH! {resultado['data']} meio {resultado['meio']}: "
                          f"{len(resultado['matches'])} publicação(ões)       ")

    # Resultados finais
    elapsed_total = time.time() - start_time

    print("\n\n" + "=" * 80)
    print("RESULTADOS FINAIS")
    print("=" * 80)
    print(f"Tempo: {elapsed_total/60:.2f} min")
    print(f"Publicações processadas: {total_pubs:,}")
    print(f"Matches: {len(all_matches)}")
    print("=" * 80)

    if all_matches:
        print(f"\n✅ OAB {target_num}/{target_uf} ENCONTRADA!\n")
        for i, match in enumerate(all_matches, 1):
            print(f"{i}. {match['data']} - Meio {match['meio']}")
            print(f"   Processo: {match['processo']}")
            print(f"   Tipo: {match['tipo']}")
            print(f"   Órgão: {match['orgao']}")
            print(f"   Advogado: {match['advogado']}")
            print(f"   OAB: {match['oab']}")
            print()

        # Salvar
        output = f"oab_129021_sp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(all_matches, f, indent=2, ensure_ascii=False)
        print(f"💾 Salvo em: {output}")

    else:
        print(f"\n❌ OAB {target_num}/{target_uf} NÃO encontrada")
        print(f"\n   Período: {datas[0]} até {datas[-1]}")
        print(f"   Meios: {meios}")
        print(f"   Publicações: {total_pubs:,}")
        print("\n💡 Se não encontrou, a publicação pode estar:")
        print("   - Em data anterior a 30 dias")
        print("   - Em outro tribunal (não TJSP)")
        print("   - Com número de OAB ligeiramente diferente")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido")
    except Exception as e:
        print(f"\n\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
