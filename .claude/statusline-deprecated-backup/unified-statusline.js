#!/usr/bin/env node

// unified-statusline.js - Professional 3-line statusline
//
// Architecture:
// - Line 1 (bg_primary): System Status (Git, Venv, Legal-Braniac, Hooks, Skills)
// - Line 2 (bg_secondary): Metrics (Vibe score, Agents, MCP, Duration, Cost)
// - Line 3 (bg_accent): Coaching + Context/Tokens
//
// Responsive modes:
// - < 80 cols: Minimal (1 line per section)
// - 80-120: Compact (2 lines L1/L2)
// - 120-160: Comfortable (full design)
// - > 160: Wide (longer coaching)
//
// Performance target: < 100ms

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Import libraries
const { PALETTE, colorize, bg, reset, separator, stripAnsi, visibleLength } = require('./lib/color-palette-v2');
const vibeIntegration = require('./lib/vibe-integration');
const skillsTracker = require('./lib/skills-tracker');
const mcpMonitor = require('./lib/mcp-monitor');

// Project root detection (go up 2 levels from .claude/statusline)
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

// ============================================================================
// LAYOUT CALCULATION (Responsive)
// ============================================================================

/**
 * Calculate layout based on terminal width
 * @param {number} termWidth - Terminal width in columns
 * @returns {object} - Layout configuration
 */
function calculateLayout(termWidth) {
  if (termWidth < 80) {
    return { mode: 'minimal', width: termWidth };
  }

  if (termWidth < 120) {
    return { mode: 'compact', width: termWidth, col1: 70, col2: termWidth - 73 };
  }

  // Comfortable and wide modes: 70/30 split
  const col1Width = Math.floor(termWidth * 0.70) - 2;
  const col2Width = termWidth - col1Width - 3; // 3 = separator + padding

  const mode = termWidth > 160 ? 'wide' : 'comfortable';

  return { mode, width: termWidth, col1: col1Width, col2: col2Width };
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Pad two columns to align separator
 * @param {string} col1Text - Left column text (with ANSI codes)
 * @param {string} col2Text - Right column text (with ANSI codes)
 * @param {number} col1Width - Target width for left column (visible chars)
 * @param {number} col2Width - Target width for right column (visible chars)
 * @returns {string} - Formatted line with separator
 */
function padColumns(col1Text, col2Text, col1Width, col2Width) {
  const col1Length = visibleLength(col1Text);
  const col2Length = visibleLength(col2Text);

  const padding = ' '.repeat(Math.max(0, col1Width - col1Length));
  const sep = colorize(' │ ', 'fg_tertiary');

  return col1Text + padding + sep + col2Text;
}

/**
 * Format separator line
 * @param {number} width - Terminal width
 * @returns {string} - Separator line
 */
function formatSeparator(width) {
  return separator('╌', width);
}

/**
 * Truncate text to max length (respecting ANSI codes)
 * @param {string} text - Text to truncate
 * @param {number} maxLen - Maximum visible length
 * @returns {string} - Truncated text with "..." if needed
 */
function truncate(text, maxLen) {
  const visible = stripAnsi(text);
  if (visible.length <= maxLen) {
    return text;
  }

  // Truncate and add ellipsis
  return visible.substring(0, maxLen - 3) + '...';
}

// ============================================================================
// DATA FETCHERS
// ============================================================================

/**
 * Get git status (branch, clean/dirty)
 */
function getGitStatus() {
  try {
    const branch = execSync('git rev-parse --abbrev-ref HEAD', {
      cwd: PROJECT_ROOT,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
      timeout: 500
    }).trim();

    const status = execSync('git status --porcelain', {
      cwd: PROJECT_ROOT,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
      timeout: 500
    }).trim();

    const isDirty = status.length > 0;

    return { branch, isDirty };
  } catch (error) {
    return { branch: 'unknown', isDirty: false };
  }
}

/**
 * Get venv status (active/inactive)
 */
function getVenvStatus() {
  // Check if VIRTUAL_ENV is set
  if (process.env.VIRTUAL_ENV) {
    return { active: true, name: path.basename(process.env.VIRTUAL_ENV) };
  }

  return { active: false, name: null };
}

/**
 * Get Legal-Braniac status
 */
function getLegalBraniacStatus() {
  const statusFile = path.join(PROJECT_ROOT, '.claude/legal-braniac-session.json');

  try {
    if (!fs.existsSync(statusFile)) {
      return { active: false, task: null };
    }

    const content = fs.readFileSync(statusFile, 'utf8');
    const data = JSON.parse(content);

    // Check if data is stale (> 10 minutes)
    const age = Date.now() - (data.timestamp || 0);
    if (age > 10 * 60 * 1000) {
      return { active: false, task: null };
    }

    return {
      active: true,
      task: data.current_task || 'orchestrating'
    };
  } catch (error) {
    return { active: false, task: null };
  }
}

/**
 * Get hooks status
 */
function getHooksStatus() {
  const hooksDir = path.join(PROJECT_ROOT, '.claude/hooks');

  try {
    if (!fs.existsSync(hooksDir)) {
      return { total: 0, ok: 0 };
    }

    const hookFiles = fs.readdirSync(hooksDir)
      .filter(f => (f.endsWith('.js') || f.endsWith('.sh')) && !f.startsWith('test-'));

    // For now, assume all hooks are OK (no validation)
    // Future: implement hook validation via hooks-status.json
    return { total: hookFiles.length, ok: hookFiles.length };
  } catch (error) {
    return { total: 0, ok: 0 };
  }
}

/**
 * Get agents count
 */
function getAgentsCount() {
  const agentsDir = path.join(PROJECT_ROOT, '.claude/agents');

  try {
    if (!fs.existsSync(agentsDir)) {
      return 0;
    }

    const agentFiles = fs.readdirSync(agentsDir)
      .filter(f => f.endsWith('.md'));

    return agentFiles.length;
  } catch (error) {
    return 0;
  }
}

/**
 * Estimate cost based on token usage
 * @param {number} tokensUsed - Tokens used in session
 * @returns {string} - Formatted cost (e.g., "$0.45")
 */
function estimateCost(tokensUsed) {
  // Claude Sonnet 4.5 pricing (approximate)
  // Input: $3 / 1M tokens, Output: $15 / 1M tokens
  // Assume 50/50 split for estimation
  const avgCostPerMToken = (3 + 15) / 2; // $9 per 1M tokens
  const cost = (tokensUsed / 1000000) * avgCostPerMToken;

  if (cost < 0.01) {
    return '$0.00';
  }

  return `$${cost.toFixed(2)}`;
}

/**
 * Estimate context usage percentage
 * @returns {number} - Percentage (0-100)
 */
function estimateContext() {
  // Simple heuristic: based on session duration
  // Longer sessions = higher context usage
  const duration = vibeIntegration.getSessionDuration();

  if (!duration) {
    return 0;
  }

  // Extract hours/minutes
  const match = duration.match(/(\d+)h(\d+)m|(\d+)m/);
  if (!match) {
    return 0;
  }

  const hours = parseInt(match[1] || 0);
  const minutes = parseInt(match[2] || match[3] || 0);
  const totalMinutes = hours * 60 + minutes;

  // Assume linear growth: 0% at 0 min, 100% at 120 min (2 hours)
  const percentage = Math.min(100, Math.round((totalMinutes / 120) * 100));

  return percentage;
}

// ============================================================================
// LINE FORMATTERS (Full mode - Comfortable/Wide)
// ============================================================================

/**
 * Format Line 1: System Status
 * Layout: 70/30 split, 2 rows
 * - Row 1: Legal-Braniac, Hooks | Python venv
 * - Row 2: Git, Skills |
 */
function formatLine1(layout) {
  const { mode, col1, col2 } = layout;

  // Get data
  const gitStatus = getGitStatus();
  const venvStatus = getVenvStatus();
  const braniacStatus = getLegalBraniacStatus();
  const hooksStatus = getHooksStatus();
  const skillsCount = skillsTracker.getFormattedCount();

  // Build components
  const braniacEmoji = braniacStatus.active ? '🧠' : '💤';
  const braniacText = braniacStatus.active
    ? colorize(`Legal-Braniac: ${braniacStatus.task}`, 'info')
    : colorize('Legal-Braniac: idle', 'fg_secondary');

  const hooksText = hooksStatus.ok === hooksStatus.total
    ? colorize(`⚡ Hooks: ${hooksStatus.ok} ok`, 'success')
    : colorize(`⚡ Hooks: ${hooksStatus.ok}/${hooksStatus.total}`, 'warning');

  const venvText = venvStatus.active
    ? colorize(`📦 Python: ${venvStatus.name}`, 'success')
    : colorize('📦 Python: no venv', 'warning');

  const gitEmoji = gitStatus.isDirty ? '🌿' : '🌿';
  const gitText = gitStatus.isDirty
    ? colorize(`Git: ${gitStatus.branch} ●`, 'warning')
    : colorize(`Git: ${gitStatus.branch} ✓`, 'success');

  const skillsText = colorize(`✨ Skills: ${skillsCount}`, 'info');

  // Row 1
  const row1Col1 = `${braniacEmoji} ${braniacText}  ${hooksText}`;
  const row1Col2 = venvText;
  const row1 = padColumns(row1Col1, row1Col2, col1, col2);

  // Row 2
  const row2Col1 = `${gitEmoji} ${gitText}                   ${skillsText}`;
  const row2Col2 = '';
  const row2 = padColumns(row2Col1, row2Col2, col1, col2);

  // Apply background and return
  const bgCode = bg('bg_primary');
  const resetCode = reset();

  return bgCode + row1 + ' '.repeat(Math.max(0, layout.width - visibleLength(row1))) + resetCode + '\n' +
         bgCode + row2 + ' '.repeat(Math.max(0, layout.width - visibleLength(row2))) + resetCode;
}

/**
 * Format Line 2: Metrics
 * Layout: 70/30 split, 2 rows
 * - Row 1: Vibe score | Duration
 * - Row 2: Agents, MCP | Cost
 */
function formatLine2(layout) {
  const { mode, col1, col2 } = layout;

  // Get data
  const vibeScore = vibeIntegration.getVibeScore();
  const agentsCount = getAgentsCount();
  const mcpStatus = mcpMonitor.getFormattedStatus();
  const sessionDuration = vibeIntegration.getSessionDuration();
  const tokenUsage = vibeIntegration.getTokenUsage();

  // Build components
  let vibeText;
  if (!vibeScore) {
    vibeText = colorize('💫 Vibe: not configured', 'fg_secondary');
  } else if (vibeScore.state === 'loading') {
    vibeText = colorize(`⏳ Vibe: ${vibeScore.message}`, 'info');
  } else {
    const scoreColor = vibeScore.score >= 80 ? 'success' : vibeScore.score >= 60 ? 'info' : 'warning';
    vibeText = colorize(`${vibeScore.emoji} Vibe: ${vibeScore.score}/100`, scoreColor) + ' ' +
               colorize(truncate(vibeScore.suggestion, 30), 'fg_secondary');
  }

  const agentsText = colorize(`🦾 Agents: ${agentsCount} available`, 'info');

  const mcpText = mcpStatus
    ? colorize(`🔌 MCP: ${mcpStatus}`, 'info')
    : colorize('🔌 MCP: not configured', 'fg_secondary');

  const durationText = sessionDuration
    ? colorize(`⏱ ${sessionDuration}`, 'fg_primary')
    : colorize('⏱ --', 'fg_secondary');

  const costText = tokenUsage
    ? colorize(`💰 ${estimateCost(tokenUsage.used)}`, 'fg_primary')
    : colorize('💰 $0.00', 'fg_secondary');

  // Row 1
  const row1Col1 = vibeText;
  const row1Col2 = durationText;
  const row1 = padColumns(row1Col1, row1Col2, col1, col2);

  // Row 2
  const row2Col1 = `${agentsText}                            ${mcpText}`;
  const row2Col2 = costText;
  const row2 = padColumns(row2Col1, row2Col2, col1, col2);

  // Apply background and return
  const bgCode = bg('bg_secondary');
  const resetCode = reset();

  return bgCode + row1 + ' '.repeat(Math.max(0, layout.width - visibleLength(row1))) + resetCode + '\n' +
         bgCode + row2 + ' '.repeat(Math.max(0, layout.width - visibleLength(row2))) + resetCode;
}

/**
 * Format Line 3: Coaching + Context/Tokens
 * Layout: 100% width, 2 rows
 * - Row 1: Gordon coaching message
 * - Row 2: Context percentage, Tokens
 */
function formatLine3(layout) {
  const { mode, width } = layout;

  // Get data
  const coaching = vibeIntegration.getCoachingSuggestion();
  const contextPercent = estimateContext();
  const tokenUsage = vibeIntegration.getTokenUsage();

  // Build components
  const coachingText = colorize(truncate(coaching, width - 4), 'gordon');

  const contextText = colorize(`🧠 Context: ${contextPercent}%`, 'fg_primary');

  let tokensText;
  if (tokenUsage) {
    const tokensK = Math.round(tokenUsage.used / 1000);
    const totalK = Math.round(tokenUsage.total / 1000);
    tokensText = colorize(`📊 Tokens: ${tokensK}k/${totalK}k (${tokenUsage.percentage}%)`, 'fg_primary');
  } else {
    tokensText = colorize('📊 Tokens: --', 'fg_secondary');
  }

  // Row 1
  const row1 = coachingText;

  // Row 2
  const row2 = `${contextText}  ${colorize('│', 'fg_tertiary')}  ${tokensText}`;

  // Apply background and return
  const bgCode = bg('bg_accent');
  const resetCode = reset();

  return bgCode + row1 + ' '.repeat(Math.max(0, width - visibleLength(row1))) + resetCode + '\n' +
         bgCode + row2 + ' '.repeat(Math.max(0, width - visibleLength(row2))) + resetCode;
}

// ============================================================================
// MINIMAL/COMPACT MODES
// ============================================================================

/**
 * Format Line 1 (Minimal mode - single line)
 */
function formatLine1Minimal() {
  const gitStatus = getGitStatus();
  const venvStatus = getVenvStatus();
  const braniacStatus = getLegalBraniacStatus();

  const braniacIcon = braniacStatus.active ? '🧠' : '💤';
  const gitIcon = gitStatus.isDirty ? '●' : '✓';
  const venvIcon = venvStatus.active ? '✓' : '✗';

  const text = `${braniacIcon}: ${braniacStatus.task || 'idle'} │ 🌿: ${gitStatus.branch} ${gitIcon} │ 📦: ${venvIcon}`;

  return bg('bg_primary') + colorize(text, 'fg_primary') + reset();
}

/**
 * Format Line 2 (Minimal mode - single line)
 */
function formatLine2Minimal() {
  const vibeScore = vibeIntegration.getVibeScore();
  const agentsCount = getAgentsCount();

  const vibeText = vibeScore ? `${vibeScore.emoji} ${vibeScore.score}` : '💫 --';
  const text = `${vibeText} │ 🦾: ${agentsCount} │ ⏱: ${vibeIntegration.getSessionDuration() || '--'}`;

  return bg('bg_secondary') + colorize(text, 'fg_primary') + reset();
}

/**
 * Format Line 3 (Minimal mode - single line)
 */
function formatLine3Minimal() {
  const coaching = vibeIntegration.getCoachingSuggestion();
  const text = truncate(coaching, 70);

  return bg('bg_accent') + colorize(text, 'gordon') + reset();
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

function main() {
  const termWidth = process.stdout.columns || 120;
  const layout = calculateLayout(termWidth);

  let line1, sep1, line2, sep2, line3;

  if (layout.mode === 'minimal') {
    line1 = formatLine1Minimal();
    sep1 = formatSeparator(layout.width);
    line2 = formatLine2Minimal();
    sep2 = formatSeparator(layout.width);
    line3 = formatLine3Minimal();
  } else {
    // Comfortable, compact, wide modes use same formatters
    line1 = formatLine1(layout);
    sep1 = formatSeparator(layout.width);
    line2 = formatLine2(layout);
    sep2 = formatSeparator(layout.width);
    line3 = formatLine3(layout);
  }

  console.log(line1);
  console.log(sep1);
  console.log(line2);
  console.log(sep2);
  console.log(line3);
}

// ============================================================================
// BENCHMARK MODE
// ============================================================================

function benchmark() {
  const start = Date.now();
  main();
  const end = Date.now();
  console.error(`\nExecution time: ${end - start}ms`);
}

if (process.argv.includes('--benchmark')) {
  benchmark();
} else {
  main();
}
