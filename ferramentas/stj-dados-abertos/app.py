import streamlit as st
import duckdb
import pandas as pd
import time
import datetime
import random
import sys
import logging
from pathlib import Path
from typing import List

# Backend imports
sys.path.insert(0, str(Path(__file__).parent))
from src.downloader import STJDownloader
from src.processor import STJProcessor
from src.database import STJDatabase
from config import get_date_range_urls, ORGAOS_JULGADORES, DATABASE_PATH

# Configure logging for backend operations
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# -----------------------------------------------------------------------------
# APP CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="STJ Dados Abertos v1.1",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark Theme CSS Injection
st.markdown("""
    <style>
        /* CORE THEME */
        .stApp {
            background-color: #020617;
            color: #e2e8f0;
            font-family: 'Source Code Pro', monospace;
        }

        /* WIDGETS */
        .stSelectbox > div > div > div,
        .stMultiSelect > div > div > div,
        .stTextInput > div > div > input {
            background-color: #0f172a;
            color: #f8fafc;
            border: 1px solid #1e293b;
            border-radius: 6px;
        }

        /* TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            background-color: #0f172a;
            padding: 8px;
            border-radius: 8px;
            border: 1px solid #1e293b;
        }

        .stTabs [data-baseweb="tab"] {
            height: 40px;
            background-color: transparent;
            border: none;
            color: #64748b;
            font-weight: 600;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #1e293b;
            color: #38bdf8;
            border-radius: 6px;
        }

        /* CUSTOM METRICS */
        div[data-testid="metric-container"] {
            background-color: #0f172a;
            border: 1px solid #1e293b;
            padding: 10px;
            border-radius: 6px;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HEADER & SYSTEM STATUS
# -----------------------------------------------------------------------------
c1, c2 = st.columns([3, 1])
with c1:
    st.title("STJ Dados Abertos // PRO")
    st.caption("Advanced Jurisprudence Extraction & Analysis Engine")

with c2:
    st.markdown("""
        <div style='text-align: right; color: #10b981; font-family: monospace; font-size: 12px; margin-top: 10px;'>
            [ SYSTEM ONLINE ]<br>
            LATENCY: 14ms
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

tab_dl, tab_lab, tab_code = st.tabs(["DOWNLOAD CENTER", "JURISPRUDENCE LAB", "SOURCE CODE"])

# -----------------------------------------------------------------------------
# HELPER FUNCTION: MAP UI ORGAN NAMES TO CONFIG KEYS
# -----------------------------------------------------------------------------
def map_organ_name_to_key(ui_name: str) -> str:
    """Map user-friendly organ names to config keys."""
    mapping = {
        "Corte Especial": "corte_especial",
        "1ª Seção": "primeira_secao",
        "2ª Seção": "segunda_secao",
        "3ª Seção": "terceira_secao",
        "1ª Turma": "primeira_turma",
        "2ª Turma": "segunda_turma",
    }
    return mapping.get(ui_name, "corte_especial")

# -----------------------------------------------------------------------------
# TAB 1: MASSIVE DOWNLOAD CENTER
# -----------------------------------------------------------------------------
with tab_dl:
    col_config, col_term = st.columns([1, 2])

    with col_config:
        st.markdown("#### CONFIGURATION")
        with st.container(border=True):
            start_d = st.date_input("Start Date", datetime.date(2023, 1, 1))
            end_d = st.date_input("End Date", datetime.date.today())

            target_organs = st.multiselect(
                "Judicial Targets",
                ["Corte Especial", "1ª Seção", "2ª Seção", "3ª Seção", "1ª Turma", "2ª Turma"],
                default=["Corte Especial"]
            )

            st.write("")
            if st.button("INITIATE EXTRACTION", type="primary", use_container_width=True):
                st.session_state['extracting'] = True

    with col_term:
        st.markdown("#### SYSTEM LOGS")
        terminal = st.empty()

        if st.session_state.get('extracting'):
            logs = []

            try:
                # Convert dates to datetime
                start_date = datetime.datetime.combine(start_d, datetime.time.min)
                end_date = datetime.datetime.combine(end_d, datetime.time.min)

                # Generate URLs for selected organs
                all_url_configs = []
                for organ_ui_name in target_organs:
                    organ_key = map_organ_name_to_key(organ_ui_name)
                    url_configs = get_date_range_urls(start_date, end_date, organ_key)
                    all_url_configs.extend(url_configs)

                total_files = len(all_url_configs)

                # Log initial info
                log_time = datetime.datetime.now().strftime('%H:%M:%S')
                logs.append(f"[{log_time}] INFO: Starting extraction for {len(target_organs)} organ(s)")
                logs.append(f"[{log_time}] INFO: Date range: {start_d} to {end_d}")
                logs.append(f"[{log_time}] INFO: Total files to download: {total_files}")

                # Render initial terminal
                log_html = "<br>".join([f"<span style='color:#64748b'>></span> {l}" for l in logs[-8:]])
                terminal.markdown(f"""
                    <div style='background-color: #020617; padding: 15px; border-radius: 6px; border: 1px solid #1e293b; height: 300px; font-family: monospace; font-size: 12px; overflow-y: auto;'>
                        <div style='color: #38bdf8; margin-bottom: 10px;'>root@stj-node-01:~/extraction# ./batch_runner.sh</div>
                        {log_html}
                        <div style='display: inline-block; width: 8px; height: 14px; background-color: #10b981; margin-left: 5px;'></div>
                    </div>
                """, unsafe_allow_html=True)

                # Create progress bar
                bar = st.progress(0)

                # Phase 1: Download
                log_time = datetime.datetime.now().strftime('%H:%M:%S')
                logs.append(f"[{log_time}] PHASE 1: Downloading JSON files...")

                with STJDownloader() as downloader:
                    downloaded_files = []

                    for idx, config in enumerate(all_url_configs):
                        try:
                            file_path = downloader.download_json(
                                config["url"],
                                config["filename"],
                                force=False
                            )

                            if file_path:
                                downloaded_files.append(file_path)
                                log_time = datetime.datetime.now().strftime('%H:%M:%S')
                                logs.append(f"[{log_time}] SUCCESS: {config['filename']}")

                            # Update progress
                            progress = int((idx + 1) / total_files * 40)  # 40% for download phase
                            bar.progress(progress)

                            # Update terminal every 5 downloads
                            if idx % 5 == 0 or idx == len(all_url_configs) - 1:
                                log_html = "<br>".join([f"<span style='color:#64748b'>></span> {l}" for l in logs[-8:]])
                                terminal.markdown(f"""
                                    <div style='background-color: #020617; padding: 15px; border-radius: 6px; border: 1px solid #1e293b; height: 300px; font-family: monospace; font-size: 12px; overflow-y: auto;'>
                                        <div style='color: #38bdf8; margin-bottom: 10px;'>root@stj-node-01:~/extraction# ./batch_runner.sh</div>
                                        {log_html}
                                        <div style='display: inline-block; width: 8px; height: 14px; background-color: #10b981; margin-left: 5px;'></div>
                                    </div>
                                """, unsafe_allow_html=True)

                        except Exception as e:
                            log_time = datetime.datetime.now().strftime('%H:%M:%S')
                            logs.append(f"[{log_time}] WARN: {config['filename']} - {str(e)[:50]}")

                    # Print download stats
                    downloader.print_stats()

                log_time = datetime.datetime.now().strftime('%H:%M:%S')
                logs.append(f"[{log_time}] INFO: Downloaded {len(downloaded_files)} files")
                bar.progress(40)

                # Phase 2: Process
                log_time = datetime.datetime.now().strftime('%H:%M:%S')
                logs.append(f"[{log_time}] PHASE 2: Processing JSON data...")

                processor = STJProcessor()
                all_records = []

                for idx, file_path in enumerate(downloaded_files):
                    try:
                        records = processor.processar_arquivo_json(file_path)
                        all_records.extend(records)

                        log_time = datetime.datetime.now().strftime('%H:%M:%S')
                        logs.append(f"[{log_time}] PROCESSED: {file_path.name} ({len(records)} records)")

                        # Update progress
                        progress = 40 + int((idx + 1) / len(downloaded_files) * 30)  # 30% for processing
                        bar.progress(progress)

                        # Update terminal
                        if idx % 3 == 0 or idx == len(downloaded_files) - 1:
                            log_html = "<br>".join([f"<span style='color:#64748b'>></span> {l}" for l in logs[-8:]])
                            terminal.markdown(f"""
                                <div style='background-color: #020617; padding: 15px; border-radius: 6px; border: 1px solid #1e293b; height: 300px; font-family: monospace; font-size: 12px; overflow-y: auto;'>
                                    <div style='color: #38bdf8; margin-bottom: 10px;'>root@stj-node-01:~/extraction# ./batch_runner.sh</div>
                                    {log_html}
                                    <div style='display: inline-block; width: 8px; height: 14px; background-color: #10b981; margin-left: 5px;'></div>
                                </div>
                            """, unsafe_allow_html=True)

                    except Exception as e:
                        log_time = datetime.datetime.now().strftime('%H:%M:%S')
                        logs.append(f"[{log_time}] ERROR: Processing {file_path.name} - {str(e)[:50]}")

                log_time = datetime.datetime.now().strftime('%H:%M:%S')
                logs.append(f"[{log_time}] INFO: Processed {len(all_records)} total records")
                bar.progress(70)

                # Phase 3: Database insertion
                log_time = datetime.datetime.now().strftime('%H:%M:%S')
                logs.append(f"[{log_time}] PHASE 3: Inserting into database...")

                with STJDatabase(DATABASE_PATH) as db:
                    # Create schema if needed
                    db.criar_schema()

                    log_time = datetime.datetime.now().strftime('%H:%M:%S')
                    logs.append(f"[{log_time}] INFO: Database schema ready")

                    # Insert records
                    if all_records:
                        inseridos, duplicados, erros = db.inserir_batch(all_records)

                        log_time = datetime.datetime.now().strftime('%H:%M:%S')
                        logs.append(f"[{log_time}] SUCCESS: {inseridos} inserted, {duplicados} duplicates, {erros} errors")
                    else:
                        log_time = datetime.datetime.now().strftime('%H:%M:%S')
                        logs.append(f"[{log_time}] WARN: No records to insert")

                bar.progress(100)

                # Final log
                log_time = datetime.datetime.now().strftime('%H:%M:%S')
                logs.append(f"[{log_time}] COMPLETE: Extraction finished successfully")

                # Final terminal render
                log_html = "<br>".join([f"<span style='color:#64748b'>></span> {l}" for l in logs[-8:]])
                terminal.markdown(f"""
                    <div style='background-color: #020617; padding: 15px; border-radius: 6px; border: 1px solid #1e293b; height: 300px; font-family: monospace; font-size: 12px; overflow-y: auto;'>
                        <div style='color: #38bdf8; margin-bottom: 10px;'>root@stj-node-01:~/extraction# ./batch_runner.sh</div>
                        {log_html}
                        <div style='display: inline-block; width: 8px; height: 14px; background-color: #10b981; margin-left: 5px;'></div>
                    </div>
                """, unsafe_allow_html=True)

                st.success("Extraction Complete.")

            except Exception as e:
                log_time = datetime.datetime.now().strftime('%H:%M:%S')
                logs.append(f"[{log_time}] FATAL ERROR: {str(e)}")

                log_html = "<br>".join([f"<span style='color:#64748b'>></span> {l}" for l in logs[-8:]])
                terminal.markdown(f"""
                    <div style='background-color: #020617; padding: 15px; border-radius: 6px; border: 1px solid #1e293b; height: 300px; font-family: monospace; font-size: 12px; overflow-y: auto;'>
                        <div style='color: #38bdf8; margin-bottom: 10px;'>root@stj-node-01:~/extraction# ./batch_runner.sh</div>
                        {log_html}
                        <div style='display: inline-block; width: 8px; height: 14px; background-color: #ef4444; margin-left: 5px;'></div>
                    </div>
                """, unsafe_allow_html=True)

                st.error(f"Extraction failed: {str(e)}")

            finally:
                st.session_state['extracting'] = False
        else:
            terminal.info("System Ready. Awaiting Command.")

# -----------------------------------------------------------------------------
# TAB 2: JURISPRUDENCE LAB (SMART QUERY)
# -----------------------------------------------------------------------------
with tab_lab:
    # --- HELPER FUNCTIONS ---
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def query_acordaos(keywords: List[str], only_acordao: bool, limit: int = 100) -> pd.DataFrame:
        """
        Query real acordaos table from DuckDB with filters.
        """
        try:
            db = STJDatabase(DATABASE_PATH)
            db.connect()

            # Build WHERE clause for keyword search
            where_clauses = []
            params = []

            # Keyword search in ementa (multiple keywords = OR logic)
            if keywords:
                keyword_conditions = []
                for kw in keywords:
                    keyword_conditions.append("ementa LIKE ?")
                    params.append(f"%{kw}%")
                where_clauses.append(f"({' OR '.join(keyword_conditions)})")

            # Filter only Acórdãos
            if only_acordao:
                where_clauses.append("tipo_decisao = 'Acórdão'")

            # Build final query
            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            query = f"""
                SELECT
                    id,
                    numero_processo as processo,
                    relator,
                    tipo_decisao as tipo,
                    resultado_julgamento,
                    data_publicacao as data,
                    ementa
                FROM acordaos
                {where_sql}
                ORDER BY data_publicacao DESC
                LIMIT ?
            """
            params.append(limit)

            df = db.get_dataframe(query, params if params else None)
            db.close()

            return df

        except Exception as e:
            logging.error(f"Erro ao consultar acordaos: {e}")
            return pd.DataFrame()

    def format_resultado_badge(resultado: str) -> str:
        """Format resultado_julgamento with color badge."""
        if pd.isna(resultado) or not resultado:
            return "—"

        resultado_lower = str(resultado).lower()

        if 'provid' in resultado_lower or 'provimento' in resultado_lower:
            return f"🟢 {resultado}"
        elif 'desprovid' in resultado_lower or 'desprovimento' in resultado_lower:
            return f"🔴 {resultado}"
        elif 'parcial' in resultado_lower:
            return f"🟡 {resultado}"
        else:
            return f"⚪ {resultado}"

    # --- QUERY BUILDER UI ---
    col_builder, col_templates = st.columns([3, 1])

    with col_builder:
        st.markdown("#### SMART QUERY BUILDER")
        with st.container(border=True):
            # 1. Semantic Inputs
            c_theme, c_trigger = st.columns(2)
            with c_theme:
                theme = st.selectbox("Legal Domain (Theme)", ["Direito Civil", "Direito Penal", "Tributário", "Administrativo"])
                st.caption("⚠️ Theme filter not implemented (schema limitation)")
            with c_trigger:
                keywords = st.multiselect("Trigger Words", ["Dano Moral", "Lucros Cessantes", "Habeas Corpus", "ICMS"], default=["Dano Moral"])

            # 2. Filters
            st.markdown("---")
            c_toggles, c_sql = st.columns([1, 2])
            with c_toggles:
                st.caption("STRICT FILTERS")
                only_acordao = st.toggle("Somente Acórdãos", value=True)
                if only_acordao:
                    st.warning("⚠️ Excluding Monocratic Decisions")

            with c_sql:
                # Live SQL Generation Preview
                keyword_sql = " OR ".join([f"ementa LIKE '%{kw}%'" for kw in keywords]) if keywords else "1=1"
                tipo_sql = "AND tipo_decisao = 'Acórdão'" if only_acordao else ""
                sql_preview = f"""SELECT * FROM acordaos
WHERE ({keyword_sql})
{tipo_sql}
ORDER BY data_publicacao DESC
LIMIT 100"""
                st.text_area("SQL Generated Preview", sql_preview, height=100, disabled=True)

            run_query = st.button("RUN SMART QUERY", type="primary", use_container_width=True)

    with col_templates:
        st.markdown("#### TEMPLATES")
        # Template Buttons
        if st.button("⚡ Divergência Turmas"):
            st.toast("Template Loaded: Circuit Split")
        if st.button("🔖 Recursos Repetitivos"):
            st.toast("Template Loaded: Repetitive Appeals")
        if st.button("📅 Súmulas Recentes"):
            st.toast("Template Loaded: Recent Summaries")

    # --- RESULTS ---
    if run_query:
        if not keywords:
            st.info("ℹ️ Please select at least one trigger word to search")
        else:
            with st.spinner("Querying DuckDB..."):
                df = query_acordaos(keywords, only_acordao, limit=100)

                if df.empty:
                    st.info(f"📭 No results found for: {', '.join(keywords)}")
                else:
                    # Display summary stats
                    col_count, col_tipos, col_resultados = st.columns(3)
                    with col_count:
                        st.metric("Total Records", len(df))
                    with col_tipos:
                        if 'tipo' in df.columns:
                            st.caption("Decision Types")
                            tipo_counts = df['tipo'].value_counts()
                            st.write(tipo_counts.to_dict())
                    with col_resultados:
                        if 'resultado_julgamento' in df.columns:
                            st.caption("Outcomes Distribution")
                            valid_results = df['resultado_julgamento'].dropna()
                            if not valid_results.empty:
                                provimentos = sum(valid_results.str.lower().str.contains('provid|provimento', na=False))
                                desprovimentos = sum(valid_results.str.lower().str.contains('desprovid|desprovimento', na=False))
                                parciais = sum(valid_results.str.lower().str.contains('parcial', na=False))
                                st.write({
                                    "🟢 Provimento": provimentos,
                                    "🔴 Desprovimento": desprovimentos,
                                    "🟡 Parcial": parciais
                                })

                    st.markdown(f"### RESULTS ({len(df)} records)")

                    # Format resultado_julgamento with badges
                    if 'resultado_julgamento' in df.columns:
                        df_display = df.copy()
                        df_display['resultado_julgamento'] = df_display['resultado_julgamento'].apply(format_resultado_badge)
                    else:
                        df_display = df

                    # Truncate long ementa for readability
                    if 'ementa' in df_display.columns:
                        df_display['ementa'] = df_display['ementa'].str[:200] + '...'

                    st.dataframe(df_display, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# TAB 3: SOURCE CODE
# -----------------------------------------------------------------------------
with tab_code:
    st.header("Application Source Code")
    st.code(open(__file__).read(), language='python')
