#!/usr/bin/env python3
"""
Mostra TODAS as OABs reais encontradas em uma amostra
Para validar formato e lógica de parsing
"""
import requests
import json
import zipfile
import io
from collections import Counter

def extract_all_oabs(tribunal: str = "TJSP", data: str = "2025-11-14", max_show: int = 50):
    """Extrai e mostra todas as OABs de um caderno"""
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/E"

    print("=" * 80)
    print(f"EXTRAÇÃO DE OABs REAIS: {tribunal} - {data}")
    print("=" * 80)

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    api_data = resp.json()

    # Baixar ZIP
    s3_url = api_data['url']
    s3_resp = requests.get(s3_url, timeout=30)
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

    print(f"\n📊 Total de publicações: {len(all_items)}")

    # Extrair TODAS as OABs
    all_oabs = []
    oabs_raw_format = []
    oab_counter = Counter()

    for item in all_items:
        advs = item.get('destinatarioadvogados', [])
        for adv_entry in advs:
            adv = adv_entry.get('advogado', {})
            numero = adv.get('numero_oab', '')
            uf = adv.get('uf_oab', '')

            if numero and uf:
                # Raw format
                raw = f"{numero}/{uf}"
                oabs_raw_format.append(raw)

                # Normalized (sem sufixo N)
                numero_norm = numero.replace('N', '').strip()
                normalized = f"{numero_norm}/{uf}"
                all_oabs.append(normalized)
                oab_counter[normalized] += 1

    print(f"📝 Total de advogados com OAB: {len(all_oabs)}")
    print(f"🔢 OABs únicas (normalizadas): {len(oab_counter)}")

    # Mostrar amostra de formatos RAW
    print(f"\n📋 AMOSTRA DE FORMATOS RAW (primeiras {max_show}):")
    for i, oab_raw in enumerate(oabs_raw_format[:max_show], 1):
        print(f"  {i:3d}. {oab_raw}")

    # Mostrar OABs mais frequentes
    print(f"\n🔥 TOP 20 OABs MAIS FREQUENTES:")
    for oab, count in oab_counter.most_common(20):
        print(f"  {oab:20s} → {count:3d} vezes")

    # Buscar especificamente OABs próximas de 129021
    print(f"\n🎯 OABs PRÓXIMAS DE 129021/SP (±1000):")
    target_range = range(128021, 130021)
    found_nearby = []

    for oab in oab_counter.keys():
        if '/SP' in oab:
            numero_str = oab.split('/')[0]
            try:
                numero_int = int(numero_str)
                if numero_int in target_range:
                    found_nearby.append((oab, oab_counter[oab]))
            except ValueError:
                pass

    if found_nearby:
        found_nearby.sort()
        for oab, count in found_nearby:
            print(f"  {oab:20s} → {count:3d} vezes")
    else:
        print("  Nenhuma OAB nessa faixa encontrada")

    # Buscar exatamente 129021
    print(f"\n🔍 BUSCA EXATA:")
    targets = ['129021/SP', '120210/SP']
    for target in targets:
        if target in oab_counter:
            print(f"  ✅ {target} encontrada {oab_counter[target]} vezes")
        else:
            print(f"  ❌ {target} NÃO encontrada")

    # Verificar se há variações com sufixo N
    print(f"\n🔤 VERIFICAÇÃO DE SUFIXO N:")
    for target in ['129021', '120210']:
        variants = [
            f"{target}/SP",
            f"{target}N/SP",
        ]
        for variant in variants:
            # Buscar no raw format
            count_raw = oabs_raw_format.count(variant)
            if count_raw > 0:
                print(f"  ✅ '{variant}' encontrada {count_raw} vezes (formato raw)")

    # Mostrar estrutura completa de UM advogado para debug
    print(f"\n🔬 ESTRUTURA COMPLETA DE 1 ADVOGADO (para debug):")
    for item in all_items[:50]:  # Primeiros 50 items
        advs = item.get('destinatarioadvogados', [])
        if advs:
            print(json.dumps(advs[0], indent=2, ensure_ascii=False))
            break


if __name__ == "__main__":
    try:
        extract_all_oabs()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
