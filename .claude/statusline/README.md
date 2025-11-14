# Status Line - Legal-Braniac System

Sistema de status line customizado para o projeto Claude-Code-Projetos. Exibe informações em tempo real sobre agentes, skills, hooks e contexto do projeto.

**Fase de Desenvolvimento:** ✅ FASE 3 COMPLETA (Sistema de tracking completo + UI final)

---

## 📋 Statuslines Disponíveis

### 1. **legal-braniac-statusline.js** ✨ (Orquestrador Principal)
**Agente:** Legal-Braniac (Coordenador Mestre)
**Características:**
- ✅ Único com emoji 🧠 (decisão de design)
- ✅ Tracking de execução via hook wrapper
- ✅ Exibe status de sucesso/erro do orquestrador
- ✅ Timestamp da última execução
- ✅ Detecção de agentes ativos em tempo real
- ✅ Indicadores de status de hooks (✓/ERR)

**Formato:**
```
🧠 LEGAL-BRANIAC snt-4.5 | 📂 Claude-Code-Projetos | 🌿 main | 💰 $1.25 | 📊 95k
├ 🤖 7 agentes (1 ativo: legal-braniac) | 📦 34 skills | 🔧 7 hooks (all ✓)
└ ✅ LEGAL-BRANIAC success (30s ago)
```

---

### 2. **analise-dados-legal-statusline.js** (Clean UI)
**Agente:** Análise de Dados Legais
**Especialização:** Análise de métricas legais, publicações DJEN, estatísticas OAB
**Características:**
- ✅ UI limpa sem emojis
- ✅ Indicadores de status de hooks (OK/ERR/N/M OK)

**Formato:**
```
[ANALISE-DADOS-LEGAL] snt-4.5 | DIR: Claude-Code-Projetos | BRANCH: main | COST: $1.25 | TOKENS: 95k
└ 7 agentes | 34 skills | 7 hooks (6/7 OK)
```

---

### 3. **desenvolvimento-statusline.js** (Clean UI)
**Agente:** Desenvolvimento
**Especialização:** Implementação técnica, coding, refactoring, Git operations, TDD
**Características:**
- ✅ UI limpa sem emojis
- ✅ Indicadores de status de hooks (OK/ERR/N/M OK)

**Formato:**
```
[DESENVOLVIMENTO] snt-4.5 | DIR: Claude-Code-Projetos | BRANCH: main | COST: $1.25 | TOKENS: 95k
└ 7 agentes | 34 skills | 7 hooks (OK)
```

---

### 4. **documentacao-statusline.js** (Clean UI)
**Agente:** Documentação
**Especialização:** Documentação técnica, arquitetura, APIs, guias, onboarding
**Características:**
- ✅ UI limpa sem emojis
- ✅ Indicadores de status de hooks (OK/ERR/N/M OK)

**Formato:**
```
[DOCUMENTACAO] snt-4.5 | DIR: Claude-Code-Projetos | BRANCH: main | COST: $1.25 | TOKENS: 95k
└ 7 agentes | 34 skills | 7 hooks (OK)
```

---

### 5. **legal-articles-finder-statusline.js** (Clean UI)
**Agente:** Legal Articles Finder
**Especialização:** Identificação de citações legais, extração de artigos de leis brasileiras
**Características:**
- ✅ UI limpa sem emojis
- ✅ Indicadores de status de hooks (OK/ERR/N/M OK)

**Formato:**
```
[LEGAL-ARTICLES-FINDER] snt-4.5 | DIR: Claude-Code-Projetos | BRANCH: main | COST: $1.25 | TOKENS: 95k
└ 7 agentes | 34 skills | 7 hooks (OK)
```

---

### 6. **planejamento-legal-statusline.js** (Clean UI)
**Agente:** Planejamento Legal
**Especialização:** Planejamento de sistemas de automação legal, arquitetura de software jurídico
**Características:**
- ✅ UI limpa sem emojis
- ✅ Indicadores de status de hooks (OK/ERR/N/M OK)

**Formato:**
```
[PLANEJAMENTO-LEGAL] snt-4.5 | DIR: Claude-Code-Projetos | BRANCH: main | COST: $1.25 | TOKENS: 95k
└ 7 agentes | 34 skills | 7 hooks (OK)
```

---

### 7. **qualidade-codigo-statusline.js** (Clean UI)
**Agente:** Qualidade de Código
**Especialização:** Code review, testing, debugging, auditoria, segurança
**Características:**
- ✅ UI limpa sem emojis
- ✅ Indicadores de status de hooks (OK/ERR/N/M OK)

**Formato:**
```
[QUALIDADE-CODIGO] snt-4.5 | DIR: Claude-Code-Projetos | BRANCH: main | COST: $1.25 | TOKENS: 95k
└ 7 agentes | 34 skills | 7 hooks (OK)
```

---

## ⚙️ Como Configurar

Edite `.claude/settings.json` e adicione a configuração `statusLine`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "node .claude/statusline/<nome-do-agente>-statusline.js",
    "padding": 0,
    "_note": "Status line customizado para <nome-do-agente>"
  }
}
```

**Exemplos:**
```json
// Para Legal-Braniac (orquestrador)
"command": "node .claude/statusline/legal-braniac-statusline.js"

// Para Desenvolvimento
"command": "node .claude/statusline/desenvolvimento-statusline.js"

// Para Documentação
"command": "node .claude/statusline/documentacao-statusline.js"
```

---

## 🔧 Sistema de Tracking (FASE 1 + FASE 2)

### Hook Wrapper (`hook-wrapper.js`)
**FASE 1:** Sistema universal de tracking para todos os 7 hooks do projeto.

**Funcionalidades:**
- Intercepta execução de hooks via wrapper transparente
- Registra timestamp de início/fim, status (success/error), output
- Salva dados em `hooks-status.json` (gitignored)
- Não interfere no funcionamento dos hooks

**Hooks Trackeados:**
1. `session-context-hybrid.js`
2. `invoke-legal-braniac-hybrid.js`
3. `venv-check.js`
4. `git-status-watcher.js`
5. `data-layer-validator.js`
6. `dependency-drift-checker.js`
7. `corporate-detector.js`

**Configuração em `.claude/settings.json`:**
```json
{
  "hooks": {
    "onStart": [
      {
        "command": "node .claude/hooks/hook-wrapper.js session-context-hybrid"
      }
    ],
    "onStop": [
      {
        "command": "node .claude/hooks/hook-wrapper.js invoke-legal-braniac-hybrid"
      }
    ]
  }
}
```

**Formato de `hooks-status.json`:**
```json
{
  "session-context-hybrid": {
    "lastRun": "2025-11-14T10:30:45.123Z",
    "status": "success",
    "duration": 245,
    "output": "Session context loaded successfully"
  },
  "invoke-legal-braniac-hybrid": {
    "lastRun": "2025-11-14T10:35:12.456Z",
    "status": "error",
    "duration": 1023,
    "output": "Failed to invoke orchestrator"
  }
}
```

---

### Active Agents Detector (`active-agents-detector.js`)
**FASE 2:** Detecta agentes executados recentemente (últimos 5 minutos).

**Funcionalidades:**
- Analisa `hooks-status.json` para detectar hooks de agentes
- Identifica agentes ativos por timestamp (< 5 minutos)
- Gera `active-agents.json` automaticamente
- Integrado ao statusline do Legal-Braniac

**Execução:**
```bash
# Manual (para debug)
node .claude/statusline/active-agents-detector.js

# Automático (chamado por legal-braniac-statusline.js)
```

**Formato de `active-agents.json`:**
```json
{
  "agents": ["legal-braniac", "desenvolvimento"],
  "timestamp": "2025-11-14T10:35:30.789Z"
}
```

**Exibição no Legal-Braniac:**
```
🤖 7 agentes (2 ativos: legal-braniac, desenvolvimento)
```

---

## 🧩 Arquitetura

### Auto-Discovery
Todos os statuslines detectam automaticamente:
- **Agentes:** Lê `.claude/agents/*.md`
- **Skills:** Lê `skills/*/SKILL.md`
- **Hooks:** Lê `.claude/settings.json`
- **Hooks Status:** Lê `hooks-status.json` (gerado por hook-wrapper.js)
- **Agentes Ativos:** Lê `active-agents.json` (gerado por active-agents-detector.js)

### Graceful Fallback
Se houver erro ao carregar dados, exibe mensagem genérica sem quebrar o Claude Code:
```
<Agente> Status (error loading data)
```

---

## 📊 Indicadores Visuais (FASE 3)

### Status de Hooks
**FASE 3:** Todos os 7 statuslines exibem status de hooks em tempo real.

**Formatos:**
- `7 hooks (all ✓)` - Todos os hooks executaram com sucesso
- `7 hooks (OK)` - Todos os hooks sem erros (formato compacto)
- `7 hooks (6/7 OK)` - 6 de 7 hooks com sucesso, 1 com erro
- `7 hooks (ERR)` - Todos os hooks com erro

**Lógica:**
```javascript
// Legal-Braniac (formato com emoji)
const allSuccess = hooks.every(h => h.status === 'success');
if (allSuccess) return "all ✓";

// Demais agentes (formato compacto)
const successCount = hooks.filter(h => h.status === 'success').length;
if (successCount === totalHooks) return "OK";
if (successCount === 0) return "ERR";
return `${successCount}/${totalHooks} OK`;
```

### Agentes Ativos
**Exclusivo Legal-Braniac:** Exibe contagem e lista de agentes ativos.

**Formatos:**
- `7 agentes (1 ativo: legal-braniac)` - 1 agente ativo
- `7 agentes (2 ativos: legal-braniac, desenvolvimento)` - 2 agentes ativos
- `7 agentes` - Nenhum agente ativo (fallback)

**Critério:** Agente considerado ativo se hook foi executado nos últimos 5 minutos.

---

## 🎨 Decisões de Design

### Emojis
- **Legal-Braniac:** ✅ Único agente com emojis decorativos (🧠 📂 🌿 💰 📊 🤖 📦 🔧)
- **Demais agentes:** ❌ SEM emojis (clean UI para não poluir interface)

**Motivo:** Legal-Braniac é o orquestrador principal - merece destaque visual.

### Cores ANSI
Todos usam a mesma paleta:
- **Cyan:** Nome do agente
- **Yellow:** Modelo (snt-4.5)
- **Blue:** Diretório
- **Green:** Branch, contadores, status OK
- **Red:** Status ERR
- **Magenta:** Custo
- **White:** Tokens
- **Dim:** Separadores

---

## 📁 Estrutura de Arquivos

```
.claude/statusline/
├── README.md                                   ← Você está aqui
│
├── hook-wrapper.js                             ← FASE 1: Wrapper universal para hooks
├── active-agents-detector.js                   ← FASE 2: Detector de agentes ativos
│
├── legal-braniac-statusline.js                 ← FASE 3: Orquestrador (emojis + agentes ativos)
├── analise-dados-legal-statusline.js           ← FASE 3: Clean UI + status hooks
├── desenvolvimento-statusline.js               ← FASE 3: Clean UI + status hooks
├── documentacao-statusline.js                  ← FASE 3: Clean UI + status hooks
├── legal-articles-finder-statusline.js         ← FASE 3: Clean UI + status hooks
├── planejamento-legal-statusline.js            ← FASE 3: Clean UI + status hooks
├── qualidade-codigo-statusline.js              ← FASE 3: Clean UI + status hooks
│
├── hooks-status.json                           ← Gerado automaticamente (gitignored)
└── active-agents.json                          ← Gerado automaticamente (gitignored)
```

---

## 🧪 Testes e Verificação

### Verificar Hooks Status
```bash
# Verificar arquivo gerado pelo hook-wrapper.js
cat .claude/statusline/hooks-status.json

# Verificar se hooks estão sendo trackeados
node .claude/statusline/hook-wrapper.js session-context-hybrid
```

**Saída esperada:**
```json
{
  "session-context-hybrid": {
    "lastRun": "2025-11-14T10:30:45.123Z",
    "status": "success",
    "duration": 245,
    "output": "Session context loaded"
  }
}
```

### Verificar Agentes Ativos
```bash
# Executar detector manualmente
node .claude/statusline/active-agents-detector.js

# Verificar arquivo gerado
cat .claude/statusline/active-agents.json
```

**Saída esperada:**
```json
{
  "agents": ["legal-braniac"],
  "timestamp": "2025-11-14T10:35:30.789Z"
}
```

### Testar Statusline
```bash
# Testar formatação do statusline
echo '{"workspace":{"current_dir":"C:\\claude-work\\repos\\Claude-Code-Projetos"},"model":{"display_name":"claude-sonnet-4.5"},"git":{"branch":"main"},"tokens":{"total":95000},"cost":{"total_usd":1.25}}' | node .claude/statusline/<agente>-statusline.js

# Exemplo para Legal-Braniac
echo '{"workspace":{"current_dir":"C:\\claude-work\\repos\\Claude-Code-Projetos"},"model":{"display_name":"claude-sonnet-4.5"},"git":{"branch":"main"},"tokens":{"total":95000},"cost":{"total_usd":1.25}}' | node .claude/statusline/legal-braniac-statusline.js
```

---

## 🔧 Manutenção

### Adicionar Novo Statusline
1. Copiar template de um statusline existente (ex: `desenvolvimento-statusline.js`)
2. Trocar nome do agente no cabeçalho e função `generateHeader()`
3. Adicionar lógica de leitura de `hooks-status.json` para exibir status
4. Validar sintaxe: `node -c .claude/statusline/<novo>-statusline.js`
5. Configurar em `.claude/settings.json`

### Adicionar Novo Hook ao Tracking
1. Editar `.claude/settings.json`
2. Substituir comando do hook por: `node .claude/hooks/hook-wrapper.js <nome-do-hook>`
3. Verificar se hook aparece em `hooks-status.json` após execução

---

## 📜 Histórico

**2025-11-14 (Commit 1fefd6f):** Implementação inicial do Legal-Braniac com hook wrapper
**2025-11-14 (Commit anterior):** Expansão para os 6 agentes restantes (clean UI)
**2025-11-14 (Commit 7d70fc5):** ✅ FASE 1 - Hook wrappers para todos os 7 hooks
**2025-11-14 (Commit 5f7b236):** ✅ FASE 2 - Detecção de agentes ativos (active-agents-detector.js)
**2025-11-14 (Commit 301ab8c):** ✅ FASE 3 - UI final com status de hooks em todos os statuslines

---

## ✅ Status do Projeto

**FASE 1 (Hook Wrappers):** ✅ COMPLETA
- Todos os 7 hooks trackeados via `hook-wrapper.js`
- Arquivo `hooks-status.json` gerado automaticamente
- Sistema transparente sem interferência

**FASE 2 (Agentes Ativos):** ✅ COMPLETA
- Detector implementado (`active-agents-detector.js`)
- Arquivo `active-agents.json` gerado automaticamente
- Integração com Legal-Braniac statusline

**FASE 3 (UI Final):** ✅ COMPLETA
- Todos os 7 statuslines exibem status de hooks
- Legal-Braniac exibe agentes ativos
- Indicadores visuais: (OK), (ERR), (N/M OK), (all ✓)

---

## 🎯 Funcionalidades Futuras (Opcional)

1. Adicionar métricas de performance (duração média de hooks)
2. Implementar alertas visuais para hooks com falhas frequentes
3. Dashboard web para visualização de histórico de execuções
4. Exportação de logs de hooks para análise externa

---

**Última atualização:** 2025-11-14
**Mantido por:** PedroGiudice
**Sistema:** Claude Code v2.0.31
