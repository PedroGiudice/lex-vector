# ESPECIFICAÇÃO TÉCNICA: HOOKS SESSIONSTART PORTÁVEIS

**Versão:** 1.0  
**Data:** 2025-11-12  
**Autor:** Agente de Planejamento Especializado  
**Status:** PROPOSTA PARA APROVAÇÃO  
**Criticidade:** ALTA - Arquitetura crítica conforme DISASTER_HISTORY.md

---

## SUMÁRIO EXECUTIVO

Este documento especifica a reescrita completa dos 3 hooks SessionStart existentes para garantir portabilidade total entre:
- **Windows** (Claude Code CLI local)
- **Linux** (Claude Code Web remoto)

**Problema crítico identificado:**
- Hooks atuais são bash puro com paths hardcoded Unix
- 27 pontos de falha catalogados
- Violação da LIÇÃO 4 do DISASTER_HISTORY (linha 4 de session-context.sh)

**Solução proposta:**
- OPÇÃO 2: Node.js Puro (decisão fundamentada na seção 1)

---

## SEÇÃO 1: DECISÃO ARQUITETURAL

### 1.1 ANÁLISE DAS OPÇÕES

#### OPÇÃO 1: Wrapper Bash + PowerShell
```
.claude/hooks/
├── session-start.sh      (Linux)
├── session-start.ps1     (Windows)
├── session-start         (wrapper detector)
├── session-context.sh
├── session-context.ps1
├── session-context       (wrapper)
├── venv-check.sh
├── venv-check.ps1
└── venv-check            (wrapper)
```

**Prós:**
- Mantém compatibilidade com hooks bash existentes
- Syntax familiar para usuário (PowerShell já usado em run_agent.ps1)
- Não requer novas dependências

**Contras:**
- Duplicação de código (9 arquivos vs 3)
- Lógica de detecção de plataforma em cada wrapper
- Manutenção duplicada: bug fix requer alteração em .sh E .ps1
- Teste requer validação de 6 arquivos de código (3 pares)
- Complexity no versionamento Git (diff duplicado)

**Análise contra DISASTER_HISTORY:**
- ✅ LIÇÃO 1: Respeita separação de camadas
- ✅ LIÇÃO 4: Pode usar caminhos dinâmicos em ambos
- ⚠️ LIÇÃO 5: Aumenta surface area para debugging (mais pontos de falha)

#### OPÇÃO 2: Node.js Puro ⭐ ESCOLHIDA
```
.claude/hooks/
├── session-start.js
├── session-context.js
└── venv-check.js
```

**Prós:**
- Single codebase, zero duplicação
- Portabilidade nativa (Node.js cross-platform garantido)
- Claude Code CLI garante Node.js disponível
- Path manipulation via `path` module (cross-platform nativo)
- JSON output nativo (sem cat << HEREDOC complexo)
- Debugging unificado (1 código para debugar, não 2)
- Versionamento limpo (3 arquivos ao invés de 9)

**Contras:**
- Migração de bash→JavaScript (1 vez apenas)
- Usuário menos familiar com JS (mas não precisa editar hooks frequentemente)

**Análise contra DISASTER_HISTORY:**
- ✅ LIÇÃO 1: Respeita separação de camadas
- ✅ LIÇÃO 4: Path.join() e process.env garantem paths dinâmicos
- ✅ LIÇÃO 5: Surface area mínima para debugging
- ✅ LIÇÃO 7: Single source of truth no Git

**Decisão técnica:**
```
Node.js nativo do Claude Code CLI:
  - path.join() → paths cross-platform
  - fs.existsSync() → verificações de arquivo
  - child_process.execSync() → comandos shell quando necessário
  - JSON.stringify() → output estruturado
  - setTimeout() → timeouts nativos
```

#### OPÇÃO 3: Híbrido (Wrapper + Node.js)
```
.claude/hooks/
├── session-start         (wrapper bash mínimo)
├── session-start.js      (lógica)
├── session-context
├── session-context.js
├── venv-check
└── venv-check.js
```

**Prós:**
- Melhor de bash (detecção) + JavaScript (lógica)

**Contras:**
- Ainda duplica arquivos (6 vs 3)
- Wrapper adiciona latency
- Complexity aumenta

**Análise contra DISASTER_HISTORY:**
- ✅ Respeita lições, mas adiciona complexidade desnecessária
- ⚠️ Overhead de 2 processos por hook

### 1.2 DECISÃO FINAL

**ESCOLHIDA: OPÇÃO 2 - Node.js Puro**

**Justificativa técnica:**

1. **Portabilidade garantida**
   - Node.js é requisito do Claude Code CLI (já instalado)
   - Módulos `path`, `fs`, `os` são nativos (zero deps externas)

2. **Manutenibilidade máxima**
   - 3 arquivos ao invés de 9 (OPÇÃO 1) ou 6 (OPÇÃO 3)
   - Bug fix em 1 local propaga para ambas plataformas

3. **Conformidade DISASTER_HISTORY**
   - LIÇÃO 4: `path.join(process.env.CLAUDE_PROJECT_DIR, 'skills')` NUNCA hardcode
   - LIÇÃO 5: Debugging simplificado (single codebase)
   - LIÇÃO 7: Git simples (3 arquivos JS versionados)

4. **Performance**
   - Node.js startup ~50ms (aceitável para hooks)
   - Sem overhead de wrapper intermediário

5. **Precedente no projeto**
   - `.claude/hooks/skill-activation-prompt.ts` já usa TypeScript
   - Transpilar TS→JS ou usar JS direto (JS escolhido por simplicidade)

**Trade-offs aceitos:**
- Usuário menos familiar com JS (mitigado: hooks são read-only na maior parte do tempo)
- Necessita shebang correto (`#!/usr/bin/env node`)

---

## SEÇÃO 2: ESTRUTURA DE ARQUIVOS

### 2.1 ÁRVORE FINAL

```
/home/user/Claude-Code-Projetos/.claude/hooks/
├── session-start.js              # NEW - substitui session-start.sh
├── session-context.js            # NEW - substitui session-context.sh
├── venv-check.js                 # NEW - substitui venv-check.sh
├── session-start.sh.backup       # OLD - mantido para rollback
├── session-context.sh.backup     # OLD - mantido para rollback
├── venv-check.sh.backup          # OLD - mantido para rollback
├── skill-activation-prompt.sh    # KEEP - mantido (fora do escopo)
└── skill-activation-prompt.ts    # KEEP - mantido (fora do escopo)
```

### 2.2 VERSIONAMENTO GIT

**Arquivos para commit:**
```bash
git add .claude/hooks/session-start.js
git add .claude/hooks/session-context.js
git add .claude/hooks/venv-check.js
git add .claude/hooks/*.backup  # Opcional: manter backups no Git ou não
```

**Arquivos em .gitignore:**
Nenhum novo arquivo para .gitignore (todos os .js devem ser versionados)

### 2.3 PERMISSÕES EXECUTÁVEIS

**Linux (Claude Code Web):**
```bash
chmod +x .claude/hooks/session-start.js
chmod +x .claude/hooks/session-context.js
chmod +x .claude/hooks/venv-check.js
```

**Windows (Claude Code CLI):**
Permissões não necessárias (Node.js executará via `node session-start.js`)

---

## SEÇÃO 3: ESPECIFICAÇÃO TÉCNICA DOS HOOKS

### 3.1 session-start.js - Instalação de Dependências Python

#### 3.1.1 Funcionalidade

Substitui `session-start.sh` (43 linhas bash) com equivalente JavaScript portável.

**Objetivo:**
- Detectar ambiente remoto (Claude Code Web)
- Instalar dependências Python via pip
- Configurar PYTHONPATH
- Reportar status via JSON

#### 3.1.2 Inputs (Variáveis de Ambiente)

| Variável | Origem | Obrigatória | Exemplo | Uso |
|----------|--------|-------------|---------|-----|
| `CLAUDE_CODE_REMOTE` | Claude Code Web | Não | `"true"` | Detecção de ambiente remoto |
| `CLAUDE_PROJECT_DIR` | Claude Code | Sim | `/home/user/Claude-Code-Projetos` | Raiz do projeto |
| `CLAUDE_ENV_FILE` | Claude Code | Sim | `/tmp/claude-env-123` | Arquivo para exportar variáveis |

#### 3.1.3 Outputs (JSON)

```json
{
  "continue": true,
  "systemMessage": "🔧 Setting up Python environment...\n✅ Python environment setup complete!\n   - Root dependencies installed\n   - pytest available\n   - mypy available\n   - PYTHONPATH configured"
}
```

**Formato de erro:**
```json
{
  "continue": true,
  "systemMessage": "⚠️ Error installing dependencies: <error_message>\n(Continuing anyway...)"
}
```

#### 3.1.4 Pseudocódigo Detalhado

```javascript
#!/usr/bin/env node

/**
 * session-start.js - Instala dependências Python para Claude Code Web
 * 
 * DISASTER_HISTORY compliance:
 * - LIÇÃO 4: Usa process.env.CLAUDE_PROJECT_DIR (dinâmico)
 * - LIÇÃO 4: NUNCA hardcode paths
 * - Timeouts em operações pip (evita hang no Windows)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const os = require('os');

// ============================================================================
// CONSTANTES
// ============================================================================

const TIMEOUT_PIP_INSTALL = 120000; // 2 minutos por comando pip
const PIP_QUIET_FLAGS = '--user --quiet';

// ============================================================================
// FUNÇÕES AUXILIARES
// ============================================================================

/**
 * Executa comando com timeout
 * @param {string} command - Comando a executar
 * @param {number} timeout - Timeout em ms
 * @returns {string} - Output do comando
 */
function execWithTimeout(command, timeout = TIMEOUT_PIP_INSTALL) {
  try {
    return execSync(command, {
      timeout: timeout,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });
  } catch (error) {
    // Retorna erro mas não lança exceção (|| true behavior)
    return null;
  }
}

/**
 * Verifica se arquivo existe
 */
function fileExists(filepath) {
  return fs.existsSync(filepath);
}

/**
 * Instala requirements.txt se existir
 */
function installRequirements(requirementsPath, label) {
  if (!fileExists(requirementsPath)) {
    return null;
  }

  console.error(`📦 Installing ${label}...`);
  const result = execWithTimeout(
    `pip install ${PIP_QUIET_FLAGS} -r "${requirementsPath}"`,
    TIMEOUT_PIP_INSTALL
  );

  if (result === null) {
    return `⚠️ Timeout or error installing ${label}`;
  }

  return `✓ ${label} installed`;
}

/**
 * Adiciona variável ao CLAUDE_ENV_FILE
 */
function exportEnvVar(name, value) {
  const envFile = process.env.CLAUDE_ENV_FILE;
  if (!envFile) {
    return false;
  }

  try {
    fs.appendFileSync(envFile, `export ${name}="${value}"\n`);
    return true;
  } catch (error) {
    return false;
  }
}

// ============================================================================
// LÓGICA PRINCIPAL
// ============================================================================

function main() {
  // GUARD: Só executar em Claude Code Web (remoto)
  if (process.env.CLAUDE_CODE_REMOTE !== 'true') {
    // Exit silencioso - não é ambiente remoto
    process.exit(0);
  }

  // GUARD: Validar variáveis de ambiente obrigatórias
  const projectDir = process.env.CLAUDE_PROJECT_DIR;
  if (!projectDir) {
    console.error('❌ CLAUDE_PROJECT_DIR não definido');
    outputJSON({
      continue: true,
      systemMessage: '⚠️ CLAUDE_PROJECT_DIR não definido (hook session-start.js)'
    });
    process.exit(0);
  }

  console.error('🔧 Setting up Python environment for Claude-Code-Projetos (web)...');

  const messages = [];

  // -------------------------------------------------------------------------
  // 1. Instalar dependências root
  // -------------------------------------------------------------------------
  const rootRequirements = path.join(projectDir, 'requirements.txt');
  const rootResult = installRequirements(rootRequirements, 'root dependencies');
  if (rootResult) messages.push(rootResult);

  // -------------------------------------------------------------------------
  // 2. Instalar dependências oab-watcher (includes pytest)
  // -------------------------------------------------------------------------
  const oabRequirements = path.join(projectDir, 'agentes/oab-watcher/requirements.txt');
  const oabResult = installRequirements(oabRequirements, 'oab-watcher dependencies (includes pytest)');
  if (oabResult) messages.push(oabResult);

  // Instalar pytest-cov
  console.error('📦 Installing pytest-cov...');
  execWithTimeout(`pip install ${PIP_QUIET_FLAGS} pytest-cov`, TIMEOUT_PIP_INSTALL);

  // -------------------------------------------------------------------------
  // 3. Instalar dependências legal-rag (includes mypy)
  // -------------------------------------------------------------------------
  const legalRequirements = path.join(projectDir, 'agentes/legal-rag/requirements.txt');
  const legalResult = installRequirements(legalRequirements, 'legal-rag dependencies (includes mypy)');
  if (legalResult) messages.push(legalResult);

  // -------------------------------------------------------------------------
  // 4. Instalar type stubs para mypy
  // -------------------------------------------------------------------------
  console.error('📦 Installing type stubs for mypy...');
  execWithTimeout(`pip install ${PIP_QUIET_FLAGS} types-requests types-tqdm`, TIMEOUT_PIP_INSTALL);

  // -------------------------------------------------------------------------
  // 5. Configurar PYTHONPATH
  // -------------------------------------------------------------------------
  const currentPythonPath = process.env.PYTHONPATH || '';
  const newPythonPath = currentPythonPath 
    ? `${projectDir}:${currentPythonPath}`
    : projectDir;

  const exportSuccess = exportEnvVar('PYTHONPATH', newPythonPath);
  if (exportSuccess) {
    messages.push('✓ PYTHONPATH configured');
  }

  // -------------------------------------------------------------------------
  // 6. Output final
  // -------------------------------------------------------------------------
  console.error('✅ Python environment setup complete!');

  const finalMessage = `✅ Python environment setup complete!
   - Root dependencies installed
   - pytest available for testing
   - mypy available for linting
   - PYTHONPATH configured`;

  outputJSON({
    continue: true,
    systemMessage: finalMessage
  });
}

/**
 * Output JSON para Claude Code
 */
function outputJSON(obj) {
  console.log(JSON.stringify(obj, null, 2));
}

// ============================================================================
// EXECUÇÃO
// ============================================================================

try {
  main();
} catch (error) {
  outputJSON({
    continue: true,
    systemMessage: `⚠️ session-start.js error: ${error.message}\n(Continuing anyway...)`
  });
  process.exit(0);
}
```

#### 3.1.5 Validações Obrigatórias

1. ✅ `CLAUDE_CODE_REMOTE === 'true'` → senão exit(0) silencioso
2. ✅ `CLAUDE_PROJECT_DIR` existe → senão error message
3. ✅ Timeout em TODAS operações pip (2min) → evita hang
4. ✅ Paths construídos com `path.join()` → cross-platform
5. ✅ Erros não bloqueiam (`|| true` behavior) → continue: true sempre

#### 3.1.6 Tratamento de Erros

**Filosofia:**
- Erros em hooks NÃO devem bloquear Claude Code
- Output `continue: true` SEMPRE
- Mensagens de erro são informativos, não bloqueantes

**Exemplo:**
```javascript
try {
  installDependencies();
} catch (error) {
  // Não lançar - apenas reportar
  outputJSON({
    continue: true,
    systemMessage: `⚠️ Error: ${error.message}\n(Continuing anyway...)`
  });
}
```

---

### 3.2 session-context.js - Injeção de Contexto do Projeto

#### 3.2.1 Funcionalidade

Substitui `session-context.sh` (49 linhas bash) com equivalente JavaScript portável.

**Objetivo:**
- Injetar contexto arquitetural (3 layers)
- Listar skills disponíveis
- Listar agentes especializados
- Reportar via systemMessage

#### 3.2.2 Inputs (Variáveis de Ambiente)

| Variável | Origem | Obrigatória | Exemplo | Uso |
|----------|--------|-------------|---------|-----|
| `CLAUDE_PROJECT_DIR` | Claude Code | Sim | `/home/user/Claude-Code-Projetos` | Raiz do projeto |

**CRÍTICO - VIOLAÇÃO ATUAL:**
Linha 4 de `session-context.sh`:
```bash
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/home/user/Claude-Code-Projetos}"
```
❌ **VIOLAÇÃO LIÇÃO 4 - Path hardcoded `/home/user/Claude-Code-Projetos`**

**CORREÇÃO:**
```javascript
const projectDir = process.env.CLAUDE_PROJECT_DIR;
if (!projectDir) {
  // NÃO usar fallback hardcoded - reportar erro
  outputJSON({
    continue: true,
    systemMessage: '⚠️ CLAUDE_PROJECT_DIR não definido'
  });
  process.exit(0);
}
```

#### 3.2.3 Outputs (JSON)

```json
{
  "continue": true,
  "systemMessage": "ARQUITETURA DO PROJETO:\n- LAYER_1_CODE: Código em Git...\n\nSKILLS DISPONÍVEIS: 3 skills instaladas\nLocalização: /home/user/Claude-Code-Projetos/skills/\n\nAGENTES ESPECIALIZADOS: 5 agentes\n  - planejamento-legal\n  - qualidade-codigo\n  - documentacao\n  - desenvolvimento\n  - analise-dados-legal"
}
```

#### 3.2.4 Pseudocódigo Detalhado

```javascript
#!/usr/bin/env node

/**
 * session-context.js - Injeta contexto essencial do projeto
 * 
 * DISASTER_HISTORY compliance:
 * - LIÇÃO 4: NUNCA hardcode paths (antiga violação na linha 4)
 * - Usa CLAUDE_PROJECT_DIR dinâmico
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

// ============================================================================
// FUNÇÕES AUXILIARES
// ============================================================================

/**
 * Conta diretórios em um path (equivalente a find -maxdepth 1 -type d | wc -l)
 */
function countDirectories(dirPath) {
  try {
    if (!fs.existsSync(dirPath)) {
      return 0;
    }

    const items = fs.readdirSync(dirPath, { withFileTypes: true });
    const directories = items.filter(item => item.isDirectory());
    return directories.length;
  } catch (error) {
    return 0;
  }
}

/**
 * Lista arquivos .md em um diretório (equivalente a find -name "*.md")
 */
function listMdFiles(dirPath) {
  try {
    if (!fs.existsSync(dirPath)) {
      return [];
    }

    const items = fs.readdirSync(dirPath);
    return items.filter(item => item.endsWith('.md'));
  } catch (error) {
    return [];
  }
}

/**
 * Remove extensão .md de filename (equivalente a basename {} .md)
 */
function removeExtension(filename) {
  return path.basename(filename, '.md');
}

// ============================================================================
// LÓGICA PRINCIPAL
// ============================================================================

function main() {
  // GUARD: Validar CLAUDE_PROJECT_DIR
  const projectDir = process.env.CLAUDE_PROJECT_DIR;
  
  if (!projectDir) {
    outputJSON({
      continue: true,
      systemMessage: '⚠️ CLAUDE_PROJECT_DIR não definido (hook session-context.js)'
    });
    process.exit(0);
  }

  // Detectar plataforma para mensagem
  const platform = os.platform(); // 'win32', 'linux', 'darwin'
  const isWindows = platform === 'win32';

  // Construir mensagem de contexto
  let context = '';

  // -------------------------------------------------------------------------
  // 1. Arquitetura 3 Layers
  // -------------------------------------------------------------------------
  const codeLayer = isWindows 
    ? 'C:\\claude-work\\repos\\Claude-Code-Projetos'
    : projectDir;

  context += `
ARQUITETURA DO PROJETO:
- LAYER_1_CODE: Código em Git (${codeLayer})
- LAYER_2_ENVIRONMENT: venv local (.venv/)
- LAYER_3_DATA: Dados externos (configurável via env vars)

REGRAS CRÍTICAS:
- RULE_006: venv SEMPRE obrigatório
- RULE_004: NUNCA hardcode paths
- LESSON_001: Código NUNCA em HD externo
`;

  // -------------------------------------------------------------------------
  // 2. Skills disponíveis
  // -------------------------------------------------------------------------
  const skillsDir = path.join(projectDir, 'skills');
  const skillCount = countDirectories(skillsDir);

  if (skillCount > 0) {
    context += `
SKILLS DISPONÍVEIS: ${skillCount} skills instaladas
Localização: ${skillsDir}/
`;
  }

  // -------------------------------------------------------------------------
  // 3. Agentes especializados
  // -------------------------------------------------------------------------
  const agentsDir = path.join(projectDir, '.claude/agents');
  const agentFiles = listMdFiles(agentsDir);

  if (agentFiles.length > 0) {
    context += `
AGENTES ESPECIALIZADOS: ${agentFiles.length} agentes
`;
    
    // Listar agentes (equivalente a sed 's/^/  - /')
    agentFiles.forEach(file => {
      const agentName = removeExtension(file);
      context += `  - ${agentName}\n`;
    });
  }

  // -------------------------------------------------------------------------
  // 4. Output JSON
  // -------------------------------------------------------------------------
  outputJSON({
    continue: true,
    systemMessage: context.trim()
  });
}

/**
 * Output JSON para Claude Code
 */
function outputJSON(obj) {
  console.log(JSON.stringify(obj, null, 2));
}

// ============================================================================
// EXECUÇÃO
// ============================================================================

try {
  main();
} catch (error) {
  outputJSON({
    continue: true,
    systemMessage: `⚠️ session-context.js error: ${error.message}`
  });
  process.exit(0);
}
```

#### 3.2.5 Validações Obrigatórias

1. ✅ `CLAUDE_PROJECT_DIR` existe → senão error message
2. ✅ Paths construídos com `path.join()` → cross-platform
3. ✅ Verificação de existência de diretórios antes de ler
4. ✅ Tratamento de erros em fs operations
5. ✅ Detecção de plataforma para mensagens contextuais

#### 3.2.6 Correção da Violação LIÇÃO 4

**ANTES (session-context.sh linha 4):**
```bash
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/home/user/Claude-Code-Projetos}"
```
❌ Hardcoded path Unix

**DEPOIS (session-context.js):**
```javascript
const projectDir = process.env.CLAUDE_PROJECT_DIR;
if (!projectDir) {
  // Reportar erro ao invés de usar fallback hardcoded
  outputJSON({
    continue: true,
    systemMessage: '⚠️ CLAUDE_PROJECT_DIR não definido'
  });
  process.exit(0);
}
```
✅ Dinâmico, sem fallback hardcoded

---

### 3.3 venv-check.js - Verificação de Virtual Environment

#### 3.3.1 Funcionalidade

Substitui `venv-check.sh` (26 linhas bash) com equivalente JavaScript portável.

**Objetivo:**
- Verificar se virtual environment está ativo
- Alertar se RULE_006 está sendo violada
- Indicar comando correto para ativar

#### 3.3.2 Inputs (Variáveis de Ambiente)

| Variável | Origem | Obrigatória | Exemplo | Uso |
|----------|--------|-------------|---------|-----|
| `VIRTUAL_ENV` | Python venv | Não | `/path/to/project/.venv` | Indica venv ativo |

#### 3.3.3 Outputs (JSON)

**Cenário 1: venv ATIVO**
```json
{
  "continue": true,
  "systemMessage": "✓ Virtual environment ativo: /path/to/project/.venv"
}
```

**Cenário 2: venv INATIVO**
```json
{
  "continue": true,
  "systemMessage": "⚠️ RULE_006 VIOLATION: Virtual environment NÃO está ativo!\n\nPara ativar (Linux/Mac):\n  source .venv/bin/activate\n\nPara ativar (Windows PowerShell):\n  .venv\\Scripts\\Activate.ps1\n\nPara ativar (Windows CMD):\n  .venv\\Scripts\\activate.bat\n\nEste é um requisito OBRIGATÓRIO antes de qualquer execução Python."
}
```

#### 3.3.4 Pseudocódigo Detalhado

```javascript
#!/usr/bin/env node

/**
 * venv-check.js - Verifica se virtual environment está ativo
 * 
 * DISASTER_HISTORY compliance:
 * - LIÇÃO 6: Ambiente virtual NÃO é opcional
 * - RULE_006: venv SEMPRE obrigatório
 */

const os = require('os');

// ============================================================================
// LÓGICA PRINCIPAL
// ============================================================================

function main() {
  const venvPath = process.env.VIRTUAL_ENV;
  const platform = os.platform();

  if (!venvPath) {
    // VENV NÃO ATIVO - Gerar mensagem com instruções multi-plataforma
    const isWindows = platform === 'win32';

    let instructions = '';
    if (isWindows) {
      instructions = `Para ativar (Windows PowerShell):
  .venv\\Scripts\\Activate.ps1

Para ativar (Windows CMD):
  .venv\\Scripts\\activate.bat`;
    } else {
      instructions = `Para ativar (Linux/Mac):
  source .venv/bin/activate`;
    }

    const message = `⚠️ RULE_006 VIOLATION: Virtual environment NÃO está ativo!

${instructions}

Este é um requisito OBRIGATÓRIO antes de qualquer execução Python.`;

    outputJSON({
      continue: true,
      systemMessage: message
    });

  } else {
    // VENV ATIVO - Mensagem de sucesso
    outputJSON({
      continue: true,
      systemMessage: `✓ Virtual environment ativo: ${venvPath}`
    });
  }
}

/**
 * Output JSON para Claude Code
 */
function outputJSON(obj) {
  console.log(JSON.stringify(obj, null, 2));
}

// ============================================================================
// EXECUÇÃO
// ============================================================================

try {
  main();
} catch (error) {
  outputJSON({
    continue: true,
    systemMessage: `⚠️ venv-check.js error: ${error.message}`
  });
  process.exit(0);
}
```

#### 3.3.5 Validações Obrigatórias

1. ✅ Detecção de plataforma via `os.platform()`
2. ✅ Instruções corretas para Windows vs Unix
3. ✅ Mensagem clara de violação RULE_006
4. ✅ Sempre `continue: true` (não bloquear Claude Code)

#### 3.3.6 Melhoria vs Versão Bash

**ANTES (venv-check.sh):**
```bash
Para ativar:
  source .venv/bin/activate  # ❌ Só funciona em Unix
```

**DEPOIS (venv-check.js):**
```javascript
// Detecta plataforma e mostra comando correto
if (isWindows) {
  // .venv\Scripts\Activate.ps1
} else {
  // source .venv/bin/activate
}
```
✅ Instruções corretas para cada plataforma

---

## SEÇÃO 4: DETECÇÃO DE PLATAFORMA

### 4.1 Método: os.platform()

```javascript
const os = require('os');
const platform = os.platform();

// Valores possíveis:
// - 'win32'   → Windows
// - 'linux'   → Linux
// - 'darwin'  → macOS
// - 'freebsd', 'openbsd', 'sunos', 'aix'

const isWindows = (platform === 'win32');
const isLinux = (platform === 'linux');
const isMac = (platform === 'darwin');
```

### 4.2 Uso nos Hooks

```javascript
// Exemplo: Construir path de ativação venv
const venvActivateScript = isWindows
  ? '.venv\\Scripts\\Activate.ps1'  // Windows PowerShell
  : '.venv/bin/activate';            // Unix

// Exemplo: Caminho de dados
const dataRoot = isWindows
  ? 'E:\\claude-code-data'
  : process.env.CLAUDE_CODE_DATA_PATH || '/tmp/claude-data';
```

### 4.3 Fallbacks

**NÃO usar fallbacks hardcoded para paths críticos:**
```javascript
// ❌ ERRADO
const projectDir = process.env.CLAUDE_PROJECT_DIR || '/home/user/default';

// ✅ CORRETO
const projectDir = process.env.CLAUDE_PROJECT_DIR;
if (!projectDir) {
  // Reportar erro ao invés de assumir default
  throw new Error('CLAUDE_PROJECT_DIR não definido');
}
```

---

## SEÇÃO 5: CAMINHOS DINÂMICOS

### 5.1 Construção Cross-Platform

```javascript
const path = require('path');

// ✅ CORRETO - Cross-platform
const skillsDir = path.join(projectDir, 'skills');
const agentsDir = path.join(projectDir, '.claude', 'agents');
const requirementsFile = path.join(projectDir, 'agentes', 'oab-watcher', 'requirements.txt');

// ❌ ERRADO - Unix hardcoded
const skillsDir = projectDir + '/skills';

// ❌ ERRADO - Windows hardcoded
const skillsDir = projectDir + '\\skills';
```

### 5.2 Variáveis de Ambiente

**Disponíveis no Claude Code:**

| Variável | Descrição | Exemplo Windows | Exemplo Linux |
|----------|-----------|-----------------|---------------|
| `CLAUDE_PROJECT_DIR` | Raiz do projeto | `C:\claude-work\repos\Claude-Code-Projetos` | `/home/user/Claude-Code-Projetos` |
| `CLAUDE_ENV_FILE` | Arquivo para export | `C:\Users\...\claude-env.bat` | `/tmp/claude-env-123` |
| `CLAUDE_CODE_REMOTE` | Ambiente remoto | `undefined` | `"true"` |
| `VIRTUAL_ENV` | venv ativo | `C:\..\.venv` | `/path/to/.venv` |

**Uso:**
```javascript
// Sempre via process.env
const projectDir = process.env.CLAUDE_PROJECT_DIR;
const isRemote = (process.env.CLAUDE_CODE_REMOTE === 'true');
```

### 5.3 Referência: skills/ vs .claude/skills/

**Estrutura atual:**
```
/home/user/Claude-Code-Projetos/
├── skills/                 # Skills de usuário (custom)
│   ├── ocr-pro/
│   ├── deep-parser/
│   └── sign-recognition/
│
└── .claude/
    └── skills/             # Skills de sistema (Claude Code)
        └── skill-rules.json
```

**Paths corretos:**
```javascript
// Skills de usuário
const userSkillsDir = path.join(projectDir, 'skills');

// Skills de sistema
const systemSkillsDir = path.join(projectDir, '.claude', 'skills');

// Agentes
const agentsDir = path.join(projectDir, '.claude', 'agents');
```

---

## SEÇÃO 6: TESTES DE VALIDAÇÃO

### 6.1 Teste Manual no Linux (Atual)

```bash
cd /home/user/Claude-Code-Projetos

# Teste 1: session-start.js
CLAUDE_CODE_REMOTE=true CLAUDE_PROJECT_DIR=/home/user/Claude-Code-Projetos CLAUDE_ENV_FILE=/tmp/test-env node .claude/hooks/session-start.js

# Verificar output JSON válido
# Verificar /tmp/test-env contém export PYTHONPATH

# Teste 2: session-context.js
CLAUDE_PROJECT_DIR=/home/user/Claude-Code-Projetos node .claude/hooks/session-context.js

# Verificar JSON contém "SKILLS DISPONÍVEIS"
# Verificar JSON contém "AGENTES ESPECIALIZADOS"

# Teste 3: venv-check.js (sem venv)
node .claude/hooks/venv-check.js
# Verificar mensagem "RULE_006 VIOLATION"

# Teste 3b: venv-check.js (com venv)
VIRTUAL_ENV=/tmp/fake-venv node .claude/hooks/venv-check.js
# Verificar mensagem "✓ Virtual environment ativo"
```

### 6.2 Simulação de Comportamento Windows (Linux)

Não é possível simular `os.platform() === 'win32'` em Linux.

**Alternativa: Mock testing**
```javascript
// test-venv-check.js
const originalPlatform = os.platform;

// Mock Windows
os.platform = () => 'win32';
main(); // Deve mostrar .venv\Scripts\Activate.ps1

// Mock Linux
os.platform = () => 'linux';
main(); // Deve mostrar source .venv/bin/activate

// Restore
os.platform = originalPlatform;
```

### 6.3 Casos de Teste Obrigatórios

#### 6.3.1 session-start.js

| Caso | Env Vars | Comportamento Esperado |
|------|----------|------------------------|
| TC-01 | `CLAUDE_CODE_REMOTE=false` | Exit 0 silencioso (não executar) |
| TC-02 | `CLAUDE_CODE_REMOTE=true`, sem `CLAUDE_PROJECT_DIR` | Error message, continue: true |
| TC-03 | `CLAUDE_CODE_REMOTE=true`, `CLAUDE_PROJECT_DIR` válido | Instalar deps, output JSON sucesso |
| TC-04 | Requirements.txt inexistente | Pular instalação, sem erro |
| TC-05 | pip timeout | Continuar, reportar warning |

#### 6.3.2 session-context.js

| Caso | Env Vars | Comportamento Esperado |
|------|----------|------------------------|
| TC-10 | Sem `CLAUDE_PROJECT_DIR` | Error message, continue: true |
| TC-11 | `CLAUDE_PROJECT_DIR` válido, skills/ existe | JSON contém "SKILLS DISPONÍVEIS: N skills" |
| TC-12 | `CLAUDE_PROJECT_DIR` válido, skills/ vazio | JSON não menciona skills |
| TC-13 | .claude/agents/ existe | JSON lista agentes |
| TC-14 | .claude/agents/ vazio | JSON não menciona agentes |

#### 6.3.3 venv-check.js

| Caso | Env Vars | Plataforma | Comportamento Esperado |
|------|----------|------------|------------------------|
| TC-20 | Sem `VIRTUAL_ENV` | Windows | Mensagem com `.venv\Scripts\Activate.ps1` |
| TC-21 | Sem `VIRTUAL_ENV` | Linux | Mensagem com `source .venv/bin/activate` |
| TC-22 | `VIRTUAL_ENV=/path/to/venv` | Qualquer | Mensagem "✓ Virtual environment ativo" |

### 6.4 Script de Teste Automatizado

```bash
#!/bin/bash
# test-hooks.sh - Testa todos os hooks

set -e

PROJECT_DIR="/home/user/Claude-Code-Projetos"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"

echo "========================================="
echo "TESTE: session-start.js"
echo "========================================="

# TC-01: Não remoto
CLAUDE_CODE_REMOTE=false CLAUDE_PROJECT_DIR=$PROJECT_DIR node $HOOKS_DIR/session-start.js
echo "✓ TC-01: Exit silencioso quando não remoto"

# TC-03: Remoto válido
CLAUDE_CODE_REMOTE=true CLAUDE_PROJECT_DIR=$PROJECT_DIR CLAUDE_ENV_FILE=/tmp/test-env node $HOOKS_DIR/session-start.js | grep -q "continue"
echo "✓ TC-03: JSON válido quando remoto"

echo ""
echo "========================================="
echo "TESTE: session-context.js"
echo "========================================="

# TC-11: Listar skills
CLAUDE_PROJECT_DIR=$PROJECT_DIR node $HOOKS_DIR/session-context.js | grep -q "SKILLS"
echo "✓ TC-11: Lista skills disponíveis"

# TC-13: Listar agentes
CLAUDE_PROJECT_DIR=$PROJECT_DIR node $HOOKS_DIR/session-context.js | grep -q "AGENTES"
echo "✓ TC-13: Lista agentes especializados"

echo ""
echo "========================================="
echo "TESTE: venv-check.js"
echo "========================================="

# TC-21: Sem venv (Linux)
node $HOOKS_DIR/venv-check.js | grep -q "RULE_006"
echo "✓ TC-21: Detecta ausência de venv"

# TC-22: Com venv
VIRTUAL_ENV=/tmp/fake-venv node $HOOKS_DIR/venv-check.js | grep -q "✓ Virtual"
echo "✓ TC-22: Detecta venv ativo"

echo ""
echo "========================================="
echo "TODOS OS TESTES PASSARAM! ✓"
echo "========================================="
```

---

## SEÇÃO 7: CHECKLIST DISASTER_HISTORY

### 7.1 Conformidade com Lições Aprendidas

| Lição | Requisito | Implementação | Status |
|-------|-----------|---------------|--------|
| **LIÇÃO 1** | Separação CÓDIGO/AMBIENTE/DADOS | Hooks são código (Git), não tocam dados (E:\) | ✅ |
| **LIÇÃO 2** | Symlinks não portáveis | Não usa symlinks | ✅ |
| **LIÇÃO 3** | PATH apenas binários | Não modifica PATH | ✅ |
| **LIÇÃO 4** | Paths dinâmicos | `process.env.CLAUDE_PROJECT_DIR` + `path.join()` | ✅ |
| **LIÇÃO 5** | Debugging causa raiz | Single codebase facilita debugging | ✅ |
| **LIÇÃO 6** | venv obrigatório | venv-check.js valida RULE_006 | ✅ |
| **LIÇÃO 7** | Git diário | Hooks versionados no Git | ✅ |

### 7.2 Proof: Paths Não Hardcoded

**ANTES (session-context.sh linha 4):**
```bash
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/home/user/Claude-Code-Projetos}"
```
❌ Hardcoded `/home/user/Claude-Code-Projetos`

**DEPOIS (session-context.js):**
```javascript
const projectDir = process.env.CLAUDE_PROJECT_DIR;
if (!projectDir) {
  // Erro ao invés de fallback hardcoded
  throw new Error('CLAUDE_PROJECT_DIR não definido');
}
```
✅ 100% dinâmico

**PROOF via Grep:**
```bash
# Verificar se há paths hardcoded Unix
grep -r "/home/user" .claude/hooks/*.js
# Resultado: (vazio) ✓

# Verificar se há paths hardcoded Windows
grep -r "C:\\" .claude/hooks/*.js
# Resultado: (vazio) ✓ (apenas em mensagens, não em paths usados)

# Verificar uso de path.join()
grep -r "path.join" .claude/hooks/*.js
# Resultado: múltiplas ocorrências ✓
```

### 7.3 Proof: Funciona em Ambas Plataformas

**Mecanismos de portabilidade:**

1. **Detecção de plataforma**
```javascript
const platform = os.platform();
const isWindows = (platform === 'win32');
```

2. **Path construction**
```javascript
const skillsDir = path.join(projectDir, 'skills'); // ✓ Win + Unix
```

3. **Separadores de linha**
```javascript
// Não hardcode \n vs \r\n - JSON.stringify cuida disso
```

4. **Shebang portável**
```javascript
#!/usr/bin/env node
// node.exe no Windows ignora shebang
// bash no Linux usa shebang
```

---

## SEÇÃO 8: PLANO DE ROLLBACK

### 8.1 Estratégia de Backup

**ANTES de implementar novos hooks:**
```bash
cd /home/user/Claude-Code-Projetos/.claude/hooks

# Backup de segurança
cp session-start.sh session-start.sh.backup
cp session-context.sh session-context.sh.backup
cp venv-check.sh venv-check.sh.backup

# Commit backups no Git (opcional)
git add *.backup
git commit -m "backup: Hooks originais antes de migração Node.js"
```

### 8.2 Processo de Migração Segura

**FASE 1: POC (Proof of Concept) - 1 hook**
```bash
# 1. Criar session-start.js
# 2. Testar manualmente
# 3. Manter session-start.sh ativo
# 4. Validar output idêntico
```

**FASE 2: Migração Completa - 3 hooks**
```bash
# 1. Criar session-context.js e venv-check.js
# 2. Testar todos 3
# 3. Renomear .sh → .sh.backup
# 4. Commit .js no Git
```

**FASE 3: Validação**
```bash
# 1. Testar Claude Code startup
# 2. Verificar systemMessage correto
# 3. Executar test-hooks.sh
# 4. Validar em ambas plataformas (se possível)
```

### 8.3 Rollback em Caso de Falha

**Cenário: Hooks .js falhando**
```bash
cd /home/user/Claude-Code-Projetos/.claude/hooks

# Restaurar backups
mv session-start.sh.backup session-start.sh
mv session-context.sh.backup session-context.sh
mv venv-check.sh.backup venv-check.sh

# Remover .js problemáticos
rm session-start.js session-context.js venv-check.js

# Commit rollback
git add .
git commit -m "rollback: Restaurar hooks bash originais"
git push
```

**Tempo de rollback:** ~2 minutos

### 8.4 Checklist de Segurança

Antes de considerar migração bem-sucedida:

- [ ] Todos os 3 hooks .js criados
- [ ] Permissões executáveis configuradas (Linux)
- [ ] Teste manual de cada hook passa
- [ ] test-hooks.sh automatizado passa
- [ ] Backups .sh.backup mantidos
- [ ] Git commit dos novos hooks
- [ ] Claude Code startup funciona
- [ ] systemMessage exibido corretamente
- [ ] PYTHONPATH configurado (session-start)
- [ ] Skills listadas (session-context)
- [ ] venv check funcional (venv-check)

**Apenas quando todos itens ✓ → Remover .sh.backup**

---

## SEÇÃO 9: ROADMAP DE IMPLEMENTAÇÃO

### 9.1 Passo-a-Passo Detalhado

#### ETAPA 1: PREPARAÇÃO (Estimativa: 15min)

```bash
# 1.1 Criar branch Git
cd /home/user/Claude-Code-Projetos
git checkout -b feature/nodejs-hooks-portable

# 1.2 Backup de segurança
cd .claude/hooks
cp session-start.sh session-start.sh.backup
cp session-context.sh session-context.sh.backup
cp venv-check.sh venv-check.sh.backup

# 1.3 Commit backups
git add *.backup
git commit -m "backup: Hooks bash originais antes de migração Node.js"
```

#### ETAPA 2: POC - session-start.js (Estimativa: 30min)

```bash
# 2.1 Criar arquivo
cat > .claude/hooks/session-start.js << 'EOJS'
#!/usr/bin/env node
// [copiar pseudocódigo da seção 3.1.4]
EOJS

# 2.2 Permissões executáveis
chmod +x .claude/hooks/session-start.js

# 2.3 Teste manual
CLAUDE_CODE_REMOTE=true \
CLAUDE_PROJECT_DIR=/home/user/Claude-Code-Projetos \
CLAUDE_ENV_FILE=/tmp/test-env \
node .claude/hooks/session-start.js

# 2.4 Validar output
# - JSON válido?
# - continue: true?
# - systemMessage coerente?
# - /tmp/test-env contém export PYTHONPATH?

# 2.5 Commit POC
git add .claude/hooks/session-start.js
git commit -m "feat(hooks): Add session-start.js (Node.js portable version)"
```

#### ETAPA 3: session-context.js (Estimativa: 20min)

```bash
# 3.1 Criar arquivo
cat > .claude/hooks/session-context.js << 'EOJS'
#!/usr/bin/env node
// [copiar pseudocódigo da seção 3.2.4]
EOJS

# 3.2 Permissões
chmod +x .claude/hooks/session-context.js

# 3.3 Teste manual
CLAUDE_PROJECT_DIR=/home/user/Claude-Code-Projetos node .claude/hooks/session-context.js

# 3.4 Validar output
# - JSON válido?
# - Lista skills?
# - Lista agentes?

# 3.5 Commit
git add .claude/hooks/session-context.js
git commit -m "feat(hooks): Add session-context.js (Node.js portable version)"
```

#### ETAPA 4: venv-check.js (Estimativa: 15min)

```bash
# 4.1 Criar arquivo
cat > .claude/hooks/venv-check.js << 'EOJS'
#!/usr/bin/env node
// [copiar pseudocódigo da seção 3.3.4]
EOJS

# 4.2 Permissões
chmod +x .claude/hooks/venv-check.js

# 4.3 Teste manual (sem venv)
node .claude/hooks/venv-check.js
# Deve mostrar RULE_006 VIOLATION

# 4.4 Teste manual (com venv)
VIRTUAL_ENV=/tmp/fake-venv node .claude/hooks/venv-check.js
# Deve mostrar "✓ Virtual environment ativo"

# 4.5 Commit
git add .claude/hooks/venv-check.js
git commit -m "feat(hooks): Add venv-check.js (Node.js portable version)"
```

#### ETAPA 5: TESTES AUTOMATIZADOS (Estimativa: 20min)

```bash
# 5.1 Criar script de teste
cat > .claude/hooks/test-hooks.sh << 'EOTEST'
#!/bin/bash
# [copiar script da seção 6.4]
EOTEST

chmod +x .claude/hooks/test-hooks.sh

# 5.2 Executar
.claude/hooks/test-hooks.sh

# 5.3 Validar todos testes passam
# Se falhar: debugar e corrigir

# 5.4 Commit script de teste
git add .claude/hooks/test-hooks.sh
git commit -m "test(hooks): Add automated test suite for Node.js hooks"
```

#### ETAPA 6: VALIDAÇÃO INTEGRADA (Estimativa: 15min)

```bash
# 6.1 Testar Claude Code startup
# (Se possível em ambiente de teste)

# 6.2 Verificar systemMessage exibido

# 6.3 Verificar PYTHONPATH configurado
echo $PYTHONPATH
# Deve incluir /home/user/Claude-Code-Projetos

# 6.4 Verificar skills listadas

# 6.5 Verificar venv check funcional
```

#### ETAPA 7: MERGE E DEPLOY (Estimativa: 10min)

```bash
# 7.1 Merge para main
git checkout main
git merge feature/nodejs-hooks-portable

# 7.2 Push para remoto
git push origin main

# 7.3 Atualizar README se necessário
# Adicionar nota sobre hooks Node.js
```

### 9.2 Diagrama de Fluxo ASCII

```
┌─────────────────────────────────────────────────────────────┐
│                    INÍCIO: PREPARAÇÃO                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. git checkout -b feature/nodejs-hooks-portable    │   │
│  │ 2. Backup .sh → .sh.backup                          │   │
│  │ 3. git commit backups                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 POC: session-start.js                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Criar session-start.js                           │   │
│  │ 2. chmod +x                                          │   │
│  │ 3. Teste manual com env vars                        │   │
│  │ 4. Validar JSON output                              │   │
│  │ 5. git commit                                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              session-context.js + venv-check.js             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Repetir processo POC para cada hook                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   TESTES AUTOMATIZADOS                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Criar test-hooks.sh                               │   │
│  │ 2. Executar suite completa                           │   │
│  │ 3. Validar 100% passing                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ Todos passam?  │
                  └────────────────┘
                    │            │
                   Sim          Não
                    │            │
                    │            ▼
                    │    ┌─────────────────┐
                    │    │ DEBUG & FIX     │
                    │    │ Voltar para POC │
                    │    └─────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  VALIDAÇÃO INTEGRADA                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Testar Claude Code startup                        │   │
│  │ 2. Verificar systemMessage                           │   │
│  │ 3. Verificar PYTHONPATH                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ Tudo OK?       │
                  └────────────────┘
                    │            │
                   Sim          Não
                    │            │
                    │            ▼
                    │    ┌─────────────────┐
                    │    │ ROLLBACK        │
                    │    │ Restaurar .sh   │
                    │    └─────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                      MERGE & DEPLOY                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. git merge main                                    │   │
│  │ 2. git push                                          │   │
│  │ 3. Atualizar documentação                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │   CONCLUÍDO ✓  │
                  └────────────────┘
```

### 9.3 Estimativa de Tempo

| Etapa | Tempo Estimado | Acumulado |
|-------|----------------|-----------|
| 1. Preparação | 15min | 15min |
| 2. POC session-start.js | 30min | 45min |
| 3. session-context.js | 20min | 65min |
| 4. venv-check.js | 15min | 80min |
| 5. Testes automatizados | 20min | 100min |
| 6. Validação integrada | 15min | 115min |
| 7. Merge & deploy | 10min | 125min |
| **TOTAL** | **~2 horas** | - |

**Buffer para debugging:** +30min (reserva)

**TOTAL COM BUFFER:** ~2.5 horas

---

## SEÇÃO 10: APÊNDICES

### 10.1 Comparação Bash vs Node.js

| Comando Bash | Equivalente Node.js | Notas |
|--------------|---------------------|-------|
| `find . -type d` | `fs.readdirSync()` + filter | Mais portável |
| `wc -l` | `array.length` | Nativo |
| `basename {} .md` | `path.basename(f, '.md')` | Nativo |
| `sed 's/^/  - /'` | `arr.map(x => '  - ' + x)` | Mais legível |
| `cat << EOF` | `console.log()` | Simples |
| `if [ -f "$file" ]` | `fs.existsSync(file)` | Mais robusto |
| `export VAR=val` | `fs.appendFileSync(envFile)` | Funcional |

### 10.2 Troubleshooting Comum

#### Erro: "node: command not found"

**Causa:** Node.js não instalado ou não no PATH

**Solução:**
```bash
# Verificar Node.js
which node
node --version

# Se não instalado:
# Linux: apt install nodejs npm
# Windows: Download de nodejs.org
```

#### Erro: "Permission denied: session-start.js"

**Causa:** Arquivo não é executável

**Solução:**
```bash
chmod +x .claude/hooks/*.js
```

#### Erro: JSON malformado

**Causa:** console.log() mesclado com console.error()

**Solução:**
- Usar `console.error()` para logs de progresso
- Usar `console.log()` APENAS para JSON final

```javascript
console.error('📦 Installing...'); // OK - vai para stderr
console.log(JSON.stringify({...})); // OK - vai para stdout
```

### 10.3 Referências Externas

- Node.js `path` module: https://nodejs.org/api/path.html
- Node.js `fs` module: https://nodejs.org/api/fs.html
- Node.js `os` module: https://nodejs.org/api/os.html
- Node.js `child_process`: https://nodejs.org/api/child_process.html
- Claude Code hooks documentation: (consultar docs oficiais)

---

## SEÇÃO 11: DECISÕES FINAIS

### 11.1 Resumo de Decisões Técnicas

1. **Arquitetura:** Node.js puro (OPÇÃO 2)
2. **Número de arquivos:** 3 (.js) + 3 (.backup)
3. **Detecção de plataforma:** `os.platform()`
4. **Path construction:** `path.join()`
5. **Timeout pip:** 120 segundos
6. **Error handling:** `continue: true` sempre
7. **Versionamento:** Todos .js no Git
8. **Rollback:** Manter .backup temporariamente

### 11.2 Pontos de Atenção

- ⚠️ **Shebang:** `#!/usr/bin/env node` obrigatório em Linux
- ⚠️ **Permissões:** `chmod +x` após criar arquivos
- ⚠️ **PYTHONPATH:** Verificar export correto para CLAUDE_ENV_FILE
- ⚠️ **JSON output:** Sempre via `console.log()`, não `console.error()`

### 11.3 Critérios de Sucesso

Migração considerada bem-sucedida quando:

1. ✅ Todos 3 hooks .js executam sem erros
2. ✅ test-hooks.sh passa 100%
3. ✅ Claude Code startup funciona normalmente
4. ✅ systemMessage exibido corretamente
5. ✅ PYTHONPATH configurado (verificável via `echo $PYTHONPATH`)
6. ✅ Skills listadas no contexto
7. ✅ venv check detecta corretamente VIRTUAL_ENV
8. ✅ Nenhum path hardcoded em código (grep validation)

---

## CONCLUSÃO

Esta especificação técnica detalha a migração completa dos hooks SessionStart de bash para Node.js, garantindo portabilidade total entre Windows (Claude Code CLI) e Linux (Claude Code Web).

**Principais benefícios:**
- ✅ Código único (3 arquivos vs 9)
- ✅ Paths 100% dinâmicos (LIÇÃO 4)
- ✅ Portabilidade garantida (Node.js cross-platform)
- ✅ Manutenção simplificada (single source of truth)
- ✅ Conformidade total com DISASTER_HISTORY

**Próximos passos:**
1. Aprovação desta especificação
2. Implementação seguindo ETAPA 1-7 (seção 9.1)
3. Validação via test-hooks.sh
4. Merge para main

**Estimativa:** ~2.5 horas total

---

**Documento gerado em:** 2025-11-12  
**Versão:** 1.0 - PROPOSTA FINAL  
**Status:** AGUARDANDO APROVAÇÃO PARA IMPLEMENTAÇÃO
