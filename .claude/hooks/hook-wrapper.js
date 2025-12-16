#!/usr/bin/env node
/**
 * hook-wrapper.js - Wrapper para tracking de execução de hooks
 *
 * Intercepta execução de hooks e registra:
 * - Timestamp de execução
 * - Status (success/error)
 * - Mensagens de erro (se houver)
 *
 * Uso: node hook-wrapper.js <caminho-do-hook-original.js>
 *
 * Exemplo:
 *   node .claude/hooks/hook-wrapper.js .claude/hooks/invoke-legal-braniac-hybrid.js
 */

const { spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

// Stub for removed last-used tracker (functionality deprecated)
const lastUsedTracker = {
  updateHook: () => {},
  updateOrchestrator: () => {}
};

/**
 * Main entry point
 */
async function main() {
  try {
    // O hook original é passado como argumento
    const hookPath = process.argv[2];

    if (!hookPath) {
      console.error('❌ hook-wrapper: Nenhum hook especificado');
      process.exit(1);
    }

    // Extrair nome do hook
    const hookName = path.basename(hookPath, '.js');

    // Determinar diretório do projeto
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

    // Arquivo de status
    const statusFile = path.join(projectDir, '.claude', 'statusline', 'hooks-status.json');

    // Registrar início da execução
    await updateHookStatus(statusFile, hookName, 'running', Date.now());

    // Read stdin first (to pass to child process)
    const stdinData = await readStdin();

    // Executar o hook original
    const result = await executeHook(hookPath, projectDir, stdinData);

    // Registrar resultado
    if (result.exitCode === 0) {
      await updateHookStatus(statusFile, hookName, 'success', Date.now(), result.stdout);

      // Atualizar last-used tracker
      lastUsedTracker.updateHook(hookName);

      // Se for o orchestrator, atualizar também
      if (hookName === 'invoke-legal-braniac-hybrid') {
        lastUsedTracker.updateOrchestrator();
      }
    } else {
      await updateHookStatus(statusFile, hookName, 'error', Date.now(), result.stderr, result.exitCode);
    }

    // Passar stdout do hook original para o Claude Code
    if (result.stdout) {
      process.stdout.write(result.stdout);
    }

    // Sair com o mesmo código do hook original
    process.exit(result.exitCode);

  } catch (error) {
    console.error('❌ hook-wrapper error:', error.message);
    process.exit(1);
  }
}

/**
 * Read stdin with timeout (non-blocking)
 */
function readStdin(timeout = 500) {
  return new Promise((resolve) => {
    let data = '';
    let hasData = false;

    const timer = setTimeout(() => {
      if (!hasData) resolve('');
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
      resolve(data);
    });
    process.stdin.on('error', () => {
      clearTimeout(timer);
      resolve('');
    });
  });
}

/**
 * Executa o hook original e captura output
 */
async function executeHook(hookPath, projectDir, stdinData) {
  return new Promise((resolve) => {
    let stdout = '';
    let stderr = '';

    // Executar hook como subprocesso
    // Use pipe for all stdio to avoid permission issues with stdin inheritance
    // Use absolute path to node to ensure it's found
    const child = spawn('/usr/bin/node', [hookPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: process.env,
      cwd: projectDir  // CRITICAL: Execute from project root, not .claude/hooks/
    });

    // Pass stdin data to child process
    if (stdinData) {
      child.stdin.write(stdinData);
    }
    child.stdin.end();

    // Capturar stdout
    child.stdout.on('data', (data) => {
      const output = data.toString();
      stdout += output;
    });

    // Capturar stderr
    child.stderr.on('data', (data) => {
      const output = data.toString();
      stderr += output;
    });

    // Quando terminar
    child.on('close', (exitCode) => {
      resolve({
        exitCode: exitCode || 0,
        stdout,
        stderr
      });
    });

    // Se houver erro no spawn
    child.on('error', (error) => {
      resolve({
        exitCode: 1,
        stdout: '',
        stderr: error.message
      });
    });
  });
}

/**
 * Atualiza arquivo de status dos hooks
 */
async function updateHookStatus(statusFile, hookName, status, timestamp, output = '', exitCode = 0) {
  try {
    // Criar diretório se não existir
    const dir = path.dirname(statusFile);
    await fs.mkdir(dir, { recursive: true });

    // Ler status atual (se existir)
    let data = {};
    try {
      const content = await fs.readFile(statusFile, 'utf8');
      data = JSON.parse(content);
    } catch {
      // Arquivo não existe ou está vazio - começar do zero
    }

    // Atualizar status do hook
    data[hookName] = {
      status,
      timestamp,
      lastRun: new Date(timestamp).toISOString(),
      exitCode: status === 'error' ? exitCode : 0
    };

    // Adicionar output/erro se houver
    if (output && output.trim()) {
      if (status === 'error') {
        data[hookName].error = output.trim();
      } else {
        data[hookName].output = output.substring(0, 500); // Limitar tamanho
      }
    }

    // Salvar arquivo
    await fs.writeFile(statusFile, JSON.stringify(data, null, 2), 'utf8');

  } catch (error) {
    // Não falhar se não conseguir salvar status
    console.error('⚠️ hook-wrapper: Erro ao salvar status:', error.message);
  }
}

// Executar
main();
