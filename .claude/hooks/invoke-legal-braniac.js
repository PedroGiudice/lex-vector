#!/usr/bin/env node
/**
 * Legal-Braniac SessionStart Hook
 *
 * Invoca o agente Legal-Braniac no início de cada sessão (Claude Code Web)
 * Realiza auto-discovery de agentes e skills disponíveis
 *
 * Funcionalidades:
 * - Auto-discovery de agentes em .claude/agents/
 * - Auto-discovery de skills em skills/
 * - Detecção de ambiente (Web vs CLI, Corporate vs Normal)
 * - Output token-efficient
 *
 * @version 1.0.0
 * @date 2025-11-13
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

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
 * Verifica se um diretório existe
 */
function dirExists(dirPath) {
  try {
    const stat = fs.statSync(dirPath);
    return stat.isDirectory();
  } catch (error) {
    return false;
  }
}

/**
 * Verifica se um arquivo existe
 */
function fileExists(filePath) {
  try {
    const stat = fs.statSync(filePath);
    return stat.isFile();
  } catch (error) {
    return false;
  }
}

// =============================================================================
// AUTO-DISCOVERY: AGENTES
// =============================================================================

/**
 * Descobre agentes disponíveis em .claude/agents/
 *
 * @param {string} projectDir - Diretório raiz do projeto
 * @returns {Array<Object>} Lista de agentes descobertos
 */
function discoverAgentes(projectDir) {
  const agentsDir = path.join(projectDir, '.claude', 'agents');

  if (!dirExists(agentsDir)) {
    return [];
  }

  try {
    const files = fs.readdirSync(agentsDir);

    return files
      .filter(f => f.endsWith('.md'))
      .filter(f => f !== 'legal-braniac.md') // Excluir self-reference
      .map(f => {
        const nome = f.replace('.md', '');
        const filePath = path.join(agentsDir, f);

        // Extrair primeira linha (geralmente título com especialidade)
        let especialidade = 'Agente especializado';
        try {
          const content = fs.readFileSync(filePath, 'utf8');
          const lines = content.split('\n');

          // Procurar linha "**Papel**:" ou similar
          const papelLine = lines.find(l => l.includes('**Papel**:') || l.includes('**Domínio**:'));
          if (papelLine) {
            especialidade = papelLine.split(':')[1]?.trim() || especialidade;
            // Truncar se muito longo (token efficiency)
            if (especialidade.length > 50) {
              especialidade = especialidade.substring(0, 47) + '...';
            }
          }
        } catch (readError) {
          // Fallback: usar nome do arquivo
        }

        return {
          nome,
          especialidade,
          path: `.claude/agents/${f}`
        };
      })
      .sort((a, b) => a.nome.localeCompare(b.nome)); // Ordem alfabética
  } catch (error) {
    // Em caso de erro, retornar array vazio (graceful degradation)
    return [];
  }
}

// =============================================================================
// AUTO-DISCOVERY: SKILLS
// =============================================================================

/**
 * Descobre skills disponíveis em skills/
 *
 * @param {string} projectDir - Diretório raiz do projeto
 * @returns {Array<Object>} Lista de skills descobertas
 */
function discoverSkills(projectDir) {
  const skillsDir = path.join(projectDir, 'skills');

  if (!dirExists(skillsDir)) {
    return [];
  }

  try {
    const dirs = fs.readdirSync(skillsDir);

    return dirs
      .filter(d => {
        const skillPath = path.join(skillsDir, d);
        const stat = fs.statSync(skillPath);
        // Deve ser diretório E ter SKILL.md
        return stat.isDirectory() && fileExists(path.join(skillPath, 'SKILL.md'));
      })
      .map(d => {
        const skillPath = path.join(skillsDir, d, 'SKILL.md');

        // Extrair descrição (primeira linha após título)
        let descricao = 'Skill disponível';
        try {
          const content = fs.readFileSync(skillPath, 'utf8');
          const lines = content.split('\n').filter(l => l.trim().length > 0);

          // Procurar linha "description:" ou segunda linha
          const descLine = lines.find(l => l.includes('description:'));
          if (descLine) {
            descricao = descLine.split(':')[1]?.trim() || descricao;
          } else if (lines.length > 1) {
            // Fallback: segunda linha (geralmente descrição)
            descricao = lines[1].replace(/^#+\s*/, '').trim();
          }

          // Truncar (token efficiency)
          if (descricao.length > 60) {
            descricao = descricao.substring(0, 57) + '...';
          }
        } catch (readError) {
          // Fallback
        }

        return {
          nome: d,
          descricao,
          path: `skills/${d}/SKILL.md`
        };
      })
      .sort((a, b) => a.nome.localeCompare(b.nome)); // Ordem alfabética
  } catch (error) {
    return [];
  }
}

// =============================================================================
// DETECÇÃO DE AMBIENTE
// =============================================================================

/**
 * Detecta características do ambiente de execução
 *
 * @returns {Object} Informações sobre o ambiente
 */
function detectEnvironment() {
  const isRemote = process.env.CLAUDE_CODE_REMOTE === 'true';
  const isWindows = os.platform() === 'win32';
  const username = process.env.USERNAME || process.env.USER || 'unknown';

  // Heurística: ambientes corporativos geralmente têm usuários específicos
  // (CMR, nomes curtos, etc) e não "pedro" ou nomes pessoais longos
  const possibleCorporate = isWindows && (
    username.length <= 3 ||  // Siglas (CMR, ABC)
    /^[A-Z]{2,4}$/.test(username)  // Todas maiúsculas, 2-4 chars
  );

  return {
    isRemote,
    isWindows,
    username,
    possibleCorporate
  };
}

// =============================================================================
// FORMATAÇÃO DE MENSAGEM
// =============================================================================

/**
 * Gera mensagem compacta para injeção no contexto
 * Token-efficient: máximo 3-4 linhas
 *
 * @param {Array} agentes - Lista de agentes descobertos
 * @param {Array} skills - Lista de skills descobertas
 * @param {Object} env - Informações de ambiente
 * @returns {string} Mensagem formatada
 */
function formatMessage(agentes, skills, env) {
  const lines = [];

  // Linha 1: Header do Legal-Braniac
  lines.push('🧠 Legal-Braniac: Orquestrador ativo');

  // Linha 2: Agentes e Skills (contagem + primeiros nomes)
  const agentesNomes = agentes.slice(0, 3).map(a => a.nome).join(', ');
  const agentesExtra = agentes.length > 3 ? `, +${agentes.length - 3}` : '';
  lines.push(`📋 Agentes (${agentes.length}): ${agentesNomes}${agentesExtra}`);

  const skillsNomes = skills.slice(0, 3).map(s => s.nome).join(', ');
  const skillsExtra = skills.length > 3 ? `, +${skills.length - 3}` : '';
  lines.push(`🛠️  Skills (${skills.length}): ${skillsNomes}${skillsExtra}`);

  // Linha 3: Avisos importantes (se houver)
  const warnings = [];
  if (env.possibleCorporate) {
    warnings.push('🏢 Env corporativo detectado');
  }
  // Warning APENAS para CLI Windows corporativo (risco real de EPERM)
  if (!env.isRemote && env.isWindows && env.possibleCorporate) {
    warnings.push('⚠️  CLI corporativo - EPERM possível');
  }

  if (warnings.length > 0) {
    lines.push(warnings.join(' | '));
  }

  return lines.join('\n');
}

// =============================================================================
// MAIN
// =============================================================================

function main() {
  // STRATEGY: Usar CLAUDE_PROJECT_DIR se disponível, senão process.cwd()
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

  // GUARD 1: Verificar se é projeto com Legal-Braniac
  const legalBraniacPath = path.join(projectDir, '.claude', 'agents', 'legal-braniac.md');

  if (!fileExists(legalBraniacPath)) {
    // Não é projeto com Legal-Braniac - skip silenciosamente
    // (Permite portabilidade - hook não quebra outros projetos)
    outputJSON({
      continue: true,
      systemMessage: ''
    });
    process.exit(0);
  }

  // GUARD 2: Ambiente CLI Windows CORPORATIVO (onde hooks causam freeze)
  const env = detectEnvironment();
  if (!env.isRemote && env.isWindows && env.possibleCorporate) {
    // CLI Windows corporativo detectado - skip para evitar EPERM loop
    // Silent skip - usuário já informado via DISASTER_HISTORY DIA 4
    outputJSON({
      continue: true,
      systemMessage: ''
    });
    process.exit(0);
  }

  // AUTO-DISCOVERY
  try {
    const agentes = discoverAgentes(projectDir);
    const skills = discoverSkills(projectDir);

    // Validação: deve ter pelo menos 1 agente ou 1 skill para ser útil
    if (agentes.length === 0 && skills.length === 0) {
      outputJSON({
        continue: true,
        systemMessage: '🧠 Legal-Braniac: Ativo (sem agentes/skills descobertos ainda)'
      });
      process.exit(0);
    }

    // Formatação de mensagem token-efficient
    const message = formatMessage(agentes, skills, env);

    // Output final
    outputJSON({
      continue: true,
      systemMessage: message
    });

  } catch (error) {
    // Erro durante auto-discovery - não deve quebrar sessão
    // Fallback graceful
    outputJSON({
      continue: true,
      systemMessage: `🧠 Legal-Braniac: Erro durante auto-discovery (${error.message})`
    });
  }
}

// Executar
main();
