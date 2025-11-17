// vibe-integration.js - Integração com VibbinLoggin (vibe-log-cli)
//
// Lê análises de prompts de ~/.vibe-log/analyzed-prompts/
// Vibe-log salva análises por session_id quando hooks estão instalados

const fs = require('fs');
const path = require('path');
const { colorize } = require('./color-palette');

/**
 * Get score emoji based on vibe-log scoring
 */
function getScoreEmoji(score) {
  if (score <= 40) return '🔴';      // Poor (0-40)
  if (score <= 60) return '🟠';      // Fair (41-60)
  if (score <= 80) return '🟡';      // Good (61-80)
  return '🟢';                       // Excellent (81-100)
}

/**
 * Get most recent analysis file from vibe-log
 * Returns null if:
 * - Directory doesn't exist (vibe-log not installed)
 * - No files found
 * - Files are stale (> 5 minutes old)
 */
function getLatestAnalysis() {
  const homeDir = process.env.HOME || process.env.USERPROFILE;
  const analysisDir = path.join(homeDir, '.vibe-log', 'analyzed-prompts');

  try {
    if (!fs.existsSync(analysisDir)) {
      return null; // Vibe-log not installed or no hooks configured
    }

    // List all JSON files
    const files = fs.readdirSync(analysisDir)
      .filter(f => f.endsWith('.json'))
      .map(f => ({
        name: f,
        path: path.join(analysisDir, f),
        mtime: fs.statSync(path.join(analysisDir, f)).mtime.getTime()
      }))
      .sort((a, b) => b.mtime - a.mtime); // Most recent first

    if (files.length === 0) {
      return null; // No analysis files yet
    }

    // Get most recent file
    const latest = files[0];

    // Check if stale (older than 5 minutes)
    const age = Date.now() - latest.mtime;
    if (age > 5 * 60 * 1000) {
      return null; // Too old, not relevant
    }

    // Read and parse
    const content = fs.readFileSync(latest.path, 'utf8');
    const data = JSON.parse(content);

    return data;
  } catch (error) {
    // Parsing error, permission error, etc - degrade gracefully
    return null;
  }
}

/**
 * Get VibbinLoggin coaching metrics
 *
 * Reads from ~/.vibe-log/analyzed-prompts/ directory
 *
 * Expected JSON format:
 * {
 *   "quality": "excellent" | "good" | "fair" | "poor",
 *   "score": 0-100,
 *   "suggestion": "string",
 *   "contextualEmoji": "💡" (optional),
 *   "actionableSteps": "string" (optional)
 * }
 *
 * Or loading state:
 * {
 *   "state": "loading",
 *   "message": "Analyzing...",
 *   "timestamp": 123456789
 * }
 *
 * Returns formatted string for statusline
 */
function getVibeLoggingMetrics() {
  try {
    const analysis = getLatestAnalysis();

    if (!analysis) {
      // No data - either not installed, no hooks, or stale
      return colorize('💫 Vibe: not configured', 'gray');
    }

    // Check if loading state
    if (analysis.state === 'loading') {
      const message = analysis.message || 'Analyzing...';
      // Truncate long loading messages
      const shortMessage = message.length > 25
        ? message.substring(0, 22) + '...'
        : message;
      return colorize(`⏳ Vibe: ${shortMessage}`, 'cyan');
    }

    // Check if valid completed analysis
    if (typeof analysis.score !== 'number' || !analysis.suggestion) {
      return colorize('💫 Vibe: invalid data', 'gray');
    }

    const score = analysis.score;
    const suggestion = analysis.suggestion;

    // Use contextual emoji from analysis, or default based on score
    const emoji = analysis.contextualEmoji || getScoreEmoji(score);

    // Color based on score
    let scoreColor = 'cyan';
    if (score >= 80) scoreColor = 'green';
    else if (score >= 60) scoreColor = 'cyan';
    else if (score >= 40) scoreColor = 'yellow';
    else scoreColor = 'red';

    // Truncate suggestion if too long (statusline real estate is limited)
    const maxLen = 35;
    const shortSuggestion = suggestion.length > maxLen
      ? suggestion.substring(0, maxLen - 3) + '...'
      : suggestion;

    // Format: "🟢 Vibe: 85/100 Add more context"
    const scoreText = colorize(`${emoji} Vibe: ${score}/100`, scoreColor);
    const suggestionText = colorize(shortSuggestion, 'gray');

    return `${scoreText} ${suggestionText}`;
  } catch (error) {
    // Unexpected error - degrade gracefully
    return colorize('💫 Vibe: error', 'red');
  }
}

/**
 * Get vibe score object with detailed info
 *
 * Returns:
 * - null: vibe-log not installed or data stale
 * - { state: 'loading', ... }: analysis in progress
 * - { score, emoji, suggestion, quality }: complete analysis
 */
function getVibeScore() {
  const analysis = getLatestAnalysis();

  if (!analysis) {
    return null;
  }

  if (analysis.state === 'loading') {
    return {
      state: 'loading',
      message: analysis.message || 'Analyzing...'
    };
  }

  if (typeof analysis.score !== 'number') {
    return null;
  }

  return {
    score: analysis.score,
    emoji: analysis.contextualEmoji || getScoreEmoji(analysis.score),
    suggestion: analysis.suggestion || '',
    quality: analysis.quality || 'unknown'
  };
}

/**
 * Get full coaching suggestion (Gordon Ramsay style)
 *
 * Returns complete coaching message for Line 3 display
 * Format: "💡 Gordon: \"Ship by FRIDAY or you're fired! Add tests NOW!\""
 */
function getCoachingSuggestion() {
  const analysis = getLatestAnalysis();

  if (!analysis) {
    return '💡 Gordon: "Install vibe-log for coaching! npm install -g vibe-log-cli"';
  }

  if (analysis.state === 'loading') {
    const msg = analysis.message || 'Analyzing your prompt quality...';
    return `⏳ Gordon: "${msg}"`;
  }

  // Use actionableSteps if available (Gordon's aggressive coaching)
  if (analysis.actionableSteps) {
    return `💡 Gordon: "${analysis.actionableSteps}"`;
  }

  // Fallback to regular suggestion
  if (analysis.suggestion) {
    return `💡 Suggestion: "${analysis.suggestion}"`;
  }

  return '💡 Gordon: "Good work! Keep this momentum going!"';
}

/**
 * Get token usage stats
 *
 * Reads from ~/.vibe-log/hooks-stats.json
 * Returns { used, total, percentage } or null if unavailable
 */
function getTokenUsage() {
  const homeDir = process.env.HOME || process.env.USERPROFILE;
  const statsPath = path.join(homeDir, '.vibe-log', 'hooks-stats.json');

  try {
    if (!fs.existsSync(statsPath)) {
      return null;
    }

    const content = fs.readFileSync(statsPath, 'utf8');
    const stats = JSON.parse(content);

    // Expected format: { tokens_used: 92000, tokens_total: 200000 }
    if (typeof stats.tokens_used === 'number' && typeof stats.tokens_total === 'number') {
      const percentage = Math.round((stats.tokens_used / stats.tokens_total) * 100);
      return {
        used: stats.tokens_used,
        total: stats.tokens_total,
        percentage: percentage
      };
    }

    return null;
  } catch (error) {
    return null;
  }
}

/**
 * Get session duration formatted as human-readable string
 *
 * Reads from ~/.vibe-log/config.json (session_start_time)
 * Returns "2h15m" or null if unavailable
 */
function getSessionDuration() {
  const homeDir = process.env.HOME || process.env.USERPROFILE;
  const configPath = path.join(homeDir, '.vibe-log', 'config.json');

  try {
    if (!fs.existsSync(configPath)) {
      return null;
    }

    const content = fs.readFileSync(configPath, 'utf8');
    const config = JSON.parse(content);

    if (!config.session_start_time) {
      return null;
    }

    // Calculate duration
    const startTime = new Date(config.session_start_time).getTime();
    const now = Date.now();
    const durationMs = now - startTime;

    // Format as "XhYYm"
    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) {
      return `${hours}h${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  } catch (error) {
    return null;
  }
}

module.exports = {
  getVibeLoggingMetrics,
  getVibeScore,
  getCoachingSuggestion,
  getTokenUsage,
  getSessionDuration
};
