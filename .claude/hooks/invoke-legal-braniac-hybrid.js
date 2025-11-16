#!/usr/bin/env node

/**
 * invoke-legal-braniac-hybrid.js - Auto-discovery Legal-Braniac (ASYNC para Windows)
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
  if (process.env.CLAUDE_LEGAL_BRANIAC_LOADED === 'true') {
    return true;
  }
  process.env.CLAUDE_LEGAL_BRANIAC_LOADED = 'true';
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

async function fileExists(filepath) {
  try {
    await fs.access(filepath);
    return true;
  } catch {
    return false;
  }
}

// ============================================================================
// DETECÇÃO DE AMBIENTE
// ============================================================================

function detectEnvironment() {
  const isWindows = process.platform === 'win32';
  const isRemote = process.env.TERM_PROGRAM === 'vscode' && process.env.VSCODE_PID;

  // Detecção heurística de ambiente corporativo
  let possibleCorporate = false;

  if (isWindows && !isRemote) {
    const username = process.env.USERNAME || '';

    // Heurística 1: username formato corporativo (2-4 letras maiúsculas ou FirstLast)
    if (/^[A-Z]{2,4}$/.test(username) || /^[A-Z][a-z]+[A-Z][a-z]+$/.test(username)) {
      possibleCorporate = true;
    }

    // Heurística 2: USERDOMAIN diferente de hostname (domínio Windows)
    const domain = process.env.USERDOMAIN || '';
    const hostname = process.env.COMPUTERNAME || '';
    if (domain && domain !== hostname && domain !== 'WORKGROUP') {
      possibleCorporate = true;
    }
  }

  return {
    isWindows,
    isRemote,
    possibleCorporate,
    platform: process.platform
  };
}

// ============================================================================
// AUTO-DISCOVERY (ASYNC)
// ============================================================================

async function discoverAgentes(projectDir) {
  const agentsDir = path.join(projectDir, '.claude', 'agents');

  if (!await dirExists(agentsDir)) {
    return [];
  }

  try {
    const files = await fs.readdir(agentsDir);
    return files
      .filter(f => f.endsWith('.md') && f !== 'legal-braniac.md')
      .map(f => f.replace('.md', ''))
      .sort();
  } catch {
    return [];
  }
}

async function discoverSkills(projectDir) {
  const skillsDir = path.join(projectDir, 'skills');

  if (!await dirExists(skillsDir)) {
    return [];
  }

  try {
    const entries = await fs.readdir(skillsDir);

    // Verifica em paralelo quais são diretórios com SKILL.md
    const checks = await Promise.all(
      entries.map(async (entry) => {
        try {
          const entryPath = path.join(skillsDir, entry);
          const stat = await fs.stat(entryPath);

          if (!stat.isDirectory()) {
            return null;
          }

          const skillMdPath = path.join(entryPath, 'SKILL.md');
          const hasSkillMd = await fileExists(skillMdPath);

          return hasSkillMd ? entry : null;
        } catch {
          return null;
        }
      })
    );

    return checks.filter(Boolean).sort();
  } catch {
    return [];
  }
}

// ============================================================================
// FORMATAÇÃO
// ============================================================================

function formatMessage(agentes, skills) {
  const agentesStr = agentes.length <= 3
    ? agentes.join(', ')
    : `${agentes.slice(0, 2).join(', ')}, +${agentes.length - 2}`;

  const skillsStr = skills.length <= 3
    ? skills.join(', ')
    : `${skills.slice(0, 2).join(', ')}, +${skills.length - 2}`;

  let message = `🧠 Legal-Braniac: Orquestrador ativo\n`;

  if (agentes.length > 0) {
    message += `📋 Agentes (${agentes.length}): ${agentesStr}\n`;
  }

  if (skills.length > 0) {
    message += `🛠️  Skills (${skills.length}): ${skillsStr}`;
  }

  return message;
}

// ============================================================================
// MAIN LOGIC (ASYNC)
// ============================================================================

async function main() {
  console.error('[DEBUG] invoke-legal-braniac-hybrid: Iniciando...');

  // RUN-ONCE GUARD
  if (shouldSkip()) {
    console.error('[DEBUG] invoke-legal-braniac-hybrid: Skipando (run-once guard)');
    outputJSON({
      continue: true,
      systemMessage: ''
    });
    return;
  }

  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const env = detectEnvironment();
  console.error(`[DEBUG] invoke-legal-braniac-hybrid: Env detectado - isWindows:${env.isWindows}, isRemote:${env.isRemote}, possibleCorporate:${env.possibleCorporate}`);

  // Skip no Windows CLI corporativo (EPERM risk)
  if (!env.isRemote && env.isWindows && env.possibleCorporate) {
    console.error('[DEBUG] invoke-legal-braniac-hybrid: Skipando (ambiente corporativo Windows)');
    outputJSON({
      continue: true,
      systemMessage: ''
    });
    return;
  }

  try {
    // Paralelização: busca agentes e skills simultaneamente
    const [agentes, skills] = await Promise.all([
      discoverAgentes(projectDir),
      discoverSkills(projectDir)
    ]);

    console.error(`[DEBUG] invoke-legal-braniac-hybrid: Descobertos - Agentes:${agentes.length}, Skills:${skills.length}`);

    // Se não tem nada, skip silencioso
    if (agentes.length === 0 && skills.length === 0) {
      console.error('[DEBUG] invoke-legal-braniac-hybrid: Nenhum agente/skill descoberto');
      outputJSON({
        continue: true,
        systemMessage: '🧠 Legal-Braniac: Ativo (sem agentes/skills descobertos)'
      });
      return;
    }

    const message = formatMessage(agentes, skills);
    console.error(`[DEBUG] invoke-legal-braniac-hybrid: Mensagem formatada, enviando output`);

    // Criar marker file para statusline
    try {
      const markerPath = path.join(projectDir, '.claude/legal-braniac-active.json');
      const markerData = {
        timestamp: Date.now(),
        action: 'orchestrating',
        agentes: agentes.length,
        skills: skills.length
      };
      await fs.writeFile(markerPath, JSON.stringify(markerData, null, 2));
      console.error(`[DEBUG] invoke-legal-braniac-hybrid: Marker file criado em ${markerPath}`);
    } catch (err) {
      console.error(`[DEBUG] invoke-legal-braniac-hybrid: Erro ao criar marker file: ${err.message}`);
    }

    outputJSON({
      continue: true,
      systemMessage: message
    });

  } catch (error) {
    outputJSON({
      continue: true,
      systemMessage: `🧠 Legal-Braniac: Erro durante auto-discovery (${error.message})`
    });
  }
}

// ============================================================================
// WRAPPER COM TIMEOUT
// ============================================================================

async function mainWithTimeout() {
  const timeout = new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        continue: true,
        systemMessage: '🧠 Legal-Braniac: Ativo (timeout)\n'
      });
    }, 500); // 500ms timeout
  });

  const execution = main();

  try {
    await Promise.race([execution, timeout]);
  } catch (error) {
    outputJSON({
      continue: true,
      systemMessage: ''
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
