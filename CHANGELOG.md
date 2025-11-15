# Changelog - Claude Code Projetos

Todas as mudanças notáveis serão documentadas neste arquivo.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Sprint 2] - 2025-11-15

### Changed

- **[BREAKING]** Padronizado estrutura de diretórios cross-machine
  - WSL/Linux: `~/projects/Claude-Code-Projetos` → `~/claude-work/repos/Claude-Code-Projetos`
  - Alinhado com PC trabalho (Windows): `C:\claude-work\repos\Claude-Code-Projetos`
  - **Razão:** Consistência entre máquinas, scripts portáveis, documentação unificada
  - **Impacto:** Workspaces VSCode/IDE precisam ser atualizados

### Added

- **Documentação WSL:**
  - `WSL_SETUP.md` - Guia completo de setup WSL2 (hooks, venv, npm, git workflow)
  - `CHANGELOG.md` - Este arquivo

- **Infraestrutura WSL:**
  - Node.js v24.11.1 instalado via nvm
  - npm 11.6.2
  - Claude Code 2.0.42 instalado no WSL (não Windows)
  - Python 3.12.3 com pip/venv

- **Virtual Environments Python:**
  - `agentes/djen-tracker/.venv` ✅
  - `agentes/legal-articles-finder/.venv` ✅
  - `agentes/legal-lens/.venv` ✅
  - `agentes/legal-rag/.venv` ✅
  - `agentes/oab-watcher/.venv` ✅

- **npm Dependencies:**
  - `mcp-servers/djen-mcp-server/node_modules/` - 340 packages instalados

- **Hooks Funcionando:**
  - `invoke-legal-braniac-hybrid.js` - Orquestrador ativo no WSL
  - `session-context-hybrid.js` - Context tracking
  - Todos os 10 hooks validados em ambiente Linux

### Security

- **Vulnerabilidades npm detectadas:**
  - 5 moderate severity (esbuild <=0.24.2, vite, vitest)
  - **Impacto:** DEV tools apenas, não afeta produção
  - **Advisory:** https://github.com/advisories/GHSA-67mh-4wv8-2f99
  - **Decisão:** NÃO corrigir agora (npm audit fix --force causa breaking changes)
  - **Tracking:** Documentado para futuro update de dependências

- **Packages deprecados (warnings):**
  - rimraf@2.7.1 → Sugestão: atualizar para rimraf@5.x
  - fstream@1.0.12 → Sugestão: usar streams nativos Node.js
  - inflight@1.0.6 → Dependency transitiva, aguardar upstream
  - lodash.isequal@4.5.0 → Sugestão: migrar para lodash-es moderno
  - glob@7.2.3 → Sugestão: atualizar para glob@10.x

### Fixed

- Conflito npm config prefix com nvm resolvido
  - Removido `~/.npm-global` manual
  - nvm agora gerencia npm global corretamente
  - prefix: `~/.nvm/versions/node/v24.11.1`

- package.json acidental na raiz removido
  - Criado por erro durante diagnóstico
  - Removido antes de commit

### Infrastructure

- **WSL Config (.wslconfig):**
  - memory: 4GB (50% de 8GB total)
  - processors: 2
  - swap: 1GB
  - localhostForwarding: true

- **Windows Defender Exclusion:**
  - Path adicionado: `%USERPROFILE%\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu24.04LTS_79rhkp1fndgsc`
  - Melhora performance WSL

### Deprecated

Nenhuma API ou feature deprecada neste sprint.

---

## [Sprint 1] - 2025-11-07

### Added

- **Estrutura inicial do projeto**
  - Three-layer separation: CODE (Git) / ENV (.venv) / DATA (externo)
  - Regra RULE_006: venv obrigatório
  - Regra RULE_004: sem hardcoded paths

- **Documentação arquitetural:**
  - `CLAUDE.md` - Regras e guidelines para Claude Code
  - `DISASTER_HISTORY.md` - Lições aprendidas (3-day disaster: EPERM loop, PATH corruption)
  - `README.md` - Visão geral do projeto

- **Agentes Python (5):**
  - `agentes/djen-tracker/` - Monitora DJEN (Diário Eletrônico da Justiça)
  - `agentes/legal-articles-finder/` - Extrai artigos de leis brasileiras
  - `agentes/legal-lens/` - Analisa publicações legais
  - `agentes/legal-rag/` - RAG para documentos jurídicos
  - `agentes/oab-watcher/` - Monitora publicações OAB

- **Agentes Claude Code (7):**
  - `@legal-braniac` - Orquestrador mestre
  - `@planejamento-legal` - Planejamento de features
  - `@qualidade-codigo` - Code review e QA
  - `@documentacao` - Documentação técnica
  - `@desenvolvimento` - Implementação hands-on
  - `@analise-dados-legal` - Data analysis e visualizações
  - `@legal-articles-finder` - Especialista em extração legal

- **Skills (34):**
  - Planejamento: feature-planning, writing-plans, executing-plans, ship-learn-next
  - Qualidade: code-auditor, test-fixing, test-driven-development, systematic-debugging, root-cause-tracing
  - Documentação: codebase-documenter, technical-doc-creator, architecture-diagram-creator
  - Desenvolvimento: code-execution, code-refactor, git-pushing, project-bootstrapper
  - Documentos: docx, pdf, pptx, xlsx
  - OCR: ocr-pro, sign-recognition
  - Outros: article-extractor, youtube-transcript, conversation-analyzer

- **Hooks (10):**
  - SessionStart hooks: invoke-legal-braniac, session-context
  - UserPromptSubmit: skill-activation-prompt
  - Validation: venv-check, git-status-watcher, dependency-drift-checker, data-layer-validator
  - Detection: corporate-detector
  - Wrapper: hook-wrapper (tracking)

- **Status Line UI:**
  - Tracking em tempo real de agentes/skills/hooks ativos
  - Scripts em `.claude/statusline/`

### Changed

Primeira versão do projeto. Sem mudanças anteriores.

### Removed

Nenhuma feature removida neste sprint.

---

## Próximos Sprints Planejados

### Sprint 3 - Integração Servidor Corporativo (planejado)
- Montagem SMB/CIFS do servidor de documentos jurídicos
- Configuração `/etc/fstab` para auto-mount
- Benchmark de performance rede vs local

### Sprint 4 - Cache Híbrido (planejado)
- Sincronização servidor → cache local WSL
- Scripts rsync bidirecionais
- Cron jobs para sync automático

### Sprint 5 - Adaptação de Código (planejado)
- Atualizar `shared/utils/path_utils.py` para cache-first
- Adaptar agentes para usar cache híbrido
- Testar workflows completos

### Sprint 6 - Reorganização e Docs (planejado)
- Mover `skills/` para `.claude/skills/`
- Atualizar `CLAUDE.md` com arquitetura WSL
- Commit final e validação completa

---

## Tipos de Mudanças

- **Added** - Nova feature
- **Changed** - Mudança em feature existente
- **Deprecated** - Feature que será removida
- **Removed** - Feature removida
- **Fixed** - Bug fix
- **Security** - Vulnerabilidade corrigida

## Convenções de Commit

- `feat:` - Nova feature
- `fix:` - Bug fix
- `docs:` - Apenas documentação
- `refactor:` - Refatoração (sem mudança funcional)
- `test:` - Adicionar/corrigir testes
- `chore:` - Tarefas de manutenção

---

**Última atualização:** 2025-11-15
**Responsável:** Sprint 2 - WSL2 Migration Complete
