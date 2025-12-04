import streamlit as st
import duckdb
import pandas as pd
import time
import datetime
import random

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
            bar = st.progress(0)
            for i in range(1, 101):
                time.sleep(0.02)
                if i % 15 == 0:
                    logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] INFO: Batch {i} archived.")
                
                # Render Terminal
                log_html = "<br>".join([f"<span style='color:#64748b'>></span> {l}" for l in logs[-8:]])
                terminal.markdown(f"""
                    <div style='background-color: #020617; padding: 15px; border-radius: 6px; border: 1px solid #1e293b; height: 300px; font-family: monospace; font-size: 12px;'>
                        <div style='color: #38bdf8; margin-bottom: 10px;'>root@stj-node-01:~/extraction# ./batch_runner.sh</div>
                        {log_html}
                        <div style='display: inline-block; width: 8px; height: 14px; background-color: #10b981; margin-left: 5px; animation: blink 1s infinite;'></div>
                    </div>
                """, unsafe_allow_html=True)
                bar.progress(i)
            st.session_state['extracting'] = False
            st.success("Extraction Complete.")
        else:
            terminal.info("System Ready. Awaiting Command.")

# -----------------------------------------------------------------------------
# TAB 2: JURISPRUDENCE LAB (SMART QUERY)
# -----------------------------------------------------------------------------
with tab_lab:
    # --- MOCK DATA ---
    @st.cache_data
    def get_data():
        return pd.DataFrame({
            'id': [f'DOC-{i}' for i in range(1000, 1050)],
            'processo': [f'REsp {random.randint(1e6, 2e6)}/SP' for _ in range(50)],
            'relator': [random.choice(['Min. Nancy Andrighi', 'Min. Herman Benjamin']) for _ in range(50)],
            'tema': [random.choice(['Direito Civil', 'Tributário', 'Penal']) for _ in range(50)],
            'tipo': [random.choice(['Acórdão', 'Decisão Monocrática']) for _ in range(50)],
            'data': [(datetime.date(2023,1,1) + datetime.timedelta(days=i)).isoformat() for i in range(50)]
        })
    
    df = get_data()

    # --- QUERY BUILDER UI ---
    col_builder, col_templates = st.columns([3, 1])
    
    with col_builder:
        st.markdown("#### SMART QUERY BUILDER")
        with st.container(border=True):
            # 1. Semantic Inputs
            c_theme, c_trigger = st.columns(2)
            with c_theme:
                theme = st.selectbox("Legal Domain (Theme)", ["Direito Civil", "Direito Penal", "Tributário", "Administrativo"])
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
                # Live SQL Generation
                sql_preview = f"SELECT * FROM stj_acordaos \nWHERE tema = '{theme}' \nAND contains(ementa, {keywords}) \n{'AND tipo = ACORDAO' if only_acordao else ''}"
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
        with st.spinner("Querying DuckDB..."):
            time.sleep(0.5)
            filtered = df[df['tema'] == theme] if theme else df
            if only_acordao:
                filtered = filtered[filtered['tipo'] == 'Acórdão']
            
            st.markdown(f"### RESULTS ({len(filtered)} records)")
            st.dataframe(filtered, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 3: SOURCE CODE
# -----------------------------------------------------------------------------
with tab_code:
    st.header("Application Source Code")
    st.code(open(__file__).read(), language='python')
