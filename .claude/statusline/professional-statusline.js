#!/usr/bin/env node
// professional-statusline.js - Statusline profissional para Claude Code
//
// Layout de 3 linhas:
// 1. Context & Active Tasks (venv, git, hooks, skills)
// 2. VibbinLoggin + MCP
// 3. Session Metrics (duration, cost, context %)

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Importar módulos
const { colors, colorize, separator } = require('./lib/color-palette');
const spinner = require('./lib/liquid-spinner');
const skillsTracker = require('./lib/skills-tracker');
const vibeIntegration = require('./lib/vibe-integration');
const mcpMonitor = require('./lib/mcp-monitor');

// ============================================================================
// LINHA 1: Context & Active Tasks
// ============================================================================

function getVenvStatus() {
  const venv = process.env.VIRTUAL_ENV;
  if (venv) {
    const venvName = path.basename(venv);
    return colorize(`📦 Python: ${venvName}`, 'cyan');
  }
  return colorize('📦 Python: no venv', 'gray');
}

function getGitStatus() {
  try {
    const branch = execSync('git branch --show-current 2>/dev/null', {
      encoding: 'utf8',
      timeout: 100
    }).trim();

    if (!branch) return null;

    // Verificar se há mudanças
    const status = execSync('git status --porcelain 2>/dev/null', {
      encoding: 'utf8',
      timeout: 100
    }).trim();

    const hasChanges = status.length > 0;
    const statusIcon = hasChanges ? '±' : '✓';
    const statusColor = hasChanges ? 'yellow' : 'green';

    return `${colorize('🌿 Git:', 'gray')} ${colorize(branch, 'cyan')} ${colorize(statusIcon, statusColor)}`;
  } catch {
    return null;
  }
}

function getLegalBraniacStatus() {
  // Verificar se legal-braniac está orquestrando
  const braniacMarker = path.join(
    process.cwd(),
    '.claude/legal-braniac-active.json'
  );

  try {
    if (fs.existsSync(braniacMarker)) {
      const data = JSON.parse(fs.readFileSync(braniacMarker, 'utf8'));
      const age = Date.now() - (data.timestamp || 0);

      // Considerar ativo se < 30 segundos
      if (age < 30000) {
        const frame = spinner.getCurrentFrame();
        const action = data.action || 'orchestrating';
        return `${colorize('🧠 Legal-Braniac:', 'purple')} ${colorize(frame + ' ' + action, 'purple')} ${colorize('(ACTIVE)', 'green', 'bold')}`;
      }
    }
  } catch {}

  return null;  // Não mostrar se não ativo
}

function getHooksStatus() {
  // Verificar se há hooks rodando (via marker file)
  const hooksStatusFile = path.join(
    process.env.HOME || '/home/cmr-auto',
    '.claude/statusline/hooks-status.json'
  );

  try {
    if (fs.existsSync(hooksStatusFile)) {
      const data = JSON.parse(fs.readFileSync(hooksStatusFile, 'utf8'));
      if (data.status === 'running' && data.hooks && data.hooks.length > 0) {
        const frame = spinner.getCurrentFrame();
        const hookName = data.hooks[0].replace('.js', '').replace(/-/g, ' ');
        return `${colorize('⚡ Hooks:', 'gray')} ${colorize(frame + ' ' + hookName, 'blue')}`;
      }
    }
  } catch {}

  // Idle
  return colorize('⚡ Hooks: idle', 'gray');
}

function getSkillsStatus() {
  const total = skillsTracker.getTotalCount();
  const active = skillsTracker.getActiveCount();

  if (total === 0) {
    return colorize('✨ Skills: none installed', 'gray');
  }

  if (active > 0) {
    return `${colorize('✨ Skills:', 'gray')} ${colorize(`${active}/${total} active`, 'blue')}`;
  }

  return `${colorize('✨ Skills:', 'gray')} ${colorize(`${total} available`, 'blue')}`;
}

// Helper para padding de texto (alinhamento)
function padRight(text, width) {
  // Remove ANSI codes para calcular largura real
  const stripped = text.replace(/\x1b\[[0-9;]*m/g, '');
  const actualLength = stripped.length;
  const padding = Math.max(0, width - actualLength);
  return text + ' '.repeat(padding);
}

function line1() {
  // DESTAQUE: Legal-Braniac (se ativo, aparece PRIMEIRO)
  const braniacStatus = getLegalBraniacStatus();

  // Coluna esquerda: informações principais
  const gitStatus = getGitStatus();
  const hooksStatus = getHooksStatus();
  const skillsStatus = getSkillsStatus();

  const leftParts = [gitStatus, hooksStatus, skillsStatus].filter(Boolean);

  // Se legal-braniac ativo, adicionar no início
  if (braniacStatus) {
    leftParts.unshift(braniacStatus);
  }

  const leftColumn = leftParts.join(` ${separator()} `);

  // Coluna direita: contexto
  const venvStatus = getVenvStatus();
  const rightColumn = venvStatus;

  // Calcular largura do terminal
  const termWidth = getTerminalWidth();
  const dividerPos = Math.floor(termWidth * 0.70);  // 70% para esquerda

  // Alinhar
  const paddedLeft = padRight(leftColumn, dividerPos - 3);
  return `${paddedLeft} ${colorize('┃', 'gray')} ${rightColumn}`;
}

// ============================================================================
// LINHA 2: VibbinLoggin
// ============================================================================

function getVibeStatus() {
  // Nova integração - lê de ~/.vibe-log/analyzed-prompts/
  return vibeIntegration.getVibeLoggingMetrics();
}

function getMCPStatus() {
  if (!mcpMonitor.isAvailable()) {
    return `${colorize('🔌 MCP Servers:', 'gray')} ${colorize('not configured', 'gray')}`;
  }

  const servers = mcpMonitor.getServers();
  if (servers.length === 0) {
    return `${colorize('🔌 MCP Servers:', 'gray')} ${colorize('none', 'gray')}`;
  }

  const statuses = mcpMonitor.getServerStatuses();
  const healthy = Object.values(statuses).filter(Boolean).length;
  const total = servers.length;

  if (healthy === total) {
    const serverList = servers.join(', ');
    return `${colorize('🔌 MCP Servers:', 'blue')} ${colorize(`${total} active`, 'green')} ${colorize('(' + serverList + ')', 'gray')}`;
  } else {
    return `${colorize('🔌 MCP Servers:', 'blue')} ${colorize(`${healthy}/${total} active`, 'yellow')}`;
  }
}

function getAgentsStatus() {
  // Detectar agentes disponíveis
  const agentsDir = path.join(process.cwd(), 'agentes');

  try {
    if (!fs.existsSync(agentsDir)) {
      return `${colorize('🦾 Agents:', 'gray')} ${colorize('none', 'gray')}`;
    }

    const agents = fs.readdirSync(agentsDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);

    if (agents.length === 0) {
      return `${colorize('🦾 Agents:', 'gray')} ${colorize('none', 'gray')}`;
    }

    // TODO: Detectar agentes em execução via process table ou marker files
    const activeAgents = 0;  // Placeholder

    if (activeAgents > 0) {
      return `${colorize('🦾 Agents:', 'blue')} ${colorize(`${activeAgents}/${agents.length} running`, 'green')}`;
    }

    return `${colorize('🦾 Agents:', 'blue')} ${colorize(`${agents.length} available`, 'cyan')}`;
  } catch {
    return `${colorize('🦾 Agents:', 'gray')} ${colorize('error detecting', 'gray')}`;
  }
}

function line2() {
  // Coluna esquerda: VibbinLoggin, Agents
  const vibeStatus = getVibeStatus();
  const agentsStatus = getAgentsStatus();

  const leftColumn = [vibeStatus, agentsStatus].filter(Boolean).join(` ${separator()} `);

  // Coluna direita: Session duration
  const duration = getSessionDuration();
  const rightColumn = `${colorize('⏱ Session:', 'gray')} ${colorize(duration, 'cyan')}`;

  // Alinhar
  const termWidth = getTerminalWidth();
  const dividerPos = Math.floor(termWidth * 0.70);
  const paddedLeft = padRight(leftColumn, dividerPos - 3);

  return `${paddedLeft} ${colorize('┃', 'gray')} ${rightColumn}`;
}

// ============================================================================
// LINHA 3: Session Metrics
// ============================================================================

function getSessionDuration() {
  // Tentar ler do session file do Claude Code
  const sessionFile = path.join(
    process.env.HOME || '/home/cmr-auto',
    '.claude/statusline/session-start.json'
  );

  try {
    if (fs.existsSync(sessionFile)) {
      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
      const startTime = data.timestamp || Date.now();
      const elapsed = Date.now() - startTime;

      const hours = Math.floor(elapsed / (1000 * 60 * 60));
      const minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 0) {
        return `${hours}h${minutes.toString().padStart(2, '0')}m`;
      } else {
        return `${minutes}m`;
      }
    }
  } catch {}

  return '0m';
}

function getTokenCost() {
  // TODO: Implementar leitura real de token usage
  // Por ora, retornar placeholder
  return 0.00;
}

function getContextPercentage() {
  // Calcular % de contexto usado DINAMICAMENTE
  // Claude Code tem limite de ~200k tokens de contexto
  const CONTEXT_LIMIT = 200000;

  try {
    // Estratégia 1: Ler de system-reminder se disponível
    const process_env_token_usage = process.env.CLAUDE_TOKEN_USAGE;
    if (process_env_token_usage) {
      const used = parseInt(process_env_token_usage);
      return Math.min(100, Math.round((used / CONTEXT_LIMIT) * 100));
    }

    // Estratégia 2: Estimar baseado em arquivos lidos recentemente
    // Ler diretório de cache do Claude Code (se existir)
    const cacheDir = path.join(
      process.env.HOME || '/home/cmr-auto',
      '.cache/claude-code'
    );

    if (fs.existsSync(cacheDir)) {
      const files = fs.readdirSync(cacheDir);
      // Heurística: cada arquivo de cache ≈ 5k tokens
      const estimatedTokens = files.length * 5000;
      return Math.min(100, Math.round((estimatedTokens / CONTEXT_LIMIT) * 100));
    }

    // Estratégia 3: Estimar baseado em timestamp da sessão
    const sessionFile = path.join(
      process.env.HOME || '/home/cmr-auto',
      '.claude/statusline/session-start.json'
    );

    if (fs.existsSync(sessionFile)) {
      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
      const elapsed = Date.now() - (data.timestamp || Date.now());
      const hours = elapsed / (1000 * 60 * 60);

      // Heurística: ~15k tokens/hora de conversa ativa
      const estimatedTokens = Math.floor(hours * 15000);
      return Math.min(100, Math.round((estimatedTokens / CONTEXT_LIMIT) * 100));
    }

    // Fallback: 0%
    return 0;
  } catch {
    return 0;
  }
}

function line3() {
  // Linha 3 simplificada: apenas Context % na direita
  const contextPct = getContextPercentage();

  // Contexto % (com cor baseada em uso)
  let contextColor = 'green';
  if (contextPct > 80) contextColor = 'red';
  else if (contextPct > 60) contextColor = 'yellow';

  // Coluna esquerda: vazia (ou pode adicionar outras métricas no futuro)
  const leftColumn = '';

  // Coluna direita: Context %
  const rightColumn = `${colorize('🧠 Context:', 'gray')} ${colorize(contextPct + '%', contextColor)}`;

  // Alinhar
  const termWidth = getTerminalWidth();
  const dividerPos = Math.floor(termWidth * 0.70);
  const paddedLeft = padRight(leftColumn, dividerPos - 3);

  return `${paddedLeft} ${colorize('┃', 'gray')} ${rightColumn}`;
}

// ============================================================================
// SEPARADORES VISUAIS
// ============================================================================

// Obter largura do terminal (padrão: 80)
function getTerminalWidth() {
  try {
    return process.stdout.columns || 80;
  } catch {
    return 80;
  }
}

// Opção 1: Linhas horizontais finas entre cada linha
function separator_style_1() {
  const width = getTerminalWidth();
  return colorize('─'.repeat(width), 'gray');
}

// Opção 2: Linha central mais destacada
function separator_style_2() {
  const width = getTerminalWidth();
  return colorize('━'.repeat(width), 'cyan');
}

// Opção 3: Box completo com bordas
function box_top() {
  const width = getTerminalWidth() - 2;
  return colorize('╭' + '─'.repeat(width) + '╮', 'cyan');
}

function box_middle() {
  const width = getTerminalWidth() - 2;
  return colorize('├' + '─'.repeat(width) + '┤', 'gray');
}

function box_bottom() {
  const width = getTerminalWidth() - 2;
  return colorize('╰' + '─'.repeat(width) + '╯', 'cyan');
}

function wrap_in_box(text) {
  return `${colorize('│', 'cyan')} ${text} ${colorize('│', 'cyan')}`;
}

// ============================================================================
// MAIN
// ============================================================================

function main() {
  try {
    const l1 = line1();
    const l2 = line2();
    const l3 = line3();

    // ESCOLHA DE ESTILO (pode trocar facilmente)
    const STYLE = 'clean_separators';  // Options: 'clean_separators', 'bold_middle', 'full_box'

    if (STYLE === 'clean_separators') {
      // Estilo 1: Linhas finas entre cada linha
      console.log(separator_style_1());
      console.log(l1);
      console.log(separator_style_1());
      console.log(l2);
      console.log(separator_style_1());
      console.log(l3);
      console.log(separator_style_1());
    } else if (STYLE === 'bold_middle') {
      // Estilo 2: Apenas linha central destacada
      console.log(l1);
      console.log(separator_style_2());
      console.log(l2);
      console.log(l3);
    } else if (STYLE === 'full_box') {
      // Estilo 3: Box completo com bordas
      console.log(box_top());
      console.log(wrap_in_box(l1));
      console.log(box_middle());
      console.log(wrap_in_box(l2));
      console.log(box_middle());
      console.log(wrap_in_box(l3));
      console.log(box_bottom());
    }
  } catch (err) {
    // Fallback: output mínimo
    console.error('Statusline error:', err.message);
    console.log(colorize('⚡ statusline error', 'red'));
  }
}

main();
