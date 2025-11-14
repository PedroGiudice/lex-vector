#!/usr/bin/env node
/**
 * Corporate Environment Detector Hook
 *
 * Detecta se Claude Code está rodando em ambiente corporativo Windows
 * e avisa sobre limitações conhecidas (EPERM, GPO restrictions, etc)
 *
 * Funcionalidades:
 * - Detecção heurística de ambiente corporativo
 * - Verificação de GPOs comuns que causam problemas
 * - Sugestão de workarounds quando aplicável
 * - Output token-efficient
 *
 * @version 1.0.0
 * @date 2025-11-13
 * @related DISASTER_HISTORY.md DIA 4 - LIÇÃO 8
 */

const os = require('os');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Output padronizado em formato JSON (requerido por Claude Code hooks)
 */
function outputJSON(obj) {
  console.log(JSON.stringify(obj));
}

/**
 * Executa comando shell e retorna output (com error handling)
 */
function safeExec(command) {
  try {
    return execSync(command, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
  } catch (error) {
    return null;
  }
}

// =============================================================================
// CORPORATE DETECTION HEURISTICS
// =============================================================================

/**
 * Detecta se username sugere ambiente corporativo
 * Heurísticas:
 * - 2-4 caracteres todos maiúsculos (ex: CMR, ABC, JDO)
 * - Padrão FirstnameLastname sem espaços (ex: JohnDoe)
 * - Padrão empresa.usuario (ex: contoso.jdoe)
 */
function isCorporateUsername(username) {
  if (!username || username === 'unknown') return false;

  // Heurística 1: Siglas (2-4 chars, maiúsculas)
  if (/^[A-Z]{2,4}$/.test(username)) {
    return true;
  }

  // Heurística 2: Empresa.Usuario pattern
  if (/^[a-z]+\.[a-z]+$/i.test(username)) {
    return true;
  }

  // Heurística 3: FirstnameLastname sem espaços (PascalCase)
  if (/^[A-Z][a-z]+[A-Z][a-z]+$/.test(username)) {
    return true;
  }

  return false;
}

/**
 * Detecta se máquina está em domínio Windows (Active Directory)
 */
function isInWindowsDomain() {
  if (os.platform() !== 'win32') return false;

  const output = safeExec('wmic computersystem get domain');
  if (!output) return false;

  // Parse output: se domain != WORKGROUP, está em domínio corporativo
  const lines = output.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  if (lines.length < 2) return false;

  const domain = lines[1];
  return domain && domain.toUpperCase() !== 'WORKGROUP';
}

/**
 * Detecta se há GPOs aplicadas (Group Policy Objects)
 */
function hasActiveGPOs() {
  if (os.platform() !== 'win32') return false;

  const output = safeExec('gpresult /r /scope:computer');
  if (!output) return false;

  // Procurar por GPOs aplicadas
  return output.includes('Applied Group Policy Objects') ||
         output.includes('Objetos de Diretiva de Grupo Aplicados');
}

/**
 * Testa se consegue criar diretório temporário .lock (simulação)
 */
function canCreateLockDir() {
  const testLockPath = path.join(os.homedir(), '.test-corporate-lock-detector');

  try {
    // Tentar criar
    fs.mkdirSync(testLockPath);

    // Tentar remover
    fs.rmdirSync(testLockPath);

    return true; // Sucesso
  } catch (error) {
    // Falha com EPERM ou similar
    return error.code === 'EPERM' ? false : true;
  }
}

/**
 * Detecta administrador elevado (admin rights)
 */
function isElevatedAdmin() {
  if (os.platform() !== 'win32') return false;

  const output = safeExec('net session 2>&1');
  if (!output) return false;

  // Se net session funciona, tem privilégios admin
  return !output.toLowerCase().includes('access is denied');
}

// =============================================================================
// CORPORATE ENVIRONMENT DETECTION
// =============================================================================

/**
 * Executa todas as heurísticas e determina se é ambiente corporativo
 *
 * @returns {Object} Resultado da detecção
 */
function detectCorporateEnvironment() {
  const username = process.env.USERNAME || process.env.USER || 'unknown';
  const platform = os.platform();
  const isWindows = platform === 'win32';

  // Score system: quanto maior, mais provável ser corporativo
  let corporateScore = 0;
  const indicators = [];

  // Indicador 1: Username corporativo (+3 pontos)
  if (isCorporateUsername(username)) {
    corporateScore += 3;
    indicators.push(`username pattern: ${username}`);
  }

  // Indicador 2: Domínio Windows (+4 pontos - forte indicador)
  if (isInWindowsDomain()) {
    corporateScore += 4;
    indicators.push('Active Directory domain');
  }

  // Indicador 3: GPOs ativas (+3 pontos)
  if (hasActiveGPOs()) {
    corporateScore += 3;
    indicators.push('GPOs detected');
  }

  // Indicador 4: Não consegue criar .lock dirs (+2 pontos)
  if (!canCreateLockDir()) {
    corporateScore += 2;
    indicators.push('EPERM on lock creation');
  }

  // Indicador 5: Admin elevado mas com restrições (+1 ponto - paradoxo corporativo)
  if (isElevatedAdmin() && corporateScore > 0) {
    corporateScore += 1;
    indicators.push('elevated admin with restrictions');
  }

  // Classificação
  let classification;
  if (corporateScore >= 6) {
    classification = 'CORPORATE_HIGH_CONFIDENCE';
  } else if (corporateScore >= 3) {
    classification = 'CORPORATE_LIKELY';
  } else if (corporateScore >= 1) {
    classification = 'CORPORATE_POSSIBLE';
  } else {
    classification = 'PERSONAL_ENVIRONMENT';
  }

  return {
    isCorporate: corporateScore >= 3,
    score: corporateScore,
    classification,
    indicators,
    platform: isWindows ? 'Windows' : platform,
    username
  };
}

// =============================================================================
// MESSAGE FORMATTING
// =============================================================================

/**
 * Formata mensagem de aviso baseado na detecção
 */
function formatCorporateWarning(detection) {
  if (!detection.isCorporate) {
    // Ambiente pessoal - sem avisos
    return '';
  }

  const lines = [];

  // Header
  if (detection.classification === 'CORPORATE_HIGH_CONFIDENCE') {
    lines.push('🏢 AMBIENTE CORPORATIVO DETECTADO');
  } else {
    lines.push('🏢 Possível ambiente corporativo');
  }

  // Limitações conhecidas (token-efficient)
  const warnings = [];

  if (detection.indicators.includes('EPERM on lock creation')) {
    warnings.push('File locking pode falhar (EPERM)');
  }

  if (detection.indicators.includes('GPOs detected')) {
    warnings.push('GPOs podem bloquear operações');
  }

  if (warnings.length > 0) {
    lines.push(`⚠️  Limitações: ${warnings.join(', ')}`);
  }

  // Workaround disponível (apenas se EPERM detectado)
  if (detection.indicators.includes('EPERM on lock creation')) {
    lines.push('Workaround: ./fix-claude-permissions.ps1');
  }

  return lines.join('\n');
}

// =============================================================================
// MAIN
// =============================================================================

function main() {
  console.error('[DEBUG] corporate-detector: Iniciando detecção...');
  // GUARD: Só roda em Windows (corporativo é problema Windows-specific)
  if (os.platform() !== 'win32') {
    console.error('[DEBUG] corporate-detector: Não é Windows, skipando');
    outputJSON({
      continue: true,
      systemMessage: ''
    });
    process.exit(0);
  }

  // GUARD: Se está no ambiente remoto (Web), não há problema de GPO
  if (process.env.CLAUDE_CODE_REMOTE === 'true') {
    outputJSON({
      continue: true,
      systemMessage: ''
    });
    process.exit(0);
  }

  try {
    // Executar detecção
    const detection = detectCorporateEnvironment();
    console.error(`[DEBUG] corporate-detector: Detecção completa - isCorporate:${detection.isCorporate}, score:${detection.score}`);

    // Formatar mensagem
    const message = formatCorporateWarning(detection);

    // Output final
    outputJSON({
      continue: true,
      systemMessage: message
    });

  } catch (error) {
    // Erro durante detecção - não deve quebrar sessão
    outputJSON({
      continue: true,
      systemMessage: '' // Silent fail
    });
  }
}

// Executar
main();
