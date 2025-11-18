#!/usr/bin/env node
/**
 * Professional Statusline v6.0 - Flowing Aesthetic Design
 *
 * Layout: [LEFT aligned info] ··· [RIGHT aligned info]
 *
 * LEFT:  ▸ Gordon  ◆  Legal-Braniac ● 8m  ◆  Session 1h23m
 * RIGHT: ● 7 agents  ◇  ● 38 skills  ◇  ● 4 hooks  ◇  venv ●  ◇  git main*
 *
 * Features:
 * - NO heavy bar separator - uses flowing ··· dots or subtle ◇ diamonds
 * - BLINKING indicators (●) when hooks are active (< 5s ago)
 * - Harmonious color palette: cyan, magenta, blue, green, purple, orange, pink
 * - Clean spacing with breathing room between elements
 * - Dynamic visual feedback without clutter
 * - Terminal-native blinking (resource-efficient)
 * - Elegant, flowing design that guides the eye naturally
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ============================================================================
// CACHE SYSTEM - Reduce latency from ~3.4s to ~0.05s
// ============================================================================

const CACHE_DIR = path.join(process.env.CLAUDE_PROJECT_DIR || process.cwd(), '.claude', 'cache');
const CACHE_FILE = path.join(CACHE_DIR, 'statusline-cache.json');

// TTL (Time To Live) in seconds for each cache key
const CACHE_TTL = {
  'vibe-log': 30,      // Gordon analysis changes slowly
  'git-status': 5,     // Git status changes with commits
  'git-branch': 5,     // Branch rarely changes
  'tracker': 2,        // Real-time tracking data
  'session-file': 1,   // Session file almost static during session
  'status-file': 1     // Status file almost static
};

/**
 * Get cached data or fetch fresh if expired
 * @param {string} key - Cache key
 * @param {function} fetchFn - Function to fetch fresh data if cache miss
 * @returns {any} Cached or fresh data
 */
function getCachedData(key, fetchFn) {
  try {
    // Load cache from file
    let cache = {};
    if (fs.existsSync(CACHE_FILE)) {
      const fileContent = fs.readFileSync(CACHE_FILE, 'utf8');
      cache = JSON.parse(fileContent);
    }

    const entry = cache[key];
    const ttl = CACHE_TTL[key] || 5; // Default 5s TTL
    const now = Date.now();

    // Check if cache is valid
    if (entry && entry.timestamp && (now - entry.timestamp) < (ttl * 1000)) {
      return entry.data; // Cache HIT
    }

    // Cache MISS - fetch fresh data
    const freshData = fetchFn();

    // Update cache
    cache[key] = {
      data: freshData,
      timestamp: now
    };

    // Write cache to file (async, best effort)
    try {
      fs.mkdirSync(CACHE_DIR, { recursive: true });
      fs.writeFileSync(CACHE_FILE, JSON.stringify(cache));
    } catch (writeError) {
      // Ignore write errors - cache will just be less effective
    }

    return freshData;

  } catch (error) {
    // On any error, fall back to fetching fresh data without caching
    return fetchFn();
  }
}

// ANSI colors - Professional palette
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  blink: '\x1b[5m', // Blinking text

  // Foreground colors - Harmonious palette
  red: '\x1b[31m',
  green: '\x1b[38;5;42m',    // Brighter green
  yellow: '\x1b[38;5;226m',  // Vibrant yellow
  blue: '\x1b[38;5;39m',     // Bright blue
  magenta: '\x1b[38;5;170m', // Soft magenta
  cyan: '\x1b[38;5;51m',     // Bright cyan
  white: '\x1b[37m',
  gray: '\x1b[90m',
  lightGray: '\x1b[38;5;246m', // Lighter gray for separators
  orange: '\x1b[38;5;208m',    // Orange
  purple: '\x1b[38;5;141m',    // Soft purple
  pink: '\x1b[38;5;213m',      // Pink
  teal: '\x1b[38;5;87m',       // Teal for accents

  // Background colors
  bgRed: '\x1b[41m',
  bgGreen: '\x1b[42m',
  bgYellow: '\x1b[43m',
  bgBlue: '\x1b[44m',
};

/**
 * Get blinking indicator character
 * Returns a colored, blinking ● when activity detected
 */
function getBlinkingIndicator(color) {
  return `${colors.blink}${color}●${colors.reset}`;
}

/**
 * Get vibe-log statusline (Gordon coaching) - WITH CACHE
 */
function getVibeLogLine() {
  return getCachedData('vibe-log', () => {
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
  });
}

/**
 * Get legal-braniac status with blinking indicator when recently used
 */
function getLegalBraniacStatus() {
  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const sessionFile = path.join(projectDir, '.claude', 'hooks', 'legal-braniac-session.json');
    const statusFile = path.join(projectDir, '.claude', 'statusline', 'hooks-status.json');

    let status = '○'; // Default: inactive
    let indicator = '';
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
          // BLINKING indicator if used <5s ago
          indicator = ` ${getBlinkingIndicator(colors.yellow)}`;
        } else if (secondsAgo < 60) {
          indicator = ` ${secondsAgo}s`;
        } else if (secondsAgo < 3600) {
          const minutesAgo = Math.floor(secondsAgo / 60);
          indicator = ` ${minutesAgo}m`;
        }
      } else if (isActive) {
        // Active but no last-used timestamp - show blinking
        indicator = ` ${getBlinkingIndicator(colors.yellow)}`;
      }
    } else if (isActive) {
      // Active but no status file - show blinking
      indicator = ` ${getBlinkingIndicator(colors.yellow)}`;
    }

    return `${status}${indicator}`;
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
 * Get real-time tracking data from simple_tracker.py - WITH CACHE
 */
function getTrackerData() {
  return getCachedData('tracker', () => {
    try {
      const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
      const trackerPath = path.join(projectDir, '.claude', 'monitoring', 'simple_tracker.py');

      if (fs.existsSync(trackerPath)) {
        const output = execSync(`${trackerPath} statusline`, {
          encoding: 'utf8',
          timeout: 500,
          stdio: ['pipe', 'pipe', 'pipe']
        }).trim();

        // Parse output: "🤖 0/0 │ ⚡ 0 │ 🛠️ -"
        const match = output.match(/🤖 (\d+)\/(\d+) │ ⚡ (\d+) │ 🛠️ (.+)/);
        if (match) {
          return {
            activeAgents: parseInt(match[1]),
            totalAgents: parseInt(match[2]),
            hooksRecent: parseInt(match[3]),
            skillsStr: match[4]
          };
        }
      }
    } catch (error) {
      // Fall through
    }

    return null;
  });
}

/**
 * Get counts (agents, skills, hooks) with activity tracking
 */
function getCounts() {
  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const sessionFile = path.join(projectDir, '.claude', 'hooks', 'legal-braniac-session.json');
    const statusFile = path.join(projectDir, '.claude', 'statusline', 'hooks-status.json');

    let agentsCount = 0;
    let skillsCount = 0;
    let hooksCount = 0;
    let agentsActive = false;
    let skillsActive = false;
    let hooksActive = false;

    // Try getting real-time data from tracker first
    const trackerData = getTrackerData();
    if (trackerData && trackerData.totalAgents > 0) {
      agentsCount = trackerData.totalAgents;
      agentsActive = trackerData.activeAgents > 0;
      skillsActive = trackerData.skillsStr !== '-';
      hooksActive = trackerData.hooksRecent > 0;
    }

    if (fs.existsSync(sessionFile)) {
      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));

      // Use legal-braniac counts if tracker has no data
      if (agentsCount === 0) {
        agentsCount = data.agents?.available?.length || 0;
      }
      if (skillsCount === 0) {
        skillsCount = data.skills?.available?.length || 0;
      }
      hooksCount = Object.keys(data.hooks || {}).length || 0;
    }

    // Check if any hook was used recently (< 5s ago)
    if (fs.existsSync(statusFile)) {
      const hookStatus = JSON.parse(fs.readFileSync(statusFile, 'utf8'));
      const now = Date.now();

      for (const hookName in hookStatus) {
        const lastRun = new Date(hookStatus[hookName].timestamp);
        const secondsAgo = Math.floor((now - lastRun.getTime()) / 1000);

        if (secondsAgo < 5) {
          // Determine which category is active
          if (hookName.includes('agent') || hookName.includes('braniac')) {
            agentsActive = true;
          }
          if (hookName.includes('skill')) {
            skillsActive = true;
          }
          hooksActive = true;
        }
      }
    }

    return {
      agents: agentsCount,
      skills: skillsCount,
      hooks: hooksCount,
      agentsActive,
      skillsActive,
      hooksActive
    };
  } catch (error) {
    // Fall through
  }

  return { agents: 0, skills: 0, hooks: 0, agentsActive: false, skillsActive: false, hooksActive: false };
}

/**
 * Get venv status
 */
function getVenvStatus() {
  const venvPath = process.env.VIRTUAL_ENV;
  return venvPath ? '●' : '○';
}

/**
 * Get git status - WITH CACHE
 */
function getGitStatus() {
  return getCachedData('git-status', () => {
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
  });
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

    // Blinking indicators for active items
    const agentIndicator = counts.agentsActive ? `${getBlinkingIndicator(colors.green)} ` : '';
    const skillIndicator = counts.skillsActive ? `${getBlinkingIndicator(colors.purple)} ` : '';
    const hookIndicator = counts.hooksActive ? `${getBlinkingIndicator(colors.orange)} ` : '';

    // Elegant separators (different styles for variety)
    const diamond = `${colors.lightGray}◇${colors.reset}`;
    const dot = `${colors.lightGray}·${colors.reset}`;

    // LEFT side - uses ◆ diamond for major sections
    const left = `${colors.cyan}▸${colors.reset} ${colors.bright}${gordon}${colors.reset} ${colors.lightGray}◆${colors.reset} ${colors.magenta}Legal-Braniac${colors.reset} ${colors.yellow}${braniacStatus}${colors.reset} ${colors.lightGray}◆${colors.reset} ${colors.blue}Session${colors.reset} ${colors.bright}${session}${colors.reset}`;

    // RIGHT side - uses ◇ hollow diamond for subsections
    const right = `${agentIndicator}${colors.green}${counts.agents} agents${colors.reset} ${diamond} ${skillIndicator}${colors.purple}${counts.skills} skills${colors.reset} ${diamond} ${hookIndicator}${colors.orange}${counts.hooks} hooks${colors.reset} ${diamond} ${colors.cyan}venv${colors.reset} ${colors.yellow}${venv}${colors.reset} ${diamond} ${colors.pink}git${colors.reset} ${colors.teal}${git}${colors.reset}`;

    // Calculate spacing - use flowing dots for middle section
    const leftStripped = left.replace(/\x1b\[[0-9;]*m/g, '');
    const rightStripped = right.replace(/\x1b\[[0-9;]*m/g, '');
    const middleLength = Math.max(3, termWidth - leftStripped.length - rightStripped.length - 2);

    // Create elegant flowing separator with dots
    let middle;
    if (middleLength > 20) {
      // Long separator: use spaced dots for breathing room
      const numDots = Math.floor(middleLength / 2);
      middle = ' ' + `${colors.dim}${dot}${colors.reset} `.repeat(Math.max(1, numDots - 1)) + ' ';
    } else if (middleLength > 6) {
      // Medium separator: compact dots
      middle = ` ${colors.dim}${dot.repeat(3)}${colors.reset} `;
    } else {
      // Short separator: minimal spacing
      middle = '  ';
    }

    // Output - flowing design with no heavy bars
    console.log(left + middle + right);

  } catch (error) {
    // Fallback - elegant even in error
    console.log(`${colors.cyan}▸${colors.reset} Claude Code ${colors.lightGray}◆${colors.reset} ${colors.magenta}Legal-Braniac${colors.reset}`);
  }
}

main();
