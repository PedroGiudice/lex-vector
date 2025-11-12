#!/usr/bin/env node
/**
 * SKILL AUTO-ACTIVATION HOOK
 *
 * Executa em: UserPromptSubmit (antes do Claude processar prompt)
 * Função: Analisa prompt do usuário e injeta skills relevantes no contexto
 *
 * Baseado em: diet103/claude-code-infrastructure-showcase
 */

import * as fs from 'fs';
import * as path from 'path';

interface SkillConfig {
  type: string;
  enforcement: string;
  priority: string;
  description: string;
  promptTriggers?: {
    keywords?: string[];
    intentPatterns?: string[];
  };
  filePathTriggers?: {
    patterns?: string[];
  };
  relatedSkills?: string[];
}

interface SkillRules {
  description: string;
  version: string;
  context: any;
  skills: Record<string, SkillConfig>;
}

interface HookInput {
  prompt: string;
  session_id: string;
  cwd: string;
  permission_mode: string;
  hook_event_name: string;
}

// Ler input via stdin
const input = JSON.parse(fs.readFileSync(0, 'utf8')) as HookInput;
const userPrompt = input.prompt.toLowerCase();

// Ler skill-rules.json
const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const rulesPath = path.join(projectDir, '.claude', 'skills', 'skill-rules.json');

if (!fs.existsSync(rulesPath)) {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}

const skillRules: SkillRules = JSON.parse(fs.readFileSync(rulesPath, 'utf8'));

// Array para armazenar skills sugeridas
const suggestedSkills: Array<{ name: string; priority: string; reason: string }> = [];

// Verificar cada skill
for (const [skillName, config] of Object.entries(skillRules.skills)) {
  let matched = false;
  let matchReason = '';

  // Verificar keywords
  if (config.promptTriggers?.keywords) {
    for (const keyword of config.promptTriggers.keywords) {
      if (userPrompt.includes(keyword.toLowerCase())) {
        matched = true;
        matchReason = `keyword: "${keyword}"`;
        break;
      }
    }
  }

  // Verificar intent patterns (regex)
  if (!matched && config.promptTriggers?.intentPatterns) {
    for (const pattern of config.promptTriggers.intentPatterns) {
      try {
        const regex = new RegExp(pattern, 'i');
        if (regex.test(userPrompt)) {
          matched = true;
          matchReason = `pattern: "${pattern}"`;
          break;
        }
      } catch (e) {
        // Ignorar padrões regex inválidos
      }
    }
  }

  if (matched) {
    suggestedSkills.push({
      name: skillName,
      priority: config.priority,
      reason: matchReason
    });
  }
}

// Ordenar por prioridade (critical > high > medium > low)
const priorityOrder: Record<string, number> = {
  'critical': 0,
  'high': 1,
  'medium': 2,
  'low': 3
};

suggestedSkills.sort((a, b) =>
  priorityOrder[a.priority] - priorityOrder[b.priority]
);

// Gerar output
if (suggestedSkills.length > 0) {
  const skillList = suggestedSkills
    .slice(0, 5)  // Máximo 5 skills para não sobrecarregar
    .map(s => `- ${s.name} (${s.priority})`)
    .join('\n');

  const injection = `\n\n[SYSTEM CONTEXT: Relevant skills detected for this query]\n${skillList}\n\nConsider using these skills for optimal response quality.\n`;

  console.log(JSON.stringify({
    continue: true,
    systemMessage: injection,
    suppressOutput: false
  }));
} else {
  // Nenhuma skill detectada - prosseguir normalmente
  console.log(JSON.stringify({ continue: true }));
}

process.exit(0);
