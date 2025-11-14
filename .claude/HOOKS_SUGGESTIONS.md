# Sugestões de Novos Hooks Não Bloqueantes

**Última atualização:** 2025-11-13
**Status:** Propostas para revisão

---

## 📋 Índice

1. [Princípios de Design](#princípios-de-design)
2. [Hooks de Alta Prioridade](#hooks-de-alta-prioridade)
3. [Hooks de Média Prioridade](#hooks-de-média-prioridade)
4. [Hooks de Baixa Prioridade](#hooks-de-baixa-prioridade)
5. [Como Testar Antes de Ativar](#como-testar-antes-de-ativar)
6. [Template para Novos Hooks](#template-para-novos-hooks)

---

## 🎯 Princípios de Design

**TODOS os novos hooks DEVEM seguir:**

### ✅ Checklist de Segurança

- [ ] **ASYNC:** Usar `fs.promises`, `async/await`, nunca `*Sync`
- [ ] **TIMEOUT:** `Promise.race()` com timeout 300-500ms
- [ ] **RUN-ONCE GUARD:** Variável de ambiente para prevenir loops
- [ ] **GRACEFUL DEGRADATION:** Mensagem padrão se timeout/erro
- [ ] **NO SUBPROCESS:** NUNCA `execSync()`, `spawnSync()` (risco de freeze)
- [ ] **ERROR HANDLING:** `try/catch` com fallback silencioso
- [ ] **PERFORMANCE:** <100ms idealmente, <500ms máximo

### ❌ Anti-Patterns (BLOQUEIAM)

```javascript
// ❌ NUNCA FAZER:
execSync('python script.py');           // Subprocess síncrono
fs.readFileSync(file);                  // I/O bloqueante
await fetch(url);                       // Sem timeout (pode travar)
throw new Error('...');                 // Quebra sessão (use return)
process.exit(1);                        // Mata Claude Code
```

---

## 🔥 Hooks de Alta Prioridade

### 1. `git-status-watcher.js` - Aviso de Mudanças Não Commitadas

**Propósito:** Avisa se há mudanças não salvas no Git antes de iniciar sessão.

**Valor:** Previne perda de trabalho, alinha com DISASTER_HISTORY.md (commit frequente).

**Implementação:**

```javascript
#!/usr/bin/env node
/**
 * git-status-watcher.js - Avisa sobre mudanças não commitadas
 * ASYNC | TIMEOUT 300ms | RUN-ONCE GUARD
 */

const fs = require('fs').promises;
const path = require('path');

// Run-once guard
if (process.env.CLAUDE_GIT_STATUS_CHECKED === 'true') {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}
process.env.CLAUDE_GIT_STATUS_CHECKED = 'true';

async function checkGitStatus() {
  try {
    const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const gitDir = path.join(cwd, '.git');

    // Verificar se é repositório Git
    try {
      await fs.access(gitDir);
    } catch {
      // Não é repo Git, pular silenciosamente
      return { continue: true };
    }

    // Verificar arquivos modificados (git status --porcelain)
    // IMPORTANTE: Não usar execSync - ler diretamente .git/index
    const gitIndex = path.join(gitDir, 'index');
    const gitIndexStat = await fs.stat(gitIndex);
    const now = Date.now();
    const minutesSinceLastCommit = (now - gitIndexStat.mtimeMs) / 1000 / 60;

    let message = '';

    if (minutesSinceLastCommit > 60) {
      // Último commit há mais de 1 hora
      message = `⚠️ GIT: Último commit há ${Math.floor(minutesSinceLastCommit / 60)}h ${Math.floor(minutesSinceLastCommit % 60)}m\n`;
      message += `💡 Considere commitar mudanças: git add . && git commit -m "..." && git push\n`;
    }

    return {
      continue: true,
      systemMessage: message
    };
  } catch (error) {
    // Graceful degradation
    return { continue: true };
  }
}

async function mainWithTimeout() {
  const timeout = new Promise(resolve =>
    setTimeout(() => resolve({ continue: true }), 300)
  );
  const result = await Promise.race([checkGitStatus(), timeout]);
  console.log(JSON.stringify(result));
}

mainWithTimeout().catch(() => {
  console.log(JSON.stringify({ continue: true }));
});
```

**Teste:**
```bash
node .claude/hooks/git-status-watcher.js
# Deve retornar JSON em <300ms
```

**Riscos:** ✅ Nenhum (apenas lê timestamps de arquivos)

---

### 2. `data-layer-validator.js` - Valida Separação CODE/ENV/DATA

**Propósito:** Valida que CODE, ENV e DATA estão separados corretamente (DISASTER_HISTORY.md).

**Valor:** Previne repetição do desastre de 3 dias (código no E:\).

**Implementação:**

```javascript
#!/usr/bin/env node
/**
 * data-layer-validator.js - Valida separação CODE/ENV/DATA
 * ASYNC | TIMEOUT 400ms | RUN-ONCE GUARD
 */

const fs = require('fs').promises;
const path = require('path');

if (process.env.CLAUDE_DATA_LAYER_VALIDATED === 'true') {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}
process.env.CLAUDE_DATA_LAYER_VALIDATED = 'true';

async function validateLayers() {
  try {
    const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();

    // RULE 1: Código deve estar em C:\claude-work\repos\ ou similar (não E:\)
    const isOnExternalDrive = /^[D-Z]:\\/.test(cwd) && !/^C:\\/.test(cwd);

    if (isOnExternalDrive) {
      return {
        continue: true,
        systemMessage:
          '🚨 VIOLAÇÃO RULE_001: Código detectado em drive externo!\n' +
          `📂 Localização atual: ${cwd}\n` +
          '⚠️ DESASTRE IMINENTE - Ver DISASTER_HISTORY.md\n' +
          '✅ Ação: Mova código para C:\\claude-work\\repos\\ IMEDIATAMENTE\n'
      };
    }

    // RULE 2: .venv deve estar em .gitignore
    const gitignorePath = path.join(cwd, '.gitignore');
    try {
      const gitignoreContent = await fs.readFile(gitignorePath, 'utf8');
      const hasVenvIgnore = gitignoreContent.includes('.venv') || gitignoreContent.includes('venv/');

      if (!hasVenvIgnore) {
        return {
          continue: true,
          systemMessage:
            '⚠️ VIOLAÇÃO RULE_002: .venv não está em .gitignore!\n' +
            '📖 Adicione: .venv/ venv/ __pycache__/\n'
        };
      }
    } catch {
      // .gitignore não existe (OK se não for repo Git)
    }

    // RULE 3: Data dir deve estar fora do repo
    const dataDir = process.env.CLAUDE_DATA_ROOT || 'E:/claude-code-data';
    const isDataInsideRepo = dataDir.startsWith(cwd);

    if (isDataInsideRepo) {
      return {
        continue: true,
        systemMessage:
          '⚠️ VIOLAÇÃO RULE_003: Data dir dentro do repositório!\n' +
          `📂 Data dir: ${dataDir}\n` +
          '✅ Configure: CLAUDE_DATA_ROOT para localização externa\n'
      };
    }

    // ✅ Tudo OK
    return { continue: true };
  } catch (error) {
    return { continue: true }; // Graceful degradation
  }
}

async function mainWithTimeout() {
  const timeout = new Promise(resolve =>
    setTimeout(() => resolve({ continue: true }), 400)
  );
  const result = await Promise.race([validateLayers(), timeout]);
  console.log(JSON.stringify(result));
}

mainWithTimeout().catch(() => {
  console.log(JSON.stringify({ continue: true }));
});
```

**Teste:**
```bash
node .claude/hooks/data-layer-validator.js
# Deve retornar JSON validando separação
```

**Riscos:** ✅ Nenhum (apenas lê caminhos e .gitignore)

---

### 3. `dependency-drift-checker.js` - Detecta Dependências Desatualizadas

**Propósito:** Avisa se `requirements.txt` está desatualizado vs `pip freeze`.

**Valor:** Previne "funciona na minha máquina" por dependências divergentes.

**Implementação:**

```javascript
#!/usr/bin/env node
/**
 * dependency-drift-checker.js - Detecta dependências desatualizadas
 * ASYNC | TIMEOUT 500ms | RUN-ONCE GUARD
 */

const fs = require('fs').promises;
const path = require('path');

if (process.env.CLAUDE_DEPS_CHECKED === 'true') {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}
process.env.CLAUDE_DEPS_CHECKED = 'true';

async function checkDependencies() {
  try {
    const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();

    // Verificar se .venv está ativo
    const venvActive = !!process.env.VIRTUAL_ENV;

    if (!venvActive) {
      // venv-check.js já avisa sobre isso
      return { continue: true };
    }

    // Procurar requirements.txt em agentes/*/
    const agentesDir = path.join(cwd, 'agentes');

    try {
      const agents = await fs.readdir(agentesDir);
      const warnings = [];

      for (const agent of agents) {
        const agentDir = path.join(agentesDir, agent);
        const reqFile = path.join(agentDir, 'requirements.txt');

        try {
          const stat = await fs.stat(reqFile);
          const daysSinceModified = (Date.now() - stat.mtimeMs) / 1000 / 60 / 60 / 24;

          // Avisar se requirements.txt não foi modificado há >30 dias
          if (daysSinceModified > 30) {
            warnings.push(`📦 ${agent}: requirements.txt há ${Math.floor(daysSinceModified)} dias sem atualização`);
          }
        } catch {
          // requirements.txt não existe neste agente (OK)
        }
      }

      if (warnings.length > 0) {
        return {
          continue: true,
          systemMessage:
            '⚠️ DEPENDENCY DRIFT DETECTADO:\n' +
            warnings.join('\n') + '\n' +
            '💡 Atualize com: pip freeze > requirements.txt\n'
        };
      }

      return { continue: true };
    } catch {
      // Diretório agentes/ não existe
      return { continue: true };
    }
  } catch (error) {
    return { continue: true };
  }
}

async function mainWithTimeout() {
  const timeout = new Promise(resolve =>
    setTimeout(() => resolve({ continue: true }), 500)
  );
  const result = await Promise.race([checkDependencies(), timeout]);
  console.log(JSON.stringify(result));
}

mainWithTimeout().catch(() => {
  console.log(JSON.stringify({ continue: true }));
});
```

**Teste:**
```bash
cd agentes/oab-watcher
node ../../.claude/hooks/dependency-drift-checker.js
```

**Riscos:** ✅ Nenhum (apenas lê timestamps)

---

## ⚙️ Hooks de Média Prioridade

### 4. `recent-errors-detector.js` - Analisa Logs de Erros Recentes

**Propósito:** Avisa sobre erros recentes em logs de agentes.

**Valor:** Visibilidade proativa de problemas em execuções anteriores.

**Implementação:**

```javascript
#!/usr/bin/env node
/**
 * recent-errors-detector.js - Analisa logs de erros recentes
 * ASYNC | TIMEOUT 500ms | RUN-ONCE GUARD
 */

const fs = require('fs').promises;
const path = require('path');

if (process.env.CLAUDE_ERRORS_CHECKED === 'true') {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}
process.env.CLAUDE_ERRORS_CHECKED = 'true';

async function checkRecentErrors() {
  try {
    const dataRoot = process.env.CLAUDE_DATA_ROOT || 'E:/claude-code-data';

    // Verificar se data root existe
    try {
      await fs.access(dataRoot);
    } catch {
      // Data root não existe ou inacessível (OK)
      return { continue: true };
    }

    const agentesLogDir = path.join(dataRoot, 'agentes');
    const agents = await fs.readdir(agentesLogDir).catch(() => []);

    const errorSummary = [];
    const last24h = Date.now() - 24 * 60 * 60 * 1000;

    for (const agent of agents) {
      const logsDir = path.join(agentesLogDir, agent, 'logs');

      try {
        const logFiles = await fs.readdir(logsDir);

        for (const logFile of logFiles) {
          const logPath = path.join(logsDir, logFile);
          const stat = await fs.stat(logPath);

          // Apenas logs das últimas 24h
          if (stat.mtimeMs < last24h) continue;

          // Ler primeiras/últimas 100 linhas (não todo arquivo - pode ser grande)
          const content = await fs.readFile(logPath, 'utf8');
          const lines = content.split('\n').slice(-100);

          // Contar erros (heurística: linhas com ERROR, CRITICAL, Exception)
          const errorCount = lines.filter(line =>
            /ERROR|CRITICAL|Exception|Traceback/i.test(line)
          ).length;

          if (errorCount > 0) {
            errorSummary.push(`🔴 ${agent}: ${errorCount} erros em ${logFile}`);
          }
        }
      } catch {
        // Logs dir não existe para este agente
      }
    }

    if (errorSummary.length > 0) {
      return {
        continue: true,
        systemMessage:
          '⚠️ ERROS RECENTES DETECTADOS (últimas 24h):\n' +
          errorSummary.slice(0, 5).join('\n') + '\n' +
          `📂 Logs em: ${agentesLogDir}\n`
      };
    }

    return { continue: true };
  } catch (error) {
    return { continue: true };
  }
}

async function mainWithTimeout() {
  const timeout = new Promise(resolve =>
    setTimeout(() => resolve({ continue: true }), 500)
  );
  const result = await Promise.race([checkRecentErrors(), timeout]);
  console.log(JSON.stringify(result));
}

mainWithTimeout().catch(() => {
  console.log(JSON.stringify({ continue: true }));
});
```

**Teste:**
```bash
# Criar log de teste primeiro
mkdir -p E:/claude-code-data/agentes/oab-watcher/logs
echo "ERROR: Test error" > E:/claude-code-data/agentes/oab-watcher/logs/test.log

node .claude/hooks/recent-errors-detector.js
```

**Riscos:** ⚠️ Baixo (pode ser lento se logs muito grandes - limitar a 100 linhas)

---

### 5. `corporate-environment-guard.js` - Aviso de Ambiente Corporativo

**Propósito:** Detecta ambiente corporativo Windows e avisa sobre limitações.

**Valor:** Previne confusão com EPERM, file locking issues.

**Nota:** Já existe `corporate-detector.js` - apenas precisa ser ativado!

**Ativação:**

```json
// .claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "node .claude/hooks/session-context-hybrid.js" },
          { "type": "command", "command": "node .claude/hooks/invoke-legal-braniac-hybrid.js" },
          { "type": "command", "command": "node .claude/hooks/venv-check.js" },
          { "type": "command", "command": "node .claude/hooks/corporate-detector.js" }  // NOVO
        ]
      }
    ]
  }
}
```

**Teste:**
```bash
node .claude/hooks/corporate-detector.js
# Deve retornar detecção corporativa (se aplicável)
```

**Riscos:** ⚠️ Baixo (usa `wmic` e `gpresult` - pode ser lento em alguns sistemas)

---

## 📊 Hooks de Baixa Prioridade (Nice-to-Have)

### 6. `legal-context-injector.js` - Contexto de Leis Brasileiras

**Propósito:** Injeta referências rápidas a leis brasileiras relevantes.

**Valor:** Acesso rápido a CF, CC, CPC, CLT sem precisar procurar.

**Implementação:**

```javascript
#!/usr/bin/env node
/**
 * legal-context-injector.js - Injeta contexto de leis brasileiras
 * ASYNC | TIMEOUT 300ms | RUN-ONCE GUARD
 */

const LEGAL_CONTEXT = `
📚 REFERÊNCIAS LEGAIS RÁPIDAS:

🇧🇷 **Constituição Federal (CF/88)**
   - Direitos Fundamentais: Art. 5º
   - Processo Legal: Art. 5º, LIV, LV
   - Ampla Defesa: Art. 5º, LV

⚖️ **Código Civil (CC/2002)**
   - Prescrição: Arts. 189-206
   - Contratos: Arts. 421-853

⚖️ **Código de Processo Civil (CPC/2015)**
   - Prazos: Arts. 218-233
   - Recursos: Arts. 994-1.044

👷 **CLT (Consolidação das Leis do Trabalho)**
   - Jornada: Arts. 58-75
   - Férias: Arts. 129-153

🛡️ **CDC (Código de Defesa do Consumidor)**
   - Direitos Básicos: Art. 6º
   - Práticas Abusivas: Arts. 39-41

💡 Use /legal-articles-finder para extrair artigos completos.
`;

if (process.env.CLAUDE_LEGAL_CONTEXT_INJECTED === 'true') {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}
process.env.CLAUDE_LEGAL_CONTEXT_INJECTED = 'true';

console.log(JSON.stringify({
  continue: true,
  systemMessage: LEGAL_CONTEXT
}));
```

**Teste:**
```bash
node .claude/hooks/legal-context-injector.js
```

**Riscos:** ✅ Nenhum (apenas string estática)

---

### 7. `session-metrics.js` - Métricas de Uso (Opcional)

**Propósito:** Coleta métricas anônimas de uso (prompts/dia, agentes usados).

**Valor:** Insights sobre padrões de uso.

**Privacidade:** ⚠️ Requer consentimento explícito do usuário.

**Implementação:** Não incluída (requer discussão sobre privacidade primeiro).

---

## 🧪 Como Testar Antes de Ativar

### Método 1: Teste Manual (Recomendado)

```bash
# 1. Navegue até o projeto
cd C:\claude-work\repos\Claude-Code-Projetos

# 2. Execute o hook manualmente
node .claude/hooks/<novo-hook>.js

# 3. Verifique:
# - Retorna JSON válido?
# - Termina em <500ms?
# - Não trava?
# - Mensagem faz sentido?

# 4. Teste múltiplas execuções (verificar run-once guard)
node .claude/hooks/<novo-hook>.js
node .claude/hooks/<novo-hook>.js
# Segunda execução deve retornar {} imediatamente
```

### Método 2: Teste com settings.local.json (Isolado)

```json
// .claude/settings.local.json (NÃO commitado)
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "node .claude/hooks/<novo-hook>.js" }
        ]
      }
    ]
  }
}
```

Depois:
```bash
claude
# Testar se hook executa sem travar
```

**IMPORTANTE:** Se travar, pressione Ctrl+C e remova de `settings.local.json`!

### Método 3: Validação Automatizada

```bash
# Criar script de validação
cat > .claude/validate-hook.sh <<'EOF'
#!/bin/bash
HOOK=$1
echo "🧪 Testando hook: $HOOK"

# Timeout de 1s (máximo absoluto)
timeout 1s node ".claude/hooks/$HOOK" > /tmp/hook-output.json 2>&1

if [ $? -eq 124 ]; then
  echo "❌ FALHOU: Hook travou (timeout 1s)"
  exit 1
fi

# Validar JSON
cat /tmp/hook-output.json | jq . > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "❌ FALHOU: Output não é JSON válido"
  cat /tmp/hook-output.json
  exit 1
fi

echo "✅ PASSOU: Hook executou em <1s e retornou JSON válido"
cat /tmp/hook-output.json | jq .
EOF

chmod +x .claude/validate-hook.sh

# Usar:
./.claude/validate-hook.sh git-status-watcher.js
```

---

## 📝 Template para Novos Hooks

```javascript
#!/usr/bin/env node
/**
 * <hook-name>.js - <Descrição curta>
 * ASYNC | TIMEOUT <X>ms | RUN-ONCE GUARD
 *
 * Propósito: <Descrição detalhada>
 * Valor: <Por que este hook é útil>
 * Riscos: <Riscos potenciais ou "Nenhum">
 */

const fs = require('fs').promises;
const path = require('path');

// ============================================================================
// RUN-ONCE GUARD
// ============================================================================
const GUARD_VAR = 'CLAUDE_<HOOK_NAME>_EXECUTED';

if (process.env[GUARD_VAR] === 'true') {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}
process.env[GUARD_VAR] = 'true';

// ============================================================================
// LÓGICA PRINCIPAL (ASYNC)
// ============================================================================
async function main() {
  try {
    const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();

    // TODO: Implementar lógica aqui
    // - Usar fs.promises (NUNCA fs.*Sync)
    // - Usar await para operações async
    // - Retornar { continue: true, systemMessage?: string }

    return {
      continue: true,
      systemMessage: '✅ Hook executado com sucesso!'
    };
  } catch (error) {
    // GRACEFUL DEGRADATION: Nunca lançar exceção
    // Apenas retornar silenciosamente
    return { continue: true };
  }
}

// ============================================================================
// TIMEOUT WRAPPER
// ============================================================================
async function mainWithTimeout() {
  const TIMEOUT_MS = 500; // Ajustar conforme necessário (300-500ms recomendado)

  const timeout = new Promise(resolve =>
    setTimeout(() => resolve({ continue: true }), TIMEOUT_MS)
  );

  const result = await Promise.race([main(), timeout]);
  console.log(JSON.stringify(result));
}

// ============================================================================
// EXECUÇÃO
// ============================================================================
mainWithTimeout().catch(() => {
  // Fallback final: Se tudo falhar, retornar JSON vazio
  console.log(JSON.stringify({ continue: true }));
});
```

**Como usar este template:**

1. Copie o template para `.claude/hooks/<novo-hook>.js`
2. Substitua `<hook-name>`, `<HOOK_NAME>`, descrições
3. Implemente lógica em `main()`
4. Teste com `node .claude/hooks/<novo-hook>.js`
5. Adicione a `settings.local.json` para teste integrado
6. Se passar, adicione a `settings.json` e commit

---

## 📊 Resumo de Prioridades

| Hook | Prioridade | Valor | Risco | Esforço |
|------|-----------|-------|-------|---------|
| `git-status-watcher.js` | 🔥 ALTA | Previne perda de trabalho | ✅ Nenhum | 1h |
| `data-layer-validator.js` | 🔥 ALTA | Previne DISASTER_HISTORY | ✅ Nenhum | 2h |
| `dependency-drift-checker.js` | 🔥 ALTA | Previne "funciona na minha máquina" | ✅ Nenhum | 1.5h |
| `recent-errors-detector.js` | ⚙️ MÉDIA | Visibilidade proativa | ⚠️ Baixo (logs grandes) | 2h |
| `corporate-detector.js` (ativar) | ⚙️ MÉDIA | Previne confusão EPERM | ⚠️ Baixo (wmic lento) | 10min |
| `legal-context-injector.js` | 📊 BAIXA | Conveniência | ✅ Nenhum | 30min |
| `session-metrics.js` | 📊 BAIXA | Insights de uso | ⚠️ Privacidade | 3h |

---

## 🚀 Próximos Passos Recomendados

1. **Implementar hooks de Alta Prioridade primeiro:**
   - `git-status-watcher.js`
   - `data-layer-validator.js`
   - `dependency-drift-checker.js`

2. **Testar cada hook individualmente antes de ativar:**
   - Usar `validate-hook.sh` script
   - Testar em `settings.local.json` primeiro

3. **Documentar em CLAUDE.md:**
   - Adicionar seção "Hooks Ativos" listando todos
   - Explicar quando cada hook executa

4. **Considerar ativar `corporate-detector.js`:**
   - Já existe e foi testado
   - Apenas adicionar a `settings.json`

5. **Criar hooks customizados para agentes específicos:**
   - `oab-watcher-status.js` - Status do agente OAB Watcher
   - `djen-tracker-status.js` - Status do DJEN tracker

---

**Última atualização:** 2025-11-13
**Mantido por:** PedroGiudice
**Feedback:** Abra issue ou edite este arquivo diretamente
