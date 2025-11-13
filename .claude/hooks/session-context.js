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
  // STRATEGY: Usar CLAUDE_PROJECT_DIR se disponível, senão process.cwd()
  // Isso NÃO é hardcoded - é dinâmico baseado no diretório de execução
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

  // Validar que estamos em um diretório de projeto válido
  if (!fs.existsSync(path.join(projectDir, '.claude'))) {
    outputJSON({
      continue: true,
      systemMessage: '⚠️ Diretório .claude não encontrado - não parece ser um projeto Claude Code'
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
  context += `📁 Arquitetura: CODE (Git) | ENV (.venv) | DATA (externo)
⚠️  Regras: RULE_006 (venv obrigatório) | RULE_004 (sem hardcode paths)
`;

  // -------------------------------------------------------------------------
  // 2. Skills disponíveis
  // -------------------------------------------------------------------------
  const skillsDir = path.join(projectDir, 'skills');
  const skillCount = countDirectories(skillsDir);

  if (skillCount > 0) {
    context += `🛠️  Skills: ${skillCount} disponíveis\n`;
  }

  // -------------------------------------------------------------------------
  // 3. Agentes especializados
  // -------------------------------------------------------------------------
  const agentsDir = path.join(projectDir, '.claude', 'agents');
  const agentFiles = listMdFiles(agentsDir);

  if (agentFiles.length > 0) {
    const names = agentFiles.map(f => removeExtension(f)).join(', ');
    context += `🤖 Agentes: ${agentFiles.length} (${names})\n`;
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
