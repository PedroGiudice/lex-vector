"""
FastHTML Workbench - Main Application Shell

A modular legal tools platform with dynamic plugin loading
and module-specific theming.

Usage:
    python main.py

    Or with uvicorn:
    uvicorn main:app --reload --port 5001
"""

import logging
from fasthtml.common import *
from starlette.staticfiles import StaticFiles
from starlette.responses import Response, HTMLResponse

from core import PluginRegistry, Config
from core.config import config
from core.middleware import create_theme_trigger
from themes import get_theme, generate_css, SHARED_THEME
from shared.layouts import app_shell

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================================
# Plugin Discovery
# ============================================================================
registry = PluginRegistry()
registry.discover()

# Log any loading errors
for error in registry.errors:
    logger.warning(error)

# ============================================================================
# FastHTML App Setup
# ============================================================================

# Generate base CSS from shared theme
base_css = generate_css(SHARED_THEME)

# Initialize FastHTML with dependencies
app, rt = fast_app(
    debug=config.DEBUG,
    live=config.DEBUG,  # Live reload in debug mode
    hdrs=(
        # Tailwind CSS (for utility classes)
        Script(src="https://cdn.tailwindcss.com"),
        # HTMX (hypermedia interactions)
        Script(src="https://unpkg.com/htmx.org@2.0.3"),
        # HTMX SSE extension (for streaming)
        Script(src="https://unpkg.com/htmx-ext-sse@2.2.2/sse.js"),
        # Theme CSS (base styles)
        NotStr(base_css),
        # Theme switcher JS
        Script(src="/static/theme-switcher.js", defer=True),
        # Meta
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(charset="utf-8"),
    ),
)

# Mount static files
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

# Mount all discovered plugins
registry.mount_all(app)

# ============================================================================
# Shell Routes
# ============================================================================

@rt("/")
def index():
    """
    Main landing page - renders the app shell with sidebar.
    """
    return Title(f"{config.APP_NAME}"), app_shell(
        plugins=registry.plugins,
        app_name=config.APP_NAME,
    )


@rt("/m/{module_id}/")
def module_redirect(module_id: str):
    """
    Handle direct module URL access.

    Returns the full shell with the module pre-loaded.
    """
    plugin = registry.get(module_id)
    if not plugin:
        return Response("Module not found", status_code=404)

    # Get the module's index content
    # Note: This assumes the module's app has a "/" route
    # We'll render the shell and let HTMX load the content
    return Title(f"{plugin.name} - {config.APP_NAME}"), app_shell(
        plugins=registry.plugins,
        active_id=module_id,
        app_name=config.APP_NAME,
    )


@rt("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "plugins": len(registry.plugins),
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found(request, exc):
    """Custom 404 page."""
    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 - Não Encontrado</title>
            <style>
                body {{
                    background: #0a0f1a;
                    color: #e2e8f0;
                    font-family: system-ui, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                }}
                .container {{
                    text-align: center;
                }}
                h1 {{
                    font-size: 4rem;
                    color: #f59e0b;
                    margin-bottom: 1rem;
                }}
                p {{
                    color: #94a3b8;
                    margin-bottom: 2rem;
                }}
                a {{
                    color: #f59e0b;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>404</h1>
                <p>A página que você procura não foi encontrada.</p>
                <a href="/">← Voltar ao início</a>
            </div>
        </body>
        </html>
        """,
        status_code=404,
    )


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    logger.info(f"Loaded plugins: {[p.name for p in registry.plugins]}")
    logger.info(f"Server running at http://{config.HOST}:{config.PORT}")

    serve(host=config.HOST, port=config.PORT)
