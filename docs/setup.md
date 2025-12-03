# Guia de Setup Detalhado

## Pre-requisitos

- Python 3.10+ instalado
- Git configurado com SSH ou HTTPS
- WSL2 (Ubuntu 24.04+) ou Linux nativo
- Espaco em disco para dados (configuravel)

## Setup Inicial em Nova Maquina

### 1. Clone do Repositorio

```bash
mkdir -p ~/claude-work/repos
cd ~/claude-work/repos
git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git
cd Claude-Code-Projetos
```

### 2. Criar Estrutura de Dados

```bash
# Criar diretorios para cada agente
mkdir -p ~/claude-code-data/agentes/oab-watcher/{downloads/cadernos,downloads/busca_oab,logs,outputs/relatorios}
mkdir -p ~/claude-code-data/agentes/djen-tracker/{downloads,logs,outputs}
mkdir -p ~/claude-code-data/agentes/legal-lens/{downloads,logs,outputs}
mkdir -p ~/claude-code-data/agentes/legal-text-extractor/{downloads,logs,outputs}
mkdir -p ~/claude-code-data/agentes/legal-articles-finder/{downloads,logs,outputs}
mkdir -p ~/claude-code-data/agentes/legal-rag/{downloads,logs,outputs}
mkdir -p ~/claude-code-data/shared/{cache,temp}
```

### 3. Setup de Cada Agente

```bash
# Exemplo: oab-watcher
cd agentes/oab-watcher

# Criar ambiente virtual
python3 -m venv .venv

# Ativar ambiente
source .venv/bin/activate

# Verificar ativacao
which python  # Deve mostrar caminho com .venv

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Verificar instalacao
pip list
```

Repita para cada agente conforme necessario.

## Workflow Git

### Maquina A

```bash
# Fazer mudancas
# ...

# Commit
git add .
git commit -m "Descricao das mudancas"
git push
```

### Maquina B

```bash
# Sincronizar
git pull

# Ambiente ja existe? Use-o
cd agentes/oab-watcher
source .venv/bin/activate

# Ambiente nao existe? Recrie
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Troubleshooting

Veja secao Troubleshooting no README.md principal.

## Status

Em desenvolvimento - Sera expandido conforme novos casos de uso
