"""Testes para loader.py - carregamento de arquivos YAML."""

import pytest
from pathlib import Path
import tempfile
import os

from core.loader import load_prompt, load_library, reload_library
from core.models import PromptTemplate, PromptLibrary


SAMPLE_VALID_YAML = """
id: test_prompt
titulo: "Prompt de Teste"
categoria: teste
tags: [exemplo, teste, demo]
descricao: "Um prompt para testes unitários"
variaveis:
  - nome: nome_usuario
    label: "Nome do usuário"
    tipo: text
    obrigatorio: true
  - nome: contexto
    label: "Contexto adicional"
    tipo: textarea
    obrigatorio: false
    default: "Nenhum contexto adicional"
template: |
  Olá {nome_usuario}!

  Contexto: {contexto}

  Este é um prompt de teste.
"""

SAMPLE_INVALID_YAML = """
id: missing_required
titulo: "Faltando Campos"
# falta: categoria, descricao, template
"""

SAMPLE_MALFORMED_YAML = """
this is not: valid: yaml:
  - broken
    indentation
"""


class TestLoadPrompt:
    """Testes para load_prompt()."""

    def test_load_valid_yaml(self, tmp_path):
        """Carrega YAML válido com sucesso."""
        yaml_file = tmp_path / "valid.yaml"
        yaml_file.write_text(SAMPLE_VALID_YAML)

        result = load_prompt(yaml_file)

        assert result is not None
        assert result.id == "test_prompt"
        assert result.titulo == "Prompt de Teste"
        assert len(result.variaveis) == 2
        assert result.variaveis[0].nome == "nome_usuario"

    def test_load_invalid_schema(self, tmp_path):
        """Retorna None para YAML com schema inválido."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text(SAMPLE_INVALID_YAML)

        result = load_prompt(yaml_file)

        assert result is None

    def test_load_malformed_yaml(self, tmp_path):
        """Retorna None para YAML malformado."""
        yaml_file = tmp_path / "malformed.yaml"
        yaml_file.write_text(SAMPLE_MALFORMED_YAML)

        result = load_prompt(yaml_file)

        assert result is None

    def test_load_empty_file(self, tmp_path):
        """Retorna None para arquivo vazio."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        result = load_prompt(yaml_file)

        assert result is None

    def test_load_nonexistent_file(self, tmp_path):
        """Retorna None para arquivo inexistente."""
        result = load_prompt(tmp_path / "nao_existe.yaml")

        assert result is None


class TestLoadLibrary:
    """Testes para load_library()."""

    def test_load_directory_with_prompts(self, tmp_path):
        """Carrega múltiplos prompts de diretório."""
        # Cria estrutura de diretórios
        juridico = tmp_path / "juridico"
        juridico.mkdir()

        # Prompt 1
        (juridico / "contrato.yaml").write_text("""
id: contrato_001
titulo: Análise de Contrato
categoria: juridico
descricao: Analisa contratos
template: Analise este contrato
""")

        # Prompt 2
        (juridico / "peticao.yaml").write_text("""
id: peticao_001
titulo: Revisão de Petição
categoria: juridico
descricao: Revisa petições
template: Revise esta petição
""")

        library = load_library(tmp_path)

        assert len(library.prompts) == 2
        assert {p.id for p in library.prompts} == {"contrato_001", "peticao_001"}

    def test_load_nested_directories(self, tmp_path):
        """Carrega prompts de subdiretórios recursivamente."""
        (tmp_path / "cat1" / "subcat").mkdir(parents=True)

        (tmp_path / "cat1" / "prompt1.yaml").write_text("""
id: p1
titulo: P1
categoria: cat1
descricao: Desc
template: T
""")

        (tmp_path / "cat1" / "subcat" / "prompt2.yaml").write_text("""
id: p2
titulo: P2
categoria: subcat
descricao: Desc
template: T
""")

        library = load_library(tmp_path)

        assert len(library.prompts) == 2

    def test_load_mixed_valid_invalid(self, tmp_path):
        """Carrega válidos e ignora inválidos."""
        # Válido
        (tmp_path / "valid.yaml").write_text("""
id: valid
titulo: Valid
categoria: test
descricao: D
template: T
""")

        # Inválido
        (tmp_path / "invalid.yaml").write_text(SAMPLE_INVALID_YAML)

        library = load_library(tmp_path)

        assert len(library.prompts) == 1
        assert library.prompts[0].id == "valid"

    def test_load_empty_directory(self, tmp_path):
        """Retorna biblioteca vazia para diretório vazio."""
        library = load_library(tmp_path)

        assert len(library.prompts) == 0

    def test_load_nonexistent_directory(self, tmp_path):
        """Retorna biblioteca inexistente para diretório inexistente."""
        library = load_library(tmp_path / "nao_existe")

        assert len(library.prompts) == 0

    def test_supports_yml_extension(self, tmp_path):
        """Suporta arquivos .yml além de .yaml."""
        (tmp_path / "prompt.yml").write_text("""
id: yml_prompt
titulo: YML
categoria: test
descricao: D
template: T
""")

        library = load_library(tmp_path)

        assert len(library.prompts) == 1
        assert library.prompts[0].id == "yml_prompt"


class TestReloadLibrary:
    """Testes para reload_library()."""

    def test_reload_updates_content(self, tmp_path):
        """Reload captura mudanças no diretório."""
        yaml_file = tmp_path / "prompt.yaml"
        yaml_file.write_text("""
id: original
titulo: Original
categoria: test
descricao: D
template: T
""")

        library = load_library(tmp_path)
        assert library.prompts[0].titulo == "Original"

        # Modifica arquivo
        yaml_file.write_text("""
id: original
titulo: Modificado
categoria: test
descricao: D
template: T
""")

        new_library = reload_library(tmp_path, library)

        assert new_library.prompts[0].titulo == "Modificado"
