#!/usr/bin/env node
/**
 * Professional Statusline - Horizontal layout with colors
 *
 * Layout: [LEFT aligned info] ────────── [RIGHT aligned info]
 *
 * LEFT:  ▸ Gordon | Legal-Braniac (●) | Session: 1h23m
 * RIGHT: 7 agents | 38 skills | 4 hooks | venv: ● | git: main*
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ANSI colors (works in all terminals)
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',

  // Foreground colors
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  gray: '\x1b[90m',

  // Background colors
  bgRed: '\x1b[41m',
  bgGreen: '\x1b[42m',
  bgYellow: '\x1b[43m',
  bgBlue: '\x1b[44m',
};

// Bash spinner frames
const spinnerFrames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

/**
 * Get current spinner frame based on timestamp
 */
function getSpinner() {
  const frame = Math.floor(Date.now() / 100) % spinnerFrames.length;
  return spinnerFrames[frame];
}

/**
 * Get vibe-log statusline (Gordon coaching)
 */
function getVibeLogLine() {
  try {
    const output = execSync('npx vibe-log-cli statusline --format compact', {
      encoding: 'utf8',
      timeout: 3000,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // Remove emojis
    let cleaned = output.replace(/[\u{1F300}-\u{1F9FF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F900}-\u{1F9FF}\u{1FA70}-\u{1FAFF}]/gu, '');
    cleaned = cleaned.replace(/\s+/g, ' ').trim();

    return cleaned || 'Gordon is analyzing your prompts...';
  } catch (error) {
    return 'Gordon is ready';
  }
}

/**
 * Get legal-braniac status with last-used indicator
 */
function getLegalBraniacStatus() {
  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const sessionFile = path.join(projectDir, '.claude', 'hooks', 'legal-braniac-session.json');
    const statusFile = path.join(projectDir, '.claude', 'statusline', 'hooks-status.json');

    let status = '○'; // Default: inactive
    let lastUsed = '';
    let isActive = false;

    // Check if session loaded
    if (fs.existsSync(sessionFile)) {
      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
      if (data.agents && data.agents.available && data.agents.available.length > 0) {
        status = '●'; // Active
        isActive = true;
      }
    }

    // Check last-used timestamp
    if (fs.existsSync(statusFile)) {
      const hookStatus = JSON.parse(fs.readFileSync(statusFile, 'utf8'));
      if (hookStatus['legal-braniac-loader']) {
        const lastRun = new Date(hookStatus['legal-braniac-loader'].timestamp);
        const secondsAgo = Math.floor((Date.now() - lastRun.getTime()) / 1000);

        if (secondsAgo < 5) {
          lastUsed = ` ${getSpinner()}`; // Spinner if used <5s ago
        } else if (secondsAgo < 60) {
          lastUsed = ` ${secondsAgo}s`;
        } else if (secondsAgo < 3600) {
          const minutesAgo = Math.floor(secondsAgo / 60);
          lastUsed = ` ${minutesAgo}m`;
        }
      } else if (isActive) {
        // Active but no last-used timestamp - show spinner
        lastUsed = ` ${getSpinner()}`;
      }
    } else if (isActive) {
      // Active but no status file - show spinner
      lastUsed = ` ${getSpinner()}`;
    }

    return `${status}${lastUsed}`;
  } catch (error) {
    return '○';
  }
}

/**
 * Get session duration
 */
function getSessionDuration() {
  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const sessionFile = path.join(projectDir, '.claude', 'hooks', 'legal-braniac-session.json');

    if (fs.existsSync(sessionFile)) {
      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
      const startTime = data.sessionStart || Date.now();
      const durationMs = Date.now() - startTime;
      const durationMin = Math.floor(durationMs / 60000);

      if (durationMin < 60) {
        return `${durationMin}m`;
      } else {
        const hours = Math.floor(durationMin / 60);
        const mins = durationMin % 60;
        return `${hours}h${mins}m`;
      }
    }
  } catch (error) {
    // Fall through
  }

  return '0m';
}

/**
 * Get counts (agents, skills, hooks)
 */
function getCounts() {
  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const sessionFile = path.join(projectDir, '.claude', 'hooks', 'legal-braniac-session.json');

    if (fs.existsSync(sessionFile)) {
      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));

      return {
        agents: data.agents?.available?.length || 0,
        skills: data.skills?.available?.length || 0,
        hooks: Object.keys(data.hooks || {}).length || 0
      };
    }
  } catch (error) {
    // Fall through
  }

  return { agents: 0, skills: 0, hooks: 0 };
}

/**
 * Get venv status
 */
function getVenvStatus() {
  const venvPath = process.env.VIRTUAL_ENV;
  return venvPath ? '●' : '○';
}

/**
 * Get git status
 */
function getGitStatus() {
  try {
    const branch = execSync('git rev-parse --abbrev-ref HEAD', {
      encoding: 'utf8',
      timeout: 1000,
      stdio: ['pipe', 'pipe', 'pipe']
    }).trim();

    const status = execSync('git status --porcelain', {
      encoding: 'utf8',
      timeout: 1000,
      stdio: ['pipe', 'pipe', 'pipe']
    }).trim();

    const hasChanges = status.length > 0;
    return hasChanges ? `${branch}*` : branch;
  } catch (error) {
    return 'unknown';
  }
}

/**
 * Pad string to width
 */
function pad(str, width) {
  // Strip ANSI codes for length calculation
  const stripped = str.replace(/\x1b\[[0-9;]*m/g, '');
  const padding = Math.max(0, width - stripped.length);
  return str + ' '.repeat(padding);
}

/**
 * Main entry point
 */
function main() {
  try {
    // Get terminal width (default 120)
    const termWidth = process.stdout.columns || 120;

    // Get data
    const gordon = getVibeLogLine();
    const braniacStatus = getLegalBraniacStatus();
    const session = getSessionDuration();
    const counts = getCounts();
    const venv = getVenvStatus();
    const git = getGitStatus();

    // LEFT side
    const left = `${colors.cyan}▸${colors.reset} ${colors.bright}${gordon}${colors.reset} ${colors.dim}|${colors.reset} ${colors.magenta}Legal-Braniac${colors.reset} ${colors.yellow}(${braniacStatus})${colors.reset} ${colors.dim}|${colors.reset} ${colors.blue}Session: ${session}${colors.reset}`;

    // RIGHT side
    const right = `${colors.green}${counts.agents} agents${colors.reset} ${colors.dim}|${colors.reset} ${colors.green}${counts.skills} skills${colors.reset} ${colors.dim}|${colors.reset} ${colors.green}${counts.hooks} hooks${colors.reset} ${colors.dim}|${colors.reset} ${colors.cyan}venv: ${venv}${colors.reset} ${colors.dim}|${colors.reset} ${colors.yellow}git: ${git}${colors.reset}`;

    // Calculate padding
    const leftStripped = left.replace(/\x1b\[[0-9;]*m/g, '');
    const rightStripped = right.replace(/\x1b\[[0-9;]*m/g, '');
    const middleLength = Math.max(3, termWidth - leftStripped.length - rightStripped.length);
    const middle = colors.dim + '─'.repeat(middleLength) + colors.reset;

    // Output
    console.log(left + middle + right);

  } catch (error) {
    // Fallback
    console.log(`${colors.cyan}▸${colors.reset} Claude Code ${colors.dim}|${colors.reset} ${colors.magenta}Legal-Braniac${colors.reset}`);
  }
}

main();
