import asyncio
import os
import sys
import re
import json
from datetime import datetime
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Adicionar src/ ao path para imports funcionarem
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Imports do backend
from models import EnvironmentSettings
from trello_client import TrelloClient

# --- CONFIGURATION ---
load_dotenv()

st.set_page_config(
    page_title="TRELLO_HEX_TERM",
    page_icon="📟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS INJECTION (CLI THEME) ---
st.markdown("""
<style>
    /* MAIN THEME */
    .stApp { background-color: #000000; color: #00FF00; font-family: 'Courier New', monospace; }
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* SIDEBAR */
    section[data-testid="stSidebar"] { background-color: #050505; border-right: 1px solid #004400; }

    /* WIDGETS */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #001100; color: #00FF00; border: 1px solid #004400;
        font-family: 'Courier New', monospace;
    }

    /* BUTTONS */
    .stButton button {
        background-color: transparent;
        color: #00FF00;
        border: 2px solid #00FF00;
        border-radius: 0;
        font-weight: bold;
        text-transform: uppercase;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #00FF00;
        color: #000000;
        box-shadow: 0 0 10px #00FF00;
    }

    /* LOGS */
    .log-box {
        height: 120px;
        overflow-y: scroll;
        background-color: #000000;
        border: 1px solid #00FF00;
        padding: 8px;
        font-size: 11px;
        font-family: 'Courier New', monospace;
        margin-bottom: 10px;
    }

    /* METRICS */
    .metric-card {
        background-color: #001100;
        border: 1px solid #004400;
        padding: 15px;
        text-align: center;
        margin: 5px;
    }
    .metric-value { font-size: 24px; color: #00FF00; font-weight: bold; }
    .metric-label { font-size: 12px; color: #008800; }
</style>
""", unsafe_allow_html=True)

# --- REGEX PATTERNS (BRAZILIAN LEGAL) ---
REGEX_MAP = {
    "cpf": r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
    "cnpj": r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}",
    "rg": r"\d{1,2}\.?\d{3}\.?\d{3}-?[\dXx]",
    "valor": r"R\$\s?(\d{1,3}(?:\.\d{3})*,\d{2})",
    "oab": r"\d{1,6}/?[A-Z]{2}",
    "telefone": r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}",
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "cep": r"\d{5}-?\d{3}",
}

# --- HELPER FUNCTIONS ---

def log_message(msg: str):
    """Appends a message to session state log."""
    if 'system_logs' not in st.session_state:
        st.session_state.system_logs = []
    st.session_state.system_logs.append(msg)


def extract_legal_data(text: str, card_name: str = "") -> Dict[str, Any]:
    """Extracts legal/cadastral data using regex."""
    data = {"nome": card_name}

    for key, pattern in REGEX_MAP.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(0)
            if key == "valor":
                clean_val = match.group(1).replace('.', '').replace(',', '.')
                data["valor_numerico"] = float(clean_val)
            data[key] = val

    return data


def build_json_export(cards_data: List[Dict], board_name: str) -> Dict:
    """Builds structured JSON for export."""
    return {
        "dados": cards_data,
        "metadata": {
            "board": board_name,
            "total_registros": len(cards_data),
            "extraido_em": datetime.now().isoformat()
        }
    }


async def fetch_boards(api_key: str, token: str) -> List[Dict]:
    """Fetches all boards for the user."""
    settings = EnvironmentSettings(
        trello_api_key=api_key,
        trello_api_token=token
    )
    async with TrelloClient(settings) as client:
        await client.validate_credentials()
        boards_data = await client._request("GET", "/members/me/boards?fields=id,name,url")
        return [{"id": b["id"], "name": b["name"]} for b in boards_data]


async def run_pipeline(api_key: str, token: str, board_id: str, board_name: str, progress_callback=None):
    """Main extraction pipeline."""
    log_message("[SYS] INITIALIZING CLIENT...")
    if progress_callback:
        progress_callback(10)

    try:
        settings = EnvironmentSettings(
            trello_api_key=api_key,
            trello_api_token=token
        )

        async with TrelloClient(settings) as client:
            user = await client.validate_credentials()
            log_message(f"[AUTH] USER: {user.get('fullName')}")
            if progress_callback:
                progress_callback(20)

            log_message(f"[NET] FETCHING BOARD: {board_name}")
            if progress_callback:
                progress_callback(30)

            cards_data = await client._request(
                "GET",
                f"/boards/{board_id}/cards?fields=id,name,desc,idList,url"
            )
            log_message(f"[SYS] FOUND {len(cards_data)} CARDS")
            if progress_callback:
                progress_callback(50)

            log_message("[CPU] EXECUTING REGEX KERNELS (CPF, CNPJ, OAB)...")
            if progress_callback:
                progress_callback(60)

            processed_data = []
            for card in cards_data:
                extracted = extract_legal_data(card.get("desc", ""), card.get("name", ""))
                extracted["card_id"] = card.get("id", "")
                extracted["list_id"] = card.get("idList", "")
                extracted["descricao_original"] = card.get("desc", "")
                processed_data.append(extracted)

            log_message("[CPU] VALIDATING CHECKSUMS...")
            if progress_callback:
                progress_callback(80)

            log_message(f"[OK] EXTRACTED {len(processed_data)} RECORDS")
            if progress_callback:
                progress_callback(100)

            return processed_data, board_name

    except Exception as e:
        log_message(f"[CRITICAL] {str(e)}")
        return None, None


# --- HEADER ---
st.markdown("""
<pre style="color: #00FF00; font-size: 11px; line-height: 1.0; margin: 0 0 10px 0;">
╔══════════════════════════════════════════════════════════════╗
║   TRELLO MCP  //  LITIGATION EXTRACTION KERNEL  //  v3.0    ║
╚══════════════════════════════════════════════════════════════╝</pre>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS (Configuration only) ---
with st.sidebar:
    st.markdown("### /// CONNECTION")

    api_key = os.getenv("TRELLO_API_KEY", "")
    token = os.getenv("TRELLO_API_TOKEN", "")

    if api_key and token:
        st.success("CREDENTIALS: OK")
    else:
        st.error("CREDENTIALS: MISSING")

    with st.expander("AUTH CONFIG", expanded=False):
        api_key_input = st.text_input("API_KEY", type="password", value=api_key)
        token_input = st.text_input("TOKEN", type="password", value=token)
        if api_key_input:
            api_key = api_key_input
        if token_input:
            token = token_input

    st.markdown("---")
    st.markdown("### /// TARGET")

    selected_board_name = None
    selected_board_id = None

    if api_key and token:
        @st.cache_data(ttl=300)
        def get_boards(_api_key: str, _token: str):
            return asyncio.run(fetch_boards(_api_key, _token))

        try:
            boards = get_boards(api_key, token)
            board_options = {b["name"]: b["id"] for b in boards}
            selected_board_name = st.selectbox(
                "BOARD",
                options=list(board_options.keys()),
                index=0
            )
            selected_board_id = board_options[selected_board_name]
        except Exception as e:
            st.error(f"ERROR: {e}")
    else:
        st.warning("LOAD CREDENTIALS")

# --- MAIN CONTENT ---

# Control buttons (in main area, not sidebar)
col_exec, col_refresh, col_spacer = st.columns([1, 1, 4])
with col_exec:
    execute_clicked = st.button("[ EXECUTE ]", disabled=(selected_board_id is None))
with col_refresh:
    if st.button("[ REFRESH ]"):
        st.cache_data.clear()
        st.rerun()

# System Logs
st.markdown("###### SYSTEM_LOG")
log_container = st.empty()
progress_container = st.empty()

# Execute pipeline if triggered
if execute_clicked and selected_board_id:
    st.session_state.system_logs = []
    progress_bar = progress_container.progress(0)

    def update_progress(value):
        progress_bar.progress(value)

    data, board_name = asyncio.run(
        run_pipeline(api_key, token, selected_board_id, selected_board_name, update_progress)
    )

    if data:
        st.session_state.extracted_data = data
        st.session_state.board_name = board_name
        log_message("[SYS] PIPELINE EXECUTION SUCCESSFUL.")

    progress_container.empty()

# Render logs
if 'system_logs' in st.session_state and st.session_state.system_logs:
    log_html = "<div class='log-box'>" + "<br>".join([f"> {l}" for l in st.session_state.system_logs]) + "</div>"
    log_container.markdown(log_html, unsafe_allow_html=True)
else:
    log_container.markdown("<div class='log-box'>> [SYSTEM] STANDBY...</div>", unsafe_allow_html=True)

# --- TABS ---
tab_viewer, tab_data, tab_json = st.tabs(["VIEWER", "DATA", "JSON"])

with tab_viewer:
    if 'extracted_data' in st.session_state and st.session_state.extracted_data:
        df = pd.DataFrame(st.session_state.extracted_data)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{len(df)}</div>
                <div class='metric-label'>TOTAL_RECORDS</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            cpf_count = df['cpf'].notna().sum() if 'cpf' in df.columns else 0
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{cpf_count}</div>
                <div class='metric-label'>CPF_EXTRACTED</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            cnpj_count = df['cnpj'].notna().sum() if 'cnpj' in df.columns else 0
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{cnpj_count}</div>
                <div class='metric-label'>CNPJ_EXTRACTED</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            valor_sum = df['valor_numerico'].sum() if 'valor_numerico' in df.columns else 0
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>R$ {valor_sum:,.2f}</div>
                <div class='metric-label'>TOTAL_VALUE</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        if 'valor_numerico' in df.columns and df['valor_numerico'].sum() > 0:
            st.markdown("### VALUES_CHART")
            chart_df = df[df['valor_numerico'] > 0][['nome', 'valor_numerico']].head(10)
            if not chart_df.empty:
                st.bar_chart(chart_df.set_index('nome'))
    else:
        st.info("AWAITING DATASET...")

with tab_data:
    if 'extracted_data' in st.session_state:
        df = pd.DataFrame(st.session_state.extracted_data)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "[ DOWNLOAD_CSV ]",
            csv,
            f"dados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )
    else:
        st.text("NO DATA LOADED.")

with tab_json:
    if 'extracted_data' in st.session_state:
        json_export = build_json_export(
            st.session_state.extracted_data,
            st.session_state.get('board_name', 'unknown')
        )

        st.json(json_export)

        json_str = json.dumps(json_export, ensure_ascii=False, indent=2)
        st.download_button(
            "[ DOWNLOAD_JSON ]",
            json_str.encode('utf-8'),
            f"dados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json"
        )
    else:
        st.text("NO DATA LOADED.")
