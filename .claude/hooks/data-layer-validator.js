#!/usr/bin/env node
/**
 * data-layer-validator.js - Valida separação CODE/ENV/DATA
 * ASYNC | TIMEOUT 400ms | RUN-ONCE GUARD
 *
 * Propósito: Valida que CODE, ENV e DATA estão separados corretamente (DISASTER_HISTORY.md)
 * Valor: Previne repetição do desastre de 3 dias (código no E:\)
 * Riscos: Nenhum (apenas lê caminhos e .gitignore)
 */

const fs = require('fs').promises;
const path = require('path');

// ============================================================================
// RUN-ONCE GUARD
// ============================================================================
if (process.env.CLAUDE_DATA_LAYER_VALIDATED === 'true') {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}
process.env.CLAUDE_DATA_LAYER_VALIDATED = 'true';

// ============================================================================
// LÓGICA PRINCIPAL (ASYNC)
// ============================================================================
async function validateLayers() {
  console.error('[DEBUG] data-layer-validator: Iniciando validação de camadas...');
  try {
    const cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd();

    // ========================================================================
    // RULE 1: Código deve estar em C:\ ou /home (não em drives externos)
    // ========================================================================
    const isWindows = process.platform === 'win32';

    if (isWindows) {
      // Windows: Detectar drives externos (D:\ a Z:\, exceto C:\)
      const isOnExternalDrive = /^[D-Z]:[\\\/]/i.test(cwd);

      if (isOnExternalDrive) {
        return {
          continue: true,
          systemMessage:
            '🚨 VIOLAÇÃO RULE_001: Código detectado em drive externo!\n' +
            `Localização: ${cwd}\n` +
            '⚠️ DESASTRE IMINENTE - Ver DISASTER_HISTORY.md\n' +
            'Ação: Mova código para C:\\claude-work\\repos\\ IMEDIATAMENTE\n'
        };
      }
    } else {
      // Linux/macOS: Detectar /mnt ou /media (montagens externas)
      const isOnExternalMount = /^\/(mnt|media)\//.test(cwd);

      if (isOnExternalMount) {
        return {
          continue: true,
          systemMessage:
            '🚨 VIOLAÇÃO RULE_001: Código detectado em montagem externa!\n' +
            `Localização: ${cwd}\n` +
            '⚠️ Ver DISASTER_HISTORY.md\n' +
            'Ação: Mova código para /home/$USER/ ou /opt/\n'
        };
      }
    }

    // ========================================================================
    // RULE 2: .venv deve estar em .gitignore
    // ========================================================================
    const gitignorePath = path.join(cwd, '.gitignore');

    try {
      const gitignoreContent = await fs.readFile(gitignorePath, 'utf8');
      const hasVenvIgnore = gitignoreContent.includes('.venv') ||
                           gitignoreContent.includes('venv/') ||
                           gitignoreContent.includes('*.venv');

      if (!hasVenvIgnore) {
        return {
          continue: true,
          systemMessage:
            '⚠️ VIOLAÇÃO RULE_002: .venv não está em .gitignore!\n' +
            'Adicione ao .gitignore:\n' +
            '   .venv/\n' +
            '   venv/\n' +
            '   __pycache__/\n' +
            '   *.pyc\n'
        };
      }
    } catch {
      // .gitignore não existe (OK se não for repo Git)
    }

    // ========================================================================
    // RULE 3: Data dir deve estar fora do repo
    // ========================================================================
    const dataDir = process.env.CLAUDE_DATA_ROOT || (isWindows ? 'E:/claude-code-data' : '/data/claude-code-data');

    // Normalizar paths para comparação
    const normalizedCwd = path.resolve(cwd);
    const normalizedDataDir = path.resolve(dataDir);

    const isDataInsideRepo = normalizedDataDir.startsWith(normalizedCwd);

    if (isDataInsideRepo) {
      return {
        continue: true,
        systemMessage:
          '⚠️ VIOLAÇÃO RULE_003: Data dir dentro do repositório!\n' +
          `Repo: ${normalizedCwd}\n` +
          `Data dir: ${normalizedDataDir}\n` +
          'Configure: CLAUDE_DATA_ROOT para localização externa\n' +
          'Exemplo Windows: set CLAUDE_DATA_ROOT=E:\\claude-code-data\n' +
          'Exemplo Linux: export CLAUDE_DATA_ROOT=/data/claude-code-data\n'
      };
    }

    // ========================================================================
    // RULE 4: Verificar se .gitignore exclui dados (se existir pasta de dados)
    // ========================================================================
    try {
      const gitignoreContent = await fs.readFile(gitignorePath, 'utf8');
      const hasDataIgnore = gitignoreContent.includes('claude-code-data') ||
                           gitignoreContent.includes('*.csv') ||
                           gitignoreContent.includes('*.log');

      // Verificar se existe pasta suspeita de dados no repo
      const suspiciousDataDirs = ['data/', 'downloads/', 'logs/', 'outputs/'];
      const warnings = [];

      for (const dir of suspiciousDataDirs) {
        const dirPath = path.join(cwd, dir);
        try {
          await fs.access(dirPath);
          // Diretório existe - verificar se está no .gitignore
          if (!gitignoreContent.includes(dir) && !gitignoreContent.includes(dir.replace('/', ''))) {
            warnings.push(`${dir} existe mas NÃO está em .gitignore`);
          }
        } catch {
          // Diretório não existe (OK)
        }
      }

      if (warnings.length > 0) {
        return {
          continue: true,
          systemMessage:
            '⚠️ VIOLAÇÃO RULE_004: Diretórios de dados não ignorados pelo Git!\n' +
            warnings.join('\n') + '\n' +
            'Adicione ao .gitignore para evitar commit acidental de dados\n'
        };
      }
    } catch {
      // .gitignore não existe (já verificado antes)
    }

    // ========================================================================
    // ✅ TUDO OK
    // ========================================================================
    return { continue: true };
  } catch (error) {
    // Graceful degradation
    return { continue: true };
  }
}

// ============================================================================
// TIMEOUT WRAPPER
// ============================================================================
async function mainWithTimeout() {
  const TIMEOUT_MS = 400;

  const timeout = new Promise(resolve =>
    setTimeout(() => resolve({ continue: true }), TIMEOUT_MS)
  );

  const result = await Promise.race([validateLayers(), timeout]);
  console.log(JSON.stringify(result));
}

// ============================================================================
// EXECUÇÃO
// ============================================================================
mainWithTimeout().catch(() => {
  // Fallback final: Se tudo falhar, retornar JSON vazio
  console.log(JSON.stringify({ continue: true }));
});
