#!/usr/bin/env node

/**
 * context-collector.js - Coleta contexto e delega para Legal-Braniac
 *
 * Trigger: UserPromptSubmit (Nx por sessão)
 * Função: Coletar contexto + invocar Decision Engine
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');
const { runValidations } = require('./lib/validations');
const { detectSkill } = require('./lib/skill-detector');
const { orchestrateAgents } = require('./lib/agent-orchestrator');
const { enforceAesthetics } = require('./lib/aesthetic-enforcer');

// ============================================================================
// CONTEXT COLLECTION
// ============================================================================

async function collectContext(projectDir) {
  const context = {
    timestamp: Date.now(),
    prompt: process.env.CLAUDE_USER_PROMPT || '',
    projectDir,
    git: {
      modifiedFiles: [],
      status: 'unknown',
      lastCommitAge: null
    },
    env: {
      venvActive: !!process.env.VIRTUAL_ENV,
      venvPath: process.env.VIRTUAL_ENV || null,
      platform: process.platform
    }
  };

  // Git context (se disponível)
  try {
    const modifiedFiles = execSync('git diff --name-only', {
      cwd: projectDir,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'] // Silenciar stderr
    })
      .trim()
      .split('\n')
      .filter(Boolean);

    const gitStatus = execSync('git status --porcelain', {
      cwd: projectDir,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore']
    }).trim();

    // Tentar obter idade do último commit
    try {
      const gitIndexPath = path.join(projectDir, '.git', 'index');
      const gitIndexStat = await fs.stat(gitIndexPath);
      context.git.lastCommitAge = Date.now() - gitIndexStat.mtimeMs;
    } catch {
      // .git/index não acessível - OK
    }

    context.git = {
      modifiedFiles,
      status: gitStatus ? 'dirty' : 'clean',
      lastCommitAge: context.git.lastCommitAge
    };
  } catch {
    // Não é repo Git ou erro - usar defaults
    context.git.status = 'not-a-git-repo';
  }

  return context;
}

// ============================================================================
// LEGAL-BRANIAC DECISION ENGINE
// ============================================================================

async function legalBraniacDecide(context, sessionState) {
  const decisions = {
    validations: [],
    skillActivation: null,
    agentOrchestration: null,
    aestheticEnforcement: null
  };

  // 1. VALIDATIONS
  decisions.validations = await runValidations(context, sessionState.validations);

  // 2. SKILL DETECTION (v2.0: detectSkill agora lê skill-rules.json diretamente)
  decisions.skillActivation = detectSkill(context.prompt);

  // 3. AGENT ORCHESTRATION (só para prompts complexos)
  decisions.agentOrchestration = await orchestrateAgents(
    context,
    sessionState.agentes
  );

  // 4. AESTHETIC ENFORCEMENT (se git commit detectado)
  if (context.prompt.toLowerCase().includes('git commit')) {
    decisions.aestheticEnforcement = await enforceAesthetics(context);
  }

  return decisions;
}

// ============================================================================
// OUTPUT FORMATTING
// ============================================================================

function formatOutput(decisions) {
  const messages = [];

  // Validations (só failures)
  const failures = decisions.validations.filter(v => !v.passed);
  if (failures.length > 0) {
    const failureMessages = failures.map(f => f.message).join('\n');
    messages.push(`⚠️  VALIDATIONS:\n${failureMessages}`);
  }

  // Skill activation (v2.0: mostra top 5 skills detectadas)
  if (decisions.skillActivation && decisions.skillActivation.topSkills && decisions.skillActivation.topSkills.length > 0) {
    const detection = decisions.skillActivation;
    const top5List = detection.topSkills
      .map(s => `  - ${s.skillName} (${s.config.priority}) [score: ${s.finalScore}]`)
      .join('\n');

    messages.push(
      `🎯 SKILLS DETECTADAS (${detection.totalMatched} matched de ${detection.totalConsidered}, showing top ${detection.topSkills.length}):\n` +
      top5List + `\n\n` +
      `💡 Consider using these skills for optimal response quality.`
    );
  }

  // Agent orchestration
  if (
    decisions.agentOrchestration &&
    decisions.agentOrchestration.complexity !== 'LOW'
  ) {
    const orch = decisions.agentOrchestration;
    messages.push(
      `🧠 LEGAL-BRANIAC - ORQUESTRAÇÃO DETECTADA:\n` +
        `Complexidade: ${orch.complexity}\n` +
        `Subtarefas: ${orch.subtasks.length}\n\n` +
        `PLANO:\n${orch.plan}`
    );
  }

  // Aesthetic enforcement
  if (decisions.aestheticEnforcement) {
    if (!decisions.aestheticEnforcement.passed) {
      messages.push(
        `🎨 AESTHETIC ENFORCEMENT FAILED:\n` +
          decisions.aestheticEnforcement.violations.join('\n')
      );
    } else if (decisions.aestheticEnforcement.warning) {
      messages.push(decisions.aestheticEnforcement.warning);
    } else if (decisions.aestheticEnforcement.warnings) {
      messages.push(
        `⚠️  AESTHETIC WARNINGS:\n` +
          decisions.aestheticEnforcement.warnings.join('\n')
      );
    }
  }

  return messages.length > 0 ? messages.join('\n\n') : '';
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

  try {
    // Carregar session state (criado por legal-braniac-loader.js)
    const sessionPath = path.join(projectDir, '.claude', 'hooks', 'legal-braniac-session.json');

    let sessionState;
    try {
      const sessionContent = await fs.readFile(sessionPath, 'utf8');
      sessionState = JSON.parse(sessionContent);
    } catch (error) {
      // Session state não existe ou corrompido - recriar on-the-fly
      console.error('[WARN] Session state inválido - recriando...');

      execSync('node .claude/hooks/legal-braniac-loader.js', { cwd: projectDir });

      // Tentar novamente
      const sessionContent = await fs.readFile(sessionPath, 'utf8');
      sessionState = JSON.parse(sessionContent);
    }

    // Coletar contexto
    const context = await collectContext(projectDir);

    // Legal-Braniac decide
    const decisions = await legalBraniacDecide(context, sessionState);

    // Formatar output
    const message = formatOutput(decisions);

    // Determinar se deve continuar
    const shouldContinue = decisions.aestheticEnforcement
      ? decisions.aestheticEnforcement.passed
      : true;

    // Output para Claude Code
    console.log(
      JSON.stringify({
        continue: shouldContinue,
        systemMessage: message
      })
    );

    // Exit code (para aesthetic enforcement blocker)
    if (!shouldContinue) {
      process.exit(1);
    }
  } catch (error) {
    console.error(`[ERROR] context-collector: ${error.message}`);
    console.log(
      JSON.stringify({
        continue: true,
        systemMessage: `⚠️  Context collector: ${error.message}`
      })
    );
  }
}

main().catch(() => {
  console.log(JSON.stringify({ continue: true, systemMessage: '' }));
});
