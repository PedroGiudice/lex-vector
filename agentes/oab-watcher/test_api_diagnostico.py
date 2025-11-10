"""
Script de Diagnóstico - Testar API DJEN
Objetivo: Validar se filtro por OAB funciona corretamente
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "https://comunicaapi.pje.jus.br"

def testar_api_sem_filtro():
    """Teste 1: Buscar publicações sem filtro de OAB (apenas por data)"""
    print("\n" + "="*70)
    print("TESTE 1: API sem filtro de OAB (apenas data)")
    print("="*70)

    # Data de ontem (mais provável ter dados)
    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    url = f"{BASE_URL}/api/v1/comunicacao"
    params = {
        'data_inicio': ontem,
        'data_fim': ontem
    }

    print(f"\nURL: {url}")
    print(f"Params: {json.dumps(params, indent=2)}")

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Total de items: {len(data.get('items', []))}")
            print(f"Count: {data.get('count', 'N/A')}")

            # Mostrar primeiro item como exemplo
            items = data.get('items', [])
            if items:
                print(f"\n--- Exemplo de item (primeiro) ---")
                primeiro = items[0]
                print(f"ID: {primeiro.get('id')}")
                print(f"Tribunal: {primeiro.get('siglaTribunal')}")
                print(f"Data: {primeiro.get('data_disponibilizacao')}")
                print(f"Tipo: {primeiro.get('tipoComunicacao')}")
                print(f"Texto (primeiros 100 chars): {primeiro.get('texto', '')[:100]}...")

                # Verificar estrutura de destinatários
                print(f"\nDestinatários: {len(primeiro.get('destinatarios', []))}")
                print(f"Destinatário Advogados: {len(primeiro.get('destinatarioadvogados', []))}")

                if primeiro.get('destinatarioadvogados'):
                    dest_adv = primeiro['destinatarioadvogados'][0]
                    print(f"\nEstrutura destinatarioadvogados:")
                    print(json.dumps(dest_adv, indent=2, ensure_ascii=False))

            return data
        else:
            print(f"Erro: {response.text}")
            return None

    except Exception as e:
        print(f"Erro na requisição: {e}")
        return None


def testar_api_com_filtro_oab():
    """Teste 2: Buscar com filtro de OAB"""
    print("\n" + "="*70)
    print("TESTE 2: API COM filtro de OAB")
    print("="*70)

    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    url = f"{BASE_URL}/api/v1/comunicacao"
    params = {
        'data_inicio': ontem,
        'data_fim': ontem,
        'numero_oab': '129021',  # OAB de teste
        'uf_oab': 'SP'
    }

    print(f"\nURL: {url}")
    print(f"Params: {json.dumps(params, indent=2)}")

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Total de items: {len(data.get('items', []))}")
            print(f"Count: {data.get('count', 'N/A')}")

            items = data.get('items', [])

            # DIAGNÓSTICO CRÍTICO: Verificar se algum item contém a OAB filtrada
            print("\n" + "-"*70)
            print("DIAGNÓSTICO: Verificando se items contêm OAB 129021/SP")
            print("-"*70)

            oab_encontradas = 0
            for i, item in enumerate(items[:20]):  # Verificar primeiros 20
                texto = item.get('texto', '')
                dest_advogados = item.get('destinatarioadvogados', [])

                # Buscar no texto
                if '129021' in texto:
                    oab_encontradas += 1
                    print(f"\n✓ Item {i+1}: OAB encontrada no TEXTO")
                    print(f"  Trecho: ...{texto[max(0, texto.find('129021')-30):texto.find('129021')+50]}...")

                # Buscar em destinatarioadvogados
                for dest in dest_advogados:
                    advogado = dest.get('advogado', {})
                    if advogado.get('numero_oab') == '129021' and advogado.get('uf_oab') == 'SP':
                        oab_encontradas += 1
                        print(f"\n✓ Item {i+1}: OAB encontrada em DESTINATARIOADVOGADOS")
                        print(f"  Advogado: {advogado.get('nome')}")

            print(f"\n{'='*70}")
            print(f"RESULTADO: {oab_encontradas} de {min(20, len(items))} items contêm OAB 129021/SP")

            if oab_encontradas == 0 and len(items) > 0:
                print("⚠️  PROBLEMA CONFIRMADO: API retornou items mas NENHUM contém a OAB filtrada!")
                print("    Conclusão: Filtro por OAB NÃO está funcionando na API")
            elif oab_encontradas > 0:
                print("✓ Filtro parece estar funcionando!")

            return data
        else:
            print(f"Erro: {response.text}")
            return None

    except Exception as e:
        print(f"Erro na requisição: {e}")
        return None


def testar_comparacao():
    """Teste 3: Comparar responses com e sem filtro"""
    print("\n" + "="*70)
    print("TESTE 3: Comparação - Com filtro vs Sem filtro")
    print("="*70)

    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    # Sem filtro
    url = f"{BASE_URL}/api/v1/comunicacao"
    params_sem_filtro = {
        'data_inicio': ontem,
        'data_fim': ontem
    }

    # Com filtro
    params_com_filtro = {
        'data_inicio': ontem,
        'data_fim': ontem,
        'numero_oab': '129021',
        'uf_oab': 'SP'
    }

    try:
        print("\nRequisição SEM filtro OAB...")
        resp1 = requests.get(url, params=params_sem_filtro, timeout=30)
        data1 = resp1.json() if resp1.status_code == 200 else {}
        count1 = len(data1.get('items', []))

        print("\nRequisição COM filtro OAB...")
        resp2 = requests.get(url, params=params_com_filtro, timeout=30)
        data2 = resp2.json() if resp2.status_code == 200 else {}
        count2 = len(data2.get('items', []))

        print("\n" + "-"*70)
        print("COMPARAÇÃO:")
        print("-"*70)
        print(f"Sem filtro OAB: {count1} items")
        print(f"Com filtro OAB: {count2} items")

        if count1 == count2:
            print("\n⚠️  PROBLEMA: Mesmo número de items!")
            print("    Conclusão: Filtro por OAB está sendo IGNORADO pela API")
        elif count2 < count1:
            print("\n✓ Filtro parece estar funcionando (menos items com filtro)")
        elif count2 > count1:
            print("\n⚠️  ESTRANHO: Mais items com filtro do que sem!")

    except Exception as e:
        print(f"Erro: {e}")


def main():
    """Executar todos os testes"""
    print("\n" + "#"*70)
    print("DIAGNÓSTICO API DJEN - Filtro por OAB")
    print("#"*70)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Teste 1: Sem filtro
    data_sem_filtro = testar_api_sem_filtro()

    # Teste 2: Com filtro
    data_com_filtro = testar_api_com_filtro_oab()

    # Teste 3: Comparação
    testar_comparacao()

    print("\n" + "#"*70)
    print("DIAGNÓSTICO COMPLETO")
    print("#"*70)


if __name__ == "__main__":
    main()
