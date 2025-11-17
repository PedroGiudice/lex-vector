#!/usr/bin/env node
/**
 * Enhanced Statusline - Vibe-Log Native + Project Customizations
 *
 * Architecture:
 * 1. Call vibe-log native statusline (Gordon/coach + prompt analysis)
 * 2. Add project-specific context (legal-braniac, agentes, skills, hooks, venv, git)
 * 3. Display unified output
 *
 * Visual Priority:
 * - Line 1: Vibe-log analysis (Gordon coaching)
 * - Line 2: Project context (legal-braniac, agentes, skills)
 * - Line 3: Technical status (hooks, venv, git, session)
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

/**
 * Remove all emojis from text (replace with ASCII alternatives)
 */
function removeEmojis(text) {
  // Remove all emoji Unicode ranges
  let cleaned = text.replace(/[\u{1F300}-\u{1F9FF}]/gu, ''); // Misc symbols and pictographs
  cleaned = cleaned.replace(/[\u{1F600}-\u{1F64F}]/gu, ''); // Emoticons
  cleaned = cleaned.replace(/[\u{1F680}-\u{1F6FF}]/gu, ''); // Transport and map symbols
  cleaned = cleaned.replace(/[\u{2600}-\u{26FF}]/gu, '');   // Misc symbols
  cleaned = cleaned.replace(/[\u{2700}-\u{27BF}]/gu, '');   // Dingbats
  cleaned = cleaned.replace(/[\u{FE00}-\u{FE0F}]/gu, '');   // Variation selectors
  cleaned = cleaned.replace(/[\u{1F900}-\u{1F9FF}]/gu, ''); // Supplemental symbols
  cleaned = cleaned.replace(/[\u{1FA70}-\u{1FAFF}]/gu, ''); // Extended symbols

  // Clean up extra whitespace
  cleaned = cleaned.replace(/\s+/g, ' ').trim();

  // Add ASCII prefix if text starts without indicator
  if (cleaned && !cleaned.match(/^[▸►●○■□•-]/)) {
    cleaned = '▸ ' + cleaned;
  }

  return cleaned;
}

/**
 * Get vibe-log native statusline
 */
function getVibeLogStatusline() {
  try {
    const output = execSync('npx vibe-log-cli statusline --format compact', {
      encoding: 'utf8',
      timeout: 5000,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    return removeEmojis(output.trim());
  } catch (error) {
    // Fallback if vibe-log fails
    return '▸ Legal-Braniac is analyzing your prompts...';
  }
}

/**
 * Get legal-braniac session info
 */
function getLegalBraniacStatus() {
  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const sessionFile = path.join(projectDir, '.claude', 'hooks', 'legal-braniac-session.json');

    if (fs.existsSync(sessionFile)) {
      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
      return {
        loaded: true,
        agents: data.agents?.available?.length || 0,
        skills: data.skills?.available?.length || 0,
        lastUpdate: data.sessionStart || Date.now()
      };
    }
  } catch (error) {
    // Silent fail
  }

  return { loaded: false, agents: 0, skills: 0 };
}

/**
 * Get hooks status
 */
function getHooksStatus() {
  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const settingsFile = path.join(projectDir, '.claude', 'settings.json');

    if (fs.existsSync(settingsFile)) {
      const settings = JSON.parse(fs.readFileSync(settingsFile, 'utf8'));
      const hooks = settings.hooks || {};

      let activeHooks = 0;
      for (const [hookName, hookArray] of Object.entries(hooks)) {
        if (Array.isArray(hookArray) && hookArray.length > 0) {
          activeHooks++;
        }
      }

      return activeHooks;
    }
  } catch (error) {
    // Silent fail
  }

  return 0;
}

/**
 * Get venv status
 */
function getVenvStatus() {
  const venvPath = process.env.VIRTUAL_ENV;

  if (venvPath) {
    // Extract venv name from path
    const venvName = path.basename(path.dirname(venvPath));
    return { active: true, name: venvName };
  }

  return { active: false };
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

    // Check for uncommitted changes
    const status = execSync('git status --porcelain', {
      encoding: 'utf8',
      timeout: 1000,
      stdio: ['pipe', 'pipe', 'pipe']
    }).trim();

    const hasChanges = status.length > 0;

    return { branch, hasChanges };
  } catch (error) {
    return { branch: 'unknown', hasChanges: false };
  }
}

/**
 * Get session duration (from legal-braniac-session.json)
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
    // Silent fail
  }

  return '0m';
}

/**
 * Format project context line
 */
function formatProjectContext() {
  const braniac = getLegalBraniacStatus();
  const hooks = getHooksStatus();

  if (!braniac.loaded) {
    return '● Legal-Braniac: initializing...';
  }

  return `● Legal-Braniac | ${braniac.agents} agentes | ${braniac.skills} skills | ${hooks} hooks`;
}

/**
 * Format technical status line
 */
function formatTechnicalStatus() {
  const venv = getVenvStatus();
  const git = getGitStatus();
  const duration = getSessionDuration();

  const parts = [];

  // Venv
  if (venv.active) {
    parts.push(`venv: ●`);
  } else {
    parts.push(`venv: ○`);
  }

  // Git
  if (git.hasChanges) {
    parts.push(`git: ${git.branch}*`);
  } else {
    parts.push(`git: ${git.branch}`);
  }

  // Session duration
  parts.push(`session: ${duration}`);

  return parts.join(' | ');
}

/**
 * Main entry point
 */
function main() {
  try {
    // Line 1: Vibe-log analysis (Gordon)
    const vibeLogLine = getVibeLogStatusline();

    // Line 2: Project context
    const projectLine = formatProjectContext();

    // Line 3: Technical status
    const technicalLine = formatTechnicalStatus();

    // Output unified statusline
    console.log(vibeLogLine);
    console.log(projectLine);
    console.log(technicalLine);

  } catch (error) {
    // Fallback: minimal statusline
    console.log('▸ Gordon | Legal-Braniac | Claude Code');
  }
}

// Execute
main();
