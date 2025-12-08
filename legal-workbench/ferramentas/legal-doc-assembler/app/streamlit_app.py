"""
Legal Engine Workbench v2.1

Streamlit frontend integrado com o backend de normalização e BATCH PROCESSING.
NÃO duplica lógica - importa diretamente de src.normalizers e src.batch_engine.

Features:
- Upload de JSON/TXT para entrada de dados
- Batch Processing: Upload de múltiplos arquivos ou ZIP
- Template Builder com upload de .docx
- Botão de Assembling para processamento (Single & Batch)
- Visualização em tempo real (Clean & Efficient)
"""

import json
import sys
import io
import re
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
import shutil

import streamlit as st
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importa do BACKEND - zero duplicação de lógica
from src.normalizers import (
    normalize_whitespace,
    normalize_name,
    normalize_address,
    format_cpf,
    format_cnpj,
    format_cep,
    format_oab,
    normalize_punctuation,
    normalize_all,
)
from src.engine import DocumentEngine
from src.batch_engine import BatchProcessor

# -----------------------------------------------------------------------------
# UI CONFIGURATION & STYLING (GitHub-inspired Dark Theme)
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Legal Engine",
    page_icon="§",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - GitHub-inspired dark theme
st.markdown("""
<style>
    /* Global Theme - GitHub Dark */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #161b22;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #58a6ff;
        box-shadow: 0 0 0 3px rgba(56, 139, 253, 0.3);
    }

    /* JSON / Code Blocks */
    .stJson, .stCode {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }

    /* Headers */
    h1, h2, h3 {
        color: #c9d1d9 !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
        font-weight: 600;
    }

    /* Expanders (Cards) */
    div[data-testid="stExpander"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
    }

    /* Upload area */
    .stFileUploader > div {
        background-color: #161b22;
        border: 1px dashed #30363d;
        border-radius: 6px;
    }

    /* Primary Buttons - GitHub style */
    .stButton > button[kind="primary"] {
        background-color: #238636;
        color: white;
        border: 1px solid rgba(240, 246, 252, 0.1);
        border-radius: 6px;
        padding: 5px 16px;
        font-weight: 500;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #2ea043;
    }

    /* Secondary Buttons */
    .stButton > button {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 5px 16px;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #30363d;
        border-color: #8b949e;
    }

    /* Status boxes */
    .status-success {
        background-color: rgba(46, 160, 67, 0.15);
        border: 1px solid #238636;
        border-radius: 6px;
        padding: 12px 16px;
        color: #3fb950;
    }
    .status-error {
        background-color: rgba(248, 81, 73, 0.15);
        border: 1px solid #f85149;
        border-radius: 6px;
        padding: 12px 16px;
        color: #f85149;
    }
    .status-warning {
        background-color: rgba(187, 128, 9, 0.15);
        border: 1px solid #d29922;
        border-radius: 6px;
        padding: 12px 16px;
        color: #d29922;
    }
    .status-info {
        background-color: rgba(56, 139, 253, 0.15);
        border: 1px solid #58a6ff;
        border-radius: 6px;
        padding: 12px 16px;
        color: #58a6ff;
    }

    /* Labels/Badges */
    .label {
        display: inline-block;
        padding: 0 7px;
        font-size: 12px;
        font-weight: 500;
        line-height: 18px;
        border-radius: 2em;
        margin-right: 4px;
    }
    .label-green {
        background-color: #238636;
        color: #ffffff;
    }
    .label-red {
        background-color: #da3633;
        color: #ffffff;
    }
    .label-blue {
        background-color: #1f6feb;
        color: #ffffff;
    }
    .label-gray {
        background-color: #30363d;
        color: #8b949e;
    }

    /* Muted text */
    .text-muted {
        color: #8b949e;
    }

    /* Border utilities */
    .border-bottom {
        border-bottom: 1px solid #30363d;
        padding-bottom: 16px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------

if 'input_data' not in st.session_state:
    st.session_state.input_data = {}
if 'batch_data' not in st.session_state:
    st.session_state.batch_data = [] # List of dicts for batch processing
if 'normalized_data' not in st.session_state:
    st.session_state.normalized_data = {}
if 'template_content' not in st.session_state:
    st.session_state.template_content = None
if 'template_variables' not in st.session_state:
    st.session_state.template_variables = []
if 'assembled_doc' not in st.session_state:
    st.session_state.assembled_doc = None
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = None

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------

with st.sidebar:
    st.markdown(