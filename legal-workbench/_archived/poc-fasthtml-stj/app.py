"""
FastHTML STJ PoC - Main Application
Demonstrates BFF pattern with terminal aesthetic
"""

from fasthtml.common import *
from typing import List, Optional
import asyncio

# Local imports
# Use backend_adapter in Docker, falls back to mock if engines unavailable
try:
    import backend_adapter as mock_data
except ImportError:
    import mock_data
from styles import PREMIUM_STYLE, TAILWIND_CDN, ICONIFY_CDN
from components import query_builder, results, terminal

# Initialize FastHTML app with premium styling
app, rt = fast_app(
    hdrs=(
        # Premium fonts
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap", rel="stylesheet"),
        # Core dependencies
        Script(src=TAILWIND_CDN),
        Script(src="https://unpkg.com/htmx.org@2.0.3"),
        Script(src="https://unpkg.com/htmx-ext-sse@2.2.2/sse.js"),
        Script(src=ICONIFY_CDN),
        # Premium CSS
        NotStr(PREMIUM_STYLE),
    ),
    live=True
)


def app_header() -> FT:
    """Application header with premium styling and icons"""
    return Div(
        Div(
            # Logo and title
            Div(
                # Icon using Iconify
                Span(
                    NotStr('<iconify-icon icon="ph:scales-bold" width="32" height="32"></iconify-icon>'),
                    cls="text-blue-400 mr-3"
                ),
                Div(
                    H1("STJ Jurisprudence Lab", cls="app-title"),
                    P("FastHTML Backend-for-Frontend Demo", cls="app-subtitle"),
                ),
                cls="flex items-center"
            ),
            # Status indicator
            Div(
                Span(
                    NotStr('<iconify-icon icon="ph:circle-fill" width="8" height="8"></iconify-icon>'),
                    cls="text-green-400 mr-2 animate-pulse"
                ),
                Span("Sistema Online", cls="text-xs text-gray-400"),
                cls="flex items-center"
            ),
            cls="flex items-center justify-between"
        ),
        cls="app-header"
    )


@rt("/health")
def get():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "fasthtml-stj"}


@rt("/")
def get_main():
    """Main page"""

    stats = mock_data.get_quick_stats()

    return Html(
        Head(
            Title("STJ Jurisprudence Lab - Legal Workbench"),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            # Premium fonts
            Link(rel="preconnect", href="https://fonts.googleapis.com"),
            Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
            Link(href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap", rel="stylesheet"),
            # Core dependencies
            Script(src=TAILWIND_CDN),
            Script(src="https://unpkg.com/htmx.org@2.0.3"),
            Script(src="https://unpkg.com/htmx-ext-sse@2.2.2/sse.js"),
            Script(src=ICONIFY_CDN),
            # Premium styles
            NotStr(PREMIUM_STYLE),
        ),
        Body(
            app_header(),

            Div(
                # Quick stats
                results.quick_stats_card(stats),

                # Two-column layout
                Div(
                    # Left column - Query Builder
                    Div(
                        query_builder.query_builder_card(),
                        cls="col-span-1"
                    ),

                    # Right column - Results
                    Div(
                        results.results_container(),
                        cls="col-span-1"
                    ),

                    cls="grid-2 mb-6"
                ),

                # Download Center (full width)
                terminal.download_center_card(),

                cls="container"
            )
        )
    )


@rt("/sql-preview")
def get(domain: str = "", keywords: List[str] = None, acordaos_only: bool = False):
    """
    HTMX endpoint: Live SQL preview
    Updates whenever form inputs change
    """

    if keywords is None:
        keywords = []

    # Handle single keyword as string
    if isinstance(keywords, str):
        keywords = [keywords]

    sql = mock_data.generate_sql_query(domain, keywords, acordaos_only)

    return Div(
        Pre(sql, cls="sql-preview"),
        id="sql-preview-container"
    )


@rt("/keyword-selector")
def get(domain: str = "", keywords: List[str] = None):
    """
    HTMX endpoint: Update keyword selector when domain changes
    """

    if keywords is None:
        keywords = []

    # Handle single keyword as string
    if isinstance(keywords, str):
        keywords = [keywords]

    return Div(
        query_builder.keyword_selector(domain, keywords),
        id="keyword-selector-container"
    )


@rt("/search-results")
def get(domain: str = "", keywords: List[str] = None, acordaos_only: bool = False):
    """
    HTMX endpoint: Execute search and return results
    """

    if keywords is None:
        keywords = []

    # Handle single keyword as string
    if isinstance(keywords, str):
        keywords = [keywords]

    # Simulate search delay
    import time
    time.sleep(0.5)

    # Generate mock results
    search_results = mock_data.generate_mock_acordaos(domain, keywords, acordaos_only)

    return results.results_container(search_results, domain, keywords)


@rt("/apply-template")
def get(name: str):
    """
    HTMX endpoint: Apply a query template
    """

    # Find template
    template = None
    for t in mock_data.QUERY_TEMPLATES:
        if t["name"] == name:
            template = t
            break

    if not template:
        return query_builder.query_builder_card()

    # Parse template to extract filters
    # For demo purposes, we'll set some defaults based on template name
    domain = ""
    keywords = []
    acordaos_only = False

    if "Divergência" in name:
        domain = "Direito Civil"
        keywords = ["Dano Moral"]
    elif "Recursos Repetitivos" in name:
        domain = "Direito Tributário"
        keywords = ["ICMS"]
        acordaos_only = True
    elif "Súmulas" in name:
        domain = "Direito Penal"
        keywords = ["Habeas Corpus"]

    return query_builder.query_builder_card(domain, keywords, acordaos_only)


@rt("/start-download")
async def get(start_date: str = "", end_date: str = ""):
    """
    HTMX endpoint: Start download process with streaming logs
    """

    # Return updated card with streaming indicator
    logs = [
        "[2024-12-13 10:23:45] Iniciando processo de download...",
        f"[2024-12-13 10:23:45] Período: {start_date} até {end_date}",
        "[2024-12-13 10:23:45] Conectando ao portal STJ...",
    ]

    # Start streaming in background
    return Div(
        Div("Centro de Download", cls="card-header"),

        P(
            "Demonstração de streaming de logs em tempo real usando HTMX SSE (Server-Sent Events). "
            "Este componente mostra como FastHTML pode fazer proxy de logs do backend para o frontend "
            "sem expor tokens no navegador.",
            cls="text-sm text-gray-400 mb-6 leading-relaxed"
        ),

        # Disabled controls while running
        terminal.download_controls(is_running=True),

        Div(
            Label("Logs de Execução", cls="block text-sm font-semibold mb-2 text-amber-400"),

            # Terminal with SSE streaming
            Div(
                # Initial logs
                Div("[2024-12-13 10:23:45] Iniciando processo de download...", cls="terminal-line"),
                Div(f"[2024-12-13 10:23:45] Período: {start_date} até {end_date}", cls="terminal-line"),
                Div("[2024-12-13 10:23:45] Conectando ao portal STJ...", cls="terminal-line"),

                # SSE target for streaming
                Div(
                    hx_ext="sse",
                    sse_connect="/stream-logs",
                    sse_swap="message",
                    sse_close="close",
                    hx_swap="beforeend"
                ),

                cls="terminal",
                id="terminal-output"
            )
        ),

        # Connection info
        Div(
            Span("Backend Proxy:", cls="text-xs text-gray-500"),
            Span(" http://stj-service:8000/api/v1/download", cls="font-mono text-xs text-amber-400 ml-2"),
            Div(
                Span("Status: ", cls="text-xs text-gray-500"),
                Span("CONECTADO", cls="text-xs font-bold text-green-400")
            ),
            cls="mt-4 pt-4 border-t border-gray-800 text-sm"
        ),

        id="download-container",
        cls="card"
    )


@rt("/stream-logs")
async def get(start_date: str = "", end_date: str = ""):
    """
    SSE endpoint: Stream download logs from real backend
    This demonstrates the server-side proxy pattern
    """

    async def event_generator():
        """Generate SSE events"""

        async for log_line in mock_data.stream_download(start_date, end_date):
            await asyncio.sleep(0.3)

            # Determine CSS class based on content
            if "ERROR" in log_line or "FALHA" in log_line:
                cls = "terminal-line terminal-error"
            elif "WARNING" in log_line:
                cls = "terminal-line terminal-warning"
            else:
                cls = "terminal-line"

            # Yield SSE event
            yield f'event: message\ndata: <div class="{cls}">{log_line}</div>\n\n'

        # Send close event
        yield 'event: close\ndata: <div class="terminal-line text-green-400">[SYSTEM] Processo finalizado.</div>\n\n'

    return EventStream(event_generator())


@rt("/reset-download")
def get():
    """Reset download center to initial state"""
    return terminal.download_center_card(is_running=False)


# Error handling
@app.exception_handler(404)
def not_found(request, exc):
    return Div(
        H1("404 - Página não encontrada", cls="text-2xl text-red-400"),
        P("A página solicitada não existe.", cls="text-gray-500 mt-4"),
        A("Voltar ao início", href="/", cls="btn btn-primary mt-6"),
        cls="container text-center py-12"
    )


if __name__ == "__main__":
    print("\n" + "="*60)
    print("STJ FastHTML PoC - Terminal Aesthetic")
    print("="*60)
    print("\nServer starting on http://localhost:5001")
    print("\nFeatures:")
    print("  - Live SQL preview with HTMX")
    print("  - Server-side log streaming (SSE)")
    print("  - Terminal hacker aesthetic")
    print("  - Zero JavaScript (HTMX only)")
    print("\nPress Ctrl+C to stop")
    print("="*60 + "\n")

    serve(port=5001)
