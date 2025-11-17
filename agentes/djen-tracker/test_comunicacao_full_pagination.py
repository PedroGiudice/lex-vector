#!/usr/bin/env python3
"""
Busca OAB 129021/SP paginando por TODAS as páginas do endpoint /api/v1/comunicacao
"""
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def search_page(page: int, target_num: str, target_uf: str):
    """Busca OAB em uma página específica"""
    url = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"

    try:
        resp = requests.get(url, params={"page": page}, timeout=20)

        if resp.status_code != 200:
            return {'page': page, 'error': f'HTTP {resp.status_code}', 'matches': []}

        data = resp.json()
        matches = []

        for item in data.get('items', []):
            advs = item.get('destinatarioadvogados', [])
            for adv_entry in advs:
                adv = adv_entry.get('advogado', {})
                numero_raw = adv.get('numero_oab', '')
                uf = adv.get('uf_oab', '')

                # Busca flexível - começa com target_num
                if numero_raw.startswith(target_num) and uf == target_uf:
                    matches.append({
                        'page': page,
                        'processo': item.get('numeroprocessocommascara'),
                        'tribunal': item.get('siglaTribunal'),
                        'data': item.get('data_disponibilizacao'),
                        'tipo': item.get('tipoComunicacao'),
                        'advogado': adv.get('nome'),
                        'oab': f"{numero_raw}/{uf}"
                    })

        return {
            'page': page,
            'count': data.get('count'),
            'items_checked': len(data.get('items', [])),
            'matches': matches
        }

    except Exception as e:
        return {'page': page, 'error': str(e)[:50], 'matches': []}


def main():
    """Busca em todas as páginas"""
    print("="*80)
    print("BUSCA COMPLETA: OAB 129021/SP com paginação total")
    print("="*80)

    target_num = "129021"
    target_uf = "SP"

    # Primeiro, verificar quantas páginas existem
    print("\n🔍 Verificando total de registros...")
    resp = requests.get("https://comunicaapi.pje.jus.br/api/v1/comunicacao", timeout=15)
    data = resp.json()

    total_count = data.get('count', 0)
    items_per_page = len(data.get('items', []))
    total_pages = (total_count // items_per_page) + (1 if total_count % items_per_page else 0)

    print(f"📊 Total de registros: {total_count:,}")
    print(f"📄 Items por página: {items_per_page}")
    print(f"📑 Total de páginas: {total_pages}")

    # Limitar a 100 páginas para não demorar muito
    max_pages = min(total_pages, 100)
    print(f"\n⏳ Buscando OAB {target_num}/{target_uf} em {max_pages} páginas...")
    print(f"   (Total de publicações: {max_pages * items_per_page:,})\n")

    all_matches = []
    completed = 0
    start_time = time.time()

    # Buscar em paralelo
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(search_page, page, target_num, target_uf): page
                   for page in range(1, max_pages + 1)}

        for future in as_completed(futures):
            completed += 1
            resultado = future.result()

            # Progress
            if completed % 10 == 0 or completed == max_pages:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (max_pages - completed) / rate if rate > 0 else 0
                print(f"   {completed}/{max_pages} ({completed*100//max_pages}%) | "
                      f"{rate:.1f} pág/s | ETA: {eta:.0f}s", end='\r')

            # Verificar matches
            if resultado.get('matches'):
                all_matches.extend(resultado['matches'])
                print(f"\n   🎉 MATCH na página {resultado['page']}! ({len(resultado['matches'])} publicação(ões))       ")

    elapsed_total = time.time() - start_time

    # Resultados
    print(f"\n\n" + "="*80)
    print("RESULTADOS")
    print("="*80)
    print(f"Tempo: {elapsed_total:.1f}s")
    print(f"Páginas verificadas: {completed}")
    print(f"Publicações verificadas: {completed * items_per_page:,}")
    print(f"Matches encontrados: {len(all_matches)}")
    print("="*80)

    if all_matches:
        print(f"\n✅ OAB {target_num}/{target_uf} ENCONTRADA!\n")
        for i, match in enumerate(all_matches, 1):
            print(f"{i}. Página {match['page']}")
            print(f"   Processo: {match['processo']}")
            print(f"   Tribunal: {match['tribunal']}")
            print(f"   Data: {match['data']}")
            print(f"   Tipo: {match['tipo']}")
            print(f"   Advogado: {match['advogado']}")
            print(f"   OAB: {match['oab']}")
            print()

        # Salvar
        output = f"oab_129021_sp_comunicacao_{int(time.time())}.json"
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(all_matches, f, indent=2, ensure_ascii=False)
        print(f"💾 Salvo em: {output}")

    else:
        print(f"\n❌ OAB {target_num}/{target_uf} NÃO encontrada")
        print(f"   Páginas verificadas: {completed}")
        print(f"   Publicações: ~{completed * items_per_page:,}")
        print("\n💡 A OAB pode estar:")
        print("   - Além das primeiras 100 páginas")
        print("   - Em endpoint diferente")
        print("   - Com número ligeiramente diferente")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido")
    except Exception as e:
        print(f"\n\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
