#!/usr/bin/env python3
"""
CLI para STJ Dados Abertos.
Comandos para espelhos de acordaos e integras de decisoes do STJ.
"""
import json
import typer
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from rich.console import Console
from rich.table import Table

from config import (
    STAGING_DIR,
    ORGAOS_JULGADORES,
    CKAN_DATASETS,
    DATA_ROOT,
    DATABASE_PATH,
    LOGS_DIR,
    INTEGRAS_STAGING_DIR,
    INTEGRAS_TEXTOS_DIR,
    INTEGRAS_METADATA_DIR,
    INTEGRAS_PROGRESS_FILE,
)
from src.downloader import STJDownloader
from src.processor import STJProcessor
from src.database import STJDatabase
from src.ckan_client import CKANClient
from src.integras_downloader import IntegrasDownloader
from src.integras_processor import IntegrasProcessor

app = typer.Typer(
    help="CLI para STJ Dados Abertos - Acordaos e Integras do Superior Tribunal de Justica",
    add_completion=False
)
console = Console()
logger = logging.getLogger(__name__)


# ============================================================================
# COMANDOS DE DOWNLOAD - ESPELHOS
# ============================================================================

@app.command("stj-download-periodo")
def download_periodo(
    inicio: str = typer.Argument(..., help="Data inicio (YYYY-MM-DD)"),
    fim: str = typer.Argument(..., help="Data fim (YYYY-MM-DD)"),
    orgao: str = typer.Option(
        "corte_especial",
        help="Orgao julgador (corte_especial, primeira_turma, etc)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Sobrescrever arquivos existentes")
):
    """
    Baixa espelhos de acordaos do STJ por periodo especifico via CKAN API.

    Exemplo:
        stj-download-periodo 2024-01-01 2024-12-31 --orgao terceira_turma
    """
    try:
        if orgao not in ORGAOS_JULGADORES:
            console.print(f"[red]Orgao invalido: {orgao}[/red]")
            console.print(f"Orgaos disponiveis: {', '.join(ORGAOS_JULGADORES.keys())}")
            raise typer.Exit(1)

        console.print(f"[cyan]Baixando espelhos de {ORGAOS_JULGADORES[orgao]['name']}[/cyan]")
        console.print(f"[cyan]Periodo: {inicio} ate {fim}[/cyan]")

        with STJDownloader() as downloader:
            files = downloader.download_from_ckan(orgao, inicio, fim, force)
            downloader.print_stats()

        console.print(f"\n[green]Download concluido: {len(files)} arquivos[/green]")

    except Exception as e:
        logger.error(f"Erro no download: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-download-orgao")
def download_orgao(
    orgao: str = typer.Argument(..., help="Orgao julgador (ex: corte_especial)"),
    meses: int = typer.Option(3, help="Baixar ultimos N meses"),
    force: bool = typer.Option(False, "--force", "-f", help="Sobrescrever existentes")
):
    """
    Baixa espelhos de acordaos de um orgao julgador via CKAN API.

    Exemplo:
        stj-download-orgao terceira_turma --meses 6
    """
    try:
        if orgao not in ORGAOS_JULGADORES:
            console.print(f"[red]Orgao invalido: {orgao}[/red]")
            console.print("\nOrgaos disponiveis:")
            for key, info in ORGAOS_JULGADORES.items():
                console.print(f"  - {key}: {info['name']}")
            raise typer.Exit(1)

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=meses * 30)).strftime("%Y-%m-%d")

        console.print(f"[cyan]Baixando espelhos de {ORGAOS_JULGADORES[orgao]['name']}[/cyan]")
        console.print(f"[cyan]Ultimos {meses} meses ({start_date} ate {end_date})[/cyan]")

        with STJDownloader() as downloader:
            files = downloader.download_from_ckan(orgao, start_date, end_date, force)
            downloader.print_stats()

        console.print(f"\n[green]Download concluido: {len(files)} arquivos[/green]")

    except Exception as e:
        logger.error(f"Erro no download: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-download-mvp")
def download_mvp():
    """
    Download MVP: ultimo mes de todos os orgaos via CKAN API.
    """
    try:
        console.print("[cyan]Download MVP: ultimo mes de todos os orgaos[/cyan]\n")

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        with STJDownloader() as downloader:
            results = downloader.download_all_orgaos(start_date, end_date)
            total = sum(len(files) for files in results.values())
            downloader.print_stats()

        console.print(f"\n[green]MVP concluido: {total} arquivos de {len(results)} orgaos[/green]")

    except Exception as e:
        logger.error(f"Erro no download MVP: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# COMANDOS DE DOWNLOAD - INTEGRAS
# ============================================================================

@app.command("stj-download-integras")
def download_integras(
    inicio: str = typer.Option(None, help="Data inicio (YYYY-MM-DD). Default: baixa tudo"),
    fim: str = typer.Option(None, help="Data fim (YYYY-MM-DD). Default: hoje"),
    force: bool = typer.Option(False, "--force", "-f", help="Forcar re-download"),
):
    """
    Baixa integras completas (decisoes + acordaos) do STJ.

    Download retroativo desde fev/2022 com persistencia de progresso.
    Se interrompido, retoma de onde parou.
    """
    try:
        console.print("[cyan]Buscando resources de integras via CKAN...[/cyan]")

        with CKANClient() as ckan:
            if inicio or fim:
                start = inicio or "2022-02-01"
                end = fim or datetime.now().strftime("%Y-%m-%d")
                pairs = ckan.get_integras_resources_by_date_range(start, end)
                console.print(f"[cyan]Periodo: {start} ate {end}[/cyan]")
            else:
                pairs = ckan.get_integras_resource_pairs()

        console.print(f"[cyan]Encontrados {len(pairs)} pares (ZIP + JSON metadados)[/cyan]\n")

        if not pairs:
            console.print("[yellow]Nenhum resource encontrado[/yellow]")
            raise typer.Exit(0)

        # Preparar lista de downloads
        download_pairs = []
        for zip_res, meta_res in pairs:
            date_key = zip_res.extract_date_key()
            download_pairs.append({
                "zip_url": zip_res.url,
                "zip_name": zip_res.name,
                "meta_url": meta_res.url,
                "meta_name": meta_res.name,
                "date_key": date_key,
            })

        with IntegrasDownloader(
            INTEGRAS_STAGING_DIR,
            INTEGRAS_TEXTOS_DIR,
            INTEGRAS_METADATA_DIR,
            INTEGRAS_PROGRESS_FILE,
        ) as downloader:
            stats = downloader.download_all(download_pairs, force)

        console.print(f"\n[green]Download concluido:[/green]")
        console.print(f"  Completados: {stats['completed']}")
        console.print(f"  Pulados (ja baixados): {stats['skipped']}")
        console.print(f"  Erros: {stats['errors']}")

    except Exception as e:
        logger.error(f"Erro no download de integras: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-processar-integras")
def processar_integras(
    data: str = typer.Option(None, help="Processar apenas data especifica (YYYYMMDD ou YYYYMM)"),
):
    """
    Processa integras baixadas: extrai textos, normaliza metadados, insere no banco.
    """
    try:
        console.print("[cyan]Processando integras...[/cyan]")

        # Listar JSONs de metadados disponiveis
        if data:
            meta_files = sorted(INTEGRAS_METADATA_DIR.glob(f"metadados{data}*"))
        else:
            meta_files = sorted(INTEGRAS_METADATA_DIR.glob("metadados*.json"))

        if not meta_files:
            console.print("[yellow]Nenhum arquivo de metadados encontrado[/yellow]")
            console.print(f"[yellow]Diretorio: {INTEGRAS_METADATA_DIR}[/yellow]")
            raise typer.Exit(0)

        console.print(f"[cyan]Arquivos de metadados: {len(meta_files)}[/cyan]")

        total_inseridos = 0
        total_duplicados = 0
        total_erros = 0

        with STJDatabase() as db:
            db.criar_schema()

            for meta_file in meta_files:
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        metadados = json.load(f)
                    if not isinstance(metadados, list):
                        metadados = [metadados]

                    processor = IntegrasProcessor()
                    registros = processor.processar_batch(metadados, INTEGRAS_TEXTOS_DIR)

                    if registros:
                        inseridos, duplicados, erros = db.inserir_integras_batch(registros)
                        total_inseridos += inseridos
                        total_duplicados += duplicados
                        total_erros += erros
                        console.print(f"  {meta_file.name}: {inseridos} novos, {duplicados} dup, {erros} err")
                    else:
                        console.print(f"  {meta_file.name}: sem registros processados")

                except Exception as e:
                    logger.error(f"Erro processando {meta_file.name}: {e}")
                    console.print(f"  [red]{meta_file.name}: erro - {e}[/red]")
                    total_erros += 1

            # Rebuild FTS
            console.print("[cyan]Reconstruindo indice FTS para integras...[/cyan]")
            db.rebuild_fts_integras()

        console.print(f"\n[green]Processamento concluido:[/green]")
        console.print(f"  Inseridos: {total_inseridos}")
        console.print(f"  Duplicados: {total_duplicados}")
        console.print(f"  Erros: {total_erros}")

    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# COMANDOS DE PROCESSAMENTO - ESPELHOS
# ============================================================================

@app.command("stj-processar-staging")
def processar_staging(
    pattern: str = typer.Option("*.json", help="Pattern glob para filtrar arquivos"),
    atualizar: bool = typer.Option(False, "--atualizar", help="Atualizar registros duplicados")
):
    """
    Processa arquivos JSON do staging e insere no banco DuckDB.
    """
    try:
        console.print("[cyan]Processando arquivos do staging...[/cyan]\n")

        staging_files = sorted(STAGING_DIR.glob(pattern))

        if not staging_files:
            console.print(f"[yellow]Nenhum arquivo encontrado com pattern: {pattern}[/yellow]")
            raise typer.Exit(0)

        console.print(f"[cyan]Arquivos encontrados: {len(staging_files)}[/cyan]")

        processor = STJProcessor()
        registros = processor.processar_batch(staging_files)

        console.print(f"\n[cyan]Total de registros processados: {len(registros)}[/cyan]")

        if registros:
            with STJDatabase() as db:
                db.criar_schema()
                inseridos, duplicados, erros = db.inserir_batch(registros, atualizar_duplicados=atualizar)
                console.print(f"\n[green]Processamento concluido:[/green]")
                console.print(f"  Inseridos: {inseridos}")
                console.print(f"  Duplicados: {duplicados}")
                console.print(f"  Erros: {erros}")

    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# COMANDOS DE BUSCA
# ============================================================================

@app.command("stj-buscar-ementa")
def buscar_ementa(
    termo: str = typer.Argument(..., help="Termo para buscar nas ementas"),
    orgao: Optional[str] = typer.Option(None, help="Filtrar por orgao julgador"),
    dias: int = typer.Option(365, help="Buscar nos ultimos N dias"),
    limit: int = typer.Option(20, help="Maximo de resultados")
):
    """
    Busca termo nas ementas dos acordaos do STJ.
    """
    try:
        console.print(f"[cyan]Buscando '{termo}' nas ementas...[/cyan]\n")

        with STJDatabase() as db:
            resultados = db.buscar_ementa(termo, orgao, dias, limit)

            if not resultados:
                console.print("[yellow]Nenhum resultado encontrado[/yellow]")
                raise typer.Exit(0)

            table = Table(title=f"Resultados para '{termo}'")
            table.add_column("Processo", style="cyan")
            table.add_column("Orgao", style="green")
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
            console.print(f"\n[green]{len(resultados)} resultado(s)[/green]")

    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-buscar-acordao")
def buscar_acordao(
    termo: str = typer.Argument(..., help="Termo para buscar nos acordaos"),
    orgao: Optional[str] = typer.Option(None, help="Filtrar por orgao julgador"),
    dias: int = typer.Option(30, help="Buscar nos ultimos N dias"),
    limit: int = typer.Option(10, help="Maximo de resultados")
):
    """
    Busca termo no inteiro teor dos acordaos do STJ (espelhos).
    """
    try:
        console.print(f"[cyan]Buscando '{termo}' no inteiro teor dos acordaos...[/cyan]\n")

        with STJDatabase() as db:
            resultados = db.buscar_acordao(termo, orgao, dias, limit)

            if not resultados:
                console.print("[yellow]Nenhum resultado encontrado[/yellow]")
                raise typer.Exit(0)

            table = Table(title=f"Acordaos com '{termo}'")
            table.add_column("Processo", style="cyan")
            table.add_column("Orgao", style="green")
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
            console.print(f"\n[green]{len(resultados)} resultado(s)[/green]")

    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-buscar-integra")
def buscar_integra(
    termo: str = typer.Argument(..., help="Termo de busca"),
    tipo: str = typer.Option(None, help="DECISAO ou ACORDAO"),
    dias: int = typer.Option(365, help="Ultimos N dias"),
    limit: int = typer.Option(20, help="Limite de resultados"),
):
    """Busca full-text no texto completo das integras."""
    try:
        console.print(f"[cyan]Buscando '{termo}' nas integras...[/cyan]\n")

        with STJDatabase() as db:
            resultados = db.buscar_integras(termo, tipo, dias, limit)

            if not resultados:
                console.print("[yellow]Nenhum resultado encontrado[/yellow]")
                raise typer.Exit(0)

            table = Table(title=f"Integras com '{termo}'")
            table.add_column("SeqDoc", style="cyan")
            table.add_column("Processo", style="green")
            table.add_column("Tipo", style="blue")
            table.add_column("Ministro", style="yellow")
            table.add_column("Data Pub.", style="magenta")
            table.add_column("Preview", style="white")

            for r in resultados:
                table.add_row(
                    str(r['seq_documento']),
                    r['numero_processo'],
                    r['tipo_documento'],
                    r['ministro'] or 'N/A',
                    str(r['data_publicacao'])[:10] if r['data_publicacao'] else 'N/A',
                    (r['preview'][:60] + '...') if r.get('preview') and len(r['preview']) > 60 else (r.get('preview') or 'N/A'),
                )

            console.print(table)
            console.print(f"\n[green]{len(resultados)} resultado(s)[/green]")

    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-buscar-processo")
def buscar_processo(
    numero: str = typer.Argument(..., help="Numero do processo"),
):
    """
    Busca unificada por numero de processo.
    Retorna espelho + integra(s) correlacionados.
    """
    try:
        console.print(f"[cyan]Buscando processo {numero}...[/cyan]\n")

        with STJDatabase() as db:
            resultado = db.buscar_por_processo(numero)

            # Mostrar espelhos
            if resultado['acordaos']:
                console.print(f"[bold]Espelhos (acordaos): {len(resultado['acordaos'])}[/bold]")
                for ac in resultado['acordaos']:
                    console.print(f"  Processo: {ac.get('numero_processo')}")
                    console.print(f"  Orgao: {ac.get('orgao_julgador')}")
                    console.print(f"  Relator: {ac.get('relator')}")
                    console.print(f"  Data: {ac.get('data_publicacao')}")
                    if ac.get('ementa'):
                        console.print(f"  Ementa: {ac['ementa'][:120]}...")
                    console.print()
            else:
                console.print("[yellow]Nenhum espelho encontrado[/yellow]")

            # Mostrar integras
            if resultado['integras']:
                console.print(f"[bold]Integras: {len(resultado['integras'])}[/bold]")
                for it in resultado['integras']:
                    console.print(f"  SeqDocumento: {it.get('seq_documento')}")
                    console.print(f"  Tipo: {it.get('tipo_documento')}")
                    console.print(f"  Ministro: {it.get('ministro')}")
                    console.print(f"  Data: {it.get('data_publicacao')}")
                    console.print(f"  Teor: {it.get('teor')}")
                    texto = it.get('texto_completo', '')
                    if texto:
                        console.print(f"  Texto: {texto[:200]}...")
                    console.print()
            else:
                console.print("[yellow]Nenhuma integra encontrada[/yellow]")

            total = len(resultado['acordaos']) + len(resultado['integras'])
            console.print(f"[green]Total: {total} resultado(s)[/green]")

    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# COMANDOS DE ESTATISTICAS E EXPORTACAO
# ============================================================================

@app.command("stj-estatisticas")
def estatisticas():
    """
    Mostra estatisticas do banco de dados STJ (espelhos).
    """
    try:
        console.print("[cyan]Estatisticas do Banco STJ - Espelhos[/cyan]\n")

        with STJDatabase() as db:
            stats = db.obter_estatisticas()

            console.print(f"[bold]Total de acordaos:[/bold] {stats.get('total_acordaos', 0):,}")
            console.print(f"[bold]Tamanho do banco:[/bold] {stats.get('tamanho_db_mb', 0):.2f} MB\n")

            if 'periodo' in stats:
                console.print(f"[bold]Periodo coberto:[/bold]")
                console.print(f"  Mais antigo: {stats['periodo']['mais_antigo']}")
                console.print(f"  Mais recente: {stats['periodo']['mais_recente']}\n")

            console.print(f"[bold]Ultimos 30 dias:[/bold] {stats.get('ultimos_30_dias', 0):,} acordaos\n")

            if stats.get('por_orgao'):
                table = Table(title="Acordaos por Orgao Julgador")
                table.add_column("Orgao", style="cyan")
                table.add_column("Quantidade", style="green", justify="right")
                for orgao, count in sorted(stats['por_orgao'].items(), key=lambda x: -x[1]):
                    table.add_row(orgao, f"{count:,}")
                console.print(table)

    except Exception as e:
        logger.error(f"Erro ao obter estatisticas: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-estatisticas-integras")
def estatisticas_integras():
    """Estatisticas do dataset de integras."""
    try:
        console.print("[cyan]Estatisticas do Banco STJ - Integras[/cyan]\n")

        with STJDatabase() as db:
            stats = db.estatisticas_integras()

            console.print(f"[bold]Total de integras:[/bold] {stats.get('total_integras', 0):,}\n")

            if stats.get('por_tipo'):
                table = Table(title="Integras por Tipo")
                table.add_column("Tipo", style="cyan")
                table.add_column("Quantidade", style="green", justify="right")
                for tipo, count in stats['por_tipo'].items():
                    table.add_row(tipo, f"{count:,}")
                console.print(table)
                console.print()

            if stats.get('periodo'):
                console.print(f"[bold]Periodo:[/bold]")
                console.print(f"  Mais antigo: {stats['periodo']['mais_antigo']}")
                console.print(f"  Mais recente: {stats['periodo']['mais_recente']}\n")

            if stats.get('por_ministro_top10'):
                table = Table(title="Top 10 Ministros")
                table.add_column("Ministro", style="cyan")
                table.add_column("Quantidade", style="green", justify="right")
                for ministro, count in stats['por_ministro_top10'].items():
                    table.add_row(ministro, f"{count:,}")
                console.print(table)

    except Exception as e:
        logger.error(f"Erro: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-exportar")
def exportar(
    query: str = typer.Argument(..., help="Query SQL para exportar"),
    output: str = typer.Option("export.csv", help="Arquivo de saida (.csv)"),
):
    """Exporta resultados de query SQL para CSV."""
    try:
        output_path = Path(output)
        console.print(f"[cyan]Exportando para: {output_path}[/cyan]")
        console.print(f"[cyan]Query:[/cyan] {query}\n")

        with STJDatabase() as db:
            db.exportar_csv(query, output_path)

        console.print(f"[green]Exportacao concluida[/green]")

    except Exception as e:
        logger.error(f"Erro na exportacao: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# COMANDOS DE UTILIDADE
# ============================================================================

@app.command("stj-init")
def init():
    """Inicializa o sistema: cria diretorios e schema do banco."""
    try:
        console.print("[cyan]Inicializando sistema STJ Dados Abertos...[/cyan]\n")

        if not DATA_ROOT.exists():
            DATA_ROOT.mkdir(parents=True, exist_ok=True)

        with STJDatabase() as db:
            db.criar_schema()

        console.print("[green]Sistema inicializado com sucesso![/green]")
        console.print(f"\n[cyan]Diretorios:[/cyan]")
        console.print(f"  Data Root: {DATA_ROOT}")
        console.print(f"  Staging (espelhos): {STAGING_DIR}")
        console.print(f"  Staging (integras): {INTEGRAS_STAGING_DIR}")
        console.print(f"  Textos (integras): {INTEGRAS_TEXTOS_DIR}")
        console.print(f"  Database: {DATABASE_PATH}")

    except Exception as e:
        logger.error(f"Erro na inicializacao: {e}")
        console.print(f"[red]Erro: {e}[/red]")
        raise typer.Exit(1)


@app.command("stj-info")
def info():
    """Mostra informacoes do sistema e configuracoes."""
    console.print("[bold cyan]STJ Dados Abertos - Informacoes do Sistema[/bold cyan]\n")

    # Paths
    console.print("[bold]Paths:[/bold]")
    console.print(f"  Data Root: {DATA_ROOT}")
    console.print(f"  Staging (espelhos): {STAGING_DIR}")
    console.print(f"  Staging (integras): {INTEGRAS_STAGING_DIR}")
    console.print(f"  Textos (integras): {INTEGRAS_TEXTOS_DIR}")
    console.print(f"  Database: {DATABASE_PATH}")
    console.print(f"  Logs: {LOGS_DIR}")
    console.print(f"  Acessivel: {'Sim' if DATA_ROOT.exists() else 'Nao'}\n")

    # Datasets
    console.print("[bold]Datasets Disponiveis:[/bold]")
    console.print(f"  Espelhos de Acordaos: {len(CKAN_DATASETS)} orgaos")
    console.print(f"  Integras: 1 dataset (decisoes + acordaos)\n")

    # Orgaos
    console.print("[bold]Orgaos Julgadores (Espelhos):[/bold]")
    for key, org_info in ORGAOS_JULGADORES.items():
        console.print(f"  - {key}: {org_info['name']}")

    console.print()

    # Comandos
    console.print("[bold]Comandos Principais:[/bold]")
    console.print("  Espelhos:")
    console.print("    stj-download-periodo  - Baixar por periodo")
    console.print("    stj-download-orgao    - Baixar por orgao")
    console.print("    stj-download-mvp      - Ultimo mes (todos)")
    console.print("    stj-processar-staging - Processar JSONs")
    console.print("    stj-buscar-ementa     - Buscar em ementas")
    console.print("    stj-buscar-acordao    - Buscar inteiro teor")
    console.print("    stj-estatisticas      - Estatisticas")
    console.print("  Integras:")
    console.print("    stj-download-integras     - Baixar integras")
    console.print("    stj-processar-integras    - Processar integras")
    console.print("    stj-buscar-integra        - Buscar texto completo")
    console.print("    stj-buscar-processo        - Busca unificada")
    console.print("    stj-estatisticas-integras - Estatisticas integras")

    console.print("\n[cyan]Use --help em qualquer comando para mais detalhes[/cyan]")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    app()
