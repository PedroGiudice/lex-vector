#!/usr/bin/env node
// superpowers-activator.js - Auto-ativação inteligente das skills do superpowers
//
// Detecta contexto do prompt do usuário e ativa a skill apropriada:
// - brainstorming: Para refinar ideias e arquitetura
// - systematic-debugging: Para bugs e erros
// - test-driven-development: Para implementação de features
// - root-cause-tracing: Para investigar problemas profundos

const fs = require('fs');
const path = require('path');

// Palavras-chave para detectar necessidade de cada skill
const SKILL_TRIGGERS = {
  brainstorming: [
    'como deveria', 'qual a melhor forma', 'como fazer', 'como implementar',
    'design', 'arquitetura', 'abordagem', 'estratégia',
    'how should', "what's the best way", 'approach', 'strategy', 'design'
  ],

  'systematic-debugging': [
    'bug', 'erro', 'error', 'failing', 'broken', 'não funciona',
    'crash', 'exception', 'falha', 'problema', 'issue'
  ],

  'test-driven-development': [
    'implementar', 'implement', 'add feature', 'criar feature',
    'nova funcionalidade', 'new feature', 'desenvolver', 'develop'
  ],

  'root-cause-tracing': [
    '5 whys', 'root cause', 'causa raiz', 'por que', 'why is',
    'investigar', 'investigate', 'diagnose', 'diagnosticar'
  ]
};

// Ler último prompt do usuário (passado via stdin ou env var)
function getUserPrompt() {
  // Tentar ler de environment variable (setada pelo Claude Code)
  const envPrompt = process.env.CLAUDE_USER_PROMPT;
  if (envPrompt) {
    return envPrompt.toLowerCase();
  }

  // Fallback: ler stdin (se disponível)
  try {
    const stdin = fs.readFileSync(0, 'utf-8');
    return stdin.toLowerCase();
  } catch {
    return '';
  }
}

// Detectar qual skill deve ser ativada
function detectSkill(prompt) {
  for (const [skillName, keywords] of Object.entries(SKILL_TRIGGERS)) {
    for (const keyword of keywords) {
      if (prompt.includes(keyword.toLowerCase())) {
        return skillName;
      }
    }
  }

  return null;  // Nenhuma skill detectada
}

// Gerar mensagem de ativação da skill
function generateActivationMessage(skillName) {
  const skillPath = `.claude/skills/superpowers/skills/${skillName}/SKILL.md`;

  const messages = {
    brainstorming: `
🧠 **Superpowers: Brainstorming Activated**

Detected: Design/architecture question
Using: Collaborative refinement process
- Will ask clarifying questions (one at a time)
- Will explore 2-3 approaches with trade-offs
- Will present design in digestible sections (200-300 words)

Skill: ${skillPath}
`,

    'systematic-debugging': `
🔍 **Superpowers: Systematic Debugging Activated**

Detected: Bug/error investigation
Using: 4-phase debugging framework
⚠️  IRON LAW: NO FIXES WITHOUT ROOT CAUSE FIRST
- Phase 1: Root cause investigation
- Phase 2: Pattern analysis
- Phase 3: Hypothesis testing
- Phase 4: Implementation

Skill: ${skillPath}
`,

    'test-driven-development': `
✅ **Superpowers: Test-Driven Development Activated**

Detected: Feature implementation request
Using: Red-Green-Refactor cycle
📋 Process:
1. Write the test FIRST
2. Watch it FAIL (verify test works)
3. Write MINIMAL code to pass
4. Refactor if needed

Skill: ${skillPath}
`,

    'root-cause-tracing': `
🎯 **Superpowers: Root Cause Tracing Activated**

Detected: Deep investigation needed
Using: 5 Whys + systematic analysis
🔎 Will trace back from symptom to root cause
- Ask "Why?" repeatedly
- Identify true underlying issue
- Avoid symptom fixes

Skill: ${skillPath}
`
  };

  return messages[skillName] || '';
}

// Main
function main() {
  const userPrompt = getUserPrompt();

  if (!userPrompt) {
    // Nenhum prompt detectado - hook silencioso
    return;
  }

  const detectedSkill = detectSkill(userPrompt);

  if (detectedSkill) {
    console.log(generateActivationMessage(detectedSkill));
  }

  // Sempre retornar sucesso (hook não-bloqueante)
  process.exit(0);
}

main();
