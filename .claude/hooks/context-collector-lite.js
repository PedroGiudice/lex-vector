#!/usr/bin/env node

/**
 * context-collector-lite.js - Versão simplificada (sem orquestração)
 *
 * Trigger: UserPromptSubmit
 * Função: Coletar contexto + validações + aesthetic enforcement
 *
 * REMOVIDO (legal-braniac redundante):
 * - Session state dependency
 * - Agent orchestration
 * - Skill detection (já feito por skill-content-injector.js)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Importar apenas o necessário
let runValidations, enforceAesthetics;
try {
  runValidations = require('./lib/validations').runValidations;
} catch {
  runValidations = async () => [];
}
try {
  enforceAesthetics = require('./lib/aesthetic-enforcer').enforceAesthetics;
} catch {
  enforceAesthetics = async () => ({ passed: true });
}

// ============================================================================
// CONTEXT COLLECTION
// ============================================================================

function collectContext(projectDir, stdinData = null) {
  let prompt = '';

  // Fonte 1: stdin JSON (fonte primária - Claude Code padrão)
  if (stdinData) {
    prompt = stdinData.prompt || stdinData.userPrompt || stdinData.message || '';
  }

  // Fonte 2: env var (fallback)
  if (!prompt) {
    prompt = process.env.CLAUDE_USER_PROMPT || '';
  }

  const context = {
    timestamp: Date.now(),
    prompt,
    projectDir,
    git: {
      modifiedFiles: [],
      status: 'unknown'
    },
    env: {
      venvActive: !!process.env.VIRTUAL_ENV,
      platform: process.platform
    }
  };

  // Git context (se disponível)
  try {
    const modifiedFiles = execSync('git diff --name-only', {
      cwd: projectDir,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore']
    }).trim().split('\n').filter(Boolean);

    const gitStatus = execSync('git status --porcelain', {
      cwd: projectDir,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore']
    }).trim();

    context.git = {
      modifiedFiles,
      status: gitStatus ? 'dirty' : 'clean'
    };
  } catch {
    context.git.status = 'not-a-git-repo';
  }

  return context;
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

  // Ler stdin JSON
  let stdinData = null;
  try {
    const stdinBuffer = fs.readFileSync(0, 'utf-8');
    if (stdinBuffer.trim()) {
      stdinData = JSON.parse(stdinBuffer);
    }
  } catch {
    // Silently ignore stdin read errors
  }

  try {
    // Coletar contexto
    const context = collectContext(projectDir, stdinData);

    const parts = [];

    // 1. VALIDATIONS
    const validations = await runValidations(context, []);
    const failures = validations.filter(v => !v.passed);
    if (failures.length > 0) {
      parts.push(`${failures.map(f => f.message).join(' | ')}`);
    }

    // 2. AESTHETIC ENFORCEMENT (só se git commit detectado)
    if (context.prompt.toLowerCase().includes('git commit')) {
      const aesthetic = await enforceAesthetics(context);
      if (!aesthetic.passed) {
        parts.push(`${aesthetic.violations?.join(' | ') || 'Aesthetic violation'}`);
        console.log(JSON.stringify({
          continue: false,
          systemMessage: parts.join('\n')
        }));
        process.exit(1);
      }
    }

    // Output para Claude Code
    console.log(JSON.stringify({
      continue: true,
      systemMessage: parts.length > 0 ? parts.join('\n') : ''
    }));

  } catch (error) {
    console.log(JSON.stringify({
      continue: true,
      systemMessage: `Context collector: ${error.message}`
    }));
  }
}

main().catch(() => {
  console.log(JSON.stringify({ continue: true, systemMessage: '' }));
});
