#!/usr/bin/env python3
"""
TESTE DE SANIDADE: Buscar OAB que SABEMOS que existe
OAB 460221/SP apareceu em TJSP 2025-11-14
"""
import requests
import json
import zipfile
import io

def buscar_oab(tribunal: str, data: str, target_num: str, target_uf: str):
    """Busca OAB específica"""
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/E"

    print("=" * 80)
    print(f"TESTE DE SANIDADE: Buscando OAB {target_num}/{target_uf}")
    print(f"Tribunal: {tribunal}, Data: {data}")
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

    print(f"\n📊 Total publicações: {len(all_items)}")

    # Buscar OAB target - COM DEBUG
    print(f"\n🔍 Buscando OAB {target_num}/{target_uf} em destinatarioadvogados...")

    matches = []
    debug_samples = []

    for i, item in enumerate(all_items):
        advs = item.get('destinatarioadvogados', [])

        # Debug: mostrar primeiras 5 OABs
        if i < 5 and advs:
            for adv_entry in advs:
                adv = adv_entry.get('advogado', {})
                debug_samples.append({
                    'raw': adv.get('numero_oab', ''),
                    'uf': adv.get('uf_oab', ''),
                    'normalizado': adv.get('numero_oab', '').replace('N', '').strip()
                })

        for adv_entry in advs:
            adv = adv_entry.get('advogado', {})
            numero_raw = adv.get('numero_oab', '')
            uf = adv.get('uf_oab', '')

            # Normalizar
            numero = numero_raw.replace('N', '').strip()

            # DEBUG: Mostrar a comparação
            if i == 0 and adv:
                print(f"\n   DEBUG primeira OAB:")
                print(f"     Raw: '{numero_raw}'")
                print(f"     UF: '{uf}'")
                print(f"     Normalizado: '{numero}'")
                print(f"     Target: '{target_num}'")
                print(f"     Match numero: {numero == target_num}")
                print(f"     Match UF: {uf == target_uf}")

            # Comparar
            if numero == target_num and uf == target_uf:
                matches.append({
                    'processo': item.get('numeroprocessocommascara', 'N/A'),
                    'tipo': item.get('tipoComunicacao', 'N/A'),
                    'advogado': adv.get('nome', 'N/A'),
                    'oab_raw': numero_raw,
                    'oab_norm': numero,
                    'uf': uf
                })

    # Mostrar debug samples
    print(f"\n📋 Amostra das primeiras OABs (debug):")
    for i, sample in enumerate(debug_samples[:10], 1):
        print(f"   {i}. Raw: {sample['raw']:15s} UF: {sample['uf']:5s} Norm: {sample['normalizado']}")

    # Resultados
    print(f"\n" + "=" * 80)
    print(f"RESULTADO: {len(matches)} match(es)")
    print("=" * 80)

    if matches:
        print(f"\n✅ OAB {target_num}/{target_uf} ENCONTRADA!\n")
        for match in matches:
            print(f"  Processo: {match['processo']}")
            print(f"  Tipo: {match['tipo']}")
            print(f"  Advogado: {match['advogado']}")
            print(f"  OAB raw: {match['oab_raw']}")
            print(f"  OAB norm: {match['oab_norm']}/{match['uf']}")
            print()
        print("🎉 CÓDIGO DE BUSCA ESTÁ FUNCIONANDO!")
    else:
        print(f"\n❌ OAB {target_num}/{target_uf} NÃO encontrada")
        print("⚠️  CÓDIGO DE BUSCA PODE ESTAR COM BUG!")

    return len(matches) > 0


if __name__ == "__main__":
    # Teste 1: OAB que sabemos que existe (vimos no JSON)
    print("\n🧪 TESTE 1: OAB 460221/SP (sabemos que existe)")
    teste1_ok = buscar_oab("TJSP", "2025-11-14", "460221", "SP")

    # Teste 2: OAB alvo do usuário
    print("\n\n🧪 TESTE 2: OAB 129021/SP (OAB do chefe/pai do usuário)")
    teste2_ok = buscar_oab("TJSP", "2025-11-14", "129021", "SP")

    # Conclusão
    print("\n" + "=" * 80)
    print("CONCLUSÃO DOS TESTES")
    print("=" * 80)
    if teste1_ok:
        print("✅ Teste 1 PASSOU - código de busca funciona")
    else:
        print("❌ Teste 1 FALHOU - BUG no código!")

    if teste2_ok:
        print("✅ Teste 2 PASSOU - OAB 129021/SP encontrada em 2025-11-14")
    else:
        print("❌ Teste 2 FALHOU - OAB 129021/SP NÃO está em 2025-11-14 TJSP")
        print("   Possibilidades:")
        print("   - Data diferente (anterior a 7 dias)")
        print("   - Tribunal diferente")
        print("   - Meio diferente (I ou R, não E)")
