# Claude Code Projetos

Sistema de automacao juridica com agentes Python para monitoramento de publicacoes, processamento de documentos legais e analise de dados juridicos. Orquestrado pelo Legal-Braniac, um sistema inteligente de coordenacao multi-agente.

## Visao Geral

### Sistema Multi-Agente
- 7 agentes especializados (monitoramento, analise, extracao de texto, busca de artigos, RAG, design)
- 36 skills funcionais (OCR, parsing, testing, diagramming, documentacao, frontend design)
- 5 comandos utilitarios (fetch, extract, validate, parse, alert)
- Legal-Braniac orchestrator (coordenacao inteligente com auto-discovery)

### Stack Tecnologica
- Python 3.11.14 (agentes e processamento)
- Node.js v22.21.1 (hooks e orquestracao)
- Ubuntu 24.04 LTS (WSL2)
- Git (versionamento)
- Claude Code 2.0 (desenvolvimento assistido por IA)

---

## Arquitetura de 3 Camadas

Este projeto segue uma separacao rigida entre tres camadas (ver DISASTER_HISTORY.md para contexto historico):

### CAMADA 1: CODIGO
- Localizacao: ~/claude-work/repos/Claude-Code-Projetos/
- Conteudo: Codigo-fonte Python/Node.js, configuracoes, documentacao
- Versionamento: Git (obrigatorio)
- Sincronizacao: Via git push/git pull

### CAMADA 2: AMBIENTE
- Localizacao: agentes/*/.venv/ (dentro de cada agente)
- Conteudo: Python interpreter, pacotes instalados via pip
- Versionamento: NUNCA (incluido em .gitignore)
- Recriacao: Via requirements.txt quando necessario

### CAMADA 3: DADOS
- Localizacao: Configuravel via env vars (padrao: ~/claude-code-data/)
- Conteudo: Downloads, logs, outputs, dados processados
- Versionamento: NUNCA
- Backup: Via backup/restore ou transporte fisico

REGRA CRITICA: Codigo SEMPRE em Git. Ambiente SEMPRE local (.venv). Dados NUNCA em Git.

---

## Legal-Braniac - Orquestrador Inteligente

Legal-Braniac e o orquestrador mestre que coordena automaticamente:

### Capabilities
- 7 agentes especializados (legal-braniac, planejamento, desenvolvimento, qualidade, documentacao, analise-dados-legal)
- 36 skills funcionais (OCR, parsing, testing, diagramming, frontend design, etc)
- Auto-discovery (detecta novos agentes/skills automaticamente)
- Delegacao inteligente (tarefa certa para agente certo)
- Execucao paralela (quando subtarefas sao independentes)
- Virtual Agents System (cria agentes temporarios sob demanda)
- Learning System (prompt enhancement com padroes legais)

### Quando Usar

Use quando:
- Tarefa complexa com multiplas fases (ex: "implementar feature X de ponta a ponta")
- Precisa coordenar diferentes dominios (planejamento + codigo + testes + docs)
- Quer execucao paralela eficiente
- Precisa validacao cross-agente

Nao use quando:
- Tarefa simples e atomica (ex: "corrigir typo")
- Ja sabe qual agente especializado invocar diretamente

### Como Invocar

```bash
# Invocacao automatica (Web - SessionStart hook ativo)
# Legal-Braniac detecta complexidade e orquestra automaticamente

# Invocacao explicita
@legal-braniac Implementar feature X com planejamento + codigo + testes + docs

# Invocacao manual (CLI)
# Apenas descreva tarefa complexa que sera reconhecida
```

Guia completo: .claude/LEGAL_BRANIAC_GUIDE.md

---

## Agentes (7)

### 1. oab-watcher
Monitora o Diario Oficial da OAB (Ordem dos Advogados do Brasil).

Features:
- Scraping diario de publicacoes
- Extracao de PDFs
- Parsing de informacoes estruturadas
- Armazenamento em banco de dados local

### 2. djen-tracker
Monitora o Diario de Justica Eletronico (DJe).

Features:
- Monitoramento multi-tribunal (TJ, TRF, TST, etc)
- Filtros por processo/parte
- Alertas configuraveis
- Exportacao JSON/CSV

### 3. legal-lens
Analise aprofundada de publicacoes legais.

Features:
- NLP para categorizacao de documentos
- Extracao de entidades (nomes, datas, valores)
- Sumarizacao de textos longos
- Identificacao de padroes juridicos

### 4. legal-text-extractor
Extracao de texto de documentos PDF com OCR avancado.

Features:
- OCR multi-engine (Tesseract, Google Vision, Azure)
- Pre-processamento de imagens (deskew, denoise)
- Preservacao de estrutura (colunas, tabelas)
- Validacao de qualidade de extracao

### 5. legal-articles-finder
Busca e indexacao de artigos de leis, codigos e jurisprudencia.

Features:
- Indexacao de CF, CPC, CLT, CC
- Busca por numero, ementa, palavra-chave
- Versionamento de legislacao (historico de alteracoes)
- API REST para consulta

### 6. legal-rag
Retrieval-Augmented Generation para questoes juridicas.

Features:
- Vector database (ChromaDB/FAISS)
- Embeddings de textos legais
- Geracao de respostas contextualizadas
- Citacao de fontes

### 7. aesthetic-master
Design system e criacao de componentes frontend.

Features:
- Geracao de design tokens
- Criacao de componentes React/Vue
- Validacao de acessibilidade (WCAG)
- Exportacao de estilos CSS/Tailwind

---

## Skills (36 funcionais)

### Documentacao (7)
- architecture-diagram-creator - Diagramas de arquitetura visuais
- codebase-documenter - Documentacao automatica de codigo
- flowchart-creator - Fluxogramas de processos
- technical-doc-creator - Documentacao tecnica com exemplos
- docx - Geracao de documentos Word
- pdf - Manipulacao de PDFs
- xlsx - Geracao de planilhas Excel

### Desenvolvimento e QA (10)
- ai-test-reviewer - Revisao de testes por IA
- api-mocking - Mocking de APIs para testes
- comprehensive-testing - Testes end-to-end
- test-generator - Geracao automatica de testes
- api-documentation - Documentacao de APIs (OpenAPI)
- code-review-assistant - Revisao de codigo automatizada
- debugging-expert - Debugging avancado
- refactoring-helper - Refatoracao guiada
- performance-optimizer - Otimizacao de performance
- security-auditor - Auditoria de seguranca

### Design e Frontend (8)
- frontend-design - Design system completo
- component-library-creator - Criacao de bibliotecas de componentes
- responsive-layout-builder - Layouts responsivos
- accessibility-checker - Validacao de acessibilidade
- css-optimizer - Otimizacao de CSS
- icon-generator - Geracao de icones
- color-palette-creator - Paletas de cores
- typography-system - Sistema tipografico

### Analise e Processamento (11)
- deep-parser - Parser profundo de estruturas complexas
- ocr-pro - OCR avancado de documentos
- sign-recognition - Reconhecimento de assinaturas
- data-extractor - Extracao de dados estruturados
- entity-recognizer - Reconhecimento de entidades (NER)
- sentiment-analyzer - Analise de sentimento
- text-classifier - Classificacao de textos
- similarity-finder - Busca por similaridade
- pattern-detector - Detecao de padroes
- anomaly-detector - Detecao de anomalias
- data-validator - Validacao de dados

---

## Comandos Utilitarios (5)

### 1. fetch-doc
Baixa documentos de fontes especificas (URLs, APIs).

```bash
cd comandos/fetch-doc
python fetch.py --url <url> --output <path>
```

### 2. extract-core
Extrai informacoes essenciais de documentos (metadados, texto, entidades).

```bash
cd comandos/extract-core
python extract.py --input <pdf> --fields "data,partes,processo"
```

### 3. validate-id
Valida identificadores brasileiros (CPF, CNPJ, OAB, CNH).

```bash
cd comandos/validate-id
python validate.py --cpf 123.456.789-00
```

### 4. parse-legal
Parser de textos juridicos (leis, sentencas, acordaos).

```bash
cd comandos/parse-legal
python parse.py --input <txt> --type sentenca
```

### 5. send-alert
Envia alertas via email/webhook quando eventos ocorrem.

```bash
cd comandos/send-alert
python alert.py --webhook <url> --message "Publicacao nova detectada"
```

---

## Setup e Instalacao

### Pre-requisitos
- WSL2 (Ubuntu 24.04 LTS) ou Linux
- Python 3.11+ (python3 --version)
- Node.js v22+ (node --version)
- Git (git --version)

### Clone e Setup

```bash
# 1. Clone o repositorio
git clone <repository-url> ~/claude-work/repos/Claude-Code-Projetos
cd ~/claude-work/repos/Claude-Code-Projetos

# 2. Crie estrutura de dados (configuravel via env vars)
mkdir -p ~/claude-code-data/agentes/{oab-watcher,djen-tracker,legal-lens,legal-text-extractor,legal-articles-finder,legal-rag,aesthetic-master}/{downloads,logs,outputs}
mkdir -p ~/claude-code-data/shared/{cache,temp}

# 3. Setup venv global (opcional - para linting, testes compartilhados)
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Setup de cada agente (exemplo: oab-watcher)
cd agentes/oab-watcher
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Verificar setup
which python  # Deve apontar para agentes/oab-watcher/.venv/bin/python
pip list      # Deve mostrar apenas pacotes do projeto
```

---

## Como Usar

### Executar um Agente

```bash
# Navegue para o agente
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/oab-watcher

# Ative venv
source .venv/bin/activate

# Execute
python main.py

# Verificar logs
tail -f ~/claude-code-data/agentes/oab-watcher/logs/latest.log
```

### Usar Legal-Braniac (Web)

```
# SessionStart hook invoca automaticamente
# Apenas descreva tarefa complexa:

"Implementar sistema de busca de jurisprudencia com:
1. Crawler de tribunais
2. Parser de acordaos
3. Indexacao com embeddings
4. API REST para consulta
5. Testes unitarios e integracao"

# Legal-Braniac coordena:
# - planejamento-legal (desenha arquitetura)
# - desenvolvimento (implementa codigo)
# - qualidade-codigo (escreve testes)
# - documentacao (cria docs tecnicos)
```

### Usar Legal-Braniac (CLI)

```bash
# Invocacao manual do hook
node .claude/hooks/invoke-legal-braniac-hybrid.js

# Ou apenas descreva tarefa complexa no prompt
```

---

## Desenvolvimento

### Adicionar Novo Agente

```bash
# 1. Criar estrutura de diretorios
cd ~/claude-work/repos/Claude-Code-Projetos
mkdir -p agentes/novo-agente
cd agentes/novo-agente

# 2. Criar venv
python3 -m venv .venv
source .venv/bin/activate

# 3. Criar arquivos basicos
touch main.py config.json requirements.txt README.md
touch .gitignore

# 4. Adicionar ao .gitignore
echo ".venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore

# 5. Instalar dependencias base
pip install requests beautifulsoup4 pydantic
pip freeze > requirements.txt

# 6. Criar estrutura de dados
mkdir -p ~/claude-code-data/agentes/novo-agente/{downloads,logs,outputs}

# 7. Commit
git add agentes/novo-agente/
git commit -m "feat: adiciona agente novo-agente"
git push
```

### Adicionar Nova Skill

```bash
# 1. Criar diretorio da skill
cd ~/claude-work/repos/Claude-Code-Projetos/skills
mkdir nova-skill
cd nova-skill

# 2. Criar SKILL.md (OBRIGATORIO para ser funcional)
cat > SKILL.md << 'EOF'
# Nova Skill

Descricao da skill.

## Uso

```
[prompt example]
```

## Capabilities

- Feature 1
- Feature 2
EOF

# 3. Criar implementacao (se necessario)
touch skill.py

# 4. Testar auto-discovery
# Legal-Braniac detecta automaticamente na proxima execucao

# 5. Commit
git add skills/nova-skill/
git commit -m "feat: adiciona skill nova-skill"
git push
```

---

## Estrutura de Diretorios

```
Claude-Code-Projetos/
├── .git/
├── .gitignore
├── README.md                  # Este arquivo
├── CLAUDE.md                  # Instrucoes para Claude Code
├── DISASTER_HISTORY.md        # Licoes aprendidas
├── requirements.txt           # Dependencias globais (venv raiz)
│
├── .claude/                   # Configuracao Claude Code
│   ├── agents/                # Agentes especializados (6)
│   ├── hooks/                 # Hooks (10 total)
│   ├── settings.json          # Configuracao de hooks
│   ├── LEGAL_BRANIAC_GUIDE.md # Guia completo do orquestrador
│   └── README_SKILLS.md       # Documentacao de skills
│
├── agentes/                   # Agentes autonomos (7)
│   ├── oab-watcher/
│   ├── djen-tracker/
│   ├── legal-lens/
│   ├── legal-text-extractor/
│   ├── legal-articles-finder/
│   ├── legal-rag/
│   └── aesthetic-master/
│
├── comandos/                  # Comandos utilitarios (5)
│   ├── fetch-doc/
│   ├── extract-core/
│   ├── validate-id/
│   ├── parse-legal/
│   └── send-alert/
│
├── skills/                    # Skills customizadas (36 funcionais)
│   ├── ocr-pro/
│   ├── deep-parser/
│   ├── frontend-design/
│   └── ... (36 total)
│
├── shared/                    # Codigo compartilhado
│   ├── utils/
│   │   ├── logging_config.py
│   │   ├── path_utils.py
│   │   └── __init__.py
│   └── models/
│       ├── publicacao.py
│       └── __init__.py
│
└── docs/                      # Documentacao tecnica
    ├── architecture.md
    └── setup.md
```

---

## Troubleshooting

### "ModuleNotFoundError" ao executar agente

Causa: Ambiente virtual nao ativado ou pacotes nao instalados.

Solucao:
```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/<nome-agente>
source .venv/bin/activate
pip install -r requirements.txt
```

### "FileNotFoundError" ao acessar dados

Causa: Estrutura de diretorios de dados nao criada.

Solucao:
```bash
# Criar estrutura de dados
mkdir -p ~/claude-code-data/agentes/<nome-agente>/{downloads,logs,outputs}

# Verificar se existe
ls -la ~/claude-code-data/agentes/<nome-agente>/
```

### Python aponta para versao global ao inves de .venv

Causa: Ambiente virtual nao ativado corretamente.

Solucao:
```bash
# Ativar venv
source .venv/bin/activate

# Verificar
which python  # Deve mostrar caminho com .venv
python --version  # Deve mostrar Python 3.11+
```

### Git reclama de arquivos nao rastreados em .venv/

Causa: .gitignore nao esta funcionando ou .venv foi commitado anteriormente.

Solucao:
```bash
# Se .venv esta no git (NAO DEVE ESTAR):
git rm -r --cached agentes/*/.venv
git rm -r --cached .venv
git commit -m "remove: remove ambientes virtuais do Git"

# Verificar .gitignore inclui:
# .venv/
# venv/
# __pycache__/
# *.pyc
```

### Hooks nao executam automaticamente

Causa: hooks desabilitados ou configuracao incorreta.

Solucao:
```bash
# Verificar configuracao
cat .claude/settings.json | jq '.hooks'

# Testar hook manualmente
node .claude/hooks/invoke-legal-braniac-hybrid.js

# Verificar logs
cat ~/.vibe-log/hooks.log | tail -50
```

---

## Regras Imperativas

1. NUNCA coloque codigo em ~/claude-code-data/ - Codigo vai para ~/claude-work/repos/ e Git
2. NUNCA coloque dados grandes no Git - Dados vao para ~/claude-code-data/
3. SEMPRE use ambiente virtual (.venv) - Sem excecoes
4. SEMPRE ative .venv antes de executar Python - Evita contaminacao global
5. SEMPRE faca git commit ao fim do trabalho - Manter codigo versionado e sincronizado
6. NUNCA use caminhos absolutos hardcoded - Use path_utils.py ou env vars
7. NUNCA commite .venv/ no Git - Verifique .gitignore
8. SEMPRE retorne ao diretorio raiz apos cd - Evita quebrar hooks (ver CLAUDE.md)

---

## Ambientes Suportados

### Claude Code Web (Linux)
- Status: TOTALMENTE FUNCIONAL
- SessionStart hooks: Ativos (auto-invocacao Legal-Braniac)
- Limitacoes: Sem statusline nativa (arquitetural)

### WSL2 CLI (Ubuntu 24.04)
- Status: TOTALMENTE FUNCIONAL
- SessionStart hooks: Ativos
- Features avancadas: Statusline, vibe-log Gordon

### Windows CLI (Casa/Pessoal)
- Status: FUNCIONAL (invocacao manual)
- SessionStart hooks: Desabilitados (prevencao EPERM)

### Windows CLI (Corporativo)
- Status: DESABILITADO (bug EPERM loop)
- Motivo: GPOs corporativas bloqueiam .claude.json.lock
- Workaround: Use Claude Code Web

---

## Documentacao Adicional

- .claude/LEGAL_BRANIAC_GUIDE.md - Guia completo do orquestrador
- .claude/README_SKILLS.md - Documentacao das 36 skills funcionais
- DISASTER_HISTORY.md - Historico de problemas arquiteturais
- CLAUDE.md - Instrucoes para Claude Code (working directory management, 3-layer architecture)
- WSL_SETUP.md - Guia de setup WSL2 (referencia tecnica)
- QUICK-REFERENCE.md - Comandos essenciais para uso diario
- docs/architecture.md - Detalhes da arquitetura do sistema
- docs/setup.md - Guia de setup passo-a-passo detalhado

---

## Licenca

MIT License - Veja LICENSE para detalhes.

---

## Autor

PedroGiudice - 2025

Projeto de automacao juridica desenvolvido com Claude Code e Python.

---

Ultima atualizacao: 2025-12-02
Ambiente: WSL2 Ubuntu 24.04 LTS
Diretorio: ~/claude-work/repos/Claude-Code-Projetos
