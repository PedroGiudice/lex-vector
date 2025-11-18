# Plano de Integração: ccstatusline + Nossa Statusline

**Data:** 2025-11-18
**Objetivo:** Combinar visual rico do ccstatusline com nossas funcionalidades (cache 10.8x, tracking SQLite, blinking)

---

## 1. ANÁLISE TÉCNICA

### 1.1. ccstatusline (Upstream)

**Stack:** TypeScript + React/Ink (compilado para Node.js bundle)
**Localização:** `/opt/node22/lib/node_modules/ccstatusline/`
**Versão:** 2.0.23

**Como funciona:**
```
Input (stdin):  JSON com session info
                ↓
Process:        React/Ink TUI → renderiza widgets
                ↓
Output:         ANSI-formatted statusline (multi-linha)
```

**Widgets disponíveis:**
- ✅ Model Name (Sonnet 4, Opus 4, etc.)
- ✅ Context % (dinâmico: 1M tokens Sonnet 4.5, 200k outros)
- ✅ Git Branch + status (clean/dirty)
- ✅ Token Usage (total, input, output, cache)
- ✅ Session Duration
- ✅ Block Timer (5-hour window)
- ✅ Custom Text (estático)
- ✅ **Custom Command** (executa shell command) ⭐
- ✅ Separator (visual dividers)

**Features:**
- Powerline separators (arrows, caps)
- Color support: 16-color, 256-color, truecolor (hex)
- Multi-linha (até 3 linhas)
- Widget merging (com/sem padding)

### 1.2. Nossa Statusline Atual

**Stack:** Node.js vanilla (professional-statusline.js)
**Features críticas:**
- ✅ **Cache 10.8x:** Reduz latência de 3.4s → 0.05s
- ✅ **Tracking SQLite:** Agents, hooks, skills (simple_tracker.py)
- ✅ **Blinking indicators:** ANSI `\x1b[5m` para atividade < 5s
- ✅ **Logging estruturado:** Observabilidade em `.claude/monitoring/logs/`
- ✅ **Visual Powerline:** Cores harmoniosas (cyan, magenta, purple, etc.)

**Dados custom:**
- Legal-Braniac status (loaded, agents count, skills count)
- Virtual agents tracking (active/total)
- Hooks recent executions (< 5s blinking)
- Session duration (minutos/horas)
- Venv status (● active, ○ inactive)
- Git status (branch, dirty indicator)

**Cache TTLs:**
```javascript
const CACHE_TTL = {
  'vibe-log': 30,      // Gordon analysis
  'git-status': 5,     // Git changes
  'tracker': 2,        // Real-time tracking
  'session-file': 1,   // Session metadata
};
```

---

## 2. ESTRATÉGIA DE INTEGRAÇÃO

### Opção Selecionada: **WRAPPER HYBRID** ✅

**Arquitetura:**
```
┌───────────────────────────────────────────────────────────┐
│ hybrid-statusline.js (WRAPPER)                            │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ Line 1: ccstatusline output (visual rico)             │ │
│ │   ▸ Sonnet 4 ● │ main* │ 45K tokens │ 1h23m           │ │
│ └───────────────────────────────────────────────────────┘ │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ Line 2: Legal-Braniac + Tracking (nossos dados)       │ │
│ │   ● Legal-Braniac ● 8m │ ● 7 agents │ ● 38 skills     │ │
│ └───────────────────────────────────────────────────────┘ │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ Line 3: Technical Status (cache, venv, hooks)         │ │
│ │   ● 4 hooks │ venv ● │ cache 98% hits                 │ │
│ └───────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
          ↓ calls subprocess
┌───────────────────────────────────────────────────────────┐
│ ccstatusline (TypeScript/React)                           │
│ - Widgets: Model, Git, Tokens, Session                   │
│ - Powerline separators, truecolor                        │
└───────────────────────────────────────────────────────────┘
```

**Justificativa:**
1. ✅ **Rápido:** 2-4 horas implementação vs 1-2 semanas (fork)
2. ✅ **Preserva features críticas:** Cache 10.8x, logging, tracking
3. ✅ **Visual rico:** Aproveita powerline do ccstatusline
4. ✅ **Manutenível:** Sem fork, updates upstream gratuitos
5. ✅ **Iterável:** Funciona já, pode refinar depois

**Trade-offs:**
- ⚠️ Dupla execução: ccstatusline + nossa lógica (~50-100ms overhead)
- ⚠️ Complexidade: Coordenar dois sistemas
- ✅ Benefício: Visual profissional + funcionalidades custom

---

## 3. PLANO DE EXECUÇÃO

### FASE 1: Testes e Validação (30 min)

**Task 1.1: Testar ccstatusline standalone**
```bash
# Criar payload de teste
cat > /tmp/test-payload.json << 'EOF'
{
  "session_id": "test-123",
  "model": {
    "display_name": "Sonnet 4",
    "max_context_tokens": 1000000
  },
  "workspace": {
    "current_dir": "/home/user/Claude-Code-Projetos"
  },
  "tokens": {
    "total": 45000,
    "input": 30000,
    "output": 15000
  },
  "cost": {
    "total_cost_usd": 0.23
  }
}
EOF

# Testar ccstatusline
cat /tmp/test-payload.json | /opt/node22/bin/ccstatusline

# Expected output: Statusline formatada com ANSI colors
```

**Task 1.2: Mapear widgets duplicados**
| Widget | ccstatusline | Nossa Statusline | Ação |
|--------|--------------|------------------|------|
| Model Name | ✅ Native | ❌ N/A | Usar ccstatusline |
| Git Branch | ✅ Native | ✅ Cached | Usar ccstatusline (remover nosso) |
| Session Duration | ✅ Native | ✅ Custom | Usar ccstatusline |
| Tokens | ✅ Native | ❌ N/A | Usar ccstatusline |
| Legal-Braniac | ❌ N/A | ✅ Custom | Manter nosso (Line 2) |
| Agents/Skills/Hooks | ❌ N/A | ✅ Tracking | Manter nosso (Line 2) |
| Venv Status | ❌ N/A | ✅ Custom | Manter nosso (Line 3) |
| Cache Stats | ❌ N/A | ✅ Custom | Manter nosso (Line 3) |

**Task 1.3: Validar ANSI passthrough**
```bash
# Testar se ccstatusline preserva ANSI codes no output
echo '{"test": true}' | /opt/node22/bin/ccstatusline | cat -A

# Verificar blinking: \x1b[5m deve aparecer no output
# Se não, precisamos implementar blinking em nossa Line 2/3
```

**Checkpoint 1:** ccstatusline funciona + widgets mapeados + ANSI validado

---

### FASE 2: Implementação Wrapper (1.5 - 2 horas)

**Task 2.1: Criar estrutura do hybrid-statusline.js**

```javascript
#!/usr/bin/env node
/**
 * Hybrid Statusline - ccstatusline + Legal-Braniac Tracking
 *
 * Architecture:
 * Line 1: ccstatusline (Model, Git, Tokens, Session)
 * Line 2: Legal-Braniac + Tracking (Agents, Skills, Hooks)
 * Line 3: Technical Status (Venv, Cache, Logging)
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ============================================================================
// CACHE SYSTEM (Preserve 10.8x speedup)
// ============================================================================
const CACHE_DIR = path.join(process.env.CLAUDE_PROJECT_DIR || process.cwd(), '.claude', 'cache');
const CACHE_FILE = path.join(CACHE_DIR, 'statusline-cache.json');

const CACHE_TTL = {
  'ccstatusline': 5,   // ccstatusline output (5s cache)
  'tracker': 2,        // SQLite tracking (2s cache)
  'session-file': 1,   // Session metadata (1s cache)
};

function getCachedData(key, fetchFn) {
  try {
    let cache = {};
    if (fs.existsSync(CACHE_FILE)) {
      cache = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8'));
    }

    const entry = cache[key];
    const ttl = CACHE_TTL[key] || 5;
    const now = Date.now();

    if (entry && entry.timestamp && (now - entry.timestamp) < (ttl * 1000)) {
      return entry.data; // Cache HIT
    }

    // Cache MISS - fetch fresh
    const freshData = fetchFn();

    cache[key] = {
      data: freshData,
      timestamp: now
    };

    fs.mkdirSync(CACHE_DIR, { recursive: true });
    fs.writeFileSync(CACHE_FILE, JSON.stringify(cache));

    return freshData;
  } catch (error) {
    return fetchFn(); // Fallback: no cache
  }
}

// ============================================================================
// LINE 1: ccstatusline (SUBPROCESS CALL)
// ============================================================================
function getLine1_ccstatusline(claudeInput) {
  return getCachedData('ccstatusline', () => {
    try {
      // Pass Claude input to ccstatusline via stdin
      const output = execSync('/opt/node22/bin/ccstatusline', {
        input: JSON.stringify(claudeInput),
        encoding: 'utf8',
        timeout: 5000,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      return output.trim();
    } catch (error) {
      // Fallback: minimal line
      const model = claudeInput.model?.display_name || 'Claude';
      return `▸ ${model} | Claude Code`;
    }
  });
}

// ============================================================================
// LINE 2: Legal-Braniac + Tracking (NOSSA LÓGICA)
// ============================================================================
function getLine2_LegalBraniac() {
  // ... (reuse existing code from professional-statusline.js)
  // - Legal-Braniac status (with blinking if < 5s ago)
  // - Agents count (with blinking if active)
  // - Skills count (with blinking if active)
  // - Hooks count (with blinking if recent)
}

// ============================================================================
// LINE 3: Technical Status (CACHE, VENV, ETC)
// ============================================================================
function getLine3_TechnicalStatus() {
  // ... (cache hit rate, venv status, etc.)
}

// ============================================================================
// MAIN
// ============================================================================
function main() {
  try {
    // Read Claude input from stdin
    let claudeInput = {};
    const stdinBuffer = fs.readFileSync(0, 'utf-8'); // fd 0 = stdin
    if (stdinBuffer.trim()) {
      claudeInput = JSON.parse(stdinBuffer);
    }

    // Get lines
    const line1 = getLine1_ccstatusline(claudeInput);
    const line2 = getLine2_LegalBraniac();
    const line3 = getLine3_TechnicalStatus();

    // Output
    console.log(line1);
    console.log(line2);
    console.log(line3);

  } catch (error) {
    // Fallback: minimal output
    console.log('▸ Claude Code | Legal-Braniac');
  }
}

main();
```

**Task 2.2: Portar código existente**
- Copiar funções de cache de `professional-statusline.js`
- Copiar funções de tracking (agents, hooks, skills)
- Copiar funções de blinking indicators
- Adaptar para estrutura de 3 linhas

**Task 2.3: Integrar simple_tracker.py**
```javascript
function getTrackerData() {
  return getCachedData('tracker', () => {
    try {
      const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
      const trackerPath = path.join(projectDir, '.claude', 'monitoring', 'simple_tracker.py');

      if (fs.existsSync(trackerPath)) {
        const output = execSync(`${trackerPath} statusline`, {
          encoding: 'utf8',
          timeout: 500,
          stdio: ['pipe', 'pipe', 'pipe']
        }).trim();

        // Parse: "🤖 0/0 │ ⚡ 0 │ 🛠️ -"
        const match = output.match(/🤖 (\d+)\/(\d+) │ ⚡ (\d+) │ 🛠️ (.+)/);
        if (match) {
          return {
            activeAgents: parseInt(match[1]),
            totalAgents: parseInt(match[2]),
            hooksRecent: parseInt(match[3]),
            skillsStr: match[4]
          };
        }
      }
    } catch (error) {
      // Silent fail
    }

    return null;
  });
}
```

**Checkpoint 2:** hybrid-statusline.js funciona + 3 linhas renderizadas + cache preservado

---

### FASE 3: Testes e Performance (30 min - 1 hora)

**Task 3.1: Teste de latência**
```bash
# Benchmark: latência total deve ser < 200ms
time cat /tmp/test-payload.json | node /home/user/Claude-Code-Projetos/.claude/statusline/hybrid-statusline.js

# Expected:
# real    0m0.150s  (ccstatusline: ~100ms + nossa lógica: ~50ms)
# user    0m0.080s
# sys     0m0.020s

# Se > 200ms: aumentar cache TTLs
```

**Task 3.2: Teste de blinking**
```bash
# Simular hook recente (< 5s ago)
# 1. Atualizar hooks-status.json com timestamp NOW
# 2. Executar statusline
# 3. Verificar output contém \x1b[5m (blinking ANSI code)

# Manual check:
node hybrid-statusline.js | cat -A
# Look for: ^[[5m●  (blinking indicator)
```

**Task 3.3: Teste de cache (hit rate)**
```bash
# Executar statusline 10x consecutivas
for i in {1..10}; do
  time cat /tmp/test-payload.json | node hybrid-statusline.js > /dev/null
done

# Primeira execução: ~150ms (cache MISS)
# Execuções 2-10: ~50ms (cache HIT) ← 3x speedup esperado
```

**Task 3.4: Validar cores e separadores**
- Verificar harmonização visual (ccstatusline Line 1 vs nossas Lines 2-3)
- Ajustar cores se necessário (professional palette)
- Testar em terminal com 256-color e truecolor

**Checkpoint 3:** Latência < 200ms + blinking funciona + cache 3x+ + visual harmonizado

---

### FASE 4: Refinamento e Documentação (30 min)

**Task 4.1: Implementar fallbacks**
```javascript
// Fallback 1: Se ccstatusline falha
function getLine1_ccstatusline(claudeInput) {
  return getCachedData('ccstatusline', () => {
    try {
      // ... call ccstatusline
    } catch (error) {
      // FALLBACK: Nossa minimal line 1
      const model = claudeInput.model?.display_name || 'Claude';
      const git = getGitStatus(); // Usar nossa função cached
      return `${colors.cyan}▸${colors.reset} ${colors.bright}${model}${colors.reset} ${colors.lightGray}│${colors.reset} ${colors.teal}${git}${colors.reset}`;
    }
  });
}

// Fallback 2: Se tracking SQLite falha
function getTrackerData() {
  return getCachedData('tracker', () => {
    try {
      // ... call simple_tracker.py
    } catch (error) {
      // FALLBACK: Use legal-braniac-session.json
      return getSessionFileData();
    }
  });
}
```

**Task 4.2: Logging estruturado**
```javascript
const LOG_DIR = path.join(process.env.CLAUDE_PROJECT_DIR || process.cwd(), '.claude', 'monitoring', 'logs');
const LOG_FILE = path.join(LOG_DIR, 'hybrid-statusline.log');

function logError(component, error) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    component,
    error: error.message,
    stack: error.stack
  };

  fs.mkdirSync(LOG_DIR, { recursive: true });
  fs.appendFileSync(LOG_FILE, JSON.stringify(logEntry) + '\n');
}

// Usage:
try {
  const output = execSync('/opt/node22/bin/ccstatusline', { ... });
} catch (error) {
  logError('ccstatusline-subprocess', error);
  // ... fallback
}
```

**Task 4.3: Atualizar settings.json**
```json
{
  "statusLine": {
    "type": "command",
    "command": "node /home/user/Claude-Code-Projetos/.claude/statusline/hybrid-statusline.js",
    "padding": 0
  }
}
```

**Task 4.4: Documentação**
- README.md atualizado (arquitetura híbrida)
- Comentários inline no código
- Troubleshooting guide (fallbacks, erros comuns)

**Checkpoint 4:** Fallbacks testados + logging funcional + documentação completa

---

## 4. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| ccstatusline muito lento (> 100ms) | Média | Alto | Cache sua saída (TTL: 5s) + fallback nossa Line 1 |
| Blinking não funciona (ccstatusline strip ANSI) | Baixa | Médio | Implementar em Lines 2-3 (controle total) |
| Conflito visual (ccstatusline vs nossas cores) | Média | Baixo | Testar em terminal + ajustar palette |
| Latência total > 200ms | Média | Alto | Profiling + cache agressivo + parallel execution |
| ccstatusline crash | Baixa | Alto | Try-catch + fallback completo |
| SQLite lock contention | Baixa | Médio | Timeout 10s + WAL mode (já implementado) |

---

## 5. MÉTRICAS DE SUCESSO

**Performance:**
- ✅ Latência total < 200ms (target: 150ms)
- ✅ Cache hit rate > 80% (target: 95%)
- ✅ ccstatusline overhead < 100ms

**Funcionalidades:**
- ✅ Blinking indicators funcionando (hooks < 5s)
- ✅ Tracking SQLite integrado
- ✅ Cache 10.8x preservado
- ✅ Logging estruturado ativo
- ✅ Visual Powerline harmonioso (3 linhas)

**Confiabilidade:**
- ✅ Fallbacks testados (ccstatusline fail, tracker fail)
- ✅ Zero crashes durante 1 hora de uso contínuo
- ✅ Logs de erros capturados (structured JSON)

---

## 6. PRÓXIMOS 3 COMANDOS EXATOS

### Comando 1: Testar ccstatusline standalone
```bash
cat > /tmp/test-payload.json << 'EOF'
{"session_id":"test-123","model":{"display_name":"Sonnet 4","max_context_tokens":1000000},"workspace":{"current_dir":"/home/user/Claude-Code-Projetos"},"tokens":{"total":45000,"input":30000,"output":15000},"cost":{"total_cost_usd":0.23}}
EOF

cat /tmp/test-payload.json | /opt/node22/bin/ccstatusline
```

### Comando 2: Criar esqueleto do hybrid-statusline.js
```bash
cat > /home/user/Claude-Code-Projetos/.claude/statusline/hybrid-statusline.js << 'EOF'
#!/usr/bin/env node
const { execSync } = require('child_process');
const fs = require('fs');

function main() {
  try {
    const stdin = fs.readFileSync(0, 'utf-8');
    const input = stdin.trim() ? JSON.parse(stdin) : {};

    // Line 1: ccstatusline
    const line1 = execSync('/opt/node22/bin/ccstatusline', {
      input: JSON.stringify(input),
      encoding: 'utf8',
      timeout: 5000
    }).trim();

    // Line 2: Placeholder
    const line2 = '● Legal-Braniac | Tracking';

    // Line 3: Placeholder
    const line3 = 'venv ● | cache ✓';

    console.log(line1);
    console.log(line2);
    console.log(line3);
  } catch (error) {
    console.log('▸ Claude Code | Legal-Braniac');
  }
}

main();
EOF

chmod +x /home/user/Claude-Code-Projetos/.claude/statusline/hybrid-statusline.js
```

### Comando 3: Testar esqueleto
```bash
cat /tmp/test-payload.json | node /home/user/Claude-Code-Projetos/.claude/statusline/hybrid-statusline.js
```

---

## 7. TIMELINE ESTIMADO

| Fase | Duração | Acumulado |
|------|---------|-----------|
| FASE 1: Testes e Validação | 30 min | 0.5h |
| FASE 2: Implementação Wrapper | 2 horas | 2.5h |
| FASE 3: Testes e Performance | 1 hora | 3.5h |
| FASE 4: Refinamento | 30 min | **4 horas** |

**Total estimado:** 4 horas (meio dia de trabalho)

---

## 8. FALLBACK PLAN

Se em FASE 3 descobrimos que ccstatusline não funciona (crashes, muito lento, conflitos):

**Plan B:** Usar apenas nossa statusline (professional-statusline.js)
- ✅ Já funciona perfeitamente
- ✅ Cache 10.8x garantido
- ✅ Blinking indicators garantidos
- ❌ Perde visual rico do ccstatusline (mas ainda temos Powerline próprio)

**Decisão:** Testar ccstatusline por 1 hora. Se > 3 problemas críticos → abortar e usar Plan B.

---

**Última atualização:** 2025-11-18
**Status:** Ready for execution
**Próximo passo:** Executar Comando 1 (testar ccstatusline)
