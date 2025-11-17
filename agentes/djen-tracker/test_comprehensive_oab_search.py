#!/usr/bin/env python3
"""
Busca ABRANGENTE por OAB 129021/SP em múltiplos tribunais
Testa variações de formato e tribunais prioritários
"""
import requests
import json
import zipfile
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any

def buscar_oab_tribunal(tribunal: str, data: str, target_oabs: List[tuple]) -> Dict[str, Any]:
    """
    Busca OABs em um tribunal/data específicos

    Args:
        tribunal: Código do tribunal (TJSP, TRF3, etc)
        data: Data no formato YYYY-MM-DD
        target_oabs: Lista de tuplas (numero, uf) para buscar

    Returns:
        Dict com status e matches encontrados
    """
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/E"

    try:
        resp = requests.get(url, timeout=15)

        if resp.status_code == 404:
            return {'status': 'sem_publicacoes', 'matches': [], 'total': 0}

        resp.raise_for_status()
        api_data = resp.json()

        if api_data.get('status') != 'Processado':
            return {'status': 'nao_processado', 'matches': [], 'total': 0}

        # Baixar ZIP com JSONs
        s3_url = api_data['url']
        s3_resp = requests.get(s3_url, timeout=30)
        s3_resp.raise_for_status()

        # Extrair todos os JSONs
        zip_data = io.BytesIO(s3_resp.content)
        all_items = []

        with zipfile.ZipFile(zip_data) as zf:
            for filename in zf.namelist():
                if filename.endswith('.json'):
                    content = zf.read(filename).decode('utf-8')
                    parsed = json.loads(content)
                    all_items.extend(parsed.get('items', []))

        # Buscar OABs alvo em destinatarioadvogados
        matches = []
        for item in all_items:
            advs = item.get('destinatarioadvogados', [])
            for adv_entry in advs:
                adv = adv_entry.get('advogado', {})
                numero_raw = adv.get('numero_oab', '')
                uf = adv.get('uf_oab', '')

                # Normalizar número OAB (remover sufixo N se existir)
                numero = numero_raw.replace('N', '').strip()

                # Verificar se bate com alguma OAB alvo
                for target_num, target_uf in target_oabs:
                    if numero == target_num and uf == target_uf:
                        matches.append({
                            'tribunal': tribunal,
                            'data': data,
                            'processo': item.get('numeroprocessocommascara', 'N/A'),
                            'tipo': item.get('tipoComunicacao', 'N/A'),
                            'orgao': item.get('nomeOrgao', 'N/A'),
                            'advogado': adv.get('nome', 'N/A'),
                            'oab_raw': numero_raw,
                            'oab_normalizado': f"{numero}/{uf}"
                        })
                        break

        return {
            'status': 'ok',
            'total': len(all_items),
            'matches': matches
        }

    except Exception as e:
        return {'status': f'erro: {str(e)[:50]}', 'matches': [], 'total': 0}


def main():
    """Executa busca abrangente"""
    print("=" * 80)
    print("BUSCA ABRANGENTE: OAB 129021/SP em múltiplos tribunais")
    print("=" * 80)

    # OABs alvo (testar variações)
    target_oabs = [
        ("129021", "SP"),
        ("120210", "SP")
    ]

    # Tribunais prioritários (SP e federais)
    tribunais = [
        "TJSP",   # Tribunal de Justiça de SP
        "TRF3",   # Tribunal Regional Federal 3ª Região (SP/MS)
        "TRT2",   # Tribunal Regional do Trabalho 2ª Região (SP)
        "TRT15",  # Tribunal Regional do Trabalho 15ª Região (Campinas)
        "STJ",    # Superior Tribunal de Justiça
        "STF",    # Supremo Tribunal Federal
        "TST",    # Tribunal Superior do Trabalho
    ]

    # Gerar datas (últimos 10 dias úteis)
    hoje = datetime.now()
    datas = []
    for i in range(1, 20):
        data = hoje - timedelta(days=i)
        if data.weekday() < 5:  # Seg-Sex
            datas.append(data.strftime('%Y-%m-%d'))
        if len(datas) >= 10:
            break

    print(f"\n🎯 OABs alvo: {', '.join([f'{n}/{u}' for n, u in target_oabs])}")
    print(f"🏛️  Tribunais: {', '.join(tribunais)}")
    print(f"📅 Período: {datas[0]} até {datas[-1]} ({len(datas)} dias úteis)")
    print("\n" + "=" * 80)

    # Executar busca
    total_matches = []
    total_publicacoes = 0
    total_verificacoes = 0

    for tribunal in tribunais:
        print(f"\n🔍 {tribunal}:")
        tribunal_matches = 0

        for data in datas:
            total_verificacoes += 1
            resultado = buscar_oab_tribunal(tribunal, data, target_oabs)

            if resultado['status'] == 'sem_publicacoes':
                print(f"  {data}: Sem publicações", end='')
            elif resultado['status'] == 'ok':
                total_publicacoes += resultado['total']
                if resultado['matches']:
                    tribunal_matches += len(resultado['matches'])
                    total_matches.extend(resultado['matches'])
                    print(f"  {data}: ✅ {len(resultado['matches'])} MATCH(ES) em {resultado['total']} pubs", end='')
                else:
                    print(f"  {data}: {resultado['total']} pubs, 0 matches", end='')
            else:
                print(f"  {data}: {resultado['status']}", end='')

            # Nova linha a cada 3 datas para legibilidade
            if (datas.index(data) + 1) % 3 == 0:
                print()
            else:
                print(" | ", end='')

        print(f"\n  📊 Total {tribunal}: {tribunal_matches} matches")

    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO FINAL")
    print("=" * 80)
    print(f"Tribunais verificados: {len(tribunais)}")
    print(f"Datas verificadas: {len(datas)}")
    print(f"Total de verificações: {total_verificacoes}")
    print(f"Publicações processadas: {total_publicacoes:,}")
    print(f"Matches encontrados: {len(total_matches)}")
    print("=" * 80)

    if total_matches:
        print("\n✅ OAB ENCONTRADA! Detalhes:\n")
        for i, match in enumerate(total_matches, 1):
            print(f"{i}. {match['tribunal']} - {match['data']}")
            print(f"   Processo: {match['processo']}")
            print(f"   Tipo: {match['tipo']}")
            print(f"   Órgão: {match['orgao']}")
            print(f"   Advogado: {match['advogado']}")
            print(f"   OAB (raw): {match['oab_raw']}")
            print(f"   OAB (normalizado): {match['oab_normalizado']}")
            print()

        # Salvar resultados
        output_file = f"oab_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(total_matches, f, indent=2, ensure_ascii=False)
        print(f"💾 Resultados salvos em: {output_file}")

    else:
        print("\n❌ NENHUMA PUBLICAÇÃO ENCONTRADA")
        print("\n🔍 Possíveis explicações:")
        print("   1. OAB realmente não consta nas publicações do período")
        print("   2. Publicações em outros tribunais não testados")
        print("   3. Formato de OAB diferente no JSON (ex: com prefixo/sufixo)")
        print("   4. Necessário expandir período de busca")
        print("\n💡 Recomendações:")
        print("   - Verificar manualmente uma publicação conhecida")
        print("   - Testar tribunais adicionais (TRF1, TRF2, TRF4, TRF5, TRF6)")
        print("   - Expandir período para 30 dias")
        print("   - Verificar formato exato da OAB em publicação real")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Busca interrompida pelo usuário")
    except Exception as e:
        print(f"\n\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
