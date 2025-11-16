#!/usr/bin/env node
/**
 * legal-braniac-statusline.js - Status line customizado para Legal-Braniac
 *
 * Exibe em tempo real:
 * - Informações do modelo e sessão (tokens, custo)
 * - Contadores de agentes, skills e hooks disponíveis
 * - Contexto do projeto (diretório, branch Git)
 *
 * MVP - Fase 1: Auto-discovery estático (sem tracking de execução)
 */

const fs = require('fs').promises;
const path = require('path');

// ANSI Colors
const colors = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',

  // Foreground
  black: '\x1b[30m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  gray: '\x1b[90m',
};

/**
 * Main entry point
 */
async function main() {
  try {
    // Lê JSON do Claude Code via stdin
    const claudeData = JSON.parse(await readStdin());

    // Lê dados do projeto
    const projectData = await getProjectData(claudeData.workspace?.current_dir || process.cwd());

    // Gera statusline
    const statusline = generateStatusline(claudeData, projectData);

    console.log(statusline);
  } catch (error) {
    // Graceful fallback - não quebrar o Claude Code
    console.log(`${colors.yellow}⚠️ Legal-Braniac Status${colors.reset} ${colors.dim}(error loading data)${colors.reset}`);
  }
}

/**
 * Coleta dados do projeto
 */
async function getProjectData(projectDir) {
  const [agents, skills, hooks, hooksStatus, activeAgents, promptQuality, vocabulary, confidence] = await Promise.all([
    discoverAgents(projectDir),
    discoverSkills(projectDir),
    discoverHooks(projectDir),
    getHooksStatus(projectDir),
    getActiveAgents(projectDir),
    getPromptQuality(projectDir),
    getUserVocabulary(projectDir),
    getPatternConfidence(projectDir)
  ]);

  return {
    agents,
    skills,
    hooks,
    hooksStatus,
    activeAgents,
    promptQuality,
    vocabulary,
    confidence
  };
}

/**
 * Descobre agentes em .claude/agents/*.md
 */
async function discoverAgents(projectDir) {
  try {
    const agentsDir = path.join(projectDir, '.claude', 'agents');
    const files = await fs.readdir(agentsDir);

    const agents = files
      .filter(f => f.endsWith('.md'))
      .map(f => ({
        name: f.replace('.md', ''),
        file: f
      }));

    return agents;
  } catch {
    return [];
  }
}

/**
 * Descobre skills no diretório skills/
 */
async function discoverSkills(projectDir) {
  try {
    const skillsDir = path.join(projectDir, 'skills');
    const dirs = await fs.readdir(skillsDir, { withFileTypes: true });

    const skills = [];

    for (const dirent of dirs) {
      if (dirent.isDirectory()) {
        const skillFile = path.join(skillsDir, dirent.name, 'SKILL.md');
        try {
          await fs.access(skillFile);
          skills.push({
            name: dirent.name,
            dir: dirent.name
          });
        } catch {
          // Skill sem SKILL.md, ignorar
        }
      }
    }

    return skills;
  } catch {
    return [];
  }
}

/**
 * Descobre hooks ativos em settings.json
 */
async function discoverHooks(projectDir) {
  try {
    const settingsPath = path.join(projectDir, '.claude', 'settings.json');
    const content = await fs.readFile(settingsPath, 'utf8');
    const settings = JSON.parse(content);

    const hooks = [];

    if (settings.hooks && settings.hooks.UserPromptSubmit) {
      for (const entry of settings.hooks.UserPromptSubmit) {
        if (entry.hooks) {
          for (const h of entry.hooks) {
            const cmd = h.command;
            // Extrair nome do arquivo do comando
            // Ex: "node .claude/hooks/session-context-hybrid.js" -> "session-context-hybrid"
            const match = cmd.match(/([^\/\\]+)\.js/);
            if (match) {
              hooks.push({
                name: match[1],
                command: cmd
              });
            }
          }
        }
      }
    }

    return hooks;
  } catch {
    return [];
  }
}

/**
 * Lê status de execução dos hooks
 */
async function getHooksStatus(projectDir) {
  try {
    const statusFile = path.join(projectDir, '.claude', 'statusline', 'hooks-status.json');
    const content = await fs.readFile(statusFile, 'utf8');
    return JSON.parse(content);
  } catch {
    return {};
  }
}

/**
 * Lê agentes ativos
 */
async function getActiveAgents(projectDir) {
  try {
    const activeFile = path.join(projectDir, '.claude', 'statusline', 'active-agents.json');
    const content = await fs.readFile(activeFile, 'utf8');
    const data = JSON.parse(content);
    return data.activeAgents || [];
  } catch {
    return [];
  }
}

/**
 * Lê vocabulário aprendido do usuário
 */
async function getUserVocabulary(projectDir) {
  try {
    const vocabFile = path.join(projectDir, '.claude', 'hooks', 'lib', 'user-vocabulary.json');
    const content = await fs.readFile(vocabFile, 'utf8');
    return JSON.parse(content);
  } catch {
    return { terms: {}, customPatterns: [] };
  }
}

/**
 * Lê confidence dos patterns
 */
async function getPatternConfidence(projectDir) {
  try {
    const confidenceFile = path.join(projectDir, '.claude', 'hooks', 'lib', 'pattern-confidence.json');
    const content = await fs.readFile(confidenceFile, 'utf8');
    return JSON.parse(content);
  } catch {
    return { patterns: {} };
  }
}

/**
 * Lê métricas de qualidade de prompts
 */
async function getPromptQuality(projectDir) {
  try {
    const qualityFile = path.join(projectDir, '.claude', 'statusline', 'prompt-quality.json');
    const content = await fs.readFile(qualityFile, 'utf8');
    return JSON.parse(content);
  } catch {
    return null;
  }
}

/**
 * Gera statusline formatado
 */
function generateStatusline(claudeData, projectData) {
  const { workspace, model, git, tokens, cost } = claudeData;
  const { agents, skills, hooks, hooksStatus, activeAgents, promptQuality, vocabulary, confidence } = projectData;

  const lines = [];

  // Linha 1: Cabeçalho com informações principais
  lines.push(generateHeader(model, workspace, git, cost, tokens));

  // Linha 2: Contadores de sistema
  lines.push(generateSystemInfo(agents, skills, hooks, hooksStatus, activeAgents));

  // Linha 3: Prompt Enhancer status (se disponível)
  const enhancerInfo = generatePromptEnhancerStatus(promptQuality, vocabulary, confidence);
  if (enhancerInfo) {
    lines.push(enhancerInfo);
  }

  // Linha 4: Status do Legal-Braniac (se disponível)
  const brainiacInfo = generateBrainiacStatus(hooksStatus);
  if (brainiacInfo) {
    lines.push(brainiacInfo);
  }

  return lines.join('\n');
}

/**
 * Gera cabeçalho principal
 */
function generateHeader(model, workspace, git, cost, tokens) {
  const modelName = model?.display_name ? model.display_name.replace('claude-', '').replace('sonnet-', 'snt-') : 'unknown';
  const dirName = workspace?.current_dir ? path.basename(workspace.current_dir) : 'unknown';
  const branch = git?.branch ? truncate(git.branch, 25) : 'no-git';
  const costUsd = cost?.total_usd ? `$${cost.total_usd.toFixed(2)}` : '$0.00';
  const totalTokens = tokens?.total ? formatTokens(tokens.total) : '0k';

  return `${colors.bold}${colors.cyan}🧠 LEGAL-BRANIAC${colors.reset} ` +
         `${colors.yellow}${modelName}${colors.reset} ${colors.dim}|${colors.reset} ` +
         `📂 ${colors.blue}${dirName}${colors.reset} ${colors.dim}|${colors.reset} ` +
         `🌿 ${colors.green}${branch}${colors.reset} ${colors.dim}|${colors.reset} ` +
         `💰 ${colors.magenta}${costUsd}${colors.reset} ${colors.dim}|${colors.reset} ` +
         `📊 ${colors.white}${totalTokens}${colors.reset}`;
}

/**
 * Gera informações de sistema
 */
function generateSystemInfo(agents, skills, hooks, hooksStatus, activeAgents) {
  const agentCount = agents.length;
  const skillCount = skills.length;
  const hookCount = hooks.length;

  // Contar hooks com sucesso/erro
  const hooksArray = Object.values(hooksStatus);
  const hooksSuccess = hooksArray.filter(h => h.status === 'success').length;
  const hooksError = hooksArray.filter(h => h.status === 'error').length;

  // Formatar agentes (com ativos se houver)
  let agentInfo = `🤖 ${colors.green}${agentCount}${colors.reset} agentes`;
  if (activeAgents && activeAgents.length > 0) {
    const activeNames = activeAgents.map(a => a.name).join(', ');
    agentInfo += ` ${colors.yellow}(${activeAgents.length} ativo${activeAgents.length > 1 ? 's' : ''}: ${activeNames})${colors.reset}`;
  }

  // Formatar hooks (com status se houver)
  let hookInfo = `🔧 ${colors.green}${hookCount}${colors.reset} hooks`;
  if (hooksArray.length > 0) {
    if (hooksError > 0) {
      hookInfo += ` ${colors.red}(${hooksError} ✗)${colors.reset}`;
    } else if (hooksSuccess === hooksArray.length) {
      hookInfo += ` ${colors.green}(all ✓)${colors.reset}`;
    } else {
      hookInfo += ` ${colors.yellow}(${hooksSuccess}/${hooksArray.length} ✓)${colors.reset}`;
    }
  }

  return `${colors.dim}├${colors.reset} ` +
         `${agentInfo} ${colors.dim}|${colors.reset} ` +
         `📦 ${colors.green}${skillCount}${colors.reset} skills ${colors.dim}|${colors.reset} ` +
         `${hookInfo}`;
}

/**
 * Gera status do Prompt Enhancer
 */
function generatePromptEnhancerStatus(qualityData, vocabulary, confidence) {
  if (!qualityData || !qualityData.stats) {
    return null;
  }

  const enabled = qualityData.enabled ? '●ON' : '○OFF';
  const enabledColor = qualityData.enabled ? colors.green : colors.dim;

  const avg = qualityData.stats.averageQuality || 0;
  const total = qualityData.stats.totalPrompts || 0;
  const enhanced = qualityData.stats.enhancedPrompts || 0;
  const rate = total > 0 ? Math.round((enhanced / total) * 100) : 0;

  // Learning metrics
  const termCount = Object.keys(vocabulary.terms || {}).length;
  const customPatterns = (vocabulary.customPatterns || []).length;

  // Calculate average confidence
  const patterns = Object.values(confidence.patterns || {});
  const avgConfidence = patterns.length > 0
    ? Math.round(patterns.reduce((sum, p) => sum + p.confidenceScore, 0) / patterns.length)
    : 100;

  // Color coding
  let qualityColor = colors.yellow;
  if (avg >= 70) qualityColor = colors.green;
  else if (avg < 40) qualityColor = colors.red;

  let confidenceColor = colors.yellow;
  if (avgConfidence >= 80) confidenceColor = colors.green;
  else if (avgConfidence < 60) confidenceColor = colors.red;

  return `${colors.dim}├${colors.reset} ` +
         `📝 Enhancer [${enabledColor}${enabled}${colors.reset}] ` +
         `Quality: ${qualityColor}${avg}/100${colors.reset} ${colors.dim}|${colors.reset} ` +
         `Enhanced: ${colors.cyan}${rate}%${colors.reset} ${colors.dim}(${enhanced}/${total})${colors.reset} ${colors.dim}|${colors.reset} ` +
         `📚 Learned: ${colors.magenta}${termCount}${colors.reset} terms ${colors.dim}|${colors.reset} ` +
         `Confidence: ${confidenceColor}${avgConfidence}%${colors.reset} ${colors.dim}|${colors.reset} ` +
         `${colors.dim}Manual: ${colors.yellow}++${colors.reset}`;
}

/**
 * Gera status do Legal-Braniac (orquestrador)
 */
function generateBrainiacStatus(hooksStatus) {
  const brainiacKey = 'invoke-legal-braniac-hybrid';

  if (!hooksStatus[brainiacKey]) {
    return null; // Não foi executado ainda
  }

  const status = hooksStatus[brainiacKey];
  const isSuccess = status.status === 'success';
  const statusIcon = isSuccess ? '✅' : '❌';
  const statusColor = isSuccess ? colors.green : colors.red;

  // Formatar tempo desde última execução
  let timeAgo = '';
  if (status.timestamp) {
    const secondsAgo = Math.floor((Date.now() - status.timestamp) / 1000);
    if (secondsAgo < 60) {
      timeAgo = `${secondsAgo}s`;
    } else if (secondsAgo < 3600) {
      timeAgo = `${Math.floor(secondsAgo / 60)}m`;
    } else {
      timeAgo = `${Math.floor(secondsAgo / 3600)}h`;
    }
  }

  let line = `${colors.dim}└${colors.reset} ` +
             `${statusIcon} ${colors.bold}LEGAL-BRANIAC${colors.reset} ` +
             `${statusColor}${status.status}${colors.reset}`;

  if (timeAgo) {
    line += ` ${colors.dim}(${timeAgo} ago)${colors.reset}`;
  }

  // Adicionar mensagem de erro se houver
  if (!isSuccess && status.error) {
    const errorMsg = truncate(status.error, 50);
    line += ` ${colors.red}- ${errorMsg}${colors.reset}`;
  }

  return line;
}

/**
 * Formata número de tokens
 */
function formatTokens(total) {
  if (total >= 1000000) {
    return `${(total / 1000000).toFixed(1)}M`;
  } else if (total >= 1000) {
    return `${Math.floor(total / 1000)}k`;
  }
  return total.toString();
}

/**
 * Trunca string se necessário
 */
function truncate(str, maxLen) {
  if (str.length <= maxLen) {
    return str;
  }
  return str.substring(0, maxLen - 3) + '...';
}

/**
 * Lê stdin completo
 */
async function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => data += chunk);
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', reject);
  });
}

// Executar
main().catch(err => {
  console.error(`${colors.red}Error:${colors.reset}`, err.message);
  process.exit(1);
});
