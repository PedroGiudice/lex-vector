"""STJ Jurisprudence Lab - Reflex PoC for Legal Workbench.

Terminal aesthetic, reactive state management, live SQL preview.
"""

import reflex as rx
from typing import List, Dict


# Mock data for results
MOCK_RESULTS = [
    {
        "id": "REsp 1.234.567",
        "ementa": "Recurso Especial. Direito Civil. Dano Moral. Quantum indenizatório desproporcional.",
        "outcome": "Provido",
        "date": "2024-11-15",
        "relator": "Min. João Silva"
    },
    {
        "id": "REsp 1.234.568",
        "ementa": "Apelação Cível. Lucros Cessantes. Ausência de prova do prejuízo alegado.",
        "outcome": "Desprovido",
        "date": "2024-11-12",
        "relator": "Min. Maria Santos"
    },
    {
        "id": "REsp 1.234.569",
        "ementa": "Recurso Especial. Dano Moral. Reforma parcial da sentença quanto ao valor.",
        "outcome": "Parcial",
        "date": "2024-11-10",
        "relator": "Min. Carlos Oliveira"
    },
    {
        "id": "HC 98.765",
        "ementa": "Habeas Corpus. Direito Penal. Nulidade processual reconhecida.",
        "outcome": "Provido",
        "date": "2024-11-08",
        "relator": "Min. Ana Paula"
    },
]


class STJState(rx.State):
    """Reactive state for STJ Query Builder."""

    # Form inputs
    legal_domain: str = ""
    trigger_words: List[str] = []
    only_acordaos: bool = False
    show_results: bool = False

    # Results data
    results_data: List[Dict[str, str]] = []

    # Available options (include empty for "no selection")
    domains: List[str] = [
        "",
        "Direito Civil",
        "Direito Penal",
        "Tributário",
        "Administrativo"
    ]

    available_triggers: List[str] = [
        "Dano Moral",
        "Lucros Cessantes",
        "Habeas Corpus",
        "ICMS",
        "ISS",
        "Responsabilidade Civil",
        "Súmula",
        "Jurisprudência Dominante"
    ]

    # Explicit setters (to avoid deprecation warnings)
    def set_legal_domain(self, value: str):
        """Set legal domain."""
        self.legal_domain = value

    def set_only_acordaos(self, value: bool):
        """Set only acordaos filter."""
        self.only_acordaos = value

    @rx.var
    def sql_preview(self) -> str:
        """Computed property: Live SQL preview that updates reactively."""
        if not self.legal_domain and not self.trigger_words:
            return "-- Selecione domínio ou palavras-gatilho para gerar SQL"

        sql_parts = ["SELECT"]
        sql_parts.append("  acor.id,")
        sql_parts.append("  acor.numero_processo,")
        sql_parts.append("  acor.ementa,")
        sql_parts.append("  acor.decisao,")
        sql_parts.append("  acor.data_julgamento,")
        sql_parts.append("  acor.relator")
        sql_parts.append("FROM stj_acordaos acor")

        where_clauses = []

        if self.legal_domain:
            where_clauses.append(f"  acor.dominio = '{self.legal_domain}'")

        if self.trigger_words:
            trigger_conditions = " OR ".join([
                f"acor.ementa LIKE '%{word}%'" for word in self.trigger_words
            ])
            where_clauses.append(f"  ({trigger_conditions})")

        if self.only_acordaos:
            where_clauses.append("  acor.tipo_documento = 'ACORDAO'")

        if where_clauses:
            sql_parts.append("WHERE")
            sql_parts.append(" AND\n".join(where_clauses))

        sql_parts.append("ORDER BY acor.data_julgamento DESC")
        sql_parts.append("LIMIT 100;")

        return "\n".join(sql_parts)

    @rx.var
    def selected_trigger_count(self) -> int:
        """Count of selected trigger words."""
        return len(self.trigger_words)

    @rx.var
    def results_count(self) -> int:
        """Count of results."""
        return len(self.results_data)

    def toggle_trigger_word(self, word: str):
        """Toggle trigger word selection."""
        if word in self.trigger_words:
            self.trigger_words = [w for w in self.trigger_words if w != word]
        else:
            self.trigger_words = self.trigger_words + [word]

    def apply_template_divergencia(self):
        """Apply 'Divergência entre Turmas' template."""
        self.legal_domain = "Direito Civil"
        self.trigger_words = ["Jurisprudência Dominante", "Súmula"]
        self.only_acordaos = True

    def apply_template_repetitivos(self):
        """Apply 'Recursos Repetitivos' template."""
        self.legal_domain = "Tributário"
        self.trigger_words = ["ICMS", "ISS"]
        self.only_acordaos = True

    def apply_template_sumulas(self):
        """Apply 'Súmulas Recentes' template."""
        self.legal_domain = ""
        self.trigger_words = ["Súmula"]
        self.only_acordaos = False

    def execute_query(self):
        """Execute the query (mock)."""
        # Filter mock results based on current query
        results = MOCK_RESULTS.copy()

        # Filter by domain if selected
        if self.legal_domain:
            if self.legal_domain == "Direito Civil":
                results = [r for r in results if "Civil" in r["ementa"]]
            elif self.legal_domain == "Direito Penal":
                results = [r for r in results if "Penal" in r["ementa"] or "HC" in r["id"]]

        # Filter by trigger words
        if self.trigger_words:
            filtered = []
            for result in results:
                if any(word in result["ementa"] for word in self.trigger_words):
                    filtered.append(result)
            results = filtered

        self.results_data = results
        self.show_results = True

    def clear_query(self):
        """Clear all query parameters."""
        self.legal_domain = ""
        self.trigger_words = []
        self.only_acordaos = False
        self.show_results = False
        self.results_data = []


def outcome_badge(outcome: str) -> rx.Component:
    """Create outcome badge with appropriate color."""
    colors = {
        "Provido": {"bg": "#22c55e", "text": "#ffffff"},
        "Desprovido": {"bg": "#dc2626", "text": "#ffffff"},
        "Parcial": {"bg": "#f59e0b", "text": "#000000"},
    }

    style = colors.get(outcome, {"bg": "#6b7280", "text": "#ffffff"})

    return rx.box(
        rx.text(outcome.upper(), size="1", weight="bold"),
        padding="4px 12px",
        border_radius="12px",
        background=style["bg"],
        color=style["text"],
        display="inline-block",
        font_family="monospace",
    )


def result_card(result: Dict) -> rx.Component:
    """Render a single result card."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    result["id"],
                    size="3",
                    weight="bold",
                    color="#f59e0b",
                    font_family="monospace",
                ),
                rx.spacer(),
                outcome_badge(result["outcome"]),
                width="100%",
                align="center",
            ),
            rx.text(
                result["ementa"],
                size="2",
                color="#e2e8f0",
                margin_top="8px",
            ),
            rx.hstack(
                rx.text(
                    f"Data: {result['date']}",
                    size="1",
                    color="#94a3b8",
                    font_family="monospace",
                ),
                rx.text("|", color="#475569"),
                rx.text(
                    result["relator"],
                    size="1",
                    color="#94a3b8",
                    font_family="monospace",
                ),
                margin_top="8px",
                spacing="2",
            ),
            align_items="start",
            spacing="1",
        ),
        padding="16px",
        border_radius="4px",
        border=f"1px solid #334155",
        background="#0f172a",
        width="100%",
        _hover={"border_color": "#f59e0b"},
    )


def query_builder() -> rx.Component:
    """Main STJ Query Builder component."""
    return rx.box(
        rx.vstack(
            # Header
            rx.heading(
                "STJ JURISPRUDENCE LAB",
                size="8",
                color="#f59e0b",
                font_family="monospace",
                letter_spacing="0.1em",
            ),
            rx.text(
                "[QUERY BUILDER v2.1.0]",
                size="2",
                color="#64748b",
                font_family="monospace",
            ),

            # Query Form
            rx.box(
                rx.vstack(
                    # Legal Domain
                    rx.vstack(
                        rx.text(
                            "> DOMÍNIO JURÍDICO",
                            size="2",
                            weight="bold",
                            color="#f59e0b",
                            font_family="monospace",
                        ),
                        rx.select(
                            STJState.domains,
                            placeholder="Selecione um domínio...",
                            value=STJState.legal_domain,
                            on_change=STJState.set_legal_domain,
                            size="3",
                            color_scheme="orange",
                        ),
                        align_items="start",
                        width="100%",
                        spacing="2",
                    ),

                    # Trigger Words
                    rx.vstack(
                        rx.hstack(
                            rx.text(
                                "> PALAVRAS-GATILHO",
                                size="2",
                                weight="bold",
                                color="#f59e0b",
                                font_family="monospace",
                            ),
                            rx.badge(
                                STJState.selected_trigger_count,
                                color_scheme="orange",
                                variant="solid",
                            ),
                            align="center",
                            spacing="3",
                        ),
                        rx.box(
                            rx.flex(
                                rx.foreach(
                                    STJState.available_triggers,
                                    lambda word: rx.button(
                                        word,
                                        on_click=lambda w=word: STJState.toggle_trigger_word(w),
                                        variant=rx.cond(
                                            STJState.trigger_words.contains(word),
                                            "solid",
                                            "outline"
                                        ),
                                        color_scheme="orange",
                                        size="2",
                                    ),
                                ),
                                wrap="wrap",
                                spacing="2",
                            ),
                            width="100%",
                        ),
                        align_items="start",
                        width="100%",
                        spacing="2",
                    ),

                    # Only Acórdãos Toggle
                    rx.hstack(
                        rx.switch(
                            checked=STJState.only_acordaos,
                            on_change=STJState.set_only_acordaos,
                            color_scheme="orange",
                        ),
                        rx.text(
                            "SOMENTE ACÓRDÃOS",
                            size="2",
                            weight="bold",
                            color="#f59e0b",
                            font_family="monospace",
                        ),
                        rx.cond(
                            STJState.only_acordaos,
                            rx.badge(
                                "ATIVO",
                                color_scheme="red",
                                variant="solid",
                            ),
                            rx.fragment(),
                        ),
                        align="center",
                        spacing="3",
                    ),

                    # Template Quick Buttons
                    rx.vstack(
                        rx.text(
                            "> TEMPLATES RÁPIDOS",
                            size="2",
                            weight="bold",
                            color="#64748b",
                            font_family="monospace",
                        ),
                        rx.hstack(
                            rx.button(
                                "Divergência Turmas",
                                on_click=STJState.apply_template_divergencia,
                                variant="outline",
                                color_scheme="gray",
                                size="2",
                            ),
                            rx.button(
                                "Recursos Repetitivos",
                                on_click=STJState.apply_template_repetitivos,
                                variant="outline",
                                color_scheme="gray",
                                size="2",
                            ),
                            rx.button(
                                "Súmulas Recentes",
                                on_click=STJState.apply_template_sumulas,
                                variant="outline",
                                color_scheme="gray",
                                size="2",
                            ),
                            spacing="2",
                            wrap="wrap",
                        ),
                        align_items="start",
                        width="100%",
                        spacing="2",
                    ),

                    spacing="6",
                    width="100%",
                ),
                padding="24px",
                border_radius="4px",
                border="1px solid #334155",
                background="#0f172a",
                width="100%",
            ),

            # Live SQL Preview
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            "> SQL PREVIEW [LIVE]",
                            size="2",
                            weight="bold",
                            color="#22c55e",
                            font_family="monospace",
                        ),
                        rx.badge(
                            "REACTIVE",
                            color_scheme="green",
                            variant="soft",
                        ),
                        align="center",
                        spacing="3",
                    ),
                    rx.code_block(
                        STJState.sql_preview,
                        language="sql",
                        show_line_numbers=True,
                        theme="dark",
                        width="100%",
                    ),
                    align_items="start",
                    width="100%",
                    spacing="3",
                ),
                padding="20px",
                border_radius="4px",
                border="1px solid #22c55e",
                background="#0a0f1a",
                width="100%",
            ),

            # Action Buttons
            rx.hstack(
                rx.button(
                    "EXECUTAR QUERY",
                    on_click=STJState.execute_query,
                    size="3",
                    color_scheme="orange",
                    variant="solid",
                ),
                rx.button(
                    "LIMPAR",
                    on_click=STJState.clear_query,
                    size="3",
                    variant="outline",
                    color_scheme="gray",
                ),
                spacing="3",
            ),

            # Results Section
            rx.cond(
                STJState.show_results,
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.text(
                                "> RESULTADOS",
                                size="3",
                                weight="bold",
                                color="#f59e0b",
                                font_family="monospace",
                            ),
                            rx.badge(
                                STJState.results_count,
                                color_scheme="orange",
                                variant="solid",
                            ),
                            align="center",
                            spacing="3",
                        ),
                        rx.vstack(
                            rx.foreach(
                                STJState.results_data,
                                result_card,
                            ),
                            width="100%",
                            spacing="3",
                        ),
                        align_items="start",
                        width="100%",
                        spacing="4",
                    ),
                    padding="24px",
                    border_radius="4px",
                    border="1px solid #334155",
                    background="#0f172a",
                    width="100%",
                    margin_top="24px",
                ),
                rx.fragment(),
            ),

            spacing="6",
            width="100%",
            max_width="1200px",
            padding="40px 20px",
        ),
        width="100%",
        min_height="100vh",
        background="#0a0f1a",
        display="flex",
        justify_content="center",
    )


def index() -> rx.Component:
    """Main page."""
    return query_builder()


# Create the app
app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap",
    ],
)
app.add_page(index)
