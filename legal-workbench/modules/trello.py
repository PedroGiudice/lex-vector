# modules/trello.py

import streamlit as st
import asyncio
import sys
import re
import os
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from dotenv import load_dotenv

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


def check_api_configured() -> tuple[bool, str]:
    """
    Check if Trello API credentials are configured.

    Returns:
        Tuple of (is_configured, message)
    """
    api_key = os.getenv("TRELLO_API_KEY")
    api_token = os.getenv("TRELLO_API_TOKEN")

    if not api_key or not api_token:
        env_path = tool_path / ".env"
        env_example_path = tool_path / ".env.example"

        message = f"""
### ⚠️ Configuração Necessária

As credenciais da API do Trello não foram encontradas.

**Passos para configurar:**

1. Copie o arquivo de exemplo:
   ```bash
   cp {env_example_path} {env_path}
   ```

2. Obtenha suas credenciais:
   - API Key: https://trello.com/power-ups/admin
   - Token: Clique em "Token" na mesma página (necessário permissões de leitura/escrita)

3. Edite o arquivo `.env` e adicione:
   ```
   TRELLO_API_KEY=sua_chave_aqui
   TRELLO_API_TOKEN=seu_token_aqui
   ```

4. Reinicie o Legal Workbench
"""
        return False, message

    return True, ""


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
    st.caption("Gerenciamento e extração de dados jurídicos de boards Trello.")

    # --- Check API Configuration ---
    is_configured, config_message = check_api_configured()

    if not is_configured:
        st.error("API não configurada")
        st.markdown(config_message)
        return

    # --- Initialize Session State ---
    if "trello_boards" not in st.session_state:
        st.session_state.trello_boards = None
    if "trello_selected_board" not in st.session_state:
        st.session_state.trello_selected_board = None
    if "trello_cards" not in st.session_state:
        st.session_state.trello_cards = None
    if "trello_extraction_results" not in st.session_state:
        st.session_state.trello_extraction_results = None

    # --- Initialize Client ---
    try:
        settings = EnvironmentSettings()
        client = TrelloClient(settings)
    except Exception as e:
        st.error(f"Erro ao inicializar cliente Trello: {e}")
        st.markdown(config_message)
        return

    # --- Tabs ---
    tab1, tab2 = st.tabs(["📋 Boards", "🔍 Extração de Dados"])

    # ========================================================================
    # TAB 1: BOARDS
    # ========================================================================
    with tab1:
        st.subheader("Boards Disponíveis")

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("🔄 Carregar Boards", use_container_width=True):
                with st.spinner("Carregando boards..."):
                    try:
                        boards = asyncio.run(load_boards_async(client))
                        st.session_state.trello_boards = boards
                        st.success(f"✅ {len(boards)} boards carregados")
                    except TrelloAuthError as e:
                        st.error(f"❌ Erro de autenticação: {e}")
                        st.info("Verifique suas credenciais no arquivo .env")
                    except TrelloAPIError as e:
                        st.error(f"❌ Erro na API: {e}")
                    except Exception as e:
                        st.error(f"❌ Erro inesperado: {e}")

        with col2:
            if st.session_state.trello_boards:
                st.metric("Total", len(st.session_state.trello_boards))

        # Display boards
        if st.session_state.trello_boards:
            st.markdown("---")

            for board in st.session_state.trello_boards:
                with st.expander(f"📋 {board.name}", expanded=False):
                    col_info, col_action = st.columns([3, 1])

                    with col_info:
                        if board.desc:
                            st.caption(board.desc)
                        st.text(f"ID: {board.id}")
                        st.text(f"Status: {'🔒 Fechado' if board.closed else '✅ Aberto'}")

                    with col_action:
                        if st.button("🔗 Abrir", key=f"open_{board.id}"):
                            st.markdown(f"[Abrir no Trello]({board.url})")

                        if st.button("📥 Selecionar", key=f"select_{board.id}"):
                            st.session_state.trello_selected_board = board
                            st.success(f"Board '{board.name}' selecionado para extração")

    # ========================================================================
    # TAB 2: DATA EXTRACTION
    # ========================================================================
    with tab2:
        st.subheader("Extração de Dados Jurídicos")

        if not st.session_state.trello_selected_board:
            st.info("👆 Selecione um board na aba 'Boards' para iniciar a extração")
            return

        board = st.session_state.trello_selected_board
        st.success(f"📋 Board selecionado: **{board.name}**")

        # Pattern selection
        st.markdown("### Padrões a Extrair")
        selected_patterns = {}

        col1, col2 = st.columns(2)
        with col1:
            if st.checkbox("CPF", value=True):
                selected_patterns["cpf"] = REGEX_MAP["cpf"]
            if st.checkbox("CNPJ", value=True):
                selected_patterns["cnpj"] = REGEX_MAP["cnpj"]

        with col2:
            if st.checkbox("OAB", value=True):
                selected_patterns["oab"] = REGEX_MAP["oab"]
            if st.checkbox("Valores Monetários", value=True):
                selected_patterns["valor"] = REGEX_MAP["valor"]

        if not selected_patterns:
            st.warning("⚠️ Selecione pelo menos um padrão para extrair")
            return

        # Extraction button
        if st.button("▶️ Iniciar Extração", use_container_width=True):
            progress_bar = st.progress(0, "Inicializando...")
            status_text = st.empty()

            try:
                # Load cards
                status_text.text("1/3 Carregando cards do board...")
                progress_bar.progress(33)

                cards = asyncio.run(load_board_cards_async(client, board.id))
                st.session_state.trello_cards = cards

                # Extract patterns
                status_text.text("2/3 Extraindo padrões...")
                progress_bar.progress(66)

                all_results = []
                for card in cards:
                    # Search in card name and description
                    search_text = f"{card.name}\n{card.desc}"
                    matches = extract_patterns_from_text(search_text, selected_patterns)

                    if matches:
                        for pattern_name, values in matches.items():
                            for value in values:
                                all_results.append({
                                    "card_name": card.name,
                                    "card_id": card.id,
                                    "card_url": card.url,
                                    "pattern_type": pattern_name.upper(),
                                    "extracted_value": value,
                                })

                st.session_state.trello_extraction_results = all_results

                status_text.text("3/3 Extração concluída!")
                progress_bar.progress(100)

                st.success(f"✅ Extração concluída: {len(all_results)} matches encontrados em {len(cards)} cards")

            except Exception as e:
                st.error(f"❌ Erro durante extração: {e}")
                st.session_state.trello_extraction_results = None

        # Display results
        if st.session_state.trello_extraction_results:
            st.markdown("---")
            st.markdown("### Resultados da Extração")

            results = st.session_state.trello_extraction_results

            # Metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total de Matches", len(results))

            with col2:
                cards_with_matches = len(set(r["card_id"] for r in results))
                st.metric("Cards com Dados", cards_with_matches)

            with col3:
                pattern_types = len(set(r["pattern_type"] for r in results))
                st.metric("Tipos de Padrão", pattern_types)

            with col4:
                if st.session_state.trello_cards:
                    coverage = (cards_with_matches / len(st.session_state.trello_cards)) * 100
                    st.metric("Cobertura", f"{coverage:.1f}%")

            # Results table
            st.markdown("### Dados Extraídos")

            df = pd.DataFrame(results)

            # Add filters
            col_filter1, col_filter2 = st.columns(2)

            with col_filter1:
                pattern_filter = st.multiselect(
                    "Filtrar por tipo",
                    options=df["pattern_type"].unique(),
                    default=df["pattern_type"].unique()
                )

            with col_filter2:
                card_filter = st.multiselect(
                    "Filtrar por card",
                    options=df["card_name"].unique()
                )

            # Apply filters
            filtered_df = df[df["pattern_type"].isin(pattern_filter)]
            if card_filter:
                filtered_df = filtered_df[filtered_df["card_name"].isin(card_filter)]

            # Display table
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "card_url": st.column_config.LinkColumn("Card URL"),
                }
            )

            # Download CSV
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"trello_extraction_{board.name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
