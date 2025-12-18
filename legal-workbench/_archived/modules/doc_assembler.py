# modules/doc_assembler.py

import streamlit as st
from pathlib import Path
import sys
import json
import zipfile
import tempfile
import re
from typing import Dict, Any, Optional, List, Tuple

# Setup backend path (must be done before imports)
_backend_path = Path(__file__).parent.parent / "ferramentas" / "legal-doc-assembler"

# Module-level variables for lazy-loaded imports
_DocumentEngine = None
_BatchProcessor = None
_normalize_all = None
_TemplateBuilder = None
_TemplateManager = None
_PatternDetector = None

# Templates directory path
TEMPLATES_DIR = Path(__file__).parent.parent / "ferramentas" / "legal-doc-assembler" / "templates"


def _setup_imports():
    """Lazy import setup to avoid module resolution issues."""
    global _DocumentEngine, _BatchProcessor, _normalize_all, _TemplateBuilder, _TemplateManager, _PatternDetector

    if _DocumentEngine is None:
        if str(_backend_path) not in sys.path:
            sys.path.insert(0, str(_backend_path))

        from src.engine import DocumentEngine
        from src.batch_engine import BatchProcessor
        from src.normalizers import normalize_all
        from src.template_builder import TemplateBuilder
        from src.template_manager import TemplateManager
        from src.pattern_detector import PatternDetector

        _DocumentEngine = DocumentEngine
        _BatchProcessor = BatchProcessor
        _normalize_all = normalize_all
        _TemplateBuilder = TemplateBuilder
        _TemplateManager = TemplateManager
        _PatternDetector = PatternDetector

    return _DocumentEngine, _BatchProcessor, _normalize_all


def identify_modified_segments(original_text: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify which segments of text were modified from template variables.

    Returns list of dicts with:
        - 'start': start index in text
        - 'end': end index in text
        - 'field': original template field name
        - 'value': rendered value
    """
    segments = []

    for field, value in data.items():
        if isinstance(value, str) and value:
            # Find all occurrences of this value in the text
            pattern = re.escape(str(value))
            for match in re.finditer(pattern, original_text):
                segments.append({
                    'start': match.start(),
                    'end': match.end(),
                    'field': field,
                    'value': value,
                    'original': f'{{{{ {field} }}}}'
                })

    # Sort by position
    segments.sort(key=lambda x: x['start'])
    return segments


def render():
    """Renders the Streamlit UI for the Document Assembler module."""
    # Initialize lazy imports
    _setup_imports()

    st.header("Document Assembler")
    st.caption("Monte documentos jurídicos a partir de templates .docx e dados JSON.")

    # --- Session State Initialization ---
    if "assembled_docs" not in st.session_state:
        st.session_state.assembled_docs = []
    if "batch_result" not in st.session_state:
        st.session_state.batch_result = None
    if "validation_result" not in st.session_state:
        st.session_state.validation_result = None
    if "preview_result" not in st.session_state:
        st.session_state.preview_result = None
    if "preview_modifications" not in st.session_state:
        st.session_state.preview_modifications = {}
    if "current_template_path" not in st.session_state:
        st.session_state.current_template_path = None
    if "current_json_data" not in st.session_state:
        st.session_state.current_json_data = None

    # --- Tab Navigation ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Documento Único",
        "📦 Processamento em Lote",
        "🔧 Criar Template",
        "📚 Galeria de Templates"
    ])

    # ===== TAB 1: SINGLE DOCUMENT =====
    with tab1:
        render_single_document_tab()

    # ===== TAB 2: BATCH PROCESSING =====
    with tab2:
        render_batch_processing_tab()

    # ===== TAB 3: TEMPLATE CREATOR =====
    with tab3:
        render_template_creator_tab()

    # ===== TAB 4: TEMPLATE GALLERY =====
    with tab4:
        render_template_gallery_tab()


def render_single_document_tab():
    """Render single document processing UI."""
    st.subheader("Processamento de Documento Único")
    st.markdown("Envie um template .docx e um arquivo JSON com os dados para gerar o documento.")

    col1, col2 = st.columns(2)

    with col1:
        template_file = st.file_uploader(
            "Template (.docx)",
            type="docx",
            key="single_template",
            help="Arquivo .docx com variáveis Jinja2 (ex: {{ nome }}, {{ cpf | cpf }})"
        )

    with col2:
        json_file = st.file_uploader(
            "Dados (JSON)",
            type="json",
            key="single_json",
            help="Arquivo JSON com os valores para as variáveis do template"
        )

    # --- Field Types Configuration ---
    with st.expander("⚙️ Configuração Avançada (Opcional)", expanded=False):
        st.markdown("**Tipos de campos para normalização automática:**")
        st.caption(
            "Deixe em branco para normalização automática básica. "
            "Cole um JSON mapeando campos para tipos: `{\"nome\": \"name\", \"cpf\": \"cpf\"}`"
        )

        field_types_json = st.text_area(
            "Mapeamento de Tipos",
            value="",
            height=100,
            placeholder='{"nome": "name", "endereco": "address", "cpf": "cpf", "cnpj": "cnpj"}',
            help=(
                "Tipos disponíveis: name, address, cpf, cnpj, cep, oab, text, raw. "
                "Exemplo: {\"nome\": \"name\", \"cpf\": \"cpf\"}"
            )
        )

    # --- Preview JSON Data ---
    if json_file:
        with st.expander("👁️ Visualizar Dados JSON", expanded=False):
            try:
                json_data = json.loads(json_file.getvalue().decode("utf-8"))
                st.json(json_data)
            except json.JSONDecodeError as e:
                st.error(f"JSON inválido: {e}")

    # --- Action Buttons ---
    if template_file and json_file:
        col_validate, col_preview, col_render = st.columns(3)

        with col_validate:
            if st.button("🔍 Validar", use_container_width=True, key="validate_single"):
                validate_single_document(template_file, json_file)

        with col_preview:
            if st.button("👁️ Pré-visualizar", use_container_width=True, key="preview_single"):
                field_types = parse_field_types(field_types_json)
                preview_single_document(template_file, json_file, field_types)

        with col_render:
            if st.button("▶️ Gerar Documento", use_container_width=True, type="primary", key="render_single"):
                field_types = parse_field_types(field_types_json)
                render_single_document(template_file, json_file, field_types)

    # --- Validation Results Display ---
    if st.session_state.validation_result:
        display_validation_result(st.session_state.validation_result)

    # --- Preview Display with Text Selection ---
    if st.session_state.preview_result:
        display_preview_with_selection()

    # --- Assembled Documents Display ---
    if st.session_state.assembled_docs:
        st.markdown("---")
        st.subheader("📥 Documentos Gerados")

        for idx, doc_info in enumerate(st.session_state.assembled_docs):
            col_name, col_download = st.columns([3, 1])

            with col_name:
                st.text(f"✅ {doc_info['filename']}")

            with col_download:
                st.download_button(
                    label="Download",
                    data=doc_info['data'],
                    file_name=doc_info['filename'],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"download_single_{idx}"
                )


def render_batch_processing_tab():
    """Render batch processing UI."""
    st.subheader("Processamento em Lote")
    st.markdown("Processe múltiplos documentos simultaneamente usando um template e vários arquivos JSON.")

    # --- File Uploaders ---
    template_file = st.file_uploader(
        "Template (.docx)",
        type="docx",
        key="batch_template",
        help="Template único para todos os documentos"
    )

    upload_method = st.radio(
        "Método de Upload:",
        options=["Arquivos JSON Individuais", "Arquivo ZIP com JSONs"],
        horizontal=True,
        key="batch_upload_method"
    )

    json_files = []

    if upload_method == "Arquivos JSON Individuais":
        uploaded_jsons = st.file_uploader(
            "Arquivos JSON",
            type="json",
            accept_multiple_files=True,
            key="batch_jsons",
            help="Selecione múltiplos arquivos JSON (Ctrl/Cmd + clique)"
        )
        if uploaded_jsons:
            json_files = uploaded_jsons
    else:
        uploaded_zip = st.file_uploader(
            "Arquivo ZIP",
            type="zip",
            key="batch_zip",
            help="Arquivo ZIP contendo múltiplos arquivos JSON"
        )
        if uploaded_zip:
            json_files = extract_json_from_zip(uploaded_zip)

    # --- Configuration Options ---
    with st.expander("⚙️ Configurações de Lote", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            max_workers = st.slider(
                "Número de Workers",
                min_value=1,
                max_value=8,
                value=4,
                help="Número de processos paralelos para renderização"
            )

        with col2:
            create_zip = st.checkbox(
                "Criar arquivo ZIP de saída",
                value=True,
                help="Agrupa todos os documentos gerados em um único arquivo ZIP"
            )

        name_field = st.text_input(
            "Campo para nome do arquivo",
            value="",
            placeholder="nome",
            help="Nome do campo JSON usado para nomear os arquivos de saída (deixe vazio para numeração sequencial)"
        )

        field_types_json = st.text_area(
            "Mapeamento de Tipos (JSON)",
            value="",
            height=100,
            placeholder='{"nome": "name", "cpf": "cpf", "endereco": "address"}',
            help="JSON com mapeamento de campos para tipos de normalização"
        )

    # --- Action Buttons ---
    if template_file and json_files:
        st.info(f"📊 **{len(json_files)}** arquivos JSON carregados")

        col_validate, col_process = st.columns(2)

        with col_validate:
            if st.button("🔍 Validar Todos", use_container_width=True, key="validate_batch"):
                validate_batch_documents(template_file, json_files)

        with col_process:
            if st.button("▶️ Processar Lote", use_container_width=True, type="primary", key="process_batch"):
                field_types = parse_field_types(field_types_json)
                process_batch_documents(
                    template_file,
                    json_files,
                    max_workers,
                    create_zip,
                    name_field if name_field else None,
                    field_types
                )

    # --- Batch Results Display ---
    if st.session_state.batch_result:
        display_batch_result(st.session_state.batch_result)


# ===== HELPER FUNCTIONS =====

def parse_field_types(field_types_json: str) -> Optional[Dict[str, str]]:
    """Parse field types JSON string into dictionary."""
    if not field_types_json.strip():
        return None

    try:
        field_types = json.loads(field_types_json)
        if not isinstance(field_types, dict):
            st.error("Mapeamento de tipos deve ser um objeto JSON válido")
            return None
        return field_types
    except json.JSONDecodeError as e:
        st.error(f"JSON de mapeamento inválido: {e}")
        return None


def extract_json_from_zip(zip_file) -> List[Any]:
    """Extract all JSON files from uploaded ZIP."""
    json_files = []

    try:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            for filename in zf.namelist():
                if filename.endswith('.json') and not filename.startswith('__MACOSX'):
                    # Create a temporary file-like object for each JSON
                    content = zf.read(filename)
                    # Create a mock uploaded file object
                    json_files.append({
                        'name': Path(filename).name,
                        'content': content
                    })

        st.success(f"Extraídos {len(json_files)} arquivos JSON do ZIP")
    except Exception as e:
        st.error(f"Erro ao extrair ZIP: {e}")

    return json_files


def validate_single_document(template_file, json_file):
    """Validate single document data against template."""
    with st.spinner("Validando dados contra template..."):
        try:
            # Save template temporarily
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_template:
                tmp_template.write(template_file.getvalue())
                template_path = Path(tmp_template.name)

            # Load JSON data
            json_data = json.loads(json_file.getvalue().decode("utf-8"))

            # Validate using engine
            engine = _DocumentEngine()
            validation = engine.validate_data(template_path, json_data)

            # Store result
            st.session_state.validation_result = {
                'type': 'single',
                'validation': validation,
                'template_vars': engine.get_template_variables(template_path)
            }

            # Cleanup
            template_path.unlink()

        except Exception as e:
            st.error(f"Erro durante validação: {e}")
            st.session_state.validation_result = None


def preview_single_document(template_file, json_file, field_types: Optional[Dict[str, str]]):
    """Generate preview of rendered document without saving to file."""
    with st.spinner("Gerando pré-visualização..."):
        try:
            # Save template temporarily
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_template:
                tmp_template.write(template_file.getvalue())
                template_path = Path(tmp_template.name)

            # Load JSON data
            json_data = json.loads(json_file.getvalue().decode("utf-8"))

            # Extract rendered text (without saving to file)
            engine = _DocumentEngine(auto_normalize=True)
            preview_data = engine.extract_rendered_text(
                template_path=template_path,
                data=json_data,
                field_types=field_types
            )

            # Identify modified segments (fields that were replaced)
            segments = identify_modified_segments(preview_data['full_text'], json_data)

            # Store preview result
            st.session_state.preview_result = {
                'preview_data': preview_data,
                'json_data': json_data,
                'segments': segments,
                'template_path': str(template_path),
                'field_types': field_types
            }

            # Store for later rendering with modifications
            st.session_state.current_template_path = template_path
            st.session_state.current_json_data = json_data.copy()
            st.session_state.preview_modifications = {}

            st.success("✅ Pré-visualização gerada!")

        except Exception as e:
            st.error(f"Erro ao gerar pré-visualização: {e}")
            st.session_state.preview_result = None


def display_preview_with_selection():
    """Display preview with editable text fields for modification."""
    st.markdown("---")
    st.subheader("👁️ Pré-visualização do Documento")

    preview_result = st.session_state.preview_result
    preview_data = preview_result['preview_data']
    json_data = preview_result['json_data']
    segments = preview_result['segments']

    # --- Metrics ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Parágrafos", preview_data['paragraph_count'])
    with col2:
        st.metric("Tabelas", preview_data['table_count'])
    with col3:
        st.metric("Campos Preenchidos", len(segments))

    # --- Full Text Preview (Read-Only) ---
    with st.expander("📄 Texto Completo (Somente Leitura)", expanded=True):
        st.text_area(
            "Texto Renderizado",
            value=preview_data['full_text'],
            height=300,
            disabled=True,
            key="preview_full_text"
        )

    # --- Editable Fields Section ---
    st.markdown("### ✏️ Editar Campos Antes de Gerar")
    st.caption("Modifique os valores abaixo. As alterações serão aplicadas ao gerar o documento final.")

    # Group segments by field name (avoid duplicates)
    fields_displayed = set()
    modifications = st.session_state.preview_modifications.copy()

    for field, value in json_data.items():
        if isinstance(value, str) and field not in fields_displayed:
            fields_displayed.add(field)

            # Get current value (modified or original)
            current_value = modifications.get(field, value)

            col_label, col_input = st.columns([1, 3])

            with col_label:
                st.markdown(f"**{field}:**")
                if field in modifications:
                    st.caption("🔄 Modificado")

            with col_input:
                new_value = st.text_input(
                    f"Valor para {field}",
                    value=current_value,
                    key=f"edit_field_{field}",
                    label_visibility="collapsed"
                )

                # Track modifications
                if new_value != value:
                    st.session_state.preview_modifications[field] = new_value
                elif field in st.session_state.preview_modifications:
                    del st.session_state.preview_modifications[field]

    # --- Actions ---
    st.markdown("---")
    col_reset, col_apply = st.columns(2)

    with col_reset:
        if st.button("🔄 Restaurar Valores Originais", use_container_width=True):
            st.session_state.preview_modifications = {}
            st.rerun()

    with col_apply:
        if st.button("▶️ Gerar com Modificações", use_container_width=True, type="primary"):
            generate_with_modifications()

    # Show modification summary
    if st.session_state.preview_modifications:
        with st.expander("📝 Resumo das Modificações", expanded=True):
            for field, new_value in st.session_state.preview_modifications.items():
                original = json_data.get(field, "")
                st.markdown(f"**{field}:** `{original}` → `{new_value}`")


def generate_with_modifications():
    """Generate document with user modifications applied."""
    with st.spinner("Gerando documento com modificações..."):
        try:
            preview_result = st.session_state.preview_result
            template_path = st.session_state.current_template_path
            json_data = st.session_state.current_json_data.copy()
            modifications = st.session_state.preview_modifications

            # Apply modifications
            for field, new_value in modifications.items():
                json_data[field] = new_value

            # Create output path
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_output:
                output_path = Path(tmp_output.name)

            # Render document
            engine = _DocumentEngine(auto_normalize=True)
            result_path = engine.render(
                template_path=template_path,
                data=json_data,
                output_path=output_path,
                field_types=preview_result.get('field_types')
            )

            # Read generated document
            with open(result_path, 'rb') as f:
                doc_data = f.read()

            # Generate output filename
            output_filename = f"documento_modificado_{len(st.session_state.assembled_docs) + 1}.docx"

            # Store in session state
            st.session_state.assembled_docs.append({
                'filename': output_filename,
                'data': doc_data,
                'modifications': modifications.copy()
            })

            # Cleanup
            result_path.unlink()

            # Clear preview
            st.session_state.preview_result = None
            st.session_state.preview_modifications = {}

            st.success("✅ Documento gerado com modificações!")
            st.rerun()

        except Exception as e:
            st.error(f"Erro ao gerar documento: {e}")


def render_single_document(template_file, json_file, field_types: Optional[Dict[str, str]]):
    """Render single document from template and JSON."""
    with st.spinner("Gerando documento..."):
        try:
            # Save template temporarily
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_template:
                tmp_template.write(template_file.getvalue())
                template_path = Path(tmp_template.name)

            # Load JSON data
            json_data = json.loads(json_file.getvalue().decode("utf-8"))

            # Create output path
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_output:
                output_path = Path(tmp_output.name)

            # Render document
            engine = _DocumentEngine(auto_normalize=True)
            result_path = engine.render(
                template_path=template_path,
                data=json_data,
                output_path=output_path,
                field_types=field_types
            )

            # Read generated document
            with open(result_path, 'rb') as f:
                doc_data = f.read()

            # Generate output filename
            output_filename = f"{template_file.name.replace('.docx', '')}_gerado.docx"

            # Store in session state
            st.session_state.assembled_docs.append({
                'filename': output_filename,
                'data': doc_data
            })

            # Cleanup
            template_path.unlink()
            result_path.unlink()

            st.success("✅ Documento gerado com sucesso!")

        except Exception as e:
            st.error(f"Erro ao gerar documento: {e}")


def validate_batch_documents(template_file, json_files):
    """Validate batch of documents."""
    with st.spinner("Validando arquivos em lote..."):
        try:
            # Save template temporarily
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_template:
                tmp_template.write(template_file.getvalue())
                template_path = Path(tmp_template.name)

            # Create temporary directory for JSON files
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                json_paths = []

                # Save all JSON files
                for json_file in json_files:
                    if isinstance(json_file, dict):  # From ZIP
                        json_path = tmp_dir_path / json_file['name']
                        json_path.write_bytes(json_file['content'])
                    else:  # Uploaded file
                        json_path = tmp_dir_path / json_file.name
                        json_path.write_bytes(json_file.getvalue())
                    json_paths.append(json_path)

                # Validate
                processor = _BatchProcessor(max_workers=1)
                validation_result = processor.validate_batch(json_paths, template_path)

                # Store result
                st.session_state.validation_result = {
                    'type': 'batch',
                    'validation': validation_result
                }

            # Cleanup
            template_path.unlink()

        except Exception as e:
            st.error(f"Erro durante validação em lote: {e}")
            st.session_state.validation_result = None


def process_batch_documents(
    template_file,
    json_files,
    max_workers: int,
    create_zip: bool,
    name_field: Optional[str],
    field_types: Optional[Dict[str, str]]
):
    """Process batch of documents."""
    with st.spinner(f"Processando {len(json_files)} documentos com {max_workers} workers..."):
        progress_bar = st.progress(0, "Iniciando processamento...")

        try:
            # Save template temporarily
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_template:
                tmp_template.write(template_file.getvalue())
                template_path = Path(tmp_template.name)

            # Create temporary directories
            with tempfile.TemporaryDirectory() as tmp_json_dir, \
                 tempfile.TemporaryDirectory() as tmp_output_dir:

                tmp_json_path = Path(tmp_json_dir)
                tmp_output_path = Path(tmp_output_dir)
                json_paths = []

                # Save all JSON files
                progress_bar.progress(10, "Preparando arquivos...")
                for json_file in json_files:
                    if isinstance(json_file, dict):  # From ZIP
                        json_path = tmp_json_path / json_file['name']
                        json_path.write_bytes(json_file['content'])
                    else:  # Uploaded file
                        json_path = tmp_json_path / json_file.name
                        json_path.write_bytes(json_file.getvalue())
                    json_paths.append(json_path)

                # Process batch
                progress_bar.progress(30, "Processando documentos...")
                processor = _BatchProcessor(max_workers=max_workers, checkpoint_enabled=False)
                result = processor.process_batch(
                    json_files=json_paths,
                    template_path=template_path,
                    output_dir=tmp_output_path,
                    create_zip=create_zip,
                    name_field=name_field,
                    field_types=field_types,
                    resume=False
                )

                progress_bar.progress(80, "Coletando resultados...")

                # Store results
                batch_result = {
                    'summary': result,
                    'outputs': []
                }

                # Read output files
                if create_zip and result.get('zip_path'):
                    zip_path = Path(result['zip_path'])
                    with open(zip_path, 'rb') as f:
                        batch_result['zip_data'] = f.read()
                        batch_result['zip_name'] = zip_path.name
                else:
                    # Read individual files
                    for output_path_str in result['outputs']:
                        output_path = Path(output_path_str)
                        if output_path.exists():
                            with open(output_path, 'rb') as f:
                                batch_result['outputs'].append({
                                    'filename': output_path.name,
                                    'data': f.read()
                                })

                st.session_state.batch_result = batch_result

                progress_bar.progress(100, "Concluído!")

            # Cleanup
            template_path.unlink()

            st.success(f"✅ Processamento concluído: {result['success']} sucessos, {result['failed']} falhas")

        except Exception as e:
            st.error(f"Erro durante processamento em lote: {e}")
            st.session_state.batch_result = None


def display_validation_result(validation_result):
    """Display validation results."""
    st.markdown("---")
    st.subheader("📋 Resultado da Validação")

    if validation_result['type'] == 'single':
        validation = validation_result['validation']
        template_vars = validation_result['template_vars']

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Variáveis no Template", len(template_vars))

        with col2:
            status = "✅ Válido" if not validation['missing'] else "⚠️ Dados Incompletos"
            st.metric("Status", status)

        if validation['missing']:
            st.warning("**Campos Faltando:**")
            st.write(", ".join(validation['missing']))
            st.caption("Estes campos aparecerão como {{ campo }} no documento gerado.")

        if validation['extra']:
            st.info("**Campos Extras (não usados no template):**")
            st.write(", ".join(validation['extra']))

        with st.expander("🔤 Variáveis do Template", expanded=False):
            st.code(", ".join(sorted(template_vars)))

    else:  # batch
        validation = validation_result['validation']

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total de Arquivos", validation['total'])

        with col2:
            st.metric("Válidos", validation['valid_count'], delta_color="normal")

        with col3:
            st.metric("Inválidos", validation['invalid_count'], delta_color="inverse")

        if validation['errors']:
            with st.expander("⚠️ Erros Encontrados", expanded=True):
                for error in validation['errors']:
                    st.error(f"**{error['json_file']}**: {error['message']}")

        if validation['valid']:
            st.success("✅ Todos os arquivos estão válidos e prontos para processamento!")


def display_batch_result(batch_result):
    """Display batch processing results."""
    st.markdown("---")
    st.subheader("📊 Resultado do Processamento")

    summary = batch_result['summary']

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total", summary['total'])

    with col2:
        st.metric("✅ Sucesso", summary['success'])

    with col3:
        st.metric("❌ Falhas", summary['failed'])

    with col4:
        st.metric("⏱️ Duração", summary['duration_formatted'])

    # Errors display
    if summary['errors']:
        with st.expander("⚠️ Erros Detalhados", expanded=False):
            for error in summary['errors']:
                st.error(f"**{error['json_file']}**: {error['message']}")
                if error.get('traceback'):
                    with st.expander("Stack Trace"):
                        st.code(error['traceback'], language="python")

    # Download section
    st.markdown("### 📥 Downloads")

    if batch_result.get('zip_data'):
        # Single ZIP download
        st.download_button(
            label=f"⬇️ Download ZIP ({summary['success']} documentos)",
            data=batch_result['zip_data'],
            file_name=batch_result['zip_name'],
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )
    else:
        # Individual file downloads
        for idx, output_info in enumerate(batch_result['outputs']):
            st.download_button(
                label=f"⬇️ {output_info['filename']}",
                data=output_info['data'],
                file_name=output_info['filename'],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"download_batch_{idx}"
            )

    # Summary JSON
    with st.expander("📄 Relatório JSON", expanded=False):
        # Remove binary data before displaying
        display_summary = {k: v for k, v in summary.items() if k not in ['outputs']}
        display_summary['output_count'] = len(summary['outputs'])
        st.json(display_summary)


def render_template_creator_tab():
    """Render template creation UI."""
    st.subheader("Criar Template")
    st.caption("Transforme um documento DOCX comum em template Jinja2 reutilizável")

    # Initialize session state for template creator
    if 'template_builder' not in st.session_state:
        st.session_state.template_builder = None
    if 'detected_patterns' not in st.session_state:
        st.session_state.detected_patterns = []
    if 'selected_patterns' not in st.session_state:
        st.session_state.selected_patterns = []
    if 'manual_fields' not in st.session_state:
        st.session_state.manual_fields = []

    # --- STEP 1: Upload Source Document ---
    st.markdown("### 1. Carregar Documento Fonte")

    source_file = st.file_uploader(
        "Selecione um documento DOCX",
        type=['docx'],
        key='template_source',
        help="O documento será analisado para criar um template"
    )

    if source_file:
        # Save to temp and create builder
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp.write(source_file.read())
            tmp_path = tmp.name

        try:
            st.session_state.template_builder = _TemplateBuilder(tmp_path)
            st.success(f"✅ Documento carregado: {source_file.name}")

            # Show structure summary
            structure = st.session_state.template_builder.get_structure()
            col1, col2, col3 = st.columns(3)
            col1.metric("Parágrafos", structure['paragraphs'])
            col2.metric("Tabelas", structure['tables'])
            col3.metric("Seções", structure['sections'])

        except Exception as e:
            st.error(f"Erro ao carregar documento: {e}")
            st.session_state.template_builder = None

    if st.session_state.template_builder:
        builder = st.session_state.template_builder

        st.markdown("---")

        # --- STEP 2: Preview ---
        st.markdown("### 2. Visualizar Conteúdo")

        with st.expander("📖 Preview do Documento", expanded=True):
            preview_text = builder.get_modified_text()
            st.text_area(
                "Conteúdo atual",
                value=preview_text,
                height=300,
                disabled=True,
                key='template_preview'
            )

        st.markdown("---")

        # --- STEP 3A: Automatic Detection ---
        st.markdown("### 3A. Detecção Automática de Padrões")
        st.caption("Detecta CPF, CNPJ, OAB, CEP, valores monetários automaticamente")

        col1, col2 = st.columns([1, 3])

        with col1:
            if st.button("🔍 Detectar Padrões", use_container_width=True):
                st.session_state.detected_patterns = builder.detect_patterns()
                st.rerun()

        with col2:
            if st.session_state.detected_patterns:
                st.info(f"Encontrados {len(st.session_state.detected_patterns)} padrões")

        if st.session_state.detected_patterns:
            st.markdown("**Padrões Detectados:**")

            for i, pattern in enumerate(st.session_state.detected_patterns):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

                with col1:
                    st.code(pattern['value'], language=None)

                with col2:
                    st.caption(f"Tipo: {pattern['type'].upper()}")

                with col3:
                    # Allow editing field name
                    field_name = st.text_input(
                        "Campo",
                        value=pattern['suggested_field'],
                        key=f"field_{i}",
                        label_visibility="collapsed"
                    )
                    pattern['custom_field'] = field_name

                with col4:
                    if st.checkbox("✓", key=f"apply_{i}", value=True):
                        if pattern not in st.session_state.selected_patterns:
                            st.session_state.selected_patterns.append(pattern)

            if st.button("✅ Aplicar Selecionados", type="primary"):
                for pattern in st.session_state.selected_patterns:
                    field_name = pattern.get('custom_field', pattern['suggested_field'])
                    builder.add_field_replacement(
                        pattern['value'],
                        field_name,
                        pattern['filter']
                    )
                st.session_state.selected_patterns = []
                st.session_state.detected_patterns = []
                st.success("Padrões aplicados!")
                st.rerun()

        st.markdown("---")

        # --- STEP 3B: Manual Selection ---
        st.markdown("### 3B. Seleção Manual")
        st.caption("Selecione qualquer texto para transformar em campo")

        col1, col2, col3 = st.columns(3)

        with col1:
            manual_text = st.text_input(
                "Texto a substituir",
                placeholder="Cole o texto exato do documento",
                key='manual_text'
            )

        with col2:
            manual_field = st.text_input(
                "Nome do campo",
                placeholder="Ex: nome_cliente",
                key='manual_field'
            )

        with col3:
            manual_filter = st.selectbox(
                "Filtro",
                options=['', 'nome', 'endereco', 'cpf', 'cnpj', 'cep', 'oab', 'valor', 'data'],
                key='manual_filter'
            )

        if st.button("➕ Adicionar Campo Manual"):
            if manual_text and manual_field:
                success = builder.add_field_replacement(
                    manual_text,
                    manual_field,
                    manual_filter
                )
                if success:
                    st.success(f"Campo '{manual_field}' adicionado!")
                    st.rerun()
                else:
                    st.error("Texto não encontrado no documento")
            else:
                st.warning("Preencha o texto e o nome do campo")

        # Show current fields
        fields = builder.get_fields()
        if fields:
            st.markdown("**Campos Configurados:**")
            for field in fields:
                col1, col2, col3 = st.columns([3, 2, 1])
                col1.code(field['jinja'])
                col2.caption(f"Original: {field['original_sample']}...")
                if col3.button("🗑️", key=f"del_{field['name']}"):
                    builder.remove_replacement(field['name'])
                    st.rerun()

        st.markdown("---")

        # --- STEP 4: Save Template ---
        st.markdown("### 4. Salvar Template")

        col1, col2 = st.columns(2)

        with col1:
            template_name = st.text_input(
                "Nome do Template",
                placeholder="Ex: Contrato de Locação",
                key='template_name'
            )

        with col2:
            template_desc = st.text_input(
                "Descrição",
                placeholder="Breve descrição do template",
                key='template_desc'
            )

        template_tags = st.text_input(
            "Tags (separadas por vírgula)",
            placeholder="Ex: contrato, locacao, imobiliario",
            key='template_tags'
        )

        if st.button("💾 Salvar Template", type="primary", use_container_width=True):
            if not template_name:
                st.error("Informe o nome do template")
            elif not fields:
                st.error("Adicione pelo menos um campo ao template")
            else:
                tags = [t.strip() for t in template_tags.split(',') if t.strip()]
                result = builder.save_template(
                    output_dir=TEMPLATES_DIR,
                    template_name=template_name,
                    description=template_desc,
                    tags=tags
                )

                if result['success']:
                    st.success(f"✅ Template salvo com {result['fields_count']} campos!")
                    st.balloons()
                    # Reset builder
                    st.session_state.template_builder = None
                    st.session_state.detected_patterns = []
                else:
                    st.error(f"Erro ao salvar: {result.get('error')}")


def render_template_gallery_tab():
    """Render template gallery UI."""
    st.subheader("Galeria de Templates")
    st.caption("Templates salvos prontos para uso")

    manager = _TemplateManager(TEMPLATES_DIR)
    templates = manager.list_templates()

    if not templates:
        st.info("Nenhum template salvo. Use a aba 'Criar Template' para criar seu primeiro template.")
    else:
        # Stats
        stats = manager.get_stats()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Templates", stats['total_templates'])
        col2.metric("Total de Campos", stats['total_fields'])
        col3.metric("Tags", len(stats['tags']))

        st.markdown("---")

        # Search
        search_query = st.text_input("🔍 Buscar templates", placeholder="Nome, descrição ou tag...")

        if search_query:
            templates = manager.search(search_query)

        # Display templates
        for template in templates:
            with st.expander(f"📄 {template['name']}", expanded=False):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**Descrição:** {template.get('description', 'N/A')}")
                    st.markdown(f"**Tags:** {', '.join(template.get('tags', []))}")
                    st.markdown(f"**Criado em:** {template.get('created_at', 'N/A')[:10]}")

                    # Show fields
                    st.markdown("**Campos:**")
                    for field in template.get('fields', []):
                        st.code(field['jinja'])

                with col2:
                    # Use template button
                    if st.button("📋 Usar", key=f"use_{template['safe_name']}"):
                        # Copy template path to session for Tab 1
                        st.session_state.current_template_path = template['docx_path']
                        st.success("Template carregado! Vá para 'Documento Único'")

                    # Delete button
                    if st.button("🗑️ Excluir", key=f"del_{template['safe_name']}"):
                        if manager.delete_template(template['safe_name']):
                            st.success("Template excluído")
                            st.rerun()
