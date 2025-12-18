"""
Results Component
Display search results with outcome badges and metadata
"""

from fasthtml.common import *
from typing import List, Dict, Optional

# ASCII art import - will be provided by another agent
# from .ascii_art import EMPTY_STATE_ART
# Placeholder for now:
EMPTY_STATE_ART = """
    ╔══════════════════════════════════╗
    ║   Nenhum resultado encontrado   ║
    ╚══════════════════════════════════╝
"""


def outcome_badge(outcome: str) -> FT:
    """Render outcome badge with appropriate styling"""

    badge_classes = {
        "PROVIDO": "badge-provido",
        "DESPROVIDO": "badge-desprovido",
        "PARCIAL": "badge-parcial",
    }

    cls = badge_classes.get(outcome, "badge-parcial")

    return Span(outcome, cls=f"badge {cls}")


def case_preview_modal(case: dict) -> FT:
    """
    Modal overlay for case preview (Obsidian Canvas style).

    Args:
        case: Case dictionary with keys: id, processo, outcome, relator,
              data, ementa, metadata (dict)

    Returns:
        FT modal component with backdrop and preview content
    """
    # Truncate ementa to 500 chars
    ementa_preview = case.get("ementa", "")
    if len(ementa_preview) > 500:
        ementa_preview = ementa_preview[:500] + "..."

    # Extract metadata pills
    metadata = case.get("metadata", {})
    metadata_pills = []
    for key, value in metadata.items():
        if value:  # Only show non-empty metadata
            metadata_pills.append(
                Span(f"{key}: {value}", cls="pill")
            )

    return Div(
        # Backdrop (click to close)
        Div(
            cls="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm z-40",
            hx_get="/close-modal",
            hx_target="#modal-container",
            hx_swap="innerHTML",
        ),

        # Modal container (centered)
        Div(
            # Header
            Div(
                Div(
                    Span(case.get("processo", ""), cls="font-mono text-xl font-bold text-amber-400"),
                    Button(
                        "✕",
                        cls="text-gray-400 hover:text-white text-2xl font-bold",
                        hx_get="/close-modal",
                        hx_target="#modal-container",
                        hx_swap="innerHTML",
                    ),
                    cls="flex items-center justify-between mb-4"
                ),
                cls="border-b border-gray-800 pb-4"
            ),

            # Preview content
            Div(
                # Outcome badge
                Div(
                    Span("Resultado: ", cls="text-sm text-gray-500 mr-2"),
                    outcome_badge(case.get("outcome", "")),
                    cls="mb-4"
                ),

                # Relator
                Div(
                    Span("Relator: ", cls="text-sm text-gray-500"),
                    Span(case.get("relator", ""), cls="text-sm text-gray-300 ml-2"),
                    cls="mb-2"
                ),

                # Publication date
                Div(
                    Span("Data de Publicação: ", cls="text-sm text-gray-500"),
                    Span(case.get("data", ""), cls="text-sm text-gray-300 ml-2 font-mono"),
                    cls="mb-4"
                ),

                # Ementa preview
                Div(
                    Div("Ementa (preview)", cls="text-sm font-bold text-amber-400 mb-2"),
                    P(ementa_preview, cls="text-sm text-gray-300 leading-relaxed"),
                    cls="mb-4 pb-4 border-b border-gray-800"
                ),

                # Metadata pills
                Div(
                    Div("Metadata", cls="text-sm font-bold text-amber-400 mb-2"),
                    Div(*metadata_pills, cls="flex flex-wrap gap-2") if metadata_pills else
                        Span("Sem metadata adicional", cls="text-xs text-gray-500"),
                    cls="mb-6"
                ),

                cls="py-4"
            ),

            # Footer
            Div(
                Button(
                    "Ver Detalhes Completos",
                    cls="btn btn-primary mr-2",
                    hx_get=f"/case/{case.get('id', '')}",
                    hx_target="#modal-container",
                    hx_swap="innerHTML",
                ),
                Button(
                    "Fechar",
                    cls="btn btn-secondary",
                    hx_get="/close-modal",
                    hx_target="#modal-container",
                    hx_swap="innerHTML",
                ),
                cls="flex justify-end gap-2 pt-4 border-t border-gray-800"
            ),

            cls="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-900 border border-gray-800 rounded-lg p-6 max-w-3xl w-full max-h-[80vh] overflow-y-auto z-50 shadow-2xl",
        ),

        id="modal-container"
    )


def case_full_view(case: dict) -> FT:
    """
    Full case details view (can be in modal or replace results).

    Args:
        case: Full case dictionary with all fields including texto_integral

    Returns:
        FT component with complete case information
    """
    # Check if texto_integral exists
    has_full_text = bool(case.get("texto_integral"))

    # Extract metadata
    metadata = case.get("metadata", {})
    metadata_rows = []
    for key, value in metadata.items():
        if value:
            metadata_rows.append(
                Tr(
                    Td(key, cls="text-sm text-gray-500 font-bold py-2"),
                    Td(value, cls="text-sm text-gray-300 py-2"),
                )
            )

    return Div(
        # Backdrop
        Div(
            cls="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm z-40",
            hx_get="/close-modal",
            hx_target="#modal-container",
            hx_swap="innerHTML",
        ),

        # Modal container
        Div(
            # Header
            Div(
                Div(
                    Span(case.get("processo", ""), cls="font-mono text-xl font-bold text-amber-400"),
                    Button(
                        "✕",
                        cls="text-gray-400 hover:text-white text-2xl font-bold",
                        hx_get="/close-modal",
                        hx_target="#modal-container",
                        hx_swap="innerHTML",
                    ),
                    cls="flex items-center justify-between mb-4"
                ),
                cls="border-b border-gray-800 pb-4"
            ),

            # Full content
            Div(
                # Outcome and basic info
                Div(
                    Div(
                        Span("Resultado: ", cls="text-sm text-gray-500 mr-2"),
                        outcome_badge(case.get("outcome", "")),
                    ),
                    Div(
                        Span("Relator: ", cls="text-sm text-gray-500"),
                        Span(case.get("relator", ""), cls="text-sm text-gray-300 ml-2"),
                    ),
                    Div(
                        Span("Turma: ", cls="text-sm text-gray-500"),
                        Span(case.get("turma", ""), cls="text-sm text-gray-300 ml-2"),
                    ),
                    Div(
                        Span("Data de Publicação: ", cls="text-sm text-gray-500"),
                        Span(case.get("data", ""), cls="text-sm text-gray-300 ml-2 font-mono"),
                    ),
                    cls="grid grid-cols-2 gap-4 mb-6 pb-4 border-b border-gray-800"
                ),

                # Ementa (full)
                Div(
                    Div("Ementa Completa", cls="text-sm font-bold text-amber-400 mb-2"),
                    P(case.get("ementa", ""), cls="text-sm text-gray-300 leading-relaxed"),
                    cls="mb-6 pb-4 border-b border-gray-800"
                ),

                # Metadata table
                Div(
                    Div("Metadata Completa", cls="text-sm font-bold text-amber-400 mb-2"),
                    Table(
                        Tbody(*metadata_rows),
                        cls="w-full"
                    ) if metadata_rows else Span("Sem metadata adicional", cls="text-xs text-gray-500"),
                    cls="mb-6 pb-4 border-b border-gray-800"
                ),

                # Texto integral (collapsible)
                Details(
                    Summary(
                        "Texto Integral",
                        cls="text-sm font-bold text-amber-400 cursor-pointer hover:text-amber-300"
                    ),
                    Div(
                        Pre(case.get("texto_integral", "Texto integral não disponível"),
                            cls="text-xs text-gray-300 leading-relaxed mt-4 p-4 bg-gray-950 rounded border border-gray-800 overflow-x-auto"),
                    ),
                    cls="mb-6"
                ) if has_full_text else Div(
                    Div("Texto Integral", cls="text-sm font-bold text-amber-400 mb-2"),
                    Span("Texto integral não disponível para este acórdão", cls="text-xs text-gray-500"),
                    cls="mb-6 pb-4 border-b border-gray-800"
                ),

                cls="py-4"
            ),

            # Footer with actions
            Div(
                Div(
                    Button(
                        "Download PDF",
                        cls="btn btn-secondary mr-2",
                        hx_get=f"/export/pdf/{case.get('id', '')}",
                        hx_indicator="#loading-indicator"
                    ),
                    Button(
                        "Download JSON",
                        cls="btn btn-secondary mr-2",
                        hx_get=f"/export/json/{case.get('id', '')}",
                    ),
                    Button(
                        "Enviar para Doc Assembler",
                        cls="btn btn-primary mr-2",
                        hx_post=f"/send-to-assembler/{case.get('id', '')}",
                    ),
                    cls="flex gap-2"
                ),
                Button(
                    "Fechar",
                    cls="btn btn-secondary",
                    hx_get="/close-modal",
                    hx_target="#modal-container",
                    hx_swap="innerHTML",
                ),
                cls="flex justify-between items-center pt-4 border-t border-gray-800"
            ),

            cls="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-900 border border-gray-800 rounded-lg p-6 max-w-5xl w-full max-h-[90vh] overflow-y-auto z-50 shadow-2xl",
        ),

        id="modal-container"
    )


def empty_results_display() -> FT:
    """
    ASCII art display when no results found.
    Obsidian/VS Code/GitHub style empty state.

    Returns:
        FT component with ASCII art and helpful message
    """
    return Div(
        # ASCII art (centered, monospace)
        Pre(
            EMPTY_STATE_ART,
            cls="font-mono text-amber-400 text-center mb-4 text-xs"
        ),

        # Message
        P(
            "Nenhum resultado encontrado",
            cls="text-center text-gray-400 text-lg font-semibold mb-2"
        ),

        # Suggestions
        Div(
            P("Sugestões:", cls="text-sm text-gray-500 mb-2"),
            Ul(
                Li("Tente ajustar os filtros de busca", cls="text-sm text-gray-400"),
                Li("Verifique se as palavras-chave estão corretas", cls="text-sm text-gray-400"),
                Li("Experimente termos mais genéricos", cls="text-sm text-gray-400"),
                cls="list-disc list-inside space-y-1"
            ),
            cls="text-center max-w-md mx-auto"
        ),

        cls="py-12"
    )


def pagination_controls(total: int, offset: int = 0, limit: int = 25) -> FT:
    """
    Pagination bar with navigation and results per page selector.

    Args:
        total: Total number of results
        offset: Current offset (starting position)
        limit: Results per page

    Returns:
        FT pagination component
    """
    # Calculate pages
    current_page = (offset // limit) + 1
    total_pages = (total + limit - 1) // limit  # Ceiling division

    # Previous/Next offsets
    prev_offset = max(0, offset - limit)
    next_offset = min(total - limit, offset + limit)

    # Disable buttons at boundaries
    prev_disabled = offset == 0
    next_disabled = offset + limit >= total

    return Div(
        # Navigation buttons
        Div(
            Button(
                "← Anterior",
                cls=f"btn btn-secondary {'opacity-50 cursor-not-allowed' if prev_disabled else ''}",
                hx_get=f"/api/search?offset={prev_offset}&limit={limit}",
                hx_target="#results-container",
                hx_swap="outerHTML",
                disabled=prev_disabled,
            ),

            Span(
                f"Página {current_page} de {total_pages}",
                cls="text-sm text-gray-400 font-mono mx-4"
            ),

            Button(
                "Próxima →",
                cls=f"btn btn-secondary {'opacity-50 cursor-not-allowed' if next_disabled else ''}",
                hx_get=f"/api/search?offset={next_offset}&limit={limit}",
                hx_target="#results-container",
                hx_swap="outerHTML",
                disabled=next_disabled,
            ),

            cls="flex items-center justify-center"
        ),

        # Results per page selector
        Div(
            Span("Resultados por página: ", cls="text-xs text-gray-500 mr-2"),
            Select(
                Option("25", value="25", selected=(limit == 25)),
                Option("50", value="50", selected=(limit == 50)),
                Option("100", value="100", selected=(limit == 100)),
                cls="input-field w-20",
                hx_get="/api/search",
                hx_trigger="change",
                hx_target="#results-container",
                hx_swap="outerHTML",
                hx_include="[name='offset']",
                name="limit"
            ),
            cls="flex items-center justify-center mt-4"
        ),

        cls="py-4 border-t border-gray-800 mt-6"
    )


def export_options_dropdown(current_query: Optional[dict] = None) -> FT:
    """
    Dropdown menu for export options.

    Args:
        current_query: Current search query parameters for export

    Returns:
        FT dropdown component
    """
    # Build query string for export
    query_params = ""
    if current_query:
        params = []
        for key, value in current_query.items():
            if isinstance(value, list):
                for v in value:
                    params.append(f"{key}={v}")
            else:
                params.append(f"{key}={value}")
        query_params = "&".join(params)

    return Details(
        Summary(
            "Exportar Resultados",
            cls="btn btn-secondary cursor-pointer inline-block"
        ),
        Div(
            Button(
                "📄 Exportar CSV",
                cls="btn btn-secondary w-full mb-2 text-left",
                hx_get=f"/export/csv?{query_params}",
                hx_indicator="#loading-indicator"
            ),
            Button(
                "📋 Exportar JSON",
                cls="btn btn-secondary w-full mb-2 text-left",
                hx_get=f"/export/json?{query_params}",
                hx_indicator="#loading-indicator"
            ),
            Button(
                "📑 Exportar PDF",
                cls="btn btn-secondary w-full mb-2 text-left",
                hx_get=f"/export/pdf?{query_params}",
                hx_indicator="#loading-indicator"
            ),
            Button(
                "🔧 Enviar para Doc Assembler",
                cls="btn btn-primary w-full text-left",
                hx_post=f"/send-to-assembler?{query_params}",
            ),
            cls="absolute right-0 mt-2 w-64 bg-gray-900 border border-gray-800 rounded-lg shadow-xl p-2 z-10"
        ),
        cls="relative inline-block"
    )


def acordao_card(result: dict) -> FT:
    """
    Individual case card (clickable to open preview modal).

    Args:
        result: Case result dictionary

    Returns:
        FT card component
    """
    return Div(
        Div(
            # Header row
            Div(
                Span(result["processo"], cls="font-mono text-sm font-bold text-amber-400"),
                outcome_badge(result["outcome"]),
                cls="flex items-center justify-between mb-2"
            ),

            # Relator and date
            Div(
                Div(
                    Span("Relator: ", cls="text-xs text-gray-500"),
                    Span(result["relator"], cls="text-xs text-gray-300"),
                ),
                Div(
                    Span(result["data"], cls="text-xs text-gray-500 font-mono"),
                ),
                cls="flex items-center justify-between mb-2"
            ),

            # Ementa preview
            P(
                result["ementa"][:200] + "..." if len(result["ementa"]) > 200 else result["ementa"],
                cls="text-sm text-gray-300 leading-relaxed mb-3"
            ),

            # Footer
            Div(
                Span(f"{result.get('citacoes', 0)} citações", cls="text-xs text-amber-400 font-mono"),
                Button(
                    "Ver Preview",
                    cls="btn btn-secondary text-xs py-1 px-3",
                ),
                cls="flex items-center justify-between"
            ),

            cls="p-4"
        ),

        # Make entire card clickable
        hx_get=f"/api/case-preview/{result.get('id', '')}",
        hx_target="#modal-container",
        hx_swap="innerHTML",
        cls="card hover:bg-gray-800 transition-colors cursor-pointer"
    )


def results_table(results: List[Dict]) -> FT:
    """Render results as a data table"""

    if not results:
        return empty_results_display()

    rows = []
    for result in results:
        rows.append(
            Tr(
                Td(
                    Div(result["processo"], cls="font-mono text-sm"),
                    Div(result["data"], cls="text-xs text-gray-500 mt-1")
                ),
                Td(outcome_badge(result["outcome"])),
                Td(
                    Div(result["relator"], cls="text-sm"),
                    Div(result["turma"], cls="text-xs text-gray-500 mt-1")
                ),
                Td(
                    P(result["ementa"], cls="text-sm leading-relaxed"),
                    cls="max-w-2xl"
                ),
                Td(
                    Div(
                        Span(str(result["citacoes"]), cls="font-mono text-amber-400 text-lg font-bold"),
                        Div("citações", cls="text-xs text-gray-500")
                    ),
                    cls="text-center"
                ),
                # Make row clickable
                hx_get=f"/api/case-preview/{result.get('id', '')}",
                hx_target="#modal-container",
                hx_swap="innerHTML",
                cls="cursor-pointer hover:bg-gray-800"
            )
        )

    return Table(
        Thead(
            Tr(
                Th("Processo", style="width: 180px"),
                Th("Resultado", style="width: 120px"),
                Th("Relator / Turma", style="width: 200px"),
                Th("Ementa"),
                Th("Citações", style="width: 100px"),
            )
        ),
        Tbody(*rows),
        cls="results-table"
    )


def results_stats(count: int, execution_time: float = 0.0) -> FT:
    """Display search statistics"""

    return Div(
        Div(
            Span(str(count), cls="font-mono text-2xl font-bold text-amber-400"),
            Span(" resultados encontrados", cls="text-sm text-gray-400 ml-2")
        ),
        Div(
            Span("Tempo de execução: ", cls="text-xs text-gray-500"),
            Span(f"{execution_time:.2f}s", cls="font-mono text-xs text-green-400")
        ) if execution_time > 0 else None,
        cls="flex items-center justify-between mb-4 pb-4 border-b border-gray-800"
    )


def export_buttons(current_query: Optional[dict] = None) -> FT:
    """Export options for results (replaced by dropdown)"""
    return export_options_dropdown(current_query)


def results_container(results: List[Dict] = None, domain: str = "", keywords: List[str] = None,
                     total: int = 0, offset: int = 0, limit: int = 25) -> FT:
    """
    Complete results container with stats, export, table, and pagination.

    Args:
        results: List of result dictionaries
        domain: Current domain filter
        keywords: Current keywords filter
        total: Total number of results (for pagination)
        offset: Current offset
        limit: Results per page

    Returns:
        FT results container component
    """

    if results is None:
        # Initial state - no search yet
        return Div(
            Div(
                P("Configure os filtros acima e clique em 'Executar Busca'", cls="text-center text-gray-500 py-12"),
                cls="card"
            ),
            id="results-container"
        )

    import time
    execution_time = round(time.time() % 1, 3)  # Mock execution time

    filter_summary = []
    if domain:
        filter_summary.append(f"Área: {domain}")
    if keywords:
        filter_summary.append(f"Palavras-chave: {', '.join(keywords)}")

    # Build current query for export
    current_query = {}
    if domain:
        current_query['domain'] = domain
    if keywords:
        current_query['keywords'] = keywords

    return Div(
        Div(
            # Header with title and export
            Div(
                Div("Resultados da Busca", cls="card-header"),
                export_options_dropdown(current_query),
                cls="flex items-center justify-between mb-4"
            ),

            # Filter summary
            Div(
                Span("Filtros aplicados: ", cls="text-xs text-gray-500"),
                Span(" | ".join(filter_summary) if filter_summary else "Nenhum filtro",
                     cls="text-xs text-amber-400 font-mono ml-2")
            ) if filter_summary else None,

            results_stats(len(results) if results else 0, execution_time),

            # Results (table or empty state)
            results_table(results) if results else empty_results_display(),

            # Pagination (only show if there are results)
            pagination_controls(total or len(results) if results else 0, offset, limit) if results else None,

            cls="card"
        ),
        id="results-container"
    )


def quick_stats_card(stats: Dict) -> FT:
    """Display quick statistics dashboard with premium icons"""

    return Div(
        Div(
            NotStr('<iconify-icon icon="ph:chart-bar-bold" width="24" height="24" class="text-blue-400 mr-2"></iconify-icon>'),
            Span("Estatísticas Rápidas", cls="text-gradient-blue"),
            cls="card-header flex items-center"
        ),

        Div(
            # Total acordãos
            Div(
                Div(
                    Div(
                        NotStr('<iconify-icon icon="ph:files-bold" width="28" height="28" class="text-amber-400 mb-2"></iconify-icon>'),
                        cls="flex justify-center"
                    ),
                    Span(f"{stats['total_acordaos']:,}", cls="font-mono text-3xl font-bold text-gradient-amber"),
                    P("Acórdãos no banco", cls="text-xs text-gray-500 mt-1")
                ),
                cls="text-center p-4 rounded-xl bg-gradient-to-b from-amber-500/10 to-transparent border border-amber-500/20"
            ),

            # Last update
            Div(
                Div(
                    Div(
                        NotStr('<iconify-icon icon="ph:clock-bold" width="28" height="28" class="text-green-400 mb-2"></iconify-icon>'),
                        cls="flex justify-center"
                    ),
                    Span(stats['ultima_atualizacao'], cls="font-mono text-lg text-green-400"),
                    P("Última atualização", cls="text-xs text-gray-500 mt-1")
                ),
                cls="text-center p-4 rounded-xl bg-gradient-to-b from-green-500/10 to-transparent border border-green-500/20"
            ),

            # This month
            Div(
                Div(
                    Div(
                        NotStr('<iconify-icon icon="ph:trend-up-bold" width="28" height="28" class="text-green-400 mb-2"></iconify-icon>'),
                        cls="flex justify-center"
                    ),
                    Span(f"+{stats['processos_mes']}", cls="font-mono text-3xl font-bold text-green-400"),
                    P("Novos este mês", cls="text-xs text-gray-500 mt-1")
                ),
                cls="text-center p-4 rounded-xl bg-gradient-to-b from-green-500/10 to-transparent border border-green-500/20"
            ),

            # Average citations
            Div(
                Div(
                    Div(
                        NotStr('<iconify-icon icon="ph:quotes-bold" width="28" height="28" class="text-blue-400 mb-2"></iconify-icon>'),
                        cls="flex justify-center"
                    ),
                    Span(f"{stats['citacoes_medio']:.1f}", cls="font-mono text-3xl font-bold text-blue-400"),
                    P("Citações médias", cls="text-xs text-gray-500 mt-1")
                ),
                cls="text-center p-4 rounded-xl bg-gradient-to-b from-blue-500/10 to-transparent border border-blue-500/20"
            ),

            cls="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4"
        ),

        cls="card mb-6"
    )
