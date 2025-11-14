## VISUALIZAÇÃO DE DIRETÓRIOS

### Estrutura CODE (C:\claude-work\repos\Claude-Code-Projetos\ ou /home/user/Claude-Code-Projetos)

```
Claude-Code-Projetos/
│
├── .claude/                              # Configuração Claude Code CLI
│   ├── agents/                           # 7 agentes especializados
│   │   ├── legal-braniac.md             # Orquestrador mestre
│   │   ├── planejamento-legal.md
│   │   ├── desenvolvimento.md
│   │   ├── qualidade-codigo.md
│   │   ├── documentacao.md
│   │   ├── analise-dados-legal.md
│   │   └── legal-articles-finder.md
│   ├── hooks/                            # 7 hooks (UserPromptSubmit)
│   │   ├── session-context-hybrid.js
│   │   ├── invoke-legal-braniac-hybrid.js
│   │   ├── venv-check.js
│   │   ├── git-status-watcher.js
│   │   ├── data-layer-validator.js
│   │   ├── dependency-drift-checker.js
│   │   └── corporate-detector.js
│   ├── skills/                           # Configuração de skills
│   │   └── skill-rules.json
│   └── settings.json                     # Configuração híbrida
│
├── .git/                                 # Git repository
├── .gitignore
├── README.md
├── CLAUDE.md                             # Instruções para Claude Code
├── DISASTER_HISTORY.md                   # História de desastres e lições
├── STATUSLINE_PLAN.md                    # Plano para status line
├── VISUALIZAÇÃO DE DIRETÓRIOS.md         # Este arquivo
│
├── agentes/                              # 5 agentes de monitoramento
│   ├── oab-watcher/
│   │   ├── .venv/                        # Ambiente virtual (não commitado)
│   │   ├── .gitignore
│   │   ├── requirements.txt
│   │   ├── run_agent.ps1
│   │   ├── main.py
│   │   ├── config.json
│   │   └── README.md
│   ├── djen-tracker/
│   │   ├── .venv/
│   │   ├── requirements.txt
│   │   ├── run_agent.ps1
│   │   ├── main.py
│   │   └── README.md
│   ├── legal-lens/
│   │   ├── .venv/
│   │   ├── requirements.txt
│   │   ├── run_agent.ps1
│   │   ├── main.py
│   │   └── README.md
│   ├── legal-rag/                        # Novo agente
│   │   └── [estrutura similar]
│   └── legal-articles-finder/            # Novo agente
│       └── [estrutura similar]
│
├── comandos/                             # 5 comandos utilitários
│   ├── fetch-doc/
│   │   ├── main.py
│   │   └── README.md
│   ├── extract-core/
│   │   ├── main.py
│   │   └── README.md
│   ├── validate-id/
│   │   ├── main.py
│   │   └── README.md
│   ├── parse-legal/
│   │   ├── main.py
│   │   └── README.md
│   └── send-alert/
│       ├── main.py
│       └── README.md
│
├── skills/                               # 34 skills (Claude Code)
│   ├── architecture-diagram-creator/
│   ├── article-extractor/
│   ├── code-auditor/
│   ├── code-execution/
│   ├── code-refactor/
│   ├── code-transfer/
│   ├── codebase-documenter/
│   ├── conversation-analyzer/
│   ├── dashboard-creator/
│   ├── deep-parser/
│   ├── docx/
│   ├── executing-plans/
│   ├── feature-planning/
│   ├── file-operations/
│   ├── flowchart-creator/
│   ├── git-pushing/
│   ├── ocr-pro/
│   ├── pdf/
│   ├── pptx/
│   ├── project-bootstrapper/
│   ├── review-implementing/
│   ├── root-cause-tracing/
│   ├── ship-learn-next/
│   ├── sign-recognition/
│   ├── skill-creator/
│   ├── systematic-debugging/
│   ├── technical-doc-creator/
│   ├── test-driven-development/
│   ├── test-fixing/
│   ├── timeline-creator/
│   ├── verification-before-completion/
│   ├── writing-plans/
│   ├── xlsx/
│   └── youtube-transcript/
│   # Cada skill possui:
│   #   ├── SKILL.md          # Definição da skill
│   #   ├── main.py           # (se aplicável)
│   #   └── config.json       # (se aplicável)
│
├── shared/                               # Código compartilhado
│   ├── utils/
│   │   ├── logging_config.py
│   │   ├── path_utils.py
│   │   └── __init__.py
│   ├── models/
│   │   ├── publicacao.py
│   │   └── __init__.py
│   └── memory/                           # Novo: sistema de memória
│       └── [arquivos de memória]
│
├── mcp-servers/                          # MCP (Model Context Protocol) Servers
│   └── djen-mcp-server/
│       └── [estrutura do servidor MCP]
│
├── legal-extraction/                     # Ferramentas de extração legal
│   ├── pdf-extractor-cli/
│   └── verbose-correct-doodle/
│
├── claude-code-agents/                   # Agentes auxiliares do Claude Code
│   └── [arquivos de configuração]
│
├── scripts/                              # Scripts utilitários
│   └── [scripts diversos]
│
└── docs/                                 # Documentação adicional
    ├── architecture.md
    └── setup.md
```

### Estrutura DATA (E:\claude-code-data\ ou /data/claude-code-data)

```
claude-code-data/
│
├── agentes/
│   ├── oab-watcher/
│   │   ├── downloads/                    # PDFs baixados
│   │   ├── logs/                         # Logs de execução
│   │   └── outputs/                      # Resultados processados
│   ├── djen-tracker/
│   │   ├── downloads/
│   │   ├── logs/
│   │   └── outputs/
│   ├── legal-lens/
│   │   ├── downloads/
│   │   ├── logs/
│   │   └── outputs/
│   ├── legal-rag/
│   │   ├── downloads/
│   │   ├── logs/
│   │   └── outputs/
│   └── legal-articles-finder/
│       ├── downloads/
│       ├── logs/
│       └── outputs/
│
└── shared/
    ├── cache/                            # Cache compartilhado
    └── temp/                             # Arquivos temporários
```

### Notas

- **Total de agentes:** 7 (5 em agentes/ + 2 especializados)
- **Total de skills:** 34 skills disponíveis
- **Total de hooks:** 7 hooks ativos (UserPromptSubmit)
- **Total de comandos:** 5 comandos utilitários

**IMPORTANTE:**
- `.venv/` e `__pycache__/` NÃO são commitados (estão em .gitignore)
- Data em E:\ NUNCA é commitada
- Código SEMPRE em C:\ (Windows) ou /home (Linux)

**Última atualização:** 2025-11-14
	