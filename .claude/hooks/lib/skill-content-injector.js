/**
 * lib/skill-content-injector.js - Auto-injection of skill content into context
 *
 * Based on jefflester/claude-skills-supercharged approach:
 * - Detects top N skills via skill-detector.js
 * - Injects SKILL.md content wrapped in XML tags
 * - Tracks loaded skills per session (prevents duplication)
 * - Outputs to stdout (automatically added to context)
 *
 * Research sources:
 * - jefflester/claude-skills-supercharged (95%+ success rate)
 * - obra/superpowers (progressive disclosure)
 * - diet103/infrastructure-showcase (rules-based triggers)
 */

const fs = require('fs');
const path = require('path');
const { detectSkill } = require('./skill-detector');

// Configuration
const MAX_INJECTED_SKILLS = 3; // Top N skills to inject (prevent context bloat)
const SESSION_TRACKING_FILE = path.join(__dirname, 'session-skills.json');

/**
 * Get session ID from environment or generate one
 * @returns {string} Session identifier
 */
function getSessionId() {
  return process.env.CLAUDE_SESSION_ID || 'default';
}

/**
 * Load session tracking data
 * @returns {object} Session tracking data (sessionId -> array of loaded skills)
 */
function loadSessionTracking() {
  try {
    if (!fs.existsSync(SESSION_TRACKING_FILE)) {
      return {};
    }
    const content = fs.readFileSync(SESSION_TRACKING_FILE, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    console.error(`[WARN] Failed to load session tracking: ${error.message}`);
    return {};
  }
}

/**
 * Save session tracking data
 * @param {object} data - Session tracking data to save
 */
function saveSessionTracking(data) {
  try {
    fs.writeFileSync(SESSION_TRACKING_FILE, JSON.stringify(data, null, 2), 'utf8');
  } catch (error) {
    console.error(`[WARN] Failed to save session tracking: ${error.message}`);
  }
}

/**
 * Get skills already loaded in this session
 * @param {string} sessionId - Session identifier
 * @returns {string[]} Array of loaded skill names
 */
function getLoadedSkills(sessionId) {
  const tracking = loadSessionTracking();
  return tracking[sessionId] || [];
}

/**
 * Mark skills as loaded in this session
 * @param {string} sessionId - Session identifier
 * @param {string[]} skillNames - Array of skill names to mark as loaded
 */
function markSkillsLoaded(sessionId, skillNames) {
  const tracking = loadSessionTracking();
  if (!tracking[sessionId]) {
    tracking[sessionId] = [];
  }
  tracking[sessionId].push(...skillNames);

  // Remove duplicates
  tracking[sessionId] = [...new Set(tracking[sessionId])];

  saveSessionTracking(tracking);
}

/**
 * Read skill content from SKILL.md
 * @param {string} skillName - Name of skill to read
 * @returns {string|null} Skill content or null if not found
 */
function readSkillContent(skillName) {
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

  // Try multiple locations (skills/ and .claude/skills/)
  const locations = [
    path.join(projectDir, 'skills', skillName, 'SKILL.md'),
    path.join(projectDir, '.claude', 'skills', skillName, 'SKILL.md')
  ];

  for (const skillPath of locations) {
    if (fs.existsSync(skillPath)) {
      try {
        return fs.readFileSync(skillPath, 'utf8');
      } catch (error) {
        console.error(`[ERROR] Failed to read ${skillPath}: ${error.message}`);
      }
    }
  }

  console.error(`[WARN] Skill not found: ${skillName}`);
  return null;
}

/**
 * Inject skill content into context
 *
 * How it works:
 * 1. Detect top skills via skill-detector.js (keywords + intent patterns)
 * 2. Filter out skills already loaded in this session
 * 3. Read SKILL.md content for top N skills
 * 4. Wrap content in <skill> XML tags
 * 5. Output to stdout (auto-injected into Claude's context)
 *
 * @param {string} prompt - User prompt
 * @returns {string[]} Array of injected skill names
 */
function injectSkillContent(prompt) {
  const sessionId = getSessionId();
  const loadedSkills = getLoadedSkills(sessionId);

  // Detect skills using existing skill-detector.js logic
  const detection = detectSkill(prompt);

  if (!detection || detection.topSkills.length === 0) {
    // No skills matched - nothing to inject
    return [];
  }

  // Filter out already loaded skills and limit to MAX_INJECTED_SKILLS
  const skillsToInject = detection.topSkills
    .filter(s => !loadedSkills.includes(s.skillName))
    .slice(0, MAX_INJECTED_SKILLS);

  if (skillsToInject.length === 0) {
    // All matched skills already loaded in this session
    return [];
  }

  // Inject each skill
  const injectedSkills = [];

  for (const { skillName, finalScore } of skillsToInject) {
    const content = readSkillContent(skillName);

    if (!content) {
      continue; // Skip if skill content not found
    }

    // Wrap in XML tags (jefflester pattern)
    // stdout is automatically added to Claude's context (UserPromptSubmit hook behavior)
    const injected = `<skill name="${skillName}" score="${finalScore}">
${content}
</skill>`;

    // Output to stdout (auto-injected into context)
    console.log(injected);
    console.log(''); // Blank line separator

    injectedSkills.push(skillName);
  }

  // Mark skills as loaded (prevent re-injection in same session)
  if (injectedSkills.length > 0) {
    markSkillsLoaded(sessionId, injectedSkills);
  }

  return injectedSkills;
}

/**
 * Main entry point (called from hook)
 */
function main() {
  try {
    const prompt = process.env.CLAUDE_USER_PROMPT || '';

    if (!prompt) {
      // No prompt - nothing to do (empty prompt or session continuation)
      process.exit(0);
    }

    const injected = injectSkillContent(prompt);

    // Debug log (to stderr, not added to context)
    if (injected.length > 0) {
      console.error(`[skill-content-injector] Injected ${injected.length} skills: ${injected.join(', ')}`);
    } else {
      console.error(`[skill-content-injector] No skills injected`);
    }

    process.exit(0);
  } catch (error) {
    console.error(`[ERROR] skill-content-injector.js: ${error.message}`);
    console.error(error.stack);
    process.exit(1);
  }
}

// Export for testing
module.exports = {
  injectSkillContent,
  readSkillContent,
  getLoadedSkills,
  markSkillsLoaded
};

// Run if executed directly
if (require.main === module) {
  main();
}
