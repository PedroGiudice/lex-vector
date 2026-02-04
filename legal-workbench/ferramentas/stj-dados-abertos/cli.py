#!/usr/bin/env python3
"""
CLI para STJ Dados Abertos.
Comandos específicos e descritivos para operações com acórdãos do STJ.
"""
import typer
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from config import (
    STAGING_DIR,
    ORGAOS_JULGADORES,
    get_date_range_urls,
    get_mvp_urls,
    DATA_ROOT,
    DATABASE_PATH,
    LOGS_DIR
)
from src.downloader import STJDownloader
from src.processor import STJProcessor
from src.database import STJDatabase

app = typer.Typer(
    help="CLI para STJ Dados Abertos - Acórdãos do Superior Tribunal de Justiça",
    add_completion=False
)
console = Console()
logger = logging.getLogger(__name__)


# ============================================================================
# COMANDOS DE DOWNLOAD
# ============================================================================

@app.command("stj-download-periodo")
def download_periodo(
    inicio: str = typer.Argument(..., help="Data início (YYYY-MM-DD)"),
    fim: str = typer.Argument(..., help="Data fim (YYYY-MM-DD)"),
    orgao: str = typer.Option(
        "corte_especial",
        help="Órgão julgador (corte_especial, primeira_turma, etc)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Sobrescrever arquivos existentes")
):
    """
    Baixa acórdãos do STJ por período específico.

    Exemplo:
        stj-download-periodo 2024-01-01 2024-12-31 --orgao terceira_turma
    """
    try:
        # Validar órgão
        if orgao not in ORGAOS_JULGADORES:
            console.print(f"[red][ERRO]Órgão inválido: {orgao}[/red]")
            console.print(f"Órgãos disponíveis: {', '.join(ORGAOS_JULGADORES.keys())}")
            raise typer.Exit(1)

        # Validar datas
        try:
            start_date = datetime.strptime(inicio, "%Y-%m-%d")
            end_date = datetime.strptime(fim, "%Y-%m-%d")
        except ValueError:
            console.print("[red][ERRO]Formato de data inválido. Use: YYYY-MM-DD[/red]")
            raise typer.Exit(1)

        if start_date > end_date:
            console.print("[red][ERRO]Data início deve ser anterior à data fim[/red]")
            raise typer.Exit(1)

        # Gerar URLs
        console.print(f"[cyan]Baixando acórdãos de {ORGAOS_JULGADORES[orgao]['name']}[/cyan]")
        console.print(f"[cyan]Período: {inicio} até {fim}[/cyan]")

        url_configs = get_date_range_urls(start_date, end_date, orgao)
        console.print(f"[cyan]Total de arquivos: {len(url_configs)}[/cyan]\n")

        # Preparar configs para download
        download_configs = [
            {
                "url": uc["url"],
                "filename": uc["filename"],
                "force": force
            }
            for uc in url_configs
        ]

        # Download
        with STJDownloader() as downloader:
            files = downloader.download_batch(download_configs)
            downloader.print_stats()

        console.print(f"\n[green][OK]Download concluído: {len(files)} arquivos[/green]")
        console.print(f"[cyan]Diretório: {STAGING_DIR}[/cyan]")

    except Exception as e:
        logger.error(f"Erro no download: {e}")
        console.print(f"[red][ERRO]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-download-orgao")
def download_orgao(
    orgao: str = typer.Argument(..., help="Órgão julgador (ex: corte_especial)"),
    meses: int = typer.Option(3, help="Baixar últimos N meses"),
    force: bool = typer.Option(False, "--force", "-f", help="Sobrescrever existentes")
):
    """
    Baixa acórdãos de um órgão julgador específico.

    Exemplo:
        stj-download-orgao terceira_turma --meses 6
    """
    try:
        # Validar órgão
        if orgao not in ORGAOS_JULGADORES:
            console.print(f"[red][ERRO]Órgão inválido: {orgao}[/red]")
            console.print("\nÓrgãos disponíveis:")
            for key, info in ORGAOS_JULGADORES.items():
                console.print(f"  • {key}: {info['name']}")
            raise typer.Exit(1)

        # Calcular período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=meses * 30)

        console.print(f"[cyan]Baixando acórdãos de {ORGAOS_JULGADORES[orgao]['name']}[/cyan]")
        console.print(f"[cyan]Últimos {meses} meses[/cyan]")

        # Gerar URLs
        url_configs = get_date_range_urls(start_date, end_date, orgao)

        download_configs = [
            {
                "url": uc["url"],
                "filename": uc["filename"],
                "force": force
            }
            for uc in url_configs
        ]

        # Download
        with STJDownloader() as downloader:
            files = downloader.download_batch(download_configs)
            downloader.print_stats()

        console.print(f"\n[green][OK]Download concluído: {len(files)} arquivos[/green]")

    except Exception as e:
        logger.error(f"Erro no download: {e}")
        console.print(f"[red][ERRO]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-download-mvp")
def download_mvp():
    """
    Download MVP: últimos 30 dias da Corte Especial apenas.

    Útil para testes rápidos e validação do sistema.
    """
    try:
        console.print("[cyan]Download MVP: Últimos 30 dias da Corte Especial[/cyan]\n")

        url_configs = get_mvp_urls()

        download_configs = [
            {
                "url": uc["url"],
                "filename": uc["filename"],
                "force": False
            }
            for uc in url_configs
        ]

        with STJDownloader() as downloader:
            files = downloader.download_batch(download_configs)
            downloader.print_stats()

        console.print(f"\n[green][OK]MVP concluído: {len(files)} arquivos[/green]")

    except Exception as e:
        logger.error(f"Erro no download MVP: {e}")
        console.print(f"[red][ERRO]Erro: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# COMANDOS DE PROCESSAMENTO
# ============================================================================

@app.command("stj-processar-staging")
def processar_staging(
    pattern: str = typer.Option("*.json", help="Pattern glob para filtrar arquivos"),
    atualizar: bool = typer.Option(False, "--atualizar", help="Atualizar registros duplicados")
):
    """
    Processa arquivos JSON do staging e insere no banco DuckDB.

    Exemplo:
        stj-processar-staging --pattern "corte_especial_*.json"
    """
    try:
        console.print("[cyan]Processando arquivos do staging...[/cyan]\n")

        # Listar arquivos
        staging_files = sorted(STAGING_DIR.glob(pattern))

        if not staging_files:
            console.print(f"[yellow][AVISO]Nenhum arquivo encontrado com pattern: {pattern}[/yellow]")
            console.print(f"[yellow]Diretório: {STAGING_DIR}[/yellow]")
            raise typer.Exit(0)

        console.print(f"[cyan]Arquivos encontrados: {len(staging_files)}[/cyan]")
        for f in staging_files[:5]:
            console.print(f"  • {f.name}")
        if len(staging_files) > 5:
            console.print(f"  ... e mais {len(staging_files) - 5} arquivos\n")

        # Processar arquivos
        processor = STJProcessor()
        registros = processor.processar_batch(staging_files)

        console.print(f"\n[cyan]Total de registros processados: {len(registros)}[/cyan]")

        # Inserir no banco
        if registros:
            with STJDatabase() as db:
                # Criar schema se não existir
                db.criar_schema()

                # Inserir batch
                inseridos, duplicados, erros = db.inserir_batch(registros, atualizar_duplicados=atualizar)

                console.print(f"\n[green][OK]Processamento concluído:[/green]")
                console.print(f"  • Inseridos: {inseridos}")
                console.print(f"  • Duplicados: {duplicados}")
                console.print(f"  • Erros: {erros}")

                # Estatísticas do banco
                stats = db.obter_estatisticas()
                console.print(f"\n[cyan]Total no banco: {stats.get('total_acordaos', 0)} acórdãos[/cyan]")
        else:
            console.print("[yellow][AVISO]Nenhum registro processado[/yellow]")

    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        console.print(f"[red][ERRO]Erro: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# COMANDOS DE BUSCA
# ============================================================================

@app.command("stj-buscar-ementa")
def buscar_ementa(
    termo: str = typer.Argument(..., help="Termo para buscar nas ementas"),
    orgao: Optional[str] = typer.Option(None, help="Filtrar por órgão julgador"),
    dias: int = typer.Option(365, help="Buscar nos últimos N dias"),
    limit: int = typer.Option(20, help="Máximo de resultados")
):
    """
    Busca termo nas ementas dos acórdãos do STJ.

    Exemplo:
        stj-buscar-ementa "responsabilidade civil" --orgao terceira_turma --dias 90
    """
    try:
        console.print(f"[cyan]Buscando '{termo}' nas ementas...[/cyan]")
        console.print(f"[cyan]Período: últimos {dias} dias[/cyan]\n")

        with STJDatabase() as db:
            resultados = db.buscar_ementa(termo, orgao, dias, limit)

            if not resultados:
                console.print("[yellow][AVISO]Nenhum resultado encontrado[/yellow]")
                raise typer.Exit(0)

            # Mostrar resultados em tabela
            table = Table(title=f"Resultados para '{termo}'")
            table.add_column("Processo", style="cyan")
            table.add_column("Órgão", style="green")
            table.add_column("Relator", style="yellow")
            table.add_column("Data Pub.", style="magenta")
            table.add_column("Ementa (preview)", style="white")

            for r in resultados:
                ementa_preview = (r['ementa'][:80] + '...') if len(r['ementa']) > 80 else r['ementa']
                table.add_row(
                    r['numero_processo'],
                    r['orgao_julgador'],
                    r['relator'] or 'N/A',
                    str(r['data_publicacao'])[:10],
                    ementa_preview
                )

            console.print(table)
            console.print(f"\n[green][OK]{len(resultados)} resultado(s) encontrado(s)[/green]")

    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        console.print(f"[red][ERRO]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-buscar-acordao")
def buscar_acordao(
    termo: str = typer.Argument(..., help="Termo para buscar nos acórdãos"),
    orgao: Optional[str] = typer.Option(None, help="Filtrar por órgão julgador"),
    dias: int = typer.Option(30, help="Buscar nos últimos N dias"),
    limit: int = typer.Option(10, help="Máximo de resultados")
):
    """
    Busca termo no inteiro teor dos acórdãos do STJ.

    ATENÇÃO: Pode ser lento em bancos grandes. Use filtros temporais.

    Exemplo:
        stj-buscar-acordao "dano moral" --dias 30 --limit 10
    """
    try:
        console.print(f"[cyan]Buscando '{termo}' no inteiro teor dos acórdãos...[/cyan]")
        console.print(f"[yellow][AVISO]Busca no texto completo pode demorar...[/yellow]")
        console.print(f"[cyan]Período: últimos {dias} dias[/cyan]\n")

        with STJDatabase() as db:
            resultados = db.buscar_acordao(termo, orgao, dias, limit)

            if not resultados:
                console.print("[yellow][AVISO]Nenhum resultado encontrado[/yellow]")
                raise typer.Exit(0)

            # Mostrar resultados
            table = Table(title=f"Acórdãos com '{termo}'")
            table.add_column("Processo", style="cyan")
            table.add_column("Órgão", style="green")
            table.add_column("Tipo", style="blue")
            table.add_column("Data Pub.", style="magenta")
            table.add_column("Tamanho", style="yellow")

            for r in resultados:
                table.add_row(
                    r['numero_processo'],
                    r['orgao_julgador'],
                    r['tipo_decisao'] or 'N/A',
                    str(r['data_publicacao'])[:10],
                    f"{r['tamanho_texto']:,} chars"
                )

            console.print(table)
            console.print(f"\n[green][OK]{len(resultados)} acórdão(s) encontrado(s)[/green]")

    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        console.print(f"[red][ERRO]Erro: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# COMANDOS DE ESTATÍSTICAS E EXPORTAÇÃO
# ============================================================================

@app.command("stj-estatisticas")
def estatisticas():
    """
    Mostra estatísticas do banco de dados STJ.

    Exibe contagens por órgão, tipo de decisão, período coberto, etc.
    """
    try:
        console.print("[cyan]Estatísticas do Banco STJ[/cyan]\n")

        with STJDatabase() as db:
            stats = db.obter_estatisticas()

            # Total
            console.print(f"[bold]Total de acórdãos:[/bold] {stats.get('total_acordaos', 0):,}")
            console.print(f"[bold]Tamanho do banco:[/bold] {stats.get('tamanho_db_mb', 0):.2f} MB\n")

            # Período
            if 'periodo' in stats:
                console.print(f"[bold]Período coberto:[/bold]")
                console.print(f"  • Mais antigo: {stats['periodo']['mais_antigo']}")
                console.print(f"  • Mais recente: {stats['periodo']['mais_recente']}\n")

            # Últimos 30 dias
            console.print(f"[bold]Últimos 30 dias:[/bold] {stats.get('ultimos_30_dias', 0):,} acórdãos\n")

            # Por órgão
            if 'por_orgao' in stats and stats['por_orgao']:
                table = Table(title="Acórdãos por Órgão Julgador")
                table.add_column("Órgão", style="cyan")
                table.add_column("Quantidade", style="green", justify="right")

                for orgao, count in sorted(stats['por_orgao'].items(), key=lambda x: -x[1]):
                    table.add_row(orgao, f"{count:,}")

                console.print(table)
                console.print()

            # Por tipo
            if 'por_tipo' in stats and stats['por_tipo']:
                table = Table(title="Acórdãos por Tipo de Decisão")
                table.add_column("Tipo", style="cyan")
                table.add_column("Quantidade", style="green", justify="right")

                for tipo, count in stats['por_tipo'].items():
                    table.add_row(tipo or 'N/A', f"{count:,}")

                console.print(table)

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        console.print(f"[red][ERRO]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-exportar")
def exportar(
    query: str = typer.Argument(..., help="Query SQL para exportar"),
    output: str = typer.Option("export.csv", help="Arquivo de saída (.csv)"),
):
    """
    Exporta resultados de query SQL para CSV.

    Exemplo:
        stj-exportar "SELECT * FROM acordaos LIMIT 100" --output top100.csv
    """
    try:
        output_path = Path(output)

        console.print(f"[cyan]Exportando para: {output_path}[/cyan]\n")
        console.print(f"[cyan]Query:[/cyan] {query}\n")

        with STJDatabase() as db:
            db.exportar_csv(query, output_path)

        console.print(f"[green][OK]Exportação concluída[/green]")

    except Exception as e:
        logger.error(f"Erro na exportação: {e}")
        console.print(f"[red][ERRO]Erro: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# COMANDOS DE UTILIDADE
# ============================================================================

@app.command("stj-init")
def init():
    """
    Inicializa o sistema: cria diretórios e schema do banco.
    """
    try:
        console.print("[cyan]Inicializando sistema STJ Dados Abertos...[/cyan]\n")

        # Verificar se DATA_ROOT existe e tem espaco
        if not DATA_ROOT.exists():
            DATA_ROOT.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]Diretorio de dados criado: {DATA_ROOT}[/green]")
        else:
            console.print(f"[green]Diretorio de dados: {DATA_ROOT}[/green]")

        # Criar schema do banco
        with STJDatabase() as db:
            db.criar_schema()

        console.print("\n[green]Sistema inicializado com sucesso![/green]")
        console.print(f"\n[cyan]Diretorios:[/cyan]")
        console.print(f"  Staging: {STAGING_DIR}")
        console.print(f"  Database: {DATABASE_PATH}")
        console.print(f"  Logs: {LOGS_DIR}")

    except Exception as e:
        logger.error(f"Erro na inicialização: {e}")
        console.print(f"[red][ERRO]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-info")
def info():
    """
    Mostra informações do sistema e configurações.
    """
    console.print("[bold cyan]STJ Dados Abertos - Informações do Sistema[/bold cyan]\n")

    # Paths
    console.print("[bold]Paths:[/bold]")
    console.print(f"  Data Root: {DATA_ROOT}")
    console.print(f"  Staging: {STAGING_DIR}")
    console.print(f"  Database: {DATABASE_PATH}")
    console.print(f"  Logs: {LOGS_DIR}")
    console.print(f"  Acessivel: {'Sim' if DATA_ROOT.exists() else 'Nao'}\n")

    # Órgãos julgadores
    console.print("[bold]Órgãos Julgadores Disponíveis:[/bold]")
    for key, info in ORGAOS_JULGADORES.items():
        console.print(f"  • {key}: {info['name']} (prioridade: {info['priority']})")

    console.print()

    # Comandos disponíveis
    console.print("[bold]Comandos Principais:[/bold]")
    console.print("  • stj-init - Inicializar sistema")
    console.print("  • stj-download-periodo - Baixar por período")
    console.print("  • stj-download-orgao - Baixar por órgão")
    console.print("  • stj-processar-staging - Processar JSONs")
    console.print("  • stj-buscar-ementa - Buscar em ementas")
    console.print("  • stj-buscar-acordao - Buscar em inteiro teor")
    console.print("  • stj-estatisticas - Ver estatísticas")
    console.print("  • stj-exportar - Exportar para CSV")

    console.print("\n[cyan]Use --help em qualquer comando para mais detalhes[/cyan]")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    app()
