# Trello-MCP Data Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add granular data extraction functionality to Trello-MCP module, allowing users to select specific cards/boards for extraction, view data in a clean format, and export to multiple formats.

**Architecture:** Refactor `modules/trello.py` to add 3 tabs: (1) Boards & Cards view with selection, (2) Data Extraction with granular control, (3) Card Management (create/move). Backend already has all methods in `trello_client.py`.

**Tech Stack:** Python 3.12, Streamlit, asyncio, pandas, existing TrelloClient

---

## Current State

| Component | Status | Issue |
|-----------|--------|-------|
| Backend `trello_client.py` | ✅ Complete | 38+ async methods available |
| Frontend `modules/trello.py` | ⚠️ Limited | Only regex extraction, no granular control |
| Card selection | ❌ Missing | Cannot select individual cards |
| Batch extraction | ❌ Missing | No batch mode with selection |
| Data visualization | ⚠️ Limited | Only pattern matches, not raw card data |
| Card creation | ❌ Not exposed | Backend has it, UI doesn't |

## Requirements (from PGR)

1. ✅ Keep card creation/manipulation (add to UI)
2. ➕ Add primary function: EXTRACT DATA from cards/boards
3. ➕ Granular control: individual to batch
4. ➕ Clean data visualization for verification

---

## Task 1: Restructure UI with 3 Tabs

**Files:**
- Modify: `legal-workbench/modules/trello.py:1-50`

**Step 1: Update imports and tab structure**

Add at top of file after existing imports:

```python
# Add these imports
import pandas as pd
from typing import Set

# Tab structure
TAB_BOARDS = "📋 Boards & Seleção"
TAB_EXTRACT = "📥 Extração de Dados"
TAB_MANAGE = "🔧 Gerenciar Cards"
```

**Step 2: Replace single render() with tabbed structure**

Change the render() function to start with:

```python
def render():
    """Renders the Streamlit UI for the Trello MCP module."""
    st.header("Trello MCP")
    st.caption("Extração e gerenciamento de dados jurídicos em boards Trello.")

    # Check API configuration first
    is_configured, config_message, api_key, api_token = check_api_configured()

    if not is_configured:
        render_credentials_form()
        return

    # Initialize client
    try:
        settings = EnvironmentSettings(
            trello_api_key=api_key,
            trello_api_token=api_token
        )
        client = TrelloClient(settings)
    except Exception as e:
        st.error(f"Erro ao inicializar cliente Trello: {e}")
        render_credentials_form()
        return

    # Initialize session state
    if "trello_selected_cards" not in st.session_state:
        st.session_state.trello_selected_cards = set()
    if "trello_extraction_mode" not in st.session_state:
        st.session_state.trello_extraction_mode = "individual"
    if "trello_extracted_data" not in st.session_state:
        st.session_state.trello_extracted_data = None

    # Sidebar status
    with st.sidebar:
        st.success("🟢 Trello Conectado")
        if st.button("🔓 Desconectar", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith('trello_'):
                    del st.session_state[key]
            st.rerun()

    # Tabs
    tab1, tab2, tab3 = st.tabs([TAB_BOARDS, TAB_EXTRACT, TAB_MANAGE])
```

**Step 3: Verify structure compiles**

Run: `cd legal-workbench && python -c "from modules import trello; print('OK')"`
Expected: "OK"

**Step 4: Commit**

```bash
git add legal-workbench/modules/trello.py
git commit -m "refactor(trello): restructure UI with 3 tabs"
```

---

## Task 2: Implement Tab 1 - Boards & Card Selection

**Files:**
- Modify: `legal-workbench/modules/trello.py`

**Step 1: Add Tab 1 content after tabs declaration**

```python
    # ==========================================================================
    # TAB 1: BOARDS & CARD SELECTION
    # ==========================================================================
    with tab1:
        st.subheader("Boards e Seleção de Cards")

        # --- Load Boards ---
        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("🔄 Carregar Boards", use_container_width=True):
                with st.spinner("Carregando boards..."):
                    try:
                        boards = asyncio.run(load_boards_async(client))
                        st.session_state.trello_boards = boards
                        st.success(f"✅ {len(boards)} boards carregados")
                    except Exception as e:
                        st.error(f"Erro: {e}")

        with col2:
            if st.session_state.get('trello_boards'):
                st.metric("Boards", len(st.session_state.trello_boards))

        # --- Board Selection ---
        if st.session_state.get('trello_boards'):
            st.markdown("---")
            st.markdown("### Selecionar Board")

            board_options = {b.name: b for b in st.session_state.trello_boards}
            selected_board_name = st.selectbox(
                "Escolha um board",
                options=list(board_options.keys()),
                key="board_selector"
            )

            if selected_board_name:
                selected_board = board_options[selected_board_name]
                st.session_state.trello_selected_board = selected_board

                # Load cards button
                if st.button("📥 Carregar Cards do Board", use_container_width=True):
                    with st.spinner(f"Carregando cards de {selected_board.name}..."):
                        try:
                            cards = asyncio.run(load_board_cards_async(client, selected_board.id))
                            st.session_state.trello_cards = cards
                            st.session_state.trello_selected_cards = set()
                            st.success(f"✅ {len(cards)} cards carregados")
                        except Exception as e:
                            st.error(f"Erro: {e}")

        # --- Card Selection Interface ---
        if st.session_state.get('trello_cards'):
            cards = st.session_state.trello_cards
            st.markdown("---")
            st.markdown("### Selecionar Cards para Extração")

            # Selection controls
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("☑️ Selecionar Todos"):
                    st.session_state.trello_selected_cards = {c.id for c in cards}
                    st.rerun()

            with col2:
                if st.button("⬜ Desmarcar Todos"):
                    st.session_state.trello_selected_cards = set()
                    st.rerun()

            with col3:
                st.metric("Selecionados", len(st.session_state.trello_selected_cards))

            # Card list with checkboxes
            st.markdown("**Cards Disponíveis:**")

            for card in cards:
                col1, col2, col3 = st.columns([0.5, 3, 1])

                with col1:
                    is_selected = card.id in st.session_state.trello_selected_cards
                    if st.checkbox(
                        "",
                        value=is_selected,
                        key=f"sel_{card.id}",
                        label_visibility="collapsed"
                    ):
                        st.session_state.trello_selected_cards.add(card.id)
                    else:
                        st.session_state.trello_selected_cards.discard(card.id)

                with col2:
                    st.markdown(f"**{card.name}**")
                    if card.desc:
                        st.caption(card.desc[:100] + "..." if len(card.desc) > 100 else card.desc)

                with col3:
                    # Labels
                    if card.labels:
                        labels_str = ", ".join([l.name for l in card.labels if l.name])
                        st.caption(f"🏷️ {labels_str}")

            # Selection summary
            if st.session_state.trello_selected_cards:
                st.info(f"📌 {len(st.session_state.trello_selected_cards)} cards selecionados. Vá para 'Extração de Dados' para extrair.")
```

**Step 2: Verify UI renders**

Run: `cd legal-workbench && streamlit run app.py --server.port 8502`
Expected: Tab 1 shows boards and card selection

**Step 3: Commit**

```bash
git add legal-workbench/modules/trello.py
git commit -m "feat(trello): add board and card selection UI"
```

---

## Task 3: Implement Tab 2 - Data Extraction

**Files:**
- Modify: `legal-workbench/modules/trello.py`

**Step 1: Add Tab 2 content**

```python
    # ==========================================================================
    # TAB 2: DATA EXTRACTION
    # ==========================================================================
    with tab2:
        st.subheader("Extração de Dados")

        # Check if cards are selected
        selected_ids = st.session_state.get('trello_selected_cards', set())
        all_cards = st.session_state.get('trello_cards', [])

        if not all_cards:
            st.info("👆 Primeiro carregue os cards na aba 'Boards & Seleção'")
            return

        # --- Extraction Mode ---
        st.markdown("### Modo de Extração")

        extraction_mode = st.radio(
            "Selecione o modo",
            options=["selected", "all", "pattern"],
            format_func=lambda x: {
                "selected": f"📌 Cards Selecionados ({len(selected_ids)})",
                "all": f"📋 Todos os Cards ({len(all_cards)})",
                "pattern": "🔍 Extração de Padrões (CPF, CNPJ, etc.)"
            }[x],
            horizontal=True
        )

        st.session_state.trello_extraction_mode = extraction_mode

        st.markdown("---")

        # --- Extraction Options ---
        st.markdown("### Opções de Extração")

        col1, col2 = st.columns(2)

        with col1:
            include_desc = st.checkbox("Incluir Descrição", value=True)
            include_labels = st.checkbox("Incluir Labels", value=True)
            include_due = st.checkbox("Incluir Due Date", value=True)

        with col2:
            include_custom = st.checkbox("Incluir Custom Fields", value=True)
            include_checklists = st.checkbox("Incluir Checklists", value=False)
            include_url = st.checkbox("Incluir URL", value=True)

        # Pattern extraction options (only if pattern mode)
        if extraction_mode == "pattern":
            st.markdown("### Padrões a Extrair")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                extract_cpf = st.checkbox("CPF", value=True)
            with col2:
                extract_cnpj = st.checkbox("CNPJ", value=True)
            with col3:
                extract_oab = st.checkbox("OAB", value=True)
            with col4:
                extract_valor = st.checkbox("Valores (R$)", value=True)

        st.markdown("---")

        # --- Extract Button ---
        if extraction_mode == "selected" and not selected_ids:
            st.warning("⚠️ Nenhum card selecionado. Selecione cards na aba anterior.")
            can_extract = False
        else:
            can_extract = True

        if st.button("📥 Extrair Dados", type="primary", disabled=not can_extract, use_container_width=True):
            with st.spinner("Extraindo dados..."):
                # Determine which cards to extract
                if extraction_mode == "selected":
                    cards_to_extract = [c for c in all_cards if c.id in selected_ids]
                else:
                    cards_to_extract = all_cards

                # Build extracted data
                extracted = []

                for card in cards_to_extract:
                    card_data = {
                        "id": card.id,
                        "name": card.name,
                    }

                    if include_desc:
                        card_data["description"] = card.desc or ""
                    if include_labels:
                        card_data["labels"] = [l.name for l in card.labels if l.name]
                    if include_due:
                        card_data["due_date"] = card.due
                    if include_url:
                        card_data["url"] = card.url
                    if include_custom and card.custom_field_items:
                        card_data["custom_fields"] = [
                            {"id": cf.id_custom_field, "value": cf.value}
                            for cf in card.custom_field_items
                        ]

                    # Pattern extraction
                    if extraction_mode == "pattern":
                        search_text = f"{card.name}\n{card.desc or ''}"
                        patterns = {}

                        if extract_cpf:
                            cpf_matches = re.findall(REGEX_MAP["cpf"], search_text)
                            if cpf_matches:
                                patterns["cpf"] = list(set(cpf_matches))

                        if extract_cnpj:
                            cnpj_matches = re.findall(REGEX_MAP["cnpj"], search_text)
                            if cnpj_matches:
                                patterns["cnpj"] = list(set(cnpj_matches))

                        if extract_oab:
                            oab_matches = re.findall(REGEX_MAP["oab"], search_text)
                            if oab_matches:
                                patterns["oab"] = list(set(oab_matches))

                        if extract_valor:
                            valor_matches = re.findall(REGEX_MAP["valor"], search_text)
                            if valor_matches:
                                patterns["valor"] = list(set(valor_matches))

                        if patterns:
                            card_data["patterns"] = patterns

                    extracted.append(card_data)

                st.session_state.trello_extracted_data = extracted
                st.success(f"✅ {len(extracted)} cards extraídos!")

        # --- Display Results ---
        if st.session_state.get('trello_extracted_data'):
            st.markdown("---")
            st.markdown("### Dados Extraídos")

            data = st.session_state.trello_extracted_data

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Cards", len(data))

            if extraction_mode == "pattern":
                total_patterns = sum(
                    len(c.get('patterns', {}).get('cpf', [])) +
                    len(c.get('patterns', {}).get('cnpj', [])) +
                    len(c.get('patterns', {}).get('oab', [])) +
                    len(c.get('patterns', {}).get('valor', []))
                    for c in data
                )
                col2.metric("Padrões Encontrados", total_patterns)

            # View mode
            view_mode = st.radio(
                "Visualização",
                options=["table", "json", "cards"],
                format_func=lambda x: {"table": "📊 Tabela", "json": "📋 JSON", "cards": "🃏 Cards"}[x],
                horizontal=True
            )

            if view_mode == "table":
                # Convert to DataFrame
                df_data = []
                for card in data:
                    row = {
                        "Nome": card["name"],
                        "Labels": ", ".join(card.get("labels", [])),
                        "Due": card.get("due_date", ""),
                    }
                    if "patterns" in card:
                        for ptype, pvalues in card["patterns"].items():
                            row[ptype.upper()] = ", ".join(pvalues)
                    df_data.append(row)

                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

            elif view_mode == "json":
                st.json(data)

            else:  # cards view
                for card in data:
                    with st.expander(f"📄 {card['name']}", expanded=False):
                        if card.get('description'):
                            st.markdown(f"**Descrição:** {card['description'][:500]}...")
                        if card.get('labels'):
                            st.markdown(f"**Labels:** {', '.join(card['labels'])}")
                        if card.get('due_date'):
                            st.markdown(f"**Due:** {card['due_date']}")
                        if card.get('patterns'):
                            st.markdown("**Padrões Encontrados:**")
                            st.json(card['patterns'])
                        if card.get('url'):
                            st.markdown(f"[🔗 Abrir no Trello]({card['url']})")

            # Export options
            st.markdown("---")
            st.markdown("### Exportar")

            col1, col2, col3 = st.columns(3)

            with col1:
                # JSON export
                import json
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                st.download_button(
                    "📥 JSON",
                    data=json_str,
                    file_name="trello_extraction.json",
                    mime="application/json",
                    use_container_width=True
                )

            with col2:
                # CSV export
                if df_data:
                    csv = pd.DataFrame(df_data).to_csv(index=False)
                    st.download_button(
                        "📥 CSV",
                        data=csv,
                        file_name="trello_extraction.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

            with col3:
                # Excel export (if openpyxl available)
                try:
                    import io
                    buffer = io.BytesIO()
                    pd.DataFrame(df_data).to_excel(buffer, index=False)
                    st.download_button(
                        "📥 Excel",
                        data=buffer.getvalue(),
                        file_name="trello_extraction.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except ImportError:
                    st.caption("Excel export requer openpyxl")
```

**Step 2: Verify extraction works**

Run: `cd legal-workbench && streamlit run app.py --server.port 8502`
Expected: Tab 2 allows extraction with different modes

**Step 3: Commit**

```bash
git add legal-workbench/modules/trello.py
git commit -m "feat(trello): add granular data extraction with multiple modes"
```

---

## Task 4: Implement Tab 3 - Card Management

**Files:**
- Modify: `legal-workbench/modules/trello.py`

**Step 1: Add Tab 3 content**

```python
    # ==========================================================================
    # TAB 3: CARD MANAGEMENT
    # ==========================================================================
    with tab3:
        st.subheader("Gerenciar Cards")
        st.caption("Criar, mover e arquivar cards no Trello")

        if not st.session_state.get('trello_boards'):
            st.info("👆 Primeiro carregue os boards na aba 'Boards & Seleção'")
            return

        # --- Create Card Section ---
        st.markdown("### ➕ Criar Novo Card")

        with st.form("create_card_form"):
            # Board selection
            board_options = {b.name: b for b in st.session_state.trello_boards}
            selected_board_name = st.selectbox(
                "Board",
                options=list(board_options.keys()),
                key="create_board"
            )

            # List selection (would need to load lists)
            list_id = st.text_input(
                "ID da Lista",
                placeholder="Digite o ID da lista de destino",
                help="Você pode encontrar o ID da lista na URL do Trello"
            )

            # Card details
            card_name = st.text_input("Nome do Card", placeholder="Título do card")
            card_desc = st.text_area("Descrição", placeholder="Descrição do card (opcional)")
            card_due = st.date_input("Data de Vencimento", value=None)

            submitted = st.form_submit_button("✅ Criar Card", type="primary")

            if submitted:
                if not list_id or not card_name:
                    st.error("Nome do card e ID da lista são obrigatórios")
                else:
                    try:
                        from models import CreateCardInput

                        input_data = CreateCardInput(
                            list_id=list_id,
                            name=card_name,
                            desc=card_desc if card_desc else None,
                            due=card_due.isoformat() if card_due else None
                        )

                        async def create():
                            async with client:
                                return await client.create_card(input_data)

                        new_card = asyncio.run(create())
                        st.success(f"✅ Card criado: {new_card.name}")
                        st.markdown(f"[🔗 Abrir no Trello]({new_card.url})")

                    except Exception as e:
                        st.error(f"Erro ao criar card: {e}")

        st.markdown("---")

        # --- Move Card Section ---
        st.markdown("### 🔀 Mover Card")

        with st.form("move_card_form"):
            card_id = st.text_input(
                "ID do Card",
                placeholder="ID do card a mover",
                key="move_card_id"
            )

            target_list_id = st.text_input(
                "ID da Lista Destino",
                placeholder="ID da lista de destino",
                key="move_list_id"
            )

            move_submitted = st.form_submit_button("🔀 Mover Card")

            if move_submitted:
                if not card_id or not target_list_id:
                    st.error("ID do card e ID da lista destino são obrigatórios")
                else:
                    try:
                        from models import MoveCardInput

                        input_data = MoveCardInput(
                            card_id=card_id,
                            target_list_id=target_list_id
                        )

                        async def move():
                            async with client:
                                return await client.move_card(input_data)

                        moved_card = asyncio.run(move())
                        st.success(f"✅ Card movido: {moved_card.name}")

                    except Exception as e:
                        st.error(f"Erro ao mover card: {e}")

        st.markdown("---")

        # --- Quick Actions on Selected Cards ---
        st.markdown("### ⚡ Ações Rápidas")

        selected_cards = st.session_state.get('trello_selected_cards', set())

        if selected_cards:
            st.info(f"📌 {len(selected_cards)} cards selecionados")

            col1, col2 = st.columns(2)

            with col1:
                target_list_batch = st.text_input(
                    "Mover todos para lista",
                    placeholder="ID da lista destino",
                    key="batch_move_list"
                )

                if st.button("🔀 Mover Selecionados"):
                    if target_list_batch:
                        # Batch move would be implemented here
                        st.info("Movendo cards em lote...")
                        # TODO: Implement batch_move in backend
                    else:
                        st.warning("Informe o ID da lista destino")

            with col2:
                if st.button("🗄️ Arquivar Selecionados"):
                    st.info("Arquivando cards...")
                    # TODO: Implement batch_archive in backend
        else:
            st.caption("Selecione cards na aba 'Boards & Seleção' para ações em lote")
```

**Step 2: Commit**

```bash
git add legal-workbench/modules/trello.py
git commit -m "feat(trello): add card management UI (create, move)"
```

---

## Task 5: Run Tests and Final Commit

**Step 1: Verify module imports**

Run: `cd legal-workbench && python -c "from modules.trello import render; print('OK')"`
Expected: "OK"

**Step 2: Test UI manually**

Run: `cd legal-workbench && streamlit run app.py --server.port 8502`
Expected: All 3 tabs functional

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat(trello): complete data extraction and management overhaul

- Restructure UI into 3 tabs: Boards, Extraction, Management
- Add granular card selection with checkboxes
- Add multiple extraction modes: selected, all, pattern
- Add clean data visualization (table, JSON, cards view)
- Add export options: JSON, CSV, Excel
- Add card creation and move functionality
- Maintain existing pattern extraction (CPF, CNPJ, OAB, values)

Closes #XX"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Restructure with 3 tabs | `modules/trello.py` |
| 2 | Card selection UI | `modules/trello.py` |
| 3 | Data extraction | `modules/trello.py` |
| 4 | Card management | `modules/trello.py` |
| 5 | Tests & final commit | - |

**Total Estimated Time:** 1-2 hours

**Key Features:**
- Granular card selection (individual checkboxes)
- Multiple extraction modes (selected/all/pattern)
- Clean data visualization (table, JSON, expandable cards)
- Export to JSON, CSV, Excel
- Card creation and move functionality
