# Guia de Setup Detalhado

## Pré-requisitos

- Python 3.10+ instalado
- Git configurado com SSH ou HTTPS
- HD externo montado em E:\ (para dados)
- PowerShell 5.1+ (Windows)

## Setup Inicial em Nova Máquina

### 1. Clone do Repositório

```powershell
cd C:\claude-work\repos
git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git
cd Claude-Code-Projetos
```

### 2. Criar Estrutura de Dados no HD Externo

```powershell
# Criar diretórios para cada agente
mkdir E:\claude-code-data\agentes\oab-watcher\downloads\cadernos
mkdir E:\claude-code-data\agentes\oab-watcher\downloads\busca_oab
mkdir E:\claude-code-data\agentes\oab-watcher\logs
mkdir E:\claude-code-data\agentes\oab-watcher\outputs\relatorios

mkdir E:\claude-code-data\agentes\djen-tracker\downloads
mkdir E:\claude-code-data\agentes\djen-tracker\logs
mkdir E:\claude-code-data\agentes\djen-tracker\outputs

mkdir E:\claude-code-data\agentes\legal-lens\downloads
mkdir E:\claude-code-data\agentes\legal-lens\logs
mkdir E:\claude-code-data\agentes\legal-lens\outputs

mkdir E:\claude-code-data\shared\cache
mkdir E:\claude-code-data\shared\temp
```

### 3. Setup de Cada Agente

```powershell
# Exemplo: oab-watcher
cd agentes\oab-watcher

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente
.venv\Scripts\activate

# Verificar ativação
where python  # Deve mostrar caminho com .venv

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Verificar instalação
pip list
```

Repita para cada agente conforme necessário.

## Workflow Git

### Máquina A (Trabalho)

```bash
# Fazer mudanças
# ...

# Commit
git add .
git commit -m "Descrição das mudanças"
git push
```

### Máquina B (Casa)

```bash
# Sincronizar
git pull

# Ambiente já existe? Use-o
cd agentes\oab-watcher
.venv\Scripts\activate

# Ambiente não existe? Recrie
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Troubleshooting

Veja seção Troubleshooting no README.md principal.

## Status

🟡 **Em desenvolvimento** - Será expandido conforme novos casos de uso
