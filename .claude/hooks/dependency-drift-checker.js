#!/usr/bin/env node
/**
 * dependency-drift-checker.js - Detecta dependências desatualizadas
 * ASYNC | TIMEOUT 500ms | RUN-ONCE GUARD
 *
 * Propósito: Avisa se requirements.txt está desatualizado vs pip freeze
 * Valor: Previne "funciona na minha máquina" por dependências divergentes
 * Riscos: Nenhum (apenas lê timestamps)
 */

const fs = require('fs').promises;
const path = require('path');

// ============================================================================
// RUN-ONCE GUARD
// ============================================================================
if (process.env.CLAUDE_DEPS_CHECKED === 'true') {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}
process.env.CLAUDE_DEPS_CHECKED = 'true';

// ============================================================================
// LÓGICA PRINCIPAL (ASYNC)
// ============================================================================
async function checkDependencies() {
  try {
    const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();

    // Verificar se .venv está ativo
    const venvActive = !!process.env.VIRTUAL_ENV;

    if (!venvActive) {
      // venv-check.js já avisa sobre isso, não duplicar mensagem
      return { continue: true };
    }

    // Procurar requirements.txt em vários locais
    const locationsToCheck = [
      cwd,  // Root do projeto
      path.join(cwd, 'agentes'),  // Diretório de agentes
    ];

    const warnings = [];
    const DAYS_THRESHOLD = 30;

    // ========================================================================
    // Verificar root do projeto
    // ========================================================================
    try {
      const reqFile = path.join(cwd, 'requirements.txt');
      const stat = await fs.stat(reqFile);
      const daysSinceModified = (Date.now() - stat.mtimeMs) / 1000 / 60 / 60 / 24;

      if (daysSinceModified > DAYS_THRESHOLD) {
        warnings.push(`📦 Root: requirements.txt há ${Math.floor(daysSinceModified)} dias sem atualização`);
      }
    } catch {
      // requirements.txt não existe no root (OK)
    }

    // ========================================================================
    // Verificar agentes/*/requirements.txt
    // ========================================================================
    const agentesDir = path.join(cwd, 'agentes');

    try {
      const agents = await fs.readdir(agentesDir);

      for (const agent of agents) {
        const agentDir = path.join(agentesDir, agent);

        // Verificar se é diretório
        try {
          const stat = await fs.stat(agentDir);
          if (!stat.isDirectory()) continue;
        } catch {
          continue;
        }

        // Verificar requirements.txt
        const reqFile = path.join(agentDir, 'requirements.txt');

        try {
          const stat = await fs.stat(reqFile);
          const daysSinceModified = (Date.now() - stat.mtimeMs) / 1000 / 60 / 60 / 24;

          if (daysSinceModified > DAYS_THRESHOLD) {
            warnings.push(`📦 ${agent}: requirements.txt há ${Math.floor(daysSinceModified)} dias sem atualização`);
          }
        } catch {
          // requirements.txt não existe neste agente (OK)
        }
      }
    } catch {
      // Diretório agentes/ não existe (OK)
    }

    // ========================================================================
    // Verificar comandos/*/requirements.txt
    // ========================================================================
    const comandosDir = path.join(cwd, 'comandos');

    try {
      const commands = await fs.readdir(comandosDir);

      for (const cmd of commands) {
        const cmdDir = path.join(comandosDir, cmd);

        // Verificar se é diretório
        try {
          const stat = await fs.stat(cmdDir);
          if (!stat.isDirectory()) continue;
        } catch {
          continue;
        }

        // Verificar requirements.txt
        const reqFile = path.join(cmdDir, 'requirements.txt');

        try {
          const stat = await fs.stat(reqFile);
          const daysSinceModified = (Date.now() - stat.mtimeMs) / 1000 / 60 / 60 / 24;

          if (daysSinceModified > DAYS_THRESHOLD) {
            warnings.push(`📦 comandos/${cmd}: requirements.txt há ${Math.floor(daysSinceModified)} dias sem atualização`);
          }
        } catch {
          // requirements.txt não existe neste comando (OK)
        }
      }
    } catch {
      // Diretório comandos/ não existe (OK)
    }

    // ========================================================================
    // Verificar skills/*/requirements.txt
    // ========================================================================
    const skillsDir = path.join(cwd, 'skills');

    try {
      const skills = await fs.readdir(skillsDir);

      for (const skill of skills) {
        const skillDir = path.join(skillsDir, skill);

        // Verificar se é diretório
        try {
          const stat = await fs.stat(skillDir);
          if (!stat.isDirectory()) continue;
        } catch {
          continue;
        }

        // Verificar requirements.txt
        const reqFile = path.join(skillDir, 'requirements.txt');

        try {
          const stat = await fs.stat(reqFile);
          const daysSinceModified = (Date.now() - stat.mtimeMs) / 1000 / 60 / 60 / 24;

          if (daysSinceModified > DAYS_THRESHOLD) {
            warnings.push(`📦 skills/${skill}: requirements.txt há ${Math.floor(daysSinceModified)} dias sem atualização`);
          }
        } catch {
          // requirements.txt não existe nesta skill (OK)
        }
      }
    } catch {
      // Diretório skills/ não existe (OK)
    }

    // ========================================================================
    // Gerar mensagem se houver warnings
    // ========================================================================
    if (warnings.length > 0) {
      let message = '⚠️ DEPENDENCY DRIFT DETECTADO:\n';
      message += warnings.slice(0, 5).join('\n');  // Limitar a 5 avisos

      if (warnings.length > 5) {
        message += `\n   ... e mais ${warnings.length - 5} arquivos\n`;
      }

      message += '\n💡 Atualize com:\n';
      message += '   cd <diretório>\n';
      message += '   .venv\\Scripts\\activate  # Windows\n';
      message += '   # ou: source .venv/bin/activate  # Linux\n';
      message += '   pip freeze > requirements.txt\n';
      message += '   git add requirements.txt\n';
      message += '   git commit -m "chore: atualiza requirements.txt"\n';

      return {
        continue: true,
        systemMessage: message
      };
    }

    // ✅ Tudo OK
    return { continue: true };
  } catch (error) {
    // Graceful degradation
    return { continue: true };
  }
}

// ============================================================================
// TIMEOUT WRAPPER
// ============================================================================
async function mainWithTimeout() {
  const TIMEOUT_MS = 500;

  const timeout = new Promise(resolve =>
    setTimeout(() => resolve({ continue: true }), TIMEOUT_MS)
  );

  const result = await Promise.race([checkDependencies(), timeout]);
  console.log(JSON.stringify(result));
}

// ============================================================================
// EXECUÇÃO
// ============================================================================
mainWithTimeout().catch(() => {
  // Fallback final: Se tudo falhar, retornar JSON vazio
  console.log(JSON.stringify({ continue: true }));
});
