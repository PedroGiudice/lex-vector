#!/usr/bin/env python3
"""
Testa endpoint /api/v1/comunicacao com diferentes parâmetros
para buscar OAB 129021/SP diretamente
"""
import requests
import json
from datetime import datetime, timedelta

def test_comunicacao_endpoint(params: dict):
    """Testa endpoint /api/v1/comunicacao com parâmetros"""
    url = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"

    print(f"\n{'='*80}")
    print(f"Testando: {url}")
    print(f"Params: {json.dumps(params, indent=2)}")
    print(f"{'='*80}")

    try:
        resp = requests.get(url, params=params, timeout=15)

        print(f"Status: HTTP {resp.status_code}")

        if resp.status_code != 200:
            print(f"Response: {resp.text[:500]}")
            return None

        data = resp.json()

        print(f"\n📊 Response structure:")
        print(f"  status: {data.get('status')}")
        print(f"  message: {data.get('message')}")
        print(f"  count: {data.get('count')}")
        print(f"  items length: {len(data.get('items', []))}")

        if data.get('items'):
            print(f"\n📋 First item sample:")
            first_item = data['items'][0]
            print(f"  Processo: {first_item.get('numeroprocessocommascara')}")
            print(f"  Tribunal: {first_item.get('siglaTribunal')}")
            print(f"  Data: {first_item.get('data_disponibilizacao')}")
            print(f"  Tipo: {first_item.get('tipoComunicacao')}")

            # Verificar se tem OABs
            advs = first_item.get('destinatarioadvogados', [])
            if advs:
                print(f"  Advogados: {len(advs)}")
                for adv_entry in advs[:3]:
                    adv = adv_entry.get('advogado', {})
                    print(f"    - {adv.get('numero_oab')}/{adv.get('uf_oab')}")

        return data

    except Exception as e:
        print(f"❌ ERRO: {e}")
        return None


def main():
    """Testa diferentes combinações de parâmetros"""
    print("="*80)
    print("TESTE DO ENDPOINT /api/v1/comunicacao")
    print("="*80)

    hoje = datetime.now()
    data_7_dias_atras = (hoje - timedelta(days=7)).strftime('%Y-%m-%d')
    data_hoje = hoje.strftime('%Y-%m-%d')

    # Lista de combinações a testar
    tests = [
        {
            "name": "Sem parâmetros (baseline)",
            "params": {}
        },
        {
            "name": "Filtro por tribunal TJSP",
            "params": {"siglaTribunal": "TJSP"}
        },
        {
            "name": "Filtro por data",
            "params": {
                "data_disponibilizacao": "2025-11-14"
            }
        },
        {
            "name": "Filtro por OAB 129021",
            "params": {
                "numero_oab": "129021"
            }
        },
        {
            "name": "Filtro por OAB 129021/SP",
            "params": {
                "numero_oab": "129021",
                "uf_oab": "SP"
            }
        },
        {
            "name": "Filtro por OAB com N",
            "params": {
                "numero_oab": "129021N",
                "uf_oab": "SP"
            }
        },
        {
            "name": "TJSP + Data + OAB",
            "params": {
                "siglaTribunal": "TJSP",
                "data_disponibilizacao": "2025-11-14",
                "numero_oab": "129021"
            }
        },
        {
            "name": "Range de datas",
            "params": {
                "data_inicio": data_7_dias_atras,
                "data_fim": data_hoje,
                "numero_oab": "129021"
            }
        },
        {
            "name": "Teste com OAB conhecida (460221)",
            "params": {
                "numero_oab": "460221",
                "uf_oab": "SP"
            }
        },
        {
            "name": "TJSP + 2025-11-14 + OAB 460221",
            "params": {
                "siglaTribunal": "TJSP",
                "data_disponibilizacao": "2025-11-14",
                "numero_oab": "460221"
            }
        },
    ]

    results = []

    for test in tests:
        print(f"\n\n🧪 TESTE: {test['name']}")
        result = test_comunicacao_endpoint(test['params'])

        if result and result.get('count', 0) > 0:
            print(f"✅ SUCESSO: {result.get('count')} comunicações encontradas!")
            results.append({
                'test': test['name'],
                'params': test['params'],
                'count': result.get('count'),
                'works': True
            })
        else:
            results.append({
                'test': test['name'],
                'params': test['params'],
                'count': 0,
                'works': False
            })

    # Resumo
    print("\n\n" + "="*80)
    print("RESUMO DOS TESTES")
    print("="*80)

    for r in results:
        status = "✅" if r['works'] else "❌"
        print(f"{status} {r['test']}: {r['count']} resultados")

    # Testes que funcionaram
    working_tests = [r for r in results if r['works']]
    if working_tests:
        print(f"\n✅ {len(working_tests)} teste(s) funcionaram!")
        print("\n💡 Parâmetros que funcionam:")
        for t in working_tests:
            print(f"  - {t['test']}: {t['params']}")
    else:
        print("\n❌ Nenhum teste retornou dados")
        print("💡 Endpoint pode requerer autenticação ou parâmetros específicos")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
