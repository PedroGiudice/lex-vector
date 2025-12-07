"""
Claude Code UI - Frontend Streamlit
Entry point da aplicacao.
"""
import streamlit as st
import sys
from pathlib import Path

# Adicionar parent ao path para imports do backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend import (
    ClaudeCodeWrapper,
    OutputParser,
    StatusLineParser,
    SessionManager,
    ConfigManager,
    CLIState,
    ContentType,
    StatusLineData,
    Message,
    CLINotFoundError,
)

from frontend.components.chat import render_chat_history, render_chat_input
from frontend.components.sidebar import render_sidebar
from frontend.components.statusline import render_statusline
from frontend.styles.theme import inject_theme

# Page config - deve ser a primeira chamada Streamlit
st.set_page_config(
    page_title="Claude Code CLI",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject theme
inject_theme()


def init_session_state():
    """Inicializa estado da sessao Streamlit."""
    if "wrapper" not in st.session_state:
        st.session_state.wrapper = None
    if "parser" not in st.session_state:
        st.session_state.parser = OutputParser()
    if "statusline_parser" not in st.session_state:
        st.session_state.statusline_parser = StatusLineParser()
    if "config" not in st.session_state:
        st.session_state.config = ConfigManager()
    if "session_manager" not in st.session_state:
        st.session_state.session_manager = SessionManager()
    if "current_session" not in st.session_state:
        st.session_state.current_session = None
    if "history" not in st.session_state:
        st.session_state.history = []
    if "statusline_data" not in st.session_state:
        st.session_state.statusline_data = StatusLineData()
    if "current_project" not in st.session_state:
        st.session_state.current_project = str(Path.home())
    if "cli_state" not in st.session_state:
        st.session_state.cli_state = CLIState.DISCONNECTED


def process_cli_output():
    """Processa output pendente do CLI."""
    wrapper = st.session_state.get("wrapper")
    if wrapper and wrapper.is_alive():
        lines = wrapper.get_output(timeout=0.1)
        if lines:
            combined = "\n".join(lines)

            # Tentar extrair statusline data
            statusline_parser = st.session_state.get("statusline_parser")
            if statusline_parser:
                status_data = statusline_parser.extract_from_output(combined)
                if status_data:
                    st.session_state.statusline_data = status_data

            # Parse output em blocos
            parser = st.session_state.get("parser")
            blocks = parser.parse(combined) if parser else []

            # Adicionar ao historico
            if combined.strip():
                st.session_state.history.append({
                    "role": "assistant",
                    "content": combined,
                    "blocks": blocks
                })

            # Atualizar estado
            st.session_state.cli_state = wrapper.get_state()


def main():
    """Funcao principal da aplicacao."""
    # Inicializar estado
    init_session_state()

    # Processar output pendente do CLI
    process_cli_output()

    # Sidebar
    render_sidebar()

    # Main content
    chat_container = st.container()

    with chat_container:
        render_chat_history()

    # Chat input
    render_chat_input()

    # Statusline (footer fixo)
    render_statusline()


if __name__ == "__main__":
    main()
