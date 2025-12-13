"""
Terminal Component
Real-time log streaming with server-side proxy pattern
"""

from fasthtml.common import *
from typing import List
import asyncio


def terminal_window(log_lines: List[str] = None, streaming: bool = False) -> FT:
    """Terminal-style output window"""

    if log_lines is None:
        log_lines = ["[SYSTEM] Terminal pronto. Aguardando comandos..."]

    lines = []
    for line in log_lines:
        # Color-code based on content
        if "ERROR" in line or "FALHA" in line or "Erro" in line:
            cls = "terminal-line terminal-error"
        elif "WARNING" in line or "AVISO" in line:
            cls = "terminal-line terminal-warning"
        else:
            cls = "terminal-line"

        lines.append(Div(line, cls=cls))

    # Add streaming indicator if active
    if streaming:
        lines.append(
            Div(
                Span("_", cls="animate-pulse"),
                cls="terminal-line text-amber-400"
            )
        )

    return Div(
        *lines,
        id="terminal-output",
        cls="terminal"
    )


def download_controls(is_running: bool = False) -> FT:
    """Controls for starting/stopping download process"""

    if is_running:
        return Div(
            Button(
                Span("Procesando...", cls="mr-2"),
                Span(cls="loading"),
                cls="btn btn-secondary w-full",
                disabled=True
            ),
            cls="mb-4"
        )

    return Div(
        Div(
            Input(
                type="date",
                name="start_date",
                cls="input-field mr-2",
                value="2024-01-01",
                style="width: auto; display: inline-block;"
            ),
            Span("até", cls="text-gray-500 mx-2"),
            Input(
                type="date",
                name="end_date",
                cls="input-field mr-2",
                value="2024-12-31",
                style="width: auto; display: inline-block;"
            ),
            cls="mb-4 flex items-center"
        ),
        Button(
            "Iniciar Download",
            cls="btn btn-primary w-full",
            hx_get="/start-download",
            hx_target="#download-container",
            hx_swap="outerHTML",
            hx_include="[name='start_date'],[name='end_date']"
        )
    )


def download_center_card(is_running: bool = False, logs: List[str] = None) -> FT:
    """Complete download center card with streaming logs"""

    return Div(
        Div("Centro de Download", cls="card-header"),

        P(
            "Demonstração de streaming de logs em tempo real usando HTMX SSE (Server-Sent Events). "
            "Este componente mostra como FastHTML pode fazer proxy de logs do backend para o frontend "
            "sem expor tokens no navegador.",
            cls="text-sm text-gray-400 mb-6 leading-relaxed"
        ),

        download_controls(is_running),

        Div(
            Label("Logs de Execução", cls="block text-sm font-semibold mb-2 text-amber-400"),
            terminal_window(logs, streaming=is_running),
        ),

        # Connection info
        Div(
            Span("Backend Proxy:", cls="text-xs text-gray-500"),
            Span(" http://stj-service:8000/api/v1/download", cls="font-mono text-xs text-amber-400 ml-2"),
            Div(
                Span("Status: ", cls="text-xs text-gray-500"),
                Span("CONECTADO" if is_running else "AGUARDANDO",
                     cls=f"text-xs font-bold {'text-green-400' if is_running else 'text-gray-500'}")
            ),
            cls="mt-4 pt-4 border-t border-gray-800 text-sm"
        ),

        id="download-container",
        cls="card"
    )


def log_stream_event(line: str) -> str:
    """Format a single log line as SSE event"""

    # Determine line class based on content
    if "ERROR" in line or "FALHA" in line:
        cls = "terminal-line terminal-error"
    elif "WARNING" in line or "AVISO" in line:
        cls = "terminal-line terminal-warning"
    else:
        cls = "terminal-line"

    return f'<div class="{cls}">{line}</div>'


async def stream_logs_generator():
    """
    Async generator for SSE log streaming
    In production, this would connect to the real backend service
    """

    from mock_data import get_streaming_logs

    logs = get_streaming_logs()

    # Simulate real-time streaming
    for log_line in logs:
        await asyncio.sleep(0.3)  # Simulate delay between log lines
        yield log_stream_event(log_line)

    # Final completion message
    await asyncio.sleep(0.5)
    yield log_stream_event("[SYSTEM] Download concluído com sucesso.")
