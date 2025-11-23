#!/usr/bin/env python3
"""
CLI para STJ Dados Abertos
===========================

Interface de linha de comando para gerenciar dados do STJ.

Comandos disponíveis:
- validate-setup: Valida configuração híbrida
- stats: Mostra estatísticas do database
- search: Busca acórdãos
- download: Download de dados do STJ
- integrity-check: Valida integridade do database
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from typing import Optional
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent))

from config import (
    validar_configuracao_hibrida,
    get_storage_info,
    INDEX_PATH,
    DATA_ROOT
)
from src.database import STJDatabase


app = typer.Typer(
    name="stj",
    help="CLI para gerenciar dados do STJ Dados Abertos",
    add_completion=False
)
console = Console()


@app.command("validate-setup")
def validate_setup():
    """
    Valida configuração híbrida (SSD + HD).

    Verificações:
    - Diretórios existem e são acessíveis
    - Espaço em disco disponível
    - Permissões de leitura/escrita
    """
    console.print("\n[bold cyan]🔍 Validando Configuração Híbrida[/bold cyan]\n")

    # Executar validação
    is_valid = validar_configuracao_hibrida()

    # Mostrar info detalhada
    storage_info = get_storage_info()

    # Tabela de status
    table = Table(title="Status do Armazenamento")
    table.add_column("Camada", style="cyan")
    table.add_column("Path", style="yellow")
    table.add_column("Espaço Livre", style="green")
    table.add_column("Espaço Usado", style="blue")

    if storage_info.get("valid"):
        ssd_info = storage_info["ssd"]
        hd_info = storage_info["hd"]

        table.add_row(
            "SSD (Índices)",
            ssd_info["path"],
            f"{ssd_info['free_gb']:.1f} GB",
            f"{ssd_info['used_gb']:.1f} GB"
        )

        table.add_row(
            "HD (Dados)",
            hd_info["path"],
            f"{hd_info['free_gb']:.1f} GB",
            f"{hd_info['used_gb']:.1f} GB"
        )

    console.print(table)

    # Resultado final
    if is_valid:
        console.print("\n[bold green]✓ Configuração híbrida válida![/bold green]\n")
    else:
        console.print("\n[bold red]✗ Configuração híbrida com problemas![/bold red]\n")
        sys.exit(1)


@app.command("stats")
def show_stats():
    """
    Mostra estatísticas do database.

    Exibe:
    - Total de acórdãos
    - Distribuição por órgão julgador
    - Top relatores
    - Uso de armazenamento
    - Distribuição temporal
    """
    console.print("\n[bold cyan]📊 Estatísticas do Database STJ[/bold cyan]\n")

    try:
        with STJDatabase() as db:
            stats = db.get_statistics()

            # Painel de resumo
            summary = f"""
[bold]Total de Acórdãos:[/bold] {stats['total_acordaos']:,}
[bold]Cache em Memória:[/bold] {stats['cache_size']} documentos
[bold]Tamanho Índices (SSD):[/bold] {stats['index_db_size_mb']:.1f} MB
[bold]Tamanho Dados (HD):[/bold] {stats['data_dir_size_gb']:.2f} GB
            """
            console.print(Panel(summary.strip(), title="Resumo", border_style="cyan"))

            # Top órgãos julgadores
            if stats.get("top_orgaos"):
                console.print("\n[bold yellow]Top 10 Órgãos Julgadores:[/bold yellow]")
                table = Table()
                table.add_column("Órgão", style="cyan")
                table.add_column("Total", justify="right", style="green")

                for item in stats["top_orgaos"]:
                    table.add_row(item["orgao"] or "(Não informado)", str(item["total"]))

                console.print(table)

            # Top relatores
            if stats.get("top_relatores"):
                console.print("\n[bold yellow]Top 10 Relatores:[/bold yellow]")
                table = Table()
                table.add_column("Relator", style="cyan")
                table.add_column("Total", justify="right", style="green")

                for item in stats["top_relatores"]:
                    table.add_row(item["relator"] or "(Não informado)", str(item["total"]))

                console.print(table)

            # Distribuição temporal
            if stats.get("distribuicao_temporal"):
                console.print("\n[bold yellow]Distribuição Temporal (Últimos 12 Meses):[/bold yellow]")
                table = Table()
                table.add_column("Mês", style="cyan")
                table.add_column("Total", justify="right", style="green")

                for item in stats["distribuicao_temporal"]:
                    table.add_row(item["mes"], str(item["total"]))

                console.print(table)

    except Exception as e:
        console.print(f"\n[bold red]Erro ao obter estatísticas: {e}[/bold red]\n")
        sys.exit(1)


@app.command("search")
def search(
    texto: Optional[str] = typer.Option(None, "--texto", "-t", help="Busca fulltext"),
    orgao: Optional[str] = typer.Option(None, "--orgao", "-o", help="Órgão julgador"),
    relator: Optional[str] = typer.Option(None, "--relator", "-r", help="Relator"),
    data_inicio: Optional[str] = typer.Option(None, "--inicio", help="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[str] = typer.Option(None, "--fim", help="Data final (YYYY-MM-DD)"),
    limit: int = typer.Option(20, "--limit", "-l", help="Máximo de resultados")
):
    """
    Busca acórdãos com filtros.

    Exemplos:
        stj search --texto "responsabilidade civil" --limit 10
        stj search --orgao "Terceira Turma" --inicio 2024-01-01
        stj search --relator "Ministro X" --fim 2024-12-31
    """
    console.print("\n[bold cyan]🔍 Buscando Acórdãos...[/bold cyan]\n")

    # Validar que pelo menos um filtro foi fornecido
    if not any([texto, orgao, relator, data_inicio, data_fim]):
        console.print("[bold red]Erro: Forneça pelo menos um critério de busca![/bold red]\n")
        console.print("Use --help para ver opções disponíveis.\n")
        sys.exit(1)

    try:
        with STJDatabase() as db:
            results = db.search(
                texto=texto,
                orgao=orgao,
                relator=relator,
                data_inicio=data_inicio,
                data_fim=data_fim,
                limit=limit
            )

            if not results:
                console.print("[yellow]Nenhum acórdão encontrado com os critérios fornecidos.[/yellow]\n")
                return

            console.print(f"[green]Encontrados {len(results)} acórdão(s):[/green]\n")

            # Mostrar resultados
            for i, acordao in enumerate(results, 1):
                ementa = acordao.get('ementa', '')
                ementa_preview = ementa[:200] + "..." if len(ementa) > 200 else ementa

                info = f"""
[bold cyan]#{i}[/bold cyan] - [bold]{acordao.get('numero_processo', 'N/A')}[/bold]
[yellow]Órgão:[/yellow] {acordao.get('orgao_julgador', 'N/A')}
[yellow]Relator:[/yellow] {acordao.get('relator', 'N/A')}
[yellow]Data:[/yellow] {acordao.get('data_publicacao', 'N/A')}
[yellow]Ementa:[/yellow] {ementa_preview}
                """
                console.print(Panel(info.strip(), border_style="cyan"))

    except Exception as e:
        console.print(f"\n[bold red]Erro na busca: {e}[/bold red]\n")
        sys.exit(1)


@app.command("integrity-check")
def integrity_check():
    """
    Valida integridade do database.

    Verificações:
    - Índices sem documentos
    - Documentos órfãos
    - Hashes duplicados
    - Inconsistências
    """
    console.print("\n[bold cyan]🔍 Validando Integridade do Database[/bold cyan]\n")

    try:
        with STJDatabase() as db:
            report = db.validate_integrity()

            # Status geral
            if report["valid"]:
                console.print("[bold green]✓ Database íntegro![/bold green]\n")
            else:
                console.print("[bold red]✗ Problemas encontrados no database![/bold red]\n")

            # Erros
            if report["errors"]:
                console.print(f"[bold red]Erros ({len(report['errors'])}):[/bold red]")
                for error in report["errors"][:10]:  # Mostrar apenas os primeiros 10
                    console.print(f"  • {error}")
                if len(report["errors"]) > 10:
                    console.print(f"  ... e mais {len(report['errors']) - 10} erro(s)")
                console.print()

            # Avisos
            if report["warnings"]:
                console.print(f"[bold yellow]Avisos ({len(report['warnings'])}):[/bold yellow]")
                for warning in report["warnings"]:
                    console.print(f"  • {warning}")
                console.print()

            # Timestamp
            console.print(f"[dim]Verificado em: {report['checked_at']}[/dim]\n")

            if not report["valid"]:
                sys.exit(1)

    except Exception as e:
        console.print(f"\n[bold red]Erro ao validar integridade: {e}[/bold red]\n")
        sys.exit(1)


@app.command("optimize")
def optimize_db():
    """
    Otimiza o database (VACUUM, ANALYZE, etc).

    Recomendado executar após grandes inserções/deleções.
    """
    console.print("\n[bold cyan]⚙️  Otimizando Database...[/bold cyan]\n")

    try:
        with STJDatabase() as db:
            db.optimize()
            console.print("[bold green]✓ Database otimizado com sucesso![/bold green]\n")

    except Exception as e:
        console.print(f"\n[bold red]Erro ao otimizar: {e}[/bold red]\n")
        sys.exit(1)


@app.command("info")
def show_info():
    """
    Mostra informações sobre o sistema.
    """
    console.print("\n[bold cyan]ℹ️  Informações do Sistema STJ Dados Abertos[/bold cyan]\n")

    info = f"""
[bold]Índices (SSD):[/bold] {INDEX_PATH}
[bold]Dados (HD):[/bold] {DATA_ROOT}
[bold]Python:[/bold] {sys.version.split()[0]}
    """

    console.print(Panel(info.strip(), title="Configuração", border_style="cyan"))
    console.print()


if __name__ == "__main__":
    app()
