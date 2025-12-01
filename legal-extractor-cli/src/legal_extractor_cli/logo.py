"""Logo ASCII para o Legal Extractor CLI."""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel

# Logo inspirado no VIBE do TUI original
LOGO_ASCII = r'''
██╗     ███████╗ ██████╗  █████╗ ██╗
██║     ██╔════╝██╔════╝ ██╔══██╗██║
██║     █████╗  ██║  ███╗███████║██║
██║     ██╔══╝  ██║   ██║██╔══██║██║
███████╗███████╗╚██████╔╝██║  ██║███████╗
╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝

███████╗██╗  ██╗████████╗██████╗  █████╗  ██████╗████████╗ ██████╗ ██████╗
██╔════╝╚██╗██╔╝╚══██╔══╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
█████╗   ╚███╔╝    ██║   ██████╔╝███████║██║        ██║   ██║   ██║██████╔╝
██╔══╝   ██╔██╗    ██║   ██╔══██╗██╔══██║██║        ██║   ██║   ██║██╔══██╗
███████╗██╔╝ ██╗   ██║   ██║  ██║██║  ██║╚██████╗   ██║   ╚██████╔╝██║  ██║
╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
'''

LOGO_COMPACT = r'''
╦  ╔═╗╔═╗╔═╗╦    ╔═╗═╗ ╦╔╦╗╦═╗╔═╗╔═╗╔╦╗╔═╗╦═╗
║  ║╣ ║ ╦╠═╣║    ║╣ ╔╩╦╝ ║ ╠╦╝╠═╣║   ║ ║ ║╠╦╝
╩═╝╚═╝╚═╝╩ ╩╩═╝  ╚═╝╩ ╚═ ╩ ╩╚═╩ ╩╚═╝ ╩ ╚═╝╩╚═
'''

def print_logo(console: Console, style: str = "full"):
    """
    Exibe o logo no console.

    Args:
        console: Console Rich para output
        style: "full" para logo completo, "compact" para versão menor
    """
    logo = LOGO_ASCII if style == "full" else LOGO_COMPACT

    # Cria texto com gradiente de cor
    text = Text(logo)
    text.stylize("bold cyan")

    console.print(text)
    console.print("[dim]Extrator Inteligente de Texto Jurídico[/dim]", justify="center")
    console.print("[dim]v0.1.0 | Tesseract + Marker + pdfplumber[/dim]", justify="center")
    console.print()


def print_banner(console: Console, message: str = ""):
    """
    Exibe um banner simples com mensagem opcional.

    Args:
        console: Console Rich para output
        message: Mensagem adicional (opcional)
    """
    panel_content = "[bold cyan]Legal Extractor CLI[/bold cyan]"
    if message:
        panel_content += f"\n[dim]{message}[/dim]"

    console.print(Panel(panel_content, border_style="cyan"))
