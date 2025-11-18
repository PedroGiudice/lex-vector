# Prompt para Claude Code Web: Unified Statusline (Gordon + Legal-Braniac + Powerline)

## Contexto do Projeto

Você está trabalhando em um projeto que possui:

1. **Legal-Braniac**: Sistema de orchestration de agentes/skills com tracking via session files
2. **vibe-log Gordon Co-pilot**: Sistema de análise de prompts em tempo real com Claude SDK
3. **Powerline Visual**: Design profissional com arrows e cores ANSI 256

**Problema atual**: Temos duas statuslines separadas:
- Statusline nativa do vibe-log (Gordon Co-pilot) - mostra apenas análise de prompts
- Statusline personalizada (hybrid-powerline-statusline.js) - mostra apenas tracking Legal-Braniac

**Objetivo**: Criar statusline UNIFICADA que combine AMBAS as funcionalidades em design profissional.

---

## Arquitetura Descoberta

### 1. vibe-log Gordon Co-pilot - Como Funciona

**Flow de análise**:
```
User Prompt → UserPromptSubmit hook → .claude/hooks/vibe-analyze-prompt.js
           → npx vibe-log-cli analyze-prompt --stdin
           → Claude SDK local analysis
           → ~/.vibe-log/analyzed-prompts/{sessionId}.json
```

**Arquivo de análise** (`~/.vibe-log/analyzed-prompts/{sessionId}.json`):
```json
{
  "score": 5,
  "quality": "poor",
  "suggestion": "Your message is just one word - we need to understand what you're actually building or testing.",
  "actionableSteps": "Start by clarifying: (1) What are you trying to build or test? (2) What's the context of your project? (3) What specific help do you need?",
  "contextualEmoji": "🎯",
  "timestamp": "2025-11-18T22:31:44.755Z",
  "sessionId": "b4efbe5f-ed86-43ef-b21b-a5c695ee9647",
  "originalPrompt": "teste",
  "missing": [
    "What you're trying to accomplish - is this a test file, a feature, a bug fix, or something else?",
    "Context about your project - tech stack, where this code goes, what problem it solves"
  ]
}
```

**Campos importantes**:
- `score`: 0-100 (qualidade do prompt)
- `quality`: "excellent" | "good" | "fair" | "poor"
- `suggestion`: Mensagem do Gordon (tough love, business-focused)
- `contextualEmoji`: Emoji contextual (🎯, 💡, ⚡, etc)
- `sessionId`: DEVE coincidir com `process.env.CLAUDE_SESSION_ID`

**Localização dos arquivos**:
- Análises: `~/.vibe-log/analyzed-prompts/{sessionId}.json`
- Session ID: `process.env.CLAUDE_SESSION_ID` ou `.claude/hooks/legal-braniac-session.json`

**Timing**:
- Análise é assíncrona (background process)
- Primeiro renderiza "Gordon analyzing..." (loading state)
- Depois atualiza com score real quando análise completa
- Staleness: considerar análises >5min como stale

---

### 2. Legal-Braniac - Como Funciona

**Arquivo de sessão** (`.claude/hooks/legal-braniac-session.json`):
```json
{
  "sessionId": "b4efbe5f-ed86-43ef-b21b-a5c695ee9647",
  "sessionStart": 1731967104755,
  "agents": {
    "available": [
      { "name": "planejamento-legal", "file": "planejamento-legal.md" },
      { "name": "desenvolvimento", "file": "desenvolvimento.md" },
      // ... mais agentes
    ]
  },
  "skills": {
    "available": [
      { "name": "ocr-pro", "file": "SKILL.md" },
      { "name": "deep-parser", "file": "SKILL.md" },
      // ... mais skills
    ]
  },
  "hooks": {
    "UserPromptSubmit": 6,
    "SessionStart": 3,
    "SessionEnd": 3
  }
}
```

**Campos importantes**:
- `sessionId`: Identificador da sessão atual
- `sessionStart`: Timestamp (milliseconds) do início da sessão
- `agents.available.length`: Total de agentes disponíveis
- `skills.available.length`: Total de skills disponíveis
- `hooks`: Contagem de hooks por tipo

**Localização**: `.claude/hooks/legal-braniac-session.json` (relativo a `process.env.CLAUDE_PROJECT_DIR`)

**Dados adicionais**:
- Virtual environment: `process.env.VIRTUAL_ENV` (● se ativo, ○ se inativo)
- Git branch: `git rev-parse --abbrev-ref HEAD`
- Git status: `git status --porcelain` (adiciona `*` se dirty)

---

### 3. Powerline Visual System

**Cores ANSI 256** (palette harmonioso):
```javascript
const powerline = {
  bg: {
    gordon: '\x1b[48;5;24m',      // Deep blue
    braniac: '\x1b[48;5;54m',     // Rich purple
    session: '\x1b[48;5;30m',     // Ocean teal
    stats: '\x1b[48;5;236m',      // Charcoal gray
    critical: '\x1b[48;5;124m',   // Dark red (warnings)
  },
  fg: {
    white: '\x1b[38;5;255m',      // Pure white
    yellow: '\x1b[38;5;226m',     // Bright yellow
    green: '\x1b[38;5;42m',       // Vibrant green
    cyan: '\x1b[38;5;51m',        // Bright cyan
    orange: '\x1b[38;5;208m',     // Orange
    purple: '\x1b[38;5;141m',     // Soft purple
    red: '\x1b[38;5;196m',        // Bright red
  },
  arrow: '▶',
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
};
```

**Função de segmento** (ver hybrid-powerline-statusline.js.backup:105-122):
```javascript
function segment(content, bgColor, fgColor, nextBgColor = null) {
  const main = `${bgColor}${fgColor} ${content} ${powerline.reset}`;

  let arrow = '';
  if (nextBgColor) {
    const arrowFg = bgColor.replace('48', '38');
    arrow = `${nextBgColor}${arrowFg}${powerline.arrow}${powerline.reset}`;
  } else {
    const arrowFg = bgColor.replace('48', '38');
    arrow = `${arrowFg}${powerline.arrow}${powerline.reset}`;
  }

  return main + arrow;
}
```

**Layout responsivo** (baseado em terminal width):
- `< 80 cols`: Minimal mode (só duração + stats básicos)
- `80-120 cols`: Compact mode (Gordon score + Braniac + stats compactos)
- `120-160 cols`: Comfortable mode (Gordon full + Braniac + stats detalhados)
- `> 160 cols`: Wide mode (máximo detalhe possível)

---

## Especificações Técnicas

### Cache System (Performance Critical)

**Problema**: Statusline é chamado a cada render (~100ms ideal, <200ms aceitável)

**Solução**: Aggressive caching com TTLs diferenciados

```javascript
const CACHE_TTL = {
  'vibe-log': 30,      // Gordon analysis muda devagar
  'git-status': 5,     // Git muda com commits
  'braniac': 2,        // Session data quasi-estático
  'session': 1,        // Timestamp precisa ser fresco
};
```

**Implementação** (ver hybrid-powerline-statusline.js.backup:35-62):
```javascript
function getCachedData(key, fetchFn) {
  const cache = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8') || '{}');
  const entry = cache[key];
  const ttl = CACHE_TTL[key] || 5;
  const now = Date.now();

  if (entry && (now - entry.timestamp) < (ttl * 1000)) {
    return entry.data; // Cache HIT
  }

  const freshData = fetchFn();
  cache[key] = { data: freshData, timestamp: now };
  fs.writeFileSync(CACHE_FILE, JSON.stringify(cache));
  return freshData;
}
```

**Cache file**: `.claude/cache/statusline-cache.json`

**Performance target**: <200ms total execution time (já atingido com cache)

---

### Session ID Matching (CRÍTICO)

**Problema descoberto**: Análises do Gordon são salvas por sessionId. Se o sessionId não coincidir, statusline não encontra a análise.

**Solução**: Sempre usar MESMO sessionId em ambos os sistemas.

**Priority order** (tentar nesta sequência):
1. `process.env.CLAUDE_SESSION_ID` (variável de ambiente do Claude Code)
2. `.claude/hooks/legal-braniac-session.json` → `sessionId` field
3. Fallback: `null` (sem session tracking)

**Implementação** (ver hybrid-powerline-statusline.js.backup:138-156):
```javascript
function getCurrentSessionId() {
  if (process.env.CLAUDE_SESSION_ID) {
    return process.env.CLAUDE_SESSION_ID;
  }

  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const sessionFile = path.join(projectDir, '.claude', 'hooks', 'legal-braniac-session.json');

    if (fs.existsSync(sessionFile)) {
      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
      return data.sessionId || null;
    }
  } catch (e) { /* ignore */ }

  return null;
}
```

---

### Gordon Analysis Reader

**Função principal** (combinar com cache system):

```javascript
function getGordonAnalysis() {
  return getCachedData('vibe-log', () => {
    try {
      const sessionId = getCurrentSessionId();
      if (!sessionId) return null;

      const analysisFile = path.join(
        process.env.HOME || process.env.USERPROFILE,
        '.vibe-log',
        'analyzed-prompts',
        `${sessionId}.json`
      );

      if (!fs.existsSync(analysisFile)) return null;

      const analysis = JSON.parse(fs.readFileSync(analysisFile, 'utf8'));

      // Check staleness (< 5 minutes)
      const timestamp = new Date(analysis.timestamp);
      const age = Date.now() - timestamp.getTime();
      if (age > 5 * 60 * 1000) return null; // Stale

      return analysis;
    } catch (e) {
      return null;
    }
  });
}
```

**Retorno esperado**: Objeto com `{score, quality, suggestion, contextualEmoji}` ou `null` se não disponível.

---

### Legal-Braniac Data Reader

**Função principal**:

```javascript
function getBraniacData() {
  return getCachedData('braniac', () => {
    try {
      const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
      const sessionFile = path.join(projectDir, '.claude', 'hooks', 'legal-braniac-session.json');

      if (!fs.existsSync(sessionFile)) return null;

      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));

      return {
        sessionId: data.sessionId,
        sessionStart: data.sessionStart,
        agentCount: data.agents?.available?.length || 0,
        skillCount: data.skills?.available?.length || 0,
        hookCount: Object.keys(data.hooks || {}).length || 0,
      };
    } catch (e) {
      return null;
    }
  });
}
```

---

### Git Status (Cached)

```javascript
function getGitStatus() {
  return getCachedData('git-status', () => {
    try {
      const branch = execSync('git rev-parse --abbrev-ref HEAD', {
        encoding: 'utf8',
        timeout: 1000,
        stdio: ['pipe', 'pipe', 'pipe']
      }).trim();

      const status = execSync('git status --porcelain', {
        encoding: 'utf8',
        timeout: 1000,
        stdio: ['pipe', 'pipe', 'pipe']
      }).trim();

      // Truncate long branch names
      let b = branch;
      if (b.length > 25) {
        b = b.substring(0, 22) + '...';
      }

      return status.length > 0 ? `${b}*` : b;
    } catch (error) {
      return '?';
    }
  });
}
```

---

### Session Duration Formatter

```javascript
function formatSessionDuration(sessionStart) {
  const durationMin = Math.floor((Date.now() - sessionStart) / 60000);

  if (durationMin < 60) {
    return `${durationMin}m`;
  } else {
    const h = Math.floor(durationMin / 60);
    const m = durationMin % 60;
    return `${h}h${m}m`;
  }
}
```

---

## Layout Proposto

### Compact Mode (80-120 cols)

```
┌─────────────────────────┐┌──────────────┐┌──────────┐┌────────────────────┐
│ 🎯 Gordon: 85/100 Good  ││ Braniac ● 7ag││ ⏱ 2h34m ││ 7a 34s 6h │ venv ● │
└─────────────────────────┘└──────────────┘└──────────┘└────────────────────┘
                                                         │ git main*          │
                                                         └────────────────────┘
```

**Prioridades** (ordem de corte quando espaço insuficiente):
1. Gordon score (sempre visível)
2. Session duration (sempre visível)
3. Braniac agent count
4. Stats (agents, skills, hooks)
5. Git status

### Comfortable Mode (120-160 cols)

```
┌──────────────────────────────────┐┌──────────────┐┌────────────────┐┌──────────────────────────────────────┐
│ 🎯 Gordon: 85/100 - Clear prompt ││ Braniac ● 7ag││ ⏱ Session 2h34m││ 7 agents │ 34 skills │ 6 hooks      │
└──────────────────────────────────┘└──────────────┘└────────────────┘│ venv ● │ git main*                   │
                                                                       └──────────────────────────────────────┘
```

### Wide Mode (>160 cols)

```
┌────────────────────────────────────────────────────────┐┌──────────────┐┌────────────────┐┌─────────────────────────────────────────────────┐
│ 🎯 Gordon: 85/100 - Clear and focused prompt structure ││ Braniac ● 7ag││ ⏱ Session 2h34m││ 7 agents │ 34 skills │ 6 hooks │ venv ● │ git main*│
└────────────────────────────────────────────────────────┘└──────────────┘└────────────────┘└─────────────────────────────────────────────────┘
```

### Minimal Mode (<80 cols)

```
┌──────┐┌──────────────────────────┐
│ 2h34m││ 7a 34s │ ● │ main*        │
└──────┘└──────────────────────────┘
```

---

## Estados Especiais

### 1. Gordon Loading State

**Quando**: Análise ainda em progresso (arquivo não existe ou muito recente)

```
┌──────────────────────────┐
│ 🔄 Gordon analyzing...   │
└──────────────────────────┘
```

### 2. Gordon Score-Based Coloring

**Score 81-100** (Excellent):
- Background: `powerline.bg.gordon` (deep blue)
- Foreground: `powerline.fg.green` (vibrant green)
- Emoji: 🎯 ou ⚡

**Score 61-80** (Good):
- Background: `powerline.bg.gordon`
- Foreground: `powerline.fg.cyan`
- Emoji: 💡

**Score 41-60** (Fair):
- Background: `powerline.bg.gordon`
- Foreground: `powerline.fg.yellow`
- Emoji: ⚠️

**Score 0-40** (Poor):
- Background: `powerline.bg.critical` (dark red)
- Foreground: `powerline.fg.white`
- Emoji: 🚨

### 3. Braniac States

**Active** (agents available):
```
Braniac ● 7ag
```

**Inactive** (no agents):
```
Braniac ○
```

### 4. Virtual Environment

**Active**: `venv ●` (green dot)
**Inactive**: `venv ○` (gray dot)

### 5. Git Dirty Flag

**Clean**: `main`
**Dirty**: `main*` (asterisk indicates uncommitted changes)

---

## Código de Referência

### Arquivo atual (NÃO funcionando completamente)

`.claude/statusline/hybrid-powerline-statusline.js.backup` (linhas 1-531)

**Problemas identificados**:
1. Linha 122: Tentava chamar comando que não existe via spawn
2. Não lê corretamente os arquivos de análise do Gordon
3. Cache system implementado mas sem usar para Gordon analysis
4. Layout responsivo existe mas não prioriza Gordon quando espaço limitado

### Arquivos de backup/referência

- `.claude/settings.json.backup`: Configuração original antes de desabilitar statusline
- `.claude/statusline/BACKUP_INFO.md`: Documentação do que foi mudado
- `~/.vibe-log/analyzed-prompts/{sessionId}.json`: Exemplo de análise real

---

## Requisitos Funcionais

### DEVE ter

1. **Gordon Analysis Display**
   - Ler análise de `~/.vibe-log/analyzed-prompts/{sessionId}.json`
   - Mostrar score + emoji + mensagem (truncada se necessário)
   - Loading state quando análise em progresso
   - Color coding baseado em score
   - Staleness check (>5min = não mostrar)

2. **Legal-Braniac Tracking**
   - Ler `.claude/hooks/legal-braniac-session.json`
   - Mostrar contagem de agentes, skills, hooks
   - Session duration calculada de `sessionStart`

3. **System Status**
   - Virtual environment (● ou ○)
   - Git branch + dirty flag
   - Session duration

4. **Performance**
   - <200ms execution time
   - Aggressive caching (TTLs diferenciados)
   - Graceful degradation se comandos falharem

5. **Responsive Layout**
   - Minimal (<80 cols)
   - Compact (80-120 cols)
   - Comfortable (120-160 cols)
   - Wide (>160 cols)
   - Auto-detect via `process.stdout.columns`

6. **Visual Design**
   - Powerline arrows (▶) entre segmentos
   - ANSI 256 color palette (harmoniosa)
   - Emojis contextuais do Gordon
   - Bold/dim para hierarquia visual

### NICE to have

1. **Token Usage Tracking** (future integration com ccusage)
2. **Last Agent Used** (via last-used.json)
3. **Multi-line mode** para terminais ultra-wide
4. **Blink effect** para análises muito recentes (<10s)
5. **Notification dot** quando novo agent/skill disponível

---

## Casos de Teste

### 1. Gordon Analysis Disponível

**Input**:
- `~/.vibe-log/analyzed-prompts/{sessionId}.json` existe
- Análise tem score 85
- Quality: "good"
- Suggestion: "Clear and focused prompt"
- contextualEmoji: "🎯"

**Output esperado** (compact mode):
```
🎯 Gordon: 85/100 Good
```

**Output esperado** (comfortable mode):
```
🎯 Gordon: 85/100 - Clear and focused prompt
```

### 2. Gordon Loading

**Input**:
- Arquivo de análise não existe OU
- Timestamp < 10s atrás

**Output esperado**:
```
🔄 Gordon analyzing...
```

### 3. Gordon Stale

**Input**:
- Análise existe mas timestamp > 5min

**Output esperado**:
- Fallback para mensagem genérica ou omitir segmento Gordon

### 4. Legal-Braniac Active

**Input**:
- `.claude/hooks/legal-braniac-session.json` existe
- `agents.available.length = 7`
- `skills.available.length = 34`
- `hooks` tem 3 entradas

**Output esperado** (compact):
```
Braniac ● 7ag
```

**Output esperado** (comfortable):
```
7 agents │ 34 skills │ 3 hooks
```

### 5. Terminal Width = 70 (Minimal)

**Output esperado**:
```
2h34m│7a 34s│●│main*
```

### 6. Terminal Width = 100 (Compact)

**Output esperado**:
```
🎯 Gordon: 85/100│Braniac ● 7ag│⏱ 2h34m│7a 34s 3h│venv ●│git main*
```

### 7. Terminal Width = 150 (Comfortable)

**Output esperado**:
```
🎯 Gordon: 85/100 - Clear prompt│Braniac ● 7ag│⏱ Session 2h34m│7 agents│34 skills│3 hooks│venv ●│git main*
```

### 8. Git Dirty

**Input**: `git status --porcelain` retorna conteúdo

**Output esperado**: `main*` (com asterisk)

### 9. Venv Inactive

**Input**: `process.env.VIRTUAL_ENV` é `undefined`

**Output esperado**: `venv ○` (círculo vazio)

### 10. Session ID Mismatch

**Input**:
- `CLAUDE_SESSION_ID = "abc123"`
- Análise existe para `sessionId = "def456"`

**Output esperado**:
- Não encontra análise (sessionId mismatch)
- Mostra loading state ou fallback

---

## Checklist de Implementação

### Fase 1: Setup Básico
- [ ] Criar arquivo `unified-statusline.js`
- [ ] Implementar cache system com TTLs
- [ ] Implementar função `getCurrentSessionId()`
- [ ] Implementar powerline visual (segment function)
- [ ] Criar constantes de cores ANSI 256

### Fase 2: Data Readers
- [ ] Implementar `getGordonAnalysis()` com session ID matching
- [ ] Implementar `getBraniacData()` lendo session file
- [ ] Implementar `getGitStatus()` com caching
- [ ] Implementar `formatSessionDuration()`
- [ ] Implementar verificação de virtual environment

### Fase 3: Layout Modes
- [ ] Implementar `layoutMinimal()`
- [ ] Implementar `layoutCompact()`
- [ ] Implementar `layoutComfortable()`
- [ ] Implementar `layoutWide()`
- [ ] Implementar auto-detection baseado em `process.stdout.columns`

### Fase 4: Gordon Integration
- [ ] Loading state ("🔄 Gordon analyzing...")
- [ ] Score-based color coding
- [ ] Emoji contextual mapping
- [ ] Staleness check (>5min)
- [ ] Message truncation responsiva

### Fase 5: Testing
- [ ] Test com análise disponível (score 85)
- [ ] Test com loading state (arquivo não existe)
- [ ] Test com stale analysis (>5min)
- [ ] Test com session ID mismatch
- [ ] Test em diferentes terminal widths (70, 100, 150, 200 cols)
- [ ] Test com git dirty/clean
- [ ] Test com venv active/inactive
- [ ] Test com Legal-Braniac session file ausente
- [ ] Performance test (<200ms execution)

### Fase 6: Error Handling
- [ ] Graceful degradation se Gordon file inacessível
- [ ] Graceful degradation se Braniac file inacessível
- [ ] Fallback se git commands falharem
- [ ] Fallback visual se terminal width não detectável
- [ ] Logs de debug opcionais (via env var `DEBUG_STATUSLINE=true`)

### Fase 7: Documentation
- [ ] Comentários inline explicando arquitetura
- [ ] README.md com instruções de instalação
- [ ] Atualizar CLAUDE.md com seção "Unified Statusline"
- [ ] Criar exemplos visuais (screenshots ou ASCII art)

---

## Instalação e Configuração

### Arquivo a criar

`.claude/statusline/unified-statusline.js` (novo arquivo, não editar hybrid-powerline)

### Configuração em `.claude/settings.json`

```json
{
  "statusLine": {
    "type": "command",
    "command": "cd \"$CLAUDE_PROJECT_DIR\" && node .claude/statusline/unified-statusline.js",
    "padding": 0,
    "_note": "Unified statusline v1.0 - Gordon Co-pilot + Legal-Braniac + Powerline visual"
  }
}
```

### Dependências

- Node.js (já instalado)
- Git (para comandos git status/branch)
- Arquivos necessários:
  - `~/.vibe-log/analyzed-prompts/{sessionId}.json` (criado por vibe-analyze-prompt.js hook)
  - `.claude/hooks/legal-braniac-session.json` (criado por legal-braniac-loader.js hook)
  - `.claude/cache/statusline-cache.json` (criado automaticamente pelo cache system)

### Validação

```bash
# Test manual
cd ~/claude-work/repos/Claude-Code-Projetos
node .claude/statusline/unified-statusline.js

# Test com width específica
COLUMNS=100 node .claude/statusline/unified-statusline.js

# Test em modo debug
DEBUG_STATUSLINE=true node .claude/statusline/unified-statusline.js
```

---

## Notas Finais

- **Não usar emojis excessivos**: Apenas o contextual emoji do Gordon + indicadores de status (●, ○)
- **Performance é crítica**: Cache agressivo é OBRIGATÓRIO (target <200ms)
- **Session ID matching é crítico**: Sem isso, Gordon analysis nunca aparecerá
- **Responsive layout é essencial**: Deve funcionar bem em terminais de 70 a 200+ colunas
- **Color coding deve ser sutil**: Não transformar em arco-íris, manter profissional
- **Fallback sempre**: Se algo falhar, ainda renderizar statusline básica (não crashar)

---

## Arquivos de Referência para Consulta

Todos os arquivos estão em: `~/claude-work/repos/Claude-Code-Projetos/`

1. `.claude/statusline/hybrid-powerline-statusline.js.backup` - Implementação anterior (referência visual + cache system)
2. `.claude/statusline/BACKUP_INFO.md` - Histórico de mudanças
3. `.claude/hooks/vibe-analyze-prompt.js` - Como análise é gerada
4. `.claude/hooks/legal-braniac-loader.js` - Como session file é criado
5. `~/.vibe-log/analyzed-prompts/b4efbe5f-ed86-43ef-b21b-a5c695ee9647.json` - Exemplo de análise real

---

## Pergunta Final

Depois de implementar, precisamos decidir:

1. **Desabilitar vibe-log statusline nativa** e usar apenas a unified?
2. **Manter ambas** (vibe-log como fallback)?

Recomendação: **Opção 1** (unified exclusiva), pois:
- Evita duplicação de lógica
- Performance melhor (um único script)
- Design mais coeso
- Mais fácil de manter

Se unified statusline funcionar conforme especificado, a vibe-log nativa torna-se redundante.

---

**Última atualização**: 2025-11-18
**Versão**: 1.0
**Target**: Claude Code Web (unlimited tokens session)
