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
    subtasks.push({
      name: 'Planejamento & Arquitetura',
      agente: 'planejamento-legal',
      skills: ['architecture-diagram-creator', 'feature-planning']
    });
    subtasks.push({
      name: 'Implementação Core',
      agente: 'desenvolvimento',
      skills: ['code-execution', 'test-driven-development']
    });
    subtasks.push({
      name: 'Testes & Quality Assurance',
      agente: 'qualidade-codigo',
      skills: ['code-auditor', 'test-driven-development']
    });
    subtasks.push({
      name: 'Documentação Técnica',
      agente: 'documentacao',
      skills: ['technical-doc-creator', 'flowchart-creator']
    });
  } else if (complexity === 'MEDIUM') {
    subtasks.push({
      name: 'Implementação',
      agente: 'desenvolvimento',
      skills: ['code-execution']
    });
    subtasks.push({
      name: 'Code Review',
      agente: 'qualidade-codigo',
      skills: ['code-auditor']
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
      return `${i + 1}. [${st.agente}] ${st.name}\n   Skills: ${st.skills.join(', ')}\n   Tools: ${toolsSummary}`;
    })
    .join('\n');
}

module.exports = { orchestrateAgents };
