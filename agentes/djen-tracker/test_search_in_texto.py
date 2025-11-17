#!/usr/bin/env python3
"""
Busca '129021' no campo TEXTO da publicação
(não apenas em destinatarioadvogados)
"""
import requests
import json
import zipfile
import io
import re

def buscar_no_texto(tribunal: str, data: str, pattern: str):
    """Busca padrão no campo texto"""
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/E"

    print("=" * 80)
    print(f"BUSCA NO TEXTO: '{pattern}' em {tribunal} - {data}")
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

    # Buscar no campo 'texto'
    print(f"\n🔍 Buscando '{pattern}' no campo 'texto'...")

    matches = []

    for item in all_items:
        texto = item.get('texto', '')

        if pattern in texto:
            matches.append({
                'processo': item.get('numeroprocessocommascara', 'N/A'),
                'tipo': item.get('tipoComunicacao', 'N/A'),
                'orgao': item.get('nomeOrgao', 'N/A'),
                'texto_snippet': texto[:500] + '...' if len(texto) > 500 else texto
            })

    # Resultados
    print(f"\n" + "=" * 80)
    print(f"RESULTADO: {len(matches)} publicação(ões) com '{pattern}' no texto")
    print("=" * 80)

    if matches:
        print(f"\n✅ PATTERN '{pattern}' ENCONTRADO!\n")
        for i, match in enumerate(matches, 1):
            print(f"{i}. Processo: {match['processo']}")
            print(f"   Tipo: {match['tipo']}")
            print(f"   Órgão: {match['orgao']}")
            print(f"   Texto: {match['texto_snippet'][:200]}...")
            print()

            # Procurar contexto da OAB no texto
            texto_full = match['texto_snippet']
            # Buscar "OAB" próximo ao número
            oab_pattern = re.search(r'OAB[/\s]*SP[/\s]*' + pattern, texto_full, re.IGNORECASE)
            if oab_pattern:
                context_start = max(0, oab_pattern.start() - 50)
                context_end = min(len(texto_full), oab_pattern.end() + 50)
                print(f"   📍 Contexto: ...{texto_full[context_start:context_end]}...")
            print()

    else:
        print(f"\n❌ Pattern '{pattern}' NÃO encontrado no campo texto")

    return len(matches) > 0


def main():
    """Testa busca no texto"""
    # Teste 1: Padrão que sabemos que existe (460221)
    print("\n🧪 TESTE 1: Buscar '460221' no texto (sabemos que existe)")
    teste1 = buscar_no_texto("TJSP", "2025-11-14", "460221")

    # Teste 2: OAB alvo
    print("\n\n🧪 TESTE 2: Buscar '129021' no texto (OAB do usuário)")
    teste2 = buscar_no_texto("TJSP", "2025-11-14", "129021")

    # Conclusão
    print("\n" + "=" * 80)
    print("CONCLUSÃO")
    print("=" * 80)
    if teste1:
        print("✅ Teste 1 PASSOU - busca no texto funciona")
    else:
        print("⚠️  Teste 1 FALHOU - OAB 460221 não está no texto (só em destinatarioadvogados)")

    if teste2:
        print("✅ Teste 2 PASSOU - OAB 129021 ESTÁ NO TEXTO!")
        print("   💡 OAB pode estar apenas no texto, não em destinatarioadvogados")
    else:
        print("❌ Teste 2 FALHOU - OAB 129021 não está no texto de 2025-11-14")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
