# Retomada: Trabalho no ADK-sandboxed-legal

## Contexto rapido

Projeto em /home/opc/ADK-sandboxed-legal. App desktop Tauri v2 para assistencia juridica com agentes
IA. 3 camadas: frontend React/TS/Vite (Bun), backend Rust (Tauri v2 com 9 plugins), agentes Python
(Google ADK executados como sidecar via shell).

O agente mais funcional e completo eh o brazilian_legal_pipeline: pipeline dialetico multi-fase
(Verificacao, Construcao, Redacao) com sub-agentes dinamicos, ferramentas customizadas (filesystem,
RAG, shell), e gerenciamento de estado via LoopController.

O frontend tem 12 componentes organizados em torno de um ChatWorkspace com editor Slate.js,
gerenciamento de casos juridicos, selecao de agentes, e integracoes (filesystem, MCP, Google Drive).
Theming customizado via TOML. Estado global via useState no App.tsx com prop drilling.

A comunicacao frontend -> agentes Python eh via tauri-plugin-shell com protocolo __ADK_EVENT__ no
stdout. Sandboxing logico via variaveis de ambiente (ADK_WORKSPACE).

Contexto detalhado em docs/contexto/09022026-analise-completa-adk.md.

## Arquivos principais

### Frontend
- src/App.tsx -- componente raiz, estado global, ThemeContext
- src/components/ChatWorkspace.tsx -- interface principal de chat, modos dev/cliente
- src/components/Sidebar.tsx -- navegacao casos/agentes
- src/components/editor/SlateEditor.tsx -- editor rich text
- src/components/ConfigPanel.tsx -- configuracoes app
- src/components/IntegrationsPanel.tsx -- integracoes externas
- src/services/agentBridge.ts -- ponte IPC frontend->Python (protocolo __ADK_EVENT__)
- src/services/adkService.ts -- chamadas diretas SDK @google/genai
- src/services/caseRegistryService.ts -- CRUD de casos
- src/services/filesystemService.ts -- operacoes FS
- src/services/googleDriveService.ts -- integracao GDrive
- src/services/mcpService.ts -- comunicacao MCP
- themes/themes.toml -- definicao de temas
- plugins/vite-plugin-toml-themes.ts -- processador TOML->CSS

### Backend Rust
- src-tauri/src/lib.rs -- setup Tauri, registro de plugins e commands
- src-tauri/src/google_drive.rs -- 6 comandos Tauri para Google Drive
- src-tauri/capabilities/default.json -- permissoes (shell, fs, store, dialog)
- src-tauri/Cargo.toml -- dependencias Rust e plugins

### Agentes Python
- adk-agents/brazilian_legal_pipeline/agent.py -- agente principal, orquestracao multi-fase
- adk-agents/brazilian_legal_pipeline/prompts.py -- prompts das 3 fases
- adk-agents/brazilian_legal_pipeline/tools/ -- ferramentas customizadas (fs, shell, rag)
- adk-agents/brazilian_legal_pipeline/knowledge_base/ -- base de conhecimento
- adk-agents/brazilian_legal_pipeline/session_cli.py -- CLI de sessao (invocado pelo frontend)
- adk-agents/deep_research_sandbox/deep_research_agent.py -- pesquisa tecnica densa
- adk-agents/jurisprudence_agent/agent.py -- pesquisa jurisprudencial com whitelist tribunais
- adk-agents/iterative_research_agent.py -- pesquisa iterativa com loop de refinamento
- adk-agents/visual_verifier/agent.py -- verificacao visual com playwright
- adk-agents/rust_expert_agent/ -- agente Rust + FastAPI local (porta 8000)
- adk-agents/.templates/agent_template.py -- template para novos agentes

## Proximos passos (por prioridade)

### 1. Definir objetivo de trabalho
**Onde:** decisao do usuario
**O que:** Escolher entre: (a) melhorar agente existente, (b) criar novo agente, (c) melhorar
frontend, (d) integrar com lex-vector, (e) outro
**Por que:** A analise foi exploratoria, proximos passos dependem da intencao

### 2. Se trabalhar no brazilian_legal_pipeline
**Onde:** adk-agents/brazilian_legal_pipeline/
**O que:** Ler agent.py (orquestracao), prompts.py (instrucoes por fase), tools/ (ferramentas),
session_cli.py (ponto de entrada)
**Por que:** Eh o agente mais robusto e base para qualquer extensao
**Verificar:** cd adk-agents/brazilian_legal_pipeline && python agent.py --help

### 3. Se trabalhar no frontend
**Onde:** src/App.tsx + src/components/ + src/services/
**O que:** Estado global todo em App.tsx via useState com prop drilling. Considerar Zustand ou mais
Contexts se crescer.
**Por que:** Padrao atual funciona mas escala mal com mais features
**Verificar:** bun install && bun run dev

### 4. Se trabalhar em integracoes/IPC
**Onde:** src/services/agentBridge.ts
**O que:** Protocolo __ADK_EVENT__ eh a ponte critica. Funcoes: runPythonAgent, runCaseSession,
parseADKEvent, stripADKEvents, buildEnvFromConfig
**Por que:** Qualquer novo agente precisa implementar este protocolo no stdout
**Verificar:** Testar com agente simples, verificar parsing de eventos

### 5. Se criar novo agente
**Onde:** adk-agents/.templates/agent_template.py (copiar e adaptar)
**O que:** Criar subdiretorio em adk-agents/, implementar agent.py com protocolo ADK_EVENT
**Por que:** Template fornece estrutura base com imports e exemplos
**Verificar:** python novo_agente/agent.py --help && testar via frontend

## Como verificar

```bash
# Frontend isolado
cd /home/opc/ADK-sandboxed-legal && bun install && bun run dev

# App Tauri completo
cd /home/opc/ADK-sandboxed-legal && cargo tauri dev

# Agente principal
cd /home/opc/ADK-sandboxed-legal/adk-agents/brazilian_legal_pipeline
python agent.py --help

# Rust expert agent (FastAPI)
cd /home/opc/ADK-sandboxed-legal/adk-agents/rust_expert_agent
python run_local.py
curl http://127.0.0.1:8000/health

# Verificar estrutura
tree -L 3 /home/opc/ADK-sandboxed-legal --dirsfirst
```
