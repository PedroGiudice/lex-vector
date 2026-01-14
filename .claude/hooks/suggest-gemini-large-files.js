#!/usr/bin/env bun
/**
 * Hook: Suggest Gemini for Large Files
 *
 * @event PreToolUse (matcher: Read)
 * @threshold 600 lines
 *
 * Verifica o tamanho do arquivo antes do Read e sugere
 * usar gemini-assistant se > 600 linhas.
 */

import { execSync } from 'child_process';

const THRESHOLD = 600;

// Read hook input from stdin
const input = await Bun.stdin.text();

try {
  const data = JSON.parse(input);

  // Only process Read tool calls
  if (data.tool_name !== 'Read') {
    process.exit(0);
  }

  const filePath = data.tool_input?.file_path;
  if (!filePath) {
    process.exit(0);
  }

  // Quick line count (very fast - pure C)
  try {
    const result = execSync(`wc -l < "${filePath}" 2>/dev/null`, { encoding: 'utf-8' });
    const lines = parseInt(result.trim(), 10);

    if (lines > THRESHOLD) {
      // Output suggestion to be injected into context
      console.log(`[large-file] Arquivo "${filePath.split('/').pop()}" tem ${lines} linhas. Considere usar gemini-assistant para analise.`);
    }
  } catch {
    // File doesn't exist or can't be read - let Read tool handle the error
  }
} catch {
  // Invalid JSON or other error - silently exit
}

process.exit(0);
