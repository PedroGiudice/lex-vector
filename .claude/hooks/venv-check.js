#!/usr/bin/env node

/**
 * venv-check.js - Verifica se virtual environment está ativo
 *
 * DISASTER_HISTORY compliance:
 * - LIÇÃO 6: Ambiente virtual NÃO é opcional
 * - RULE_006: venv SEMPRE obrigatório
 */

const os = require('os');

// ============================================================================
// LÓGICA PRINCIPAL
// ============================================================================

function main() {
  const venvPath = process.env.VIRTUAL_ENV;
  const platform = os.platform();

  if (!venvPath) {
    // VENV NÃO ATIVO - Gerar mensagem com instruções multi-plataforma
    const isWindows = platform === 'win32';

    const activateCmd = isWindows
      ? '.venv\\Scripts\\Activate.ps1'
      : 'source .venv/bin/activate';

    const message = `⚠️ RULE_006: venv não ativo! Ative com: ${activateCmd}`;

    outputJSON({
      continue: true,
      systemMessage: message
    });

  } else {
    // VENV ATIVO - Mensagem concisa
    outputJSON({
      continue: true,
      systemMessage: `✓ venv ativo`
    });
  }
}

/**
 * Output JSON para Claude Code
 */
function outputJSON(obj) {
  console.log(JSON.stringify(obj));
}

// ============================================================================
// EXECUÇÃO
// ============================================================================

try {
  main();
} catch (error) {
  outputJSON({
    continue: true,
    systemMessage: `⚠️ venv-check.js error: ${error.message}`
  });
  process.exit(0);
}
