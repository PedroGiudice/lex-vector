#!/usr/bin/env node
/**
 * block-commit-main.js - Bloqueia git commit quando na branch main
 *
 * Hook contextual para PermissionRequest que verifica:
 * 1. Se o comando é git commit
 * 2. Se a branch atual é main/master
 * 3. Bloqueia se ambos forem verdadeiros
 *
 * Diferente do hookify (declarativo/regex), este hook é CONTEXTUAL.
 */

const { execSync } = require('child_process');
const fs = require('fs');

const PROJECT_DIR = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const DEBUG = process.env.DEBUG === '1';

function debug(...args) {
  if (DEBUG) console.error('[block-commit-main]', ...args);
}

function getCurrentBranch() {
  try {
    const branch = execSync('git branch --show-current', {
      cwd: PROJECT_DIR,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    }).trim();
    return branch;
  } catch (e) {
    debug('Não é um repo git ou erro:', e.message);
    return null;
  }
}

function isGitCommitCommand(command) {
  // Detecta variações de git commit
  const patterns = [
    /^git\s+commit\b/,
    /&&\s*git\s+commit\b/,
    /;\s*git\s+commit\b/,
    /\|\s*git\s+commit\b/
  ];
  return patterns.some(p => p.test(command));
}

async function main() {
  let input = '';
  try {
    input = fs.readFileSync(0, 'utf8');
  } catch (e) {
    debug('Sem stdin');
    // Sem input = não bloquear (deixar passar para próximo hook)
    process.exit(0);
  }

  if (!input.trim()) {
    process.exit(0);
  }

  let data;
  try {
    data = JSON.parse(input);
  } catch (e) {
    debug('JSON inválido');
    process.exit(0);
  }

  const toolName = data.toolName || data.tool_name || data.tool || '';
  const toolInput = data.toolInput || data.tool_input || data.input || {};
  const command = toolInput.command || '';

  debug('Tool:', toolName);
  debug('Command:', command);

  // Só verificar comandos Bash
  if (toolName !== 'Bash') {
    process.exit(0);
  }

  // Verificar se é git commit
  if (!isGitCommitCommand(command)) {
    process.exit(0);
  }

  debug('Detectado git commit, verificando branch...');

  // Verificar branch atual
  const branch = getCurrentBranch();
  debug('Branch atual:', branch);

  if (branch === 'main' || branch === 'master') {
    // BLOQUEAR
    console.log(JSON.stringify({
      behavior: 'deny',
      message: `🛑 **COMMIT EM ${branch.toUpperCase()} BLOQUEADO**

Você está tentando fazer commit diretamente na branch \`${branch}\`.

**Por que isso é bloqueado:**
- O hook \`auto-branch.sh\` deveria ter criado uma branch de trabalho
- Commits diretos em \`${branch}\` são proibidos para proteção do código

**O que fazer:**
1. Crie uma branch de trabalho:
   \`\`\`bash
   git checkout -b work/sua-tarefa
   \`\`\`
2. Faça o commit na nova branch
3. Abra um PR para merge em \`${branch}\`

**Se você REALMENTE precisa commitar em ${branch}:**
Aprove manualmente (não recomendado).

> Hook: .claude/hooks/block-commit-main.js`
    }));
    process.exit(0);
  }

  // Não está em main/master - permitir (não emitir nada, deixar próximo hook decidir)
  debug('Branch não é main/master, permitindo...');
  process.exit(0);
}

main().catch(e => {
  console.error('[block-commit-main] Erro:', e.message);
  process.exit(0);
});
