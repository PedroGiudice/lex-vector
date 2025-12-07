"""Sidebar com controles."""
import streamlit as st
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend import ClaudeCodeWrapper, CLINotFoundError, CLIConnectionError, CLIState
from frontend.utils.helpers import get_icon


def render_sidebar():
    """Renderiza sidebar completa."""
    with st.sidebar:
        render_project_header()
        render_connection_controls()
        st.divider()
        render_quick_commands()
        st.divider()
        render_file_explorer_section()
        st.divider()
        render_statusline_config()


def render_project_header():
    """Header do projeto ativo."""
    project_path = st.session_state.get("current_project", str(Path.home()))
    project_name = Path(project_path).name

    icon_folder = get_icon("folder", "#c084fc", 18)
    st.markdown(f"""
    <div style="background:#121212; border:1px solid #222; border-radius:8px; padding:10px; display:flex; align-items:center; margin-bottom:1rem;">
        <div style="margin-right:10px;">{icon_folder}</div>
        <div style="overflow:hidden;">
            <div style="font-weight:bold; color:white; font-size:0.9rem;">{project_name}</div>
            <div style="color:#666; font-size:0.75rem; white-space:nowrap;">{project_path}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Seletor de projeto
    new_path = st.text_input("Diretorio", value=project_path, key="project_path_input")
    if new_path != project_path:
        st.session_state.current_project = new_path


def render_connection_controls():
    """Controles de conexao com CLI."""
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Conectar", type="primary", use_container_width=True):
            connect_cli()

    with col2:
        if st.button("Parar", use_container_width=True):
            disconnect_cli()

    # Status indicator
    state = st.session_state.get("cli_state", CLIState.DISCONNECTED)
    status_map = {
        CLIState.DISCONNECTED: ("Desconectado", "#666"),
        CLIState.STARTING: ("Iniciando...", "#facc15"),
        CLIState.IDLE: ("Conectado - Idle", "#4ade80"),
        CLIState.THINKING: ("Pensando...", "#facc15"),
        CLIState.EXECUTING: ("Executando...", "#f97316"),
        CLIState.ERROR: ("Erro", "#ef4444"),
    }
    text, color = status_map.get(state, ("Desconhecido", "#666"))
    st.markdown(f"<div style='color:{color}; font-size:0.8rem; text-align:center;'>{text}</div>", unsafe_allow_html=True)


def connect_cli():
    """Conecta ao Claude Code CLI."""
    disconnect_cli()  # Desconectar anterior

    project_path = st.session_state.get("current_project", str(Path.home()))
    config = st.session_state.get("config")
    skip_perms = config.get().skip_permissions if config else True
    auto_reconnect = config.get().auto_reconnect if config else True

    try:
        wrapper = ClaudeCodeWrapper(
            project_path=project_path,
            skip_permissions=skip_perms,
            auto_reconnect=auto_reconnect
        )
        wrapper.start()
        st.session_state.wrapper = wrapper
        st.session_state.cli_state = CLIState.IDLE
        st.toast("Claude CLI conectado!")

        # Criar sessao
        session_mgr = st.session_state.get("session_manager")
        if session_mgr:
            session = session_mgr.create_session(project_path)
            st.session_state.current_session = session

    except CLINotFoundError:
        st.error("Claude Code CLI nao encontrado. Instale com: npm install -g @anthropic-ai/claude-code")
    except CLIConnectionError as e:
        st.error(f"Erro ao conectar: {e}")


def disconnect_cli():
    """Desconecta do CLI."""
    wrapper = st.session_state.get("wrapper")
    if wrapper:
        wrapper.stop()
        st.session_state.wrapper = None
    st.session_state.cli_state = CLIState.DISCONNECTED


def render_quick_commands():
    """Botoes de comandos rapidos."""
    st.caption("Quick Commands")

    col1, col2 = st.columns(2)

    commands = [
        ("/status", "Status"),
        ("/compact", "Compact"),
        ("/clear", "Clear"),
        ("/help", "Help"),
    ]

    for i, (cmd, label) in enumerate(commands):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(label, use_container_width=True, key=f"qc_{cmd}"):
                wrapper = st.session_state.get("wrapper")
                if wrapper and wrapper.is_alive():
                    wrapper.send_command(cmd)
                else:
                    st.warning("CLI nao conectado")


def render_file_explorer_section():
    """Secao do file explorer."""
    with st.expander("Explorer", expanded=True):
        from frontend.components.file_explorer import render_file_explorer
        project_path = Path(st.session_state.get("current_project", str(Path.home())))
        render_file_explorer(project_path)


def render_statusline_config():
    """Configuracao da statusline."""
    with st.expander("Statusline Config", expanded=False):
        config_mgr = st.session_state.get("config")
        if not config_mgr:
            st.caption("Config nao carregado")
            return

        config = config_mgr.get()
        prefs = config.statusline

        st.caption("Widgets & Colors")

        # Model
        c1, c2 = st.columns([3, 1])
        prefs.show_model = c1.checkbox("Model", value=prefs.show_model)
        prefs.color_model = c2.color_picker("", prefs.color_model, key="color_model", label_visibility="collapsed")

        # Path
        c1, c2 = st.columns([3, 1])
        prefs.show_path = c1.checkbox("Path", value=prefs.show_path)
        prefs.color_path = c2.color_picker("", prefs.color_path, key="color_path", label_visibility="collapsed")

        # Git
        c1, c2 = st.columns([3, 1])
        prefs.show_git = c1.checkbox("Git", value=prefs.show_git)
        prefs.color_git = c2.color_picker("", prefs.color_git, key="color_git", label_visibility="collapsed")

        # Context
        c1, c2 = st.columns([3, 1])
        prefs.show_context = c1.checkbox("Context", value=prefs.show_context)
        prefs.color_context = c2.color_picker("", prefs.color_context, key="color_context", label_visibility="collapsed")

        # Cost
        prefs.show_cost = st.checkbox("Cost", value=prefs.show_cost)

        # Save button
        if st.button("Salvar", use_container_width=True):
            config_mgr.save(config)
            st.success("Configuracao salva!")
