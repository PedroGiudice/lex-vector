# Changelog - Claude Code Projetos

Todas as mudancas notaveis sao documentadas neste arquivo.

Formato baseado em Keep a Changelog (https://keepachangelog.com/en/1.0.0/).

NOTA: Changelog detalhado esta nos commits Git. Este arquivo documenta apenas marcos principais.

---

## [Sprint 2] - 2025-11-15

### Changed

- BREAKING: Padronizado estrutura de diretorios cross-machine
  - WSL/Linux: ~/projects/Claude-Code-Projetos → ~/claude-work/repos/Claude-Code-Projetos
  - Alinhado com PC trabalho (Windows): C:\claude-work\repos\Claude-Code-Projetos
  - Razao: Consistencia entre maquinas, scripts portaveis, documentacao unificada
  - Impacto: Workspaces VSCode/IDE precisam ser atualizados

### Added

- Documentacao WSL:
  - WSL_SETUP.md - Guia completo de setup WSL2 (hooks, venv, npm, git workflow)
  - CHANGELOG.md - Este arquivo

- Infraestrutura WSL:
  - Node.js v24.11.1 instalado via nvm
  - npm 11.6.2
  - Claude Code 2.0.42 instalado no WSL (nao Windows)
  - Python 3.12.3 com pip/venv

- Virtual Environments Python:
  - agentes/djen-tracker/.venv
  - agentes/legal-articles-finder/.venv
  - agentes/legal-lens/.venv
  - agentes/legal-rag/.venv
  - agentes/oab-watcher/.venv

- npm Dependencies:
  - mcp-servers/djen-mcp-server/node_modules/ - 340 packages instalados

- Hooks Funcionando:
  - invoke-legal-braniac-hybrid.js - Orquestrador ativo no WSL
  - session-context-hybrid.js - Context tracking
  - Todos os 10 hooks validados em ambiente Linux

### Security

- Vulnerabilidades npm detectadas:
  - 5 moderate severity (esbuild <=0.24.2, vite, vitest)
  - Impacto: DEV tools apenas, nao afeta producao
  - Advisory: https://github.com/advisories/GHSA-67mh-4wv8-2f99
  - Decisao: NAO corrigir agora (npm audit fix --force causa breaking changes)
  - Tracking: Documentado para futuro update de dependencias

- Packages deprecados (warnings):
  - rimraf@2.7.1 → Sugestao: atualizar para rimraf@5.x
  - fstream@1.0.12 → Sugestao: usar streams nativos Node.js
  - inflight@1.0.6 → Dependency transitiva, aguardar upstream
  - lodash.isequal@4.5.0 → Sugestao: migrar para lodash-es moderno
  - glob@7.2.3 → Sugestao: atualizar para glob@10.x

### Fixed

- Conflito npm config prefix com nvm resolvido
  - Removido ~/.npm-global manual
  - nvm agora gerencia npm global corretamente
  - prefix: ~/.nvm/versions/node/v24.11.1

- package.json acidental na raiz removido
  - Criado por erro durante diagnostico
  - Removido antes de commit

### Infrastructure

- WSL Config (.wslconfig):
  - memory: 4GB (50% de 8GB total)
  - processors: 2
  - swap: 1GB
  - localhostForwarding: true

- Windows Defender Exclusion:
  - Path adicionado para melhorar performance WSL

---

## [Sprint 1] - 2025-11-07

### Added

- Estrutura inicial do projeto
  - Three-layer separation: CODE (Git) / ENV (.venv) / DATA (externo)
  - Regra RULE_006: venv obrigatorio
  - Regra RULE_004: sem hardcoded paths

- Documentacao arquitetural:
  - CLAUDE.md - Regras e guidelines para Claude Code
  - DISASTER_HISTORY.md - Licoes aprendidas (3-day disaster: EPERM loop, PATH corruption)
  - README.md - Visao geral do projeto

- Agentes Python (5):
  - agentes/djen-tracker/ - Monitora DJEN (Diario Eletronico da Justica)
  - agentes/legal-articles-finder/ - Extrai artigos de leis brasileiras
  - agentes/legal-lens/ - Analisa publicacoes legais
  - agentes/legal-rag/ - RAG para documentos juridicos
  - agentes/oab-watcher/ - Monitora publicacoes OAB

- Agentes Claude Code (7):
  - @legal-braniac - Orquestrador mestre
  - @planejamento-legal - Planejamento de features
  - @qualidade-codigo - Code review e QA
  - @documentacao - Documentacao tecnica
  - @desenvolvimento - Implementacao hands-on
  - @analise-dados-legal - Data analysis e visualizacoes
  - @legal-articles-finder - Especialista em extracao legal

- Skills (34):
  - Planejamento: feature-planning, writing-plans, executing-plans, ship-learn-next
  - Qualidade: code-auditor, test-fixing, test-driven-development, systematic-debugging, root-cause-tracing
  - Documentacao: codebase-documenter, technical-doc-creator, architecture-diagram-creator
  - Desenvolvimento: code-execution, code-refactor, git-pushing, project-bootstrapper
  - Documentos: docx, pdf, pptx, xlsx
  - OCR: ocr-pro, sign-recognition
  - Outros: article-extractor, youtube-transcript, conversation-analyzer

- Hooks (10):
  - SessionStart hooks: invoke-legal-braniac, session-context
  - UserPromptSubmit: skill-activation-prompt
  - Validation: venv-check, git-status-watcher, dependency-drift-checker, data-layer-validator
  - Detection: corporate-detector
  - Wrapper: hook-wrapper (tracking)

- Status Line UI:
  - Tracking em tempo real de agentes/skills/hooks ativos
  - Scripts em .claude/statusline/

---

## Tipos de Mudancas

- Added - Nova feature
- Changed - Mudanca em feature existente
- Deprecated - Feature que sera removida
- Removed - Feature removida
- Fixed - Bug fix
- Security - Vulnerabilidade corrigida

## Convencoes de Commit

- feat: - Nova feature
- fix: - Bug fix
- docs: - Apenas documentacao
- refactor: - Refatoracao (sem mudanca funcional)
- test: - Adicionar/corrigir testes
- chore: - Tarefas de manutencao

---

Ultima atualizacao: 2025-12-02
Responsavel: Condensacao de documentacao principal
