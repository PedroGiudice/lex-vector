#!/usr/bin/env python3
"""
Testa se a API tem paginação real ou se o ZIP já contém tudo
"""
import requests
import json

def test_pagination(tribunal: str = "TJSP", data: str = "2025-11-14"):
    """Testa diferentes páginas da API"""

    print("=" * 80)
    print("TESTE DE PAGINAÇÃO DA API")
    print("=" * 80)

    base_url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/E"

    # Testar endpoint base vs paginado
    urls_to_test = [
        (base_url, "Base (sem parâmetros)"),
        (f"{base_url}?page=1", "Página 1"),
        (f"{base_url}?page=2", "Página 2"),
        (f"{base_url}?page=3", "Página 3"),
    ]

    results = {}

    for url, label in urls_to_test:
        print(f"\n{label}:")
        print(f"  URL: {url}")

        try:
            resp = requests.get(url, timeout=15)

            if resp.status_code != 200:
                print(f"  Status: HTTP {resp.status_code}")
                continue

            data_json = resp.json()

            # Extrair informações chave
            info = {
                'status': data_json.get('status'),
                'total_comunicacoes': data_json.get('total_comunicacoes'),
                'numero_paginas': data_json.get('numero_paginas'),
                'tamanho_bytes': data_json.get('tamanho_bytes'),
                'hash': data_json.get('hash'),
                'url_s3': data_json.get('url', '')[:80] + '...'
            }

            results[label] = info

            print(f"  Status: {info['status']}")
            print(f"  Total comunicações: {info['total_comunicacoes']}")
            print(f"  Número de páginas: {info['numero_paginas']}")
            print(f"  Tamanho: {info['tamanho_bytes']} bytes")
            print(f"  Hash: {info['hash'][:16]}...")
            print(f"  URL S3: {info['url_s3']}")

        except Exception as e:
            print(f"  ERRO: {e}")

    # Análise comparativa
    print("\n" + "=" * 80)
    print("ANÁLISE COMPARATIVA")
    print("=" * 80)

    if len(results) >= 2:
        base = results.get("Base (sem parâmetros)")
        page1 = results.get("Página 1")
        page2 = results.get("Página 2")

        if base and page1:
            if base['hash'] == page1['hash']:
                print("✅ Base == Página 1 (mesmo hash)")
            else:
                print("⚠️  Base ≠ Página 1 (HASHES DIFERENTES!)")

        if base and page2:
            if base['hash'] == page2['hash']:
                print("⚠️  Base == Página 2 (mesmo hash - suspeito!)")
            else:
                print("✅ Base ≠ Página 2 (hashes diferentes)")

        if page1 and page2:
            if page1['hash'] == page2['hash']:
                print("⚠️  Página 1 == Página 2 (mesmo hash - não há paginação real)")
            else:
                print("✅ Página 1 ≠ Página 2 (PAGINAÇÃO REAL CONFIRMADA!)")

        # Verificar total_comunicacoes
        print(f"\n📊 Total de comunicações:")
        for label, info in results.items():
            if info:
                print(f"  {label}: {info['total_comunicacoes']}")

    print("\n" + "=" * 80)
    print("CONCLUSÃO")
    print("=" * 80)

    if len(results) >= 3:
        hashes = [info['hash'] for info in results.values() if info]
        unique_hashes = len(set(hashes))

        if unique_hashes == 1:
            print("❌ TODOS OS ENDPOINTS RETORNAM O MESMO ZIP")
            print("   → API não implementa paginação real")
            print("   → ZIP único contém todas as publicações")
            print("   → Processamento atual está CORRETO e COMPLETO")

        elif unique_hashes == len(hashes):
            print("⚠️  CADA ENDPOINT RETORNA ZIP DIFERENTE")
            print("   → API TEM PAGINAÇÃO REAL")
            print("   → Precisamos baixar TODAS as páginas")
            print("   → BUG: estamos processando apenas 1 página!")

        else:
            print("⚠️  COMPORTAMENTO MISTO")
            print(f"   → {unique_hashes} hashes únicos de {len(hashes)} endpoints")
            print("   → Investigação adicional necessária")


if __name__ == "__main__":
    try:
        test_pagination()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
