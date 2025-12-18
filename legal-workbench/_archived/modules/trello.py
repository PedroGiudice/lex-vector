# modules/trello.py

import streamlit as st
import asyncio
import sys
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
from dotenv import load_dotenv

# Tab structure
TAB_BOARDS = "📋 Boards & Seleção"
TAB_EXTRACT = "📥 Extração de Dados"
TAB_MANAGE = "🔧 Gerenciar Cards"

# Adiciona o diretório de ferramentas ao path para importação do backend
tool_path = Path(__file__).parent.parent / "ferramentas" / "trello-mcp"
sys.path.insert(0, str(tool_path / "src"))

# Import backend
from models import EnvironmentSettings
from trello_client import TrelloClient, TrelloAuthError, TrelloAPIError

# Load environment variables
load_dotenv(tool_path / ".env")

# --- REGEX PATTERNS (BRAZILIAN LEGAL) ---
REGEX_MAP = {
    "cpf": r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
    "cnpj": r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}",
    "oab": r"\d{1,6}/?[A-Z]{2}",
    "valor": r"R\$\s?(\d{1,3}(?:\.\d{3})*,\d{2})",
}


def get_credentials_from_session() -> Tuple[Optional[str], Optional[str]]:
    """Get credentials from session state if available."""
    return (
        st.session_state.get("trello_api_key"),
        st.session_state.get("trello_api_token")
    )


def save_credentials_to_env(api_key: str, api_token: str) -> bool:
    """Save credentials to .env file for persistence."""
    env_path = tool_path / ".env"
    try:
        content = f"""# Trello API Credentials
# Generated via Legal Workbench UI
TRELLO_API_KEY={api_key}
TRELLO_API_TOKEN={api_token}
LOG_LEVEL=INFO
RATE_LIMIT_PER_10_SECONDS=90
"""
        env_path.write_text(content)
        return True
    except Exception as e:
        st.warning(f"Não foi possível salvar credenciais: {e}")
        return False


def check_api_configured() -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    Check if Trello API credentials are configured.

    Returns:
        Tuple of (is_configured, message, api_key, api_token)
    """
    # First check session state (UI input)
    session_key, session_token = get_credentials_from_session()
    if session_key and session_token:
        return True, "", session_key, session_token

    # Then check environment variables
    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")

    if api_key and api_token:
        return True, "", api_key, api_token

    env_path = tool_path / ".env"
    message = "Credenciais não encontradas"
    return False, message, None, None


def render_credentials_form():
    """Render the credentials input form."""
    st.markdown("### 🔐 Configurar Credenciais do Trello")
    st.info(
        "Insira suas credenciais abaixo. Elas serão salvas localmente para uso futuro.\n\n"
        "**Obtenha suas credenciais em:** https://trello.com/power-ups/admin"
    )

    with st.form("trello_credentials_form"):
        api_key = st.text_input(
            "API Key",
            type="password",
            help="Sua API Key do Trello (mínimo 32 caracteres)",
            placeholder="Cole sua API Key aqui..."
        )

        api_token = st.text_input(
            "API Token",
            type="password",
            help="Seu Token de API do Trello (mínimo 64 caracteres)",
            placeholder="Cole seu Token aqui..."
        )

        col1, col2 = st.columns(2)

        with col1:
            save_to_file = st.checkbox(
                "Salvar em arquivo .env",
                value=True,
                help="Salva as credenciais para uso futuro (recomendado)"
            )

        with col2:
            submitted = st.form_submit_button(
                "✅ Conectar",
                use_container_width=True,
                type="primary"
            )

        if submitted:
            # Validate inputs
            if not api_key or len(api_key) < 32:
                st.error("API Key deve ter pelo menos 32 caracteres")
                return False

            if not api_token or len(api_token) < 64:
                st.error("API Token deve ter pelo menos 64 caracteres")
                return False

            # Store in session state
            st.session_state.trello_api_key = api_key
            st.session_state.trello_api_token = api_token

            # Optionally save to file
            if save_to_file:
                if save_credentials_to_env(api_key, api_token):
                    st.success("✅ Credenciais salvas em .env")

            # Test connection
            with st.spinner("Testando conexão..."):
                try:
                    settings = EnvironmentSettings(
                        trello_api_key=api_key,
                        trello_api_token=api_token
                    )
                    client = TrelloClient(settings)

                    # Quick validation
                    async def test_connection():
                        async with client:
                            return await client.validate_credentials()

                    user_data = asyncio.run(test_connection())
                    st.success(f"✅ Conectado como: {user_data.get('fullName', 'Usuário')}")
                    st.rerun()

                except TrelloAuthError as e:
                    st.error(f"❌ Falha na autenticação: {e}")
                    st.session_state.trello_api_key = None
                    st.session_state.trello_api_token = None
                    return False

                except Exception as e:
                    st.error(f"❌ Erro de conexão: {e}")
                    return False

    return False


async def load_boards_async(client: TrelloClient) -> List[Any]:
    """Load boards from Trello API."""
    async with client:
        boards = await client.get_all_boards()
        return boards


async def load_board_cards_async(client: TrelloClient, board_id: str) -> List[Any]:
    """Load cards from a specific board."""
    async with client:
        cards = await client.get_board_cards_with_custom_fields(board_id)
        return cards


def extract_patterns_from_text(text: str, patterns: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Extract patterns from text using regex.

    Args:
        text: Text to search
        patterns: Dict of pattern_name -> regex_pattern

    Returns:
        Dict of pattern_name -> list of matches
    """
    results = {}
    for name, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            results[name] = list(set(matches))  # Remove duplicates
    return results


def render():
    """Renders the Streamlit UI for the Trello MCP module."""
    st.header("Trello MCP")
    st.caption("Extração e gerenciamento de dados jurídicos em boards Trello.")

    # --- Check API Configuration ---
    is_configured, config_message, api_key, api_token = check_api_configured()

    if not is_configured:
        render_credentials_form()
        return

    # --- Initialize Client with credentials ---
    try:
        settings = EnvironmentSettings(
            trello_api_key=api_key,
            trello_api_token=api_token
        )
        client = TrelloClient(settings)
    except Exception as e:
        st.error(f"Erro ao inicializar cliente Trello: {e}")
        render_credentials_form()
        return

    # --- Initialize Session State ---
    if "trello_selected_cards" not in st.session_state:
        st.session_state.trello_selected_cards = set()
    if "trello_extraction_mode" not in st.session_state:
        st.session_state.trello_extraction_mode = "individual"
    if "trello_extracted_data" not in st.session_state:
        st.session_state.trello_extracted_data = None

    # --- Show connected status with logout option ---
    with st.sidebar:
        st.success("🟢 Trello Conectado")
        if st.button("🔓 Desconectar", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith('trello_'):
                    del st.session_state[key]
            st.rerun()

    # --- Tabs ---
    tab1, tab2, tab3 = st.tabs([TAB_BOARDS, TAB_EXTRACT, TAB_MANAGE])

    # ==========================================================================
    # TAB 1: BOARDS & CARD SELECTION
    # ==========================================================================
    with tab1:
        st.subheader("Boards e Seleção de Cards")

        # --- Load Boards ---
        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("🔄 Carregar Boards", use_container_width=True):
                with st.spinner("Carregando boards..."):
                    try:
                        boards = asyncio.run(load_boards_async(client))
                        st.session_state.trello_boards = boards
                        st.success(f"✅ {len(boards)} boards carregados")
                    except Exception as e:
                        st.error(f"Erro: {e}")

        with col2:
            if st.session_state.get('trello_boards'):
                st.metric("Boards", len(st.session_state.trello_boards))

        # --- Board Selection ---
        if st.session_state.get('trello_boards'):
            st.markdown("---")
            st.markdown("### Selecionar Board")

            board_options = {b.name: b for b in st.session_state.trello_boards}
            selected_board_name = st.selectbox(
                "Escolha um board",
                options=list(board_options.keys()),
                key="board_selector"
            )

            if selected_board_name:
                selected_board = board_options[selected_board_name]
                st.session_state.trello_selected_board = selected_board

                # Load cards button
                if st.button("📥 Carregar Cards do Board", use_container_width=True):
                    with st.spinner(f"Carregando cards de {selected_board.name}..."):
                        try:
                            cards = asyncio.run(load_board_cards_async(client, selected_board.id))
                            st.session_state.trello_cards = cards
                            st.session_state.trello_selected_cards = set()
                            st.success(f"✅ {len(cards)} cards carregados")
                        except Exception as e:
                            st.error(f"Erro: {e}")

        # --- Card Selection Interface ---
        if st.session_state.get('trello_cards'):
            cards = st.session_state.trello_cards
            st.markdown("---")
            st.markdown("### Selecionar Cards para Extração")

            # Selection controls
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("☑️ Selecionar Todos"):
                    st.session_state.trello_selected_cards = {c.id for c in cards}
                    st.rerun()

            with col2:
                if st.button("⬜ Desmarcar Todos"):
                    st.session_state.trello_selected_cards = set()
                    st.rerun()

            with col3:
                st.metric("Selecionados", len(st.session_state.trello_selected_cards))

            # Card list with checkboxes
            st.markdown("**Cards Disponíveis:**")

            for card in cards:
                col1, col2, col3 = st.columns([0.5, 3, 1])

                with col1:
                    is_selected = card.id in st.session_state.trello_selected_cards
                    if st.checkbox(
                        "",
                        value=is_selected,
                        key=f"sel_{card.id}",
                        label_visibility="collapsed"
                    ):
                        st.session_state.trello_selected_cards.add(card.id)
                    else:
                        st.session_state.trello_selected_cards.discard(card.id)

                with col2:
                    st.markdown(f"**{card.name}**")
                    if card.desc:
                        st.caption(card.desc[:100] + "..." if len(card.desc) > 100 else card.desc)

                with col3:
                    # Labels
                    if card.labels:
                        labels_str = ", ".join([l.name for l in card.labels if l.name])
                        st.caption(f"🏷️ {labels_str}")

            # Selection summary
            if st.session_state.trello_selected_cards:
                st.info(f"📌 {len(st.session_state.trello_selected_cards)} cards selecionados. Vá para 'Extração de Dados' para extrair.")

    # ==========================================================================
    # TAB 2: DATA EXTRACTION
    # ==========================================================================
    with tab2:
        st.subheader("Extração de Dados")

        # Check if cards are selected
        selected_ids = st.session_state.get('trello_selected_cards', set())
        all_cards = st.session_state.get('trello_cards', [])

        if not all_cards:
            st.info("👆 Primeiro carregue os cards na aba 'Boards & Seleção'")
            return

        # --- Extraction Mode ---
        st.markdown("### Modo de Extração")

        extraction_mode = st.radio(
            "Selecione o modo",
            options=["selected", "all", "pattern"],
            format_func=lambda x: {
                "selected": f"📌 Cards Selecionados ({len(selected_ids)})",
                "all": f"📋 Todos os Cards ({len(all_cards)})",
                "pattern": "🔍 Extração de Padrões (CPF, CNPJ, etc.)"
            }[x],
            horizontal=True
        )

        st.session_state.trello_extraction_mode = extraction_mode

        st.markdown("---")

        # --- Extraction Options ---
        st.markdown("### Opções de Extração")

        col1, col2 = st.columns(2)

        with col1:
            include_desc = st.checkbox("Incluir Descrição", value=True)
            include_labels = st.checkbox("Incluir Labels", value=True)
            include_due = st.checkbox("Incluir Due Date", value=True)

        with col2:
            include_custom = st.checkbox("Incluir Custom Fields", value=True)
            include_checklists = st.checkbox("Incluir Checklists", value=False)
            include_url = st.checkbox("Incluir URL", value=True)

        # Pattern extraction options (only if pattern mode)
        if extraction_mode == "pattern":
            st.markdown("### Padrões a Extrair")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                extract_cpf = st.checkbox("CPF", value=True)
            with col2:
                extract_cnpj = st.checkbox("CNPJ", value=True)
            with col3:
                extract_oab = st.checkbox("OAB", value=True)
            with col4:
                extract_valor = st.checkbox("Valores (R$)", value=True)

        st.markdown("---")

        # --- Extract Button ---
        if extraction_mode == "selected" and not selected_ids:
            st.warning("⚠️ Nenhum card selecionado. Selecione cards na aba anterior.")
            can_extract = False
        else:
            can_extract = True

        if st.button("📥 Extrair Dados", type="primary", disabled=not can_extract, use_container_width=True):
            with st.spinner("Extraindo dados..."):
                # Determine which cards to extract
                if extraction_mode == "selected":
                    cards_to_extract = [c for c in all_cards if c.id in selected_ids]
                else:
                    cards_to_extract = all_cards

                # Build extracted data
                extracted = []

                for card in cards_to_extract:
                    card_data = {
                        "id": card.id,
                        "name": card.name,
                    }

                    if include_desc:
                        card_data["description"] = card.desc or ""
                    if include_labels:
                        card_data["labels"] = [l.name for l in card.labels if l.name]
                    if include_due:
                        card_data["due_date"] = card.due
                    if include_url:
                        card_data["url"] = card.url
                    if include_custom and card.custom_field_items:
                        card_data["custom_fields"] = [
                            {"id": cf.id_custom_field, "value": cf.value}
                            for cf in card.custom_field_items
                        ]

                    # Pattern extraction
                    if extraction_mode == "pattern":
                        search_text = f"{card.name}\n{card.desc or ''}"
                        patterns = {}

                        if extract_cpf:
                            cpf_matches = re.findall(REGEX_MAP["cpf"], search_text)
                            if cpf_matches:
                                patterns["cpf"] = list(set(cpf_matches))

                        if extract_cnpj:
                            cnpj_matches = re.findall(REGEX_MAP["cnpj"], search_text)
                            if cnpj_matches:
                                patterns["cnpj"] = list(set(cnpj_matches))

                        if extract_oab:
                            oab_matches = re.findall(REGEX_MAP["oab"], search_text)
                            if oab_matches:
                                patterns["oab"] = list(set(oab_matches))

                        if extract_valor:
                            valor_matches = re.findall(REGEX_MAP["valor"], search_text)
                            if valor_matches:
                                patterns["valor"] = list(set(valor_matches))

                        if patterns:
                            card_data["patterns"] = patterns

                    extracted.append(card_data)

                st.session_state.trello_extracted_data = extracted
                st.success(f"✅ {len(extracted)} cards extraídos!")

        # --- Display Results ---
        if st.session_state.get('trello_extracted_data'):
            st.markdown("---")
            st.markdown("### Dados Extraídos")

            data = st.session_state.trello_extracted_data

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Cards", len(data))

            if extraction_mode == "pattern":
                total_patterns = sum(
                    len(c.get('patterns', {}).get('cpf', [])) +
                    len(c.get('patterns', {}).get('cnpj', [])) +
                    len(c.get('patterns', {}).get('oab', [])) +
                    len(c.get('patterns', {}).get('valor', []))
                    for c in data
                )
                col2.metric("Padrões Encontrados", total_patterns)

            # View mode
            view_mode = st.radio(
                "Visualização",
                options=["table", "json", "cards"],
                format_func=lambda x: {"table": "📊 Tabela", "json": "📋 JSON", "cards": "🃏 Cards"}[x],
                horizontal=True
            )

            if view_mode == "table":
                # Convert to DataFrame
                df_data = []
                for card in data:
                    row = {
                        "Nome": card["name"],
                        "Labels": ", ".join(card.get("labels", [])),
                        "Due": card.get("due_date", ""),
                    }
                    if "patterns" in card:
                        for ptype, pvalues in card["patterns"].items():
                            row[ptype.upper()] = ", ".join(pvalues)
                    df_data.append(row)

                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

            elif view_mode == "json":
                st.json(data)

            else:  # cards view
                for card in data:
                    with st.expander(f"📄 {card['name']}", expanded=False):
                        if card.get('description'):
                            st.markdown(f"**Descrição:** {card['description'][:500]}...")
                        if card.get('labels'):
                            st.markdown(f"**Labels:** {', '.join(card['labels'])}")
                        if card.get('due_date'):
                            st.markdown(f"**Due:** {card['due_date']}")
                        if card.get('patterns'):
                            st.markdown("**Padrões Encontrados:**")
                            st.json(card['patterns'])
                        if card.get('url'):
                            st.markdown(f"[🔗 Abrir no Trello]({card['url']})")

            # Export options
            st.markdown("---")
            st.markdown("### Exportar")

            col1, col2, col3 = st.columns(3)

            with col1:
                # JSON export
                import json
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                st.download_button(
                    "📥 JSON",
                    data=json_str,
                    file_name="trello_extraction.json",
                    mime="application/json",
                    use_container_width=True
                )

            with col2:
                # CSV export
                if view_mode == "table" and df_data:
                    csv = pd.DataFrame(df_data).to_csv(index=False)
                    st.download_button(
                        "📥 CSV",
                        data=csv,
                        file_name="trello_extraction.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

            with col3:
                # Excel export (if openpyxl available)
                try:
                    import io
                    if view_mode == "table" and df_data:
                        buffer = io.BytesIO()
                        pd.DataFrame(df_data).to_excel(buffer, index=False)
                        st.download_button(
                            "📥 Excel",
                            data=buffer.getvalue(),
                            file_name="trello_extraction.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                except ImportError:
                    st.caption("Excel export requer openpyxl")

    # ==========================================================================
    # TAB 3: CARD MANAGEMENT
    # ==========================================================================
    with tab3:
        st.subheader("Gerenciar Cards")
        st.caption("Criar, mover e arquivar cards no Trello")

        if not st.session_state.get('trello_boards'):
            st.info("👆 Primeiro carregue os boards na aba 'Boards & Seleção'")
            return

        # --- Create Card Section ---
        st.markdown("### ➕ Criar Novo Card")

        with st.form("create_card_form"):
            # Board selection
            board_options = {b.name: b for b in st.session_state.trello_boards}
            selected_board_name = st.selectbox(
                "Board",
                options=list(board_options.keys()),
                key="create_board"
            )

            # List selection (would need to load lists)
            list_id = st.text_input(
                "ID da Lista",
                placeholder="Digite o ID da lista de destino",
                help="Você pode encontrar o ID da lista na URL do Trello"
            )

            # Card details
            card_name = st.text_input("Nome do Card", placeholder="Título do card")
            card_desc = st.text_area("Descrição", placeholder="Descrição do card (opcional)")
            card_due = st.date_input("Data de Vencimento", value=None)

            submitted = st.form_submit_button("✅ Criar Card", type="primary")

            if submitted:
                if not list_id or not card_name:
                    st.error("Nome do card e ID da lista são obrigatórios")
                else:
                    try:
                        from models import CreateCardInput

                        input_data = CreateCardInput(
                            list_id=list_id,
                            name=card_name,
                            desc=card_desc if card_desc else None,
                            due=card_due.isoformat() if card_due else None
                        )

                        async def create():
                            async with client:
                                return await client.create_card(input_data)

                        new_card = asyncio.run(create())
                        st.success(f"✅ Card criado: {new_card.name}")
                        st.markdown(f"[🔗 Abrir no Trello]({new_card.url})")

                    except Exception as e:
                        st.error(f"Erro ao criar card: {e}")

        st.markdown("---")

        # --- Move Card Section ---
        st.markdown("### 🔀 Mover Card")

        with st.form("move_card_form"):
            card_id = st.text_input(
                "ID do Card",
                placeholder="ID do card a mover",
                key="move_card_id"
            )

            target_list_id = st.text_input(
                "ID da Lista Destino",
                placeholder="ID da lista de destino",
                key="move_list_id"
            )

            move_submitted = st.form_submit_button("🔀 Mover Card")

            if move_submitted:
                if not card_id or not target_list_id:
                    st.error("ID do card e ID da lista destino são obrigatórios")
                else:
                    try:
                        from models import MoveCardInput

                        input_data = MoveCardInput(
                            card_id=card_id,
                            target_list_id=target_list_id
                        )

                        async def move():
                            async with client:
                                return await client.move_card(input_data)

                        moved_card = asyncio.run(move())
                        st.success(f"✅ Card movido: {moved_card.name}")

                    except Exception as e:
                        st.error(f"Erro ao mover card: {e}")

        st.markdown("---")

        # --- Quick Actions on Selected Cards ---
        st.markdown("### ⚡ Ações Rápidas")

        selected_cards = st.session_state.get('trello_selected_cards', set())

        if selected_cards:
            st.info(f"📌 {len(selected_cards)} cards selecionados")

            col1, col2 = st.columns(2)

            with col1:
                target_list_batch = st.text_input(
                    "Mover todos para lista",
                    placeholder="ID da lista destino",
                    key="batch_move_list"
                )

                if st.button("🔀 Mover Selecionados"):
                    if target_list_batch:
                        # Batch move would be implemented here
                        st.info("Movendo cards em lote...")
                        # TODO: Implement batch_move in backend
                    else:
                        st.warning("Informe o ID da lista destino")

            with col2:
                if st.button("🗄️ Arquivar Selecionados"):
                    st.info("Arquivando cards...")
                    # TODO: Implement batch_archive in backend
        else:
            st.caption("Selecione cards na aba 'Boards & Seleção' para ações em lote")
