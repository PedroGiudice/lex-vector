#!/usr/bin/env python3
"""
Legal Text Extractor - Unified CLI

Entry point unificado para o pipeline de extracao de texto juridico.

Comandos:
    lte process <arquivo>  - Processa um documento PDF
    lte stats              - Exibe estatisticas do Context Store
    lte batch <diretorio>  - Processamento em lote
    lte version            - Exibe versao

Exemplos:
    lte process documento.pdf --engine marker --output ./results
    lte stats --since 2025-01-01 --engine marker
    lte batch ./documentos --parallel 4 --engine auto
"""

import sys
from pathlib import Path

import typer
from rich.console import Console

# Version info
__version__ = "1.0.0"
__author__ = "Legal Workbench Team"

# Initialize console
console = Console()

# Create main app
app = typer.Typer(
    name="lte",
    help="Legal Text Extractor - CLI unificada para extracao de texto juridico",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"[bold cyan]Legal Text Extractor[/bold cyan] v{__version__}")
        console.print(f"[dim]Author: {__author__}[/dim]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        help="Mostra a versao e sai",
        callback=version_callback,
        is_eager=True,
    ),
):
    """
    Legal Text Extractor - Pipeline de extracao de texto juridico.

    Sistema de 4 estagios: Cartografo -> Saneador -> Extrator -> Bibliotecario
    """
    pass


# Import subcommands - lazy loading para evitar imports pesados
def _get_process_app():
    from cli.commands.process import process_app

    return process_app


def _get_stats_app():
    from cli.commands.stats import stats_app

    return stats_app


def _get_batch_app():
    from cli.commands.batch import batch_app

    return batch_app


# Register subcommands
# Note: We use add_typer for subcommands that are themselves Typer apps
# and app.command for simple commands


@app.command()
def version():
    """
    Mostra informacoes de versao.
    """
    from rich.panel import Panel
    from rich.text import Text

    text = Text()
    text.append("Legal Text Extractor\n", style="bold cyan")
    text.append("Versao: ", style="bold")
    text.append(f"{__version__}\n")
    text.append("Author: ", style="bold")
    text.append(f"{__author__}\n")
    text.append("Python: ", style="bold")
    text.append(f"{sys.version.split()[0]}\n")

    # Check available engines
    engines = []
    try:
        from src.engines.marker_engine import MarkerEngine

        marker = MarkerEngine()
        if marker.is_available():
            engines.append("marker (OK)")
        else:
            engines.append("marker (NOT AVAILABLE - RAM check)")
    except ImportError:
        engines.append("marker (NOT INSTALLED)")

    try:
        import pdfplumber

        engines.append("pdfplumber (OK)")
    except ImportError:
        engines.append("pdfplumber (NOT INSTALLED)")

    try:
        import pytesseract

        engines.append("tesseract (OK)")
    except ImportError:
        engines.append("tesseract (NOT INSTALLED)")

    text.append("\nEngines disponiveis:\n", style="bold")
    for e in engines:
        status_style = "green" if "OK" in e else "red"
        text.append(f"  - [{status_style}]{e}[/{status_style}]\n")

    console.print(Panel(text, title="Informacoes do Sistema", border_style="blue"))


@app.command()
def process(
    arquivo: Path = typer.Argument(
        ...,
        help="Caminho do arquivo PDF a processar",
        exists=True,
        readable=True,
        resolve_path=True,
    ),
    engine: str = typer.Option(
        "auto",
        "--engine",
        "-e",
        help="Engine de extracao: auto, marker, pdfplumber, tesseract",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Diretorio de saida (default: mesmo diretorio do arquivo)",
    ),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Formato de saida: text, markdown, json",
    ),
    force_ocr: bool = typer.Option(
        False,
        "--force-ocr",
        help="Forcar OCR em todas as paginas",
    ),
    low_memory: bool = typer.Option(
        False,
        "--low-memory",
        help="Modo de baixa memoria (ignora verificacao de RAM)",
    ),
    context_db: Path = typer.Option(
        None,
        "--context-db",
        "-c",
        help="Caminho do banco Context Store para aprendizado",
    ),
    cnj: str = typer.Option(
        None,
        "--cnj",
        help="Numero CNJ do processo (para Context Store)",
    ),
    sistema: str = typer.Option(
        None,
        "--sistema",
        help="Sistema judicial: pje, eproc, projudi, etc",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Modo verbose com logs detalhados",
    ),
):
    """
    Processa um documento PDF e extrai texto limpo.

    O pipeline executa 4 estagios:
    1. Cartografo: Analisa layout e detecta sistema judicial
    2. Saneador: Pre-processa imagens para OCR
    3. Extrator: Extrai texto com bbox filtering
    4. Bibliotecario: Limpa artefatos e normaliza

    [bold]Exemplos:[/bold]

        lte process documento.pdf

        lte process scanned.pdf --engine marker --force-ocr

        lte process processo.pdf --output ./results --format json

        lte process processo.pdf --context-db data/context.db --cnj "0000000-00.0000.0.00.0000"
    """
    import logging

    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
    from rich.table import Table

    # Configure logging
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    else:
        logging.basicConfig(level=logging.WARNING)

    # Validate engine
    valid_engines = ["auto", "marker", "pdfplumber", "tesseract"]
    if engine.lower() not in valid_engines:
        console.print(f"[red]Erro:[/red] Engine invalida: {engine}")
        console.print(f"[dim]Engines validas: {', '.join(valid_engines)}[/dim]")
        raise typer.Exit(1)

    # Validate format
    valid_formats = ["text", "markdown", "json"]
    if format.lower() not in valid_formats:
        console.print(f"[red]Erro:[/red] Formato invalido: {format}")
        console.print(f"[dim]Formatos validos: {', '.join(valid_formats)}[/dim]")
        raise typer.Exit(1)

    # Setup output path
    if output is None:
        output = arquivo.parent
    output.mkdir(parents=True, exist_ok=True)

    # Determine output filename
    ext_map = {"text": ".txt", "markdown": ".md", "json": ".json"}
    output_file = output / f"{arquivo.stem}_extracted{ext_map[format.lower()]}"

    console.print(f"\n[bold cyan]Legal Text Extractor[/bold cyan] v{__version__}")
    console.print(f"[dim]Processando: {arquivo.name}[/dim]\n")

    try:
        # Import the extractor
        from main import LegalTextExtractor

        # Process based on engine selection
        if engine.lower() == "auto":
            # Use the main extractor (defaults to Marker)
            extractor = LegalTextExtractor(low_memory_mode=low_memory)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Processando documento...", total=100)

                # Process PDF
                progress.update(task, completed=10, description="Inicializando...")
                result = extractor.process_pdf(
                    pdf_path=arquivo,
                    force_ocr=force_ocr,
                )
                progress.update(task, completed=90, description="Salvando resultado...")

                # Save result
                extractor.save(result, output_file, format=format.lower())
                progress.update(task, completed=100, description="Concluido!")

        else:
            # Use pipeline orchestrator with specific engine
            from src.pipeline.orchestrator import PipelineOrchestrator

            caso_info = None
            if cnj and sistema:
                caso_info = {"numero_cnj": cnj, "sistema": sistema}

            orchestrator = PipelineOrchestrator(
                context_db_path=context_db,
                caso_info=caso_info,
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Processando documento...", total=100)

                def progress_callback(current: int, total: int, msg: str):
                    if total > 0:
                        pct = int((current / total) * 90)
                        progress.update(task, completed=pct, description=msg)

                result = orchestrator.process(arquivo, progress_callback=progress_callback)
                progress.update(task, completed=95, description="Salvando resultado...")

                # Save based on format
                with open(output_file, "w", encoding="utf-8") as f:
                    if format.lower() == "json":
                        import json

                        data = {
                            "text": result.text,
                            "total_pages": result.total_pages,
                            "success": result.success,
                            "metadata": result.metadata,
                            "patterns_learned": result.patterns_learned,
                            "processing_time_ms": result.processing_time_ms,
                            "warnings": result.warnings,
                        }
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    else:
                        f.write(result.text)

                progress.update(task, completed=100, description="Concluido!")

        # Display results
        table = Table(title="Resultado da Extracao", show_header=False, box=None)
        table.add_column("Campo", style="bold")
        table.add_column("Valor")

        table.add_row("Arquivo", arquivo.name)
        table.add_row("Tamanho", f"{arquivo.stat().st_size / 1024:.1f} KB")

        if engine.lower() == "auto" and "result" in dir():
            table.add_row("Engine", result.engine_used)
            table.add_row("Sistema Detectado", f"{result.system_name} ({result.confidence}%)")
            table.add_row("Texto Original", f"{result.original_length:,} chars")
            table.add_row("Texto Final", f"{result.final_length:,} chars")
            table.add_row("Reducao", f"{result.reduction_pct:.1f}%")
            table.add_row("Paginas Nativas", str(result.native_pages))
            table.add_row("Paginas OCR", str(result.ocr_pages))
        else:
            table.add_row("Engine", engine)
            table.add_row("Paginas", str(result.total_pages))
            table.add_row("Texto Extraido", f"{len(result.text):,} chars")
            if result.patterns_learned > 0:
                table.add_row("Padroes Aprendidos", str(result.patterns_learned))

        table.add_row("Saida", str(output_file))

        console.print()
        console.print(table)
        console.print("\n[green]Processamento concluido com sucesso![/green]")

    except FileNotFoundError as e:
        console.print(f"[red]Erro:[/red] Arquivo nao encontrado: {e}")
        raise typer.Exit(1)
    except RuntimeError as e:
        console.print(f"[red]Erro de runtime:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Erro inesperado:[/red] {e}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def stats(
    db: Path = typer.Option(
        Path("data/context.db"),
        "--db",
        "-d",
        help="Caminho para o banco de dados SQLite",
    ),
    engine: str = typer.Option(
        None,
        "--engine",
        "-e",
        help="Filtrar por engine (marker, pdfplumber, tesseract)",
    ),
    since: str = typer.Option(
        None,
        "--since",
        "-s",
        help="Filtrar desde data (YYYY-MM-DD)",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Numero de itens a mostrar nas listas",
    ),
    section: str = typer.Option(
        None,
        "--section",
        help="Mostrar apenas uma secao: summary, engines, patterns, recent, casos",
    ),
    export_format: str = typer.Option(
        None,
        "--export",
        help="Exportar estatisticas: json, csv",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Arquivo de saida para export (default: stdout)",
    ),
):
    """
    Exibe estatisticas do Context Store.

    Visualiza metricas de uso incluindo:
    - Total de documentos processados
    - Distribuicao por OCR engine
    - Taxa de sucesso por engine
    - Padroes mais frequentes
    - Ultimos processamentos

    [bold]Exemplos:[/bold]

        lte stats --db data/context.db

        lte stats --since 2025-01-01 --engine marker

        lte stats --section engines --limit 5

        lte stats --export json --output stats.json
    """
    # Delegate to the existing context_stats module
    from datetime import datetime

    from rich.progress import Progress, SpinnerColumn, TextColumn

    from cli.context_stats import (
        ContextStatsDB,
        parse_date,
        render_casos_table,
        render_engine_table,
        render_pattern_table,
        render_recent_table,
        render_summary_panel,
    )

    # Validate database exists
    if not db.exists():
        console.print(f"[red]Erro:[/red] Database nao encontrado: {db}")
        console.print("\n[dim]Dica: Verifique o caminho ou execute processamentos primeiro.[/dim]")
        console.print(
            "[dim]Para gerar dados de teste: python -m cli.generate_sample_data --db {db}[/dim]"
        )
        raise typer.Exit(1)

    # Parse date filter
    since_dt = None
    if since:
        try:
            since_dt = parse_date(since)
        except typer.BadParameter as e:
            console.print(f"[red]Erro:[/red] {e}")
            raise typer.Exit(1)

    # Validate engine filter
    valid_engines = ["marker", "pdfplumber", "tesseract"]
    if engine and engine.lower() not in valid_engines:
        console.print(f"[red]Erro:[/red] Engine invalida: {engine}")
        console.print(f"[dim]Engines validas: {', '.join(valid_engines)}[/dim]")
        raise typer.Exit(1)

    engine_filter = engine.lower() if engine else None

    try:
        store = ContextStatsDB(db)
    except FileNotFoundError as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)

    # Handle export mode
    if export_format:
        import csv
        import json
        from io import StringIO

        summary = store.get_summary()
        engine_stats = store.get_engine_stats(engine_filter=engine_filter, since=since_dt)
        pattern_stats = store.get_pattern_distribution(since=since_dt)

        if export_format.lower() == "json":
            data = {
                "summary": summary,
                "engines": [
                    {
                        "engine": s.engine,
                        "total_patterns": s.total_patterns,
                        "avg_confidence": s.avg_confidence,
                        "total_occurrences": s.total_occurrences,
                        "deprecated_count": s.deprecated_count,
                        "active_count": s.active_count,
                        "success_rate": s.success_rate,
                    }
                    for s in engine_stats
                ],
                "patterns": [
                    {
                        "pattern_type": s.pattern_type,
                        "count": s.count,
                        "avg_confidence": s.avg_confidence,
                        "top_engine": s.top_engine,
                    }
                    for s in pattern_stats
                ],
                "exported_at": datetime.now().isoformat(),
            }
            content = json.dumps(data, indent=2, ensure_ascii=False)
        elif export_format.lower() == "csv":
            buffer = StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["# Engine Statistics"])
            writer.writerow(
                [
                    "engine",
                    "total_patterns",
                    "avg_confidence",
                    "total_occurrences",
                    "deprecated",
                    "active",
                    "success_rate",
                ]
            )
            for s in engine_stats:
                writer.writerow(
                    [
                        s.engine,
                        s.total_patterns,
                        f"{s.avg_confidence:.4f}",
                        s.total_occurrences,
                        s.deprecated_count,
                        s.active_count,
                        f"{s.success_rate:.2f}",
                    ]
                )
            writer.writerow([])
            writer.writerow(["# Pattern Distribution"])
            writer.writerow(["pattern_type", "count", "avg_confidence", "top_engine"])
            for s in pattern_stats:
                writer.writerow([s.pattern_type, s.count, f"{s.avg_confidence:.4f}", s.top_engine])
            content = buffer.getvalue()
        else:
            console.print(f"[red]Erro:[/red] Formato de export invalido: {export_format}")
            console.print("[dim]Formatos validos: json, csv[/dim]")
            raise typer.Exit(1)

        if output:
            output.write_text(content)
            console.print(f"[green]Exportado para:[/green] {output}")
        else:
            print(content)
        return

    # Show filters if active
    if engine_filter or since_dt:
        filters = []
        if engine_filter:
            filters.append(f"engine={engine_filter}")
        if since_dt:
            filters.append(f"desde={since_dt.strftime('%Y-%m-%d')}")
        console.print(f"[dim]Filtros ativos: {', '.join(filters)}[/dim]\n")

    # Render sections based on --section flag
    sections_to_show = (
        [section] if section else ["summary", "engines", "patterns", "recent", "casos"]
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Carregando estatisticas...", total=None)

        if "summary" in sections_to_show and not engine_filter and not since_dt:
            summary = store.get_summary()
            console.print(render_summary_panel(summary))
            console.print()

        if "engines" in sections_to_show:
            engine_stats = store.get_engine_stats(engine_filter=engine_filter, since=since_dt)
            if engine_stats:
                console.print(render_engine_table(engine_stats))
                console.print()
            else:
                console.print("[dim]Nenhuma estatistica de engine encontrada.[/dim]\n")

        if "patterns" in sections_to_show:
            pattern_stats = store.get_pattern_distribution(since=since_dt)
            if pattern_stats:
                console.print(render_pattern_table(pattern_stats))
                console.print()
            else:
                console.print("[dim]Nenhum padrao encontrado.[/dim]\n")

        if "recent" in sections_to_show:
            recent = store.get_recent_processings(
                limit=limit,
                engine_filter=engine_filter,
                since=since_dt,
            )
            if recent:
                console.print(render_recent_table(recent))
                console.print()
            else:
                console.print("[dim]Nenhum processamento recente encontrado.[/dim]\n")

        if "casos" in sections_to_show:
            casos = store.get_casos_summary(limit=limit)
            if casos:
                console.print(render_casos_table(casos))
            else:
                console.print("[dim]Nenhum caso encontrado.[/dim]")


@app.command()
def batch(
    diretorio: Path = typer.Argument(
        ...,
        help="Diretorio com arquivos PDF a processar",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    engine: str = typer.Option(
        "auto",
        "--engine",
        "-e",
        help="Engine de extracao: auto, marker, pdfplumber, tesseract",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Diretorio de saida (default: mesmo diretorio de entrada)",
    ),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Formato de saida: text, markdown, json",
    ),
    parallel: int = typer.Option(
        1,
        "--parallel",
        "-p",
        help="Numero de processos paralelos",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Buscar PDFs recursivamente",
    ),
    pattern: str = typer.Option(
        "*.pdf",
        "--pattern",
        help="Padrao glob para filtrar arquivos",
    ),
    context_db: Path = typer.Option(
        None,
        "--context-db",
        "-c",
        help="Caminho do banco Context Store para aprendizado",
    ),
    force_ocr: bool = typer.Option(
        False,
        "--force-ocr",
        help="Forcar OCR em todas as paginas",
    ),
    low_memory: bool = typer.Option(
        False,
        "--low-memory",
        help="Modo de baixa memoria",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Modo verbose com logs detalhados",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Apenas lista arquivos sem processar",
    ),
):
    """
    Processamento em lote de multiplos documentos PDF.

    Processa todos os PDFs em um diretorio usando o pipeline
    de extracao. Suporta processamento paralelo e recursivo.

    [bold]Exemplos:[/bold]

        lte batch ./documentos

        lte batch ./documentos --parallel 4 --engine marker

        lte batch ./documentos --recursive --pattern "processo_*.pdf"

        lte batch ./documentos --output ./resultados --format json

        lte batch ./documentos --dry-run
    """
    import logging
    from concurrent.futures import as_completed

    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
    from rich.table import Table

    # Configure logging
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    else:
        logging.basicConfig(level=logging.WARNING)

    # Validate engine
    valid_engines = ["auto", "marker", "pdfplumber", "tesseract"]
    if engine.lower() not in valid_engines:
        console.print(f"[red]Erro:[/red] Engine invalida: {engine}")
        console.print(f"[dim]Engines validas: {', '.join(valid_engines)}[/dim]")
        raise typer.Exit(1)

    # Validate format
    valid_formats = ["text", "markdown", "json"]
    if format.lower() not in valid_formats:
        console.print(f"[red]Erro:[/red] Formato invalido: {format}")
        console.print(f"[dim]Formatos validos: {', '.join(valid_formats)}[/dim]")
        raise typer.Exit(1)

    # Find PDF files
    if recursive:
        pdf_files = list(diretorio.rglob(pattern))
    else:
        pdf_files = list(diretorio.glob(pattern))

    pdf_files = [f for f in pdf_files if f.is_file()]

    if not pdf_files:
        console.print(
            f"[yellow]Nenhum arquivo encontrado com padrao '{pattern}' em {diretorio}[/yellow]"
        )
        raise typer.Exit(0)

    console.print("\n[bold cyan]Legal Text Extractor[/bold cyan] - Processamento em Lote")
    console.print(f"[dim]Diretorio: {diretorio}[/dim]")
    console.print(f"[dim]Arquivos encontrados: {len(pdf_files)}[/dim]\n")

    # Dry run mode
    if dry_run:
        table = Table(title="Arquivos a processar (dry-run)")
        table.add_column("#", justify="right")
        table.add_column("Arquivo")
        table.add_column("Tamanho", justify="right")

        for i, pdf in enumerate(pdf_files, 1):
            size = pdf.stat().st_size / 1024
            table.add_row(str(i), pdf.name, f"{size:.1f} KB")

        console.print(table)
        console.print(f"\n[dim]Total: {len(pdf_files)} arquivos[/dim]")
        console.print("[dim]Execute sem --dry-run para processar.[/dim]")
        return

    # Setup output directory
    if output is None:
        output = diretorio
    output.mkdir(parents=True, exist_ok=True)

    # Process files
    ext_map = {"text": ".txt", "markdown": ".md", "json": ".json"}
    results = []
    errors = []

    def process_single_file(pdf_path: Path) -> dict:
        """Process a single PDF file."""
        try:
            from main import LegalTextExtractor

            output_file = output / f"{pdf_path.stem}_extracted{ext_map[format.lower()]}"

            extractor = LegalTextExtractor(low_memory_mode=low_memory)
            result = extractor.process_pdf(pdf_path=pdf_path, force_ocr=force_ocr)
            extractor.save(result, output_file, format=format.lower())

            return {
                "file": pdf_path.name,
                "output": output_file.name,
                "success": True,
                "chars": result.final_length,
                "reduction": result.reduction_pct,
                "engine": result.engine_used,
            }
        except Exception as e:
            return {
                "file": pdf_path.name,
                "success": False,
                "error": str(e),
            }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processando {len(pdf_files)} arquivos...", total=len(pdf_files))

        if parallel > 1:
            # Parallel processing
            # Note: ProcessPoolExecutor may have issues with some libraries
            # For now, we use sequential processing with threading
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=parallel) as executor:
                future_to_pdf = {
                    executor.submit(process_single_file, pdf): pdf for pdf in pdf_files
                }

                for future in as_completed(future_to_pdf):
                    result = future.result()
                    if result["success"]:
                        results.append(result)
                    else:
                        errors.append(result)
                    progress.update(task, advance=1)
        else:
            # Sequential processing
            for pdf in pdf_files:
                progress.update(task, description=f"Processando {pdf.name}...")
                result = process_single_file(pdf)
                if result["success"]:
                    results.append(result)
                else:
                    errors.append(result)
                progress.update(task, advance=1)

    # Display results
    console.print()

    if results:
        table = Table(title="Arquivos Processados com Sucesso")
        table.add_column("Arquivo")
        table.add_column("Saida")
        table.add_column("Chars", justify="right")
        table.add_column("Reducao", justify="right")
        table.add_column("Engine")

        for r in results:
            table.add_row(
                r["file"],
                r["output"],
                f"{r['chars']:,}",
                f"{r['reduction']:.1f}%",
                r["engine"],
            )

        console.print(table)

    if errors:
        console.print()
        error_table = Table(title="Erros", style="red")
        error_table.add_column("Arquivo")
        error_table.add_column("Erro")

        for e in errors:
            error_table.add_row(e["file"], e.get("error", "Erro desconhecido"))

        console.print(error_table)

    # Summary
    console.print()
    console.print(f"[green]Sucesso:[/green] {len(results)} arquivos")
    console.print(f"[red]Erros:[/red] {len(errors)} arquivos")
    console.print(f"[dim]Saida: {output}[/dim]")


def main_entry():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main_entry()
