/**
 * lib/agent-orchestrator.js - Orquestração de agentes (v3.1 - Agent-Aware)
 *
 * MUDANÇA v3.1: Detecta keywords para sugerir agentes ESPECÍFICOS
 * - Refatoração → code-refactor-master
 * - Planejamento → planejamento-legal ou plan-reviewer
 * - Documentação → documentation-architect
 * - Debugging → auto-error-resolver
 * - etc.
 *
 * FILOSOFIA: "Right Agent for the Right Task"
 * - Mapeia keywords para agentes especializados
 * - Fallback para desenvolvimento apenas quando não há match específico
 */

const { getAgentToolsSummary } = require('./agent-mapping-loader');

// ============================================================================
// MAPEAMENTO: Keywords → Agentes Específicos
// ============================================================================
const AGENT_KEYWORDS = {
  'code-refactor-master': [
    'refactor', 'refatorar', 'refatoração', 'reorganizar', 'reorganize',
    'reestruturar', 'restructure', 'quebrar em', 'break down', 'split',
    'extrair componente', 'extract component', 'modularizar', 'modularize'
  ],
  'planejamento-legal': [
    'planejar', 'plan', 'arquitetura', 'architecture', 'design',
    'projetar', 'estruturar', 'roadmap'
  ],
  'plan-reviewer': [
    'revisar plano', 'review plan', 'validar plano', 'validate plan',
    'aprovar plano', 'approve plan'
  ],
  'documentation-architect': [
    'documentar', 'document', 'documentação', 'documentation',
    'readme', 'wiki', 'api docs'
  ],
  'qualidade-codigo': [
    'code review', 'revisão de código', 'auditoria', 'audit',
    'qualidade', 'quality', 'security review', 'vulnerabilidade'
  ],
  'auto-error-resolver': [
    'erro', 'error', 'bug', 'fix', 'corrigir', 'resolver',
    'typescript error', 'compilation error'
  ],
  'web-research-specialist': [
    'pesquisar', 'research', 'buscar informação', 'search for',
    'investigar', 'investigate'
  ],
  'frontend-error-fixer': [
    'frontend error', 'react error', 'build error', 'bundle error',
    'erro de frontend', 'erro react'
  ]
};

/**
 * Detecta qual agente específico deve ser sugerido baseado no prompt
 * @returns {string|null} Nome do agente ou null se não encontrar match
 */
function detectSpecificAgent(prompt) {
  const promptLower = prompt.toLowerCase();

  for (const [agent, keywords] of Object.entries(AGENT_KEYWORDS)) {
    for (const keyword of keywords) {
      // Word boundary para keywords curtas, substring para longas
      if (keyword.length <= 4) {
        const regex = new RegExp(`\\b${keyword}\\b`, 'i');
        if (regex.test(prompt)) {
          return agent;
        }
      } else if (promptLower.includes(keyword.toLowerCase())) {
        return agent;
      }
    }
  }

  return null;
}

async function orchestrateAgents(context, agentesConfig) {
  const prompt = context.prompt.toLowerCase();

  // ============================================================================
  // WHITELIST DE TAREFAS TRIVIAIS (Não requerem orquestração)
  // ============================================================================
  const TRIVIAL_TASKS = [
    // Git operations simples (consulta)
    'git status', 'git log', 'git diff', 'git show', 'git branch',

    // File operations básicas (copiar/mover/deletar SEM lógica)
    'copiar arquivo', 'copy file', 'colar', 'paste',
    'mover arquivo', 'move file', 'remover arquivo', 'delete file',
    'renomear arquivo', 'rename file',

    // Leitura/visualização pura
    'mostrar', 'show', 'listar', 'list', 'ls', 'ver', 'view',
    'cat ', 'ler arquivo', 'read file', 'abrir', 'open',

    // Informação/consulta (não-ação)
    'onde está', 'where is', 'qual é o', 'what is the',
    'como funciona', 'how does', 'o que faz', 'what does',
    'explicar como', 'explain how',

    // Typos (qualquer contexto)
    'typo', 'erro de digitação', 'spelling error',
    'fix typo', 'corrigir typo', 'corrigir erro de digitação',

    // Comandos de ajuda
    'como usar', 'how to use', 'help', 'ajuda'
  ];

  // ============================================================================
  // KEYWORDS DE ALTA COMPLEXIDADE (Sempre HIGH)
  // ============================================================================
  const HIGH_COMPLEXITY = [
    // Arquitetura & Sistema
    'sistema', 'system', 'arquitetura', 'architecture',
    'design system', 'microservice', 'microsserviço',

    // Múltiplos componentes/arquivos
    'múltiplos arquivos', 'multiple files', 'vários arquivos', 'several files',
    'múltiplos componentes', 'multiple components', 'vários componentes',

    // Novos módulos/serviços
    'novo módulo', 'new module', 'novo serviço', 'new service',
    'criar módulo', 'create module', 'criar serviço', 'create service',

    // Database & Schema
    'migration', 'migração', 'schema', 'database refactor',
    'alter table', 'create table', 'drop table',

    // Breaking changes
    'breaking change', 'mudança drástica', 'refatoração completa',
    'complete refactor', 'reescrever', 'rewrite',

    // Features grandes
    'nova feature grande', 'major feature', 'epic',
    'implementar sistema de', 'implement system for',

    // Integração de múltiplos sistemas
    'integrar com', 'integrate with', 'conectar com', 'connect to',
    'sincronizar com', 'sync with'
  ];

  // ============================================================================
  // DETECÇÃO DE COMPLEXIDADE
  // ============================================================================

  // 1. Check TRIVIAL first (whitelist restrita)
  const isTrivial = TRIVIAL_TASKS.some(task => prompt.includes(task));
  if (isTrivial) {
    return null; // Não requer orquestração
  }

  // 2. Check HIGH complexity (patterns conhecidos)
  const isHigh = HIGH_COMPLEXITY.some(kw => prompt.includes(kw));

  // 3. Padrões regex para HIGH (múltiplos arquivos, etc)
  const multipleFilesPattern = /(\d+|vários|múltiplos|several|multiple).*(arquivo|file|componente|component)/i;
  const newModulePattern = /novo.*(módulo|module|serviço|service)/i;
  const isHighByPattern = multipleFilesPattern.test(prompt) || newModulePattern.test(prompt);

  let complexity = 'MEDIUM'; // DEFAULT: Tudo que não é trivial → orquestra

  if (isHigh || isHighByPattern) {
    complexity = 'HIGH';
  }

  // ============================================================================
  // DETECÇÃO DE AGENTE ESPECÍFICO (v3.1)
  // ============================================================================
  const specificAgent = detectSpecificAgent(context.prompt);

  // ============================================================================
  // DECOMPOSIÇÃO BASEADA EM COMPLEXIDADE + AGENTE ESPECÍFICO
  // ============================================================================
  const subtasks = [];

  if (complexity === 'HIGH') {
    // Tarefas complexas: planejamento + implementação + qualidade + docs
    subtasks.push({
      name: 'Planejamento & Arquitetura',
      agente: 'planejamento-legal'
    });
    subtasks.push({
      name: 'Implementação Core',
      agente: specificAgent || 'desenvolvimento'  // Usa agente específico se detectado
    });
    subtasks.push({
      name: 'Testes & Quality Assurance',
      agente: 'qualidade-codigo'
    });
    subtasks.push({
      name: 'Documentação Técnica',
      agente: 'documentacao'
    });
  } else if (complexity === 'MEDIUM') {
    // MUDANÇA v3.1: Se detectou agente específico, usa ELE como principal
    if (specificAgent) {
      subtasks.push({
        name: getAgentTaskName(specificAgent),
        agente: specificAgent
      });
      // Adiciona code review apenas se não for já um agente de qualidade
      if (specificAgent !== 'qualidade-codigo') {
        subtasks.push({
          name: 'Code Review',
          agente: 'qualidade-codigo'
        });
      }
    } else {
      // Fallback: comportamento original
      subtasks.push({
        name: 'Implementação',
        agente: 'desenvolvimento'
      });
      subtasks.push({
        name: 'Code Review',
        agente: 'qualidade-codigo'
      });
    }
  }

  return {
    complexity,
    specificAgent,  // Incluir no retorno para debug
    subtasks,
    plan: formatOrchestrationPlan(subtasks)
  };
}

/**
 * Retorna nome da tarefa baseado no agente
 */
function getAgentTaskName(agent) {
  const taskNames = {
    'code-refactor-master': 'Refatoração de Código',
    'planejamento-legal': 'Planejamento & Arquitetura',
    'plan-reviewer': 'Revisão de Plano',
    'documentation-architect': 'Documentação',
    'qualidade-codigo': 'Auditoria & Code Review',
    'auto-error-resolver': 'Resolução de Erros',
    'web-research-specialist': 'Pesquisa',
    'frontend-error-fixer': 'Correção de Erros Frontend',
    'desenvolvimento': 'Implementação'
  };
  return taskNames[agent] || 'Execução';
}

function formatOrchestrationPlan(subtasks) {
  return subtasks
    .map((st, i) => {
      const toolsSummary = getAgentToolsSummary(st.agente);
      return `${i + 1}. [${st.agente}] ${st.name}\n   Tools: ${toolsSummary}`;
    })
    .join('\n');
}

module.exports = { orchestrateAgents };
