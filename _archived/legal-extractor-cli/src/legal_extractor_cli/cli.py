"""
Legal Extractor CLI - Interface de linha de comando simplificada.

Usa Rich para output bonito e Typer para parsing de argumentos.
NÃO reimplementa lógica de extração - apenas chama o legal-text-extractor.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.prompt import Prompt

from legal_extractor_cli import __version__
from legal_extractor_cli.logo import print_logo
from legal_extractor_cli.extractor import (
    run_extraction,
    get_system_info,
    check_tesseract,
    check_marker,
    ExtractionProgress,
    ExtractionSummary,
)

# CLI App
app = typer.Typer(
    name="legal-extract",
    help="Extrator Inteligente de Texto Jurídico",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]Legal Extractor CLI[/bold cyan] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Exibe a versão e sai"
    ),
):
    """
    Legal Extractor CLI - Extrai texto de PDFs jurídicos de forma inteligente.

    Detecta automaticamente o melhor método de extração para cada página:
    - pdfplumber para páginas com texto nativo
    - Tesseract para scans limpos
    - Marker para scans degradados (requer RAM)
    """
    pass


@app.command()
def extract(
    pdf_path: Optional[Path] = typer.Argument(
        None,
        help="Caminho para o arquivo PDF",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Diretório de saída (padrão: outputs/{nome_arquivo}/)"
    ),
    system: Optional[str] = typer.Option(
        None, "--system", "-s",
        help="Sistema judicial forçado (PJE, ESAJ, EPROC) - padrão: auto"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q",
        help="Modo silencioso (sem logo)"
    ),
):
    """
    Extrai texto de um PDF jurídico.

    Exemplo:
        legal-extract extract documento.pdf
        legal-extract extract documento.pdf -o ./saida/
        legal-extract extract documento.pdf --system PJE
    """
    # Mostra logo (a menos que --quiet)
    if not quiet:
        print_logo(console, style="compact")

    # Se PDF não foi passado como argumento, pede interativamente
    if pdf_path is None:
        pdf_path_str = Prompt.ask(
            "[bold cyan]Caminho do arquivo PDF[/bold cyan]",
            console=console,
        )
        pdf_path = Path(pdf_path_str).resolve()

        if not pdf_path.exists():
            console.print(f"[bold red]Erro:[/bold red] Arquivo não encontrado: {pdf_path}")
            raise typer.Exit(1)

        if not pdf_path.suffix.lower() == ".pdf":
            console.print(f"[bold red]Erro:[/bold red] Arquivo não é PDF: {pdf_path}")
            raise typer.Exit(1)

    # Mostra info do arquivo
    console.print(Panel(
        f"[bold]Arquivo:[/bold] {pdf_path.name}\n"
        f"[bold]Tamanho:[/bold] {pdf_path.stat().st_size / 1024:.1f} KB\n"
        f"[bold]Caminho:[/bold] {pdf_path.parent}",
        title="[cyan]PDF Selecionado[/cyan]",
        border_style="cyan"
    ))

    # Executa extração com progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processando...", total=100)

        def on_progress(p: ExtractionProgress):
            progress.update(
                task,
                completed=int(p.percentage * 100),
                description=f"[cyan]{p.message}"
            )

        result = run_extraction(
            pdf_path=pdf_path,
            output_dir=output,
            system=system,
            progress_callback=on_progress,
        )

    # Mostra resultado
    _show_result(result)


def _show_result(result: ExtractionSummary):
    """Exibe resultado da extração."""
    if result.success:
        # Tabela de estatísticas
        table = Table(title="[bold green]Extração Concluída[/bold green]", border_style="green")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="white")

        table.add_row("Total de páginas", str(result.total_pages))
        table.add_row("Páginas nativas", str(result.native_pages))
        table.add_row("Páginas OCR", str(result.raster_pages))
        table.add_row("Engine(s)", result.engine_used)
        table.add_row("Tempo", f"{result.processing_time_s:.1f}s")
        table.add_row("Texto final", f"{result.final_text_length:,} chars")
        table.add_row("Redução", f"{result.reduction_pct:.1f}%")

        console.print(table)

        if result.output_path:
            console.print(f"\n[bold green]Output:[/bold green] {result.output_path}")

    else:
        console.print(Panel(
            f"[bold red]Erro na extração[/bold red]\n\n{result.error}",
            border_style="red"
        ))
        raise typer.Exit(1)


@app.command()
def info():
    """
    Mostra informações do sistema e engines disponíveis.
    """
    print_logo(console, style="compact")

    sys_info = get_system_info()

    # Tabela de sistema
    table = Table(title="[bold cyan]Informações do Sistema[/bold cyan]", border_style="cyan")
    table.add_column("Item", style="cyan")
    table.add_column("Valor", style="white")

    table.add_row("Hostname", sys_info["hostname"])
    table.add_row("RAM Total", f"{sys_info['total_ram_gb']:.1f} GB")
    table.add_row("RAM Disponível", f"{sys_info['available_ram_gb']:.1f} GB")
    table.add_row("Plataforma", sys_info["platform"])
    table.add_row("PC Trabalho?", "[green]Sim[/green]" if sys_info["is_work_pc"] else "[yellow]Não[/yellow]")

    console.print(table)

    # Tabela de engines
    engines_table = Table(title="[bold cyan]Engines Disponíveis[/bold cyan]", border_style="cyan")
    engines_table.add_column("Engine", style="cyan")
    engines_table.add_column("Status", style="white")
    engines_table.add_column("Uso", style="dim")

    # pdfplumber (sempre disponível)
    engines_table.add_row("pdfplumber", "[green]Disponível[/green]", "Texto nativo")

    # Tesseract
    tesseract_ok = check_tesseract()
    engines_table.add_row(
        "Tesseract",
        "[green]Disponível[/green]" if tesseract_ok else "[red]Não instalado[/red]",
        "OCR (scans limpos)"
    )

    # Marker
    marker_ok = check_marker()
    marker_status = "[green]Disponível[/green]" if marker_ok else "[yellow]Não instalado[/yellow]"
    if marker_ok and not sys_info["marker_available"]:
        marker_status = "[yellow]RAM insuficiente[/yellow]"
    engines_table.add_row("Marker", marker_status, "OCR (scans degradados)")

    console.print(engines_table)

    # Recomendação
    if sys_info["is_work_pc"] and sys_info["marker_available"]:
        console.print("\n[green]Sistema configurado para uso completo (Marker disponível)[/green]")
    elif not tesseract_ok:
        console.print("\n[red]Instale Tesseract: sudo apt install tesseract-ocr tesseract-ocr-por[/red]")


@app.command()
def batch(
    input_dir: Path = typer.Argument(
        ...,
        help="Diretório com PDFs para processar",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Diretório de saída (padrão: {input_dir}/outputs/)"
    ),
):
    """
    Processa múltiplos PDFs em lote.

    Exemplo:
        legal-extract batch ./documentos/
        legal-extract batch ./documentos/ -o ./resultados/
    """
    print_logo(console, style="compact")

    # Encontra PDFs
    pdfs = list(input_dir.glob("*.pdf"))
    if not pdfs:
        console.print(f"[yellow]Nenhum PDF encontrado em {input_dir}[/yellow]")
        raise typer.Exit(0)

    console.print(f"[cyan]Encontrados {len(pdfs)} PDFs[/cyan]\n")

    # Define output dir
    if output_dir is None:
        output_dir = input_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Processa cada PDF
    results = []
    for i, pdf in enumerate(pdfs, 1):
        console.print(f"[dim]({i}/{len(pdfs)})[/dim] [bold]{pdf.name}[/bold]")

        doc_output = output_dir / pdf.stem
        result = run_extraction(
            pdf_path=pdf,
            output_dir=doc_output,
        )

        status = "[green]OK[/green]" if result.success else f"[red]Erro: {result.error}[/red]"
        console.print(f"  {status}")
        results.append((pdf.name, result))

    # Resumo
    console.print("\n" + "=" * 50)
    success_count = sum(1 for _, r in results if r.success)
    console.print(f"[bold]Processados:[/bold] {success_count}/{len(pdfs)} com sucesso")
    console.print(f"[bold]Output:[/bold] {output_dir}")


if __name__ == "__main__":
    app()
