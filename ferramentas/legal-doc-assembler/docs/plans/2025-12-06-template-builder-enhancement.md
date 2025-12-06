# Template Builder Enhancement - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable users to upload .docx files, preview text content, and interactively mark text blocks as Jinja2 variables for document generation.

**Architecture:** Paragraph-level text extraction using python-docx, interactive preview with marking capabilities in Streamlit, and pattern-based variable substitution. The approach works within Streamlit's constraints while providing practical functionality.

**Tech Stack:** Python 3.11, python-docx, Streamlit, Jinja2

---

## Background

The current Template Builder:
- Accepts .docx uploads and extracts existing Jinja2 variables
- Provides manual template text editing
- Maps variables to data fields

What's missing:
- Preview of the actual document text content
- Ability to mark arbitrary text as variables
- Pattern-based variable substitution

---

## Task 1: Add Text Extraction Function to Engine

**Files:**
- Modify: `src/engine.py:213-234` (add new method after get_template_variables)
- Test: `tests/test_engine.py` (add new test)

**Step 1: Write the failing test**

```python
# Add to tests/test_engine.py

def test_get_template_text_returns_paragraphs(tmp_path):
    """Test that get_template_text extracts paragraphs from docx."""
    from docx import Document
    from src.engine import DocumentEngine

    # Create a test docx
    doc = Document()
    doc.add_paragraph("First paragraph with some text.")
    doc.add_paragraph("Second paragraph with more content.")
    doc.add_paragraph("Third paragraph.")
    test_path = tmp_path / "test_template.docx"
    doc.save(test_path)

    engine = DocumentEngine()
    paragraphs = engine.get_template_text(str(test_path))

    assert len(paragraphs) == 3
    assert paragraphs[0]["text"] == "First paragraph with some text."
    assert paragraphs[1]["text"] == "Second paragraph with more content."
    assert paragraphs[2]["text"] == "Third paragraph."
    assert all("index" in p for p in paragraphs)
```

**Step 2: Run test to verify it fails**

```bash
cd /home/user/Claude-Code-Projetos/ferramentas/legal-doc-assembler
uv run pytest tests/test_engine.py::test_get_template_text_returns_paragraphs -v
```

Expected: FAIL with `AttributeError: 'DocumentEngine' object has no attribute 'get_template_text'`

**Step 3: Write minimal implementation**

Add to `src/engine.py` after `get_template_variables` method (around line 234):

```python
def get_template_text(self, template_path: str | Path) -> List[Dict[str, Any]]:
    """
    Extract text content from a template as a list of paragraphs.

    Each paragraph includes its text, index, and whether it contains
    Jinja2 variables.

    Args:
        template_path: Path to .docx template

    Returns:
        List of dicts with keys: 'index', 'text', 'has_variables'

    Example:
        [
            {'index': 0, 'text': 'Dear {{ nome }},', 'has_variables': True},
            {'index': 1, 'text': 'This is a legal document.', 'has_variables': False},
        ]
    """
    from docx import Document
    import re

    template_path = Path(template_path)

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    doc = Document(template_path)
    paragraphs = []

    jinja_pattern = re.compile(r'\{\{.*?\}\}')

    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:  # Skip empty paragraphs
            paragraphs.append({
                'index': i,
                'text': text,
                'has_variables': bool(jinja_pattern.search(text))
            })

    return paragraphs
```

**Step 4: Run test to verify it passes**

```bash
cd /home/user/Claude-Code-Projetos/ferramentas/legal-doc-assembler
uv run pytest tests/test_engine.py::test_get_template_text_returns_paragraphs -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/engine.py tests/test_engine.py
git commit -m "feat(engine): add get_template_text for paragraph extraction"
```

---

## Task 2: Add Variable Marking Function to Engine

**Files:**
- Modify: `src/engine.py` (add new method)
- Test: `tests/test_engine.py` (add new test)

**Step 1: Write the failing test**

```python
# Add to tests/test_engine.py

def test_mark_text_as_variable(tmp_path):
    """Test marking specific text as a Jinja2 variable in docx."""
    from docx import Document
    from src.engine import DocumentEngine

    # Create a test docx
    doc = Document()
    doc.add_paragraph("O cliente MARIA DA SILVA compareceu.")
    doc.add_paragraph("CPF: 12345678901")
    test_path = tmp_path / "test_mark.docx"
    doc.save(test_path)

    engine = DocumentEngine()

    # Mark "MARIA DA SILVA" as variable "nome"
    output_path = tmp_path / "marked.docx"
    result = engine.mark_text_as_variable(
        template_path=str(test_path),
        text_to_replace="MARIA DA SILVA",
        variable_name="nome",
        output_path=str(output_path)
    )

    # Verify the output contains the variable
    paragraphs = engine.get_template_text(str(output_path))
    assert "{{ nome }}" in paragraphs[0]["text"]
    assert paragraphs[0]["has_variables"] is True
```

**Step 2: Run test to verify it fails**

```bash
cd /home/user/Claude-Code-Projetos/ferramentas/legal-doc-assembler
uv run pytest tests/test_engine.py::test_mark_text_as_variable -v
```

Expected: FAIL with `AttributeError: 'DocumentEngine' object has no attribute 'mark_text_as_variable'`

**Step 3: Write minimal implementation**

Add to `src/engine.py` after `get_template_text` method:

```python
def mark_text_as_variable(
    self,
    template_path: str | Path,
    text_to_replace: str,
    variable_name: str,
    output_path: str | Path,
    filter_name: Optional[str] = None,
    replace_all: bool = True
) -> Path:
    """
    Replace specific text in template with Jinja2 variable placeholder.

    Args:
        template_path: Path to source .docx template
        text_to_replace: Exact text to find and replace
        variable_name: Name for the Jinja2 variable
        output_path: Path to save modified template
        filter_name: Optional filter to apply (nome, cpf, etc.)
        replace_all: If True, replace all occurrences; if False, only first

    Returns:
        Path to the modified template

    Example:
        engine.mark_text_as_variable(
            "template.docx",
            "MARIA DA SILVA",
            "nome",
            "marked_template.docx",
            filter_name="nome"
        )
        # Result: "MARIA DA SILVA" becomes "{{ nome|nome }}"
    """
    from docx import Document

    template_path = Path(template_path)
    output_path = Path(output_path)

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    doc = Document(template_path)

    # Build the variable placeholder
    if filter_name:
        placeholder = f"{{{{ {variable_name}|{filter_name} }}}}"
    else:
        placeholder = f"{{{{ {variable_name} }}}}"

    # Process each paragraph
    for para in doc.paragraphs:
        if text_to_replace in para.text:
            # Handle runs (formatted segments within paragraph)
            full_text = para.text
            if replace_all:
                new_text = full_text.replace(text_to_replace, placeholder)
            else:
                new_text = full_text.replace(text_to_replace, placeholder, 1)

            # Clear existing runs and add new text
            # Note: This may lose formatting - acceptable for MVP
            for run in para.runs:
                run.text = ""
            if para.runs:
                para.runs[0].text = new_text
            else:
                para.add_run(new_text)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)

    return output_path
```

**Step 4: Run test to verify it passes**

```bash
cd /home/user/Claude-Code-Projetos/ferramentas/legal-doc-assembler
uv run pytest tests/test_engine.py::test_mark_text_as_variable -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/engine.py tests/test_engine.py
git commit -m "feat(engine): add mark_text_as_variable for template building"
```

---

## Task 3: Add Pattern-Based Marking Function

**Files:**
- Modify: `src/engine.py` (add new method)
- Test: `tests/test_engine.py` (add new test)

**Step 1: Write the failing test**

```python
# Add to tests/test_engine.py

def test_find_markable_patterns():
    """Test finding common patterns (CPF, CNPJ, names) in text."""
    from src.engine import DocumentEngine

    engine = DocumentEngine()

    text = "Cliente: MARIA DA SILVA, CPF: 123.456.789-01, CNPJ: 12.345.678/0001-99"
    patterns = engine.find_markable_patterns(text)

    assert any(p["type"] == "cpf" and p["text"] == "123.456.789-01" for p in patterns)
    assert any(p["type"] == "cnpj" and p["text"] == "12.345.678/0001-99" for p in patterns)
```

**Step 2: Run test to verify it fails**

```bash
cd /home/user/Claude-Code-Projetos/ferramentas/legal-doc-assembler
uv run pytest tests/test_engine.py::test_find_markable_patterns -v
```

Expected: FAIL

**Step 3: Write minimal implementation**

Add to `src/engine.py`:

```python
def find_markable_patterns(self, text: str) -> List[Dict[str, Any]]:
    """
    Find common patterns in text that could be marked as variables.

    Detects:
        - CPF (formatted or unformatted)
        - CNPJ (formatted or unformatted)
        - CEP
        - Uppercase names (potential proper nouns)
        - Dates

    Args:
        text: Text to analyze

    Returns:
        List of dicts with: 'text', 'type', 'start', 'end', 'suggested_var'
    """
    import re

    patterns = []

    # CPF patterns (formatted and unformatted)
    cpf_pattern = re.compile(r'\b\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2}\b')
    for match in cpf_pattern.finditer(text):
        patterns.append({
            'text': match.group(),
            'type': 'cpf',
            'start': match.start(),
            'end': match.end(),
            'suggested_var': 'cpf',
            'suggested_filter': 'cpf'
        })

    # CNPJ patterns
    cnpj_pattern = re.compile(r'\b\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-.\s]?\d{2}\b')
    for match in cnpj_pattern.finditer(text):
        patterns.append({
            'text': match.group(),
            'type': 'cnpj',
            'start': match.start(),
            'end': match.end(),
            'suggested_var': 'cnpj',
            'suggested_filter': 'cnpj'
        })

    # CEP patterns
    cep_pattern = re.compile(r'\b\d{5}[-.\s]?\d{3}\b')
    for match in cep_pattern.finditer(text):
        # Exclude if already matched as CPF/CNPJ
        if not any(p['start'] <= match.start() < p['end'] for p in patterns):
            patterns.append({
                'text': match.group(),
                'type': 'cep',
                'start': match.start(),
                'end': match.end(),
                'suggested_var': 'cep',
                'suggested_filter': 'cep'
            })

    # Date patterns (DD/MM/YYYY)
    date_pattern = re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')
    for match in date_pattern.finditer(text):
        patterns.append({
            'text': match.group(),
            'type': 'date',
            'start': match.start(),
            'end': match.end(),
            'suggested_var': 'data',
            'suggested_filter': None
        })

    return patterns
```

**Step 4: Run test to verify it passes**

```bash
cd /home/user/Claude-Code-Projetos/ferramentas/legal-doc-assembler
uv run pytest tests/test_engine.py::test_find_markable_patterns -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/engine.py tests/test_engine.py
git commit -m "feat(engine): add find_markable_patterns for auto-detection"
```

---

## Task 4: Update Frontend - Add Document Preview Section

**Files:**
- Modify: `app/streamlit_app.py:451-580` (Template Builder section)

**Step 1: Understand current structure**

The current Template Builder section (lines 455-580) has:
- Upload template (.docx)
- Create template from text
- Variable mapping

We need to add a "Document Preview" section after upload that shows paragraphs.

**Step 2: Add preview functionality after upload**

Locate the Template Builder section (around line 455) and modify:

```python
elif nav_mode == "Template Builder":
    st.markdown("## Template Builder")
    st.markdown('<span class="text-muted">Upload and configure document templates with variable marking.</span>', unsafe_allow_html=True)

    # Tab-based interface
    tab_upload, tab_text, tab_preview = st.tabs(["Upload Template", "Text Editor", "Preview & Mark"])

    with tab_upload:
        st.markdown("#### Upload .docx Template")
        st.markdown('<span class="text-muted">Upload a Word document to use as template base.</span>', unsafe_allow_html=True)

        uploaded_template = st.file_uploader(
            "Choose a .docx file",
            type=["docx"],
            help="Word document - can contain existing {{ variable }} placeholders or plain text",
            key="template_upload"
        )

        if uploaded_template is not None:
            try:
                # Save to temp file for processing
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                    tmp.write(uploaded_template.read())
                    tmp_path = tmp.name

                # Store path in session
                st.session_state.template_content = tmp_path
                st.session_state.template_name = uploaded_template.name

                # Create engine and extract info
                engine = DocumentEngine()
                variables = engine.get_template_variables(tmp_path)
                paragraphs = engine.get_template_text(tmp_path)

                st.session_state.template_variables = list(variables)
                st.session_state.template_paragraphs = paragraphs

                st.success(f"Template loaded: {uploaded_template.name}")

                # Quick stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Paragraphs", len(paragraphs))
                with col2:
                    st.metric("Variables Found", len(variables))
                with col3:
                    st.metric("Markable Patterns", sum(
                        len(engine.find_markable_patterns(p['text']))
                        for p in paragraphs
                    ))

                st.info("Go to 'Preview & Mark' tab to view content and mark variables.")

            except Exception as e:
                st.error(f"Error processing template: {e}")

    with tab_text:
        # Keep existing text editor functionality
        st.markdown("#### Create Template from Text")
        st.markdown('<span class="text-muted">Write template content with Jinja2 placeholders.</span>', unsafe_allow_html=True)

        template_text = st.text_area(
            "Template Content",
            value=st.session_state.get('template_text_content', """PROCURACAO AD JUDICIA

Outorgante: {{ nome|nome }}
CPF: {{ cpf|cpf }}
Endereco: {{ endereco|endereco }}
CEP: {{ cep|cep }} - {{ cidade|nome }}/{{ estado }}

Outorgado: {{ advogado|nome }}
OAB: {{ oab|oab }}

{{ cidade|nome }}, {{ data }}

_______________________________
{{ nome|nome }}
"""),
            height=400,
            help="Use {{ variable }} or {{ variable|filter }} syntax",
            key="template_text_area"
        )

        if st.button("Use This Template", key="use_text_template"):
            st.session_state.template_text_content = template_text
            # Extract variables from text
            text_vars = set(re.findall(r'\{\{\s*(\w+)(?:\|[\w]+)?\s*\}\}', template_text))
            st.session_state.template_variables = list(text_vars)
            st.success(f"Template text saved with {len(text_vars)} variables")

    with tab_preview:
        st.markdown("#### Document Preview")

        if 'template_paragraphs' not in st.session_state or not st.session_state.template_paragraphs:
            st.info("Upload a template first to preview its content.")
        else:
            paragraphs = st.session_state.template_paragraphs

            st.markdown('<span class="text-muted">Review paragraphs and mark text as variables.</span>', unsafe_allow_html=True)

            # Initialize marked variables storage
            if 'marked_variables' not in st.session_state:
                st.session_state.marked_variables = []

            # Display paragraphs with marking options
            for i, para in enumerate(paragraphs):
                with st.expander(f"Paragraph {i+1}", expanded=i < 3):
                    # Show paragraph text
                    if para['has_variables']:
                        st.markdown(f'<span class="label label-blue">Has Variables</span>', unsafe_allow_html=True)
                    st.text(para['text'])

                    # Auto-detected patterns
                    engine = DocumentEngine()
                    patterns = engine.find_markable_patterns(para['text'])

                    if patterns:
                        st.markdown("**Detected Patterns:**")
                        for pat in patterns:
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.code(pat['text'])
                            with col2:
                                st.caption(f"Type: {pat['type']}")
                            with col3:
                                if st.button(f"Mark as {pat['suggested_var']}", key=f"mark_{i}_{pat['start']}"):
                                    st.session_state.marked_variables.append({
                                        'paragraph_index': i,
                                        'text': pat['text'],
                                        'variable': pat['suggested_var'],
                                        'filter': pat['suggested_filter']
                                    })
                                    st.rerun()

                    # Manual marking
                    st.markdown("**Manual Marking:**")
                    col_text, col_var, col_filter, col_btn = st.columns([3, 2, 2, 1])

                    with col_text:
                        text_to_mark = st.text_input(
                            "Text to mark",
                            key=f"text_mark_{i}",
                            placeholder="Enter exact text..."
                        )
                    with col_var:
                        var_name = st.text_input(
                            "Variable name",
                            key=f"var_name_{i}",
                            placeholder="e.g., nome"
                        )
                    with col_filter:
                        filter_choice = st.selectbox(
                            "Filter",
                            ["none", "nome", "endereco", "cpf", "cnpj", "cep", "oab", "texto"],
                            key=f"filter_{i}"
                        )
                    with col_btn:
                        st.write("")  # Spacing
                        st.write("")
                        if st.button("Mark", key=f"mark_manual_{i}"):
                            if text_to_mark and var_name:
                                st.session_state.marked_variables.append({
                                    'paragraph_index': i,
                                    'text': text_to_mark,
                                    'variable': var_name,
                                    'filter': filter_choice if filter_choice != "none" else None
                                })
                                st.rerun()

            # Show marked variables summary
            if st.session_state.marked_variables:
                st.markdown("---")
                st.markdown("#### Marked Variables Summary")

                for j, mark in enumerate(st.session_state.marked_variables):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.code(f'"{mark["text"]}" -> {{{{ {mark["variable"]}{"| " + mark["filter"] if mark["filter"] else ""} }}}}')
                    with col2:
                        st.caption(f"Paragraph {mark['paragraph_index'] + 1}")
                    with col3:
                        if st.button("Remove", key=f"remove_mark_{j}"):
                            st.session_state.marked_variables.pop(j)
                            st.rerun()

                # Apply markings button
                st.markdown("---")
                if st.button("Apply All Markings", type="primary"):
                    try:
                        engine = DocumentEngine()
                        current_path = st.session_state.template_content

                        # Apply each marking
                        for mark in st.session_state.marked_variables:
                            output_path = Path(tempfile.gettempdir()) / f"marked_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                            engine.mark_text_as_variable(
                                template_path=current_path,
                                text_to_replace=mark['text'],
                                variable_name=mark['variable'],
                                output_path=str(output_path),
                                filter_name=mark['filter']
                            )
                            current_path = str(output_path)

                        # Update session state
                        st.session_state.template_content = current_path
                        st.session_state.template_paragraphs = engine.get_template_text(current_path)
                        st.session_state.template_variables = list(engine.get_template_variables(current_path))
                        st.session_state.marked_variables = []

                        st.success("All markings applied! Template updated.")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error applying markings: {e}")

    # Sidebar status (keep existing)
    # ...
```

**Step 3: Test manually**

```bash
cd /home/user/Claude-Code-Projetos/ferramentas/legal-doc-assembler
uv run streamlit run app/streamlit_app.py
```

Open browser, navigate to Template Builder, upload a .docx file, verify:
- Paragraphs appear in Preview & Mark tab
- Patterns are auto-detected
- Manual marking works
- Apply markings modifies template

**Step 4: Commit**

```bash
git add app/streamlit_app.py
git commit -m "feat(ui): add interactive Template Builder with preview and marking"
```

---

## Task 5: Add Session State Initialization

**Files:**
- Modify: `app/streamlit_app.py:209-220` (session state init section)

**Step 1: Add missing session state variables**

Find the session state initialization section and add:

```python
# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------

if 'input_data' not in st.session_state:
    st.session_state.input_data = {}
if 'normalized_data' not in st.session_state:
    st.session_state.normalized_data = {}
if 'template_content' not in st.session_state:
    st.session_state.template_content = None
if 'template_variables' not in st.session_state:
    st.session_state.template_variables = []
if 'assembled_doc' not in st.session_state:
    st.session_state.assembled_doc = None
# NEW: Template builder state
if 'template_paragraphs' not in st.session_state:
    st.session_state.template_paragraphs = []
if 'template_name' not in st.session_state:
    st.session_state.template_name = None
if 'marked_variables' not in st.session_state:
    st.session_state.marked_variables = []
if 'template_text_content' not in st.session_state:
    st.session_state.template_text_content = None
```

**Step 2: Commit**

```bash
git add app/streamlit_app.py
git commit -m "feat(ui): add session state for template builder"
```

---

## Task 6: Add Download Modified Template

**Files:**
- Modify: `app/streamlit_app.py` (Template Builder section, after Apply Markings)

**Step 1: Add download button**

After the "Apply All Markings" success message, add:

```python
# Download modified template
if st.session_state.template_content and Path(st.session_state.template_content).exists():
    st.markdown("---")
    st.markdown("#### Download Modified Template")

    with open(st.session_state.template_content, "rb") as f:
        st.download_button(
            label="Download Template with Variables",
            data=f.read(),
            file_name=f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary"
        )
```

**Step 2: Commit**

```bash
git add app/streamlit_app.py
git commit -m "feat(ui): add download button for modified template"
```

---

## Task 7: Run Full Test Suite

**Step 1: Run all tests**

```bash
cd /home/user/Claude-Code-Projetos/ferramentas/legal-doc-assembler
uv run pytest -v
```

Expected: All tests pass

**Step 2: Manual integration test**

1. Start app: `uv run streamlit run app/streamlit_app.py`
2. Upload a plain .docx document (no Jinja2 variables)
3. Go to Preview & Mark tab
4. Verify paragraphs are displayed
5. Test auto-detection (add a CPF like "123.456.789-01" in document)
6. Mark a piece of text manually
7. Apply markings
8. Verify template variables are updated
9. Go to Assembler, verify new variables appear
10. Load JSON data and assemble document

**Step 3: Final commit**

```bash
git add -A
git commit -m "test: verify template builder integration"
```

---

## Summary

| Task | Description | Files | Status |
|------|-------------|-------|--------|
| 1 | Text extraction function | engine.py, test_engine.py | Pending |
| 2 | Variable marking function | engine.py, test_engine.py | Pending |
| 3 | Pattern detection function | engine.py, test_engine.py | Pending |
| 4 | Frontend preview section | streamlit_app.py | Pending |
| 5 | Session state init | streamlit_app.py | Pending |
| 6 | Download button | streamlit_app.py | Pending |
| 7 | Integration testing | - | Pending |

---

## Execution Notes

- TDD approach: write test first, then implementation
- Each task is independent and can be committed separately
- Frontend changes (Tasks 4-6) depend on backend (Tasks 1-3)
- Manual testing required after Task 4 for UI verification
