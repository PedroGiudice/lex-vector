#!/usr/bin/env python3
"""
Procura o padrão '129021' em TODOS os campos do JSON
Para verificar se a OAB está em outro lugar além de destinatarioadvogados
"""
import requests
import json
import zipfile
import io
import re

def search_oab_in_all_fields(tribunal: str = "TJSP", data: str = "2025-11-14"):
    """Busca padrão OAB em todos os campos"""
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/E"

    print("=" * 80)
    print(f"BUSCA DE '129021' EM TODOS OS CAMPOS: {tribunal} - {data}")
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

    # Padrões a buscar
    patterns = [
        '129021',
        '120210',
    ]

    # Buscar em TODO o JSON serializado
    print(f"\n🔍 Buscando padrões: {patterns}")
    print(f"\nResultados:\n")

    matches_found = []

    for i, item in enumerate(all_items, 1):
        # Serializar item completo
        item_str = json.dumps(item, ensure_ascii=False)

        # Buscar cada padrão
        for pattern in patterns:
            if pattern in item_str:
                matches_found.append({
                    'index': i,
                    'pattern': pattern,
                    'item': item
                })

                print(f"✅ MATCH #{len(matches_found)}: Padrão '{pattern}' encontrado na publicação {i}")
                print(f"   Processo: {item.get('numeroprocessocommascara', 'N/A')}")
                print(f"   Tipo: {item.get('tipoComunicacao', 'N/A')}")

                # Mostrar ONDE no JSON está o padrão
                for key, value in item.items():
                    value_str = json.dumps(value, ensure_ascii=False)
                    if pattern in value_str:
                        print(f"   📍 Campo '{key}' contém '{pattern}'")
                        print(f"      Valor: {value_str[:200]}...")
                print()

    print("=" * 80)
    print(f"TOTAL: {len(matches_found)} publicações com os padrões buscados")
    print("=" * 80)

    if matches_found:
        print(f"\n📋 DETALHES COMPLETOS:")
        for match in matches_found:
            print(f"\n{'=' * 80}")
            print(json.dumps(match['item'], indent=2, ensure_ascii=False))
            print(f"{'=' * 80}")
    else:
        print(f"\n❌ Padrões {patterns} NÃO encontrados em nenhum campo")

        # Mostrar estrutura completa de UMA publicação para referência
        print(f"\n📋 ESTRUTURA COMPLETA DE 1 PUBLICAÇÃO (para referência):")
        if all_items:
            print(json.dumps(all_items[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        search_oab_in_all_fields()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
