#!/usr/bin/env node

/**
 * agent-auto-discovery.js - Auto-discovery system for virtual agents
 *
 * PROBLEMA RESOLVIDO:
 * - Agents existiam em .claude/agents/*.md mas não estavam no agent-tools-mapping.json
 * - Sistema "disfuncional" porque 11 agents não eram reconhecidos
 *
 * SOLUÇÃO:
 * - Auto-descobre TODOS agents em .claude/agents/ (RECURSIVO, todas subpastas)
 * - Lê YAML frontmatter para extrair name, description, tools
 * - Gera automaticamente agent-tools-mapping.json
 *
 * USO:
 * node .claude/hooks/lib/agent-auto-discovery.js --update
 *
 * Version: 2.0.0
 * Date: 2025-11-30
 *
 * CHANGELOG v2.0.0:
 * - Recursive discovery: now scans all subdirectories under .claude/agents/
 * - Supports organized agent structure with subdirs (development/, quality-testing/, etc)
 */

const fs = require('fs');
const path = require('path');

// ============================================================================
// YAML FRONTMATTER PARSER
// ============================================================================

function parseYamlFrontmatter(content) {
  const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---/;
  const match = content.match(frontmatterRegex);

  if (!match) return null;

  const yamlContent = match[1];
  const parsed = {};

  // Simple YAML parser (supports key: value format)
  yamlContent.split('\n').forEach(line => {
    const colonIndex = line.indexOf(':');
    if (colonIndex === -1) return;

    const key = line.substring(0, colonIndex).trim();
    const value = line.substring(colonIndex + 1).trim();

    // Remove quotes if present
    parsed[key] = value.replace(/^["']|["']$/g, '');
  });

  return parsed;
}

// ============================================================================
// AGENT DISCOVERY (RECURSIVE)
// ============================================================================

/**
 * Recursively find all .md files in a directory
 */
function findMdFilesRecursive(dir, baseDir = dir) {
  const results = [];

  if (!fs.existsSync(dir)) return results;

  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      // Recurse into subdirectories
      results.push(...findMdFilesRecursive(fullPath, baseDir));
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      // Get relative path from base agents dir
      const relativePath = path.relative(baseDir, fullPath);
      results.push({ fullPath, relativePath, filename: entry.name });
    }
  }

  return results;
}

function discoverAgents(projectDir = process.cwd()) {
  const agentsDir = path.join(projectDir, '.claude', 'agents');

  if (!fs.existsSync(agentsDir)) {
    console.error(`[ERROR] Agents directory not found: ${agentsDir}`);
    return [];
  }

  // Recursively find all .md files
  const allMdFiles = findMdFilesRecursive(agentsDir);

  // Filter out documentation files
  const agentFiles = allMdFiles.filter(f => {
    // Exclude documentation files
    if (f.filename === 'README.md') return false;
    if (f.filename.match(/^[A-Z_]+.*\.md$/)) return false; // ALL_CAPS or UPPER_CASE docs

    return true;
  }).sort((a, b) => a.relativePath.localeCompare(b.relativePath));

  const discovered = [];

  for (const file of agentFiles) {
    const content = fs.readFileSync(file.fullPath, 'utf8');
    const frontmatter = parseYamlFrontmatter(content);

    // Extract agent name from filename if not in frontmatter
    const agentName = frontmatter?.name || file.filename.replace('.md', '');

    // Extract description
    const description = frontmatter?.description || `Agent: ${agentName}`;

    // Extract tools from frontmatter or infer from content
    let tools = [];
    if (frontmatter?.tools) {
      tools = frontmatter.tools.split(',').map(t => t.trim());
    } else {
      // Infer tools based on agent type
      tools = inferToolsFromContent(content, agentName);
    }

    // Extract critical_instruction if present
    const critical_instruction = frontmatter?.critical_instruction || null;

    discovered.push({
      name: agentName,
      description,
      tools,
      critical_instruction,
      source: file.relativePath  // Now includes subdir path
    });
  }

  return discovered;
}

function inferToolsFromContent(content, agentName) {
  const contentLower = content.toLowerCase();

  // Exact matches (highest priority)
  const exactMatches = {
    'desenvolvimento': ['Read', 'Write', 'Edit', 'Bash', 'Glob', 'Grep'],
    'qualidade-codigo': ['Read', 'Glob', 'Grep', 'Bash'],
    'analise-dados-legal': ['Read', 'Glob', 'Grep', 'Bash'],
    'documentacao': ['Read', 'Write', 'Edit', 'Glob', 'Grep'],
    'planejamento-legal': ['Read', 'Glob', 'Grep', 'WebFetch', 'WebSearch'],
    'legal-articles-finder': ['Read', 'Glob', 'Grep'],
    'legal-text-extractor': ['Read', 'Glob', 'Grep'],
    'code-refactor-master': ['*'],
    'frontend-error-fixer': ['*'],
    'auto-error-resolver': ['Read', 'Write', 'Edit', 'MultiEdit', 'Bash'],
    'auth-route-debugger': ['Read', 'Glob', 'Grep', 'Bash', 'WebFetch', 'WebSearch'],
    'auth-route-tester': ['Read', 'Glob', 'Grep', 'Bash'],
    'web-research-specialist': ['WebFetch', 'WebSearch', 'Read', 'Glob', 'Grep'],
    'plan-reviewer': ['Read', 'Glob', 'Grep', 'WebFetch', 'WebSearch'],
    'refactor-planner': ['Read', 'Glob', 'Grep'],
    'code-architecture-reviewer': ['Read', 'Glob', 'Grep', 'Edit'],
    'documentation-architect': ['Read', 'Write', 'Glob', 'Grep'],
    'tui-master': ['Read', 'Write', 'Edit', 'MultiEdit', 'Bash', 'Grep', 'Glob']
  };

  if (exactMatches[agentName]) {
    return exactMatches[agentName];
  }

  // Pattern-based inference (fallback)
  if (agentName.includes('plan') || agentName.includes('research')) {
    return ['Read', 'Glob', 'Grep', 'WebFetch', 'WebSearch'];
  }

  if (agentName.includes('dev') || agentName.includes('implement')) {
    return ['Read', 'Write', 'Edit', 'Bash', 'Glob', 'Grep'];
  }

  if (agentName.includes('doc')) {
    return ['Read', 'Write', 'Edit', 'Glob', 'Grep'];
  }

  if (agentName.includes('quality') || agentName.includes('test')) {
    return ['Read', 'Glob', 'Grep', 'Bash'];
  }

  if (agentName.includes('refactor') && !agentName.includes('planner')) {
    return ['*']; // Comprehensive refactoring needs all tools
  }

  if (agentName.includes('error') || agentName.includes('debug')) {
    return ['Read', 'Glob', 'Grep', 'Bash', 'WebFetch', 'WebSearch'];
  }

  if (agentName.includes('auth')) {
    return ['Read', 'Glob', 'Grep', 'Bash'];
  }

  // Default: read-only
  return ['Read', 'Glob', 'Grep'];
}

// ============================================================================
// MAPPING GENERATION
// ============================================================================

function generateAgentMapping(discoveredAgents, existingMapping = null) {
  const agents = {};

  // Preserve existing mapping for special agents (Plan, Explore, etc)
  if (existingMapping && existingMapping.agents) {
    const specialAgents = ['Plan', 'Explore', 'general-purpose', 'claude-code-guide',
                          'statusline-setup', 'vibe-log-session-analyzer', 'vibe-log-report-generator'];

    for (const specialAgent of specialAgents) {
      if (existingMapping.agents[specialAgent]) {
        agents[specialAgent] = existingMapping.agents[specialAgent];
      }
    }
  }

  // Add discovered agents
  for (const agent of discoveredAgents) {
    agents[agent.name] = {
      tools: agent.tools,
      description: agent.description,
      critical_instruction: agent.critical_instruction
    };
  }

  return {
    "$schema": "https://json-schema.org/draft-07/schema#",
    "$comment": "Mapeamento declarativo de agentes → ferramentas disponíveis (AUTO-GENERATED)",
    "version": "2.1.0",
    "description": "Auto-discovery system: agents são descobertos automaticamente de .claude/agents/**/*.md (recursive)",
    "generated_at": new Date().toISOString(),
    "agents": agents,
    "_notes": {
      "toolsWildcard": "Use '*' to grant all available tools (inherits from main context)",
      "criticalInstruction": "Injected at end of prompt when non-null - use for tool usage reminders",
      "autoDiscovery": "Run 'node .claude/hooks/lib/agent-auto-discovery.js --update' to regenerate this file"
    }
  };
}

// ============================================================================
// CLI INTERFACE
// ============================================================================

function main() {
  const args = process.argv.slice(2);
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

  console.log('🔍 AGENT AUTO-DISCOVERY\n');

  // Discover agents
  const discovered = discoverAgents(projectDir);
  console.log(`✅ Discovered ${discovered.length} agents from .claude/agents/**/*.md (recursive)\n`);

  // Show discovered agents
  console.log('📋 DISCOVERED AGENTS:');
  discovered.forEach(agent => {
    const toolsSummary = agent.tools.includes('*') ? 'ALL tools' : agent.tools.join(', ');
    console.log(`  - ${agent.name}: ${toolsSummary}`);
  });
  console.log('');

  // Update mapping if requested
  if (args.includes('--update')) {
    const mappingPath = path.join(projectDir, '.claude', 'hooks', 'agent-tools-mapping.json');

    // Load existing mapping
    let existingMapping = null;
    if (fs.existsSync(mappingPath)) {
      try {
        existingMapping = JSON.parse(fs.readFileSync(mappingPath, 'utf8'));
      } catch (err) {
        console.warn(`⚠️  Could not parse existing mapping: ${err.message}`);
      }
    }

    // Generate new mapping
    const newMapping = generateAgentMapping(discovered, existingMapping);

    // Write to file
    fs.writeFileSync(mappingPath, JSON.stringify(newMapping, null, 2));
    console.log(`✅ Updated: ${mappingPath}`);
    console.log(`   Total agents: ${Object.keys(newMapping.agents).length}`);
  } else {
    console.log('ℹ️  Use --update to regenerate agent-tools-mapping.json');
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  discoverAgents,
  generateAgentMapping,
  parseYamlFrontmatter
};
