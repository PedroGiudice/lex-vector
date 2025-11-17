#!/usr/bin/env python3
"""
Testa TODOS os meios disponíveis na API
E = Eletrônico (testado)
I = Intimação
R = Outros?
"""
import requests
import json
import zipfile
import io

def buscar_por_meio(tribunal: str, data: str, meio: str, target_oab: tuple):
    """Busca OAB em um meio específico"""
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/{meio}"
    target_num, target_uf = target_oab

    try:
        resp = requests.get(url, timeout=10)

        if resp.status_code == 404:
            return {'meio': meio, 'status': '404', 'matches': 0}

        resp.raise_for_status()
        api_data = resp.json()

        if api_data.get('status') != 'Processado':
            return {'meio': meio, 'status': 'não processado', 'matches': 0}

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

        # Buscar OAB
        matches = 0
        for item in all_items:
            advs = item.get('destinatarioadvogados', [])
            for adv_entry in advs:
                adv = adv_entry.get('advogado', {})
                numero = adv.get('numero_oab', '').replace('N', '').strip()
                uf = adv.get('uf_oab', '')

                if numero == target_num and uf == target_uf:
                    matches += 1
                    break

        return {
            'meio': meio,
            'status': 'ok',
            'total_publicacoes': len(all_items),
            'matches': matches,
            'total_comunicacoes': api_data.get('total_comunicacoes', 0)
        }

    except Exception as e:
        return {'meio': meio, 'status': f'erro: {str(e)[:30]}', 'matches': 0}


def main():
    """Testa todos os meios"""
    print("=" * 80)
    print("TESTE DE MEIOS: Buscando OAB 129021/SP em diferentes meios")
    print("=" * 80)

    tribunal = "TJSP"
    data = "2025-11-14"
    target_oab = ("129021", "SP")

    # Meios a testar
    meios = ['E', 'I', 'R', 'A', 'B', 'C', 'D']

    print(f"\n🏛️  Tribunal: {tribunal}")
    print(f"📅 Data: {data}")
    print(f"🎯 OAB: {target_oab[0]}/{target_oab[1]}")
    print(f"\n{'Meio':<10} {'Status':<20} {'Publicações':<15} {'Matches':<10}")
    print("-" * 80)

    resultados = []

    for meio in meios:
        resultado = buscar_por_meio(tribunal, data, meio, target_oab)
        resultados.append(resultado)

        status_str = resultado.get('status', 'erro')
        total = resultado.get('total_publicacoes', 0)
        matches = resultado.get('matches', 0)

        print(f"{meio:<10} {status_str:<20} {total:<15} {matches:<10}")

        if matches > 0:
            print(f"   🎉 ENCONTRADA!")

    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)

    meios_com_dados = [r for r in resultados if r.get('status') == 'ok']
    total_pubs = sum(r.get('total_publicacoes', 0) for r in meios_com_dados)
    total_matches = sum(r.get('matches', 0) for r in meios_com_dados)

    print(f"Meios testados: {len(meios)}")
    print(f"Meios com publicações: {len(meios_com_dados)}")
    print(f"Total de publicações: {total_pubs:,}")
    print(f"Matches encontrados: {total_matches}")

    if total_matches > 0:
        print(f"\n✅ OAB 129021/SP ENCONTRADA!")
        for r in resultados:
            if r.get('matches', 0) > 0:
                print(f"   Meio '{r['meio']}': {r['matches']} ocorrência(s)")
    else:
        print(f"\n❌ OAB 129021/SP não encontrada em nenhum meio")
        print("\n💡 Próximo passo: expandir período de busca (30 dias)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
