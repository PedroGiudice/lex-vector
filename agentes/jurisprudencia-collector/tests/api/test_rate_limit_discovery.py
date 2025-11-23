#!/usr/bin/env python3
"""
Teste de Descoberta de Rate Limit Real da API DJEN

Metodologia:
1. Inicia com taxa baixa (10 req/min)
2. Aumenta gradualmente (10→20→30→50→100→200)
3. Monitora HTTP 429
4. Registra limite exato quando receber primeiro 429
5. Analisa headers: Retry-After, X-RateLimit-*

ATUALIZADO: Usa nova API do DJENDownloader (2025-11-22)
"""

import sys
from pathlib import Path

# Adicionar src/ ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import time
import requests
from datetime import datetime, timedelta
import json

def test_rate_limit():
    """Descobre limite real enviando requisições crescentes."""
    api_url = "https://comunicaapi.pje.jus.br/api/v1"
    data_teste = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    rates = [10, 20, 30, 50, 100, 200, 300]  # req/min

    for rate in rates:
        print(f"\n🔍 Testando taxa: {rate} req/min")
        delay = 60.0 / rate  # Delay entre requisições

        results = {
            'rate': rate,
            'requests': [],
            'got_429': False,
            'timestamp': datetime.now().isoformat()
        }

        # Enviar 60 requisições (1 minuto completo)
        for i in range(60):
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
                    timeout=10
                )
                latency = (time.time() - start) * 1000

                results['requests'].append({
                    'index': i,
                    'status': response.status_code,
                    'latency_ms': latency,
                    'headers': dict(response.headers)
                })

                if response.status_code == 429:
                    results['got_429'] = True
                    print(f"⚠️  HTTP 429 recebido após {i+1} requisições!")
                    print(f"   Limite descoberto: ~{rate} req/min")

                    # Salvar dados
                    output_path = Path(__file__).parent.parent.parent / 'data' / 'diagnostics' / f'rate_limit_discovery_{rate}rpm.json'
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w') as f:
                        json.dump(results, f, indent=2)

                    return rate  # Retorna taxa que causou 429

                time.sleep(delay)

            except Exception as e:
                print(f"❌ Erro na requisição {i}: {e}")
                results['requests'].append({
                    'index': i,
                    'error': str(e)
                })

        print(f"✅ Taxa {rate} req/min: Sem HTTP 429")

        # Salvar dados mesmo sem 429
        output_path = Path(__file__).parent.parent.parent / 'data' / 'diagnostics' / f'rate_limit_discovery_{rate}rpm.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        # Pausa entre taxas para não saturar
        print("⏸️  Aguardando 60s antes da próxima taxa...")
        time.sleep(60)

    print("\n✅ Nenhuma taxa testada causou HTTP 429!")
    print("   Conclusão: Limite > 300 req/min ou não existe")
    return None

if __name__ == '__main__':
    limite = test_rate_limit()
    if limite:
        print(f"\n🎯 LIMITE DESCOBERTO: ~{limite} req/min")
    else:
        print(f"\n🎯 LIMITE: > 300 req/min (ou inexistente)")
