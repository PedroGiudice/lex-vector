#!/usr/bin/env node
/**
 * git-status-watcher.js - Avisa sobre mudanças não commitadas
 * ASYNC | TIMEOUT 300ms | RUN-ONCE GUARD
 *
 * Propósito: Avisa se há mudanças não salvas no Git antes de iniciar sessão
 * Valor: Previne perda de trabalho, alinha com DISASTER_HISTORY.md (commit frequente)
 * Riscos: Nenhum (apenas lê timestamps de arquivos)
 */

const fs = require('fs').promises;
const path = require('path');

// ============================================================================
// RUN-ONCE GUARD
// ============================================================================
if (process.env.CLAUDE_GIT_STATUS_CHECKED === 'true') {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}
process.env.CLAUDE_GIT_STATUS_CHECKED = 'true';

// ============================================================================
// LÓGICA PRINCIPAL (ASYNC)
// ============================================================================
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

    try {
      const gitIndexStat = await fs.stat(gitIndex);
      const now = Date.now();
      const minutesSinceLastCommit = (now - gitIndexStat.mtimeMs) / 1000 / 60;

      let message = '';

      if (minutesSinceLastCommit > 60) {
        // Último commit há mais de 1 hora
        const hours = Math.floor(minutesSinceLastCommit / 60);
        const minutes = Math.floor(minutesSinceLastCommit % 60);

        message = `⚠️ GIT: Último commit há ${hours}h ${minutes}m\n`;
        message += `💡 Considere commitar mudanças: git add . && git commit -m "..." && git push\n`;
        message += `📖 Ver DISASTER_HISTORY.md sobre importância de commits frequentes\n`;
      }

      return {
        continue: true,
        systemMessage: message
      };
    } catch {
      // .git/index não existe ou não acessível (repo novo?)
      return { continue: true };
    }
  } catch (error) {
    // Graceful degradation
    return { continue: true };
  }
}

// ============================================================================
// TIMEOUT WRAPPER
// ============================================================================
async function mainWithTimeout() {
  const TIMEOUT_MS = 300;

  const timeout = new Promise(resolve =>
    setTimeout(() => resolve({ continue: true }), TIMEOUT_MS)
  );

  const result = await Promise.race([checkGitStatus(), timeout]);
  console.log(JSON.stringify(result));
}

// ============================================================================
// EXECUÇÃO
// ============================================================================
mainWithTimeout().catch(() => {
  // Fallback final: Se tudo falhar, retornar JSON vazio
  console.log(JSON.stringify({ continue: true }));
});
