#!/usr/bin/env python3
"""Busca OAB 129021/SP em múltiplas datas usando formato JSON"""
import requests
import json
import zipfile
import io
from datetime import datetime, timedelta

def buscar_oab_em_data(tribunal, data, target_oab="129021", target_uf="SP"):
    """Busca OAB em uma data específica"""
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/E"

    try:
        resp = requests.get(url, timeout=15)

        if resp.status_code == 404:
            return {'status': '404', 'matches': []}

        resp.raise_for_status()
        api_data = resp.json()

        if api_data.get('status') != 'Processado':
            return {'status': 'não processado', 'matches': []}

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
                    all_items.extend(parsed['items'])

        # Buscar OAB target em destinatarioadvogados
        matches = []
        for item in all_items:
            advs = item.get('destinatarioadvogados', [])
            for adv_entry in advs:
                adv = adv_entry.get('advogado', {})
                numero = adv.get('numero_oab', '').replace('N', '')  # Remove sufixo
                uf = adv.get('uf_oab', '')

                if numero == target_oab and uf == target_uf:
                    matches.append({
                        'processo': item['numeroprocessocommascara'],
                        'tipo': item['tipoComunicacao'],
                        'orgao': item['nomeOrgao'],
                        'advogado': adv['nome']
                    })
                    break

        return {
            'status': 'ok',
            'total': len(all_items),
            'matches': matches
        }

    except Exception as e:
        return {'status': f'erro: {e}', 'matches': []}

# Testar últimos 7 dias úteis
hoje = datetime.now()
datas = []
for i in range(1, 15):
    data = hoje - timedelta(days=i)
    if data.weekday() < 5:  # Seg-Sex
        datas.append(data.strftime('%Y-%m-%d'))
    if len(datas) >= 7:
        break

print("=" * 80)
print("BUSCA: OAB 129021/SP nos últimos 7 dias úteis")
print("=" * 80)

total_matches = []

for data in datas:
    print(f"\n{data}: ", end='', flush=True)
    resultado = buscar_oab_em_data('TJSP', data)

    if resultado['status'] == '404':
        print("Sem publicações")
    elif resultado['status'] == 'ok':
        print(f"{resultado['total']} publicações, {len(resultado['matches'])} matches")
        if resultado['matches']:
            total_matches.extend(resultado['matches'])
            for match in resultado['matches']:
                print(f"  ✅ {match['processo']} - {match['tipo']}")
    else:
        print(resultado['status'])

print("\n" + "=" * 80)
print(f"TOTAL: {len(total_matches)} publicações com OAB 129021/SP")
print("=" * 80)

if total_matches:
    print("\n✅ OAB 129021/SP ENCONTRADA!")
    for i, match in enumerate(total_matches, 1):
        print(f"\n{i}. Processo: {match['processo']}")
        print(f"   Tipo: {match['tipo']}")
        print(f"   Órgão: {match['orgao']}")
        print(f"   Advogado: {match['advogado']}")
else:
    print("\n⚠️  OAB 129021/SP não encontrada nos últimos 7 dias úteis do TJSP")
    print("   Isso pode significar:")
    print("   1. Não houve publicações para esta OAB no período")
    print("   2. Publicações foram em outros tribunais (TRF, TRT, etc)")
