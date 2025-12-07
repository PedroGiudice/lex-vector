"""Statusline visual fixa no footer."""
import streamlit as st
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend import CLIState
from frontend.utils.helpers import get_icon


def render_statusline():
    """Renderiza statusline como HTML fixo no bottom."""
    config_mgr = st.session_state.get("config")
    if not config_mgr:
        return

    config = config_mgr.get()
    prefs = config.statusline
    data = st.session_state.get("statusline_data")
    cli_state = st.session_state.get("cli_state", CLIState.DISCONNECTED)

    segments = []

    # Model
    if prefs.show_model:
        model_name = "Claude"
        if data:
            model_name = data.model_display or data.model or "Claude"
        icon = get_icon("bot", prefs.color_model)
        segments.append(f'<div class="status-segment" style="color:{prefs.color_model}"><span class="icon-svg">{icon}</span> {model_name}</div>')

    # Path
    if prefs.show_path:
        current_project = st.session_state.get("current_project", "")
        path_display = Path(current_project).name if current_project else "~"
        if data and data.current_dir:
            path_display = Path(data.current_dir).name
        icon = get_icon("folder", prefs.color_path)
        segments.append(f'<div class="status-segment" style="color:{prefs.color_path}"><span class="icon-svg">{icon}</span> {path_display}</div>')

    # Git
    if prefs.show_git:
        git_display = ""
        if data and data.git_branch:
            git_display = data.git_branch
            if data.git_dirty:
                git_display += "*"
        if git_display:
            icon = get_icon("git", prefs.color_git)
            segments.append(f'<div class="status-segment" style="color:{prefs.color_git}"><span class="icon-svg">{icon}</span> {git_display}</div>')

    # Context
    if prefs.show_context and data and data.context_percent > 0:
        ctx_color = (
            "#4ade80" if data.context_percent < 50 else
            "#facc15" if data.context_percent < 80 else
            "#ef4444"
        )
        segments.append(f'<div class="status-segment" style="color:{ctx_color}">Context: {data.context_percent:.1f}%</div>')

    # Cost
    if prefs.show_cost and data and data.session_cost > 0:
        segments.append(f'<div class="status-segment" style="color:{prefs.color_cost}">Cost: ${data.session_cost:.3f}</div>')

    segments_html = "".join(segments)

    # Status indicator
    status_colors = {
        CLIState.DISCONNECTED: "#666",
        CLIState.STARTING: "#facc15",
        CLIState.IDLE: "#4ade80",
        CLIState.THINKING: "#facc15",
        CLIState.EXECUTING: "#f97316",
        CLIState.ERROR: "#ef4444",
    }
    status_color = status_colors.get(cli_state, "#666")
    status_text = cli_state.value.upper()

    st.markdown(f"""
        <div class="status-line">
            {segments_html}
            <div style="flex-grow:1"></div>
            <div class="status-segment" style="color:{status_color}">
                <div style="width:8px; height:8px; background:{status_color}; border-radius:50%; display:inline-block; margin-right:8px;"></div>
                {status_text}
            </div>
        </div>
    """, unsafe_allow_html=True)
