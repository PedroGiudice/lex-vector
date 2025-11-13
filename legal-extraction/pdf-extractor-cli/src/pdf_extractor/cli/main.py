"""
CLI entry point for PDF Extractor.

Usa Click para interface de linha de comando profissional.
"""

import sys
from pathlib import Path

import click
import pdfplumber

from ..__version__ import __version__
from ..core.cleaner import DocumentCleaner
from ..exporters.text import export_txt


@click.group()
@click.version_option(version=__version__, prog_name="pdf-extractor")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.pass_context
def cli(ctx, debug):
    """
    PDF Extractor CLI - Extração de Documentos Jurídicos Brasileiros

    Ferramenta profissional para extrair e limpar PDFs do sistema judicial brasileiro.

    \b
    Sistemas suportados:
      • PJE (Processo Judicial Eletrônico)
      • ESAJ (Sistema de Automação da Justiça)
      • EPROC (Sistema de Processo Eletrônico)
      • PROJUDI (Processo Judicial Digital)
      • STF (Supremo Tribunal Federal)
      • STJ (Superior Tribunal de Justiça)

    \b
    Exemplos:
      $ pdf-extractor process documento.pdf
      $ pdf-extractor process doc.pdf --system PJE --output resultado.txt
      $ pdf-extractor process doc.pdf -b CONFIDENCIAL -b "USO INTERNO"
      $ pdf-extractor detect documento.pdf
    """
    # Configuração de contexto
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug


@cli.command()
@click.argument("pdf_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (auto-named if not specified)",
)
@click.option(
    "--system",
    "-s",
    default="auto",
    help="Judicial system (auto|PJE|ESAJ|EPROC|PROJUDI|STF|STJ)",
)
@click.option(
    "--blacklist",
    "-b",
    multiple=True,
    help="Custom terms to remove (can be used multiple times)",
)
@click.option(
    "--with-header",
    is_flag=True,
    help="Include header with metadata in output",
)
@click.pass_context
def process(ctx, pdf_file: Path, output: Path | None, system: str, blacklist: tuple, with_header: bool):
    """
    Process a single PDF file.

    Extracts text from PDF and removes judicial signatures and certifications.

    \b
    Example:
        $ pdf-extractor process petição.pdf
        $ pdf-extractor process doc.pdf --system PJE -o clean.txt
        $ pdf-extractor process doc.pdf -b CONFIDENCIAL --with-header
    """
    debug = ctx.obj.get("DEBUG", False)

    # Feedback inicial
    click.echo(f"📄 Processing: {click.style(pdf_file.name, bold=True)}")

    try:
        # 1. Extrai texto do PDF
        if debug:
            click.echo("[DEBUG] Extracting text from PDF...")

        text = extract_text_from_pdf(pdf_file)

        if not text or len(text) < 10:
            click.secho(
                f"❌ Error: PDF contains insufficient text ({len(text)} chars)",
                fg="red",
                err=True,
            )
            sys.exit(1)

        if debug:
            click.echo(f"[DEBUG] Extracted {len(text)} characters")

        # 2. Limpa texto
        click.echo("🧹 Cleaning text...")

        cleaner = DocumentCleaner()
        result = cleaner.clean(
            text=text, system=system if system != "auto" else None, custom_blacklist=list(blacklist) if blacklist else None
        )

        # 3. Mostra estatísticas
        stats = result.stats
        click.echo(
            f"✓ System detected: {click.style(stats.system_name, fg='cyan')} "
            f"({stats.confidence}% confidence)"
        )
        click.echo(
            f"✓ Text cleaned: {stats.original_length:,} → {stats.final_length:,} chars "
            f"({click.style(f'-{stats.reduction_pct:.1f}%', fg='green')})"
        )

        if stats.patterns_removed and debug:
            click.echo(f"[DEBUG] Removed {len(stats.patterns_removed)} pattern types")

        # 4. Exporta
        if output is None:
            output = pdf_file.with_suffix(".txt")

        click.echo(f"💾 Exporting to: {click.style(str(output), fg='blue')}")

        export_txt(result, output, include_header=with_header)

        # 5. Sucesso
        click.secho(f"\n✨ Done! Saved to: {output}", fg="green", bold=True)

    except Exception as e:
        click.secho(f"\n❌ Error: {e}", fg="red", err=True)
        if debug:
            import traceback

            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command()
@click.argument("pdf_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def detect(pdf_file: Path):
    """
    Detect judicial system without cleaning.

    Analyzes PDF and shows which judicial system generated it.

    \b
    Example:
        $ pdf-extractor detect documento.pdf
    """
    click.echo(f"🔍 Analyzing: {click.style(pdf_file.name, bold=True)}")

    try:
        # Extrai texto
        text = extract_text_from_pdf(pdf_file)

        if not text or len(text) < 100:
            click.secho("❌ Error: PDF contains insufficient text for analysis", fg="red", err=True)
            sys.exit(1)

        # Detecta sistema
        cleaner = DocumentCleaner()
        detection = cleaner.detect_only(text)

        # Mostra resultado
        click.echo("\n" + "─" * 60)
        click.echo(f"System: {click.style(detection['name'], fg='cyan', bold=True)}")
        click.echo(f"Code: {detection['system']}")
        click.echo(f"Confidence: {detection['confidence']}%")

        if detection["confidence"] >= 80:
            emoji = "🟢"
        elif detection["confidence"] >= 50:
            emoji = "🟡"
        else:
            emoji = "🔴"

        click.echo(f"Status: {emoji}")

        # Detalhes adicionais
        details = detection.get("details", {})
        if "matches" in details:
            click.echo(f"\nMatches: {details['matches']}/{details['total_patterns']} patterns")

        if "all_results" in details:
            click.echo("\nOther possibilities:")
            for alt in details["all_results"][:3]:
                if alt["system"] != detection["system"]:
                    click.echo(f"  • {alt['system']}: {alt['confidence']}%")

        click.echo("─" * 60)

    except Exception as e:
        click.secho(f"\n❌ Error: {e}", fg="red", err=True)
        sys.exit(1)


@cli.command()
def systems():
    """
    List all supported judicial systems.

    Shows information about each supported system.
    """
    cleaner = DocumentCleaner()
    systems_list = cleaner.get_supported_systems()

    click.echo("\n" + click.style("Supported Judicial Systems", bold=True, underline=True))
    click.echo()

    for idx, system_info in enumerate(systems_list, 1):
        click.echo(
            f"{idx}. {click.style(system_info['code'], fg='cyan', bold=True)} - "
            f"{system_info['name']}"
        )
        click.echo(f"   {system_info['description']}")
        click.echo()


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extrai texto de PDF usando pdfplumber.

    Args:
        pdf_path: Caminho do arquivo PDF

    Returns:
        Texto extraído

    Raises:
        Exception: Se houver erro ao abrir ou processar PDF
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)

            return "\n\n".join(pages_text)

    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {e}")


if __name__ == "__main__":
    cli()
