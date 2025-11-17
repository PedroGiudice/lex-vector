#!/usr/bin/env python3
"""
Verifica se os filtros do /api/v1/comunicacao realmente funcionam
Analisa TODOS os 100 items retornados
"""
import requests
import json

def check_comunicacao_filters():
    """Verifica se filtros funcionam"""
    url = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"

    print("="*80)
    print("TESTE DE FILTROS: /api/v1/comunicacao")
    print("="*80)

    # Teste 1: Buscar OAB 129021
    print("\n🧪 TESTE 1: numero_oab=129021")
    resp1 = requests.get(url, params={"numero_oab": "129021"}, timeout=20)
    data1 = resp1.json()

    print(f"Count: {data1.get('count')}")
    print(f"Items retornados: {len(data1.get('items', []))}")

    # Verificar se ALGUM item tem OAB 129021
    found_129021 = False
    oabs_found = set()

    for item in data1.get('items', []):
        advs = item.get('destinatarioadvogados', [])
        for adv_entry in advs:
            adv = adv_entry.get('advogado', {})
            numero = adv.get('numero_oab', '').replace('N', '').strip()
            uf = adv.get('uf_oab', '')
            oabs_found.add(f"{numero}/{uf}")

            if numero.startswith('129021'):
                found_129021 = True
                print(f"\n✅ ENCONTRADA! OAB {numero}/{uf}")
                print(f"   Processo: {item.get('numeroprocessocommascara')}")
                print(f"   Data: {item.get('data_disponibilizacao')}")
                print(f"   Tribunal: {item.get('siglaTribunal')}")

    if not found_129021:
        print(f"\n❌ OAB 129021 NÃO encontrada nos {len(data1.get('items', []))} items")
        print(f"\n📋 OABs únicas encontradas (primeiras 20):")
        for oab in sorted(list(oabs_found))[:20]:
            print(f"  {oab}")

    # Teste 2: TJSP + data_disponibilizacao=2025-11-14
    print(f"\n\n🧪 TESTE 2: siglaTribunal=TJSP + data_disponibilizacao=2025-11-14")
    resp2 = requests.get(url, params={
        "siglaTribunal": "TJSP",
        "data_disponibilizacao": "2025-11-14"
    }, timeout=20)
    data2 = resp2.json()

    tribunais = set()
    datas = set()

    for item in data2.get('items', []):
        tribunais.add(item.get('siglaTribunal'))
        datas.add(item.get('data_disponibilizacao'))

    print(f"Items: {len(data2.get('items', []))}")
    print(f"Tribunais únicos: {sorted(tribunais)}")
    print(f"Datas únicas: {sorted(datas)}")

    if len(tribunais) == 1 and 'TJSP' in tribunais:
        print("✅ Filtro siglaTribunal FUNCIONA")
    else:
        print(f"⚠️  Filtro siglaTribunal NÃO funciona (esperava só TJSP, got {tribunais})")

    if len(datas) == 1 and '2025-11-14' in datas:
        print("✅ Filtro data_disponibilizacao FUNCIONA")
    else:
        print(f"⚠️  Filtro data_disponibilizacao NÃO funciona (esperava 2025-11-14, got {datas})")

    # Teste 3: Paginação
    print(f"\n\n🧪 TESTE 3: Paginação (buscar OAB 129021 em múltiplas páginas)")

    found_in_pagination = False
    max_pages = 10  # Verificar 10 páginas = 1000 publicações

    for page in range(1, max_pages + 1):
        print(f"  Página {page}...", end=' ')
        resp = requests.get(url, params={
            "numero_oab": "129021",
            "page": page
        }, timeout=20)

        data = resp.json()

        for item in data.get('items', []):
            advs = item.get('destinatarioadvogados', [])
            for adv_entry in advs:
                adv = adv_entry.get('advogado', {})
                numero = adv.get('numero_oab', '').replace('N', '').strip()
                uf = adv.get('uf_oab', '')

                if numero.startswith('129021') and uf == 'SP':
                    found_in_pagination = True
                    print(f"\n  ✅ ENCONTRADA na página {page}!")
                    print(f"     OAB: {numero}/{uf}")
                    print(f"     Processo: {item.get('numeroprocessocommascara')}")
                    print(f"     Data: {item.get('data_disponibilizacao')}")
                    break
            if found_in_pagination:
                break

        if found_in_pagination:
            break
        else:
            print("not found", end='')

        print()

    if not found_in_pagination:
        print(f"\n❌ OAB 129021/SP NÃO encontrada nas primeiras {max_pages} páginas ({max_pages * 100} publicações)")

    print("\n" + "="*80)
    print("CONCLUSÃO")
    print("="*80)
    print("Os filtros da API podem:")
    print("1. NÃO funcionar (bug da API)")
    print("2. Requerer sintaxe diferente")
    print("3. Estar retornando cache desatualizado")
    print("\n💡 Recomendação: Usar endpoint /api/v1/caderno (que sabemos que funciona)")


if __name__ == "__main__":
    try:
        check_comunicacao_filters()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
