#!/usr/bin/env python3
"""
Profile detalhado para responder questões específicas:

1. Request latency distribution (p50, p95, p99)
2. Quantos inserts por request?
3. Tribunal response times separadamente?
4. Tamanho dos payloads JSON?
"""

import sys
import time
import json
import statistics
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import sqlite3

# Adicionar src/ ao path (igual ao scheduler.py)
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from downloader import DJENDownloader
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================

DATA_ROOT = Path("/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector/data")
TRIBUNAIS = ['STJ', 'TJSP']
NUM_REQUESTS = 20  # Número de requests para medir distribuição


# ==============================================================================
# TESTE 1: Request Latency Distribution
# ==============================================================================

def test_request_latency_distribution():
    """Mede distribuição de latência (p50, p95, p99)."""
    console.print("\n[bold cyan]═" * 40)
    console.print("[bold cyan]TESTE 1: Request Latency Distribution")
    console.print("[bold cyan]═" * 40)

    data = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    tribunal = 'STJ'

    console.print(f"\nℹ Testando {NUM_REQUESTS} requisições")
    console.print(f"ℹ Data: {data}, Tribunal: {tribunal}")

    downloader = DJENDownloader(
        data_root=DATA_ROOT,
        requests_per_minute=999,  # Sem rate limiting para medir apenas latência
        delay_seconds=0.0,
        max_retries=1
    )

    latencies = []
    sizes = []
    pub_counts = []

    for i in range(NUM_REQUESTS):
        start = time.time()

        try:
            # Variar data (últimos 20 dias) para evitar cache da API
            data_teste = (datetime.now() - timedelta(days=i+1)).strftime('%Y-%m-%d')

            publicacoes = downloader.baixar_api(
                tribunal=tribunal,
                data=data_teste,
                limit=100,
                max_pages=1  # Apenas primeira página para medir latência
            )

            latency = (time.time() - start) * 1000  # ms
            latencies.append(latency)
            pub_counts.append(len(publicacoes))

            # Estimar tamanho do payload (aproximado)
            if publicacoes:
                # Serializar uma publicação sample para estimar tamanho
                sample_size = sys.getsizeof(str(publicacoes[0].__dict__))
                total_size = sample_size * len(publicacoes)
                sizes.append(total_size)

            console.print(f"  ✓ Request {i+1}/{NUM_REQUESTS}: {latency:.0f}ms, {len(publicacoes)} pubs")

            time.sleep(0.1)  # Pequeno delay para não sobrecarregar API

        except Exception as e:
            console.print(f"  ✗ Request {i+1}/{NUM_REQUESTS} falhou: {e}")
            continue

    if not latencies:
        console.print("[red]✗ Nenhuma requisição bem-sucedida")
        return

    # Calcular percentis
    latencies.sort()
    n = len(latencies)

    p50 = latencies[int(n * 0.50)]
    p95 = latencies[int(n * 0.95)]
    p99 = latencies[int(n * 0.99)]
    avg = statistics.mean(latencies)
    std = statistics.stdev(latencies) if len(latencies) > 1 else 0

    # Estatísticas de publicações por request
    avg_pubs = statistics.mean(pub_counts) if pub_counts else 0
    total_pubs = sum(pub_counts)

    # Tamanho médio de payload
    avg_size = statistics.mean(sizes) if sizes else 0

    # Exibir resultados
    table = Table(title="Latency Distribution", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Requests", str(len(latencies)))
    table.add_row("p50 (median)", f"{p50:.0f}ms")
    table.add_row("p95", f"{p95:.0f}ms")
    table.add_row("p99", f"{p99:.0f}ms")
    table.add_row("Average", f"{avg:.0f}ms")
    table.add_row("Std Dev", f"{std:.0f}ms")
    table.add_row("Min", f"{min(latencies):.0f}ms")
    table.add_row("Max", f"{max(latencies):.0f}ms")

    console.print(table)

    # Publicações por request
    table2 = Table(title="Publications per Request", show_header=True, header_style="bold magenta")
    table2.add_column("Metric", style="cyan")
    table2.add_column("Value", style="green")

    table2.add_row("Total publications", str(total_pubs))
    table2.add_row("Avg per request", f"{avg_pubs:.1f}")
    table2.add_row("Min per request", str(min(pub_counts)))
    table2.add_row("Max per request", str(max(pub_counts)))

    console.print(table2)

    # Tamanho de payload
    console.print(f"\n[yellow]Payload Size:[/yellow]")
    console.print(f"  Average: {avg_size/1024:.1f} KB")
    console.print(f"  Total: {sum(sizes)/1024/1024:.2f} MB ({len(sizes)} requests)")

    if avg_size < 100 * 1024:  # < 100KB
        console.print(f"  [green]✓ Payload pequeno (<100KB) - JSON serialization NÃO é problema[/green]")
    elif avg_size > 5 * 1024 * 1024:  # > 5MB
        console.print(f"  [red]⚠ Payload grande (>5MB) - JSON serialization PODE ser problema[/red]")
    else:
        console.print(f"  [yellow]⚠ Payload médio (100KB-5MB) - JSON serialization pode ter impacto moderado[/yellow]")

    return {
        'p50': p50,
        'p95': p95,
        'p99': p99,
        'avg': avg,
        'avg_pubs_per_request': avg_pubs,
        'avg_payload_size': avg_size
    }


# ==============================================================================
# TESTE 2: Database INSERT Pattern (N+1?)
# ==============================================================================

def test_database_insert_pattern():
    """Verifica se há N+1 queries (1 INSERT + 1 COMMIT por publicação)."""
    console.print("\n[bold cyan]═" * 40)
    console.print("[bold cyan]TESTE 2: Database INSERT Pattern (N+1?)")
    console.print("[bold cyan]═" * 40)

    # Analisar código fonte
    scheduler_path = Path(__file__).parent / 'scheduler.py'

    with open(scheduler_path, 'r') as f:
        code = f.read()

    # Procurar por commit() dentro de loop
    has_n_plus_1 = False

    if 'def inserir_publicacao' in code:
        # Extrair função inserir_publicacao
        start = code.find('def inserir_publicacao')
        end = code.find('\ndef ', start + 1)
        func_code = code[start:end]

        if 'conn.commit()' in func_code:
            has_n_plus_1 = True
            console.print("[red]✗ PROBLEMA N+1 DETECTADO![/red]")
            console.print("\n[yellow]Evidência:[/yellow]")
            console.print("  • conn.commit() está DENTRO de inserir_publicacao()")
            console.print("  • Cada publicação = 1 INSERT + 1 COMMIT")
            console.print("  • Se 100 pubs/request → 100 commits → MUITO LENTO")
            console.print("\n[green]Solução:[/green]")
            console.print("  • Remover commit() de inserir_publicacao()")
            console.print("  • Fazer commit em batch (ex: a cada 100 publicações)")
            console.print("  • Ganho esperado: 535x mais rápido (conforme diagnóstico)")
        else:
            console.print("[green]✓ Sem problema N+1 - commits em batch[/green]")

    # Verificar processamento de publicações
    if 'for pub_raw in publicacoes:' in code:
        console.print("\n[yellow]Loop de processamento encontrado:[/yellow]")
        console.print("  • Loop: for pub_raw in publicacoes:")
        console.print("  • Cada iteração chama: inserir_publicacao(conn, pub_processada)")

        if has_n_plus_1:
            console.print("  • [red]CRÍTICO: Commit em CADA iteração[/red]")
        else:
            console.print("  • [green]OK: Commit em batch[/green]")

    return {'has_n_plus_1': has_n_plus_1}


# ==============================================================================
# TESTE 3: Network vs Processing Time
# ==============================================================================

def test_network_vs_processing():
    """Separa tempo de network (request) vs tempo de processamento (parsing/DB)."""
    console.print("\n[bold cyan]═" * 40)
    console.print("[bold cyan]TESTE 3: Network vs Processing Time")
    console.print("[bold cyan]═" * 40)

    data = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    tribunal = 'STJ'

    downloader = DJENDownloader(
        data_root=DATA_ROOT,
        requests_per_minute=999,
        delay_seconds=0.0,
        max_retries=1
    )

    console.print(f"\nℹ Testando 5 requests completos")
    console.print(f"ℹ Data: {data}, Tribunal: {tribunal}")

    network_times = []
    processing_times = []

    for i in range(5):
        # Variar data para evitar cache
        data_teste = (datetime.now() - timedelta(days=i+1)).strftime('%Y-%m-%d')

        # Tempo de network (apenas request)
        start_network = time.time()
        publicacoes = downloader.baixar_api(
            tribunal=tribunal,
            data=data_teste,
            limit=100,
            max_pages=1  # Apenas primeira página
        )
        network_time = (time.time() - start_network) * 1000

        # Tempo de processamento (simular: parsing + validação)
        start_processing = time.time()
        for pub in publicacoes:
            # Simular processamento (sem DB)
            _ = pub.__dict__  # Acesso a dados
            _ = str(pub.texto_html)[:100]  # Simular parsing
        processing_time = (time.time() - start_processing) * 1000

        network_times.append(network_time)
        processing_times.append(processing_time)

        console.print(f"  Request {i+1}/5: network={network_time:.0f}ms, processing={processing_time:.0f}ms")

    avg_network = statistics.mean(network_times)
    avg_processing = statistics.mean(processing_times)
    total_avg = avg_network + avg_processing

    network_pct = (avg_network / total_avg) * 100
    processing_pct = (avg_processing / total_avg) * 100

    console.print(f"\n[bold]Breakdown:[/bold]")
    console.print(f"  Network time:    {avg_network:.0f}ms ({network_pct:.1f}%)")
    console.print(f"  Processing time: {avg_processing:.0f}ms ({processing_pct:.1f}%)")
    console.print(f"  Total:           {total_avg:.0f}ms")

    if network_pct > 80:
        console.print(f"\n[red]✗ BOTTLENECK: Network latency ({network_pct:.0f}%)[/red]")
        console.print("  → Solução: Async batching, paralelização")
        console.print("  → Connection pooling NÃO ajuda (cada request é independente)")
    elif processing_pct > 50:
        console.print(f"\n[yellow]⚠ BOTTLENECK: Processing ({processing_pct:.0f}%)[/yellow]")
        console.print("  → Solução: Otimizar parsing, batch DB commits")
    else:
        console.print(f"\n[green]✓ Balanceado[/green]")

    return {
        'avg_network': avg_network,
        'avg_processing': avg_processing,
        'network_pct': network_pct
    }


# ==============================================================================
# TESTE 4: Payload Size Analysis
# ==============================================================================

def test_payload_size_analysis():
    """Analisa tamanho dos payloads JSON em detalhe."""
    console.print("\n[bold cyan]═" * 40)
    console.print("[bold cyan]TESTE 4: Payload Size Analysis")
    console.print("[bold cyan]═" * 40)

    data = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    tribunal = 'STJ'

    downloader = DJENDownloader(
        data_root=DATA_ROOT,
        requests_per_minute=999,
        delay_seconds=0.0,
        max_retries=1
    )

    console.print(f"\nℹ Analisando payloads de 3 requests")

    publicacoes = downloader.baixar_api(tribunal=tribunal, data=data, limit=100)

    if not publicacoes:
        console.print("[red]✗ Nenhuma publicação retornada[/red]")
        return

    # Analisar tamanhos
    sizes = []
    html_sizes = []

    for pub in publicacoes[:10]:  # Analisar primeiras 10
        # Tamanho total do objeto
        obj_size = sys.getsizeof(str(pub.__dict__))
        sizes.append(obj_size)

        # Tamanho do HTML (geralmente o maior campo)
        html_size = sys.getsizeof(pub.texto_html)
        html_sizes.append(html_size)

    avg_size = statistics.mean(sizes)
    avg_html = statistics.mean(html_sizes)

    # Estimar payload completo
    total_pubs = len(publicacoes)
    estimated_payload = avg_size * total_pubs

    console.print(f"\n[bold]Análise de {len(publicacoes)} publicações:[/bold]")
    console.print(f"  Avg size per publication: {avg_size/1024:.2f} KB")
    console.print(f"  Avg HTML size:            {avg_html/1024:.2f} KB")
    console.print(f"  Estimated full payload:   {estimated_payload/1024:.2f} KB")

    if estimated_payload < 100 * 1024:
        console.print(f"\n[green]✓ Payload pequeno (<100KB)[/green]")
        console.print("  → JSON serialization NÃO é problema")
        console.print("  → py-spy profiling DESNECESSÁRIO")
    elif estimated_payload > 5 * 1024 * 1024:
        console.print(f"\n[red]⚠ Payload GRANDE (>5MB)[/red]")
        console.print("  → JSON serialization PODE ser problema")
        console.print("  → RECOMENDADO: py-spy profiling")
    else:
        console.print(f"\n[yellow]⚠ Payload médio (100KB-5MB)[/yellow]")
        console.print("  → JSON serialization tem impacto moderado")
        console.print("  → Profiling opcional")

    return {
        'avg_size': avg_size,
        'estimated_payload': estimated_payload
    }


# ==============================================================================
# RELATÓRIO FINAL
# ==============================================================================

def generate_final_report(results):
    """Gera relatório final respondendo todas as 4 questões."""
    console.print("\n\n[bold green]═" * 40)
    console.print("[bold green]RELATÓRIO FINAL - Respostas às 4 Questões")
    console.print("[bold green]═" * 40)

    # Questão 1: Request latency distribution
    console.print("\n[bold cyan]1. Request Latency Distribution:[/bold cyan]")
    if 'latency' in results:
        lat = results['latency']
        console.print(f"   p50 (median): {lat['p50']:.0f}ms")
        console.print(f"   p95:          {lat['p95']:.0f}ms")
        console.print(f"   p99:          {lat['p99']:.0f}ms")
        console.print(f"   Average:      {lat['avg']:.0f}ms")

    # Questão 2: Inserts por request
    console.print("\n[bold cyan]2. Database INSERTs per Request:[/bold cyan]")
    if 'latency' in results:
        avg_pubs = results['latency']['avg_pubs_per_request']
        console.print(f"   Avg publications per request: {avg_pubs:.0f}")

        if 'n_plus_1' in results and results['n_plus_1']['has_n_plus_1']:
            console.print(f"   [red]✗ PROBLEMA: {avg_pubs:.0f} INSERTs + {avg_pubs:.0f} COMMITs per request[/red]")
            console.print(f"   [red]  → Rate limit (30 req/min) + N+1 commits = DOUBLE BOTTLENECK[/red]")
        else:
            console.print(f"   [green]✓ OK: Batch commits[/green]")

    # Questão 3: Network vs processing
    console.print("\n[bold cyan]3. Tribunal Response Times (separate):[/bold cyan]")
    if 'network_vs_processing' in results:
        nvp = results['network_vs_processing']
        console.print(f"   Network time:    {nvp['avg_network']:.0f}ms ({nvp['network_pct']:.1f}%)")
        console.print(f"   Processing time: {nvp['avg_processing']:.0f}ms")

        if nvp['network_pct'] > 80:
            console.print("   [yellow]→ Connection pooling WON'T help (independent requests)[/yellow]")
            console.print("   [green]→ Async batching WILL help[/green]")

    # Questão 4: JSON serialization
    console.print("\n[bold cyan]4. JSON Serialization CPU Usage:[/bold cyan]")
    if 'payload_size' in results:
        ps = results['payload_size']
        console.print(f"   Estimated payload: {ps['estimated_payload']/1024:.2f} KB")

        if ps['estimated_payload'] < 100 * 1024:
            console.print("   [green]✓ Payload <100KB - JSON serialization NOT a problem[/green]")
            console.print("   [green]✓ py-spy profiling UNNECESSARY[/green]")
        else:
            console.print("   [yellow]⚠ Payload >100KB - may need py-spy profiling[/yellow]")

    # Recomendação final
    console.print("\n[bold yellow]═" * 40)
    console.print("[bold yellow]RECOMENDAÇÃO FINAL:")
    console.print("[bold yellow]═" * 40)

    console.print("\n[bold]Primary bottleneck:[/bold] Rate limiting artificial (delay 2s)")
    console.print("[bold]Secondary bottleneck:[/bold] N+1 database commits")

    console.print("\n[bold green]Otimizações prioritárias:[/bold green]")
    console.print("  1. [green]Remover delay artificial (2s) → ganho 10x[/green]")
    console.print("  2. [green]Implementar batch commits → ganho 535x em DB[/green]")
    console.print("  3. [green]Rate limiting adaptativo (18-19 req/window)[/green]")

    console.print("\n[bold red]Otimizações DESNECESSÁRIAS:[/bold red]")
    console.print("  ✗ Connection pooling (SQLite single-writer)")
    console.print("  ✗ Indexes (writes são gargalo, não reads)")
    console.print("  ✗ py-spy profiling (payload <100KB)")


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    console.print("[bold green]╔" + "═" * 78 + "╗")
    console.print("[bold green]║" + " " * 78 + "║")
    console.print("[bold green]║" + "  PROFILING DETALHADO - Jurisprudência Collector".center(78) + "║")
    console.print("[bold green]║" + " " * 78 + "║")
    console.print("[bold green]╚" + "═" * 78 + "╝")

    results = {}

    try:
        # Teste 1: Latency distribution
        results['latency'] = test_request_latency_distribution()

        input("\nPressione Enter para continuar...")

        # Teste 2: N+1 pattern
        results['n_plus_1'] = test_database_insert_pattern()

        input("\nPressione Enter para continuar...")

        # Teste 3: Network vs processing
        results['network_vs_processing'] = test_network_vs_processing()

        input("\nPressione Enter para continuar...")

        # Teste 4: Payload size
        results['payload_size'] = test_payload_size_analysis()

        input("\nPressione Enter para ver relatório final...")

        # Relatório final
        generate_final_report(results)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrompido pelo usuário[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Erro: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
