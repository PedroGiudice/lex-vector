"""Tema visual: preto absoluto + OpenDyslexic."""
import streamlit as st

COLORS = {
    "background": "#000000",
    "surface": "#0a0a0a",
    "surface_elevated": "#121212",
    "border": "#1a1a1a",
    "border_focus": "#7c3aed",
    "text": "#e0e0e0",
    "text_muted": "#888888",
    "accent": "#7c3aed",
}

CUSTOM_CSS = """
<style>
    @import url('https://fonts.cdnfonts.com/css/opendyslexic');

    /* Global Reset to Absolute Black */
    .stApp {
        background-color: #000000;
        font-family: 'OpenDyslexic', sans-serif !important;
        color: #e0e0e0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #1a1a1a;
    }

    /* Input Fields */
    .stTextInput input {
        background-color: #0a0a0a !important;
        color: #e0e0e0 !important;
        border: 1px solid #1a1a1a !important;
        border-radius: 8px;
    }
    .stTextInput input:focus {
        border-color: #7c3aed !important;
    }

    /* Status Line */
    .status-line {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 42px;
        background: rgba(10, 10, 10, 0.95);
        backdrop-filter: blur(10px);
        border-top: 1px solid #1a1a1a;
        display: flex;
        align-items: center;
        padding: 0 1.5rem;
        z-index: 99999;
        font-family: 'OpenDyslexic', sans-serif;
        font-size: 0.85rem;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.5);
    }

    .status-segment {
        display: flex;
        align-items: center;
        margin-right: 1.5rem;
        padding: 4px 8px;
        border-radius: 4px;
        transition: all 0.2s;
    }
    .status-segment:hover {
        background: rgba(255,255,255,0.08);
    }

    .icon-svg {
        margin-right: 8px;
        vertical-align: middle;
        display: inline-block;
    }

    /* Chat */
    .stChatMessage {
        background-color: transparent !important;
        border-bottom: 1px solid rgba(255,255,255,0.02);
    }

    /* Padding para statusline nao cobrir conteudo */
    .main .block-container {
        padding-bottom: 60px;
    }

    /* Status widget */
    div[data-testid="stStatusWidget"] {
        background-color: #0a0a0a;
        border: 1px solid #222;
    }

    /* Blockquote for Thought */
    blockquote {
        border-left: 2px solid #333 !important;
        background: transparent !important;
        color: #888 !important;
        font-style: italic;
        font-size: 0.9rem;
    }

    /* File Explorer Tree */
    .file-tree-item {
        font-size: 0.8rem;
        padding: 4px 0;
        color: #888;
        display: flex;
        align-items: center;
        cursor: pointer;
        transition: color 0.2s;
    }
    .file-tree-item:hover {
        color: #e0e0e0;
    }

    /* Spinner animation */
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .custom-spinner {
        animation: spin 1s linear infinite;
    }

    /* Terminal Cursor Animation */
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }
    .blinking-cursor::after {
        content: '|';
        color: #c084fc;
        animation: blink 1s step-end infinite;
        margin-left: 2px;
    }
</style>
"""


def inject_theme():
    """Injeta CSS customizado na pagina Streamlit."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
