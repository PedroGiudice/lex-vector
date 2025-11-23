/**
 * Basic Usage Examples - Orchestration Tracker Plugin
 *
 * This file demonstrates common usage patterns for the orchestration-tracker
 * plugin in vibe-log-cli.
 */

import { pluginRegistry } from '../src/plugins/core/plugin-registry.js';
import { orchestrationTracker } from '../src/plugins/orchestration-tracker/index.js';
import type { PluginConfig } from '../src/plugins/core/types.js';

// ============================================================================
// Example 1: Basic Plugin Registration
// ============================================================================

/**
 * Enable orchestration tracking with default settings
 */
async function example1_basicRegistration() {
  console.log('Example 1: Basic Registration\n');

  const config: PluginConfig = {
    enabled: true,
    settings: {
      // Use defaults
      agentsDir: '.claude/agents',
      skillsDir: 'skills',
      agentPatterns: ['*.md'],
      skillFormats: ['SKILL.md', 'skill.yaml', 'skill.json'],
    },
  };

  await pluginRegistry.register(orchestrationTracker, config);

  console.log('✅ Orchestration tracker enabled with default settings');
  console.log('   - Agents: .claude/agents/*.md');
  console.log('   - Skills: skills/*/SKILL.md\n');
}

// ============================================================================
// Example 2: Custom Configuration
// ============================================================================

/**
 * Register plugin with custom paths and patterns
 */
async function example2_customConfiguration() {
  console.log('Example 2: Custom Configuration\n');

  const config: PluginConfig = {
    enabled: true,
    settings: {
      // Custom paths
      agentsDir: 'custom/agents',
      skillsDir: 'custom-skills',

      // Support YAML and JSON agent definitions
      agentPatterns: ['*.md', '*.yaml', '*.json'],

      // Only look for skill.yaml files
      skillFormats: ['skill.yaml'],

      // Custom detection patterns
      detectionPatterns: {
        agentSpawn: [
          'Task tool',
          '@agent-',
          'delegating to',
          'spawning agent',
          'CrewAI spawn', // Support CrewAI
        ],
        skillInvoke: [
          'using skill',
          'invoke skill',
          'skill:',
          'Skill:',
          'apply skill', // Custom pattern
        ],
        hookExecution: [
          'hook success',
          'hook tracked',
          'Hook executed',
          '[HOOK]', // Custom marker
        ],
      },
    },
    cache: {
      enabled: true,
      ttlSeconds: 600, // 10 minutes
    },
  };

  await pluginRegistry.register(orchestrationTracker, config);

  console.log('✅ Orchestration tracker enabled with custom settings');
  console.log('   - Agents: custom/agents/*.{md,yaml,json}');
  console.log('   - Skills: custom-skills/*/skill.yaml');
  console.log('   - Cache: 10 minutes\n');
}

// ============================================================================
// Example 3: Programmatic Metrics Querying
// ============================================================================

/**
 * Query orchestration metrics programmatically
 */
async function example3_queryMetrics() {
  console.log('Example 3: Query Metrics\n');

  // Enable plugin first
  await example1_basicRegistration();

  // Simulate querying metrics (in real usage, this would be from storage)
  const sessionId = 'abc-123-def-456';

  // Import storage (assuming it's implemented)
  const { OrchestrationStorage } = await import(
    '../src/plugins/orchestration-tracker/storage.js'
  );

  const storage = new OrchestrationStorage('~/.vibe-log/orchestration');

  try {
    const session = await storage.loadSession(sessionId);

    console.log('Session Metrics:');
    console.log(`  - Total Agents: ${session.agents.length}`);
    console.log(`  - Total Skills Used: ${Object.keys(session.skills).length}`);
    console.log(`  - Total Hooks: ${Object.keys(session.hooks).length}`);
    console.log(`  - Efficiency Score: ${session.metrics.efficiency_score}\n`);

    // Find bottleneck agents
    if (session.metrics.bottleneck_agents.length > 0) {
      console.log('⚠️  Bottleneck Agents:');
      session.metrics.bottleneck_agents.forEach((agent) => {
        console.log(`   - ${agent}`);
      });
      console.log('');
    }

    // Display recommendations
    if (session.metrics.recommendations.length > 0) {
      console.log('💡 Recommendations:');
      session.metrics.recommendations.forEach((rec) => {
        console.log(`   - ${rec}`);
      });
      console.log('');
    }
  } catch (error) {
    console.error('❌ Failed to load session:', error);
  }
}

// ============================================================================
// Example 4: CLI Command Usage
// ============================================================================

/**
 * Demonstrate CLI command usage (bash commands)
 */
async function example4_cliCommands() {
  console.log('Example 4: CLI Command Usage\n');

  console.log('View all metrics for current session:');
  console.log('  $ npx vibe-log-cli orchestration\n');

  console.log('View metrics for specific session:');
  console.log('  $ npx vibe-log-cli orchestration --session abc-123\n');

  console.log('View only agent metrics:');
  console.log('  $ npx vibe-log-cli orchestration --agents\n');

  console.log('View only hook metrics:');
  console.log('  $ npx vibe-log-cli orchestration --hooks\n');

  console.log('View only skill metrics:');
  console.log('  $ npx vibe-log-cli orchestration --skills\n');

  console.log('Export metrics to JSON:');
  console.log('  $ npx vibe-log-cli orchestration --format json > metrics.json\n');

  console.log('Export metrics to CSV:');
  console.log(
    '  $ npx vibe-log-cli orchestration --format csv --export metrics.csv\n'
  );
}

// ============================================================================
// Example 5: Conditional Plugin Loading
// ============================================================================

/**
 * Enable plugin only in specific environments
 */
async function example5_conditionalLoading() {
  console.log('Example 5: Conditional Loading\n');

  const isMultiAgentProject = await checkForMultiAgentSetup();

  const config: PluginConfig = {
    // Only enable if project uses multi-agent orchestration
    enabled: isMultiAgentProject,
    settings: {
      agentsDir: '.claude/agents',
      skillsDir: 'skills',
      agentPatterns: ['*.md'],
      skillFormats: ['SKILL.md'],
    },
  };

  await pluginRegistry.register(orchestrationTracker, config);

  if (isMultiAgentProject) {
    console.log('✅ Multi-agent project detected - plugin enabled');
  } else {
    console.log('ℹ️  Single-agent project - plugin disabled');
  }
  console.log('');
}

/**
 * Helper: Check if project uses multi-agent orchestration
 */
async function checkForMultiAgentSetup(): Promise<boolean> {
  // Check for .claude/agents directory
  const fs = await import('fs/promises');
  const path = await import('path');

  try {
    const agentsDir = path.join(process.cwd(), '.claude/agents');
    const files = await fs.readdir(agentsDir);

    // Consider it multi-agent if there are 2+ agent definitions
    return files.filter((f) => f.endsWith('.md')).length >= 2;
  } catch {
    return false;
  }
}

// ============================================================================
// Example 6: Performance Monitoring
// ============================================================================

/**
 * Monitor plugin performance overhead
 */
async function example6_performanceMonitoring() {
  console.log('Example 6: Performance Monitoring\n');

  const config: PluginConfig = {
    enabled: true,
    settings: {
      agentsDir: '.claude/agents',
      skillsDir: 'skills',
      agentPatterns: ['*.md'],
      skillFormats: ['SKILL.md'],
    },
    cache: {
      enabled: true,
      ttlSeconds: 300,
    },
  };

  // Measure registration time
  const startTime = Date.now();
  await pluginRegistry.register(orchestrationTracker, config);
  const registrationTime = Date.now() - startTime;

  console.log(`✅ Plugin registered in ${registrationTime}ms`);

  // Get plugin info
  const loadedPlugin = pluginRegistry.get('orchestration-tracker');

  if (loadedPlugin) {
    console.log(`   - Load time: ${loadedPlugin.loadTime}ms`);
    console.log(`   - Cache enabled: ${config.cache?.enabled}`);
    console.log(`   - Cache TTL: ${config.cache?.ttlSeconds}s\n`);

    // Performance targets
    const TARGET_LOAD_TIME = 100; // ms
    if (loadedPlugin.loadTime > TARGET_LOAD_TIME) {
      console.log(
        `⚠️  Warning: Load time (${loadedPlugin.loadTime}ms) exceeds target (${TARGET_LOAD_TIME}ms)`
      );
      console.log('   Consider enabling caching or reducing discovery scope\n');
    } else {
      console.log('✅ Load time within target (<100ms)\n');
    }
  }
}

// ============================================================================
// Example 7: Integration with Existing Vibe-Log Features
// ============================================================================

/**
 * Use orchestration tracking alongside vibe-log's prompt analysis
 */
async function example7_vibeLogIntegration() {
  console.log('Example 7: Vibe-Log Integration\n');

  // Enable orchestration tracking
  const config: PluginConfig = {
    enabled: true,
    settings: {
      agentsDir: '.claude/agents',
      skillsDir: 'skills',
      agentPatterns: ['*.md'],
      skillFormats: ['SKILL.md'],
    },
  };

  await pluginRegistry.register(orchestrationTracker, config);

  console.log('✅ Orchestration tracker enabled');
  console.log('ℹ️  Vibe-log prompt analysis continues to work normally');
  console.log('');
  console.log('Combined insights:');
  console.log(
    '  - Prompt quality (vibe-log): Scores and improvement suggestions'
  );
  console.log(
    '  - Orchestration (plugin): Agent/skill/hook metrics and patterns'
  );
  console.log('');
  console.log('Example combined workflow:');
  console.log('  1. User submits prompt');
  console.log("  2. Vibe-log analyzes prompt quality → 'Gordon: 85/100'");
  console.log("  3. Orchestration detects agent spawn → 'Agent: desenvolvimento'");
  console.log('  4. Both insights available in session report\n');
}

// ============================================================================
// Example 8: Disabling Plugin
// ============================================================================

/**
 * Temporarily disable orchestration tracking
 */
async function example8_disablePlugin() {
  console.log('Example 8: Disable Plugin\n');

  // First, enable it
  await example1_basicRegistration();

  console.log('Disabling orchestration tracker...');

  // Unregister plugin
  await pluginRegistry.unregister('orchestration-tracker');

  console.log('✅ Plugin disabled');
  console.log('   - No orchestration data will be collected');
  console.log('   - Existing data preserved in ~/.vibe-log/orchestration/');
  console.log('   - Re-enable anytime with: npx vibe-log-cli config set ...\n');
}

// ============================================================================
// Run Examples
// ============================================================================

async function main() {
  console.log('='.repeat(70));
  console.log('ORCHESTRATION TRACKER PLUGIN - USAGE EXAMPLES');
  console.log('='.repeat(70));
  console.log('');

  try {
    // Run all examples
    await example1_basicRegistration();
    await example2_customConfiguration();
    // await example3_queryMetrics(); // Requires session data
    await example4_cliCommands();
    await example5_conditionalLoading();
    await example6_performanceMonitoring();
    await example7_vibeLogIntegration();
    await example8_disablePlugin();

    console.log('='.repeat(70));
    console.log('All examples completed successfully!');
    console.log('='.repeat(70));
  } catch (error) {
    console.error('❌ Error running examples:', error);
    process.exit(1);
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

// Export for use in tests
export {
  example1_basicRegistration,
  example2_customConfiguration,
  example3_queryMetrics,
  example4_cliCommands,
  example5_conditionalLoading,
  example6_performanceMonitoring,
  example7_vibeLogIntegration,
  example8_disablePlugin,
};
