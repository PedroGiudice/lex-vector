"""
Query Builder Component
Interactive jurisprudence search with live SQL preview
"""

from fasthtml.common import *
from typing import List
# Use backend_adapter in Docker, falls back to mock if engines unavailable
try:
    import backend_adapter as mock_data
except ImportError:
    import mock_data


def domain_selector(selected: str = "") -> FT:
    """Legal domain dropdown selector"""

    options = [Option("Selecione...", value="", selected=(selected == ""))]
    for domain in mock_data.DOMAINS:
        options.append(
            Option(domain, value=domain, selected=(selected == domain))
        )

    return Div(
        Label("Área do Direito", cls="block text-sm font-semibold mb-2 text-amber-400"),
        Select(
            *options,
            name="domain",
            id="domain-select",
            cls="input-field",
            hx_get="/sql-preview",
            hx_trigger="change",
            hx_target="#sql-preview-container",
            hx_include="[name='keywords'],[name='acordaos_only']",
        ),
        cls="mb-4"
    )


def keyword_selector(domain: str = "", selected_keywords: List[str] = None) -> FT:
    """Multi-select trigger words with pills"""

    if selected_keywords is None:
        selected_keywords = []

    # Get keywords for domain
    keywords = mock_data.KEYWORDS_BY_DOMAIN.get(domain, []) if domain else []

    if not keywords:
        return Div(
            Label("Palavras-Chave", cls="block text-sm font-semibold mb-2 text-amber-400"),
            P(
                "Selecione uma área do direito para ver palavras-chave disponíveis",
                cls="text-sm text-gray-500 italic py-3"
            ),
            cls="mb-4"
        )

    pills = []
    for kw in keywords:
        is_selected = kw in selected_keywords
        pills.append(
            Label(
                Input(
                    type="checkbox",
                    name="keywords",
                    value=kw,
                    checked=is_selected,
                    cls="hidden",
                    hx_get="/sql-preview",
                    hx_trigger="change",
                    hx_target="#sql-preview-container",
                    hx_include="[name='domain'],[name='keywords'],[name='acordaos_only']",
                ),
                Span(kw, cls="pill" + (" selected" if is_selected else "")),
                cls="inline-block cursor-pointer"
            )
        )

    return Div(
        Label("Palavras-Chave", cls="block text-sm font-semibold mb-2 text-amber-400"),
        Div(*pills, cls="flex flex-wrap gap-2", id="keyword-pills"),
        cls="mb-4"
    )


def acordaos_toggle(checked: bool = False) -> FT:
    """Toggle for 'Somente Acórdãos' with warning badge"""

    return Div(
        Div(
            Label(
                Input(
                    type="checkbox",
                    name="acordaos_only",
                    id="acordaos-toggle",
                    checked=checked,
                    hx_get="/sql-preview",
                    hx_trigger="change",
                    hx_target="#sql-preview-container",
                    hx_include="[name='domain'],[name='keywords']",
                ),
                Span(cls="toggle-slider"),
                cls="toggle-switch"
            ),
            Label(
                "Somente Acórdãos",
                _for="acordaos-toggle",
                cls="ml-3 font-semibold text-sm"
            ),
            cls="flex items-center"
        ),
        Div(
            Span("WARNING", cls="badge badge-warning"),
            Span(
                "Filtra apenas documentos tipo ACORDÃO, excluindo decisões monocráticas",
                cls="text-xs text-gray-400 ml-2"
            ),
            cls="flex items-center mt-2"
        ),
        cls="mb-6"
    )


def template_buttons() -> FT:
    """Quick template buttons for common queries"""

    buttons = []
    for template in mock_data.QUERY_TEMPLATES:
        buttons.append(
            Button(
                template["name"],
                cls="btn-template",
                hx_get=f"/apply-template?name={template['name']}",
                hx_target="#query-form-container",
                hx_swap="outerHTML",
                title=template["description"]
            )
        )

    return Div(
        Label("Templates Rápidos", cls="block text-sm font-semibold mb-2 text-amber-400"),
        Div(*buttons, cls="flex flex-wrap gap-2"),
        cls="mb-6"
    )


def sql_preview_box(sql: str = "") -> FT:
    """Live SQL preview that updates via HTMX"""

    if not sql:
        sql = "-- Selecione filtros acima para gerar a query SQL"

    return Div(
        Pre(sql, cls="sql-preview"),
        id="sql-preview-container"
    )


def search_button() -> FT:
    """Execute search button"""

    return Div(
        Button(
            Div(
                Span("Executar Busca", id="search-text"),
                Span(cls="loading htmx-indicator ml-2", id="search-loading"),
                cls="flex items-center justify-center"
            ),
            cls="btn btn-primary w-full text-base py-3",
            hx_get="/search-results",
            hx_include="[name='domain'],[name='keywords'],[name='acordaos_only']",
            hx_target="#results-container",
            hx_indicator="#search-loading"
        ),
        cls="mt-6"
    )


def query_builder_card(domain: str = "", keywords: List[str] = None, acordaos_only: bool = False) -> FT:
    """Complete query builder card"""

    if keywords is None:
        keywords = []

    return Div(
        Div("Laboratório de Jurisprudência", cls="card-header"),

        Form(
            domain_selector(domain),
            Div(
                keyword_selector(domain, keywords),
                id="keyword-selector-container"
            ),
            acordaos_toggle(acordaos_only),
            template_buttons(),

            # SQL Preview Section
            Div(
                Label("Preview SQL", cls="block text-sm font-semibold mb-2 text-amber-400"),
                sql_preview_box(mock_data.generate_sql_query(domain, keywords, acordaos_only)),
                cls="mb-6"
            ),

            search_button(),

            id="query-form-container",
            hx_ext="json-enc"
        ),

        cls="card"
    )
