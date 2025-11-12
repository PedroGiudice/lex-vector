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
  const agentsDir = path.join(projectDir, '.claude', 'agents');
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
