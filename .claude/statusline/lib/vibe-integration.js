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

module.exports = {
  getVibeLoggingMetrics
};
