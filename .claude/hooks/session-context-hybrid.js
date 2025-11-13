#!/usr/bin/env node

/**
 * session-context-hybrid.js - Injeta contexto do projeto (ASYNC para Windows)
 *
 * SOLUÇÃO DEFINITIVA para Windows CLI subprocess polling + lock contention:
 * - Usa fs.promises (ASYNC) ao invés de fs.*Sync (evita Issue #9849 lock contention)
 * - Timeout 500ms (evita hang infinito)
 * - Run-once guard (evita execuções repetidas em UserPromptSubmit)
 * - Promise.all() para paralelização
 *
 * Compatibilidade:
 * - SessionStart (Web/Linux): executa normalmente
 * - UserPromptSubmit (Windows CLI): executa ASYNC sem bloqueio
 *
 * Baseado em:
 * - https://github.com/DennisLiuCk/cc-toolkit/commit/09ab8674
 * - Issue #9542 (SessionStart hang) + Issue #9849 (UserPromptSubmit loop)
 */

const fs = require('fs').promises;
const path = require('path');

// ============================================================================
// RUN-ONCE GUARD
// ============================================================================

function shouldSkip() {
  if (process.env.CLAUDE_SESSION_CONTEXT_LOADED === 'true') {
    return true;
  }
  process.env.CLAUDE_SESSION_CONTEXT_LOADED = 'true';
  return false;
}

// ============================================================================
// FUNÇÕES AUXILIARES ASYNC
// ============================================================================

function outputJSON(obj) {
  console.log(JSON.stringify(obj));
}

async function dirExists(dirpath) {
  try {
    const stat = await fs.stat(dirpath);
    return stat.isDirectory();
  } catch {
    return false;
  }
}

async function countFiles(dirpath, extension) {
  try {
    const files = await fs.readdir(dirpath);
    return files.filter(f => f.endsWith(extension)).length;
  } catch {
    return 0;
  }
}

async function countDirs(dirpath) {
  try {
    const entries = await fs.readdir(dirpath);
    const checks = await Promise.all(
      entries.map(async (entry) => {
        try {
          const stat = await fs.stat(path.join(dirpath, entry));
          return stat.isDirectory();
        } catch {
          return false;
        }
      })
    );
    return checks.filter(Boolean).length;
  } catch {
    return 0;
  }
}

// ============================================================================
// DETECÇÃO DE AMBIENTE
// ============================================================================

function detectEnvironment() {
  const isWindows = process.platform === 'win32';
  const isRemote = process.env.TERM_PROGRAM === 'vscode' && process.env.VSCODE_PID;

  return {
    isWindows,
    isRemote,
    platform: process.platform
  };
}

// ============================================================================
// MAIN LOGIC (ASYNC)
// ============================================================================

async function main() {
  // RUN-ONCE GUARD
  if (shouldSkip()) {
    outputJSON({
      continue: true,
      systemMessage: ''
    });
    return;
  }

  const env = detectEnvironment();
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

  let context = `📂 Projeto: ${path.basename(projectDir)}\n`;

  // Estrutura .claude/ (ASYNC)
  const claudeDir = path.join(projectDir, '.claude');

  if (await dirExists(claudeDir)) {
    const agentsDir = path.join(claudeDir, 'agents');
    const hooksDir = path.join(claudeDir, 'hooks');
    const skillsDir = path.join(projectDir, 'skills');

    // Paralelização com Promise.all
    const [agentCount, hookCount, skillCount] = await Promise.all([
      countFiles(agentsDir, '.md'),
      (async () => {
        try {
          const files = await fs.readdir(hooksDir);
          return files.filter(f => f.endsWith('.js') || f.endsWith('.sh')).length;
        } catch {
          return 0;
        }
      })(),
      countDirs(skillsDir)
    ]);

    context += `🤖 Agentes: ${agentCount} | ⚙️  Hooks: ${hookCount} | 🛠️  Skills: ${skillCount}\n`;
  }

  // Arquitetura do projeto
  context += `📁 Arquitetura: CODE (Git) | ENV (.venv) | DATA (externo)\n`;
  context += `⚠️  Regras: RULE_006 (venv obrigatório) | RULE_004 (sem hardcode paths)\n`;

  // Ambiente atual
  if (env.isRemote) {
    context += `🌐 Ambiente: Web (Linux)\n`;
  } else if (env.isWindows) {
    context += `💻 Ambiente: Windows CLI\n`;
  } else {
    context += `🖥️  Ambiente: ${env.platform}\n`;
  }

  outputJSON({
    continue: true,
    systemMessage: context
  });
}

// ============================================================================
// WRAPPER COM TIMEOUT
// ============================================================================

async function mainWithTimeout() {
  const timeout = new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        continue: true,
        systemMessage: '📂 Projeto carregado (timeout)\n'
      });
    }, 500); // 500ms timeout
  });

  const execution = main();

  try {
    await Promise.race([execution, timeout]);
  } catch (error) {
    outputJSON({
      continue: true,
      systemMessage: `⚠️ session-context: ${error.message}`
    });
  }
}

// ============================================================================
// EXECUÇÃO
// ============================================================================

mainWithTimeout().catch(() => {
  outputJSON({
    continue: true,
    systemMessage: ''
  });
});
