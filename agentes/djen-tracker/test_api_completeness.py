#!/usr/bin/env python3
"""
Verifica COMPLETUDE dos dados retornados pela API DJEN
Testa se estamos recebendo TODAS as publicações ou apenas uma amostra
"""
import requests
import json
import zipfile
import io
from typing import Dict, Any, List

def investigar_api_response(tribunal: str = "TJSP", data: str = "2025-11-14") -> Dict[str, Any]:
    """
    Investiga detalhadamente a resposta da API

    Verifica:
    1. Estrutura do JSON de metadata
    2. Quantidade de arquivos no ZIP
    3. Total de publicações por arquivo
    4. Campos de paginação/batch
    """
    url = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/E"

    print("=" * 80)
    print(f"INVESTIGAÇÃO: {tribunal} - {data}")
    print("=" * 80)

    # 1. Request inicial à API
    print(f"\n1️⃣ GET {url}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    api_data = resp.json()
    print(f"\n📋 Metadata da API:")
    print(json.dumps(api_data, indent=2, ensure_ascii=False))

    # Verificar campos de paginação/totalização
    print(f"\n🔍 Campos relevantes:")
    for key in ['total', 'totalPublicacoes', 'totalRegistros', 'paginas', 'batch', 'page', 'size']:
        if key in api_data:
            print(f"  {key}: {api_data[key]}")

    # 2. Download do ZIP
    s3_url = api_data.get('url')
    if not s3_url:
        print("❌ Sem URL de download")
        return {}

    print(f"\n2️⃣ GET {s3_url[:80]}...")
    s3_resp = requests.get(s3_url, timeout=30)
    s3_resp.raise_for_status()

    zip_size_mb = len(s3_resp.content) / (1024 * 1024)
    print(f"📦 Tamanho do ZIP: {zip_size_mb:.2f} MB")

    # 3. Extrair e analisar JSONs
    print(f"\n3️⃣ Conteúdo do ZIP:")
    zip_data = io.BytesIO(s3_resp.content)

    json_files = []
    total_items = 0
    items_per_file = {}

    with zipfile.ZipFile(zip_data) as zf:
        all_files = zf.namelist()
        print(f"📄 Total de arquivos no ZIP: {len(all_files)}")

        for filename in all_files:
            if filename.endswith('.json'):
                json_files.append(filename)
                content = zf.read(filename).decode('utf-8')
                parsed = json.loads(content)

                # Verificar estrutura
                items = parsed.get('items', [])
                items_per_file[filename] = len(items)
                total_items += len(items)

                # Verificar campos de paginação no JSON
                metadata_keys = [k for k in parsed.keys() if k != 'items']
                if metadata_keys:
                    print(f"\n  📋 {filename}: {len(items)} items")
                    print(f"     Metadados: {metadata_keys}")
                    for key in metadata_keys:
                        print(f"     {key}: {parsed[key]}")
            else:
                print(f"  📄 {filename} (não-JSON)")

    print(f"\n📊 RESUMO:")
    print(f"  Arquivos JSON: {len(json_files)}")
    print(f"  Total de publicações: {total_items}")
    print(f"  Publicações por arquivo:")
    for filename, count in items_per_file.items():
        print(f"    {filename}: {count}")

    # 4. Verificar se há indicação de múltiplos batches
    print(f"\n4️⃣ ANÁLISE DE COMPLETUDE:")

    # Verificar nomes dos arquivos (podem indicar batch/parte)
    if len(json_files) > 1:
        print(f"  ⚠️  Múltiplos arquivos JSON ({len(json_files)})")
        print(f"  Padrão: {json_files[0]} até {json_files[-1]}")

        # Verificar se há sequência numérica
        import re
        pattern = r'_(\d+)\.json$'
        numbers = []
        for fname in json_files:
            match = re.search(pattern, fname)
            if match:
                numbers.append(int(match.group(1)))

        if numbers:
            numbers.sort()
            print(f"  📈 Sequência detectada: {numbers[0]} até {numbers[-1]}")
            if numbers[-1] - numbers[0] + 1 == len(numbers):
                print(f"  ✅ Sequência contígua (sem gaps)")
            else:
                print(f"  ⚠️  Sequência com gaps!")
                missing = set(range(numbers[0], numbers[-1] + 1)) - set(numbers)
                print(f"  ❌ Faltando: {sorted(missing)}")
    else:
        print(f"  ✅ Arquivo único - provavelmente completo")

    # 5. Testar se há outros endpoints/páginas
    print(f"\n5️⃣ TESTE DE ENDPOINTS ADICIONAIS:")

    # Testar variações de URL que podem indicar paginação
    test_urls = [
        f"{url}?page=1",
        f"{url}?page=2",
        f"{url}/1",
        f"{url}/2",
        f"{url.replace('/E', '/E/1')}",
        f"{url.replace('/E', '/E/2')}",
    ]

    for test_url in test_urls:
        try:
            test_resp = requests.get(test_url, timeout=5)
            if test_resp.status_code == 200:
                print(f"  ✅ {test_url} → HTTP 200 (PODE HAVER MAIS DADOS!)")
            elif test_resp.status_code == 404:
                print(f"  ❌ {test_url} → HTTP 404")
            else:
                print(f"  ⚠️  {test_url} → HTTP {test_resp.status_code}")
        except Exception as e:
            print(f"  ❌ {test_url} → {str(e)[:30]}")

    return {
        'tribunal': tribunal,
        'data': data,
        'json_files': len(json_files),
        'total_items': total_items,
        'zip_size_mb': zip_size_mb,
        'api_metadata': api_data
    }


def main():
    """Executa investigação"""
    # Testar data que sabemos ter publicações
    resultado = investigar_api_response("TJSP", "2025-11-14")

    print("\n" + "=" * 80)
    print("CONCLUSÃO")
    print("=" * 80)

    if resultado.get('total_items', 0) > 0:
        print(f"✅ {resultado['total_items']} publicações encontradas")
        print(f"📦 {resultado['json_files']} arquivo(s) JSON no ZIP")
        print(f"💾 {resultado['zip_size_mb']:.2f} MB de dados")

        print("\n💡 PRÓXIMOS PASSOS:")
        print("  1. Verificar se há endpoints adicionais para obter mais dados")
        print("  2. Confirmar que estamos processando TODOS os arquivos do ZIP")
        print("  3. Comparar com total esperado (se disponível na API)")
    else:
        print("❌ Nenhuma publicação encontrada")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
