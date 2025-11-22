#!/usr/bin/env python3
"""
Diagnóstico de Performance - Encontrar o Gargalo Real

Mede:
1. Latência da API (sem delay artificial)
2. Tempo de parsing HTML
3. Tempo de inserção no DB
4. Limite de rate da API

Uso:
    python diagnostico_performance.py
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import requests
from statistics import mean, stdev
import sqlite3

# Adicionar src/ ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Cores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_success(msg):
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ {msg}{Colors.ENDC}")

# ==============================================================================
# TESTE 1: Latência da API (sem delay)
# ==============================================================================

def test_api_latency():
    """Mede latência pura da API sem rate limiting."""
    print_header("TESTE 1: Latência da API DJEN")

    api_url = "https://comunicaapi.pje.jus.br/api/v1"
    data_teste = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    print_info(f"Testando com data: {data_teste}")
    print_info(f"Tribunal: STJ")
    print_info(f"Requisições: 10 (para calcular média)")

    latencies = []
    errors = 0

    for i in range(10):
        try:
            start = time.time()

            response = requests.get(
                f"{api_url}/comunicacao",
                params={
                    'siglaTribunal': 'STJ',
                    'dataDisponibilizacao': data_teste,
                    'limit': 100,
                    'offset': i * 100
                },
                timeout=30
            )

            end = time.time()
            latency = (end - start) * 1000  # ms

            latencies.append(latency)

            status_emoji = "✓" if response.status_code == 200 else "✗"
            print(f"  {status_emoji} Requisição {i+1}/10: {latency:.0f}ms (status {response.status_code})")

            if response.status_code == 429:
                print_warning(f"HTTP 429 (Too Many Requests) na requisição {i+1}!")
                print_warning(f"Limite de rate atingido após {i+1} requisições em ~{sum(latencies)/1000:.1f}s")
                break

        except Exception as e:
            errors += 1
            print(f"  ✗ Erro na requisição {i+1}: {e}")

        # Pequeno delay para não saturar (0.1s)
        time.sleep(0.1)

    if latencies:
        print(f"\n{Colors.BOLD}Resultados:{Colors.ENDC}")
        print(f"  Mínimo:    {min(latencies):.0f}ms")
        print(f"  Média:     {mean(latencies):.0f}ms")
        print(f"  Máximo:    {max(latencies):.0f}ms")
        if len(latencies) > 1:
            print(f"  Desvio:    {stdev(latencies):.0f}ms")
        print(f"  Erros:     {errors}/10")

        # Calcular taxa máxima teórica
        avg_latency_s = mean(latencies) / 1000
        max_req_per_sec = 1 / avg_latency_s
        max_req_per_min = max_req_per_sec * 60

        print(f"\n{Colors.BOLD}Taxa máxima teórica (sem delay):{Colors.ENDC}")
        print(f"  {max_req_per_sec:.1f} req/sec")
        print(f"  {max_req_per_min:.0f} req/min")

        # Comparar com taxa atual (delay de 2s)
        current_rate = 30  # req/min
        speedup = max_req_per_min / current_rate
        print(f"\n{Colors.BOLD}Comparação:{Colors.ENDC}")
        print(f"  Taxa atual (delay 2s):  {current_rate} req/min")
        print(f"  Taxa teórica máxima:    {max_req_per_min:.0f} req/min")
        print(f"  Ganho potencial:        {speedup:.1f}x mais rápido")

        return {
            'min_latency': min(latencies),
            'avg_latency': mean(latencies),
            'max_latency': max(latencies),
            'max_req_per_min': max_req_per_min,
            'speedup': speedup
        }
    else:
        print_warning("Nenhuma latência válida medida")
        return None


# ==============================================================================
# TESTE 2: Parsing HTML (BeautifulSoup)
# ==============================================================================

def test_html_parsing():
    """Mede tempo de parsing HTML."""
    print_header("TESTE 2: Performance de Parsing HTML")

    from bs4 import BeautifulSoup

    # Simular HTML de publicação (exemplo real do STJ)
    sample_html = """
    <div class="publicacao">
        <p><strong>EMENTA:</strong> AGRAVO INTERNO NO RECURSO ESPECIAL. TRIBUTÁRIO.
        ICMS. BASE DE CÁLCULO. INCLUSÃO DO VALOR DO FRETE. POSSIBILIDADE.</p>
        <p><strong>ACÓRDÃO:</strong> Vistos e relatados estes autos...</p>
        <p><strong>RELATÓRIO:</strong> O EXMO. SR. MINISTRO RELATOR...</p>
    </div>
    """ * 100  # Simular 100 publicações

    print_info(f"Testando parsing de {len(sample_html)} bytes de HTML")
    print_info("Iterações: 100")

    parsing_times = []

    for i in range(100):
        start = time.time()
        soup = BeautifulSoup(sample_html, 'html.parser')
        text = soup.get_text()
        end = time.time()

        parsing_times.append((end - start) * 1000)  # ms

    print(f"\n{Colors.BOLD}Resultados:{Colors.ENDC}")
    print(f"  Mínimo:    {min(parsing_times):.2f}ms")
    print(f"  Média:     {mean(parsing_times):.2f}ms")
    print(f"  Máximo:    {max(parsing_times):.2f}ms")

    if mean(parsing_times) < 10:
        print_success("Parsing é rápido (<10ms) - NÃO é o gargalo")
    else:
        print_warning(f"Parsing relativamente lento ({mean(parsing_times):.2f}ms)")

    return mean(parsing_times)


# ==============================================================================
# TESTE 3: Database Writes (SQLite)
# ==============================================================================

def test_database_writes():
    """Mede throughput de writes no SQLite."""
    print_header("TESTE 3: Performance de Database Writes (SQLite)")

    db_path = Path(__file__).parent / 'test_performance.db'
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Criar tabela (simulando estrutura real)
    cursor.execute("""
        CREATE TABLE publicacoes (
            id TEXT PRIMARY KEY,
            hash_conteudo TEXT,
            numero_processo TEXT,
            tribunal TEXT,
            tipo_publicacao TEXT,
            texto_html TEXT,
            data_publicacao TEXT
        )
    """)
    conn.commit()

    print_info("Testando inserção de 1000 registros")

    # Teste 1: Writes sequenciais (um por vez)
    start = time.time()
    for i in range(1000):
        cursor.execute("""
            INSERT INTO publicacoes VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f'id-{i}',
            f'hash-{i}',
            f'proc-{i}',
            'STJ',
            'Acórdão',
            '<p>Texto HTML aqui...</p>' * 10,
            '2025-11-21'
        ))
        conn.commit()
    end = time.time()

    time_sequential = end - start
    rate_sequential = 1000 / time_sequential

    print(f"\n{Colors.BOLD}Writes Sequenciais (commit a cada insert):{Colors.ENDC}")
    print(f"  Tempo total:   {time_sequential:.2f}s")
    print(f"  Taxa:          {rate_sequential:.0f} writes/sec")

    # Limpar tabela
    cursor.execute("DELETE FROM publicacoes")

    # Teste 2: Batch writes (commit no final)
    start = time.time()
    for i in range(1000):
        cursor.execute("""
            INSERT INTO publicacoes VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f'id-{i}',
            f'hash-{i}',
            f'proc-{i}',
            'STJ',
            'Acórdão',
            '<p>Texto HTML aqui...</p>' * 10,
            '2025-11-21'
        ))
    conn.commit()
    end = time.time()

    time_batch = end - start
    rate_batch = 1000 / time_batch

    print(f"\n{Colors.BOLD}Batch Writes (commit no final):{Colors.ENDC}")
    print(f"  Tempo total:   {time_batch:.2f}s")
    print(f"  Taxa:          {rate_batch:.0f} writes/sec")
    print(f"  Speedup:       {rate_batch/rate_sequential:.1f}x mais rápido")

    conn.close()
    db_path.unlink()

    if rate_sequential > 100:
        print_success("DB é rápido (>100 writes/sec) - NÃO é o gargalo")
    else:
        print_warning(f"DB pode ser gargalo ({rate_sequential:.0f} writes/sec)")

    return {
        'sequential_rate': rate_sequential,
        'batch_rate': rate_batch,
        'speedup': rate_batch / rate_sequential
    }


# ==============================================================================
# TESTE 4: Teste de Rate Limit da API
# ==============================================================================

def test_rate_limit():
    """Testa limite de requisições da API até receber 429."""
    print_header("TESTE 4: Limite de Rate da API")

    print_warning("Este teste envia requisições rápidas até encontrar o limite")
    confirm = input("Continuar? (s/N): ")
    if confirm.lower() != 's':
        print_info("Teste pulado")
        return None

    api_url = "https://comunicaapi.pje.jus.br/api/v1"
    data_teste = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    print_info("Enviando requisições sem delay até receber HTTP 429...")

    start_time = time.time()
    request_count = 0
    got_429 = False

    while not got_429 and request_count < 200:  # Limite de segurança
        try:
            response = requests.get(
                f"{api_url}/comunicacao",
                params={
                    'siglaTribunal': 'STJ',
                    'dataDisponibilizacao': data_teste,
                    'limit': 10,
                    'offset': 0
                },
                timeout=5
            )

            request_count += 1

            if response.status_code == 429:
                got_429 = True
                elapsed = time.time() - start_time
                print_warning(f"\nHTTP 429 recebido após {request_count} requisições em {elapsed:.1f}s")
                print(f"  Taxa: {request_count/elapsed:.1f} req/sec")
                print(f"  Taxa: {(request_count/elapsed)*60:.0f} req/min")

                # Verificar headers de rate limit
                if 'Retry-After' in response.headers:
                    print(f"  Retry-After: {response.headers['Retry-After']}s")
                if 'X-RateLimit-Limit' in response.headers:
                    print(f"  Rate Limit: {response.headers['X-RateLimit-Limit']}")

                return {
                    'limit_req_count': request_count,
                    'limit_time': elapsed,
                    'limit_rate_per_sec': request_count / elapsed,
                    'limit_rate_per_min': (request_count / elapsed) * 60
                }

            if request_count % 10 == 0:
                print(f"  {request_count} requisições... (status {response.status_code})")

        except Exception as e:
            print(f"  Erro: {e}")
            break

    if not got_429:
        print_success(f"Não atingiu limite após {request_count} requisições")
        print_info("API pode não ter rate limiting rígido, ou limite é muito alto")

    return None


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Executa todos os testes de diagnóstico."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║           DIAGNÓSTICO DE PERFORMANCE - Jurisprudência Collector             ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")

    results = {}

    # Teste 1: Latência da API
    results['api'] = test_api_latency()
    input("\nPressione Enter para continuar...")

    # Teste 2: Parsing HTML
    results['parsing'] = test_html_parsing()
    input("\nPressione Enter para continuar...")

    # Teste 3: Database
    results['db'] = test_database_writes()
    input("\nPressione Enter para continuar...")

    # Teste 4: Rate Limit (opcional)
    results['rate_limit'] = test_rate_limit()

    # Relatório final
    print_header("RELATÓRIO FINAL - Identificação do Gargalo")

    if results['api']:
        print(f"{Colors.BOLD}1. API Latency:{Colors.ENDC}")
        print(f"   Média: {results['api']['avg_latency']:.0f}ms")
        print(f"   Taxa teórica máxima: {results['api']['max_req_per_min']:.0f} req/min")
        print(f"   Ganho vs atual: {results['api']['speedup']:.1f}x\n")

    print(f"{Colors.BOLD}2. HTML Parsing:{Colors.ENDC}")
    print(f"   Média: {results['parsing']:.2f}ms")
    print(f"   Impacto: {'Baixo' if results['parsing'] < 10 else 'Médio'}\n")

    if results['db']:
        print(f"{Colors.BOLD}3. Database Writes:{Colors.ENDC}")
        print(f"   Taxa sequencial: {results['db']['sequential_rate']:.0f} writes/sec")
        print(f"   Taxa batch: {results['db']['batch_rate']:.0f} writes/sec")
        print(f"   Speedup batch: {results['db']['speedup']:.1f}x\n")

    if results['rate_limit']:
        print(f"{Colors.BOLD}4. Rate Limit da API:{Colors.ENDC}")
        print(f"   Limite: {results['rate_limit']['limit_rate_per_min']:.0f} req/min")

    print(f"\n{Colors.BOLD}CONCLUSÃO:{Colors.ENDC}")
    if results['api'] and results['api']['speedup'] > 10:
        print_success(f"Gargalo principal: RATE LIMITING ARTIFICIAL (delay de 2s)")
        print_success(f"Solução: Reduzir delay e testar limite real da API")
        print_success(f"Ganho estimado: {results['api']['speedup']:.1f}x mais rápido")
    else:
        print_info("Gargalo: Precisa de mais análise")

    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Diagnóstico interrompido{Colors.ENDC}\n")
        sys.exit(1)
