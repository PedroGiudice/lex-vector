# Claude Code Projetos

Sistema de automação jurídica com agentes Python para monitoramento de publicações e processamento de documentos legais.

## Arquitetura Fundamental

Este projeto segue uma separação rígida entre três camadas:

### CAMADA 1: CÓDIGO (C:\claude-work\repos\Claude-Code-Projetos\)
- **Localização:** C:\claude-work\repos\Claude-Code-Projetos\
- **Conteúdo:** Código-fonte Python, configurações, documentação
- **Versionamento:** Git (obrigatório)
- **Portabilidade:** Sincronizado via git push/pull entre máquinas

### CAMADA 2: AMBIENTE (C:\claude-work\repos\Claude-Code-Projetos\agentes\*\.venv\)
- **Localização:** Dentro de cada projeto (ex: agentes/oab-watcher/.venv/)
- **Conteúdo:** Interpretador Python, pacotes instalados
- **Versionamento:** NUNCA (incluído em .gitignore)
- **Portabilidade:** Recriado via requirements.txt em cada máquina

### CAMADA 3: DADOS (E:\claude-code-data\)
- **Localização:** E:\claude-code-data\ (HD externo)
- **Conteúdo:** Downloads, logs, outputs, dados processados
- **Versionamento:** NUNCA
- **Portabilidade:** Apenas via transporte físico do HD

**REGRA CRÍTICA:** Código NUNCA vai para E:\. Dados NUNCA vão para Git.

## Estrutura de Diretórios

### Código-fonte (neste repositório)

```
Claude-Code-Projetos/
├── .git/
├── .gitignore
├── README.md
├── DISASTER_HISTORY.md
├── CLAUDE.md
│
├── agentes/                    # Agentes autônomos de monitoramento
│   ├── oab-watcher/           # Monitora Diário da OAB
│   │   ├── .venv/             # Ambiente virtual (não versionado)
│   │   ├── .gitignore
│   │   ├── requirements.txt
│   │   ├── run_agent.ps1
│   │   ├── main.py
│   │   ├── config.json
│   │   └── README.md
│   │
│   ├── djen-tracker/          # Monitora Diário de Justiça Eletrônico
│   │   ├── .venv/
│   │   ├── requirements.txt
│   │   ├── run_agent.ps1
│   │   ├── main.py
│   │   └── README.md
│   │
│   └── legal-lens/            # Análise de publicações legais
│       ├── .venv/
│       ├── requirements.txt
│       ├── run_agent.ps1
│       ├── main.py
│       └── README.md
│
├── comandos/                   # Comandos utilitários reutilizáveis
│   ├── fetch-doc/             # Baixa documentos de fontes específicas
│   ├── extract-core/          # Extrai informações核心 de documentos
│   ├── validate-id/           # Valida identificadores (CPF, CNPJ, OAB, etc)
│   ├── parse-legal/           # Parser de textos jurídicos
│   └── send-alert/            # Envia alertas via email/webhook
│
├── skills/                     # Skills para Claude Code
│   ├── ocr-pro/               # OCR avançado de documentos
│   ├── deep-parser/           # Parser profundo de estruturas complexas
│   └── sign-recognition/      # Reconhecimento de assinaturas
│
├── shared/                     # Código compartilhado entre projetos
│   ├── utils/
│   │   ├── logging_config.py  # Configuração padronizada de logs
│   │   ├── path_utils.py      # Gerenciamento de caminhos C:\ vs E:\
│   │   └── __init__.py
│   │
│   └── models/
│       ├── publicacao.py      # Modelo de dados de publicações
│       └── __init__.py
│
└── docs/
    ├── architecture.md        # Detalhes arquiteturais
    └── setup.md               # Guia de setup detalhado
```

### Dados (HD externo E:\)

```
E:\claude-code-data/
│
├── agentes/
│   ├── oab-watcher/
│   │   ├── downloads/         # PDFs baixados
│   │   ├── logs/              # Logs de execução
│   │   └── outputs/           # Resultados processados
│   │
│   ├── djen-tracker/
│   │   ├── downloads/
│   │   ├── logs/
│   │   └── outputs/
│   │
│   └── legal-lens/
│       ├── downloads/
│       ├── logs/
│       └── outputs/
│
└── shared/
    ├── cache/                 # Cache compartilhado
    └── temp/                  # Arquivos temporários
```

## Setup Inicial

### Pré-requisitos
- Python 3.10+ instalado
- Git configurado
- HD externo montado em E:\ (para dados)
- PowerShell 5.1+ (para scripts .ps1)

### Setup do Projeto

```powershell
# 1. Clone o repositório
cd C:\claude-work\repos
git clone <repository-url> Claude-Code-Projetos
cd Claude-Code-Projetos

# 2. Crie estrutura de dados no HD externo
mkdir E:\claude-code-data\agentes\oab-watcher\downloads
mkdir E:\claude-code-data\agentes\oab-watcher\logs
mkdir E:\claude-code-data\agentes\oab-watcher\outputs
mkdir E:\claude-code-data\agentes\djen-tracker\downloads
mkdir E:\claude-code-data\agentes\djen-tracker\logs
mkdir E:\claude-code-data\agentes\djen-tracker\outputs
mkdir E:\claude-code-data\agentes\legal-lens\downloads
mkdir E:\claude-code-data\agentes\legal-lens\logs
mkdir E:\claude-code-data\agentes\legal-lens\outputs
mkdir E:\claude-code-data\shared\cache
mkdir E:\claude-code-data\shared\temp

# 3. Setup de cada agente (exemplo: oab-watcher)
cd agentes\oab-watcher
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verificar setup
where python  # Deve apontar para .venv\Scripts\python.exe
pip list      # Deve mostrar apenas pacotes do projeto
```

### Setup em Nova Máquina

```powershell
# 1. Clone do Git
cd C:\claude-work\repos
git clone <repository-url> Claude-Code-Projetos
cd Claude-Code-Projetos

# 2. Conecte HD externo em E:\
# (dados já estão lá do uso anterior)

# 3. Recrie ambientes virtuais
cd agentes\oab-watcher
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Repita para cada agente conforme necessário
```

## Executando Agentes

### Via PowerShell Script (Recomendado)

```powershell
cd agentes\oab-watcher
.\run_agent.ps1
```

### Via Linha de Comando Manual

```powershell
cd agentes\oab-watcher
.venv\Scripts\activate
python main.py
```

## Workflow Git

### Ao Fim do Dia de Trabalho

```bash
git add .
git commit -m "Adiciona [feature/correção/refatoração]"
git push
```

### Ao Iniciar em Outra Máquina

```bash
cd C:\claude-work\repos\Claude-Code-Projetos
git pull
```

**IMPORTANTE:** Apenas código vai para Git. Dados permanecem em E:\ e são acessados localmente.

## Troubleshooting

### "ModuleNotFoundError" ao executar agente
**Causa:** Ambiente virtual não ativado ou pacotes não instalados.
**Solução:**
```powershell
cd agentes\<nome-agente>
.venv\Scripts\activate
pip install -r requirements.txt
```

### "FileNotFoundError" ao acessar dados
**Causa:** HD externo não montado em E:\ ou estrutura de diretórios não criada.
**Solução:**
```powershell
# Verificar se E:\ existe
dir E:\

# Recriar estrutura se necessário (veja Setup Inicial > passo 2)
```

### Python aponta para versão global ao invés de .venv
**Causa:** Ambiente virtual não ativado corretamente.
**Solução:**
```powershell
# PowerShell
.venv\Scripts\activate

# CMD
.venv\Scripts\activate.bat

# Verificar
where python  # Deve mostrar caminho com .venv
```

### Git reclama de arquivos não rastreados em .venv/
**Causa:** .gitignore não está funcionando ou .venv foi commitado anteriormente.
**Solução:**
```bash
# Se .venv está no git (NÃO DEVE ESTAR):
git rm -r --cached agentes/*/venv
git commit -m "Remove ambientes virtuais do Git"

# Verificar .gitignore inclui:
# .venv/
# venv/
# __pycache__/
```

## Regras Imperativas

1. **NUNCA coloque código em E:\** - Código vai para C:\ e Git
2. **NUNCA coloque dados grandes no Git** - Dados vão para E:\
3. **SEMPRE use ambiente virtual (.venv)** - Sem exceções
4. **SEMPRE ative .venv antes de executar Python** - Evita contaminação global
5. **SEMPRE faça git commit ao fim do dia** - Sincronização entre máquinas
6. **NUNCA use caminhos absolutos hardcoded** - Use caminhos relativos ou variáveis de ambiente
7. **NUNCA commite .venv/ no Git** - Verifique .gitignore

## Plugins do Claude Code Marketplace Necessários

Se você usa Claude Code com este projeto, instale manualmente em cada máquina:

- **episodic-memory** - Para contexto de longo prazo
- **superpowers** - Para execução de comandos avançados
- **web-scraper** (se aplicável) - Para coleta de dados web

**IMPORTANTE:** Plugins NÃO vão para Git. Instale via Marketplace em cada máquina.

## Documentação Adicional

- **DISASTER_HISTORY.md** - Histórico de 3 dias de problemas arquiteturais (leia para NUNCA repetir)
- **CLAUDE.md** - Guia para futuras instâncias do Claude Code
- **docs/architecture.md** - Detalhes da arquitetura do sistema
- **docs/setup.md** - Guia de setup passo-a-passo detalhado

## Licença

MIT License - Veja LICENSE para detalhes.

## Autor

PedroGiudice - 2025
