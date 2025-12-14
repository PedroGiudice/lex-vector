"""
STJ Module Components

UI components specific to the STJ jurisprudence search module.
"""

from fasthtml.common import *
from shared.components import module_header, card, outcome_badge, empty_state


def stj_index() -> FT:
    """
    Main module index component.
    """
    return Div(
        module_header(
            icon="🔭",
            name="STJ Dados Abertos",
            tagline="Explore a jurisprudência do Superior Tribunal de Justiça",
        ),
        Div(
            quick_stats(),
            cls="mb-6",
        ),
        Div(
            search_form(),
            Div(
                id="results-container",
                cls="mt-6",
            ),
            cls="grid-2",
        ),
    )


def quick_stats() -> FT:
    """
    Quick statistics card.
    """
    # Mock data - would come from API
    stats = {
        "total": "15,847",
        "mes": "342",
        "atualizado": "14/12/2024",
    }

    return Div(
        Div(
            Div("Total de Acórdãos", cls="text-xs text-muted mb-1"),
            Div(stats["total"], cls="text-2xl font-bold"),
            cls="text-center",
        ),
        Div(
            Div("Últimos 30 dias", cls="text-xs text-muted mb-1"),
            Div(stats["mes"], cls="text-2xl font-bold"),
            cls="text-center",
        ),
        Div(
            Div("Última Atualização", cls="text-xs text-muted mb-1"),
            Div(stats["atualizado"], cls="text-sm"),
            cls="text-center",
        ),
        cls="grid grid-cols-3 gap-4 p-4 bg-secondary rounded-lg border border-default",
        style="background-color: var(--bg-secondary); border-color: var(--border);",
    )


def search_form() -> FT:
    """
    Search form with filters.
    """
    # Legal domains
    domains = [
        ("", "Todas as áreas"),
        ("civil", "Direito Civil"),
        ("penal", "Direito Penal"),
        ("tributario", "Direito Tributário"),
        ("administrativo", "Direito Administrativo"),
        ("trabalho", "Direito do Trabalho"),
    ]

    return card(
        "Buscar Jurisprudência",
        Form(
            # Search term
            Div(
                Label("Termo de busca", cls="block text-sm font-medium mb-2"),
                Input(
                    name="termo",
                    type="text",
                    placeholder="Ex: dano moral, responsabilidade civil...",
                    cls="input-field",
                ),
                cls="mb-4",
            ),
            # Domain filter
            Div(
                Label("Área do Direito", cls="block text-sm font-medium mb-2"),
                Select(
                    *[Option(label, value=value) for value, label in domains],
                    name="orgao",
                    cls="input-field",
                ),
                cls="mb-4",
            ),
            # Period filter
            Div(
                Label("Período", cls="block text-sm font-medium mb-2"),
                Select(
                    Option("Último ano", value="365"),
                    Option("Últimos 6 meses", value="180"),
                    Option("Últimos 30 dias", value="30"),
                    Option("Todo o período", value="9999"),
                    name="dias",
                    cls="input-field",
                ),
                cls="mb-4",
            ),
            # Submit button
            Button(
                Span("Buscar", cls="mr-2"),
                Span(cls="loading htmx-indicator"),
                type="submit",
                cls="btn btn-primary w-full",
            ),
            hx_get="/m/stj/search",
            hx_target="#results-container",
            hx_indicator=".htmx-indicator",
        ),
    )


def search_results(termo: str, orgao: str, dias: int) -> FT:
    """
    Search results display.
    """
    if not termo:
        return empty_state(
            icon="🔍",
            title="Digite um termo de busca",
            message="Use o formulário ao lado para pesquisar jurisprudência.",
        )

    # Mock results - would come from API
    results = [
        {
            "processo": "REsp 1.234.567/SP",
            "relator": "Min. João Silva",
            "turma": "3ª Turma",
            "data": "12/12/2024",
            "ementa": "CIVIL. RESPONSABILIDADE CIVIL. DANO MORAL. Comprovada a conduta ilícita...",
            "resultado": "PROVIDO",
        },
        {
            "processo": "REsp 9.876.543/RJ",
            "relator": "Min. Maria Santos",
            "turma": "4ª Turma",
            "data": "10/12/2024",
            "ementa": "CIVIL. CONTRATOS. RESCISÃO CONTRATUAL. Ausência de justa causa...",
            "resultado": "DESPROVIDO",
        },
        {
            "processo": "AgInt 5.555.555/MG",
            "relator": "Min. Pedro Costa",
            "turma": "2ª Turma",
            "data": "08/12/2024",
            "ementa": "TRIBUTÁRIO. ICMS. BASE DE CÁLCULO. Inclusão de valores...",
            "resultado": "PARCIAL",
        },
    ]

    return Div(
        # Results header
        Div(
            Span(f"{len(results)} resultados", cls="text-sm text-muted"),
            Span(f" para '{termo}'", cls="text-sm"),
            cls="mb-4",
        ),
        # Results table
        Table(
            Thead(
                Tr(
                    Th("Processo"),
                    Th("Resultado"),
                    Th("Relator/Turma"),
                    Th("Ementa"),
                ),
            ),
            Tbody(
                *[
                    Tr(
                        Td(
                            Div(r["processo"], cls="font-mono text-sm"),
                            Div(r["data"], cls="text-xs text-muted"),
                        ),
                        Td(outcome_badge(r["resultado"])),
                        Td(
                            Div(r["relator"], cls="text-sm"),
                            Div(r["turma"], cls="text-xs text-muted"),
                        ),
                        Td(
                            P(r["ementa"][:150] + "...", cls="text-sm"),
                        ),
                    )
                    for r in results
                ],
            ),
            cls="results-table",
        ),
    )
