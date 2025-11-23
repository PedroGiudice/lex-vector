#!/usr/bin/env node

/**
 * add-triggers-to-yaml.js - Adiciona triggers ao YAML frontmatter das skills
 *
 * Lê description do YAML, extrai triggers contextuais, adiciona campo triggers: []
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');

const PROJECT_DIR = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const SKILLS_DIR = path.join(PROJECT_DIR, 'skills');
const CLAUDE_SKILLS_DIR = path.join(PROJECT_DIR, '.claude', 'skills');

// Stopwords expandidas (palavras comuns que não são triggers úteis)
const STOPWORDS = new Set([
  'this', 'that', 'with', 'your', 'for', 'and', 'the', 'you', 'need', 'want', 'have',
  'when', 'user', 'wants', 'uses', 'using', 'used', 'use', 'from', 'into', 'through',
  'before', 'after', 'during', 'while', 'about', 'over', 'under', 'between', 'within',
  'should', 'would', 'could', 'will', 'can', 'may', 'might', 'must', 'shall',
  'very', 'more', 'most', 'such', 'any', 'all', 'some', 'each', 'every', 'both',
  'creating', 'building', 'making', 'doing', 'getting', 'having', 'being'
]);

/**
 * Extrai triggers da description usando análise contextual
 */
function extractTriggersFromDescription(description, skillName) {
  const triggers = [];

  // 1. Skill name como trigger base (sem hífens)
  triggers.push(skillName.replace(/-/g, ' '));

  // 2. Extrair verbos de ação da description
  const actionVerbs = [
    'implement', 'create', 'build', 'design', 'plan', 'write', 'develop',
    'test', 'debug', 'fix', 'refactor', 'optimize', 'analyze', 'review',
    'document', 'architect', 'deploy', 'monitor', 'track', 'manage'
  ];

  const descLower = description.toLowerCase();
  for (const verb of actionVerbs) {
    if (descLower.includes(verb)) {
      triggers.push(verb);
    }
  }

  // 3. Extrair substantivos técnicos (palavras-chave de domínio)
  // Pattern: "use when [verb]ing [noun]" ou "for [noun]"
  const patterns = [
    /use when (?:implementing|creating|building|designing|planning|writing|developing) ([\w\s]+?)(?:\s+[-,.]|$)/i,
    /for ([\w\s]+?) (?:development|implementation|testing|debugging|documentation)/i,
    /(?:comprehensive|detailed|complete) ([\w\s]+?) (?:guide|analysis|documentation)/i
  ];

  for (const pattern of patterns) {
    const match = description.match(pattern);
    if (match && match[1]) {
      const phrase = match[1].trim().toLowerCase();
      const words = phrase.split(/\s+/).filter(w =>
        w.length > 3 &&
        !STOPWORDS.has(w) &&
        /^[a-z]+$/.test(w)
      );
      triggers.push(...words.slice(0, 2)); // Top 2 substantivos
    }
  }

  // 4. Extrair keywords específicos de tecnologia/domínio
  const techKeywords = [
    'backend', 'frontend', 'api', 'database', 'microservice', 'component',
    'route', 'controller', 'service', 'repository', 'middleware', 'hook',
    'test', 'tdd', 'debugging', 'security', 'performance', 'architecture',
    'documentation', 'diagram', 'flowchart', 'planning', 'refactoring',
    'code review', 'git', 'typescript', 'react', 'express', 'prisma'
  ];

  for (const keyword of techKeywords) {
    if (descLower.includes(keyword)) {
      triggers.push(keyword);
    }
  }

  // Remover duplicatas e limitar a 5-7 triggers
  return Array.from(new Set(triggers)).slice(0, 7);
}

/**
 * Adiciona triggers ao YAML frontmatter de um SKILL.md
 */
async function addTriggersToSkill(skillPath, skillName) {
  try {
    const content = await fs.readFile(skillPath, 'utf8');

    // Verificar se já tem YAML frontmatter
    const yamlMatch = content.match(/^---\s*\n([\s\S]*?)\n---/);
    if (!yamlMatch) {
      return { skillName, status: 'skip', reason: 'Sem YAML frontmatter' };
    }

    const yaml = yamlMatch[1];

    // Verificar se JÁ tem triggers ou keywords
    if (yaml.match(/^(?:triggers|keywords):/m)) {
      return { skillName, status: 'skip', reason: 'Já tem triggers/keywords' };
    }

    // Extrair description
    const descMatch = yaml.match(/description:\s*(.+?)(?:\n|$)/);
    if (!descMatch) {
      return { skillName, status: 'skip', reason: 'Sem description no YAML' };
    }

    const description = descMatch[1].trim();

    // Extrair triggers da description
    const triggers = extractTriggersFromDescription(description, skillName);

    // Criar novo YAML com triggers adicionados
    const triggersLine = `triggers: [${triggers.map(t => `"${t}"`).join(', ')}]`;
    const newYaml = yaml + '\n' + triggersLine;

    // Substituir YAML no conteúdo
    const newContent = content.replace(
      /^---\s*\n[\s\S]*?\n---/,
      `---\n${newYaml}\n---`
    );

    // Salvar arquivo atualizado
    await fs.writeFile(skillPath, newContent, 'utf8');

    return {
      skillName,
      status: 'updated',
      triggers,
      description: description.substring(0, 80) + '...'
    };

  } catch (error) {
    return {
      skillName,
      status: 'error',
      reason: error.message
    };
  }
}

/**
 * Processar diretório de skills
 */
async function processSkillsDirectory(dir, prefix = '') {
  const results = [];

  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (entry.name === 'skill-rules.json' || entry.name === 'lib') continue;

      const skillName = entry.name;
      const skillPath = path.join(dir, skillName, 'SKILL.md');

      if (!fsSync.existsSync(skillPath)) {
        results.push({ skillName: prefix + skillName, status: 'skip', reason: 'SKILL.md não encontrado' });
        continue;
      }

      const result = await addTriggersToSkill(skillPath, skillName);
      result.skillName = prefix + skillName;
      results.push(result);
    }

  } catch (error) {
    console.error(`[ERROR] Erro ao processar ${dir}: ${error.message}`);
  }

  return results;
}

/**
 * Main
 */
async function main() {
  console.error('=== Adicionando triggers ao YAML frontmatter ===\n');

  // Processar skills/
  console.error('[1/2] Processando skills/ ...');
  const customResults = await processSkillsDirectory(SKILLS_DIR, 'custom/');

  // Processar .claude/skills/
  console.error('\n[2/2] Processando .claude/skills/ ...');
  const managedResults = await processSkillsDirectory(CLAUDE_SKILLS_DIR, 'managed/');

  // Consolidar resultados
  const allResults = [...customResults, ...managedResults];

  const updated = allResults.filter(r => r.status === 'updated');
  const skipped = allResults.filter(r => r.status === 'skip');
  const errors = allResults.filter(r => r.status === 'error');

  // Output detalhado
  console.error('\n' + '='.repeat(80));
  console.error('RESULTADOS CONSOLIDADOS');
  console.error('='.repeat(80) + '\n');

  console.error(`✅ Atualizadas: ${updated.length}`);
  console.error(`⏭️  Puladas: ${skipped.length}`);
  console.error(`❌ Erros: ${errors.length}\n`);

  // Detalhes de skills atualizadas (para revisão)
  if (updated.length > 0) {
    console.error('─'.repeat(80));
    console.error('SKILLS ATUALIZADAS (revisar triggers):');
    console.error('─'.repeat(80) + '\n');

    for (const result of updated) {
      console.error(`📝 ${result.skillName}`);
      console.error(`   Triggers: ${result.triggers.join(', ')}`);
      console.error(`   Descrição: ${result.description}\n`);
    }
  }

  // Skills puladas (informativo)
  if (skipped.length > 0) {
    console.error('─'.repeat(80));
    console.error('SKILLS PULADAS:');
    console.error('─'.repeat(80) + '\n');

    const reasons = {};
    for (const result of skipped) {
      reasons[result.reason] = reasons[result.reason] || [];
      reasons[result.reason].push(result.skillName);
    }

    for (const [reason, skills] of Object.entries(reasons)) {
      console.error(`${reason} (${skills.length}):`);
      skills.forEach(s => console.error(`  - ${s}`));
      console.error('');
    }
  }

  // Erros (se houver)
  if (errors.length > 0) {
    console.error('─'.repeat(80));
    console.error('ERROS:');
    console.error('─'.repeat(80) + '\n');

    for (const result of errors) {
      console.error(`❌ ${result.skillName}: ${result.reason}`);
    }
    console.error('');
  }

  console.error('='.repeat(80));
  console.error(`✅ Processo concluído! ${updated.length} skills atualizadas.`);
  console.error('='.repeat(80));
}

// Execute
main().catch(error => {
  console.error(`\n❌ ERRO FATAL: ${error.message}`);
  process.exit(1);
});
