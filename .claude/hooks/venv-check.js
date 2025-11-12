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

    let instructions = '';
    if (isWindows) {
      instructions = `Para ativar (Windows PowerShell):
  .venv\\Scripts\\Activate.ps1

Para ativar (Windows CMD):
  .venv\\Scripts\\activate.bat`;
    } else {
      instructions = `Para ativar (Linux/Mac):
  source .venv/bin/activate`;
    }

    const message = `⚠️ RULE_006 VIOLATION: Virtual environment NÃO está ativo!

${instructions}

Este é um requisito OBRIGATÓRIO antes de qualquer execução Python.`;

    outputJSON({
      continue: true,
      systemMessage: message
    });

  } else {
    // VENV ATIVO - Mensagem de sucesso
    outputJSON({
      continue: true,
      systemMessage: `✓ Virtual environment ativo: ${venvPath}`
    });
  }
}

/**
 * Output JSON para Claude Code
 */
function outputJSON(obj) {
  console.log(JSON.stringify(obj, null, 2));
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
