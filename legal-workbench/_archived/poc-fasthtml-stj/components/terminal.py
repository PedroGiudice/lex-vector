"""
Terminal Component
Real-time log streaming with server-side proxy pattern
"""

from fasthtml.common import *
from typing import List
import asyncio

# Use backend_adapter in Docker, falls back to mock if engines unavailable
try:
    import backend_adapter as mock_data
except ImportError:
    import mock_data


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
    """Complete download center card with streaming logs and premium styling"""

    return Div(
        # Header with icon
        Div(
            NotStr('<iconify-icon icon="ph:download-bold" width="24" height="24" class="text-amber-400 mr-2"></iconify-icon>'),
            Span("Centro de Download", cls="text-gradient-amber"),
            cls="card-header flex items-center"
        ),

        # Description with icon
        Div(
            NotStr('<iconify-icon icon="ph:info" width="18" height="18" class="text-blue-400 mr-2 flex-shrink-0"></iconify-icon>'),
            P(
                "Demonstração de streaming de logs em tempo real usando HTMX SSE (Server-Sent Events). "
                "Este componente mostra como FastHTML pode fazer proxy de logs do backend para o frontend "
                "sem expor tokens no navegador.",
                cls="text-sm text-gray-400 leading-relaxed"
            ),
            cls="flex items-start mb-6 p-3 rounded-lg bg-blue-500/5 border border-blue-500/20"
        ),

        download_controls(is_running),

        Div(
            Div(
                NotStr('<iconify-icon icon="ph:terminal-window-bold" width="20" height="20" class="text-amber-400 mr-2"></iconify-icon>'),
                Label("Logs de Execução", cls="text-sm font-semibold text-amber-400"),
                cls="flex items-center mb-2"
            ),
            terminal_window(logs, streaming=is_running),
        ),

        # Connection info with icons
        Div(
            Div(
                NotStr('<iconify-icon icon="ph:plugs-connected" width="16" height="16" class="text-gray-500 mr-2"></iconify-icon>'),
                Span("Backend Proxy:", cls="text-xs text-gray-500"),
                Span(" http://stj-service:8000/api/v1/download", cls="font-mono text-xs text-amber-400 ml-2"),
                cls="flex items-center"
            ),
            Div(
                NotStr('<iconify-icon icon="ph:broadcast" width="16" height="16" class="mr-2"></iconify-icon>') if is_running else
                NotStr('<iconify-icon icon="ph:radio" width="16" height="16" class="text-gray-500 mr-2"></iconify-icon>'),
                Span("Status: ", cls="text-xs text-gray-500"),
                Span("CONECTADO" if is_running else "AGUARDANDO",
                     cls=f"text-xs font-bold {'text-green-400' if is_running else 'text-gray-500'}"),
                cls=f"flex items-center {'text-green-400' if is_running else ''}"
            ),
            cls="mt-4 pt-4 border-t border-gray-800 flex items-center justify-between"
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


async def stream_logs_generator(start_date: str = "", end_date: str = ""):
    """
    Async generator for SSE log streaming
    Uses backend_adapter for real streaming or mock for demo
    """
    # Use the stream_download function from backend_adapter
    async for log_line in mock_data.stream_download(start_date, end_date):
        yield log_stream_event(log_line)

    # Final completion message
    await asyncio.sleep(0.5)
    yield log_stream_event("[SYSTEM] Download concluído com sucesso.")
