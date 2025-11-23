/**
 * lib/agent-orchestrator.js - Orquestração de agentes
 *
 * Substitui: invoke-legal-braniac-hybrid.js (parte de delegação)
 * Integração: Usa agent-tools-mapping.json para enriquecer sugestões
 */

const { getAgentToolsSummary } = require('./agent-mapping-loader');

async function orchestrateAgents(context, agentesConfig) {
  const prompt = context.prompt.toLowerCase();

  // Detecção de complexidade (simplificada)
  const complexityKeywords = {
    HIGH: ['sistema', 'arquitetura', 'rag', 'cache distribuído', 'múltiplas camadas', 'implementar sistema'],
    MEDIUM: ['refatorar', 'implementar', 'adicionar feature', 'criar componente'],
    LOW: ['adicionar log', 'corrigir typo', 'atualizar readme', 'fix', 'ajustar']
  };

  let complexity = 'LOW';
  for (const [level, keywords] of Object.entries(complexityKeywords)) {
    if (keywords.some(kw => prompt.includes(kw))) {
      complexity = level;
      break;
    }
  }

  if (complexity === 'LOW') {
    return null; // Não requer orquestração
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
