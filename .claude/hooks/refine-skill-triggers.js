/**
 * refine-skill-triggers.js - Refina triggers de skills com keywords específicos
 *
 * Problema: sync-skill-rules.js extraiu keywords genéricos ("implement", "write")
 *           que causam false positives (skills erradas sendo detectadas)
 *
 * Solução: Define triggers ESPECÍFICOS manualmente para cada skill
 *          baseado no propósito único de cada uma
 */

const fs = require('fs');
const path = require('path');

// Triggers refinados - keywords ÚNICOS e específicos por skill
const REFINED_TRIGGERS = {
  // === QUALITY SKILLS ===
  'test-driven-development': {
    keywords: ['tdd', 'test driven', 'test first', 'red green refactor', 'failing test'],
    intentPatterns: [
      '(write|create).*?(test).*?(first|before)',
      '(tdd|test.driven)',
      '(red|green|refactor).*?(cycle)'
    ]
  },

  'systematic-debugging': {
    keywords: ['debug', 'debugging', 'troubleshoot', 'diagnose', 'fix bug', 'error investigation'],
    intentPatterns: [
      '(debug|troubleshoot|diagnose).*?(error|bug|issue)',
      '(fix|resolve).*?(bug|error)'
    ]
  },

  'code-auditor': {
    keywords: ['audit', 'security review', 'code review', 'vulnerability', 'owasp'],
    intentPatterns: [
      '(audit|review).*?(security|vulnerabilit)',
      '(check|scan).*(security|vulnerabilit)'
    ]
  },

  'verification-before-completion': {
    keywords: ['verify', 'validation', 'checklist', 'double check', 'confirm'],
    intentPatterns: [
      '(verify|validate|check).*?(before|completion)',
      'make sure.*?(correct|working)'
    ]
  },

  'test-fixing': {
    keywords: ['failing test', 'broken test', 'test failure', 'fix test'],
    intentPatterns: [
      '(fix|repair).*?(test|spec)',
      'test.*?(fail|break|error)'
    ]
  },

  'testing-anti-patterns': {
    keywords: ['test smell', 'testing anti-pattern', 'bad test', 'test quality'],
    intentPatterns: [
      '(avoid|prevent).*?(test).*?(anti.pattern)',
      'improve.*?(test).*?(quality)'
    ]
  },

  // === DOMAIN SKILLS ===
  'backend-dev-guidelines': {
    keywords: ['backend', 'express', 'api', 'controller', 'service', 'repository', 'microservice'],
    intentPatterns: [
      '(create|build|implement).*?(api|endpoint|route|controller)',
      '(backend|server.side).*?(development|code)'
    ]
  },

  'frontend-dev-guidelines': {
    keywords: ['frontend', 'react', 'component', 'tsx', 'jsx', 'ui', 'tanstack router'],
    intentPatterns: [
      '(create|build).*?(component|ui|interface)',
      '(frontend|client.side).*?(development|code)'
    ]
  },

  'error-tracking': {
    keywords: ['sentry', 'error tracking', 'performance monitoring', 'error capture'],
    intentPatterns: [
      '(add|implement).*?(sentry|error.tracking)',
      '(track|monitor|capture).*?(error|exception)'
    ]
  },

  // === PLANNING SKILLS ===
  'brainstorming': {
    keywords: ['brainstorm', 'ideation', 'exploring options', 'idea refinement'],
    intentPatterns: [
      '(brainstorm|explore).*?(idea|option|approach)',
      'help.*?(refine|develop).*?(idea)'
    ]
  },

  'feature-planning': {
    keywords: ['plan feature', 'feature design', 'implementation plan', 'architecture plan'],
    intentPatterns: [
      '(plan|design).*?(feature|implementation)',
      'how.*?(implement|build).*?(feature)'
    ]
  },

  'writing-plans': {
    keywords: ['write plan', 'create plan', 'planning document'],
    intentPatterns: [
      '(write|create|draft).*?(plan)',
      'plan.*?(document|specification)'
    ]
  },

  'executing-plans': {
    keywords: ['execute plan', 'implement plan', 'follow plan'],
    intentPatterns: [
      '(execute|implement|follow).*?(plan)',
      'based on.*?(plan)'
    ]
  },

  // === DESIGN/ARCHITECTURE SKILLS ===
  'architecture-diagram-creator': {
    keywords: ['architecture diagram', 'system diagram', 'flowchart', 'mermaid diagram'],
    intentPatterns: [
      '(create|draw|generate).*?(diagram|flowchart)',
      '(architecture|system).*?(diagram|visualization)'
    ]
  },

  'flowchart-creator': {
    keywords: ['flowchart', 'flow diagram', 'process diagram'],
    intentPatterns: [
      '(create|draw).*?(flowchart)',
      'visualize.*?(flow|process)'
    ]
  },

  'frontend-design': {
    keywords: ['frontend design', 'ui design', 'design system', 'component design'],
    intentPatterns: [
      '(design|create).*?(ui|interface|component)',
      'frontend.*?(design|styling)'
    ]
  },

  'cli-design': {
    keywords: ['cli', 'command line', 'terminal interface', 'cli tool'],
    intentPatterns: [
      '(create|build|design).*?(cli|command.line)',
      'terminal.*?(tool|interface)'
    ]
  },

  // === REFACTORING SKILLS ===
  'code-refactor': {
    keywords: ['refactor', 'refactoring', 'code cleanup', 'improve code structure'],
    intentPatterns: [
      '(refactor|restructure|reorganize).*?(code)',
      'improve.*?(code).*?(structure|organization)'
    ]
  },

  'root-cause-tracing': {
    keywords: ['root cause', 'trace error', 'error source', 'investigate origin'],
    intentPatterns: [
      '(find|trace|identify).*?(root.cause)',
      'why.*?(error|bug|issue).*?(happen|occur)'
    ]
  },

  // === GIT SKILLS ===
  'git-pushing': {
    keywords: ['git push', 'push commit', 'push changes'],
    intentPatterns: [
      'git.*?push',
      'push.*?(commit|change)'
    ]
  },

  'using-git-worktrees': {
    keywords: ['git worktree', 'worktree', 'multiple branches'],
    intentPatterns: [
      'git.*?worktree',
      'work.*?(multiple).*?(branch)'
    ]
  },

  'finishing-a-development-branch': {
    keywords: ['finish branch', 'complete branch', 'merge branch', 'close branch'],
    intentPatterns: [
      '(finish|complete|close).*?(branch)',
      '(merge|integrate).*?(branch)'
    ]
  },

  // === REVIEW SKILLS ===
  'requesting-code-review': {
    keywords: ['request review', 'code review request', 'pull request'],
    intentPatterns: [
      '(request|ask.for).*?(review)',
      '(create|open).*?(pull.request|pr)'
    ]
  },

  'receiving-code-review': {
    keywords: ['respond to review', 'address feedback', 'review feedback'],
    intentPatterns: [
      '(respond|address).*?(review|feedback)',
      'received.*?(review|feedback)'
    ]
  },

  'review-implementing': {
    keywords: ['implement review feedback', 'apply feedback', 'fix review comments'],
    intentPatterns: [
      '(implement|apply|fix).*?(feedback|comment|review)',
      'address.*?(review).*?(comment)'
    ]
  },

  // === DOCUMENTATION SKILLS ===
  'codebase-documenter': {
    keywords: ['document codebase', 'write documentation', 'api docs'],
    intentPatterns: [
      '(document|create.docs).*?(codebase|api|code)',
      'write.*?(documentation)'
    ]
  },

  'technical-doc-creator': {
    keywords: ['technical documentation', 'technical spec', 'technical guide'],
    intentPatterns: [
      '(create|write).*?(technical).*?(doc|spec|guide)',
      'technical.*?(documentation)'
    ]
  },

  // === SKILL DEVELOPMENT ===
  'skill-creator': {
    keywords: ['create skill', 'new skill', 'skill development'],
    intentPatterns: [
      '(create|develop|build).*?(skill)',
      'new.*?(skill)'
    ]
  },

  'writing-skills': {
    keywords: ['write skill', 'skill writing', 'skill content'],
    intentPatterns: [
      '(write|author).*?(skill)',
      'skill.*?(content|writing)'
    ]
  },

  'sharing-skills': {
    keywords: ['share skill', 'publish skill', 'distribute skill'],
    intentPatterns: [
      '(share|publish|distribute).*?(skill)',
      'make.*?(skill).*?(available)'
    ]
  },

  'testing-skills-with-subagents': {
    keywords: ['test skill', 'skill testing', 'validate skill'],
    intentPatterns: [
      '(test|validate|verify).*?(skill)',
      'skill.*?(test|testing)'
    ]
  },

  'using-superpowers': {
    keywords: ['superpowers', 'obra superpowers', 'use superpowers'],
    intentPatterns: [
      'superpowers',
      'use.*?(superpowers)'
    ]
  },

  // === SUBAGENT SKILLS ===
  'subagent-driven-development': {
    keywords: ['subagent', 'spawn agent', 'delegate to agent', 'task delegation'],
    intentPatterns: [
      '(spawn|create|use).*?(subagent|agent)',
      '(delegate).*?(task|work)'
    ]
  },

  'dispatching-parallel-agents': {
    keywords: ['parallel agents', 'multiple agents', 'concurrent agents'],
    intentPatterns: [
      '(spawn|run).*?(parallel|multiple|concurrent).*?(agent)',
      'agents.*?(parallel|concurrent)'
    ]
  },

  // === FILE OPERATIONS ===
  'file-operations': {
    keywords: ['file operations', 'file manipulation', 'read file', 'write file'],
    intentPatterns: [
      '(read|write|create|delete|move).*?(file)',
      'file.*?(operation|manipulation)'
    ]
  },

  'code-transfer': {
    keywords: ['transfer code', 'copy code', 'move code', 'migrate code'],
    intentPatterns: [
      '(transfer|copy|move|migrate).*?(code|file)',
      'code.*?(transfer|migration)'
    ]
  },

  // === PROJECT MANAGEMENT ===
  'project-bootstrapper': {
    keywords: ['bootstrap project', 'new project', 'project setup', 'scaffold project'],
    intentPatterns: [
      '(bootstrap|setup|scaffold|init).*?(project)',
      'new.*?(project).*?(setup)'
    ]
  },

  'ship-learn-next': {
    keywords: ['ship feature', 'release', 'deploy', 'ship to production'],
    intentPatterns: [
      '(ship|release|deploy).*?(feature|code)',
      'ready.*?(ship|release)'
    ]
  },

  // === DOCUMENT PROCESSING ===
  'pdf': {
    keywords: ['pdf', 'pdf file', 'pdf document'],
    intentPatterns: [
      'pdf',
      '(read|create|generate).*?(pdf)'
    ]
  },

  'docx': {
    keywords: ['docx', 'word document', 'word file'],
    intentPatterns: [
      'docx',
      '(read|create|generate).*?(word|docx)'
    ]
  },

  'pptx': {
    keywords: ['pptx', 'powerpoint', 'presentation'],
    intentPatterns: [
      'pptx|powerpoint',
      '(read|create|generate).*?(presentation|powerpoint)'
    ]
  },

  'xlsx': {
    keywords: ['xlsx', 'excel', 'spreadsheet'],
    intentPatterns: [
      'xlsx|excel|spreadsheet',
      '(read|create|generate).*?(excel|spreadsheet)'
    ]
  },

  // === OTHER SKILLS ===
  'code-execution': {
    keywords: ['execute code', 'run code', 'code execution'],
    intentPatterns: [
      '(execute|run).*?(code|script)',
      'code.*?(execution)'
    ]
  },

  'conversation-analyzer': {
    keywords: ['analyze conversation', 'conversation analysis', 'transcript analysis'],
    intentPatterns: [
      '(analyze|review).*?(conversation|transcript)',
      'conversation.*?(analysis)'
    ]
  },

  'condition-based-waiting': {
    keywords: ['wait for', 'polling', 'condition waiting', 'wait until'],
    intentPatterns: [
      'wait.*(for|until)',
      '(poll|check).*?(condition)'
    ]
  },

  'dashboard-creator': {
    keywords: ['dashboard', 'create dashboard', 'data visualization'],
    intentPatterns: [
      '(create|build).*?(dashboard)',
      'dashboard.*(create|build)'
    ]
  },

  'defense-in-depth': {
    keywords: ['defense in depth', 'security layers', 'layered security'],
    intentPatterns: [
      'defense.*?depth',
      '(layered|multiple).*?(security)'
    ]
  },

  'prompt-improver': {
    keywords: ['improve prompt', 'refine prompt', 'prompt quality'],
    intentPatterns: [
      '(improve|refine|enhance).*?(prompt)',
      'prompt.*?(quality|improvement)'
    ]
  },

  'timeline-creator': {
    keywords: ['timeline', 'create timeline', 'chronology'],
    intentPatterns: [
      '(create|generate).*?(timeline)',
      'timeline.*?(visualization)'
    ]
  },

  'webapp-testing': {
    keywords: ['test webapp', 'web testing', 'browser testing', 'e2e testing'],
    intentPatterns: [
      '(test|verify).*?(webapp|website|web.app)',
      '(e2e|integration).*?(test)'
    ]
  },

  'youtube-transcript': {
    keywords: ['youtube transcript', 'video transcript', 'youtube caption'],
    intentPatterns: [
      'youtube.*?(transcript|caption)',
      '(get|fetch|extract).*?(youtube).*?(transcript)'
    ]
  },

  'artifacts-builder': {
    keywords: ['artifact', 'build artifact', 'create artifact'],
    intentPatterns: [
      '(build|create|generate).*?(artifact)',
      'artifact.*?(building|creation)'
    ]
  },

  'article-extractor': {
    keywords: ['extract article', 'legal article', 'article extraction'],
    intentPatterns: [
      '(extract|find|get).*?(article)',
      'article.*?(extraction)'
    ]
  }
};

/**
 * Update skill-rules.json with refined triggers
 */
function refineSkillRules() {
  const projectDir = process.cwd();
  const rulesPath = path.join(projectDir, '.claude', 'skills', 'skill-rules.json');

  // Read current skill-rules.json
  const rulesContent = fs.readFileSync(rulesPath, 'utf8');
  const rules = JSON.parse(rulesContent);

  let updated = 0;
  let skipped = 0;

  // Update each skill with refined triggers
  for (const [skillName, refinedTriggers] of Object.entries(REFINED_TRIGGERS)) {
    if (rules.skills[skillName]) {
      // Update promptTriggers with refined values
      rules.skills[skillName].promptTriggers = {
        keywords: refinedTriggers.keywords,
        intentPatterns: refinedTriggers.intentPatterns
      };
      updated++;
      console.log(`✅ ${skillName}: ${refinedTriggers.keywords.length} keywords, ${refinedTriggers.intentPatterns.length} patterns`);
    } else {
      skipped++;
      console.warn(`⚠️  ${skillName}: Not found in skill-rules.json (skipped)`);
    }
  }

  // Write updated skill-rules.json
  fs.writeFileSync(rulesPath, JSON.stringify(rules, null, 2), 'utf8');

  console.log('\n═══════════════════════════════════════════');
  console.log(`✅ Refinement complete!`);
  console.log(`   Updated: ${updated} skills`);
  console.log(`   Skipped: ${skipped} skills (not in rules)`);
  console.log(`   File: ${rulesPath}`);
  console.log('═══════════════════════════════════════════');
}

// Run
refineSkillRules();
