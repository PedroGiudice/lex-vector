/**
 * lib/subagent-detector.js - Subagent auto-detection based on context
 *
 * Similar to skill-detector.js but for agents.
 * Detects which agents are most relevant for the current prompt.
 *
 * Version: 1.0.0
 */

const fs = require('fs');
const path = require('path');

/**
 * Escapes regex special characters
 */
function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Matches keyword with word boundary
 */
function matchKeywordWithBoundary(text, keyword) {
  const keywordLower = keyword.toLowerCase();

  if (keywordLower.length <= 2) {
    const regex = new RegExp(`\\b${escapeRegex(keywordLower)}\\b`, 'i');
    return regex.test(text);
  }

  const regex = new RegExp(`\\b${escapeRegex(keywordLower)}`, 'i');
  return regex.test(text);
}

/**
 * Detect agents based on prompt
 * @param {string} prompt - User prompt
 * @param {string[]} modifiedFiles - List of modified files (optional)
 * @returns {object|null} - { topAgents, totalConsidered, totalMatched }
 */
function detectAgent(prompt, modifiedFiles = []) {
  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const rulesPath = path.join(projectDir, '.claude', 'hooks', 'lib', 'subagent-rules.json');

    if (!fs.existsSync(rulesPath)) {
      return null;
    }

    const rulesContent = fs.readFileSync(rulesPath, 'utf8');
    const rules = JSON.parse(rulesContent);

    if (!rules.agents) {
      return null;
    }

    const promptLower = prompt.toLowerCase();
    const matched = [];

    // Iterate through all agents
    for (const [agentName, config] of Object.entries(rules.agents)) {
      let score = 0;
      let matchedTriggers = [];

      // 1. KEYWORD MATCHING
      if (config.promptTriggers?.keywords) {
        for (const keyword of config.promptTriggers.keywords) {
          if (matchKeywordWithBoundary(prompt, keyword)) {
            score += 10;
            matchedTriggers.push(`keyword: "${keyword}"`);
            break;
          }
        }
      }

      // 2. INTENT PATTERN MATCHING
      if (config.promptTriggers?.intentPatterns) {
        for (const pattern of config.promptTriggers.intentPatterns) {
          try {
            const regex = new RegExp(pattern, 'i');
            if (regex.test(prompt)) {
              score += 15;
              matchedTriggers.push(`pattern: "${pattern}"`);
              break;
            }
          } catch (err) {
            // Ignore invalid regex
          }
        }
      }

      // 3. FILE PATTERN MATCHING
      if (config.fileTriggers && modifiedFiles.length > 0) {
        for (const filePattern of config.fileTriggers) {
          try {
            const regex = new RegExp(filePattern, 'i');
            for (const file of modifiedFiles) {
              if (regex.test(file)) {
                score += 8;
                matchedTriggers.push(`file: "${filePattern}"`);
                break;
              }
            }
          } catch (err) {
            // Ignore invalid regex
          }
        }
      }

      if (score > 0) {
        matched.push({
          agentName,
          config,
          score,
          matchedTriggers
        });
      }
    }

    if (matched.length === 0) {
      logDetection(prompt, Object.keys(rules.agents).length, 0, []);
      return null;
    }

    // RANKING: Priority weight + match score
    const priorityWeights = {
      'critical': 100,
      'high': 50,
      'medium': 20,
      'low': 10
    };

    matched.forEach(m => {
      const priorityWeight = priorityWeights[m.config.priority] || 0;
      m.finalScore = m.score + priorityWeight;
    });

    // Sort by finalScore (highest first)
    matched.sort((a, b) => b.finalScore - a.finalScore);

    // Return top 5
    const top5 = matched.slice(0, 5);

    logDetection(
      prompt,
      Object.keys(rules.agents).length,
      matched.length,
      top5.map(a => a.agentName)
    );

    return {
      topAgents: top5,
      totalConsidered: Object.keys(rules.agents).length,
      totalMatched: matched.length
    };

  } catch (error) {
    console.error(`[ERROR] subagent-detector.js: ${error.message}`);
    return null;
  }
}

/**
 * Log agent detection for analytics
 */
function logDetection(prompt, considered, matched, suggested) {
  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const logPath = path.join(projectDir, '.claude', 'hooks', 'lib', 'agent-tracking.log');

    const logEntry = {
      timestamp: new Date().toISOString(),
      prompt: prompt.substring(0, 100),
      considered,
      matched,
      suggested
    };

    fs.appendFileSync(logPath, JSON.stringify(logEntry) + '\n', 'utf8');
  } catch (err) {
    // Logging failure should not break detection
  }
}

/**
 * Check if agent is an ADK (Gemini-powered) agent
 */
function isAdkAgent(config) {
  return config._note && config._note.toLowerCase().includes('adk');
}

/**
 * Format agent suggestions for output
 */
function formatAgentSuggestions(detection) {
  if (!detection || detection.topAgents.length === 0) {
    return null;
  }

  const lines = ['🤖 AGENTES SUGERIDOS:'];

  for (const agent of detection.topAgents.slice(0, 3)) {
    const priority = agent.config.priority || 'medium';
    const desc = agent.config.description || '';
    const adkTag = isAdkAgent(agent.config) ? ' [ADK/Gemini]' : '';
    lines.push(`- ${agent.agentName}${adkTag} (${priority}) - ${desc.substring(0, 50)}`);
  }

  lines.push('');
  lines.push('Para usar: "Use o agente [nome] para [tarefa]"');

  // Check if any suggested agent is ADK
  const hasAdkAgent = detection.topAgents.slice(0, 3).some(a => isAdkAgent(a.config));
  if (hasAdkAgent) {
    lines.push('⚡ ADK agents require: cd adk-agents && adk run [agent-name]');
  }

  return lines.join('\n');
}

module.exports = { detectAgent, formatAgentSuggestions };

// Run if executed directly
if (require.main === module) {
  const prompt = process.env.CLAUDE_USER_PROMPT || process.argv[2] || '';

  if (!prompt) {
    console.log('Usage: CLAUDE_USER_PROMPT="your prompt" node subagent-detector.js');
    process.exit(0);
  }

  const detection = detectAgent(prompt);

  if (detection) {
    console.log(JSON.stringify(detection, null, 2));
  } else {
    console.log('No agents matched');
  }
}
