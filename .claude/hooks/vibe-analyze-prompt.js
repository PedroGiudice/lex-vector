#!/usr/bin/env node
/**
 * vibe-analyze-prompt.js - Gordon prompt analysis hook
 *
 * Integrates vibe-log-cli analyze-prompt into Claude Code UserPromptSubmit hook.
 * Provides real-time prompt quality feedback via Gordon personality.
 *
 * Features:
 * - Background analysis (non-blocking via spawn + detach)
 * - Claude SDK-based quality scoring (0-100)
 * - Saves to ~/.vibe-log/analyzed-prompts/{sessionId}.json
 * - Integrates with professional-statusline.js
 * - Graceful failure (always returns continue: true)
 *
 * Usage: node .claude/hooks/hook-wrapper.js .claude/hooks/vibe-analyze-prompt.js
 *
 * Input (stdin): Claude Code JSON with userPrompt, sessionId, transcriptPath
 * Output (stdout): { continue: true, systemMessage: '' }
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Configuration
const CONFIG = {
  USE_NPX: true, // Use npx instead of hardcoded path
  ANALYZED_PROMPTS_DIR: path.join(process.env.HOME, '.vibe-log/analyzed-prompts'),
  MAX_EXECUTION_TIME_MS: 15000, // 15s timeout for background analysis
  DEBUG: process.env.DEBUG_GORDON === 'true'
};

/**
 * Read stdin with timeout
 */
function readStdin(timeout = 1000) {
  return new Promise((resolve) => {
    let data = '';
    let hasData = false;

    const timer = setTimeout(() => {
      if (!hasData) resolve(null);
    }, timeout);

    process.stdin.setEncoding('utf8');

    process.stdin.on('readable', () => {
      let chunk;
      while ((chunk = process.stdin.read()) !== null) {
        hasData = true;
        data += chunk;
      }
    });

    process.stdin.on('end', () => {
      clearTimeout(timer);
      resolve(hasData ? data : null);
    });
  });
}

/**
 * Log debug messages
 */
function debug(...args) {
  if (CONFIG.DEBUG) {
    console.error('[vibe-analyze-prompt]', ...args);
  }
}

/**
 * Output JSON response for hook chain
 */
function outputJSON(obj) {
  console.log(JSON.stringify(obj));
}

/**
 * Write loading state immediately for instant statusline feedback
 */
function writeLoadingState(sessionId) {
  try {
    // Ensure directory exists
    if (!fs.existsSync(CONFIG.ANALYZED_PROMPTS_DIR)) {
      fs.mkdirSync(CONFIG.ANALYZED_PROMPTS_DIR, { recursive: true });
    }

    const loadingState = {
      type: 'loading',
      sessionId,
      timestamp: Date.now(),
      personality: 'gordon',
      message: '🔥 Gordon is analyzing your prompt...'
    };

    const filePath = path.join(CONFIG.ANALYZED_PROMPTS_DIR, `${sessionId}.json`);
    fs.writeFileSync(filePath, JSON.stringify(loadingState, null, 2));

    debug(`Loading state written to ${filePath}`);
  } catch (error) {
    debug('Failed to write loading state:', error.message);
  }
}

/**
 * Spawn background analysis process
 */
function spawnAnalysis(claudeData) {
  try {
    debug('Spawning background analysis process...');

    // Prepare stdin data for analyze-prompt command
    const stdinData = JSON.stringify({
      prompt: claudeData.userPrompt,
      session_id: claudeData.sessionId,
      transcript_path: claudeData.transcriptPath
    });

    // Spawn detached process using npx
    const child = spawn('npx', [
      'vibe-log-cli',
      'analyze-prompt',
      '--silent',
      '--stdin'
    ], {
      detached: true,
      stdio: ['pipe', 'ignore', 'ignore']
    });

    // Write stdin data
    child.stdin.write(stdinData);
    child.stdin.end();

    // Unref to allow parent to exit
    child.unref();

    debug('Background process spawned (detached)');

  } catch (error) {
    debug('Failed to spawn analysis:', error.message);
    // Non-fatal: hook continues
  }
}

/**
 * Main entry point
 */
async function main() {
  try {
    // Read Claude Code JSON from stdin
    const input = await readStdin();

    if (!input) {
      debug('No stdin data received');
      outputJSON({ continue: true, systemMessage: '' });
      return;
    }

    const claudeData = JSON.parse(input);
    const { userPrompt, sessionId } = claudeData;

    // Validate required fields
    if (!userPrompt || !sessionId) {
      debug('Missing userPrompt or sessionId');
      outputJSON({ continue: true, systemMessage: '' });
      return;
    }

    debug(`Processing prompt for session: ${sessionId}`);
    debug(`Prompt length: ${userPrompt.length} chars`);

    // Write loading state immediately (instant feedback in statusline)
    writeLoadingState(sessionId);

    // Spawn background analysis (non-blocking)
    spawnAnalysis(claudeData);

    // Return immediately to not block hook chain
    outputJSON({ continue: true, systemMessage: '' });

  } catch (error) {
    debug('Error in main:', error.message);
    // Always continue on error (graceful degradation)
    outputJSON({ continue: true, systemMessage: '' });
  }
}

// Execute main
main().catch(error => {
  debug('Unhandled error:', error);
  outputJSON({ continue: true, systemMessage: '' });
});
