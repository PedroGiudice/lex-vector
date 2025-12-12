# Doc-Assembler Template Creator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add template CREATION functionality to the Doc-Assembler module, allowing users to upload a plain DOCX, select text blocks to transform into Jinja2 fields, detect patterns automatically, and save reusable templates.

**Architecture:** New Tab "Criar Template" in `modules/doc_assembler.py` with 4 sub-sections: (1) Upload & Preview, (2) Pattern Detection, (3) Manual Selection, (4) Save Template. Backend uses `python-docx` for DOCX parsing and manipulation, storing templates in `ferramentas/legal-doc-assembler/templates/` with JSON metadata.

**Tech Stack:** Python 3.12, Streamlit, python-docx, docxtpl, regex patterns from existing normalizers.py

---

## Current State

| Component | Location | Lines |
|-----------|----------|-------|
| Frontend | `legal-workbench/modules/doc_assembler.py` | 856 |
| Engine | `ferramentas/legal-doc-assembler/src/engine.py` | 392 |
| Normalizers | `ferramentas/legal-doc-assembler/src/normalizers.py` | 589 |
| Templates Dir | `ferramentas/legal-doc-assembler/templates/` | Empty |

---

## Task 1: Create DOCX Parser Utility

**Files:**
- Create: `legal-workbench/ferramentas/legal-doc-assembler/src/docx_parser.py`
- Test: `legal-workbench/ferramentas/legal-doc-assembler/tests/test_docx_parser.py`

**Step 1: Write failing test for paragraph extraction**

```python
# tests/test_docx_parser.py
import pytest
from pathlib import Path
from src.docx_parser import DocxParser

def test_extract_paragraphs_returns_list():
    """Parser should extract all paragraphs from a DOCX file."""
    # Create a temp DOCX for testing
    from docx import Document
    import tempfile

    doc = Document()
    doc.add_paragraph("First paragraph")
    doc.add_paragraph("Second paragraph")

    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        doc.save(f.name)

        parser = DocxParser(f.name)
        paragraphs = parser.extract_paragraphs()

        assert isinstance(paragraphs, list)
        assert len(paragraphs) == 2
        assert paragraphs[0]['text'] == "First paragraph"
        assert paragraphs[1]['text'] == "Second paragraph"
```

**Step 2: Run test to verify it fails**

Run: `cd legal-workbench/ferramentas/legal-doc-assembler && pytest tests/test_docx_parser.py::test_extract_paragraphs_returns_list -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.docx_parser'"

**Step 3: Write minimal implementation**

```python
# src/docx_parser.py
"""
DOCX Parser for Template Creation.

Extracts structured content from DOCX files for preview and field detection.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
import re


@dataclass
class ParsedParagraph:
    """Represents a parsed paragraph with metadata."""
    index: int
    text: str
    style: str
    runs: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'index': self.index,
            'text': self.text,
            'style': self.style,
            'runs': self.runs
        }


class DocxParser:
    """
    Parser for extracting structured content from DOCX files.

    Used in Template Creator to:
    1. Extract paragraphs with metadata
    2. Extract tables with cell content
    3. Preserve formatting information for preview
    """

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"DOCX file not found: {file_path}")
        self.document = Document(str(self.file_path))

    def extract_paragraphs(self) -> List[Dict[str, Any]]:
        """
        Extract all paragraphs with text and metadata.

        Returns:
            List of dicts with keys: index, text, style, runs
        """
        paragraphs = []
        for idx, para in enumerate(self.document.paragraphs):
            if para.text.strip():  # Skip empty paragraphs
                parsed = ParsedParagraph(
                    index=idx,
                    text=para.text,
                    style=para.style.name if para.style else "Normal",
                    runs=[{
                        'text': run.text,
                        'bold': run.bold,
                        'italic': run.italic
                    } for run in para.runs]
                )
                paragraphs.append(parsed.to_dict())
        return paragraphs

    def extract_tables(self) -> List[Dict[str, Any]]:
        """
        Extract all tables with cell content.

        Returns:
            List of dicts with table data (rows x cols)
        """
        tables = []
        for idx, table in enumerate(self.document.tables):
            table_data = {
                'index': idx,
                'rows': len(table.rows),
                'cols': len(table.columns) if table.rows else 0,
                'cells': []
            }
            for row_idx, row in enumerate(table.rows):
                for col_idx, cell in enumerate(row.cells):
                    table_data['cells'].append({
                        'row': row_idx,
                        'col': col_idx,
                        'text': cell.text
                    })
            tables.append(table_data)
        return tables

    def get_full_text(self) -> str:
        """Return all text concatenated for preview."""
        texts = [p.text for p in self.document.paragraphs if p.text.strip()]
        return '\n\n'.join(texts)

    def get_structure_summary(self) -> Dict[str, int]:
        """Return counts of document elements."""
        return {
            'paragraphs': len([p for p in self.document.paragraphs if p.text.strip()]),
            'tables': len(self.document.tables),
            'sections': len(self.document.sections)
        }
```

**Step 4: Run test to verify it passes**

Run: `cd legal-workbench/ferramentas/legal-doc-assembler && pytest tests/test_docx_parser.py::test_extract_paragraphs_returns_list -v`
Expected: PASS

**Step 5: Commit**

```bash
git add legal-workbench/ferramentas/legal-doc-assembler/src/docx_parser.py
git add legal-workbench/ferramentas/legal-doc-assembler/tests/test_docx_parser.py
git commit -m "feat(doc-assembler): add DocxParser for template creation"
```

---

## Task 2: Create Pattern Detector

**Files:**
- Create: `legal-workbench/ferramentas/legal-doc-assembler/src/pattern_detector.py`
- Test: `legal-workbench/ferramentas/legal-doc-assembler/tests/test_pattern_detector.py`

**Step 1: Write failing test for CPF detection**

```python
# tests/test_pattern_detector.py
import pytest
from src.pattern_detector import PatternDetector

def test_detect_cpf_formatted():
    """Detector should find formatted CPF patterns."""
    text = "O cliente João, CPF 123.456.789-01, solicita..."
    detector = PatternDetector()
    matches = detector.detect_all(text)

    assert len(matches) >= 1
    cpf_match = next((m for m in matches if m['type'] == 'cpf'), None)
    assert cpf_match is not None
    assert cpf_match['value'] == '123.456.789-01'
    assert cpf_match['start'] == 21
    assert cpf_match['end'] == 35

def test_detect_cpf_unformatted():
    """Detector should find unformatted CPF patterns."""
    text = "CPF: 12345678901"
    detector = PatternDetector()
    matches = detector.detect_all(text)

    cpf_match = next((m for m in matches if m['type'] == 'cpf'), None)
    assert cpf_match is not None
    assert cpf_match['value'] == '12345678901'

def test_detect_cnpj():
    """Detector should find CNPJ patterns."""
    text = "Empresa XPTO, CNPJ 12.345.678/0001-99"
    detector = PatternDetector()
    matches = detector.detect_all(text)

    cnpj_match = next((m for m in matches if m['type'] == 'cnpj'), None)
    assert cnpj_match is not None

def test_detect_oab():
    """Detector should find OAB patterns."""
    text = "Advogado inscrito na OAB/SP 123.456"
    detector = PatternDetector()
    matches = detector.detect_all(text)

    oab_match = next((m for m in matches if m['type'] == 'oab'), None)
    assert oab_match is not None

def test_detect_currency():
    """Detector should find Brazilian currency values."""
    text = "O valor de R$ 1.234,56 será pago"
    detector = PatternDetector()
    matches = detector.detect_all(text)

    currency_match = next((m for m in matches if m['type'] == 'valor'), None)
    assert currency_match is not None
    assert 'R$' in currency_match['value'] or '1.234,56' in currency_match['value']

def test_detect_cep():
    """Detector should find CEP patterns."""
    text = "CEP 01310-100, São Paulo"
    detector = PatternDetector()
    matches = detector.detect_all(text)

    cep_match = next((m for m in matches if m['type'] == 'cep'), None)
    assert cep_match is not None

def test_suggest_field_name():
    """Detector should suggest appropriate Jinja2 field names."""
    detector = PatternDetector()

    assert detector.suggest_field_name('cpf', '123.456.789-01') == 'cpf'
    assert detector.suggest_field_name('cnpj', '12.345.678/0001-99') == 'cnpj'
    assert detector.suggest_field_name('valor', 'R$ 1.234,56') == 'valor'
```

**Step 2: Run test to verify it fails**

Run: `cd legal-workbench/ferramentas/legal-doc-assembler && pytest tests/test_pattern_detector.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.pattern_detector'"

**Step 3: Write minimal implementation**

```python
# src/pattern_detector.py
"""
Pattern Detector for Template Creation.

Automatically detects Brazilian legal patterns (CPF, CNPJ, OAB, CEP, currency)
in text and suggests Jinja2 field replacements.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PatternMatch:
    """Represents a detected pattern match."""
    type: str
    value: str
    start: int
    end: int
    suggested_field: str
    filter: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'value': self.value,
            'start': self.start,
            'end': self.end,
            'suggested_field': self.suggested_field,
            'filter': self.filter
        }


class PatternDetector:
    """
    Detects Brazilian legal document patterns in text.

    Supported patterns:
    - CPF (formatted and unformatted)
    - CNPJ (formatted and unformatted)
    - OAB registration numbers
    - CEP (postal codes)
    - Currency values (R$)
    - Dates (DD/MM/YYYY)
    - Phone numbers
    """

    # Pattern definitions with corresponding Jinja2 filters
    PATTERNS = {
        'cpf': {
            'regex': r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}',
            'filter': 'cpf',
            'description': 'CPF (Cadastro de Pessoa Física)'
        },
        'cnpj': {
            'regex': r'\d{2}\.?\d{3}\.?\d{3}/?\.?\d{4}-?\d{2}',
            'filter': 'cnpj',
            'description': 'CNPJ (Cadastro Nacional de Pessoa Jurídica)'
        },
        'oab': {
            'regex': r'(?:OAB/?)?([A-Z]{2})\s*\.?\s*(\d{1,6}\.?\d{0,3})|(\d{1,6}\.?\d{0,3})\s*/?([A-Z]{2})',
            'filter': 'oab',
            'description': 'Registro OAB'
        },
        'cep': {
            'regex': r'\d{5}-?\d{3}',
            'filter': 'cep',
            'description': 'CEP (Código de Endereçamento Postal)'
        },
        'valor': {
            'regex': r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}',
            'filter': 'valor',
            'description': 'Valor monetário'
        },
        'data': {
            'regex': r'\d{2}/\d{2}/\d{4}',
            'filter': 'data',
            'description': 'Data (DD/MM/YYYY)'
        },
        'telefone': {
            'regex': r'\(?\d{2}\)?\s*\d{4,5}-?\d{4}',
            'filter': 'telefone',
            'description': 'Telefone'
        }
    }

    def __init__(self, patterns: Optional[Dict] = None):
        """
        Initialize detector with optional custom patterns.

        Args:
            patterns: Dict of pattern definitions to override/extend defaults
        """
        self.patterns = {**self.PATTERNS}
        if patterns:
            self.patterns.update(patterns)

    def detect_pattern(self, text: str, pattern_type: str) -> List[PatternMatch]:
        """
        Detect all occurrences of a specific pattern type.

        Args:
            text: Text to search
            pattern_type: Type of pattern to detect (e.g., 'cpf', 'cnpj')

        Returns:
            List of PatternMatch objects
        """
        if pattern_type not in self.patterns:
            raise ValueError(f"Unknown pattern type: {pattern_type}")

        pattern_def = self.patterns[pattern_type]
        regex = pattern_def['regex']
        matches = []

        for match in re.finditer(regex, text, re.IGNORECASE):
            matches.append(PatternMatch(
                type=pattern_type,
                value=match.group(0),
                start=match.start(),
                end=match.end(),
                suggested_field=self.suggest_field_name(pattern_type, match.group(0)),
                filter=pattern_def['filter']
            ))

        return matches

    def detect_all(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect all supported patterns in text.

        Args:
            text: Text to search

        Returns:
            List of match dicts sorted by position
        """
        all_matches = []

        for pattern_type in self.patterns:
            matches = self.detect_pattern(text, pattern_type)
            all_matches.extend([m.to_dict() for m in matches])

        # Sort by start position
        all_matches.sort(key=lambda x: x['start'])

        # Remove overlapping matches (keep first/longer)
        filtered = []
        last_end = -1
        for match in all_matches:
            if match['start'] >= last_end:
                filtered.append(match)
                last_end = match['end']

        return filtered

    def suggest_field_name(self, pattern_type: str, value: str) -> str:
        """
        Suggest a Jinja2 field name for a detected pattern.

        Args:
            pattern_type: Type of pattern
            value: Matched value

        Returns:
            Suggested field name (e.g., 'cpf', 'cnpj_empresa')
        """
        # Base field name is the pattern type
        return pattern_type

    def get_jinja_replacement(self, match: Dict[str, Any]) -> str:
        """
        Get Jinja2 replacement string for a match.

        Args:
            match: Match dict from detect_all()

        Returns:
            Jinja2 variable string (e.g., '{{ cpf | cpf }}')
        """
        field = match['suggested_field']
        filter_name = match['filter']
        return f"{{{{ {field} | {filter_name} }}}}"

    def apply_detections(self, text: str, matches: List[Dict[str, Any]]) -> str:
        """
        Replace detected patterns with Jinja2 variables.

        Args:
            text: Original text
            matches: List of matches to replace

        Returns:
            Text with patterns replaced by Jinja2 variables
        """
        # Sort matches by position (reverse order for safe replacement)
        sorted_matches = sorted(matches, key=lambda x: x['start'], reverse=True)

        result = text
        for match in sorted_matches:
            replacement = self.get_jinja_replacement(match)
            result = result[:match['start']] + replacement + result[match['end']:]

        return result
```

**Step 4: Run test to verify it passes**

Run: `cd legal-workbench/ferramentas/legal-doc-assembler && pytest tests/test_pattern_detector.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add legal-workbench/ferramentas/legal-doc-assembler/src/pattern_detector.py
git add legal-workbench/ferramentas/legal-doc-assembler/tests/test_pattern_detector.py
git commit -m "feat(doc-assembler): add PatternDetector for automatic field detection"
```

---

## Task 3: Create Template Builder Class

**Files:**
- Create: `legal-workbench/ferramentas/legal-doc-assembler/src/template_builder.py`
- Test: `legal-workbench/ferramentas/legal-doc-assembler/tests/test_template_builder.py`

**Step 1: Write failing test for template creation**

```python
# tests/test_template_builder.py
import pytest
import tempfile
import json
from pathlib import Path
from docx import Document
from src.template_builder import TemplateBuilder

@pytest.fixture
def sample_docx():
    """Create a sample DOCX for testing."""
    doc = Document()
    doc.add_paragraph("Cliente: João da Silva")
    doc.add_paragraph("CPF: 123.456.789-01")
    doc.add_paragraph("Valor: R$ 1.234,56")

    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        doc.save(f.name)
        yield f.name
    Path(f.name).unlink(missing_ok=True)

@pytest.fixture
def templates_dir():
    """Create temp templates directory."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

def test_builder_loads_docx(sample_docx):
    """Builder should load and parse DOCX file."""
    builder = TemplateBuilder(sample_docx)
    assert builder.get_full_text() is not None
    assert "João da Silva" in builder.get_full_text()

def test_builder_detects_patterns(sample_docx):
    """Builder should detect patterns automatically."""
    builder = TemplateBuilder(sample_docx)
    detections = builder.detect_patterns()

    assert len(detections) >= 2  # CPF and valor
    types = [d['type'] for d in detections]
    assert 'cpf' in types
    assert 'valor' in types

def test_builder_replaces_selection(sample_docx):
    """Builder should replace selected text with Jinja2 variable."""
    builder = TemplateBuilder(sample_docx)

    # Replace "João da Silva" with {{ nome }}
    builder.add_field_replacement(
        text="João da Silva",
        field_name="nome",
        filter_name="nome"
    )

    result = builder.get_modified_text()
    assert "{{ nome | nome }}" in result
    assert "João da Silva" not in result

def test_builder_saves_template(sample_docx, templates_dir):
    """Builder should save template DOCX and metadata JSON."""
    builder = TemplateBuilder(sample_docx)
    builder.add_field_replacement("João da Silva", "nome", "nome")
    builder.add_field_replacement("123.456.789-01", "cpf", "cpf")

    result = builder.save_template(
        output_dir=templates_dir,
        template_name="contrato_teste",
        description="Template de teste"
    )

    assert result['success'] is True
    assert (templates_dir / "contrato_teste.docx").exists()
    assert (templates_dir / "contrato_teste.json").exists()

    # Check metadata
    with open(templates_dir / "contrato_teste.json") as f:
        meta = json.load(f)
    assert meta['name'] == "contrato_teste"
    assert len(meta['fields']) == 2
    assert 'nome' in [f['name'] for f in meta['fields']]
```

**Step 2: Run test to verify it fails**

Run: `cd legal-workbench/ferramentas/legal-doc-assembler && pytest tests/test_template_builder.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.template_builder'"

**Step 3: Write minimal implementation**

```python
# src/template_builder.py
"""
Template Builder for creating Jinja2 DOCX templates.

Workflow:
1. Load source DOCX
2. Preview content
3. Detect patterns automatically OR select text manually
4. Replace text with Jinja2 variables
5. Save template + metadata
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from docx import Document

from .docx_parser import DocxParser
from .pattern_detector import PatternDetector


@dataclass
class FieldReplacement:
    """Represents a text-to-field replacement."""
    original_text: str
    field_name: str
    filter_name: str
    jinja_template: str = ""

    def __post_init__(self):
        if self.filter_name:
            self.jinja_template = f"{{{{ {self.field_name} | {self.filter_name} }}}}"
        else:
            self.jinja_template = f"{{{{ {self.field_name} }}}}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.field_name,
            'filter': self.filter_name,
            'original_sample': self.original_text[:50],
            'jinja': self.jinja_template
        }


class TemplateBuilder:
    """
    Builder for creating Jinja2 DOCX templates from plain documents.

    Features:
    - Load and preview DOCX content
    - Automatic pattern detection (CPF, CNPJ, etc.)
    - Manual text selection for field creation
    - Save template with metadata
    """

    def __init__(self, source_path: str | Path):
        """
        Initialize builder with source DOCX.

        Args:
            source_path: Path to source DOCX file
        """
        self.source_path = Path(source_path)
        self.parser = DocxParser(source_path)
        self.detector = PatternDetector()
        self.document = Document(str(source_path))

        # Track replacements
        self.replacements: List[FieldReplacement] = []

        # Cache original text
        self._original_text = self.parser.get_full_text()
        self._modified_text = self._original_text

    def get_full_text(self) -> str:
        """Get full document text for preview."""
        return self._original_text

    def get_modified_text(self) -> str:
        """Get text with current replacements applied."""
        return self._modified_text

    def get_paragraphs(self) -> List[Dict[str, Any]]:
        """Get structured paragraphs for UI display."""
        return self.parser.extract_paragraphs()

    def get_structure(self) -> Dict[str, int]:
        """Get document structure summary."""
        return self.parser.get_structure_summary()

    def detect_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect all patterns in document.

        Returns:
            List of detected patterns with positions and suggested fields
        """
        return self.detector.detect_all(self._original_text)

    def add_field_replacement(
        self,
        text: str,
        field_name: str,
        filter_name: str = ""
    ) -> bool:
        """
        Add a text-to-field replacement.

        Args:
            text: Original text to replace
            field_name: Jinja2 field name
            filter_name: Optional filter (e.g., 'cpf', 'nome')

        Returns:
            True if replacement was added successfully
        """
        if text not in self._modified_text:
            return False

        replacement = FieldReplacement(
            original_text=text,
            field_name=field_name,
            filter_name=filter_name
        )

        # Apply replacement to modified text
        self._modified_text = self._modified_text.replace(
            text,
            replacement.jinja_template
        )

        self.replacements.append(replacement)
        return True

    def apply_detected_pattern(self, match: Dict[str, Any]) -> bool:
        """
        Apply a detected pattern as a field replacement.

        Args:
            match: Pattern match dict from detect_patterns()

        Returns:
            True if applied successfully
        """
        return self.add_field_replacement(
            text=match['value'],
            field_name=match['suggested_field'],
            filter_name=match['filter']
        )

    def remove_replacement(self, field_name: str) -> bool:
        """
        Remove a replacement by field name.

        Args:
            field_name: Name of field to remove

        Returns:
            True if removed successfully
        """
        for i, r in enumerate(self.replacements):
            if r.field_name == field_name:
                # Restore original text
                self._modified_text = self._modified_text.replace(
                    r.jinja_template,
                    r.original_text
                )
                self.replacements.pop(i)
                return True
        return False

    def reset(self) -> None:
        """Reset all replacements."""
        self.replacements = []
        self._modified_text = self._original_text

    def get_fields(self) -> List[Dict[str, Any]]:
        """Get list of current fields."""
        return [r.to_dict() for r in self.replacements]

    def save_template(
        self,
        output_dir: str | Path,
        template_name: str,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Save template DOCX and metadata JSON.

        Args:
            output_dir: Directory to save template
            template_name: Name for template (used as filename)
            description: Template description
            tags: Optional tags for categorization

        Returns:
            Dict with success status and file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize template name
        safe_name = re.sub(r'[^\w\-]', '_', template_name.lower())

        docx_path = output_dir / f"{safe_name}.docx"
        meta_path = output_dir / f"{safe_name}.json"

        try:
            # Apply replacements to document
            self._apply_replacements_to_document()

            # Save DOCX
            self.document.save(str(docx_path))

            # Create metadata
            metadata = {
                'name': template_name,
                'safe_name': safe_name,
                'description': description,
                'tags': tags or [],
                'fields': self.get_fields(),
                'created_at': datetime.now().isoformat(),
                'source_file': self.source_path.name,
                'structure': self.get_structure()
            }

            # Save metadata
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            return {
                'success': True,
                'docx_path': str(docx_path),
                'meta_path': str(meta_path),
                'fields_count': len(self.replacements)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _apply_replacements_to_document(self) -> None:
        """Apply all replacements to the actual DOCX document."""
        for para in self.document.paragraphs:
            for replacement in self.replacements:
                if replacement.original_text in para.text:
                    # Replace in each run
                    for run in para.runs:
                        if replacement.original_text in run.text:
                            run.text = run.text.replace(
                                replacement.original_text,
                                replacement.jinja_template
                            )
                    # Handle text split across runs
                    if replacement.original_text in para.text:
                        full_text = para.text.replace(
                            replacement.original_text,
                            replacement.jinja_template
                        )
                        # Clear existing runs and add new
                        for run in para.runs:
                            run.text = ""
                        if para.runs:
                            para.runs[0].text = full_text
```

**Step 4: Run test to verify it passes**

Run: `cd legal-workbench/ferramentas/legal-doc-assembler && pytest tests/test_template_builder.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add legal-workbench/ferramentas/legal-doc-assembler/src/template_builder.py
git add legal-workbench/ferramentas/legal-doc-assembler/tests/test_template_builder.py
git commit -m "feat(doc-assembler): add TemplateBuilder for template creation workflow"
```

---

## Task 4: Create Template Manager

**Files:**
- Create: `legal-workbench/ferramentas/legal-doc-assembler/src/template_manager.py`
- Test: `legal-workbench/ferramentas/legal-doc-assembler/tests/test_template_manager.py`

**Step 1: Write failing test for template listing**

```python
# tests/test_template_manager.py
import pytest
import tempfile
import json
from pathlib import Path
from src.template_manager import TemplateManager

@pytest.fixture
def templates_dir():
    """Create temp templates directory with sample templates."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)

        # Create sample template metadata
        meta1 = {
            'name': 'Contrato de Locação',
            'safe_name': 'contrato_locacao',
            'description': 'Template para contratos de locação',
            'tags': ['contrato', 'locacao'],
            'fields': [
                {'name': 'nome', 'filter': 'nome'},
                {'name': 'cpf', 'filter': 'cpf'}
            ],
            'created_at': '2025-01-10T10:00:00'
        }

        meta2 = {
            'name': 'Procuração',
            'safe_name': 'procuracao',
            'description': 'Procuração ad judicia',
            'tags': ['procuracao'],
            'fields': [
                {'name': 'outorgante', 'filter': 'nome'},
                {'name': 'oab', 'filter': 'oab'}
            ],
            'created_at': '2025-01-11T10:00:00'
        }

        # Save metadata files
        (d / 'contrato_locacao.json').write_text(json.dumps(meta1, ensure_ascii=False))
        (d / 'contrato_locacao.docx').write_bytes(b'')  # Dummy file

        (d / 'procuracao.json').write_text(json.dumps(meta2, ensure_ascii=False))
        (d / 'procuracao.docx').write_bytes(b'')

        yield d

def test_list_templates(templates_dir):
    """Manager should list all available templates."""
    manager = TemplateManager(templates_dir)
    templates = manager.list_templates()

    assert len(templates) == 2
    names = [t['name'] for t in templates]
    assert 'Contrato de Locação' in names
    assert 'Procuração' in names

def test_get_template(templates_dir):
    """Manager should retrieve template details."""
    manager = TemplateManager(templates_dir)
    template = manager.get_template('contrato_locacao')

    assert template is not None
    assert template['name'] == 'Contrato de Locação'
    assert len(template['fields']) == 2

def test_search_templates(templates_dir):
    """Manager should search templates by query."""
    manager = TemplateManager(templates_dir)

    results = manager.search('contrato')
    assert len(results) == 1
    assert results[0]['safe_name'] == 'contrato_locacao'

    results = manager.search('locacao')
    assert len(results) == 1

def test_delete_template(templates_dir):
    """Manager should delete template and metadata."""
    manager = TemplateManager(templates_dir)

    result = manager.delete_template('contrato_locacao')
    assert result is True

    templates = manager.list_templates()
    assert len(templates) == 1
    assert templates[0]['safe_name'] == 'procuracao'
```

**Step 2: Run test to verify it fails**

Run: `cd legal-workbench/ferramentas/legal-doc-assembler && pytest tests/test_template_manager.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/template_manager.py
"""
Template Manager for listing, searching, and managing saved templates.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class TemplateManager:
    """
    Manages saved templates in a directory.

    Templates consist of:
    - {name}.docx: The template file with Jinja2 variables
    - {name}.json: Metadata (fields, description, tags, etc.)
    """

    def __init__(self, templates_dir: str | Path):
        """
        Initialize manager with templates directory.

        Args:
            templates_dir: Directory containing templates
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates.

        Returns:
            List of template metadata dicts, sorted by creation date (newest first)
        """
        templates = []

        for meta_path in self.templates_dir.glob('*.json'):
            try:
                with open(meta_path, encoding='utf-8') as f:
                    meta = json.load(f)

                # Check if DOCX exists
                docx_path = meta_path.with_suffix('.docx')
                if docx_path.exists():
                    meta['docx_path'] = str(docx_path)
                    meta['meta_path'] = str(meta_path)
                    templates.append(meta)

            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by creation date (newest first)
        templates.sort(
            key=lambda t: t.get('created_at', ''),
            reverse=True
        )

        return templates

    def get_template(self, safe_name: str) -> Optional[Dict[str, Any]]:
        """
        Get template details by safe name.

        Args:
            safe_name: Template's safe name (filename without extension)

        Returns:
            Template metadata dict or None if not found
        """
        meta_path = self.templates_dir / f"{safe_name}.json"
        docx_path = self.templates_dir / f"{safe_name}.docx"

        if not meta_path.exists() or not docx_path.exists():
            return None

        try:
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
            meta['docx_path'] = str(docx_path)
            meta['meta_path'] = str(meta_path)
            return meta
        except (json.JSONDecodeError, KeyError):
            return None

    def search(
        self,
        query: str,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search templates by name, description, or tags.

        Args:
            query: Search query (case-insensitive)
            tags: Optional list of tags to filter by

        Returns:
            List of matching template metadata dicts
        """
        query_lower = query.lower()
        results = []

        for template in self.list_templates():
            # Search in name and description
            name_match = query_lower in template.get('name', '').lower()
            desc_match = query_lower in template.get('description', '').lower()
            tag_match = any(
                query_lower in tag.lower()
                for tag in template.get('tags', [])
            )

            if name_match or desc_match or tag_match:
                # Additional tag filter if specified
                if tags:
                    template_tags = set(template.get('tags', []))
                    if not set(tags).intersection(template_tags):
                        continue
                results.append(template)

        return results

    def delete_template(self, safe_name: str) -> bool:
        """
        Delete a template and its metadata.

        Args:
            safe_name: Template's safe name

        Returns:
            True if deleted successfully
        """
        meta_path = self.templates_dir / f"{safe_name}.json"
        docx_path = self.templates_dir / f"{safe_name}.docx"

        deleted = False

        if meta_path.exists():
            meta_path.unlink()
            deleted = True

        if docx_path.exists():
            docx_path.unlink()
            deleted = True

        return deleted

    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags from all templates.

        Returns:
            Sorted list of unique tags
        """
        tags = set()
        for template in self.list_templates():
            tags.update(template.get('tags', []))
        return sorted(tags)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about saved templates.

        Returns:
            Dict with counts and stats
        """
        templates = self.list_templates()

        total_fields = sum(
            len(t.get('fields', []))
            for t in templates
        )

        return {
            'total_templates': len(templates),
            'total_fields': total_fields,
            'tags': self.get_all_tags(),
            'most_recent': templates[0]['name'] if templates else None
        }
```

**Step 4: Run test to verify it passes**

Run: `cd legal-workbench/ferramentas/legal-doc-assembler && pytest tests/test_template_manager.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add legal-workbench/ferramentas/legal-doc-assembler/src/template_manager.py
git add legal-workbench/ferramentas/legal-doc-assembler/tests/test_template_manager.py
git commit -m "feat(doc-assembler): add TemplateManager for template storage"
```

---

## Task 5: Update __init__.py exports

**Files:**
- Modify: `legal-workbench/ferramentas/legal-doc-assembler/src/__init__.py`

**Step 1: Update exports**

```python
# src/__init__.py
"""
Legal Doc Assembler - Document assembly engine with Jinja2 templates.

Exports:
- DocumentEngine: Core rendering engine
- BatchProcessor: Parallel batch processing
- DocxParser: DOCX content extraction
- PatternDetector: Automatic pattern detection
- TemplateBuilder: Create templates from plain DOCX
- TemplateManager: Manage saved templates
- Normalizers: Brazilian legal document normalization
"""

from .engine import DocumentEngine
from .batch_engine import BatchProcessor
from .docx_parser import DocxParser
from .pattern_detector import PatternDetector
from .template_builder import TemplateBuilder
from .template_manager import TemplateManager
from .normalizers import (
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

__all__ = [
    'DocumentEngine',
    'BatchProcessor',
    'DocxParser',
    'PatternDetector',
    'TemplateBuilder',
    'TemplateManager',
    'normalize_whitespace',
    'normalize_name',
    'normalize_address',
    'format_cpf',
    'format_cnpj',
    'format_cep',
    'format_oab',
    'normalize_punctuation',
    'normalize_all',
]
```

**Step 2: Verify imports work**

Run: `cd legal-workbench/ferramentas/legal-doc-assembler && python -c "from src import TemplateBuilder, PatternDetector, TemplateManager; print('OK')"`
Expected: "OK"

**Step 3: Commit**

```bash
git add legal-workbench/ferramentas/legal-doc-assembler/src/__init__.py
git commit -m "feat(doc-assembler): export new template creation classes"
```

---

## Task 6: Add "Criar Template" Tab to Frontend

**Files:**
- Modify: `legal-workbench/modules/doc_assembler.py` (add new tab after line ~856)

**Step 1: Add imports at top of file**

Add after existing imports (around line 15):

```python
# Add these imports
from src.template_builder import TemplateBuilder
from src.template_manager import TemplateManager
from src.pattern_detector import PatternDetector

# Templates directory path
TEMPLATES_DIR = Path(__file__).parent.parent / "ferramentas" / "legal-doc-assembler" / "templates"
```

**Step 2: Modify tabs structure**

Change the tabs line (around line 50) from:

```python
tab1, tab2 = st.tabs(["📄 Documento Único", "📦 Processamento em Lote"])
```

To:

```python
tab1, tab2, tab3, tab4 = st.tabs([
    "📄 Documento Único",
    "📦 Processamento em Lote",
    "🔧 Criar Template",
    "📚 Galeria de Templates"
])
```

**Step 3: Add Tab 3 - Template Creator**

Add after tab2 code block (around line 500):

```python
# =============================================================================
# TAB 3: TEMPLATE CREATOR
# =============================================================================
with tab3:
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
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp.write(source_file.read())
            tmp_path = tmp.name

        try:
            st.session_state.template_builder = TemplateBuilder(tmp_path)
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
```

**Step 4: Add Tab 4 - Template Gallery**

Add after tab3 code block:

```python
# =============================================================================
# TAB 4: TEMPLATE GALLERY
# =============================================================================
with tab4:
    st.subheader("Galeria de Templates")
    st.caption("Templates salvos prontos para uso")

    manager = TemplateManager(TEMPLATES_DIR)
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
```

**Step 5: Verify UI renders**

Run: `cd legal-workbench && streamlit run app.py --server.port 8502`
Expected: App loads with 4 tabs without errors

**Step 6: Commit**

```bash
git add legal-workbench/modules/doc_assembler.py
git commit -m "feat(doc-assembler): add Template Creator and Gallery tabs"
```

---

## Task 7: Integration Tests

**Files:**
- Create: `legal-workbench/ferramentas/legal-doc-assembler/tests/test_integration.py`

**Step 1: Write integration test**

```python
# tests/test_integration.py
"""Integration tests for the complete template creation workflow."""

import pytest
import tempfile
import json
from pathlib import Path
from docx import Document

from src.template_builder import TemplateBuilder
from src.template_manager import TemplateManager
from src.engine import DocumentEngine


@pytest.fixture
def sample_contract():
    """Create a realistic sample contract DOCX."""
    doc = Document()
    doc.add_paragraph("CONTRATO DE PRESTAÇÃO DE SERVIÇOS")
    doc.add_paragraph("")
    doc.add_paragraph("CONTRATANTE: Maria das Graças Silva")
    doc.add_paragraph("CPF: 123.456.789-01")
    doc.add_paragraph("Endereço: Rua das Flores, 42, São Paulo/SP")
    doc.add_paragraph("CEP: 01310-100")
    doc.add_paragraph("")
    doc.add_paragraph("CONTRATADA: Empresa XYZ Ltda")
    doc.add_paragraph("CNPJ: 12.345.678/0001-99")
    doc.add_paragraph("")
    doc.add_paragraph("Valor: R$ 5.000,00 (cinco mil reais)")

    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        doc.save(f.name)
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def templates_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestFullWorkflow:
    """Test complete workflow: create template -> save -> use."""

    def test_create_and_use_template(self, sample_contract, templates_dir):
        """Full workflow: create template, save it, then use it."""

        # 1. Create template from sample contract
        builder = TemplateBuilder(sample_contract)

        # 2. Detect patterns
        patterns = builder.detect_patterns()
        assert len(patterns) >= 4  # CPF, CNPJ, CEP, valor

        # 3. Apply detected patterns
        for pattern in patterns:
            builder.apply_detected_pattern(pattern)

        # 4. Add manual field for name
        builder.add_field_replacement(
            "Maria das Graças Silva",
            "nome_contratante",
            "nome"
        )

        # 5. Save template
        result = builder.save_template(
            output_dir=templates_dir,
            template_name="Contrato de Serviços",
            description="Template para contratos de prestação de serviços",
            tags=["contrato", "serviços"]
        )
        assert result['success'] is True

        # 6. Verify template saved
        manager = TemplateManager(templates_dir)
        templates = manager.list_templates()
        assert len(templates) == 1
        assert templates[0]['name'] == "Contrato de Serviços"

        # 7. Use template with new data
        engine = DocumentEngine()
        template_path = templates_dir / "contrato_de_servicos.docx"

        new_data = {
            "nome_contratante": "João Carlos Santos",
            "cpf": "98765432100",
            "cep": "04567890",
            "cnpj": "99888777000166",
            "valor": "10000.00"
        }

        # Validate data against template
        validation = engine.validate_data(str(template_path), new_data)

        # Should have no missing required fields
        # (Note: we may have extra fields that aren't in template)
        assert 'nome_contratante' not in validation.get('missing', [])

        # 8. Render document
        output_path = templates_dir / "output.docx"
        engine.render(
            str(template_path),
            new_data,
            str(output_path)
        )

        assert output_path.exists()

        # 9. Verify output content
        output_doc = Document(str(output_path))
        output_text = '\n'.join(p.text for p in output_doc.paragraphs)

        # Check normalized values appear
        assert "João Carlos Santos" in output_text or "JOÃO CARLOS SANTOS" in output_text
```

**Step 2: Run integration test**

Run: `cd legal-workbench/ferramentas/legal-doc-assembler && pytest tests/test_integration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add legal-workbench/ferramentas/legal-doc-assembler/tests/test_integration.py
git commit -m "test(doc-assembler): add integration tests for template workflow"
```

---

## Task 8: Run All Tests

**Step 1: Run full test suite**

Run: `cd legal-workbench/ferramentas/legal-doc-assembler && pytest tests/ -v --tb=short`
Expected: All tests PASS

**Step 2: Final commit**

```bash
git add -A
git commit -m "feat(doc-assembler): complete template creation feature

- Add DocxParser for DOCX content extraction
- Add PatternDetector for automatic pattern detection (CPF, CNPJ, OAB, CEP, currency)
- Add TemplateBuilder for creating Jinja2 templates from plain DOCX
- Add TemplateManager for template storage and retrieval
- Add 'Criar Template' tab to Streamlit UI
- Add 'Galeria de Templates' tab for saved templates
- Include integration tests for full workflow

Closes #XX"
```

---

## Summary

| Task | Component | Files | Tests |
|------|-----------|-------|-------|
| 1 | DocxParser | `src/docx_parser.py` | ✓ |
| 2 | PatternDetector | `src/pattern_detector.py` | ✓ |
| 3 | TemplateBuilder | `src/template_builder.py` | ✓ |
| 4 | TemplateManager | `src/template_manager.py` | ✓ |
| 5 | Exports | `src/__init__.py` | - |
| 6 | UI Tabs | `modules/doc_assembler.py` | - |
| 7 | Integration | `tests/test_integration.py` | ✓ |
| 8 | Full Suite | All | ✓ |

**Total Estimated Time:** 2-3 hours

**Key Decisions:**
- Templates stored in `ferramentas/legal-doc-assembler/templates/` with JSON metadata
- Pattern detection uses existing regex patterns from trello module
- Manual selection allows any text to become a field
- Both detection and manual selection available (not mutually exclusive)
