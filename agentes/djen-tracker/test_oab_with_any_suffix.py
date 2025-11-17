#!/usr/bin/env python3
"""
Busca OAB 129021 com QUALQUER sufixo (não apenas removendo N)
Pode ser 129021N, 129021D, 129021DN, 129021R, etc
"""
import requests
import json
import zipfile
import io

def buscar_oab_flexible(tribunal: str, data: str, target_prefix: str, target_uf: str):
    """Busca OAB que COMECE com target_prefix"""
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/E"

    print("=" * 80)
    print(f"BUSCA FLEXÍVEL: Qualquer OAB que comece com '{target_prefix}' UF '{target_uf}'")
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

    # Buscar OAB com prefixo - SEM normalizar
    print(f"\n🔍 Buscando OABs que começam com '{target_prefix}'...")

    matches = []
    oabs_found = set()

    for item in all_items:
        advs = item.get('destinatarioadvogados', [])
        for adv_entry in advs:
            adv = adv_entry.get('advogado', {})
            numero_raw = adv.get('numero_oab', '')  # NÃO normalizar
            uf = adv.get('uf_oab', '')

            # Verificar se COMEÇA com target_prefix
            if numero_raw.startswith(target_prefix) and uf == target_uf:
                oabs_found.add(numero_raw)
                matches.append({
                    'processo': item.get('numeroprocessocommascara', 'N/A'),
                    'tipo': item.get('tipoComunicacao', 'N/A'),
                    'advogado': adv.get('nome', 'N/A'),
                    'oab_raw': numero_raw,
                    'uf': uf
                })

    # Resultados
    print(f"\n" + "=" * 80)
    print(f"RESULTADO: {len(matches)} publicação(ões) encontrada(s)")
    print(f"OABs únicas: {len(oabs_found)}")
    print("=" * 80)

    if oabs_found:
        print(f"\n✅ OABs encontradas que começam com '{target_prefix}':")
        for oab in sorted(oabs_found):
            count = sum(1 for m in matches if m['oab_raw'] == oab)
            print(f"   {oab}/{target_uf} → {count} publicação(ões)")

        print(f"\n📋 Detalhes das publicações:")
        for i, match in enumerate(matches[:10], 1):  # Primeiras 10
            print(f"\n{i}. Processo: {match['processo']}")
            print(f"   Tipo: {match['tipo']}")
            print(f"   Advogado: {match['advogado']}")
            print(f"   OAB: {match['oab_raw']}/{match['uf']}")

        if len(matches) > 10:
            print(f"\n   ... e mais {len(matches) - 10} publicação(ões)")

    else:
        print(f"\n❌ Nenhuma OAB começando com '{target_prefix}/{target_uf}' encontrada")

    return len(matches) > 0


def main():
    """Testa busca flexível"""
    # Teste 1: OAB que sabemos que existe
    print("\n🧪 TESTE 1: OAB começando com '460221' (sabemos que existe 460221N)")
    teste1 = buscar_oab_flexible("TJSP", "2025-11-14", "460221", "SP")

    # Teste 2: OAB alvo
    print("\n\n🧪 TESTE 2: OAB começando com '129021' (OAB do usuário)")
    teste2 = buscar_oab_flexible("TJSP", "2025-11-14", "129021", "SP")

    # Teste 3: Buscar em faixa maior
    print("\n\n🧪 TESTE 3: OABs na faixa 12902X (vizinhas)")
    for num in range(129020, 129030):
        resultado = buscar_oab_flexible("TJSP", "2025-11-14", str(num), "SP")
        if resultado:
            print(f"   ✅ Encontrada: {num}/SP")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
