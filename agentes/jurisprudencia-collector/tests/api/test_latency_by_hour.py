#!/usr/bin/env python3
"""
Teste de Latência por Horário do Dia

Executa 10 requisições a cada hora por 24h.
Identifica padrões de performance temporal.

ATUALIZADO: Usa nova API requests direta (2025-11-22)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import time
import requests
from datetime import datetime, timedelta
import json
from statistics import mean, stdev

def measure_latency_at_hour(hour: int):
    """Mede latência média em um horário específico."""
    api_url = "https://comunicaapi.pje.jus.br/api/v1"
    data_teste = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    latencies = []
    errors = 0

    print(f"\n⏰ Horário: {hour:02d}:00")

    for i in range(10):
        try:
            start = time.time()
            response = requests.get(
                f"{api_url}/comunicacao",
                params={
                    'siglaTribunal': 'STJ',
                    'dataDisponibilizacao': data_teste,
                    'limit': 100,
                    'offset': 0
                },
                timeout=30
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)

            print(f"  [{i+1}/10] {latency:.0f}ms (status {response.status_code})")

            time.sleep(6)  # 10 req/min = 6s delay

        except Exception as e:
            errors += 1
            print(f"  [{i+1}/10] ERRO: {e}")

    if latencies:
        return {
            'hour': hour,
            'min_latency': min(latencies),
            'avg_latency': mean(latencies),
            'max_latency': max(latencies),
            'stdev_latency': stdev(latencies) if len(latencies) > 1 else 0,
            'errors': errors,
            'total_requests': 10,
            'timestamp': datetime.now().isoformat()
        }
    else:
        return {
            'hour': hour,
            'errors': errors,
            'total_requests': 10,
            'timestamp': datetime.now().isoformat()
        }

def run_24h_test():
    """Executa teste por 24 horas."""
    results = []

    for hour in range(24):
        # Esperar até o próximo horário exato (opcional)
        current_hour = datetime.now().hour
        if current_hour == hour:
            result = measure_latency_at_hour(hour)
            results.append(result)

            # Salvar incrementalmente
            output_path = Path(__file__).parent.parent.parent / 'data' / 'diagnostics' / 'latency_by_hour.json'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)

            # Esperar ~1h até próximo horário
            print("\n⏸️  Aguardando próximo horário...")
            time.sleep(3600 - (datetime.now().minute * 60 + datetime.now().second))
        else:
            print(f"⏭️  Pulando hora {hour} (atual: {current_hour})")

    return results

def quick_test():
    """Teste rápido (apenas horário atual)."""
    current_hour = datetime.now().hour
    result = measure_latency_at_hour(current_hour)

    output_path = Path(__file__).parent.parent.parent / 'data' / 'diagnostics' / 'latency_quick_test.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump([result], f, indent=2)

    print(f"\n📊 Resultado:")
    print(f"   Mínimo: {result.get('min_latency', 'N/A'):.0f}ms")
    print(f"   Média: {result.get('avg_latency', 'N/A'):.0f}ms")
    print(f"   Máximo: {result.get('max_latency', 'N/A'):.0f}ms")

if __name__ == '__main__':
    import sys

    if '--full' in sys.argv:
        print("🕐 Iniciando teste de 24 horas...")
        run_24h_test()
    else:
        print("⚡ Teste rápido (use --full para 24h)")
        quick_test()
