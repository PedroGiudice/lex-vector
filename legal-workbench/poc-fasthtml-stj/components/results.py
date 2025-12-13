"""
Results Component
Display search results with outcome badges and metadata
"""

from fasthtml.common import *
from typing import List, Dict


def outcome_badge(outcome: str) -> FT:
    """Render outcome badge with appropriate styling"""

    badge_classes = {
        "PROVIDO": "badge-provido",
        "DESPROVIDO": "badge-desprovido",
        "PARCIAL": "badge-parcial",
    }

    cls = badge_classes.get(outcome, "badge-parcial")

    return Span(outcome, cls=f"badge {cls}")


def results_table(results: List[Dict]) -> FT:
    """Render results as a data table"""

    if not results:
        return Div(
            P("Nenhum resultado encontrado.", cls="text-center text-gray-500 py-8"),
            cls="text-center"
        )

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


def export_buttons() -> FT:
    """Export options for results"""

    return Div(
        Button("Exportar CSV", cls="btn btn-secondary mr-2"),
        Button("Exportar PDF", cls="btn btn-secondary mr-2"),
        Button("Gerar Relatório", cls="btn btn-secondary"),
        cls="mb-4"
    )


def results_container(results: List[Dict] = None, domain: str = "", keywords: List[str] = None) -> FT:
    """Complete results container with stats and table"""

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

    return Div(
        Div(
            Div("Resultados da Busca", cls="card-header"),

            # Filter summary
            Div(
                Span("Filtros aplicados: ", cls="text-xs text-gray-500"),
                Span(" | ".join(filter_summary) if filter_summary else "Nenhum filtro",
                     cls="text-xs text-amber-400 font-mono ml-2")
            ) if filter_summary else None,

            results_stats(len(results), execution_time),
            export_buttons(),
            results_table(results),

            cls="card"
        ),
        id="results-container"
    )


def quick_stats_card(stats: Dict) -> FT:
    """Display quick statistics dashboard"""

    return Div(
        Div("Estatísticas Rápidas", cls="card-header"),

        Div(
            # Total acordãos
            Div(
                Div(
                    Span(f"{stats['total_acordaos']:,}", cls="font-mono text-3xl font-bold text-amber-400"),
                    P("Acórdãos no banco", cls="text-xs text-gray-500 mt-1")
                ),
                cls="text-center"
            ),

            # Last update
            Div(
                Div(
                    Span(stats['ultima_atualizacao'], cls="font-mono text-lg text-green-400"),
                    P("Última atualização", cls="text-xs text-gray-500 mt-1")
                ),
                cls="text-center"
            ),

            # This month
            Div(
                Div(
                    Span(f"+{stats['processos_mes']}", cls="font-mono text-3xl font-bold text-green-400"),
                    P("Novos este mês", cls="text-xs text-gray-500 mt-1")
                ),
                cls="text-center"
            ),

            # Average citations
            Div(
                Div(
                    Span(f"{stats['citacoes_medio']:.1f}", cls="font-mono text-3xl font-bold text-amber-400"),
                    P("Citações médias", cls="text-xs text-gray-500 mt-1")
                ),
                cls="text-center"
            ),

            cls="grid grid-cols-2 md:grid-cols-4 gap-6 mt-4"
        ),

        cls="card mb-6"
    )
