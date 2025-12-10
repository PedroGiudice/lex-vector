# Prompt Library

Sistema de gerenciamento de templates de prompts para aplicacoes LLM.

## Funcionalidades

- **Carregamento YAML** - Templates definidos em arquivos `.yaml`/`.yml`
- **Validacao Pydantic** - Schema rigoroso com validacao automatica
- **Busca por tags/categoria** - Filtragem rapida de prompts
- **Renderizacao** - Substituicao de variaveis em templates

## Estrutura

```
prompt-library/
├── core/
│   ├── models.py      # Schemas Pydantic (PromptTemplate, PromptVariable, PromptLibrary)
│   ├── loader.py      # Carregador de YAML com validacao
│   ├── renderer.py    # Renderizacao de templates com variaveis
│   └── search.py      # Busca por ID, categoria, tags
├── prompts/           # Diretorio para arquivos YAML de prompts
└── tests/             # Testes unitarios
```

## Uso

```python
from pathlib import Path
from prompt_library.core.loader import load_library
from prompt_library.core.renderer import render_prompt

# Carregar biblioteca
library = load_library(Path("prompts/"))

# Buscar prompt por ID
template = library.get_by_id("hook_error")

# Renderizar com variaveis
rendered = render_prompt(template, {
    "error_message": "MODULE_NOT_FOUND",
    "hook_name": "UserPromptSubmit"
})
```

## Schema do Template (YAML)

```yaml
id: hook_error
titulo: User Prompt Submit Hook Error
categoria: troubleshooting
tags:
  - hooks
  - debug
  - claude-code
descricao: Template para diagnostico de erros em hooks
variaveis:
  - nome: error_message
    label: Mensagem de Erro
    tipo: textarea
    obrigatorio: true
  - nome: hook_name
    label: Nome do Hook
    tipo: select
    opcoes:
      - UserPromptSubmit
      - PreToolUse
      - SessionStart
template: |
  Diagnostique o erro no hook {hook_name}:

  Erro: {error_message}

  Sugira solucoes.
```

## API

### Models

| Classe | Descricao |
|--------|-----------|
| `PromptVariable` | Variavel preenchivel (nome, tipo, obrigatorio) |
| `PromptTemplate` | Template completo com metadados |
| `PromptLibrary` | Colecao de templates com metodos de busca |

### Loader

| Funcao | Descricao |
|--------|-----------|
| `load_prompt(path)` | Carrega um arquivo YAML |
| `load_library(dir)` | Carrega todos os YAMLs de um diretorio |
| `reload_library(dir, lib)` | Hot-reload da biblioteca |

### Search

| Metodo | Descricao |
|--------|-----------|
| `library.get_by_id(id)` | Busca por ID unico |
| `library.get_by_categoria(cat)` | Lista por categoria |
| `library.list_categorias()` | Lista categorias unicas |

## Status

**Backend Only** - Sem interface Streamlit (planejado para v2.7.0)

## Dependencias

- `pydantic>=2.0`
- `pyyaml>=6.0`

---

Ultima atualizacao: 2025-12-10
