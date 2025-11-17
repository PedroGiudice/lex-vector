# Statusline UI - Roadmap de Finalização RIGOROSA

**Objetivo:** Transformar statusline em produto profissional completo com integração VibbinLoggin

**User Directive (verbatim):**
> "Implementa os hooks do vibelogging. Planeja antes. Hooks são chatos. Seja bastante rigoroso nessa etapa, não pule fases nem aceite downgradings."

---

## Status Atual (2025-11-15)

### ✅ Implementado
- [x] Arquitetura modular (`lib/` subdirectory)
- [x] Color palette vibrant (cyan, green, blue, purple - NO dark colors)
- [x] Liquid spinner customizado (24 frames, transparency fade)
- [x] Layout 2-colunas (70% relevant / 30% context)
- [x] Separadores horizontais profissionais
- [x] Tracking de Legal-Braniac (EXTREMELY RELEVANT per user)
- [x] Context % dinâmico (3 estratégias, não mais stuck em 23%)
- [x] Skills auto-detection (5 available via superpowers + Anthropic)
- [x] Git status (branch, dirty state)
- [x] Hooks status (idle detection)
- [x] Python venv detection
- [x] Session time tracking
- [x] MCP server monitoring
- [x] Agents counting (5 agentes)

### ❌ Pendente
- [ ] **VibbinLoggin hooks installation** (CRITICAL - shows "no data yet")
- [ ] VibbinLoggin metrics display (quality, category, sentiment)
- [ ] Performance optimization (580ms → <200ms target)
- [ ] Error handling robusto
- [ ] Cache invalidation strategy
- [ ] Hook execution time tracking
- [ ] Visual regression testing

---

## FASE 1: VibbinLoggin Hooks Integration (RIGOROSO)

**Problema:** `vibe-log-cli` está instalado (v0.8.1) mas hooks não geram dados.

**Análise:**
```bash
$ which vibe-log
/home/cmr-auto/.nvm/versions/node/v24.11.1/bin/vibe-log

$ vibe-log --version
0.8.1
```

**VibbinLoggin disponibiliza 4 hooks principais:**

### 1. SessionStart Hook
**Trigger:** Início de sessão Claude Code
**Responsabilidade:** Inicializar contexto da sessão no vibe-log
**Output:** Session ID, timestamp inicial, contexto do projeto

**Implementação:**
```javascript
// .claude/hooks/vibe-session-start.js
const { execSync } = require('child_process');

function main() {
  const sessionId = Date.now();
  const projectContext = {
    name: 'Claude-Code-Projetos',
    type: 'legal_automation',
    agents: 5,
    skills: 5
  };

  execSync(`vibe-log session start --id ${sessionId} --context '${JSON.stringify(projectContext)}'`, {
    stdio: 'inherit'
  });
}

main();
```

**Registrar em settings.json:**
```json
"SessionStart": [
  {
    "type": "command",
    "command": "node .claude/hooks/vibe-session-start.js"
  }
]
```

### 2. UserPromptSubmit Hook
**Trigger:** Usuário envia prompt
**Responsabilidade:** Analisar e classificar prompt
**Output:** Quality score, category, sentiment, keywords

**Implementação:**
```javascript
// .claude/hooks/vibe-analyze-prompt.js
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function main() {
  // Obter prompt do usuário (via env var CLAUDE_USER_PROMPT)
  const userPrompt = process.env.CLAUDE_USER_PROMPT || '';

  if (!userPrompt) {
    process.exit(0); // Skip se não houver prompt
  }

  // Executar análise via vibe-log
  const result = execSync(`vibe-log analyze --text "${userPrompt.replace(/"/g, '\\"')}"`, {
    encoding: 'utf8'
  });

  // Salvar resultado para statusline consumir
  const outputPath = path.join(process.env.HOME, '.vibe-log/analyzed-prompts/latest.json');
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, result);

  // Log para debug
  console.log('🌊 VibbinLoggin: Prompt analyzed');
}

main();
```

**Registrar em settings.json:**
```json
"UserPromptSubmit": [
  {
    "type": "command",
    "command": "node .claude/hooks/hook-wrapper.js .claude/hooks/vibe-analyze-prompt.js"
  }
]
```

### 3. PreCompact Hook
**Trigger:** Antes de compactar contexto
**Responsabilidade:** Salvar snapshot do contexto antes de perder dados
**Output:** Context metrics (tokens, messages, session duration)

**Implementação:**
```javascript
// .claude/hooks/vibe-pre-compact.js
const { execSync } = require('child_process');

function main() {
  const contextMetrics = {
    timestamp: Date.now(),
    trigger: 'PreCompact',
    estimatedTokens: parseInt(process.env.CLAUDE_TOKEN_USAGE || '0')
  };

  execSync(`vibe-log metric save --type context --data '${JSON.stringify(contextMetrics)}'`, {
    stdio: 'inherit'
  });

  console.log('🌊 VibbinLoggin: Context snapshot saved');
}

main();
```

**Registrar em settings.json:**
```json
"PreCompact": [
  {
    "type": "command",
    "command": "node .claude/hooks/vibe-pre-compact.js"
  }
]
```

### 4. PostCompact Hook (Coaching)
**Trigger:** Após compactar contexto
**Responsabilidade:** Gerar insights e coaching baseado na sessão
**Output:** Sugestões de melhoria, padrões identificados

**Implementação:**
```javascript
// .claude/hooks/vibe-post-compact.js
const { execSync } = require('child_process');

function main() {
  // Gerar coaching insights
  const insights = execSync('vibe-log coach --session-id latest', {
    encoding: 'utf8'
  });

  console.log('\n🌊 VibbinLoggin Coaching:');
  console.log(insights);
}

main();
```

**Registrar em settings.json:**
```json
"PostCompact": [
  {
    "type": "command",
    "command": "node .claude/hooks/vibe-post-compact.js"
  }
]
```

---

## FASE 2: Statusline UI Integration

**Objetivo:** Mostrar métricas VibbinLoggin no statusline

**Implementação:**
```javascript
// .claude/statusline/lib/vibe-integration.js (ATUALIZAR)

function getVibeLoggingMetrics() {
  const latestAnalysis = path.join(process.env.HOME, '.vibe-log/analyzed-prompts/latest.json');

  try {
    if (fs.existsSync(latestAnalysis)) {
      const data = JSON.parse(fs.readFileSync(latestAnalysis, 'utf8'));
      const age = Date.now() - (data.timestamp || 0);

      // Só mostrar se análise foi nos últimos 5 minutos
      if (age < 5 * 60 * 1000) {
        const quality = data.quality || 0; // 0-100
        const category = data.category || 'general';
        const sentiment = data.sentiment || 'neutral';

        // Emoji baseado em quality
        let emoji = '💫'; // default
        if (quality >= 80) emoji = '✨';
        else if (quality >= 60) emoji = '💫';
        else if (quality < 40) emoji = '⚠️';

        // Color baseado em sentiment
        let color = 'cyan';
        if (sentiment === 'positive') color = 'green';
        else if (sentiment === 'negative') color = 'yellow';

        return colorize(`${emoji} Vibe: ${quality}% ${category}`, color);
      }
    }

    return colorize('💫 VibbinLoggin: no data yet', 'gray');
  } catch (error) {
    return colorize('💫 VibbinLoggin: error', 'red');
  }
}
```

**Adicionar em professional-statusline.js:**
```javascript
function line2() {
  // ...
  const vibeStatus = getVibeLoggingMetrics();  // ATUALIZADO - agora mostra métricas reais
  // ...
}
```

---

## FASE 3: Performance Optimization

**Problema:** Statusline atual ~580ms (target <200ms)

### 3.1 Identificar Gargalos
```bash
# Profile statusline execution
time node .claude/statusline/professional-statusline.js
```

**Causas prováveis:**
- Múltiplas chamadas `fs.existsSync()` síncronas
- `execSync('git status')` lento
- Falta de cache
- Leitura de múltiplos arquivos JSON sequencialmente

### 3.2 Implementar Cache Agressivo
```javascript
// lib/cache-manager.js (CRIAR)
class StatuslineCache {
  constructor() {
    this.cache = new Map();
    this.ttl = {
      git: 2000,        // Git status válido por 2s
      venv: 5000,       // Venv detection válido por 5s
      vibe: 1000,       // Vibe metrics válido por 1s
      skills: 10000     // Skills count válido por 10s
    };
  }

  get(key, fetcher, ttl) {
    const cached = this.cache.get(key);
    const now = Date.now();

    if (cached && (now - cached.timestamp) < ttl) {
      return cached.value;
    }

    const value = fetcher();
    this.cache.set(key, { value, timestamp: now });
    return value;
  }
}

module.exports = new StatuslineCache();
```

### 3.3 Paralelizar I/O
```javascript
// Usar Promise.all para operações independentes
const [gitStatus, venvStatus, vibeMetrics, skillsCount] = await Promise.all([
  getGitStatusAsync(),
  getVenvStatusAsync(),
  getVibeMetricsAsync(),
  getSkillsCountAsync()
]);
```

### 3.4 Lazy Loading
```javascript
// Carregar apenas o necessário no primeiro render
// Dados pesados (MCP, Agents) só carregam se mudarem
```

---

## FASE 4: Error Handling & Robustez

**Princípio:** "Hooks são chatos" → Nunca crashar, sempre degradar gracefully

### 4.1 Try-Catch em TODAS as funções
```javascript
function getGitStatus() {
  try {
    // ... implementação
  } catch (error) {
    // NUNCA crashar - retornar fallback
    return colorize('🌿 Git: error', 'red');
  }
}
```

### 4.2 Timeout para comandos lentos
```javascript
function execWithTimeout(command, timeout = 1000) {
  try {
    return execSync(command, {
      timeout: timeout,
      encoding: 'utf8',
      stdio: 'pipe'
    });
  } catch (error) {
    if (error.killed) {
      return null; // Timeout exceeded
    }
    throw error;
  }
}
```

### 4.3 Health Check
```javascript
// .claude/statusline/health-check.js
// Executar periodicamente para validar se statusline está OK
function healthCheck() {
  const startTime = Date.now();
  const result = execSync('node .claude/statusline/professional-statusline.js');
  const elapsed = Date.now() - startTime;

  console.log(`Statusline render time: ${elapsed}ms`);
  console.log(result);

  if (elapsed > 500) {
    console.warn(`⚠️  Statusline too slow: ${elapsed}ms (target <200ms)`);
  }
}
```

---

## FASE 5: Testing & Validation

### 5.1 Unit Tests
```javascript
// .claude/statusline/__tests__/color-palette.test.js
const { colorize } = require('../lib/color-palette');

describe('color-palette', () => {
  it('should colorize text correctly', () => {
    const result = colorize('test', 'cyan');
    expect(result).toContain('\x1b[38;5;51m');
    expect(result).toContain('test');
    expect(result).toContain('\x1b[0m');
  });
});
```

### 5.2 Integration Tests
```javascript
// .claude/statusline/__tests__/professional-statusline.test.js
const { exec } = require('child_process');

describe('professional-statusline', () => {
  it('should render without crashing', (done) => {
    exec('node .claude/statusline/professional-statusline.js', (error, stdout) => {
      expect(error).toBeNull();
      expect(stdout).toBeTruthy();
      done();
    });
  });

  it('should complete in under 200ms', (done) => {
    const start = Date.now();
    exec('node .claude/statusline/professional-statusline.js', () => {
      const elapsed = Date.now() - start;
      expect(elapsed).toBeLessThan(200);
      done();
    });
  });
});
```

### 5.3 Visual Regression Tests
```bash
# Capturar screenshots do statusline em diferentes estados
# Comparar com baseline para detectar regressões visuais

# Estado 1: Legal-Braniac ACTIVE
# Estado 2: VibbinLoggin high quality (80%+)
# Estado 3: Git dirty + hooks running
# Estado 4: Context 90%+
```

---

## FASE 6: Documentation

### 6.1 User-Facing Docs
**README.md atualizado:**
- Explicar cada linha do statusline
- Screenshots de cada estado
- Troubleshooting guide

### 6.2 Developer Docs
**ARCHITECTURE.md:**
- Fluxo de dados
- Cache strategy
- Performance budgets
- Como adicionar novos componentes

---

## Cronograma de Execução

**REGRA:** NÃO pular fases. Cada fase deve ser 100% completa antes de próxima.

| Fase | Descrição | Tempo Estimado | Blocker? |
|------|-----------|----------------|----------|
| 1 | VibbinLoggin Hooks | 2-3h | ✅ YES - sem isso statusline fica incompleto |
| 2 | Statusline UI Integration | 1h | ✅ YES - core feature |
| 3 | Performance Optimization | 2h | ⚠️ MEDIUM - usável mas não ideal |
| 4 | Error Handling | 1h | ✅ YES - hooks crashando são inaceitáveis |
| 5 | Testing | 1-2h | ⚠️ MEDIUM - importante mas não blocker |
| 6 | Documentation | 1h | ❌ NO - nice to have |

**Total:** 8-10 horas de trabalho focado

---

## Acceptance Criteria (Definição de "DONE")

### ✅ VibbinLoggin Metrics Showing
- [ ] `vibe-log` hooks instalados (SessionStart, UserPromptSubmit, PreCompact, PostCompact)
- [ ] Statusline mostra quality % real (não "no data yet")
- [ ] Statusline mostra category (e.g., "planning", "coding", "debugging")
- [ ] Statusline mostra sentiment (positive/neutral/negative com cores)

### ✅ Performance Target Met
- [ ] Statusline render <200ms (medido com `time node professional-statusline.js`)
- [ ] Cache implementado para operações lentas
- [ ] Nenhuma operação bloqueia por >100ms

### ✅ Rock-Solid Reliability
- [ ] Nenhum hook crasha NUNCA (try-catch em TUDO)
- [ ] Graceful degradation se vibe-log não disponível
- [ ] Timeouts configurados para comandos externos
- [ ] Health check passa 100% das vezes

### ✅ Professional Polish
- [ ] Layout consistente em 80-120-200 caracteres de largura
- [ ] Cores respeitam palette vibrant (NO dark colors)
- [ ] Emojis sleek e não poluídos
- [ ] Separadores horizontais bem alinhados

---

## Riscos & Mitigações

### Risco 1: vibe-log CLI não tem comandos esperados
**Mitigação:** Verificar `vibe-log --help` antes de implementar hooks. Se comandos não existirem, contribuir para vibe-log-cli ou usar API alternativa.

### Risco 2: Hooks tornam Claude Code lento
**Mitigação:** Hooks assíncronos + timeout agressivo (1s max). Se exceder, skip.

### Risco 3: Windows/WSL path differences
**Mitigação:** Usar `process.env.HOME` sempre, testar em ambos ambientes.

### Risco 4: Git operations lentas em repos grandes
**Mitigação:** Cache de 2-5s para git status. Não re-executar se já temos valor válido.

---

## Next Actions (Ordem RIGOROSA)

1. **[AGORA]** Verificar comandos disponíveis em `vibe-log --help`
2. **[AGORA]** Implementar vibe-session-start.js
3. **[AGORA]** Implementar vibe-analyze-prompt.js
4. **[DEPOIS]** Implementar vibe-pre-compact.js
5. **[DEPOIS]** Implementar vibe-post-compact.js
6. **[DEPOIS]** Atualizar lib/vibe-integration.js para consumir dados reais
7. **[DEPOIS]** Performance profiling + optimization
8. **[DEPOIS]** Error handling audit
9. **[FINAL]** Testing suite
10. **[FINAL]** Documentation

---

**Última atualização:** 2025-11-15
**Status:** ✅ PLANEJAMENTO COMPLETO - Pronto para execução rigorosa
**Próximo passo:** Verificar `vibe-log --help` e iniciar Fase 1
