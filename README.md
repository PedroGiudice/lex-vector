# Claude Code Projetos

Sistema de automacao juridica com agentes Python para monitoramento de publicacoes, processamento de documentos legais e analise de dados juridicos.

## Visao Geral

| Componente | Quantidade |
|------------|------------|
| Agentes | 9 |
| Skills | 56 custom + 8 managed |
| Comandos | 5 |
| Hooks | 18 |

**Stack:** Python 3.11, Node.js v22, Ubuntu 24.04 (WSL2), Git

---

## Arquitetura de 3 Camadas

Separacao rigida obrigatoria (ver DISASTER_HISTORY.md):

| Camada | Local | Versionamento |
|--------|-------|---------------|
| Codigo | `~/claude-work/repos/Claude-Code-Projetos/` | Git (obrigatorio) |
| Ambiente | `agentes/*/.venv/` | Nunca (local) |
| Dados | `~/claude-code-data/` | Nunca |

**Regra:** Codigo em Git. Ambiente local. Dados fora do Git.

---

## Agentes (9)

| Agente | Funcao |
|--------|--------|
| oab-watcher | Monitora Diario Oficial da OAB |
| djen-tracker | Monitora Diario de Justica Eletronico |
| legal-lens | Analise NLP de publicacoes legais |
| legal-text-extractor | OCR de documentos PDF |
| legal-articles-finder | Busca de artigos de leis |
| legal-rag | RAG para questoes juridicas |
| jurisprudencia-collector | Coleta de jurisprudencia |
| stj-dados-abertos | Dados abertos do STJ |
| aesthetic-master | Design system e componentes |

---

## Skills

**Custom (skills/):** 56 skills incluindo OCR, parsing, TDD, debugging, documentacao, frontend design, code review, brainstorming, writing-plans.

**Managed (.claude/skills/):** backend-dev-guidelines, frontend-dev-guidelines, error-tracking, route-tester, skill-developer, brainstorming, writing-plans.

---

## Comandos (5)

| Comando | Funcao |
|---------|--------|
| fetch-doc | Baixa documentos de URLs/APIs |
| extract-core | Extrai metadados e entidades |
| validate-id | Valida CPF, CNPJ, OAB |
| parse-legal | Parser de textos juridicos |
| send-alert | Alertas via email/webhook |

---

## Setup

```bash
# Clone
git clone <repo-url> ~/claude-work/repos/Claude-Code-Projetos
cd ~/claude-work/repos/Claude-Code-Projetos

# Estrutura de dados
mkdir -p ~/claude-code-data/agentes/{oab-watcher,djen-tracker,legal-lens}/{downloads,logs,outputs}

# Setup de agente
cd agentes/oab-watcher
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Uso

```bash
# Executar agente
cd agentes/oab-watcher
source .venv/bin/activate
python main.py

# Verificar logs
tail -f ~/claude-code-data/agentes/oab-watcher/logs/latest.log
```

---

## Estrutura

```
Claude-Code-Projetos/
├── .claude/           # Config Claude Code (hooks, skills managed, agents)
├── agentes/           # 9 agentes autonomos
├── comandos/          # 5 comandos utilitarios
├── skills/            # 56 skills custom
├── shared/            # Codigo compartilhado (utils, models)
└── docs/              # Documentacao tecnica
```

---

## Troubleshooting

**ModuleNotFoundError:** Ative o venv do agente
```bash
source agentes/<nome>/.venv/bin/activate
pip install -r requirements.txt
```

**FileNotFoundError:** Crie estrutura de dados
```bash
mkdir -p ~/claude-code-data/agentes/<nome>/{downloads,logs,outputs}
```

---

## Regras

1. Codigo em Git, dados fora
2. Sempre usar .venv
3. Nunca commitar .venv/
4. Nunca usar paths absolutos hardcoded
5. Commit ao fim do trabalho

---

## Documentacao

- CLAUDE.md - Instrucoes para Claude Code
- DISASTER_HISTORY.md - Licoes aprendidas
- .claude/skills/README.md - Skills managed

---

**Autor:** PedroGiudice | **Licenca:** MIT | **Atualizacao:** 2025-12-03
