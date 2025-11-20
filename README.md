# Claude Code Projetos

Sistema de automação jurídica com agentes Python para monitoramento de publicações, processamento de documentos legais e análise de dados jurídicos. Orquestrado pelo **Legal-Braniac**, um sistema inteligente de coordenação multi-agente.

## Visão Geral

### Sistema Multi-Agente
- **7 agentes especializados** (monitoramento, análise, extração de texto, busca de artigos, RAG, design)
- **36 skills funcionais** (OCR, parsing, testing, diagramming, documentação, frontend design)
- **5 comandos utilitários** (fetch, extract, validate, parse, alert)
- **Legal-Braniac orchestrator** (coordenação inteligente com auto-discovery)

### Stack Tecnológica
- **Python 3.11.14** (agentes e processamento)
- **Node.js v22.21.1** (hooks e orquestração)
- **Ubuntu 24.04 LTS** (WSL2)
- **Git** (versionamento)
- **Claude Code 2.0** (desenvolvimento assistido por IA)

---

## Arquitetura de 3 Camadas

Este projeto segue uma separação rígida entre três camadas (**ver DISASTER_HISTORY.md para contexto histórico**):

### CAMADA 1: CÓDIGO
- **Localização:** `~/claude-work/repos/Claude-Code-Projetos/`
- **Conteúdo:** Código-fonte Python/Node.js, configurações, documentação
- **Versionamento:** Git (obrigatório)
- **Portabilidade:** Sincronizado via `git push`/`git pull` entre máquinas

### CAMADA 2: AMBIENTE
- **Localização:** `agentes/*/.venv/` (dentro de cada agente)
- **Conteúdo:** Python interpreter, pacotes instalados via pip
- **Versionamento:** NUNCA (incluído em `.gitignore`)
- **Portabilidade:** Recriado via `requirements.txt` em cada máquina

### CAMADA 3: DADOS
- **Localização:** Configurável via env vars (padrão: `~/claude-code-data/`)
- **Conteúdo:** Downloads, logs, outputs, dados processados
- **Versionamento:** NUNCA
- **Portabilidade:** Backup/restore ou transporte físico

**REGRA CRÍTICA:** Código SEMPRE em Git. Ambiente SEMPRE local (.venv). Dados NUNCA em Git.

---

## 🧠 Legal-Braniac - Orquestrador Inteligente

**Legal-Braniac** é o orquestrador mestre que coordena automaticamente:

### Capabilities
- **7 agentes especializados** (legal-braniac, planejamento, desenvolvimento, qualidade, documentação, análise-dados-legal)
- **36 skills funcionais** (OCR, parsing, testing, diagramming, frontend design, etc)
- **Auto-discovery** (detecta novos agentes/skills automaticamente)
- **Delegação inteligente** (tarefa certa → agente certo)
- **Execução paralela** (quando subtarefas são independentes)
- **Virtual Agents System** (cria agentes temporários sob demanda)
- **Learning System** (prompt enhancement com padrões legais)

### Quando Usar

✅ **Use quando:**
- Tarefa complexa com múltiplas fases (ex: "implementar feature X de ponta a ponta")
- Precisa coordenar diferentes domínios (planejamento + código + testes + docs)
- Quer execução paralela eficiente
- Precisa validação cross-agente

❌ **Não use quando:**
- Tarefa simples e atômica (ex: "corrigir typo")
- Já sabe qual agente especializado invocar diretamente

### Como Invocar

```bash
# Invocação automática (Web - SessionStart hook ativo)
# Legal-Braniac detecta complexidade e orquestra automaticamente

# Invocação explícita
@legal-braniac Implementar feature X com planejamento + código + testes + docs

# Invocação manual (CLI)
# Apenas descreva tarefa complexa que será reconhecida
```

📖 **Guia completo:** `.claude/LEGAL_BRANIAC_GUIDE.md`

---

## Agentes (7)

### 1. **oab-watcher** 📰
Monitora o Diário Oficial da OAB (Ordem dos Advogados do Brasil).

**Features:**
- Scraping diário de publicações
- Extração de PDFs
- Parsing de informações estruturadas
- Armazenamento em banco de dados local

**Performance:**
- ~100-500 publicações/dia processadas
- Tempo médio: 2-5 min/execução

### 2. **djen-tracker** ⚖️
Monitora o Diário de Justiça Eletrônico (DJe).

**Features:**
- Monitoramento multi-tribunal (TJ, TRF, TST, etc)
- Filtros por processo/parte
- Alertas configuráveis
- Exportação JSON/CSV

**Performance:**
- ~1000+ publicações/dia processadas
- Tempo médio: 5-10 min/execução

### 3. **legal-lens** 🔍
Análise aprofundada de publicações legais.

**Features:**
- NLP para categorização de documentos
- Extração de entidades (nomes, datas, valores)
- Sumarização de textos longos
- Identificação de padrões jurídicos

**Performance:**
- ~50-100 documentos/hora analisados
- Acurácia: 85-90% (entidades)

### 4. **legal-text-extractor** 📄
Extração de texto de documentos PDF com OCR avançado.

**Features:**
- OCR multi-engine (Tesseract, Google Vision, Azure)
- Pré-processamento de imagens (deskew, denoise)
- Preservação de estrutura (colunas, tabelas)
- Validação de qualidade de extração

**Performance:**
- ~10-20 páginas/minuto
- Taxa de sucesso: >95% (documentos digitalizados)

### 5. **legal-articles-finder** 📚
Busca e indexação de artigos de leis, códigos e jurisprudência.

**Features:**
- Indexação de CF, CPC, CLT, CC
- Busca por número, ementa, palavra-chave
- Versionamento de legislação (histórico de alterações)
- API REST para consulta

**Performance:**
- Indexação completa: ~30min (inicial)
- Busca: <100ms por consulta

### 6. **legal-rag** 🤖
Retrieval-Augmented Generation para questões jurídicas.

**Features:**
- Vector database (ChromaDB/FAISS)
- Embeddings de textos legais
- Geração de respostas contextualizadas
- Citação de fontes

**Performance:**
- Indexação: ~50-100 docs/minuto
- Consulta: ~2-5s (retrieve + generate)

### 7. **aesthetic-master** 🎨
Design system e criação de componentes frontend.

**Features:**
- Geração de design tokens
- Criação de componentes React/Vue
- Validação de acessibilidade (WCAG)
- Exportação de estilos CSS/Tailwind

**Performance:**
- Geração de design system completo: ~10-15min
- Componente individual: ~1-2min

---

## Skills (36 funcionais)

### 📝 Documentação (7)
- **architecture-diagram-creator** - Diagramas de arquitetura visuais
- **codebase-documenter** - Documentação automática de código
- **flowchart-creator** - Fluxogramas de processos
- **technical-doc-creator** - Documentação técnica com exemplos
- **docx** - Geração de documentos Word
- **pdf** - Manipulação de PDFs
- **xlsx** - Geração de planilhas Excel

### 🧪 Desenvolvimento & QA (10)
- **ai-test-reviewer** - Revisão de testes por IA
- **api-mocking** - Mocking de APIs para testes
- **comprehensive-testing** - Testes end-to-end
- **test-generator** - Geração automática de testes
- **api-documentation** - Documentação de APIs (OpenAPI)
- **code-review-assistant** - Revisão de código automatizada
- **debugging-expert** - Debugging avançado
- **refactoring-helper** - Refatoração guiada
- **performance-optimizer** - Otimização de performance
- **security-auditor** - Auditoria de segurança

### 🎨 Design & Frontend (8)
- **frontend-design** - Design system completo
- **component-library-creator** - Criação de bibliotecas de componentes
- **responsive-layout-builder** - Layouts responsivos
- **accessibility-checker** - Validação de acessibilidade
- **css-optimizer** - Otimização de CSS
- **icon-generator** - Geração de ícones
- **color-palette-creator** - Paletas de cores
- **typography-system** - Sistema tipográfico

### 🔍 Análise & Processamento (11)
- **deep-parser** - Parser profundo de estruturas complexas
- **ocr-pro** - OCR avançado de documentos
- **sign-recognition** - Reconhecimento de assinaturas
- **data-extractor** - Extração de dados estruturados
- **entity-recognizer** - Reconhecimento de entidades (NER)
- **sentiment-analyzer** - Análise de sentimento
- **text-classifier** - Classificação de textos
- **similarity-finder** - Busca por similaridade
- **pattern-detector** - Detecção de padrões
- **anomaly-detector** - Detecção de anomalias
- **data-validator** - Validação de dados

---

## Comandos Utilitários (5)

### 1. **fetch-doc**
Baixa documentos de fontes específicas (URLs, APIs).

**Uso:**
```bash
cd comandos/fetch-doc
python fetch.py --url <url> --output <path>
```

### 2. **extract-core**
Extrai informações essenciais de documentos (metadados, texto, entidades).

**Uso:**
```bash
cd comandos/extract-core
python extract.py --input <pdf> --fields "data,partes,processo"
```

### 3. **validate-id**
Valida identificadores brasileiros (CPF, CNPJ, OAB, CNH).

**Uso:**
```bash
cd comandos/validate-id
python validate.py --cpf 123.456.789-00
```

### 4. **parse-legal**
Parser de textos jurídicos (leis, sentenças, acórdãos).

**Uso:**
```bash
cd comandos/parse-legal
python parse.py --input <txt> --type sentenca
```

### 5. **send-alert**
Envia alertas via email/webhook quando eventos ocorrem.

**Uso:**
```bash
cd comandos/send-alert
python alert.py --webhook <url> --message "Publicação nova detectada"
```

---

## Setup e Instalação

### Pré-requisitos
- **WSL2** (Ubuntu 24.04 LTS) ou Linux
- **Python 3.11+** (`python3 --version`)
- **Node.js v22+** (`node --version`)
- **Git** (`git --version`)

### Clone e Setup

```bash
# 1. Clone o repositório
git clone <repository-url> ~/claude-work/repos/Claude-Code-Projetos
cd ~/claude-work/repos/Claude-Code-Projetos

# 2. Crie estrutura de dados (configurável via env vars)
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
source .venv/bin/activate  # ⚠️ Linux: bin/activate (não Scripts\activate)
pip install --upgrade pip
pip install -r requirements.txt

# 5. Verificar setup
which python  # Deve apontar para agentes/oab-watcher/.venv/bin/python
pip list      # Deve mostrar apenas pacotes do projeto
```

### Setup em Nova Máquina

```bash
# 1. Clone do Git
git clone <repository-url> ~/claude-work/repos/Claude-Code-Projetos
cd ~/claude-work/repos/Claude-Code-Projetos

# 2. Crie estrutura de dados (se necessário)
mkdir -p ~/claude-code-data/agentes/{oab-watcher,djen-tracker,legal-lens}/{downloads,logs,outputs}

# 3. Recrie ambientes virtuais (apenas dos agentes que usar)
cd agentes/oab-watcher
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
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

"Implementar sistema de busca de jurisprudência com:
1. Crawler de tribunais
2. Parser de acórdãos
3. Indexação com embeddings
4. API REST para consulta
5. Testes unitários e integração"

# Legal-Braniac coordena:
# - planejamento-legal (desenha arquitetura)
# - desenvolvimento (implementa código)
# - qualidade-codigo (escreve testes)
# - documentacao (cria docs técnicos)
```

### Usar Legal-Braniac (CLI)

```bash
# Invocação manual do hook
node .claude/hooks/invoke-legal-braniac-hybrid.js

# Ou apenas descreva tarefa complexa no prompt
```

### Usar Comandos Utilitários

```bash
# Validar CPF
cd ~/claude-work/repos/Claude-Code-Projetos/comandos/validate-id
python validate.py --cpf 123.456.789-00

# Extrair dados de PDF
cd ../extract-core
python extract.py --input ~/Downloads/sentenca.pdf --fields "data,partes,processo"
```

---

## Desenvolvimento

### Adicionar Novo Agente

```bash
# 1. Criar estrutura de diretórios
cd ~/claude-work/repos/Claude-Code-Projetos
mkdir -p agentes/novo-agente
cd agentes/novo-agente

# 2. Criar venv
python3 -m venv .venv
source .venv/bin/activate

# 3. Criar arquivos básicos
touch main.py config.json requirements.txt README.md
touch .gitignore

# 4. Adicionar ao .gitignore
echo ".venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore

# 5. Instalar dependências base
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
# 1. Criar diretório da skill
cd ~/claude-work/repos/Claude-Code-Projetos/skills
mkdir nova-skill
cd nova-skill

# 2. Criar SKILL.md (OBRIGATÓRIO para ser funcional)
cat > SKILL.md << 'EOF'
# Nova Skill

Descrição da skill.

## Uso

```
[prompt example]
```

## Capabilities

- Feature 1
- Feature 2
EOF

# 3. Criar implementação (se necessário)
touch skill.py

# 4. Testar auto-discovery
# Legal-Braniac detecta automaticamente na próxima execução

# 5. Commit
git add skills/nova-skill/
git commit -m "feat: adiciona skill nova-skill"
git push
```

### Workflow Git

```bash
# Ao fim do trabalho
cd ~/claude-work/repos/Claude-Code-Projetos
git add .
git commit -m "feat: implementa feature X"
git push

# Ao iniciar em outra máquina
git pull
```

---

## Estrutura de Diretórios

```
Claude-Code-Projetos/
├── .git/
├── .gitignore
├── README.md                  # Este arquivo
├── CLAUDE.md                  # Instruções para Claude Code
├── DISASTER_HISTORY.md        # Lições aprendidas (leia!)
├── requirements.txt           # Dependências globais (venv raiz)
│
├── .claude/                   # Configuração Claude Code
│   ├── agents/                # Agentes especializados (6)
│   │   ├── legal-braniac.md
│   │   ├── planejamento-legal.md
│   │   ├── desenvolvimento.md
│   │   ├── qualidade-codigo.md
│   │   ├── documentacao.md
│   │   └── analise-dados-legal.md
│   ├── hooks/                 # Hooks (SessionStart, UserPromptSubmit)
│   │   ├── invoke-legal-braniac-hybrid.js
│   │   ├── session-context-hybrid.js
│   │   ├── venv-check.js
│   │   └── ... (10 total)
│   ├── settings.json          # Configuração de hooks
│   ├── LEGAL_BRANIAC_GUIDE.md # Guia completo do orquestrador
│   └── README_SKILLS.md       # Documentação de skills
│
├── agentes/                   # Agentes autônomos (7)
│   ├── oab-watcher/
│   ├── djen-tracker/
│   ├── legal-lens/
│   ├── legal-text-extractor/
│   ├── legal-articles-finder/
│   ├── legal-rag/
│   └── aesthetic-master/
│
├── comandos/                  # Comandos utilitários (5)
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
├── shared/                    # Código compartilhado
│   ├── utils/
│   │   ├── logging_config.py
│   │   ├── path_utils.py
│   │   └── __init__.py
│   └── models/
│       ├── publicacao.py
│       └── __init__.py
│
└── docs/                      # Documentação técnica
    ├── architecture.md
    └── setup.md
```

---

## Troubleshooting

### "ModuleNotFoundError" ao executar agente

**Causa:** Ambiente virtual não ativado ou pacotes não instalados.

**Solução:**
```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/<nome-agente>
source .venv/bin/activate
pip install -r requirements.txt
```

### "FileNotFoundError" ao acessar dados

**Causa:** Estrutura de diretórios de dados não criada.

**Solução:**
```bash
# Criar estrutura de dados
mkdir -p ~/claude-code-data/agentes/<nome-agente>/{downloads,logs,outputs}

# Verificar se existe
ls -la ~/claude-code-data/agentes/<nome-agente>/
```

### Python aponta para versão global ao invés de .venv

**Causa:** Ambiente virtual não ativado corretamente.

**Solução:**
```bash
# Ativar venv
source .venv/bin/activate

# Verificar
which python  # Deve mostrar caminho com .venv
python --version  # Deve mostrar Python 3.11+
```

### Git reclama de arquivos não rastreados em .venv/

**Causa:** .gitignore não está funcionando ou .venv foi commitado anteriormente.

**Solução:**
```bash
# Se .venv está no git (NÃO DEVE ESTAR):
git rm -r --cached agentes/*/.venv
git rm -r --cached .venv
git commit -m "remove: remove ambientes virtuais do Git"

# Verificar .gitignore inclui:
# .venv/
# venv/
# __pycache__/
# *.pyc
```

### Hooks não executam automaticamente

**Causa:** hooks desabilitados ou configuração incorreta.

**Solução:**
```bash
# Verificar configuração
cat .claude/settings.json | jq '.hooks'

# Testar hook manualmente
node .claude/hooks/invoke-legal-braniac-hybrid.js

# Verificar logs
cat ~/.vibe-log/hooks.log | tail -50
```

---

## Regras Imperativas

1. **NUNCA coloque código em `~/claude-code-data/`** - Código vai para `~/claude-work/repos/` e Git
2. **NUNCA coloque dados grandes no Git** - Dados vão para `~/claude-code-data/`
3. **SEMPRE use ambiente virtual (.venv)** - Sem exceções
4. **SEMPRE ative .venv antes de executar Python** - Evita contaminação global
5. **SEMPRE faça git commit ao fim do dia** - Sincronização entre máquinas
6. **NUNCA use caminhos absolutos hardcoded** - Use `path_utils.py` ou env vars
7. **NUNCA commite .venv/ no Git** - Verifique `.gitignore`
8. **SEMPRE retorne ao diretório raiz** após `cd` - Evita quebrar hooks (ver CLAUDE.md)

---

## Ambientes Suportados

### ✅ Claude Code Web (Linux)
- **Status**: ✅ TOTALMENTE FUNCIONAL
- **SessionStart hooks**: Ativos (auto-invocação Legal-Braniac)
- **Limitações**: Sem statusline nativa (arquitetural)

### ✅ WSL2 CLI (Ubuntu 24.04)
- **Status**: ✅ TOTALMENTE FUNCIONAL
- **SessionStart hooks**: Ativos
- **Features avançadas**: Statusline, vibe-log Gordon

### ⚠️ Windows CLI (Casa/Pessoal)
- **Status**: ✅ FUNCIONAL (invocação manual)
- **SessionStart hooks**: Desabilitados (prevenção EPERM)

### ❌ Windows CLI (Corporativo)
- **Status**: ⚠️ DESABILITADO (bug EPERM loop)
- **Motivo**: GPOs corporativas bloqueiam `.claude.json.lock`
- **Workaround**: Use Claude Code Web

---

## Documentação Adicional

- **`.claude/LEGAL_BRANIAC_GUIDE.md`** - 📖 Guia completo do orquestrador
- **`.claude/README_SKILLS.md`** - Documentação das 36 skills funcionais
- **`DISASTER_HISTORY.md`** - Histórico de problemas arquiteturais (leia para NUNCA repetir)
- **`CLAUDE.md`** - Instruções para Claude Code (working directory management, 3-layer architecture)
- **`WSL_SETUP.md`** - Guia de setup WSL2 (referência técnica)
- **`QUICK-REFERENCE.md`** - Comandos essenciais para uso diário
- **`docs/architecture.md`** - Detalhes da arquitetura do sistema
- **`docs/setup.md`** - Guia de setup passo-a-passo detalhado

---

## ⚙️ Configuração Especial

### Append Prompt (`.config/append-prompt.txt`)

Este projeto inclui configuração de **append-prompt** que modifica o comportamento do Claude Code:

**O que faz:**
- Define Claude Code como **DEVELOPER** trabalhando com **PRODUCT MANAGER** (usuário)
- Estabelece protocolo de **validação técnica** antes de implementações
- Requer **research-first** (pesquisa antes de assumir)
- Promove **análise crítica** em vez de validação acrítica
- Implementa **reality filter** para prevenir trabalho desperdiçado

**Quando é aplicado:**
- Automaticamente em TODAS as sessões do Claude Code neste projeto
- Via mecanismo de append-prompt do Claude Code
- Sobrescreve comportamento padrão do Claude

**Localização:** `.config/append-prompt.txt` (versionado em Git)

---

## 🔄 Monitoring & Analytics

### VibeLog Integration
**Status:** Autenticado e ativo

**Hooks instalados:**
- SessionStart: Captura início de sessão
- SessionEnd: Captura fim de sessão
- PreCompact: Captura antes de compactação de contexto

**Dashboard:** https://app.vibe-log.dev
- Streak tracking
- Session analytics
- Prompt analysis history

---

## Licença

MIT License - Veja LICENSE para detalhes.

---

## Autor

**PedroGiudice** - 2025

Projeto de automação jurídica desenvolvido com Claude Code e Python.

---

**Última atualização:** 2025-11-20
**Ambiente:** WSL2 Ubuntu 24.04 LTS
**Diretório:** `~/claude-work/repos/Claude-Code-Projetos`
