#!/usr/bin/env node

/**
 * inject-tools-to-agents.js - PreToolUse hook for Task tool
 *
 * CRITICAL HOOK: Injects tool availability instructions into Task agents
 *
 * Trigger: PreToolUse (when tool_name === "Task")
 * Function: Modify agent prompt to include tool availability and usage instructions
 *
 * Input (stdin JSON):
 * {
 *   "session_id": "uuid",
 *   "tool_name": "Task",
 *   "tool_input": {
 *     "subagent_type": "Plan",
 *     "description": "...",
 *     "prompt": "...",
 *     "model": "haiku|sonnet|opus"
 *   },
 *   "hook_event_name": "PreToolUse"
 * }
 *
 * Output (stdout JSON):
 * {
 *   "updatedInput": {
 *     "prompt": "original prompt + tool instructions"
 *   }
 * }
 *
 * Exit codes:
 * - 0: Success (tool call proceeds with modified input)
 * - 1: Error (tool call proceeds with original input)
 * - 2: Deny (tool call blocked - NOT used by this hook)
 *
 * Version: 1.0.0
 * Author: Claude Code (Sonnet 4.5)
 * Date: 2025-11-20
 */

const fs = require('fs');
const path = require('path');
const { getAgentConfig } = require('./lib/agent-mapping-loader');

// ============================================================================
// CONFIGURATION
// ============================================================================

const PROJECT_DIR = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const DEBUG_LOG = path.join(PROJECT_DIR, '.claude', 'hooks', 'lib', 'pretool-debug.log');
const ENABLE_DEBUG = process.env.PRETOOL_DEBUG === '1';

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Log debug message to file (non-blocking, never fails)
 */
function debugLog(message, data = null) {
  if (!ENABLE_DEBUG) return;

  try {
    const timestamp = new Date().toISOString();
    const logEntry = data
      ? `[${timestamp}] ${message}: ${JSON.stringify(data, null, 2)}\n`
      : `[${timestamp}] ${message}\n`;

    fs.appendFileSync(DEBUG_LOG, logEntry, { encoding: 'utf8', flag: 'a' });
  } catch (err) {
    // Silently fail - debug logging should NEVER crash the hook
  }
}

/**
 * Output JSON to stdout and exit
 */
function outputAndExit(data, exitCode = 0) {
  try {
    console.log(JSON.stringify(data, null, 0));
  } catch (err) {
    console.error(`[ERROR] Failed to stringify output: ${err.message}`);
    process.exit(1);
  }
  process.exit(exitCode);
}

/**
 * Pass through without modification
 */
function passThrough(reason) {
  debugLog(`Pass through: ${reason}`);
  // Empty object = no modification
  outputAndExit({}, 0);
}

/**
 * Handle error gracefully (pass through + log)
 */
function handleError(context, error) {
  console.error(`[ERROR] ${context}: ${error.message}`);
  debugLog(`ERROR: ${context}`, { error: error.message, stack: error.stack });
  passThrough(`error in ${context}`);
}

// ============================================================================
// CORE LOGIC
// ============================================================================

// Note: loadAgentMapping() removed - now using shared helper from lib/

/**
 * Build tool injection instruction for agent
 */
function buildToolInstruction(agentType, agentConfig) {
  const { tools, critical_instruction } = agentConfig;

  // Build tools list
  const toolsList = tools.includes('*')
    ? 'ALL tools (inherited from main context)'
    : tools.join(', ');

  let instruction = `\n\n---\n[SYSTEM: Available tools for this task: ${toolsList}]`;

  // Add critical instruction if present
  if (critical_instruction) {
    instruction += `\n${critical_instruction}`;
  }

  instruction += '\n---\n';

  return instruction;
}

/**
 * Main hook execution
 */
function main() {
  debugLog('=== PreToolUse hook started ===');

  // -------------------------------------------------------------------------
  // 1. Read and parse stdin
  // -------------------------------------------------------------------------

  let inputData;
  try {
    const stdinBuffer = fs.readFileSync(0, 'utf-8'); // fd 0 = stdin
    inputData = JSON.parse(stdinBuffer);
    debugLog('Received input', {
      tool_name: inputData.tool_name,
      has_tool_input: !!inputData.tool_input
    });
  } catch (error) {
    handleError('parsing stdin', error);
    return;
  }

  // -------------------------------------------------------------------------
  // 2. Validate input structure
  // -------------------------------------------------------------------------

  const { tool_name, tool_input, hook_event_name } = inputData;

  if (hook_event_name !== 'PreToolUse') {
    passThrough(`wrong hook event: ${hook_event_name}`);
    return;
  }

  if (tool_name !== 'Task') {
    passThrough(`not a Task tool: ${tool_name}`);
    return;
  }

  if (!tool_input || typeof tool_input !== 'object') {
    passThrough('missing or invalid tool_input');
    return;
  }

  // -------------------------------------------------------------------------
  // 3. Extract Task parameters
  // -------------------------------------------------------------------------

  const { subagent_type, prompt, description, model } = tool_input;

  if (!subagent_type) {
    passThrough('no subagent_type specified');
    return;
  }

  if (!prompt || typeof prompt !== 'string') {
    passThrough('missing or invalid prompt');
    return;
  }

  debugLog('Task tool detected', {
    subagent_type,
    prompt_length: prompt.length,
    description: description?.substring(0, 50)
  });

  // -------------------------------------------------------------------------
  // 4. Get agent configuration from shared mapping
  // -------------------------------------------------------------------------

  let agentConfig;
  try {
    agentConfig = getAgentConfig(subagent_type, { projectDir: PROJECT_DIR });

    if (!agentConfig) {
      debugLog(`Agent type "${subagent_type}" not in mapping - using defaults`);
      passThrough(`agent type not in mapping: ${subagent_type}`);
      return;
    }
  } catch (error) {
    handleError('loading agent config', error);
    return;
  }

  debugLog('Agent config found', {
    subagent_type,
    tools: agentConfig.tools,
    has_critical_instruction: !!agentConfig.critical_instruction
  });

  // -------------------------------------------------------------------------
  // 6. Build modified prompt
  // -------------------------------------------------------------------------

  let modifiedPrompt;
  try {
    const toolInstruction = buildToolInstruction(subagent_type, agentConfig);
    modifiedPrompt = prompt + toolInstruction;

    debugLog('Prompt modified', {
      original_length: prompt.length,
      modified_length: modifiedPrompt.length,
      injection_length: toolInstruction.length
    });
  } catch (error) {
    handleError('building tool instruction', error);
    return;
  }

  // -------------------------------------------------------------------------
  // 7. Return modified input
  // -------------------------------------------------------------------------

  const output = {
    updatedInput: {
      prompt: modifiedPrompt
      // Keep all other fields unchanged (description, model, etc)
      // Claude Code will merge this with original tool_input
    }
  };

  debugLog('Returning modified input', { success: true });
  outputAndExit(output, 0);
}

// ============================================================================
// EXECUTION
// ============================================================================

// Safety wrapper - catch ALL errors
try {
  main();
} catch (error) {
  handleError('unexpected error in main', error);
}
