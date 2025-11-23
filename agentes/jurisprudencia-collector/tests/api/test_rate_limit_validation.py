#!/usr/bin/env python3
"""
Validação de Rate Limiting Otimizado - 180 req/min

Testa que o sistema consegue sustentar 180 req/min (15 req/5s)
sem ultrapassar limites da API e sem ser excessivamente conservador.

Autor: Legal-Braniac (Orquestrador)
Data: 2025-11-22
"""
import time
import sys
from pathlib import Path

# Adicionar src/ ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from downloader import DJENDownloader


def test_rate_limit_180rpm():
    """
    Testa que sistema consegue sustentar 180 req/min.

    Executa 60 requisições simuladas e verifica que:
    1. Tempo total está dentro do esperado (~20-25s)
    2. Rate limiting não é muito lento (> 25s = muito conservador)
    3. Rate limiting não é muito rápido (< 18s = risco de HTTP 429)
    """
    print("=" * 80)
    print("TESTE DE VALIDAÇÃO: Rate Limiting 180 req/min")
    print("=" * 80)

    # Criar downloader com rate limiting adaptativo
    downloader = DJENDownloader(
        data_root=Path('/tmp/test_jurisprudencia'),
        requests_per_minute=180,
        adaptive_rate_limit=True,
        max_retries=3
    )

    print(f"Configuração:")
    print(f"  - Window size: {downloader.request_window_size} req")
    print(f"  - Window duration: {downloader.request_window_duration}s")
    print(f"  - Expected rate: {(downloader.request_window_size / downloader.request_window_duration) * 60:.0f} req/min")
    print()

    # Executar 60 chamadas ao rate limiter
    num_requests = 60
    print(f"Executando {num_requests} requisições simuladas...")

    start = time.time()

    for i in range(1, num_requests + 1):
        downloader._check_rate_limit()

        # Mostrar progresso a cada 15 requisições
        if i % 15 == 0:
            elapsed = time.time() - start
            current_rate = (i / elapsed) * 60
            print(f"  [{i}/{num_requests}] {elapsed:.1f}s decorridos, taxa atual: {current_rate:.0f} req/min")

    elapsed = time.time() - start
    actual_rate = (num_requests / elapsed) * 60

    print()
    print("=" * 80)
    print("RESULTADOS")
    print("=" * 80)
    print(f"Requisições: {num_requests}")
    print(f"Tempo total: {elapsed:.2f}s")
    print(f"Taxa efetiva: {actual_rate:.1f} req/min")
    print()

    # Validações
    # Com 15 req/5s, 60 requisições devem levar ~20s (4 janelas de 5s)
    # Permitir margem de ±3s para overhead de processamento
    min_expected_time = 18.0  # 60 req / 200 req/min = ~18s (limite superior)
    max_expected_time = 25.0  # 60 req / 144 req/min = ~25s (limite inferior)

    print("VALIDAÇÕES:")

    # Validação 1: Não muito rápido (risco de HTTP 429)
    if elapsed < min_expected_time:
        print(f"  ❌ MUITO RÁPIDO: {elapsed:.1f}s < {min_expected_time}s")
        print(f"     Risco de HTTP 429! Taxa: {actual_rate:.0f} req/min")
        result = False
    else:
        print(f"  ✅ Velocidade OK: {elapsed:.1f}s >= {min_expected_time}s (sem risco de 429)")

    # Validação 2: Não muito lento (muito conservador)
    if elapsed > max_expected_time:
        print(f"  ⚠️  MUITO LENTO: {elapsed:.1f}s > {max_expected_time}s")
        print(f"     Taxa: {actual_rate:.0f} req/min (muito conservador)")
        result = False
    else:
        print(f"  ✅ Eficiência OK: {elapsed:.1f}s <= {max_expected_time}s")

    # Validação 3: Taxa próxima ao esperado (180 req/min ± 10%)
    expected_rate = 180
    tolerance = 0.10  # 10%
    min_rate = expected_rate * (1 - tolerance)
    max_rate = expected_rate * (1 + tolerance)

    if min_rate <= actual_rate <= max_rate:
        print(f"  ✅ Taxa dentro da margem: {actual_rate:.0f} req/min ({expected_rate} ± {tolerance*100:.0f}%)")
        result = True
    else:
        print(f"  ❌ Taxa fora da margem: {actual_rate:.0f} req/min (esperado: {min_rate:.0f}-{max_rate:.0f})")
        result = False

    print()

    if result:
        print("🎉 TESTE PASSOU - Rate limiting otimizado funcionando corretamente!")
    else:
        print("❌ TESTE FALHOU - Ajustes necessários no rate limiting")

    print("=" * 80)

    return result


def test_window_reset():
    """
    Testa que a janela de rate limiting reseta corretamente.
    """
    print("\n" + "=" * 80)
    print("TESTE DE VALIDAÇÃO: Window Reset")
    print("=" * 80)

    downloader = DJENDownloader(
        data_root=Path('/tmp/test_jurisprudencia'),
        requests_per_minute=180,
        adaptive_rate_limit=True
    )

    window_size = downloader.request_window_size
    window_duration = downloader.request_window_duration

    print(f"Window config: {window_size} req / {window_duration}s")
    print()

    # Fase 1: Esgotar janela
    print("Fase 1: Esgotando janela...")
    start = time.time()

    for i in range(window_size):
        downloader._check_rate_limit()

    phase1_elapsed = time.time() - start
    print(f"  {window_size} requisições em {phase1_elapsed:.2f}s")

    # Fase 2: Verificar que request_count foi resetado
    print("Fase 2: Verificando reset de contadores...")

    # Se janela resetou corretamente, request_count deve estar em 0
    # e window_start deve ter sido atualizado
    if downloader.request_count == 0:
        print(f"  ✅ Counter reset OK: request_count = {downloader.request_count}")
        result = True
    else:
        print(f"  ❌ Counter NOT reset: request_count = {downloader.request_count} (esperado: 0)")
        result = False

    # Verificar que window_start foi atualizado (deve estar próximo ao tempo atual)
    time_since_reset = time.time() - downloader.window_start
    if time_since_reset < 1.0:  # Resetado há menos de 1s
        print(f"  ✅ Window timestamp OK: resetado há {time_since_reset:.2f}s")
    else:
        print(f"  ⚠️  Window timestamp antigo: resetado há {time_since_reset:.2f}s")
        result = False

    print("=" * 80)

    return result


if __name__ == '__main__':
    print("\n🧪 TESTES DE VALIDAÇÃO - RATE LIMITING OTIMIZADO")
    print("=" * 80)
    print()

    results = []

    # Teste 1: Taxa 180 req/min
    try:
        result1 = test_rate_limit_180rpm()
        results.append(("Rate Limit 180rpm", result1))
    except Exception as e:
        print(f"❌ ERRO no teste 1: {e}")
        results.append(("Rate Limit 180rpm", False))

    # Teste 2: Window reset
    try:
        result2 = test_window_reset()
        results.append(("Window Reset", result2))
    except Exception as e:
        print(f"❌ ERRO no teste 2: {e}")
        results.append(("Window Reset", False))

    # Relatório final
    print("\n" + "=" * 80)
    print("RELATÓRIO FINAL")
    print("=" * 80)

    for test_name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{status} - {test_name}")

    all_passed = all(result for _, result in results)

    print()
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        sys.exit(1)
