# Prompt Library Backend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a reusable backend for managing, searching, and rendering prompt templates stored as YAML files.

**Architecture:** Pydantic v2 models define the schema. Loader reads YAML files recursively. Search uses simple fuzzy matching (no external deps). Renderer interpolates variables with validation.

**Tech Stack:** Python 3.11, Pydantic v2, PyYAML, pytest

**Base Path:** `legal-workbench/ferramentas/prompt-library/`

---

## Execution Strategy: Parallel Batches

| Batch | Tasks | Dependencies | Parallelizable |
|-------|-------|--------------|----------------|
| 1 | Tasks 1-3 (structure, models, requirements) | None | Yes |
| 2 | Tasks 4-6 (loader, search, renderer) | Batch 1 | Yes |
| 3 | Tasks 7-11 (__init__, all tests) | Batch 2 | Yes |

---

## Batch 1: Foundation (Parallel)

### Task 1: Create Directory Structure

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/core/`
- Create: `legal-workbench/ferramentas/prompt-library/prompts/juridico/.gitkeep`
- Create: `legal-workbench/ferramentas/prompt-library/prompts/troubleshooting/.gitkeep`
- Create: `legal-workbench/ferramentas/prompt-library/prompts/meta/.gitkeep`
- Create: `legal-workbench/ferramentas/prompt-library/tests/`

**Step 1: Create all directories**

```bash
mkdir -p legal-workbench/ferramentas/prompt-library/{core,prompts/{juridico,troubleshooting,meta},tests}
```

**Step 2: Create .gitkeep files**

```bash
touch legal-workbench/ferramentas/prompt-library/prompts/juridico/.gitkeep
touch legal-workbench/ferramentas/prompt-library/prompts/troubleshooting/.gitkeep
touch legal-workbench/ferramentas/prompt-library/prompts/meta/.gitkeep
```

**Step 3: Verify structure**

```bash
tree legal-workbench/ferramentas/prompt-library/
```

Expected:
```
prompt-library/
├── core/
├── prompts/
│   ├── juridico/
│   │   └── .gitkeep
│   ├── meta/
│   │   └── .gitkeep
│   └── troubleshooting/
│       └── .gitkeep
└── tests/
```

---

### Task 2: Create requirements.txt

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/requirements.txt`

**Step 1: Write requirements**

```text
pydantic>=2.0
pyyaml>=6.0
pytest>=7.0
```

**Step 2: Verify file exists**

```bash
cat legal-workbench/ferramentas/prompt-library/requirements.txt
```

---

### Task 3: Create models.py

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/core/models.py`

**Step 1: Write Pydantic models**

```python
"""
Schemas Pydantic para templates de prompt.

Este módulo define as estruturas de dados para:
- PromptVariable: variáveis preenchíveis em templates
- PromptTemplate: template completo com metadados
- PromptLibrary: coleção de prompts carregados
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class PromptVariable(BaseModel):
    """Define uma variável preenchível no template."""

    nome: str = Field(..., description="Nome da variável no template (usado em {nome})")
    label: str = Field(..., description="Label exibido na UI")
    tipo: Literal["text", "textarea", "select"] = "text"
    obrigatorio: bool = True
    opcoes: Optional[List[str]] = None  # Para tipo "select"
    placeholder: Optional[str] = None
    default: Optional[str] = None


class PromptTemplate(BaseModel):
    """Template de prompt completo."""

    id: str = Field(..., description="Identificador único, ex: 'hook_error'")
    titulo: str = Field(..., description="Nome legível, ex: 'User Prompt Submit Hook Error'")
    categoria: str = Field(..., description="Categoria principal, ex: 'troubleshooting'")
    tags: List[str] = Field(default_factory=list, description="Tags para busca")
    descricao: str = Field(..., description="Descrição curta do propósito")
    variaveis: List[PromptVariable] = Field(default_factory=list)
    template: str = Field(..., description="Texto do prompt com placeholders {variavel}")

    # Metadados opcionais
    autor: Optional[str] = None
    versao: str = "1.0"
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None


class PromptLibrary(BaseModel):
    """Coleção de prompts carregados."""

    prompts: List[PromptTemplate] = Field(default_factory=list)

    def get_by_id(self, id: str) -> Optional[PromptTemplate]:
        """Busca prompt por ID."""
        return next((p for p in self.prompts if p.id == id), None)

    def get_by_categoria(self, categoria: str) -> List[PromptTemplate]:
        """Lista prompts de uma categoria."""
        return [p for p in self.prompts if p.categoria == categoria]

    def list_categorias(self) -> List[str]:
        """Lista categorias únicas."""
        return sorted(set(p.categoria for p in self.prompts))
```

**Step 2: Verify syntax**

```bash
cd legal-workbench/ferramentas/prompt-library && python -m py_compile core/models.py && echo "Syntax OK"
```

Expected: `Syntax OK`

---

## Batch 2: Core Modules (Parallel - depends on Batch 1)

### Task 4: Create loader.py

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/core/loader.py`

**Step 1: Write loader module**

```python
"""
Carregador de templates de prompt a partir de arquivos YAML.

Responsabilidades:
- Carregar arquivos .yaml recursivamente
- Validar contra schema PromptTemplate
- Logar erros sem quebrar (skip inválidos)
"""

import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from .models import PromptLibrary, PromptTemplate

logger = logging.getLogger(__name__)


def load_prompt(file_path: Path) -> Optional[PromptTemplate]:
    """
    Carrega e valida um único arquivo YAML.

    Args:
        file_path: Caminho para o arquivo YAML

    Returns:
        PromptTemplate validado ou None se inválido
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            logger.warning(f"Arquivo vazio: {file_path}")
            return None

        return PromptTemplate.model_validate(data)

    except yaml.YAMLError as e:
        logger.error(f"Erro de YAML em {file_path}: {e}")
        return None
    except ValidationError as e:
        logger.error(f"Erro de validação em {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro ao carregar {file_path}: {e}")
        return None


def load_library(prompts_dir: Path) -> PromptLibrary:
    """
    Carrega todos os prompts de um diretório.

    Args:
        prompts_dir: Diretório raiz dos prompts

    Returns:
        PromptLibrary com todos os prompts válidos
    """
    prompts: list[PromptTemplate] = []

    if not prompts_dir.exists():
        logger.warning(f"Diretório não existe: {prompts_dir}")
        return PromptLibrary(prompts=prompts)

    # Busca recursiva por arquivos .yaml e .yml
    for pattern in ["**/*.yaml", "**/*.yml"]:
        for file_path in prompts_dir.glob(pattern):
            if file_path.is_file():
                prompt = load_prompt(file_path)
                if prompt is not None:
                    prompts.append(prompt)
                    logger.debug(f"Carregado: {prompt.id} de {file_path}")

    logger.info(f"Carregados {len(prompts)} prompts de {prompts_dir}")
    return PromptLibrary(prompts=prompts)


def reload_library(prompts_dir: Path, library: PromptLibrary) -> PromptLibrary:
    """
    Recarrega biblioteca (para hot-reload na UI).

    Args:
        prompts_dir: Diretório raiz dos prompts
        library: Biblioteca atual (ignorada, recarrega do zero)

    Returns:
        Nova PromptLibrary com prompts atualizados
    """
    # Por simplicidade, recarrega tudo
    # Futuro: implementar diff para recarregar apenas modificados
    return load_library(prompts_dir)
```

**Step 2: Verify syntax**

```bash
cd legal-workbench/ferramentas/prompt-library && python -m py_compile core/loader.py && echo "Syntax OK"
```

---

### Task 5: Create search.py

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/core/search.py`

**Step 1: Write search module**

```python
"""
Busca fuzzy em templates de prompt.

Responsabilidades:
- Busca por título, tags, descrição
- Filtro por categoria
- Ordenação por relevância
"""

from typing import List, Optional

from .models import PromptLibrary, PromptTemplate


def _normalize(text: str) -> str:
    """Normaliza texto para busca (lowercase, strip)."""
    return text.lower().strip()


def _calculate_score(query: str, prompt: PromptTemplate) -> int:
    """
    Calcula score de relevância para um prompt.

    Pontuação:
    - Match exato no título: 100
    - Título começa com query: 50
    - Query contida no título: 30
    - Match exato em tag: 25
    - Query contida em tag: 15
    - Query contida na descrição: 10

    Returns:
        Score total (0 = sem match)
    """
    score = 0
    query_norm = _normalize(query)

    # Título
    titulo_norm = _normalize(prompt.titulo)
    if titulo_norm == query_norm:
        score += 100
    elif titulo_norm.startswith(query_norm):
        score += 50
    elif query_norm in titulo_norm:
        score += 30

    # Tags
    for tag in prompt.tags:
        tag_norm = _normalize(tag)
        if tag_norm == query_norm:
            score += 25
        elif query_norm in tag_norm:
            score += 15

    # Descrição
    descricao_norm = _normalize(prompt.descricao)
    if query_norm in descricao_norm:
        score += 10

    # ID (bonus para match exato)
    if _normalize(prompt.id) == query_norm:
        score += 80

    return score


def search(
    library: PromptLibrary,
    query: str,
    categoria: Optional[str] = None,
    limit: int = 20
) -> List[PromptTemplate]:
    """
    Busca fuzzy na biblioteca.

    Busca em: titulo, tags, descricao
    Ordena por relevância (match no título > tags > descrição)

    Args:
        library: Biblioteca de prompts
        query: Termo de busca
        categoria: Filtro opcional por categoria
        limit: Máximo de resultados

    Returns:
        Lista de prompts ordenados por relevância
    """
    if not query or not query.strip():
        # Sem query, retorna todos (filtrados por categoria se especificada)
        results = library.prompts
        if categoria:
            results = [p for p in results if p.categoria == categoria]
        return results[:limit]

    # Calcula scores
    scored: List[tuple[int, PromptTemplate]] = []
    for prompt in library.prompts:
        # Filtro por categoria
        if categoria and prompt.categoria != categoria:
            continue

        score = _calculate_score(query, prompt)
        if score > 0:
            scored.append((score, prompt))

    # Ordena por score (maior primeiro)
    scored.sort(key=lambda x: x[0], reverse=True)

    # Retorna apenas os prompts
    return [prompt for _, prompt in scored[:limit]]


def filter_by_tags(
    library: PromptLibrary,
    tags: List[str],
    match_all: bool = False
) -> List[PromptTemplate]:
    """
    Filtra por tags.

    Args:
        library: Biblioteca de prompts
        tags: Lista de tags para filtrar
        match_all: Se True, exige todas as tags; se False, qualquer uma

    Returns:
        Lista de prompts que correspondem aos critérios
    """
    if not tags:
        return library.prompts

    # Normaliza tags de busca
    tags_norm = {_normalize(t) for t in tags}

    results: List[PromptTemplate] = []
    for prompt in library.prompts:
        prompt_tags_norm = {_normalize(t) for t in prompt.tags}

        if match_all:
            # Todas as tags devem estar presentes
            if tags_norm.issubset(prompt_tags_norm):
                results.append(prompt)
        else:
            # Qualquer tag é suficiente
            if tags_norm & prompt_tags_norm:  # intersecção não vazia
                results.append(prompt)

    return results
```

**Step 2: Verify syntax**

```bash
cd legal-workbench/ferramentas/prompt-library && python -m py_compile core/search.py && echo "Syntax OK"
```

---

### Task 6: Create renderer.py

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/core/renderer.py`

**Step 1: Write renderer module**

```python
"""
Renderização de templates de prompt com interpolação de variáveis.

Responsabilidades:
- Interpolar variáveis no template
- Validar variáveis obrigatórias
- Fornecer preview com placeholders
"""

import re
from typing import Dict, List, Optional

from .models import PromptTemplate


class RenderError(Exception):
    """Erro ao renderizar template."""
    pass


class MissingVariableError(RenderError):
    """Variável obrigatória não fornecida."""

    def __init__(self, missing_vars: List[str]):
        self.missing_vars = missing_vars
        super().__init__(f"Variáveis obrigatórias faltando: {', '.join(missing_vars)}")


def get_missing_variables(
    template: PromptTemplate,
    variables: Dict[str, str]
) -> List[str]:
    """
    Retorna lista de variáveis obrigatórias faltando.

    Args:
        template: Template a verificar
        variables: Variáveis fornecidas

    Returns:
        Lista de nomes de variáveis obrigatórias não fornecidas
    """
    missing: List[str] = []

    for var in template.variaveis:
        if var.obrigatorio:
            # Variável é obrigatória
            value = variables.get(var.nome)
            if value is None or (isinstance(value, str) and not value.strip()):
                # Não fornecida ou vazia, verifica se tem default
                if var.default is None:
                    missing.append(var.nome)

    return missing


def _apply_defaults(
    template: PromptTemplate,
    variables: Dict[str, str]
) -> Dict[str, str]:
    """
    Aplica valores default para variáveis não fornecidas.

    Args:
        template: Template com definições de variáveis
        variables: Variáveis fornecidas pelo usuário

    Returns:
        Dicionário com valores (fornecidos + defaults)
    """
    result = dict(variables)

    for var in template.variaveis:
        if var.nome not in result or not result[var.nome]:
            if var.default is not None:
                result[var.nome] = var.default

    return result


def render(
    template: PromptTemplate,
    variables: Dict[str, str]
) -> str:
    """
    Renderiza template com variáveis.

    Args:
        template: Template a renderizar
        variables: Dicionário de variáveis {nome: valor}

    Returns:
        Texto do prompt com variáveis interpoladas

    Raises:
        MissingVariableError: Se variável obrigatória não fornecida
    """
    # Aplica defaults
    vars_with_defaults = _apply_defaults(template, variables)

    # Verifica obrigatórias
    missing = get_missing_variables(template, vars_with_defaults)
    if missing:
        raise MissingVariableError(missing)

    # Interpola usando str.format() style
    # Usa regex para substituição segura (evita KeyError em {texto_sem_variavel})
    result = template.template

    for var in template.variaveis:
        placeholder = "{" + var.nome + "}"
        value = vars_with_defaults.get(var.nome, "")
        result = result.replace(placeholder, str(value))

    return result


def preview(
    template: PromptTemplate,
    variables: Optional[Dict[str, str]] = None
) -> str:
    """
    Preview do template.

    Variáveis não fornecidas aparecem como [{nome}]

    Args:
        template: Template a visualizar
        variables: Variáveis opcionais para preencher

    Returns:
        Texto com variáveis interpoladas ou marcadores
    """
    vars_dict = variables or {}

    # Aplica defaults
    vars_with_defaults = _apply_defaults(template, vars_dict)

    result = template.template

    for var in template.variaveis:
        placeholder = "{" + var.nome + "}"
        value = vars_with_defaults.get(var.nome)

        if value is not None and str(value).strip():
            # Tem valor, substitui
            result = result.replace(placeholder, str(value))
        else:
            # Sem valor, mostra marcador
            result = result.replace(placeholder, f"[{var.nome}]")

    return result
```

**Step 2: Verify syntax**

```bash
cd legal-workbench/ferramentas/prompt-library && python -m py_compile core/renderer.py && echo "Syntax OK"
```

---

## Batch 3: Integration & Tests (Parallel - depends on Batch 2)

### Task 7: Create core/__init__.py

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/core/__init__.py`

**Step 1: Write exports**

```python
"""
Prompt Library Core - Backend para gerenciamento de prompts.

Uso:
    from core import load_library, search, render

    library = load_library(Path("prompts"))
    results = search(library, "contrato")
    output = render(results[0], {"parte": "João"})
"""

from .models import PromptVariable, PromptTemplate, PromptLibrary
from .loader import load_library, load_prompt, reload_library
from .search import search, filter_by_tags
from .renderer import render, preview, RenderError, MissingVariableError

__all__ = [
    # Models
    "PromptVariable",
    "PromptTemplate",
    "PromptLibrary",
    # Loader
    "load_library",
    "load_prompt",
    "reload_library",
    # Search
    "search",
    "filter_by_tags",
    # Renderer
    "render",
    "preview",
    "RenderError",
    "MissingVariableError",
]
```

---

### Task 8: Create tests/__init__.py

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/tests/__init__.py`

**Step 1: Write empty init**

```python
"""Testes unitários para o módulo prompt-library."""
```

---

### Task 9: Create test_models.py

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/tests/test_models.py`

**Step 1: Write model tests**

```python
"""Testes para models.py - validação de schemas Pydantic."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from core.models import PromptVariable, PromptTemplate, PromptLibrary


class TestPromptVariable:
    """Testes para PromptVariable."""

    def test_minimal_valid(self):
        """Variável com campos mínimos obrigatórios."""
        var = PromptVariable(nome="teste", label="Teste")
        assert var.nome == "teste"
        assert var.label == "Teste"
        assert var.tipo == "text"  # default
        assert var.obrigatorio is True  # default

    def test_all_fields(self):
        """Variável com todos os campos."""
        var = PromptVariable(
            nome="status",
            label="Status do Processo",
            tipo="select",
            obrigatorio=False,
            opcoes=["ativo", "arquivado", "suspenso"],
            placeholder="Selecione...",
            default="ativo"
        )
        assert var.tipo == "select"
        assert len(var.opcoes) == 3
        assert var.default == "ativo"

    def test_missing_required_field(self):
        """Deve falhar sem campo obrigatório."""
        with pytest.raises(ValidationError):
            PromptVariable(nome="teste")  # falta label

    def test_invalid_tipo(self):
        """Deve falhar com tipo inválido."""
        with pytest.raises(ValidationError):
            PromptVariable(nome="x", label="X", tipo="invalid")


class TestPromptTemplate:
    """Testes para PromptTemplate."""

    def test_minimal_valid(self):
        """Template com campos mínimos."""
        template = PromptTemplate(
            id="test_001",
            titulo="Teste",
            categoria="teste",
            descricao="Um teste",
            template="Olá {nome}"
        )
        assert template.id == "test_001"
        assert template.versao == "1.0"  # default
        assert template.tags == []  # default
        assert template.variaveis == []  # default

    def test_with_variables(self):
        """Template com variáveis definidas."""
        template = PromptTemplate(
            id="contract_review",
            titulo="Revisão de Contrato",
            categoria="juridico",
            descricao="Analisa cláusulas contratuais",
            variaveis=[
                PromptVariable(nome="contrato", label="Texto do Contrato", tipo="textarea"),
                PromptVariable(nome="foco", label="Foco da Análise", obrigatorio=False)
            ],
            template="Analise o contrato:\n{contrato}\n\nFoco: {foco}"
        )
        assert len(template.variaveis) == 2
        assert template.variaveis[0].tipo == "textarea"

    def test_with_metadata(self):
        """Template com metadados opcionais."""
        now = datetime.now()
        template = PromptTemplate(
            id="meta_001",
            titulo="Com Metadados",
            categoria="meta",
            descricao="Teste",
            template="...",
            autor="dev@test.com",
            versao="2.1",
            criado_em=now
        )
        assert template.autor == "dev@test.com"
        assert template.versao == "2.1"
        assert template.criado_em == now

    def test_missing_required(self):
        """Deve falhar sem campos obrigatórios."""
        with pytest.raises(ValidationError):
            PromptTemplate(id="x", titulo="X")  # falta categoria, descricao, template


class TestPromptLibrary:
    """Testes para PromptLibrary."""

    @pytest.fixture
    def sample_library(self):
        """Biblioteca de exemplo com 3 prompts."""
        return PromptLibrary(prompts=[
            PromptTemplate(
                id="juridico_001",
                titulo="Análise de Petição",
                categoria="juridico",
                descricao="Analisa petições",
                tags=["peticao", "analise"],
                template="..."
            ),
            PromptTemplate(
                id="juridico_002",
                titulo="Revisão de Contrato",
                categoria="juridico",
                descricao="Revisa contratos",
                tags=["contrato"],
                template="..."
            ),
            PromptTemplate(
                id="troubleshoot_001",
                titulo="Debug de Hook",
                categoria="troubleshooting",
                descricao="Ajuda com erros de hook",
                tags=["hook", "debug"],
                template="..."
            ),
        ])

    def test_empty_library(self):
        """Biblioteca vazia."""
        lib = PromptLibrary()
        assert lib.prompts == []
        assert lib.list_categorias() == []

    def test_get_by_id_found(self, sample_library):
        """Busca por ID existente."""
        result = sample_library.get_by_id("juridico_001")
        assert result is not None
        assert result.titulo == "Análise de Petição"

    def test_get_by_id_not_found(self, sample_library):
        """Busca por ID inexistente."""
        result = sample_library.get_by_id("nao_existe")
        assert result is None

    def test_get_by_categoria(self, sample_library):
        """Filtro por categoria."""
        juridicos = sample_library.get_by_categoria("juridico")
        assert len(juridicos) == 2

        troubleshoot = sample_library.get_by_categoria("troubleshooting")
        assert len(troubleshoot) == 1

    def test_list_categorias(self, sample_library):
        """Lista categorias únicas ordenadas."""
        categorias = sample_library.list_categorias()
        assert categorias == ["juridico", "troubleshooting"]
```

**Step 2: Run tests**

```bash
cd legal-workbench/ferramentas/prompt-library && python -m pytest tests/test_models.py -v
```

Expected: All tests PASS

---

### Task 10: Create test_loader.py

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/tests/test_loader.py`

**Step 1: Write loader tests**

```python
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
        """Retorna biblioteca vazia para diretório inexistente."""
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
```

**Step 2: Run tests**

```bash
cd legal-workbench/ferramentas/prompt-library && python -m pytest tests/test_loader.py -v
```

Expected: All tests PASS

---

### Task 11: Create test_search.py

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/tests/test_search.py`

**Step 1: Write search tests**

```python
"""Testes para search.py - busca fuzzy e filtros."""

import pytest
from core.search import search, filter_by_tags, _normalize, _calculate_score
from core.models import PromptTemplate, PromptLibrary


@pytest.fixture
def sample_library():
    """Biblioteca com prompts variados para teste de busca."""
    return PromptLibrary(prompts=[
        PromptTemplate(
            id="contrato_analise",
            titulo="Análise de Contrato",
            categoria="juridico",
            descricao="Analisa cláusulas e riscos em contratos comerciais",
            tags=["contrato", "analise", "risco"],
            template="..."
        ),
        PromptTemplate(
            id="contrato_revisao",
            titulo="Revisão de Contrato",
            categoria="juridico",
            descricao="Revisa contratos para identificar problemas",
            tags=["contrato", "revisao"],
            template="..."
        ),
        PromptTemplate(
            id="hook_error",
            titulo="Debug de Hook Error",
            categoria="troubleshooting",
            descricao="Ajuda a resolver erros em hooks do Claude",
            tags=["hook", "erro", "debug", "claude"],
            template="..."
        ),
        PromptTemplate(
            id="git_merge",
            titulo="Resolver Conflito Git",
            categoria="troubleshooting",
            descricao="Guia para resolver conflitos de merge",
            tags=["git", "merge", "conflito"],
            template="..."
        ),
        PromptTemplate(
            id="formular_pedido",
            titulo="Como Formular Pedidos",
            categoria="meta",
            descricao="Meta-prompt sobre como fazer bons pedidos ao Claude",
            tags=["meta", "pedido", "prompt"],
            template="..."
        ),
    ])


class TestNormalize:
    """Testes para _normalize()."""

    def test_lowercase(self):
        assert _normalize("TESTE") == "teste"

    def test_strip(self):
        assert _normalize("  teste  ") == "teste"

    def test_combined(self):
        assert _normalize("  TESTE  ") == "teste"


class TestCalculateScore:
    """Testes para _calculate_score()."""

    def test_exact_title_match(self, sample_library):
        """Match exato no título = 100 pontos."""
        prompt = sample_library.prompts[0]  # "Análise de Contrato"
        score = _calculate_score("Análise de Contrato", prompt)
        assert score >= 100

    def test_title_starts_with(self, sample_library):
        """Título começa com query = 50 pontos."""
        prompt = sample_library.prompts[0]
        score = _calculate_score("Análise", prompt)
        assert score >= 50

    def test_title_contains(self, sample_library):
        """Query contida no título = 30 pontos."""
        prompt = sample_library.prompts[0]
        score = _calculate_score("Contrato", prompt)
        assert score >= 30

    def test_exact_tag_match(self, sample_library):
        """Match exato em tag = 25 pontos."""
        prompt = sample_library.prompts[0]
        score = _calculate_score("risco", prompt)
        assert score >= 25

    def test_description_match(self, sample_library):
        """Query na descrição = 10 pontos."""
        prompt = sample_library.prompts[0]
        score = _calculate_score("cláusulas", prompt)
        assert score >= 10

    def test_no_match(self, sample_library):
        """Sem match = 0 pontos."""
        prompt = sample_library.prompts[0]
        score = _calculate_score("xyz123", prompt)
        assert score == 0


class TestSearch:
    """Testes para search()."""

    def test_search_by_title(self, sample_library):
        """Busca por título retorna resultados ordenados."""
        results = search(sample_library, "Contrato")

        assert len(results) == 2
        # Ambos têm "Contrato" no título
        assert all("contrato" in r.id for r in results)

    def test_search_by_tag(self, sample_library):
        """Busca por tag encontra prompts."""
        results = search(sample_library, "debug")

        assert len(results) == 1
        assert results[0].id == "hook_error"

    def test_search_by_description(self, sample_library):
        """Busca por termo na descrição."""
        results = search(sample_library, "merge")

        assert len(results) == 1
        assert results[0].id == "git_merge"

    def test_search_with_categoria_filter(self, sample_library):
        """Filtro por categoria."""
        # Busca "contrato" mas apenas em troubleshooting (não deve encontrar)
        results = search(sample_library, "contrato", categoria="troubleshooting")
        assert len(results) == 0

        # Busca em juridico (deve encontrar)
        results = search(sample_library, "contrato", categoria="juridico")
        assert len(results) == 2

    def test_search_with_limit(self, sample_library):
        """Respeita limite de resultados."""
        results = search(sample_library, "contrato", limit=1)
        assert len(results) == 1

    def test_search_empty_query_returns_all(self, sample_library):
        """Query vazia retorna todos os prompts."""
        results = search(sample_library, "")
        assert len(results) == 5

        results = search(sample_library, "   ")
        assert len(results) == 5

    def test_search_empty_query_with_categoria(self, sample_library):
        """Query vazia com filtro de categoria."""
        results = search(sample_library, "", categoria="juridico")
        assert len(results) == 2

    def test_search_relevance_order(self, sample_library):
        """Resultados ordenados por relevância."""
        results = search(sample_library, "hook")

        # "hook_error" deve vir primeiro (match no ID e tag)
        assert results[0].id == "hook_error"


class TestFilterByTags:
    """Testes para filter_by_tags()."""

    def test_single_tag_any_match(self, sample_library):
        """Filtro por uma tag (match_all=False)."""
        results = filter_by_tags(sample_library, ["contrato"])

        assert len(results) == 2
        assert all("contrato" in p.tags for p in results)

    def test_multiple_tags_any_match(self, sample_library):
        """Múltiplas tags, qualquer uma (OR)."""
        results = filter_by_tags(sample_library, ["contrato", "git"])

        assert len(results) == 3  # 2 contratos + 1 git

    def test_multiple_tags_all_match(self, sample_library):
        """Múltiplas tags, todas (AND)."""
        results = filter_by_tags(sample_library, ["contrato", "analise"], match_all=True)

        assert len(results) == 1
        assert results[0].id == "contrato_analise"

    def test_no_matching_tags(self, sample_library):
        """Nenhum prompt tem a tag."""
        results = filter_by_tags(sample_library, ["inexistente"])
        assert len(results) == 0

    def test_empty_tags_returns_all(self, sample_library):
        """Lista de tags vazia retorna todos."""
        results = filter_by_tags(sample_library, [])
        assert len(results) == 5

    def test_case_insensitive(self, sample_library):
        """Busca por tag é case-insensitive."""
        results = filter_by_tags(sample_library, ["CONTRATO"])
        assert len(results) == 2
```

**Step 2: Run tests**

```bash
cd legal-workbench/ferramentas/prompt-library && python -m pytest tests/test_search.py -v
```

Expected: All tests PASS

---

### Task 12: Create test_renderer.py

**Files:**
- Create: `legal-workbench/ferramentas/prompt-library/tests/test_renderer.py`

**Step 1: Write renderer tests**

```python
"""Testes para renderer.py - interpolação de variáveis."""

import pytest
from core.renderer import (
    render,
    preview,
    get_missing_variables,
    RenderError,
    MissingVariableError
)
from core.models import PromptTemplate, PromptVariable


@pytest.fixture
def simple_template():
    """Template simples com uma variável obrigatória."""
    return PromptTemplate(
        id="simple",
        titulo="Simple",
        categoria="test",
        descricao="Template simples",
        variaveis=[
            PromptVariable(nome="nome", label="Nome", obrigatorio=True)
        ],
        template="Olá, {nome}!"
    )


@pytest.fixture
def complex_template():
    """Template com múltiplas variáveis, algumas opcionais."""
    return PromptTemplate(
        id="complex",
        titulo="Complex",
        categoria="test",
        descricao="Template complexo",
        variaveis=[
            PromptVariable(nome="nome", label="Nome", obrigatorio=True),
            PromptVariable(nome="cargo", label="Cargo", obrigatorio=True),
            PromptVariable(
                nome="saudacao",
                label="Saudação",
                obrigatorio=False,
                default="Prezado(a)"
            ),
            PromptVariable(
                nome="assinatura",
                label="Assinatura",
                obrigatorio=False
            ),
        ],
        template="{saudacao} {nome},\n\nSeu cargo é: {cargo}\n\n{assinatura}"
    )


@pytest.fixture
def no_vars_template():
    """Template sem variáveis."""
    return PromptTemplate(
        id="static",
        titulo="Static",
        categoria="test",
        descricao="Template estático",
        variaveis=[],
        template="Este é um texto fixo sem variáveis."
    )


class TestGetMissingVariables:
    """Testes para get_missing_variables()."""

    def test_all_provided(self, simple_template):
        """Sem faltantes quando tudo fornecido."""
        missing = get_missing_variables(simple_template, {"nome": "João"})
        assert missing == []

    def test_missing_required(self, simple_template):
        """Detecta variável obrigatória faltando."""
        missing = get_missing_variables(simple_template, {})
        assert missing == ["nome"]

    def test_empty_string_counts_as_missing(self, simple_template):
        """String vazia conta como faltante."""
        missing = get_missing_variables(simple_template, {"nome": ""})
        assert missing == ["nome"]

        missing = get_missing_variables(simple_template, {"nome": "   "})
        assert missing == ["nome"]

    def test_optional_not_required(self, complex_template):
        """Variáveis opcionais não são reportadas como faltantes."""
        missing = get_missing_variables(
            complex_template,
            {"nome": "João", "cargo": "Dev"}
        )
        assert missing == []

    def test_default_satisfies_required(self, complex_template):
        """Default satisfaz requisito (não é faltante)."""
        # saudacao tem default, não deve aparecer em missing
        missing = get_missing_variables(
            complex_template,
            {"nome": "João", "cargo": "Dev"}
        )
        assert "saudacao" not in missing


class TestRender:
    """Testes para render()."""

    def test_simple_render(self, simple_template):
        """Renderiza template simples."""
        result = render(simple_template, {"nome": "Maria"})
        assert result == "Olá, Maria!"

    def test_complex_render_all_vars(self, complex_template):
        """Renderiza com todas as variáveis."""
        result = render(complex_template, {
            "nome": "Ana",
            "cargo": "Advogada",
            "saudacao": "Cara",
            "assinatura": "Atenciosamente"
        })
        assert "Cara Ana" in result
        assert "Advogada" in result
        assert "Atenciosamente" in result

    def test_render_uses_defaults(self, complex_template):
        """Usa valores default quando não fornecidos."""
        result = render(complex_template, {
            "nome": "Pedro",
            "cargo": "Gerente"
        })
        assert "Prezado(a) Pedro" in result  # default de saudacao

    def test_render_no_vars(self, no_vars_template):
        """Template sem variáveis renderiza normalmente."""
        result = render(no_vars_template, {})
        assert result == "Este é um texto fixo sem variáveis."

    def test_render_missing_required_raises(self, simple_template):
        """Levanta erro se variável obrigatória falta."""
        with pytest.raises(MissingVariableError) as exc_info:
            render(simple_template, {})

        assert "nome" in exc_info.value.missing_vars

    def test_render_missing_multiple(self, complex_template):
        """Reporta múltiplas variáveis faltantes."""
        with pytest.raises(MissingVariableError) as exc_info:
            render(complex_template, {})

        assert set(exc_info.value.missing_vars) == {"nome", "cargo"}

    def test_extra_vars_ignored(self, simple_template):
        """Variáveis extras são ignoradas."""
        result = render(simple_template, {
            "nome": "João",
            "extra": "ignorada",
            "outra": "também ignorada"
        })
        assert result == "Olá, João!"


class TestPreview:
    """Testes para preview()."""

    def test_preview_no_vars(self, simple_template):
        """Preview sem variáveis mostra marcadores."""
        result = preview(simple_template)
        assert result == "Olá, [nome]!"

    def test_preview_partial_vars(self, complex_template):
        """Preview com algumas variáveis preenchidas."""
        result = preview(complex_template, {"nome": "Ana"})

        assert "Ana" in result  # fornecida
        assert "[cargo]" in result  # não fornecida
        assert "Prezado(a)" in result  # default aplicado

    def test_preview_all_vars(self, simple_template):
        """Preview com todas as variáveis = render."""
        result = preview(simple_template, {"nome": "João"})
        assert result == "Olá, João!"

    def test_preview_uses_defaults(self, complex_template):
        """Preview usa defaults para variáveis com default."""
        result = preview(complex_template, {"nome": "Maria", "cargo": "Dev"})

        assert "Prezado(a)" in result  # default
        assert "[assinatura]" in result  # sem default, sem valor


class TestRenderError:
    """Testes para classes de erro."""

    def test_missing_variable_error_message(self):
        """MissingVariableError tem mensagem informativa."""
        error = MissingVariableError(["var1", "var2"])

        assert "var1" in str(error)
        assert "var2" in str(error)
        assert error.missing_vars == ["var1", "var2"]

    def test_render_error_is_exception(self):
        """RenderError é Exception."""
        assert issubclass(RenderError, Exception)
        assert issubclass(MissingVariableError, RenderError)
```

**Step 2: Run tests**

```bash
cd legal-workbench/ferramentas/prompt-library && python -m pytest tests/test_renderer.py -v
```

Expected: All tests PASS

---

## Task 13: Run Full Test Suite

**Step 1: Install dependencies**

```bash
cd legal-workbench/ferramentas/prompt-library
pip install -r requirements.txt
```

**Step 2: Run all tests**

```bash
cd legal-workbench/ferramentas/prompt-library
python -m pytest tests/ -v
```

Expected: All 40+ tests PASS

**Step 3: Commit**

```bash
git add legal-workbench/ferramentas/prompt-library/
git commit -m "feat(prompt-library): add backend core module

- models.py: Pydantic schemas (PromptVariable, PromptTemplate, PromptLibrary)
- loader.py: YAML loading with validation
- search.py: Fuzzy search by title/tags/description
- renderer.py: Variable interpolation with validation
- Full test coverage for all modules"
```

---

## Verification Checklist

After execution, verify:

- [ ] `legal-workbench/ferramentas/prompt-library/core/__init__.py` exists
- [ ] `legal-workbench/ferramentas/prompt-library/core/models.py` exists
- [ ] `legal-workbench/ferramentas/prompt-library/core/loader.py` exists
- [ ] `legal-workbench/ferramentas/prompt-library/core/search.py` exists
- [ ] `legal-workbench/ferramentas/prompt-library/core/renderer.py` exists
- [ ] `legal-workbench/ferramentas/prompt-library/prompts/juridico/.gitkeep` exists
- [ ] `legal-workbench/ferramentas/prompt-library/prompts/troubleshooting/.gitkeep` exists
- [ ] `legal-workbench/ferramentas/prompt-library/prompts/meta/.gitkeep` exists
- [ ] `legal-workbench/ferramentas/prompt-library/tests/__init__.py` exists
- [ ] `legal-workbench/ferramentas/prompt-library/tests/test_models.py` exists
- [ ] `legal-workbench/ferramentas/prompt-library/tests/test_loader.py` exists
- [ ] `legal-workbench/ferramentas/prompt-library/tests/test_search.py` exists
- [ ] `legal-workbench/ferramentas/prompt-library/tests/test_renderer.py` exists
- [ ] `legal-workbench/ferramentas/prompt-library/requirements.txt` exists
- [ ] `pytest tests/ -v` passes all tests
