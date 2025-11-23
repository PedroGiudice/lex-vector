#!/usr/bin/env python3
"""
Teste de Impacto de Headers HTTP

Testa se User-Agent, Accept-Encoding, etc afetam latência/rate limits.

ATUALIZADO: Usa nova API requests direta (2025-11-22)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import time
import requests
from datetime import datetime, timedelta
import json
from statistics import mean

def test_headers_configuration(config_name: str, headers: dict):
    """Testa uma configuração específica de headers."""
    api_url = "https://comunicaapi.pje.jus.br/api/v1"
    data_teste = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"\n🔧 Testando configuração: {config_name}")
    print(f"   Headers: {headers}")

    latencies = []
    status_codes = []

    # Enviar 20 requisições
    for i in range(20):
        try:
            start = time.time()
            response = requests.get(
                f"{api_url}/comunicacao",
                params={
                    'siglaTribunal': 'STJ',
                    'dataDisponibilizacao': data_teste,
                    'limit': 10,
                    'offset': 0
                },
                headers=headers,
                timeout=10
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            status_codes.append(response.status_code)

            if i % 5 == 0:
                print(f"   [{i+1}/20] {latency:.0f}ms (status {response.status_code})")

            time.sleep(0.5)  # Delay para não saturar

        except Exception as e:
            print(f"   ❌ Erro na requisição {i}: {e}")

    result = {
        'config_name': config_name,
        'headers': headers,
        'avg_latency': mean(latencies) if latencies else None,
        'min_latency': min(latencies) if latencies else None,
        'max_latency': max(latencies) if latencies else None,
        'status_codes': status_codes,
        'errors': 20 - len(latencies),
        'timestamp': datetime.now().isoformat()
    }

    print(f"   Média: {result['avg_latency']:.0f}ms")
    print(f"   Min: {result['min_latency']:.0f}ms | Max: {result['max_latency']:.0f}ms")

    return result

def run_tests():
    """Testa múltiplas configurações de headers."""
    configurations = [
        {
            'name': 'default',
            'headers': {}
        },
        {
            'name': 'browser_chrome',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
            }
        },
        {
            'name': 'browser_firefox',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate, br'
            }
        },
        {
            'name': 'api_client',
            'headers': {
                'User-Agent': 'DJEN-Collector/1.0',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip'
            }
        },
        {
            'name': 'minimal',
            'headers': {
                'Accept': 'application/json'
            }
        }
    ]

    results = []

    for config in configurations:
        result = test_headers_configuration(config['name'], config['headers'])
        results.append(result)

        # Salvar incrementalmente
        output_path = Path(__file__).parent.parent.parent / 'data' / 'diagnostics' / 'headers_impact.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        # Pausa entre configurações
        print("   ⏸️  Aguardando 15s antes da próxima configuração...")
        time.sleep(15)

    # Relatório final
    print("\n📊 RELATÓRIO FINAL")
    print("=" * 80)
    print(f"{'Configuração':<20s} | {'Avg Latency':<15s} | {'Min':<10s} | {'Max':<10s}")
    print("=" * 80)
    for r in results:
        print(f"{r['config_name']:<20s} | {r['avg_latency']:>10.0f}ms     | {r['min_latency']:>7.0f}ms | {r['max_latency']:>7.0f}ms")

    # Identificar melhor configuração
    best = min(results, key=lambda x: x['avg_latency'] if x['avg_latency'] else float('inf'))
    print(f"\n🏆 Melhor configuração: {best['config_name']} ({best['avg_latency']:.0f}ms média)")

if __name__ == '__main__':
    run_tests()
