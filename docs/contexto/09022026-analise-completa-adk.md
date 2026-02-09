# Contexto: Analise Completa do ADK-sandboxed-legal

**Data:** 2026-02-09
**Sessao:** work/session-20260202-192305 (lex-vector) -> cross-project analysis

---

## Arquitetura

App desktop hibrido Tauri v2 com 3 camadas:
- **Frontend:** React + TypeScript + Vite (SPA dentro de janela Tauri). Bun como package manager.
- **Backend Rust:** Tauri v2, ponte entre frontend e SO. Plugins para shell, fs, dialog, store,
updater, process, mcp.
- **Agentes Python:** Google ADK agents executados como sidecar via tauri-plugin-shell.

## ADK Agents (6 + 1 template)

| Agente | Tipo | Modelo | Complexidade |
|--------|------|--------|-------------|
| brazilian_legal_pipeline | Custom Orchestration | gemini-2.5-flash | ALTA |
| deep_research_sandbox | Agent | gemini-2.5-flash | MEDIA |
| iterative_research_agent | Custom Orchestration | gemini-2.5-flash | MEDIA |
| jurisprudence_agent | Custom Orchestration | gemini-2.5-flash | MEDIA |
| visual_verifier | Agent | gemini-2.5-flash | MEDIA |
| rust_expert_agent | Agent | gemini-2.0-flash-exp | BAIXA |

**Mais funcional:** brazilian_legal_pipeline - pipeline dialetico multi-fase com sub-agentes
dinamicos, ferramentas de filesystem/RAG/shell, gerenciamento de estado via LoopController.

### brazilian_legal_pipeline (detalhe)

- 3 fases: Verificacao, Construcao, Redacao
- Prompts especializados por fase importados de `prompts.py` (INTAKE_INSTRUCTION,
VERIFICADOR_INSTRUCTION, etc)
- Ferramentas customizadas em `tools/`: filesystem_tools, shell_tools, legal_rag_tools
- Knowledge base em `knowledge_base/`
- Orquestracao customizada com multiplos Agent instanciados dinamicamente
- Gerenciamento de estado via LoopController
- CLI via session_cli.py
- Usa dotenv para carregar variaveis de ambiente (sandboxing)

### Outros agentes

- **deep_research_sandbox:** Pesquisa tecnica com dataclasses para config, logging, retentativas via
tenacity. SYSTEM_PROMPT em modo "STRICT OBJECTIVE".
- **iterative_research_agent:** Loop de pesquisa iterativo com 3 prompts (DECOMPOSITION, GAP_ANALYSIS,
 SYNTHESIS). Para por saturacao ou numero de fontes.
- **jurisprudence_agent:** Especializacao do iterative, com whitelist de dominios de tribunais e
extracao de metadados juridicos (numero processo, relator).
- **visual_verifier:** Ferramentas verify_page, update_baseline, list_baselines, quick_check. Depende
de PIL e playwright.
- **rust_expert_agent:** Simples, persona de Engenheiro Senior Rust para Tauri 2.x. Tem FastAPI local
(run_local.py) na porta 8000.

## Frontend - 12 Componentes

| Componente | Arquivo | Complexidade | Responsabilidade |
|-----------|---------|-------------|-----------------|
| App | src/App.tsx | ALTA | Raiz, estado global (useState), layout com Sidebar + ChatWorkspace, modais, ThemeContext |
| ChatWorkspace | src/components/ChatWorkspace.tsx | ALTA | Chat interativo, modos dev/cliente, SlateEditor, AgentMessageBody (thought/bash/tool_call) |
| Sidebar | src/components/Sidebar.tsx | MEDIA | Navegacao, dropdowns caso/agente, progresso pipeline, botao novo caso |
| SlateEditor | src/components/editor/SlateEditor.tsx | MEDIA | Rich text Slate.js, elementos customizados, atalhos (Ctrl+B, Ctrl+Enter) |
| EditorToolbar | src/components/editor/EditorToolbar.tsx | BAIXA | Barra formatacao para SlateEditor |
| ConfigPanel | src/components/ConfigPanel.tsx | MEDIA | Config: workspace, tema, fonte, API key Gemini, temperatura, Top K |
| IntegrationsPanel | src/components/IntegrationsPanel.tsx | MEDIA | Abas: Pastas Locais, Servidores MCP, Google Drive |
| NewCaseModal | src/components/NewCaseModal.tsx | BAIXA | Form: nome, numero processo, cliente, descricao, tags |
| WorkspaceSetupModal | src/components/WorkspaceSetupModal.tsx | BAIXA | Setup inicial de pasta workspace (primeiro uso) |
| MarkdownRenderer | src/components/MarkdownRenderer.tsx | BAIXA | Renderiza markdown simplificado (#, -, >, **bold**, *italic*, code, links) |
| ResizeHandle | src/components/ResizeHandle.tsx | BAIXA | Redimensionar paineis + exporta hook useResizable |
| Icons | src/components/Icons.tsx | BAIXA | Biblioteca SVG inline |

### Features do app

1. Gerenciamento de casos juridicos (criar, selecionar, metadados)
2. Selecao de agentes IA especializados
3. Chat interativo com modo Desenvolvedor (mostra thoughts, bash, tool_calls)
4. Editor rich text (Slate.js) com formatacao completa
5. Anexo de arquivos nas mensagens
6. Configuracao de tema, fonte, API key, parametros do modelo
7. Integracoes: filesystem local (whitelist ou irrestrito), MCP servers, Google Drive

### Tema/Styling

- Sistema customizado: themes/themes.toml -> plugins/vite-plugin-toml-themes.ts ->
themes/generated-themes.css
- Classes utilitarias (bg-surface, text-accent) controladas por variaveis CSS
- 4 temas: dark (padrao), light, high-contrast, ocean
- Layout Flexbox com paineis redimensionaveis
- Icones SVG inline em Icons.tsx (sem assets externos)
- Fontes selecionaveis no ConfigPanel, aplicadas via CSS vars no <html>

### State Management

- useState + useCallback no App.tsx (prop drilling para filhos)
- ThemeContext (Context API) para tema global
- Hook useResizable: gerencia tamanho de paineis com persistencia no localStorage
- Historico de mensagens salvo por caso+agente via filesystem Tauri
- localStorage para: tema, fonte, largura sidebar, altura input, workspaceRoot

### Roteamento

Nenhuma lib de routing. SPA com navegacao por estado:
- isConfigOpen, showNewCaseModal, isIntegrationsOpen, etc no App.tsx
- Interface principal sempre ChatWorkspace, conteudo muda por estado

### Hooks customizados

- useResizable (ResizeHandle.tsx): initialSize, minSize, maxSize, storageKey -> { size, handleResize,
setSize }
- useTheme (App.tsx): wrapper para useContext(ThemeContext)

## Comandos Tauri (Rust) - src-tauri/src/google_drive.rs

| Comando | Parametros | Retorno |
|---------|-----------|---------|
| google_drive_auth | client_id, redirect_uri | Result<String> (URL OAuth) |
| google_drive_callback | code, client_id, client_secret, redirect_uri | Result<GoogleDriveCredentials> |
| google_drive_list_files | access_token, folder_id?, page_token? | Result<DriveFilesResponse> |
| google_drive_download | access_token, file_id, file_name, download_path | Result<String> |
| google_drive_upload | access_token, local_path, folder_id?, file_name? | Result<DriveFile> |
| google_drive_disconnect | nenhum | Result<()> |

## Plugins Tauri (src-tauri/Cargo.toml + lib.rs)

| Plugin | Finalidade |
|--------|-----------|
| tauri-plugin-shell | Execucao de agentes Python (python/python3 com quaisquer args) |
| tauri-plugin-fs | Acesso ao filesystem (R/W recursivo em HOME, DOCUMENT, DOWNLOAD, DESKTOP) |
| tauri-plugin-dialog | Dialogos nativos abrir/salvar |
| tauri-plugin-store | Key-value persistente |
| tauri-plugin-persisted-scope | Salvar permissoes FS entre sessoes |
| tauri-plugin-updater | Auto-update |
| tauri-plugin-process | Gerenciamento de processos |
| tauri-plugin-mcp | Comunicacao MCP/RPC (possivelmente WebSocket) |
| tauri-plugin-log | Logging |

## Permissoes (src-tauri/capabilities/default.json)

- shell: allow-execute para python e python3 com quaisquer argumentos
- fs: leitura/escrita RECURSIVA em $HOME, $DOCUMENT, $DOWNLOAD, $DESKTOP
- store: acesso completo (get, set, delete, save, load)
- dialog: abrir e salvar arquivos
- updater, process, core: permissoes padrao

## Servicos Frontend (src/services/)

| Servico | Responsabilidade |
|---------|-----------------|
| agentBridge.ts | Ponte frontend -> agentes Python via shell. Funcoes: runPythonAgent, runCaseSession, parseADKEvent, stripADKEvents, buildEnvFromConfig, filesystemToEnv |
| adkService.ts | Chamadas diretas ao SDK @google/genai (stateless, sem ADK) |
| caseRegistryService.ts | CRUD de casos (.registry.json). Funcoes: loadRegistry, createCase, listCases |
| filesystemService.ts | Operacoes FS via Tauri: selectFolder, checkFolderAccess, readFileFromFolder, writeFileToFolder |
| googleDriveService.ts | Integracao Google Drive via invoke() dos comandos Rust |
| mcpService.ts | Comunicacao com tauri-plugin-mcp |

## Protocolo IPC (Frontend -> Python)

1. Frontend chama agentBridge.runPythonAgent() ou runCaseSession()
2. Cria Command.create('python', [scriptPath, ...args]) via tauri-plugin-shell
3. Variaveis de ambiente definem sandboxing: ADK_WORKSPACE=casePath, FILESYSTEM_MODE,
FILESYSTEM_FOLDERS
4. Agente Python emite eventos estruturados no stdout: __ADK_EVENT__{json}__ADK_EVENT__
5. parseADKEvent() extrai dados JSON dos eventos
6. stripADKEvents() limpa output para exibicao ao usuario

## API FastAPI (adk-agents/rust_expert_agent/run_local.py)

| Metodo | Path | Descricao |
|--------|------|-----------|
| GET | /health | Health check |
| POST | /chat | Processa mensagem via ADK, retorna resposta do agente |

Host: 127.0.0.1:8000

## Padrao de servicos frontend

- Modulos TS que exportam funcoes async nomeadas (sem classes, sem export default)
- Erros tratados com try/catch local, retornam null/false ou lancam Error
- Tipos definidos como interface no topo do arquivo ou importados de src/types.ts
- Interacao com Tauri via @tauri-apps/api e @tauri-apps/plugin-*
