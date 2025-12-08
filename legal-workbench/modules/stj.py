# modules/stj.py

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
from datetime import datetime, timedelta

# Setup backend path (must be done before imports)
_backend_path = Path(__file__).parent.parent / "ferramentas" / "stj-dados-abertos"


def _setup_imports():
    """Lazy import setup to avoid module resolution issues."""
    if str(_backend_path) not in sys.path:
        sys.path.insert(0, str(_backend_path))

    from src.database import STJDatabase
    from config import DATABASE_PATH, ORGAOS_JULGADORES
    return STJDatabase, DATABASE_PATH, ORGAOS_JULGADORES


def render():
    """Renders the Streamlit UI for the STJ Dados Abertos module."""
    # Lazy imports to avoid module resolution issues
    STJDatabase, DATABASE_PATH, ORGAOS_JULGADORES = _setup_imports()

    st.header("STJ Dados Abertos")
    st.caption("Busca em acórdãos do Superior Tribunal de Justiça (STJ)")

    # --- Session State Initialization ---
    if "stj_search_results" not in st.session_state:
        st.session_state.stj_search_results = None
    if "stj_stats" not in st.session_state:
        st.session_state.stj_stats = None

    # --- Database Connection Check ---
    db_exists = DATABASE_PATH.exists()

    # --- Database Status ---
    st.subheader("Status do Banco de Dados")

    if not db_exists:
        st.error(f"Base de dados não encontrada em: `{DATABASE_PATH}`")
        st.info("""
        **Como criar a base de dados:**

        Execute o aplicativo standalone para fazer o download dos dados:

        ```bash
        cd legal-workbench/ferramentas/stj-dados-abertos
        source .venv/bin/activate
        streamlit run app.py
        ```

        O aplicativo standalone oferece funcionalidades completas de download,
        processamento e gerenciamento de dados do STJ.
        """)
        return

    # --- Database Metrics ---
    try:
        with STJDatabase(DATABASE_PATH) as db:
            stats = db.obter_estatisticas()
            st.session_state.stj_stats = stats

        if stats:
            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Total de Acórdãos",
                f"{stats.get('total_acordaos', 0):,}".replace(",", ".")
            )

            col2.metric(
                "Últimos 30 dias",
                f"{stats.get('ultimos_30_dias', 0):,}".replace(",", ".")
            )

            col3.metric(
                "Tamanho do Banco",
                f"{stats.get('tamanho_db_mb', 0):.1f} MB"
            )

            periodo = stats.get('periodo', {})
            mais_recente = periodo.get('mais_recente', 'N/A')
            if isinstance(mais_recente, str) and mais_recente != 'N/A':
                mais_recente_date = datetime.fromisoformat(mais_recente)
                mais_recente = mais_recente_date.strftime("%d/%m/%Y")

            col4.metric(
                "Última Publicação",
                str(mais_recente)
            )

    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {e}")
        stats = None

    st.markdown("---")

    # --- Tabs ---
    tab1, tab2, tab3 = st.tabs(["🔍 Busca", "📥 Download", "📊 Estatísticas"])

    # --- TAB 1: BUSCA ---
    with tab1:
        st.subheader("Buscar Acórdãos")

        # Search form
        col1, col2 = st.columns([3, 1])

        with col1:
            search_term = st.text_input(
                "Termo de busca",
                placeholder="Ex: prescrição tributária, responsabilidade civil...",
                help="Busca em ementas e textos integrais dos acórdãos"
            )

        with col2:
            search_type = st.selectbox(
                "Buscar em",
                ["Ementa", "Texto Integral"],
                help="Texto Integral pode ser mais lento em bases grandes"
            )

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            orgao_filter = st.selectbox(
                "Órgão Julgador",
                ["Todos"] + [config["name"] for config in ORGAOS_JULGADORES.values()],
                help="Filtrar por órgão julgador específico"
            )

        with col2:
            # Convert orgao name back to key for search
            orgao_key = None
            if orgao_filter != "Todos":
                for key, config in ORGAOS_JULGADORES.items():
                    if config["name"] == orgao_filter:
                        orgao_key = key
                        break

            dias_options = {
                "Últimos 30 dias": 30,
                "Últimos 90 dias": 90,
                "Último ano": 365,
                "Últimos 2 anos": 730,
                "Últimos 3 anos": 1095
            }
            dias_label = st.selectbox(
                "Período",
                list(dias_options.keys()),
                help="Limitar busca a um período específico"
            )
            dias = dias_options[dias_label]

        with col3:
            limit = st.number_input(
                "Máximo de resultados",
                min_value=10,
                max_value=500,
                value=50,
                step=10,
                help="Número máximo de resultados a retornar"
            )

        # Search button
        if st.button("🔍 Buscar", type="primary", use_container_width=True):
            if not search_term:
                st.warning("Digite um termo para buscar")
            else:
                with st.spinner("Buscando acórdãos..."):
                    try:
                        with STJDatabase(DATABASE_PATH) as db:
                            if search_type == "Ementa":
                                results = db.buscar_ementa(
                                    termo=search_term,
                                    orgao=orgao_key,
                                    dias=dias,
                                    limit=limit
                                )
                            else:
                                results = db.buscar_acordao(
                                    termo=search_term,
                                    orgao=orgao_key,
                                    dias=dias,
                                    limit=limit
                                )

                            st.session_state.stj_search_results = results

                    except Exception as e:
                        st.error(f"Erro na busca: {e}")
                        st.session_state.stj_search_results = None

        # Display results
        if st.session_state.stj_search_results is not None:
            results = st.session_state.stj_search_results

            st.markdown("---")
            st.subheader(f"Resultados ({len(results)} encontrados)")

            if len(results) == 0:
                st.info("Nenhum resultado encontrado para os critérios especificados.")
            else:
                # Convert to DataFrame for better display
                df = pd.DataFrame(results)

                # Format dates
                if 'data_publicacao' in df.columns:
                    df['data_publicacao'] = pd.to_datetime(df['data_publicacao']).dt.strftime('%d/%m/%Y')
                if 'data_julgamento' in df.columns:
                    df['data_julgamento'] = pd.to_datetime(df['data_julgamento']).dt.strftime('%d/%m/%Y')

                # Display each result as an expandable card
                for idx, row in df.iterrows():
                    with st.expander(f"📄 {row['numero_processo']} - {row['orgao_julgador']}"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown(f"**Processo:** {row['numero_processo']}")
                            st.markdown(f"**Órgão:** {row['orgao_julgador']}")
                            if 'tipo_decisao' in row and pd.notna(row['tipo_decisao']):
                                st.markdown(f"**Tipo:** {row['tipo_decisao']}")

                        with col2:
                            st.markdown(f"**Relator:** {row.get('relator', 'N/A')}")
                            st.markdown(f"**Publicação:** {row.get('data_publicacao', 'N/A')}")
                            if 'data_julgamento' in row and pd.notna(row['data_julgamento']):
                                st.markdown(f"**Julgamento:** {row['data_julgamento']}")

                        st.markdown("**Ementa:**")
                        st.text_area(
                            "ementa",
                            value=row.get('ementa', 'N/A'),
                            height=150,
                            key=f"ementa_{idx}",
                            label_visibility="collapsed"
                        )

                # Download results as CSV
                st.download_button(
                    label="📥 Download resultados (CSV)",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name=f"stj_resultados_{datetime.now():%Y%m%d_%H%M%S}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    # --- TAB 2: DOWNLOAD ---
    with tab2:
        st.subheader("Download de Dados")

        st.info("""
        **Gerenciamento de Downloads**

        Para fazer download de novos dados do STJ, utilize o aplicativo standalone
        que oferece funcionalidades completas:

        - Download retroativo (2022 até hoje)
        - Seleção de órgãos julgadores
        - Processamento em lote
        - Monitoramento de progresso
        - Gerenciamento de armazenamento

        **Como executar:**

        ```bash
        cd legal-workbench/ferramentas/stj-dados-abertos
        source .venv/bin/activate
        streamlit run app.py
        ```

        O aplicativo standalone possui interface completa com dashboard DuckDB
        e todas as ferramentas necessárias para gerenciar a base de dados.
        """)

        if db_exists and stats:
            st.markdown("**Dados disponíveis no banco atual:**")

            periodo = stats.get('periodo', {})
            st.markdown(f"- **Período:** {periodo.get('mais_antigo', 'N/A')} até {periodo.get('mais_recente', 'N/A')}")
            st.markdown(f"- **Total de acórdãos:** {stats.get('total_acordaos', 0):,}".replace(",", "."))

            por_orgao = stats.get('por_orgao', {})
            if por_orgao:
                st.markdown("**Distribuição por órgão:**")
                for orgao, count in list(por_orgao.items())[:5]:
                    st.markdown(f"  - {orgao}: {count:,}".replace(",", "."))

    # --- TAB 3: ESTATÍSTICAS ---
    with tab3:
        st.subheader("Estatísticas do Banco de Dados")

        if not stats:
            st.warning("Estatísticas não disponíveis")
        else:
            # Overview
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📈 Resumo Geral")
                st.markdown(f"**Total de acórdãos:** {stats.get('total_acordaos', 0):,}".replace(",", "."))
                st.markdown(f"**Tamanho do banco:** {stats.get('tamanho_db_mb', 0):.1f} MB")
                st.markdown(f"**Acórdãos (últimos 30 dias):** {stats.get('ultimos_30_dias', 0):,}".replace(",", "."))

                periodo = stats.get('periodo', {})
                st.markdown(f"**Período coberto:**")
                st.markdown(f"  - De: {periodo.get('mais_antigo', 'N/A')}")
                st.markdown(f"  - Até: {periodo.get('mais_recente', 'N/A')}")

            with col2:
                st.markdown("### 📊 Distribuição por Tipo")
                por_tipo = stats.get('por_tipo', {})
                if por_tipo:
                    tipo_df = pd.DataFrame(
                        list(por_tipo.items()),
                        columns=['Tipo', 'Quantidade']
                    ).sort_values('Quantidade', ascending=False)
                    st.dataframe(tipo_df, use_container_width=True, hide_index=True)

            # Chart: Distribuição por órgão
            st.markdown("### 📊 Acórdãos por Órgão Julgador")
            por_orgao = stats.get('por_orgao', {})
            if por_orgao:
                orgao_df = pd.DataFrame(
                    list(por_orgao.items()),
                    columns=['Órgão', 'Quantidade']
                ).sort_values('Quantidade', ascending=False)

                st.bar_chart(orgao_df.set_index('Órgão'))

                # Details table
                with st.expander("Ver detalhes"):
                    st.dataframe(orgao_df, use_container_width=True, hide_index=True)
