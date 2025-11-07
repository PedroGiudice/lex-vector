# OAB Watcher

Monitor de publicações do Diário de Justiça Eletrônico (DJEN) por número de OAB.

## Funcionalidades

1. **Busca por OAB**: Consulta publicações associadas a um número de OAB específico
2. **Download Massivo**: Baixa cadernos de tribunais para períodos determinados
3. **Relatórios**: Gera estatísticas dos dados coletados

## Estrutura de Dados

**Código (versionado no Git):**
- `C:\claude-work\repos\Claude-Code-Projetos\agentes\oab-watcher\`

**Dados (HD externo E:\):**
- `E:\claude-code-data\agentes\oab-watcher\downloads\` - PDFs e JSONs baixados
- `E:\claude-code-data\agentes\oab-watcher\logs\` - Logs de execução
- `E:\claude-code-data\agentes\oab-watcher\outputs\` - Relatórios gerados

## Setup

```powershell
# Navegar até diretório
cd agentes\oab-watcher

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

## Execução

```powershell
# Via PowerShell script
.\run_agent.ps1

# Via Python direto
.venv\Scripts\activate
python main.py
```

## API DJEN

Base URL: `https://comunicaapi.pje.jus.br`

**Endpoints utilizados:**
- `/api/v1/comunicacao` - Busca por OAB
- `/api/v1/cadernos` - Lista de cadernos disponíveis

## Configuração

Edite `config.json` para ajustar:
- Timeout de requisições
- Tribunais monitorados
- Caminhos de dados

## Status

🟡 **Em desenvolvimento** - Implementação inicial
