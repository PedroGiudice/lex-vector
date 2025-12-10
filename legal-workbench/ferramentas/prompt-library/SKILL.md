---
name: prompt-library
description: Gerenciamento de templates de prompts. Use para buscar, renderizar e criar prompts estruturados a partir de templates YAML. Ideal para troubleshooting, analise juridica e tarefas recorrentes.
---

# Prompt Library

Sistema de gerenciamento de templates de prompts para tarefas recorrentes.

## Quando Usar

- Buscar prompts por categoria ou tags
- Renderizar templates com variaveis customizadas
- Criar novos templates de prompt
- Listar prompts disponiveis

## Localizacao

```
/home/user/Claude-Code-Projetos/legal-workbench/ferramentas/prompt-library/
├── core/
│   ├── models.py      # Schemas Pydantic
│   ├── loader.py      # Carregador YAML
│   ├── renderer.py    # Renderizacao
│   └── search.py      # Busca
└── prompts/           # Templates YAML
```

## Uso Rapido

### Carregar e Buscar Prompts

```python
from pathlib import Path
import sys
sys.path.insert(0, "/home/user/Claude-Code-Projetos/legal-workbench/ferramentas/prompt-library")

from core.loader import load_library
from core.renderer import render_prompt

# Carregar biblioteca
prompts_dir = Path("/home/user/Claude-Code-Projetos/legal-workbench/ferramentas/prompt-library/prompts")
library = load_library(prompts_dir)

# Listar categorias
print(library.list_categorias())

# Buscar por ID
template = library.get_by_id("hook_error")

# Buscar por categoria
templates = library.get_by_categoria("troubleshooting")
```

### Renderizar com Variaveis

```python
rendered = render_prompt(template, {
    "error_message": "MODULE_NOT_FOUND",
    "hook_name": "UserPromptSubmit"
})
print(rendered)
```

## Criar Novo Template

Crie arquivo `.yaml` em `prompts/<categoria>/`:

```yaml
id: novo_template
titulo: Nome Legivel do Template
categoria: troubleshooting
tags:
  - debug
  - hooks
descricao: Descricao curta do proposito
variaveis:
  - nome: variavel1
    label: Label na UI
    tipo: text  # text, textarea, select
    obrigatorio: true
  - nome: variavel2
    label: Opcao
    tipo: select
    opcoes:
      - opcao1
      - opcao2
template: |
  Seu prompt aqui com {variavel1} e {variavel2}.
```

## Categorias Comuns

| Categoria | Uso |
|-----------|-----|
| `troubleshooting` | Diagnostico de erros |
| `legal` | Analise juridica |
| `code-review` | Revisao de codigo |
| `documentation` | Geracao de docs |

## Integracao com Workflows

1. **Buscar prompt** → `library.get_by_id()`
2. **Coletar variaveis** → UI ou input direto
3. **Renderizar** → `render_prompt(template, vars)`
4. **Executar** → Usar prompt renderizado

## Dependencias

Requer ambiente com:
- `pydantic>=2.0`
- `pyyaml>=6.0`

Ativar venv se necessario:
```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/ferramentas/prompt-library
source .venv/bin/activate  # se existir
```
