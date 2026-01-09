/**
 * lib/subagent-suggester.js - Suggests relevant subagents based on prompt context
 *
 * Called by UserPromptSubmit hook to suggest agents for the current task.
 * Outputs suggestions to stdout (added to context as system-reminder).
 *
 * Version: 1.0.0
 */

const { detectAgent, formatAgentSuggestions } = require('./subagent-detector');

/**
 * Main entry point
 */
function main() {
  try {
    const prompt = process.env.CLAUDE_USER_PROMPT || '';

    if (!prompt || prompt.length < 10) {
      // Too short to detect meaningful context
      process.exit(0);
    }

    // Skip if prompt already mentions using an agent
    if (/use.*?agent|agente|Task\s+tool/i.test(prompt)) {
      process.exit(0);
    }

    const detection = detectAgent(prompt);

    if (!detection || detection.topAgents.length === 0) {
      process.exit(0);
    }

    // Only suggest if we have high-confidence matches
    const topAgent = detection.topAgents[0];
    if (topAgent.finalScore < 50) {
      // Low confidence - don't suggest
      process.exit(0);
    }

    const suggestions = formatAgentSuggestions(detection);

    if (suggestions) {
      console.log(suggestions);
    }

    process.exit(0);
  } catch (error) {
    console.error(`[ERROR] subagent-suggester.js: ${error.message}`);
    process.exit(1);
  }
}

module.exports = { main };

if (require.main === module) {
  main();
}
