/**
 * agent-mapping-loader.js - Shared helper for loading agent-tools mapping
 *
 * CRITICAL: Single source of truth for agent→tools configuration
 * Used by:
 * - inject-tools-to-agents.js (PreToolUse hook)
 * - agent-orchestrator.js (Legal-Braniac decision engine)
 *
 * Version: 1.0.0
 * Author: Claude Code (Sonnet 4.5)
 * Date: 2025-11-20
 */

const fs = require('fs');
const path = require('path');

// Cache mapping in memory (loaded once per Node process)
let cachedMapping = null;
let lastLoadTime = 0;
const CACHE_TTL = 60000; // 1 minute (for development, can be increased)

/**
 * Load agent-tools mapping from JSON file
 *
 * @param {Object} options - Configuration options
 * @param {string} options.projectDir - Project directory (default: CLAUDE_PROJECT_DIR)
 * @param {boolean} options.forceReload - Bypass cache
 * @returns {Object|null} - Agents mapping or null if not found
 */
function loadAgentMapping(options = {}) {
  const {
    projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd(),
    forceReload = false
  } = options;

  const mappingPath = path.join(projectDir, '.claude', 'hooks', 'agent-tools-mapping.json');

  // Return cached mapping if valid
  const now = Date.now();
  if (!forceReload && cachedMapping && (now - lastLoadTime) < CACHE_TTL) {
    return cachedMapping.agents;
  }

  // Load from file
  try {
    const content = fs.readFileSync(mappingPath, 'utf8');
    const mapping = JSON.parse(content);

    // Validate structure
    if (!mapping.agents || typeof mapping.agents !== 'object') {
      throw new Error('Invalid mapping: missing "agents" object');
    }

    // Update cache
    cachedMapping = mapping;
    lastLoadTime = now;

    return mapping.agents;
  } catch (error) {
    if (error.code === 'ENOENT') {
      // File not found - this is OK during initial setup
      return null;
    }
    // Other errors should be logged but not crash
    console.error(`[WARN] Failed to load agent mapping: ${error.message}`);
    return null;
  }
}

/**
 * Get configuration for specific agent type
 *
 * @param {string} agentType - Agent type (e.g., "Plan", "Explore")
 * @param {Object} options - Same as loadAgentMapping
 * @returns {Object|null} - Agent config or null if not found
 */
function getAgentConfig(agentType, options = {}) {
  const mapping = loadAgentMapping(options);
  if (!mapping) return null;

  return mapping[agentType] || null;
}

/**
 * Get tools list for specific agent type
 *
 * @param {string} agentType - Agent type
 * @param {Object} options - Same as loadAgentMapping
 * @returns {Array<string>} - Tools array (empty if not found)
 */
function getAgentTools(agentType, options = {}) {
  const config = getAgentConfig(agentType, options);
  if (!config) return [];

  return config.tools || [];
}

/**
 * Check if agent has specific tool
 *
 * @param {string} agentType - Agent type
 * @param {string} toolName - Tool name (e.g., "WebFetch")
 * @param {Object} options - Same as loadAgentMapping
 * @returns {boolean} - True if agent has tool
 */
function agentHasTool(agentType, toolName, options = {}) {
  const tools = getAgentTools(agentType, options);

  // Check for wildcard (all tools)
  if (tools.includes('*')) return true;

  // Check for specific tool
  return tools.includes(toolName);
}

/**
 * Get human-readable tools summary
 *
 * @param {string} agentType - Agent type
 * @param {Object} options - Same as loadAgentMapping
 * @returns {string} - Tools summary (e.g., "WebFetch, WebSearch, Read")
 */
function getAgentToolsSummary(agentType, options = {}) {
  const tools = getAgentTools(agentType, options);

  if (tools.length === 0) {
    return 'default tools (inherited)';
  }

  if (tools.includes('*')) {
    return 'ALL tools';
  }

  return tools.join(', ');
}

/**
 * Get all registered agent types
 *
 * @param {Object} options - Same as loadAgentMapping
 * @returns {Array<string>} - List of agent types
 */
function getAllAgentTypes(options = {}) {
  const mapping = loadAgentMapping(options);
  if (!mapping) return [];

  return Object.keys(mapping);
}

/**
 * Clear cache (useful for testing)
 */
function clearCache() {
  cachedMapping = null;
  lastLoadTime = 0;
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  loadAgentMapping,
  getAgentConfig,
  getAgentTools,
  agentHasTool,
  getAgentToolsSummary,
  getAllAgentTypes,
  clearCache
};
