#!/usr/bin/env node

/**
 * remove-triggers-from-yaml.js - Remove campo triggers do YAML frontmatter
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');

const PROJECT_DIR = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const SKILLS_DIR = path.join(PROJECT_DIR, 'skills');
const CLAUDE_SKILLS_DIR = path.join(PROJECT_DIR, '.claude', 'skills');

async function removeTriggersFromSkill(skillPath, skillName) {
  try {
    const content = await fs.readFile(skillPath, 'utf8');

    // Verificar se tem YAML frontmatter
    const yamlMatch = content.match(/^---\s*\n([\s\S]*?)\n---/);
    if (!yamlMatch) {
      return { skillName, status: 'skip', reason: 'Sem YAML frontmatter' };
    }

    const yaml = yamlMatch[1];

    // Verificar se tem triggers
    if (!yaml.match(/^triggers:/m)) {
      return { skillName, status: 'skip', reason: 'Sem campo triggers' };
    }

    // Remover linha triggers (incluindo quebra de linha antes e depois)
    const newYaml = yaml.replace(/\n?triggers:.*?\n?/m, '\n');

    // Substituir YAML no conteúdo
    const newContent = content.replace(
      /^---\s*\n[\s\S]*?\n---/,
      `---\n${newYaml}---`
    );

    // Salvar arquivo atualizado
    await fs.writeFile(skillPath, newContent, 'utf8');

    return { skillName, status: 'removed' };

  } catch (error) {
    return { skillName, status: 'error', reason: error.message };
  }
}

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

      const result = await removeTriggersFromSkill(skillPath, skillName);
      result.skillName = prefix + skillName;
      results.push(result);
    }

  } catch (error) {
    console.error(`[ERROR] Erro ao processar ${dir}: ${error.message}`);
  }

  return results;
}

async function main() {
  console.error('=== Removendo campo triggers do YAML frontmatter ===\n');

  // Processar skills/
  console.error('[1/2] Processando skills/ ...');
  const customResults = await processSkillsDirectory(SKILLS_DIR, 'custom/');

  // Processar .claude/skills/
  console.error('\n[2/2] Processando .claude/skills/ ...');
  const managedResults = await processSkillsDirectory(CLAUDE_SKILLS_DIR, 'managed/');

  // Consolidar resultados
  const allResults = [...customResults, ...managedResults];

  const removed = allResults.filter(r => r.status === 'removed');
  const skipped = allResults.filter(r => r.status === 'skip');
  const errors = allResults.filter(r => r.status === 'error');

  console.error('\n' + '='.repeat(80));
  console.error('RESULTADOS');
  console.error('='.repeat(80) + '\n');

  console.error(`✅ Removidos: ${removed.length}`);
  console.error(`⏭️  Pulados: ${skipped.length}`);
  console.error(`❌ Erros: ${errors.length}\n`);

  if (removed.length > 0) {
    console.error('Skills com triggers removidos:');
    removed.forEach(r => console.error(`  - ${r.skillName}`));
  }

  console.error('\n' + '='.repeat(80));
  console.error(`✅ Concluído! ${removed.length} YAMLs limpos.`);
  console.error('='.repeat(80));
}

main().catch(error => {
  console.error(`\n❌ ERRO FATAL: ${error.message}`);
  process.exit(1);
});
