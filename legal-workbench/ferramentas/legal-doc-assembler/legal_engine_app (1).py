import streamlit as st
import re
import time
import json
from typing import Dict, Any, Set, List, Tuple

# In a real scenario, you would ensure these libraries are installed:
# pip install docxtpl jinja2
from docxtpl import DocxTemplate
from jinja2 import Environment, DebugUndefined

# -----------------------------------------------------------------------------
# 1. CORE LOGIC ENGINE
# -----------------------------------------------------------------------------

LOWERCASE_CONNECTIVES: Set[str] = {
    'da', 'de', 'do', 'das', 'dos', 'e', 'em', 'para', 'por', 'na', 'no', 'nas', 'nos'
}

ADDRESS_EXPANSIONS: List[Tuple[str, str]] = [
    (r'\bR\.?\s+', 'Rua '),
    (r'\bAV\.?\s+', 'Avenida '),
    (r'\bTV\.?\s+', 'Travessa '),
    (r'\bAL\.?\s+', 'Alameda '),
    (r'\bAP\.?\s+', 'Apartamento '),
    (r'\bBL\.?\s+', 'Bloco '),
    (r'\bN\.?\s*(\d+)', r'nº \1'),
    (r'\bNUM\.?\s*(\d+)', r'nº \1'),
    (r'\bN[ºo]\s*(\d+)', r'nº \1'),
]

UPPERCASE_EXCEPTIONS: Set[str] = {
    'LTDA', 'S/A', 'ME', 'EPP', 'CNPJ', 'CPF', 'RG', 'OAB', 'CEP', 'UF'
}

def normalize_name(text: str) -> str:
    """Title casing with exception handling for connectives and acronyms."""
    if not text:
        return ""
    words = text.split()
    normalized_words = []
    for word in words:
        word_lower = word.lower()
        word_upper = word.upper()
        if word_upper in UPPERCASE_EXCEPTIONS:
            normalized_words.append(word_upper)
        elif word_lower in LOWERCASE_CONNECTIVES:
            normalized_words.append(word_lower)
        else:
            normalized_words.append(word.capitalize())
    return " ".join(normalized_words)

def normalize_address(text: str) -> str:
    """Expands abbreviations and standardizes format."""
    if not text:
        return ""
    normalized = text.strip()
    for pattern, replacement in ADDRESS_EXPANSIONS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    return normalize_name(normalized)

# -----------------------------------------------------------------------------
# 2. UI CONFIGURATION & STYLING
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Legal Engine Workbench",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match the React App's "Linear Dark" aesthetic
st.markdown("""
<style>
    /* Global Theme */
    .stApp {
        background-color: #0F1117;
        color: #cbd5e1;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background-color: #0B0C10;
        color: #e2e8f0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 1px #6366f1;
    }
    
    /* JSON / Code Blocks */
    .stJson, .stCode {
        background-color: #0B0C10;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 10px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0B0C10;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #f1f5f9 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Custom Card Containers using Streamlit expanders or markdown hacks */
    div[data-testid="stExpander"] {
        background-color: #161922;
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. APP LAYOUT
# -----------------------------------------------------------------------------

# --- SIDEBAR ---
with st.sidebar:
    st.title("Legal Engine")
    st.caption("Workbench v1.0")
    
    st.markdown("---")
    
    nav_mode = st.radio("Navigation", ["Playground", "Template Builder", "Source Code"], label_visibility="collapsed")
    
    st.markdown("---")
    st.subheader("Configuration")
    
    auto_normalize = st.checkbox("Auto-Normalize", value=True)
    debug_mode = st.checkbox("Debug Mode", value=False)
    
    st.markdown("---")
    st.info("Status: System Ready")

# --- MAIN WORKSPACE ---
if nav_mode == "Playground":
    
    # Split Pane Layout
    col_input, col_inspector = st.columns([1.5, 1])
    
    with col_input:
        st.subheader("Document Input Context")
        st.markdown("Enter raw client data below.")
        
        # Simulating "Cards" via Expanders
        with st.expander("Person Details", expanded=True):
            full_name = st.text_input("Full Legal Name", value="JOAO DA SILVA LTDA")
            c1, c2 = st.columns(2)
            with c1:
                rg = st.text_input("RG / Document ID", placeholder="e.g. 12.345.678-9")
            with c2:
                cpf = st.text_input("CPF / Tax ID", value="123.456.789-00")

        with st.expander("Address Data", expanded=True):
            address_street = st.text_input("Street Address (Raw)", value="R. das flores, N. 42")
            c3, c4 = st.columns(2)
            with c3:
                city = st.text_input("City", value="Sao Paulo")
            with c4:
                zip_code = st.text_input("ZIP / CEP", value="01000-000")

    # --- PROCESSING LOGIC ---
    # Simulate processing delay if auto-normalize is on
    if auto_normalize:
        # In a real app, this happens instantly, but we mimic the "thinking"
        # mechanism by processing purely on data change
        pass

    raw_data = {
        "full_name": full_name,
        "rg": rg,
        "cpf": cpf,
        "address_street": address_street,
        "address_city": city,
        "address_zip": zip_code
    }

    normalized_data = raw_data.copy()
    
    if auto_normalize:
        normalized_data["full_name"] = normalize_name(full_name)
        normalized_data["address_street"] = normalize_address(address_street)
        normalized_data["address_city"] = normalize_name(city)
        # RG/CPF/ZIP usually have specific formatters, skipping for brevity

    # --- LIVE INSPECTOR ---
    with col_inspector:
        st.subheader("Live State")
        
        # JSON View
        st.markdown("#### JSON Model")
        st.json(normalized_data)
        
        # Diff View
        st.markdown("#### Field Transformer")
        
        # Let's inspect Address Street specifically for the demo
        st.caption("Focus: address_street")
        
        c_raw, c_arrow, c_clean = st.columns([1, 0.2, 1])
        with c_raw:
            st.markdown(f"**RAW**")
            st.code(raw_data['address_street'], language="text")
        with c_arrow:
            st.markdown("### →")
        with c_clean:
            st.markdown(f"**NORMALIZED**")
            st.code(normalized_data['address_street'], language="text")

elif nav_mode == "Template Builder":
    st.title("Template Builder")
    st.info("This module is under construction. It will handle .docx file uploads.")

elif nav_mode == "Source Code":
    st.title("Source Code")
    with open(__file__, "r") as f:
        st.code(f.read(), language="python")
