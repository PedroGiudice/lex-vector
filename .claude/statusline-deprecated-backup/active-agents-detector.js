#!/usr/bin/env node
/**
 * active-agents-detector.js - Detecta agentes ativos em tempo real
 *
 * Analisa hooks-status.json para determinar quais agentes foram executados
 * recentemente e gera active-agents.json com a lista de agentes ativos.
 *
 * Critério: Agente é considerado "ativo" se seu hook foi executado nos últimos 5 minutos.
 */

const fs = require('fs').promises;
const path = require('path');

// Configurações
const ACTIVE_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutos
const PROJECT_DIR = process.cwd();

// Mapeamento de hooks para agentes
const HOOK_TO_AGENT_MAP = {
  'invoke-legal-braniac-hybrid': 'legal-braniac',
  'session-context-hybrid': 'session-context',
  'venv-check': 'venv-validator',
  'git-status-watcher': 'git-watcher',
  'data-layer-validator': 'data-validator',
  'dependency-drift-checker': 'dependency-checker',
  'corporate-detector': 'corporate-detector'
};

/**
 * Main entry point
 */
async function main() {
  try {
    const activeAgents = await detectActiveAgents(PROJECT_DIR);
    await saveActiveAgents(PROJECT_DIR, activeAgents);

    // Output para debug (opcional)
    if (process.env.DEBUG) {
      console.log(JSON.stringify(activeAgents, null, 2));
    }

    process.exit(0);
  } catch (error) {
    console.error('Error detecting active agents:', error.message);
    process.exit(1);
  }
}

/**
 * Detecta agentes ativos baseado em hooks-status.json
 */
async function detectActiveAgents(projectDir) {
  const hooksStatus = await loadHooksStatus(projectDir);
  const now = Date.now();
  const activeAgents = [];

  for (const [hookName, hookData] of Object.entries(hooksStatus)) {
    // Verificar se hook foi executado recentemente
    if (!hookData.timestamp) continue;

    const timeSinceExecution = now - hookData.timestamp;

    if (timeSinceExecution <= ACTIVE_THRESHOLD_MS) {
      // Hook está ativo
      const agentName = mapHookToAgent(hookName);

      if (agentName) {
        activeAgents.push({
          name: agentName,
          lastSeen: new Date(hookData.timestamp).toISOString(),
          source: hookName,
          status: hookData.status || 'unknown',
          timeSinceExecution: Math.floor(timeSinceExecution / 1000) // em segundos
        });
      }
    }
  }

  return {
    activeAgents,
    lastUpdate: new Date().toISOString(),
    threshold: `${ACTIVE_THRESHOLD_MS / 1000}s`
  };
}

/**
 * Carrega hooks-status.json
 */
async function loadHooksStatus(projectDir) {
  try {
    const statusFile = path.join(projectDir, '.claude', 'statusline', 'hooks-status.json');
    const content = await fs.readFile(statusFile, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    // Arquivo não existe ou erro de parsing - retornar vazio
    return {};
  }
}

/**
 * Mapeia nome do hook para nome do agente
 */
function mapHookToAgent(hookName) {
  // Tentar mapeamento direto
  if (HOOK_TO_AGENT_MAP[hookName]) {
    return HOOK_TO_AGENT_MAP[hookName];
  }

  // Fallback: extrair nome do hook
  // Ex: "invoke-legal-braniac-hybrid" -> "legal-braniac"
  const match = hookName.match(/invoke-(.+)-hybrid/);
  if (match) {
    return match[1];
  }

  // Fallback 2: usar o próprio nome do hook
  return hookName;
}

/**
 * Salva active-agents.json
 */
async function saveActiveAgents(projectDir, data) {
  const outputFile = path.join(projectDir, '.claude', 'statusline', 'active-agents.json');
  await fs.writeFile(outputFile, JSON.stringify(data, null, 2), 'utf8');
}

// Executar se chamado diretamente
if (require.main === module) {
  main();
}

// Exportar para uso como módulo
module.exports = {
  detectActiveAgents,
  mapHookToAgent,
  ACTIVE_THRESHOLD_MS
};
