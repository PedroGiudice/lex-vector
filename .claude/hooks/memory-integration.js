#!/usr/bin/env node

/**
 * memory-integration.js - Integração entre Legal-Braniac e Sistema de Memória Episódica
 *
 * Funcionalidades:
 * 1. Injeta contexto de memórias relevantes no SystemMessage
 * 2. Fornece instruções para armazenar novas memórias
 *
 * Hook Type: UserPromptSubmit (com run-once guard para injeção inicial)
 *
 * Arquitetura:
 * - Python: EpisodicMemory (shared/memory/episodic_memory.py)
 * - Node.js: Este hook (bridge entre Claude Code e Python backend)
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ============================================================================
// RUN-ONCE GUARD
// ============================================================================

function shouldSkip() {
  if (process.env.CLAUDE_MEMORY_INTEGRATION_LOADED === 'true') {
    return true;
  }

  process.env.CLAUDE_MEMORY_INTEGRATION_LOADED = 'true';
  return false;
}

// ============================================================================
// FUNÇÕES AUXILIARES
// ============================================================================

function outputJSON(obj) {
  console.log(JSON.stringify(obj));
}

function getProjectDir() {
  return process.env.CLAUDE_PROJECT_DIR || process.cwd();
}

function fileExists(filepath) {
  try {
    return fs.existsSync(filepath);
  } catch {
    return false;
  }
}

// ============================================================================
// PYTHON INTEGRATION
// ============================================================================

function getMemoryDir() {
  const projectDir = getProjectDir();
  const memoryDir = path.join(projectDir, 'shared', 'memory', 'data');

  // Criar diretório se não existir
  try {
    if (!fs.existsSync(memoryDir)) {
      fs.mkdirSync(memoryDir, { recursive: true });
    }
  } catch (e) {
    // Ignorar erro se já existe
  }

  return memoryDir;
}

function recallMemories(query = null, tags = null, limit = 5) {
  /**
   * Chama o sistema de memória Python para recuperar memórias.
   *
   * Returns: Array de memórias relevantes
   */
  const projectDir = getProjectDir();
  const memoryScript = path.join(projectDir, 'shared', 'memory', 'episodic_memory.py');

  if (!fileExists(memoryScript)) {
    return null; // Sistema de memória não disponível
  }

  try {
    const memoryDir = getMemoryDir();
    let cmd = `python3 "${memoryScript}" --memory-dir "${memoryDir}" --action recall --limit ${limit}`;

    if (tags) {
      const tagsStr = Array.isArray(tags) ? tags.join(' ') : tags;
      cmd += ` --tags ${tagsStr}`;
    }

    // Executar com timeout de 5s
    const output = execSync(cmd, {
      encoding: 'utf-8',
      timeout: 5000,
      stdio: ['pipe', 'pipe', 'pipe'] // Capturar stderr
    });

    // Parse do output (formato: ## 1. Titulo\n   Tipo: ...\n   Conteúdo: ...)
    // Por simplicidade, retornar output bruto
    return output;

  } catch (error) {
    // Silent fail - memória é opcional
    return null;
  }
}

// ============================================================================
// FORMATAÇÃO DE MENSAGEM
// ============================================================================

function formatMemoryContext(memories) {
  if (!memories || memories.trim() === '') {
    return null;
  }

  // Verificar se há memórias na resposta
  if (memories.includes('0 memórias encontradas')) {
    return null;
  }

  return `🧠 Memória Episódica Ativada

Memórias relevantes do projeto:

${memories}

---

INSTRUÇÕES DE USO:

Durante esta sessão, você pode armazenar novas memórias usando:

\`\`\`bash
python3 shared/memory/episodic_memory.py \\
  --memory-dir shared/memory/data \\
  --action store \\
  --type <tipo> \\
  --title "Título da memória" \\
  --content "Conteúdo detalhado" \\
  --tags tag1 tag2 tag3
\`\`\`

Tipos disponíveis:
- architectural_decision
- bug_resolution
- solution_pattern
- project_context
- lesson_learned
- api_workaround
- orchestration

Armazene automaticamente:
- Bugs críticos resolvidos (ex: DJEN API, hooks Windows)
- Decisões arquiteturais importantes
- Workarounds descobertos
- Padrões de solução bem-sucedidos

Para buscar memórias:
\`\`\`bash
python3 shared/memory/episodic_memory.py \\
  --memory-dir shared/memory/data \\
  --action recall \\
  --tags DJEN API \\
  --limit 10
\`\`\`

Para estatísticas:
\`\`\`bash
python3 shared/memory/episodic_memory.py \\
  --memory-dir shared/memory/data \\
  --action stats
\`\`\`
`;
}

// ============================================================================
// MAIN LOGIC
// ============================================================================

function main() {
  // RUN-ONCE GUARD: Skip se já executou
  if (shouldSkip()) {
    outputJSON({
      continue: true,
      systemMessage: '' // Silent skip
    });
    return;
  }

  const projectDir = getProjectDir();

  // Verificar se sistema de memória existe
  const memoryScript = path.join(projectDir, 'shared', 'memory', 'episodic_memory.py');

  if (!fileExists(memoryScript)) {
    // Sistema de memória não disponível - skip silencioso
    outputJSON({
      continue: true,
      systemMessage: ''
    });
    return;
  }

  try {
    // Recuperar memórias recentes e relevantes
    // Tags prioritárias: project context, bugs, workarounds
    const memories = recallMemories(null, ['DJEN', 'API', 'hooks', 'windows', 'arquitetura'], 5);

    const message = formatMemoryContext(memories);

    if (message) {
      outputJSON({
        continue: true,
        systemMessage: message
      });
    } else {
      // Sem memórias - apenas informar que sistema está disponível
      outputJSON({
        continue: true,
        systemMessage: `🧠 Sistema de Memória Episódica disponível

Use \`python3 shared/memory/episodic_memory.py --help\` para detalhes.

Armazene memórias importantes durante a sessão para referência futura.`
      });
    }

  } catch (error) {
    // Silent fail - memória é opcional
    outputJSON({
      continue: true,
      systemMessage: ''
    });
  }
}

// ============================================================================
// EXECUÇÃO
// ============================================================================

try {
  main();
} catch (error) {
  outputJSON({
    continue: true,
    systemMessage: ''
  });
}
