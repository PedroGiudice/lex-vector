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
