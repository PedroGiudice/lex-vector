/**
 * lib/agent-orchestrator.js - Orquestração de agentes
 *
 * Substitui: invoke-legal-braniac-hybrid.js (parte de delegação)
 * Integração: Usa agent-tools-mapping.json para enriquecer sugestões
 */

const { getAgentToolsSummary } = require('./agent-mapping-loader');

async function orchestrateAgents(context, agentesConfig) {
  const prompt = context.prompt.toLowerCase();

  // Detecção de complexidade (expandida - triggers automáticos)
  const complexityKeywords = {
    HIGH: [
      // Arquitetura & Sistema
      'sistema', 'arquitetura', 'rag', 'cache distribuído', 'múltiplas camadas',
      'implementar sistema', 'design system', 'microservice',
      // Novos módulos/features grandes
      'novo módulo', 'new module', 'nova feature grande', 'major feature',
      'criar serviço', 'new service', 'breaking change',
      // Múltiplos componentes
      'múltiplos arquivos', 'vários componentes', 'multiple files',
      // Database & Schema
      'schema migration', 'database refactor', 'alter schema'
    ],
    MEDIUM: [
      // Escrever código novo
      'escrever', 'write', 'create', 'criar', 'develop', 'desenvolver',
      // Editar código existente (importante)
      'editar', 'edit', 'modificar', 'modify', 'alterar', 'change',
      // Revisar código
      'revisar', 'review', 'code review',
      // Refatorar
      'refatorar', 'refactor', 'reorganizar', 'restructure',
      // Features
      'adicionar feature', 'add feature', 'implementar', 'implement',
      'nova funcionalidade', 'new functionality',
      // Componentes
      'criar componente', 'new component', 'build component',
      // Código importante
      'código importante', 'critical code', 'core logic',
      // Testes
      'write tests', 'criar testes', 'test coverage'
    ],
    LOW: [
      'adicionar log', 'corrigir typo', 'atualizar readme', 'ajustar',
      'fix typo', 'update docs', 'comment'
    ]
  };

  // Detecção por keywords (prioriza HIGH → MEDIUM → LOW)
  let complexity = 'MEDIUM'; // DEFAULT: MEDIUM (para manter uniformidade)

  // Check HIGH first
  if (complexityKeywords.HIGH.some(kw => prompt.includes(kw))) {
    complexity = 'HIGH';
  }
  // Check LOW (only trivial tasks skip orchestration)
  else if (complexityKeywords.LOW.some(kw => prompt.includes(kw))) {
    complexity = 'LOW';
  }
  // Otherwise: MEDIUM (includes all MEDIUM keywords + anything not trivial)

  // Detecção adicional por padrões (MEDIUM → HIGH se múltiplos arquivos)
  if (complexity === 'MEDIUM') {
    // Check MEDIUM keywords explicitly
    const hasMediumKeyword = complexityKeywords.MEDIUM.some(kw => prompt.includes(kw));

    // Se menciona múltiplos arquivos/componentes → HIGH
    if (
      /(\d+|vários|múltiplos|several|multiple).*(arquivo|file|componente|component)/i.test(prompt) ||
      /novo.*(módulo|module|serviço|service)/i.test(prompt)
    ) {
      complexity = 'HIGH';
    }
    // Se não tem keyword MEDIUM nem LOW, mas também não é trivial → MEDIUM
    // (mantém MEDIUM para uniformidade)
  }

  if (complexity === 'LOW') {
    return null; // Não requer orquestração (apenas tarefas triviais)
  }

  // Decomposição baseada em complexidade
  const subtasks = [];

  if (complexity === 'HIGH') {
    // Skills são auto-injetadas via skill-content-injector.js (não pertencem a agents)
    subtasks.push({
      name: 'Planejamento & Arquitetura',
      agente: 'planejamento-legal'
    });
    subtasks.push({
      name: 'Implementação Core',
      agente: 'desenvolvimento'
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
    subtasks.push({
      name: 'Implementação',
      agente: 'desenvolvimento'
    });
    subtasks.push({
      name: 'Code Review',
      agente: 'qualidade-codigo'
    });
  }

  return {
    complexity,
    subtasks,
    plan: formatOrchestrationPlan(subtasks)
  };
}

function formatOrchestrationPlan(subtasks) {
  return subtasks
    .map((st, i) => {
      const toolsSummary = getAgentToolsSummary(st.agente);
      // Skills são auto-injetadas via skill-content-injector.js baseado no prompt
      // Não há "skills pertencendo a agents" - modelo incorreto do projeto anterior
      return `${i + 1}. [${st.agente}] ${st.name}\n   Tools: ${toolsSummary}`;
    })
    .join('\n');
}

module.exports = { orchestrateAgents };
