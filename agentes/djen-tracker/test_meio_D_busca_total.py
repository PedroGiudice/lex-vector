#!/usr/bin/env python3
"""
TESTE DEFINITIVO: Busca "129021" em TODOS os campos
Meios: D (Diário) e E (Eletrônico)
Últimos 7 dias úteis
"""
import requests
import json
import zipfile
import io
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def buscar_pattern_completo(tribunal: str, data: str, meio: str, pattern: str):
    """Busca pattern em QUALQUER LUGAR do JSON"""
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/{meio}"

    try:
        resp = requests.get(url, timeout=10)

        if resp.status_code == 404:
            return None

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

        # Buscar pattern em TODO o JSON serializado
        matches = []
        for item in all_items:
            item_str = json.dumps(item, ensure_ascii=False)

            if pattern in item_str:
                matches.append({
                    'tribunal': tribunal,
                    'data': data,
                    'meio': meio,
                    'processo': item.get('numeroprocessocommascara', 'N/A'),
                    'tipo': item.get('tipoComunicacao', 'N/A'),
                    'orgao': item.get('nomeOrgao', 'N/A'),
                    'item_completo': item  # Guardar item completo para análise
                })

        return {
            'tribunal': tribunal,
            'data': data,
            'meio': meio,
            'total': len(all_items),
            'matches': matches
        }

    except Exception as e:
        return None


def main():
    """Busca definitiva"""
    print("="*80)
    print("BUSCA DEFINITIVA: '129021' em AMBOS os meios (D + E)")
    print("="*80)

    tribunal = "TJSP"
    pattern = "129021"
    meios = ['D', 'E']  # DIÁRIO e ELETRÔNICO

    # Últimos 7 dias úteis
    hoje = datetime.now()
    datas = []
    for i in range(1, 15):
        data = hoje - timedelta(days=i)
        if data.weekday() < 5:
            datas.append(data.strftime('%Y-%m-%d'))
        if len(datas) >= 7:
            break

    print(f"\n🏛️  Tribunal: {tribunal}")
    print(f"🔍 Pattern: '{pattern}'")
    print(f"📅 Período: {datas[0]} até {datas[-1]} (7 dias úteis)")
    print(f"📡 Meios: {meios} (Diário + Eletrônico)")
    print(f"📊 Total de buscas: {len(datas) * len(meios)}")

    print("\n⏳ INICIANDO BUSCA...\n")

    all_matches = []
    completed = 0
    total_pubs = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for data in datas:
            for meio in meios:
                future = executor.submit(buscar_pattern_completo, tribunal, data, meio, pattern)
                futures.append((future, data, meio))

        for future, data, meio in futures:
            completed += 1
            resultado = future.result()

            # Progress
            print(f"   [{completed}/{len(futures)}] {data} meio {meio}...", end=' ')

            if resultado:
                total_pubs += resultado['total']
                print(f"{resultado['total']} pubs", end='')

                if resultado['matches']:
                    all_matches.extend(resultado['matches'])
                    print(f" → 🎉 {len(resultado['matches'])} MATCH(ES)!")
                else:
                    print()
            else:
                print("sem dados")

    elapsed = time.time() - start_time

    # Resultados
    print("\n" + "="*80)
    print("RESULTADOS")
    print("="*80)
    print(f"Tempo: {elapsed:.1f}s")
    print(f"Publicações processadas: {total_pubs:,}")
    print(f"Matches encontrados: {len(all_matches)}")
    print("="*80)

    if all_matches:
        print(f"\n✅ PATTERN '{pattern}' ENCONTRADO!\n")

        for i, match in enumerate(all_matches, 1):
            print(f"{i}. {match['data']} - Meio {match['meio']}")
            print(f"   Processo: {match['processo']}")
            print(f"   Tipo: {match['tipo']}")
            print(f"   Órgão: {match['orgao']}")

            # Encontrar ONDE no JSON está o pattern
            item = match['item_completo']

            # Verificar em destinatarioadvogados
            advs = item.get('destinatarioadvogados', [])
            for adv_entry in advs:
                adv = adv_entry.get('advogado', {})
                numero = adv.get('numero_oab', '')
                if pattern in numero:
                    print(f"   📍 OAB em destinatarioadvogados: {numero}/{adv.get('uf_oab')}")
                    print(f"      Advogado: {adv.get('nome')}")

            # Verificar no texto
            texto = item.get('texto', '')
            if pattern in texto:
                # Encontrar contexto
                idx = texto.find(pattern)
                context_start = max(0, idx - 50)
                context_end = min(len(texto), idx + 50)
                print(f"   📍 No campo 'texto': ...{texto[context_start:context_end]}...")

            # Verificar em outros campos
            for key, value in item.items():
                if key not in ['destinatarioadvogados', 'texto']:
                    value_str = json.dumps(value, ensure_ascii=False)
                    if pattern in value_str:
                        print(f"   📍 No campo '{key}': {value_str[:100]}...")

            print()

        # Salvar
        output = f"matches_129021_{int(time.time())}.json"
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(all_matches, f, indent=2, ensure_ascii=False)
        print(f"💾 Salvo em: {output}")

    else:
        print(f"\n❌ PATTERN '{pattern}' NÃO ENCONTRADO")
        print(f"\n   Período: {datas[0]} até {datas[-1]}")
        print(f"   Meios: {meios}")
        print(f"   Publicações: {total_pubs:,}")
        print("\n💡 Se você TEM CERTEZA que existe:")
        print("   1. Pode estar em data ANTERIOR a 7 dias")
        print("   2. Pode estar em OUTRO TRIBUNAL")
        print("   3. OAB pode ter FORMATO DIFERENTE (ex: sem o número completo)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido")
    except Exception as e:
        print(f"\n\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
