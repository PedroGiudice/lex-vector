#!/usr/bin/env node

/**
 * sync-skill-rules.js - Auto-sync de skills físicas para skill-rules.json
 *
 * Escaneia skills/ e .claude/skills/ e atualiza skill-rules.json automaticamente
 * Extrai triggers de YAML frontmatter ou infere de description/name
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');

const PROJECT_DIR = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const SKILLS_DIR = path.join(PROJECT_DIR, 'skills');
const CLAUDE_SKILLS_DIR = path.join(PROJECT_DIR, '.claude', 'skills');
const RULES_PATH = path.join(PROJECT_DIR, '.claude', 'skills', 'skill-rules.json');

/**
 * Extrai triggers de SKILL.md (YAML frontmatter OBRIGATÓRIO)
 *
 * REGRA: Triggers DEVEM estar no YAML frontmatter - sem inferência automática
 */
async function extractTriggersFromSkill(skillPath, skillName) {
  try {
    const content = await fs.readFile(skillPath, 'utf8');

    // YAML frontmatter é OBRIGATÓRIO
    const yamlMatch = content.match(/^---\s*\n([\s\S]*?)\n---/);
    if (!yamlMatch) {
      throw new Error(`YAML frontmatter ausente - triggers OBRIGATÓRIOS`);
    }

    const yaml = yamlMatch[1];

    // Extrair triggers (prioridade 1)
    const triggersMatch = yaml.match(/triggers:\s*\[(.*?)\]/);
    if (triggersMatch) {
      const triggers = triggersMatch[1]
        .split(',')
        .map(t => t.trim().replace(/['"]/g, ''))
        .filter(t => t.length > 0);

      if (triggers.length === 0) {
        throw new Error(`triggers: [] vazio - pelo menos 1 trigger necessário`);
      }

      return triggers;
    }

    // Extrair keywords (prioridade 2 - fallback)
    const keywordsMatch = yaml.match(/keywords:\s*\[(.*?)\]/);
    if (keywordsMatch) {
      const keywords = keywordsMatch[1]
        .split(',')
        .map(t => t.trim().replace(/['"]/g, ''))
        .filter(t => t.length > 0);

      if (keywords.length === 0) {
        throw new Error(`keywords: [] vazio - pelo menos 1 keyword necessário`);
      }

      return keywords;
    }

    // NENHUM trigger encontrado → ERRO
    throw new Error(`Nem 'triggers' nem 'keywords' encontrados no YAML frontmatter`);

  } catch (error) {
    console.error(`❌ ${skillName}: ${error.message}`);
    return null; // Retornar null = skill será IGNORADA (não adicionar ao skill-rules.json)
  }
}

/**
 * Inferir priority baseado em nome/categoria
 */
function inferPriority(skillName, content) {
  // CRITICAL: Skills de qualidade/segurança/testes
  if (
    skillName.match(/test|quality|security|audit|debug|error/) ||
    content.match(/critical|security|testing|debugging/i)
  ) {
    return 'critical';
  }

  // HIGH: Skills de desenvolvimento/arquitetura
  if (
    skillName.match(/develop|architect|design|plan|implement/) ||
    content.match(/development|architecture|planning|implementation/i)
  ) {
    return 'high';
  }

  // MEDIUM: Skills de documentação/review/refactor
  if (
    skillName.match(/document|review|refactor|improve/) ||
    content.match(/documentation|review|refactoring/i)
  ) {
    return 'medium';
  }

  // LOW: Utilitários/misc
  return 'low';
}

/**
 * Escanear diretório de skills e extrair metadados
 */
async function scanSkillsDirectory(dir, prefix = '') {
  const skills = {};

  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (entry.name === 'skill-rules.json' || entry.name === 'lib') continue;

      const skillName = entry.name;
      const skillPath = path.join(dir, skillName, 'SKILL.md');

      // Verificar se SKILL.md existe
      if (!fsSync.existsSync(skillPath)) {
        console.error(`[WARN] ${prefix}${skillName}: SKILL.md não encontrado - skip`);
        continue;
      }

      // Extrair triggers (OBRIGATÓRIO no YAML frontmatter)
      const keywords = await extractTriggersFromSkill(skillPath, skillName);

      // Se extractTriggersFromSkill retornou null → skill inválida, skip
      if (keywords === null) {
        continue;
      }

      // Ler conteúdo para inferir priority
      const content = await fs.readFile(skillPath, 'utf8');
      const priority = inferPriority(skillName, content);

      // Inferir description (primeira linha após YAML frontmatter ou primeiro parágrafo)
      let description = skillName.replace(/-/g, ' ');
      const descMatch = content.match(/---[\s\S]*?---\s*\n\s*(.+)/);
      if (descMatch) {
        description = descMatch[1].replace(/^#+\s*/, '').trim().substring(0, 100);
      }

      // Criar entrada
      skills[skillName] = {
        type: inferType(skillName, content),
        enforcement: 'suggest', // Default: suggest (não block)
        priority,
        description,
        promptTriggers: {
          keywords,
          intentPatterns: generateIntentPatterns(skillName, keywords)
        }
      };

      console.error(`✅ ${prefix}${skillName}: ${keywords.length} triggers, priority=${priority}`);
    }

  } catch (error) {
    console.error(`[ERROR] Erro ao escanear ${dir}: ${error.message}`);
  }

  return skills;
}

/**
 * Inferir type de skill (quality, development, documentation, etc.)
 */
function inferType(skillName, content) {
  if (skillName.match(/test|debug|audit|quality/) || content.match(/testing|debugging|quality/i)) {
    return 'quality';
  }
  if (skillName.match(/develop|implement|code/) || content.match(/development|implementation|coding/i)) {
    return 'development';
  }
  if (skillName.match(/document|diagram/) || content.match(/documentation|diagram/i)) {
    return 'documentation';
  }
  if (skillName.match(/plan|architect|design/) || content.match(/planning|architecture|design/i)) {
    return 'planning';
  }
  if (skillName.match(/review|refactor/) || content.match(/review|refactoring/i)) {
    return 'review';
  }
  return 'utility';
}

/**
 * Gerar intent patterns regex baseado em keywords
 */
function generateIntentPatterns(skillName, keywords) {
  const patterns = [];

  // Pattern 1: (verb).*(keyword)
  const verbs = ['implement', 'create', 'build', 'develop', 'add', 'write', 'design', 'plan'];
  for (const keyword of keywords.slice(0, 2)) { // Top 2 keywords apenas
    for (const verb of verbs.slice(0, 3)) { // Top 3 verbos
      patterns.push(`(${verb}).*?(${keyword})`);
    }
  }

  // Pattern 2: skillName-specific
  const skillWords = skillName.split('-');
  if (skillWords.length > 1) {
    // Ex: "test-driven-development" → "test.*development|development.*test"
    patterns.push(`${skillWords[0]}.*${skillWords[skillWords.length - 1]}`);
    patterns.push(`${skillWords[skillWords.length - 1]}.*${skillWords[0]}`);
  }

  // Remover duplicatas e limitar a 5 patterns
  return Array.from(new Set(patterns)).slice(0, 5);
}

/**
 * Main
 */
async function main() {
  console.error('=== Sync Skill Rules ===\n');

  // 1. Escanear skills/ (custom skills)
  console.error('[1/4] Escaneando skills/ ...');
  const customSkills = await scanSkillsDirectory(SKILLS_DIR, 'custom/');

  // 2. Escanear .claude/skills/ (managed skills)
  console.error('\n[2/4] Escaneando .claude/skills/ ...');
  const managedSkills = await scanSkillsDirectory(CLAUDE_SKILLS_DIR, 'managed/');

  // 3. Merge com skill-rules.json existente
  console.error('\n[3/4] Merging com skill-rules.json existente...');
  let existingRules = { skills: {} };

  try {
    const existingContent = await fs.readFile(RULES_PATH, 'utf8');
    existingRules = JSON.parse(existingContent);
  } catch (error) {
    console.error('[WARN] skill-rules.json não encontrado ou inválido - criando novo');
  }

  // Merge: Priorizar manual (existingRules) > auto-gerado
  const mergedSkills = { ...customSkills, ...managedSkills };

  for (const [skillName, autoConfig] of Object.entries(mergedSkills)) {
    if (existingRules.skills?.[skillName]) {
      // Skill já existe - preservar configuração manual
      // Apenas adicionar triggers ausentes
      const existing = existingRules.skills[skillName];
      const autoKeywords = autoConfig.promptTriggers.keywords;
      const existingKeywords = existing.promptTriggers?.keywords || [];

      const newKeywords = Array.from(
        new Set([...existingKeywords, ...autoKeywords])
      );

      existing.promptTriggers = existing.promptTriggers || {};
      existing.promptTriggers.keywords = newKeywords;

      mergedSkills[skillName] = existing; // Preservar manual
    } // else: usar auto-gerado
  }

  // 4. Salvar skill-rules.json atualizado
  console.error('\n[4/4] Salvando skill-rules.json...');
  const updatedRules = {
    ...existingRules,
    skills: mergedSkills,
    _metadata: {
      lastSync: new Date().toISOString(),
      totalSkills: Object.keys(mergedSkills).length,
      autoGenerated: Object.keys({ ...customSkills, ...managedSkills }).length,
      manualConfigured: Object.keys(existingRules.skills || {}).length
    }
  };

  await fs.writeFile(RULES_PATH, JSON.stringify(updatedRules, null, 2), 'utf8');

  console.error(`\n✅ Sync concluído!`);
  console.error(`   Total skills: ${Object.keys(mergedSkills).length}`);
  console.error(`   Custom: ${Object.keys(customSkills).length}`);
  console.error(`   Managed: ${Object.keys(managedSkills).length}`);
  console.error(`   skill-rules.json atualizado: ${RULES_PATH}`);
}

// Execute
main().catch(error => {
  console.error(`\n❌ ERRO: ${error.message}`);
  process.exit(1);
});
