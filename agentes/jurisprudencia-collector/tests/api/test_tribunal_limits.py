#!/usr/bin/env python3
"""
Teste de Limites por Tribunal

Verifica se STJ, TRF1, TRF2, etc têm rate limits diferentes.

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

def test_tribunal_limit(tribunal: str):
    """Testa limite de rate para um tribunal específico."""
    api_url = "https://comunicaapi.pje.jus.br/api/v1"
    data_teste = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"\n🏛️  Testando tribunal: {tribunal}")

    latencies = []
    got_429 = False
    request_count = 0

    # Enviar requisições até receber 429 (max 100 para segurança)
    for i in range(100):
        try:
            start = time.time()
            response = requests.get(
                f"{api_url}/comunicacao",
                params={
                    'siglaTribunal': tribunal,
                    'dataDisponibilizacao': data_teste,
                    'limit': 10,
                    'offset': 0
                },
                timeout=10
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            request_count += 1

            if response.status_code == 429:
                got_429 = True
                print(f"   ⚠️  HTTP 429 após {request_count} requisições")
                break

            if i % 10 == 0:
                print(f"   {request_count} requisições... (avg latency: {mean(latencies):.0f}ms)")

            # Delay mínimo (não queremos rate limiting artificial)
            time.sleep(0.1)

        except Exception as e:
            print(f"   ❌ Erro na requisição {i}: {e}")
            break

    result = {
        'tribunal': tribunal,
        'request_count': request_count,
        'got_429': got_429,
        'avg_latency': mean(latencies) if latencies else None,
        'min_latency': min(latencies) if latencies else None,
        'max_latency': max(latencies) if latencies else None,
        'timestamp': datetime.now().isoformat()
    }

    if got_429:
        print(f"   Limite: ~{request_count} requisições antes de 429")
    else:
        print(f"   ✅ Sem HTTP 429 após {request_count} requisições")

    return result

def run_tests():
    """Testa múltiplos tribunais."""
    tribunais = ['STJ', 'TRF1', 'TRF2', 'TRF3', 'TJSP']

    results = []

    for tribunal in tribunais:
        result = test_tribunal_limit(tribunal)
        results.append(result)

        # Salvar incrementalmente
        output_path = Path(__file__).parent.parent.parent / 'data' / 'diagnostics' / 'tribunal_limits.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        # Pausa entre tribunais
        print("   ⏸️  Aguardando 30s antes do próximo tribunal...")
        time.sleep(30)

    # Relatório final
    print("\n📊 RELATÓRIO FINAL")
    print("=" * 60)
    for r in results:
        status = "🚫 HTTP 429" if r['got_429'] else "✅ OK"
        print(f"{r['tribunal']:8s} | {status} | {r['request_count']} req | {r['avg_latency']:.0f}ms avg")

if __name__ == '__main__':
    run_tests()
