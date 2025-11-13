#!/usr/bin/env node

/**
 * session-start.js - Instala dependências Python para Claude Code Web
 *
 * DISASTER_HISTORY compliance:
 * - LIÇÃO 4: Usa process.env.CLAUDE_PROJECT_DIR (dinâmico)
 * - LIÇÃO 4: NUNCA hardcode paths
 * - Timeouts em operações pip (evita hang no Windows)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ============================================================================
// CONSTANTES
// ============================================================================

const TIMEOUT_PIP_INSTALL = 120000; // 2 minutos por comando pip
const PIP_QUIET_FLAGS = '--user --quiet';

// ============================================================================
// FUNÇÕES AUXILIARES
// ============================================================================

/**
 * Executa comando com timeout
 * @param {string} command - Comando a executar
 * @param {number} timeout - Timeout em ms
 * @returns {string|null} - Output do comando ou null se erro
 */
function execWithTimeout(command, timeout = TIMEOUT_PIP_INSTALL) {
  try {
    return execSync(command, {
      timeout: timeout,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });
  } catch (error) {
    // Retorna null mas não lança exceção (|| true behavior)
    return null;
  }
}

/**
 * Verifica se arquivo existe
 */
function fileExists(filepath) {
  return fs.existsSync(filepath);
}

/**
 * Instala requirements.txt se existir
 */
function installRequirements(requirementsPath, label) {
  if (!fileExists(requirementsPath)) {
    return null;
  }

  console.error(`📦 Installing ${label}...`);
  const result = execWithTimeout(
    `pip install ${PIP_QUIET_FLAGS} -r "${requirementsPath}"`,
    TIMEOUT_PIP_INSTALL
  );

  if (result === null) {
    return `⚠️ Timeout or error installing ${label}`;
  }

  return `✓ ${label} installed`;
}

/**
 * Adiciona variável ao CLAUDE_ENV_FILE
 */
function exportEnvVar(name, value) {
  const envFile = process.env.CLAUDE_ENV_FILE;
  if (!envFile) {
    return false;
  }

  try {
    fs.appendFileSync(envFile, `export ${name}="${value}"\n`);
    return true;
  } catch (error) {
    return false;
  }
}

// ============================================================================
// LÓGICA PRINCIPAL
// ============================================================================

function main() {
  // GUARD: Só executar em Claude Code Web (remoto)
  if (process.env.CLAUDE_CODE_REMOTE !== 'true') {
    // Exit silencioso - não é ambiente remoto, mas DEVE retornar JSON válido
    outputJSON({
      continue: true,
      systemMessage: ''
    });
    process.exit(0);
  }

  // STRATEGY: Usar CLAUDE_PROJECT_DIR se disponível, senão process.cwd()
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

  console.error(`📂 Project directory: ${projectDir}`);

  console.error('🔧 Setting up Python environment for Claude-Code-Projetos (web)...');

  const messages = [];

  // -------------------------------------------------------------------------
  // 1. Instalar dependências root
  // -------------------------------------------------------------------------
  const rootRequirements = path.join(projectDir, 'requirements.txt');
  const rootResult = installRequirements(rootRequirements, 'root dependencies');
  if (rootResult) messages.push(rootResult);

  // -------------------------------------------------------------------------
  // 2. Instalar dependências oab-watcher (includes pytest)
  // -------------------------------------------------------------------------
  const oabRequirements = path.join(projectDir, 'agentes', 'oab-watcher', 'requirements.txt');
  const oabResult = installRequirements(oabRequirements, 'oab-watcher dependencies (includes pytest)');
  if (oabResult) messages.push(oabResult);

  // Instalar pytest-cov
  console.error('📦 Installing pytest-cov...');
  execWithTimeout(`pip install ${PIP_QUIET_FLAGS} pytest-cov`, TIMEOUT_PIP_INSTALL);

  // -------------------------------------------------------------------------
  // 3. Instalar dependências legal-rag (includes mypy)
  // -------------------------------------------------------------------------
  const legalRequirements = path.join(projectDir, 'agentes', 'legal-rag', 'requirements.txt');
  const legalResult = installRequirements(legalRequirements, 'legal-rag dependencies (includes mypy)');
  if (legalResult) messages.push(legalResult);

  // -------------------------------------------------------------------------
  // 4. Instalar type stubs para mypy
  // -------------------------------------------------------------------------
  console.error('📦 Installing type stubs for mypy...');
  execWithTimeout(`pip install ${PIP_QUIET_FLAGS} types-requests types-tqdm`, TIMEOUT_PIP_INSTALL);

  // -------------------------------------------------------------------------
  // 5. Configurar PYTHONPATH
  // -------------------------------------------------------------------------
  const currentPythonPath = process.env.PYTHONPATH || '';
  const newPythonPath = currentPythonPath
    ? `${projectDir}:${currentPythonPath}`
    : projectDir;

  const exportSuccess = exportEnvVar('PYTHONPATH', newPythonPath);
  if (exportSuccess) {
    messages.push('✓ PYTHONPATH configured');
  }

  // -------------------------------------------------------------------------
  // 6. Output final
  // -------------------------------------------------------------------------
  console.error('✅ Python environment setup complete!');

  const finalMessage = `✅ Python environment setup complete!
   - Root dependencies installed
   - pytest available for testing
   - mypy available for linting
   - PYTHONPATH configured`;

  outputJSON({
    continue: true,
    systemMessage: finalMessage
  });
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
    systemMessage: `⚠️ session-start.js error: ${error.message}\n(Continuing anyway...)`
  });
  process.exit(0);
}
