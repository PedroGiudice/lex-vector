/**
 * Orchestration CLI Command
 *
 * CLI command for viewing orchestration metrics using commander/chalk/ora
 */

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import { OrchestrationStorage } from '../../plugins/orchestration-tracker/storage.js';
import type { OrchestrationSession } from '../../plugins/orchestration-tracker/types.js';

/**
 * Create orchestration command
 *
 * @returns Commander command instance
 */
export function createOrchestrationCommand(): Command {
  const command = new Command('orchestration');

  command
    .description('View multi-agent orchestration metrics')
    .option('-s, --session <id>', 'Session ID to analyze')
    .option('--agents', 'Show agent metrics only')
    .option('--hooks', 'Show hook metrics only')
    .option('--skills', 'Show skill metrics only')
    .option('--latest', 'Analyze latest session', false)
    .option('--list', 'List all sessions', false)
    .option('--stats', 'Show storage statistics', false)
    .action(async (options) => {
      const storage = new OrchestrationStorage();

      try {
        // List sessions
        if (options.list) {
          await listSessions(storage);
          return;
        }

        // Show storage stats
        if (options.stats) {
          await showStorageStats(storage);
          return;
        }

        // Determine session ID
        let sessionId = options.session;

        if (!sessionId && options.latest) {
          const spinner = ora('Loading latest session...').start();
          sessionId = await storage.getLatestSessionId();
          spinner.stop();

          if (!sessionId) {
            console.log(chalk.yellow('⚠️  No sessions found'));
            return;
          }
        }

        if (!sessionId) {
          console.log(
            chalk.red(
              '❌ No session specified. Use --session <id>, --latest, or --list'
            )
          );
          return;
        }

        // Load and display session
        await displaySession(storage, sessionId, options);
      } catch (error) {
        console.error(
          chalk.red('❌ Error:'),
          (error as Error).message
        );
        process.exit(1);
      }
    });

  return command;
}

/**
 * Display orchestration session metrics
 */
async function displaySession(
  storage: OrchestrationStorage,
  sessionId: string,
  options: {
    agents?: boolean;
    hooks?: boolean;
    skills?: boolean;
  }
): Promise<void> {
  const spinner = ora(`Loading session ${sessionId}...`).start();

  let session: OrchestrationSession;

  try {
    session = await storage.loadSession(sessionId);
    spinner.succeed(
      chalk.green(`Loaded session ${chalk.bold(sessionId)}`)
    );
  } catch (error) {
    spinner.fail(chalk.red(`Session not found: ${sessionId}`));
    throw error;
  }

  console.log('');

  // Header
  console.log(chalk.bold.cyan('📊 Orchestration Metrics'));
  console.log(chalk.gray('─'.repeat(60)));
  console.log('');

  // Session info
  const startDate = new Date(session.startTime).toLocaleString();
  const endDate = session.endTime
    ? new Date(session.endTime).toLocaleString()
    : 'In progress';
  const duration = session.endTime
    ? formatDuration(session.endTime - session.startTime)
    : 'N/A';

  console.log(chalk.bold('Session Info:'));
  console.log(`  ${chalk.gray('ID:')}       ${sessionId}`);
  console.log(`  ${chalk.gray('Started:')}  ${startDate}`);
  console.log(`  ${chalk.gray('Ended:')}    ${endDate}`);
  console.log(`  ${chalk.gray('Duration:')} ${duration}`);
  console.log(`  ${chalk.gray('Project:')}  ${session.projectDir}`);
  console.log('');

  // Show all by default if no specific filter
  const showAll = !options.agents && !options.hooks && !options.skills;

  // Agents
  if (options.agents || showAll) {
    displayAgents(session);
  }

  // Hooks
  if (options.hooks || showAll) {
    displayHooks(session);
  }

  // Skills
  if (options.skills || showAll) {
    displaySkills(session);
  }

  // Summary
  displaySummary(session);
}

/**
 * Display agents table
 */
function displayAgents(session: OrchestrationSession): void {
  console.log(chalk.bold.blue('👥 Agents'));
  console.log(chalk.gray('─'.repeat(60)));

  if (session.agents.length === 0) {
    console.log(chalk.gray('  No agents found'));
    console.log('');
    return;
  }

  // Sort by invocations (descending)
  const sortedAgents = [...session.agents].sort(
    (a, b) => b.invocations - a.invocations
  );

  sortedAgents.forEach((agent, index) => {
    const { definition, invocations, successRate } = agent;
    const number = chalk.gray(`${index + 1}.`);
    const name = chalk.white(definition.name);
    const type =
      definition.type === 'permanent'
        ? chalk.green('[P]')
        : chalk.cyan('[V]');
    const invokeCount = chalk.yellow(`${invocations}×`);
    const success = successRate
      ? chalk.green(`${Math.round(successRate * 100)}%`)
      : '';

    console.log(`  ${number} ${type} ${name} ${invokeCount} ${success}`);

    if (definition.description && definition.description !== 'No description') {
      console.log(`     ${chalk.gray(definition.description)}`);
    }
  });

  console.log('');
}

/**
 * Display hooks table
 */
function displayHooks(session: OrchestrationSession): void {
  console.log(chalk.bold.magenta('🪝 Hooks'));
  console.log(chalk.gray('─'.repeat(60)));

  if (session.hooks.length === 0) {
    console.log(chalk.gray('  No hooks found'));
    console.log('');
    return;
  }

  // Sort by total executions (descending)
  const sortedHooks = [...session.hooks].sort(
    (a, b) => b.stats.totalExecutions - a.stats.totalExecutions
  );

  sortedHooks.forEach((hook, index) => {
    const { definition, stats } = hook;
    const number = chalk.gray(`${index + 1}.`);
    const name = chalk.white(definition.name);
    const executions = chalk.yellow(`${stats.totalExecutions}×`);
    const avgDuration = chalk.cyan(`${stats.avgDuration}ms`);
    const failureRate =
      stats.failureRate > 0
        ? chalk.red(`${Math.round(stats.failureRate * 100)}% fail`)
        : chalk.green('✓');

    console.log(
      `  ${number} ${name} ${executions} ${avgDuration} ${failureRate}`
    );

    // Show triggers
    if (definition.triggers.length > 0) {
      const triggers = definition.triggers.join(', ');
      console.log(`     ${chalk.gray(`Triggers: ${triggers}`)}`);
    }
  });

  console.log('');
}

/**
 * Display skills table
 */
function displaySkills(session: OrchestrationSession): void {
  console.log(chalk.bold.yellow('⚡ Skills'));
  console.log(chalk.gray('─'.repeat(60)));

  if (session.skills.length === 0) {
    console.log(chalk.gray('  No skills found'));
    console.log('');
    return;
  }

  // Sort by usage count (descending)
  const sortedSkills = [...session.skills].sort(
    (a, b) => b.usageCount - a.usageCount
  );

  sortedSkills.forEach((skill, index) => {
    const { definition, usageCount, effectiveness } = skill;
    const number = chalk.gray(`${index + 1}.`);
    const name = chalk.white(definition.name);
    const uses = chalk.yellow(`${usageCount}×`);
    const effect = effectiveness
      ? chalk.green(`${Math.round(effectiveness * 100)}%`)
      : '';

    console.log(`  ${number} ${name} ${uses} ${effect}`);

    // Show description
    if (definition.description && definition.description !== 'No description') {
      console.log(`     ${chalk.gray(definition.description)}`);
    }
  });

  console.log('');
}

/**
 * Display summary metrics
 */
function displaySummary(session: OrchestrationSession): void {
  const { metrics } = session;

  console.log(chalk.bold.green('📈 Summary'));
  console.log(chalk.gray('─'.repeat(60)));

  const rows = [
    ['Total Agents', metrics.totalAgents],
    ['Total Hooks', metrics.totalHooks],
    ['Total Skills', metrics.totalSkills],
    ['Agent Invocations', metrics.agentInvocations],
    ['Skill Usages', metrics.skillUsages],
    ['Hook Executions', metrics.hookExecutions],
    ['Avg Hook Duration', `${metrics.avgHookDuration}ms`],
  ];

  rows.forEach(([label, value]) => {
    console.log(
      `  ${chalk.gray(label + ':')} ${chalk.white(String(value))}`
    );
  });

  if (metrics.mostActiveAgent) {
    console.log(
      `  ${chalk.gray('Most Active Agent:')} ${chalk.cyan(metrics.mostActiveAgent)}`
    );
  }

  if (metrics.mostUsedSkill) {
    console.log(
      `  ${chalk.gray('Most Used Skill:')} ${chalk.yellow(metrics.mostUsedSkill)}`
    );
  }

  console.log('');
}

/**
 * List all sessions
 */
async function listSessions(storage: OrchestrationStorage): Promise<void> {
  const spinner = ora('Loading sessions...').start();

  const sessionIds = await storage.listSessions();

  spinner.stop();

  console.log('');
  console.log(chalk.bold.cyan('📋 Sessions'));
  console.log(chalk.gray('─'.repeat(60)));

  if (sessionIds.length === 0) {
    console.log(chalk.gray('  No sessions found'));
    console.log('');
    return;
  }

  console.log(`  Found ${chalk.yellow(sessionIds.length)} session(s):\n`);

  for (const sessionId of sessionIds.slice(0, 10)) {
    try {
      const session = await storage.loadSession(sessionId);
      const date = new Date(session.startTime).toLocaleString();
      const duration = session.endTime
        ? formatDuration(session.endTime - session.startTime)
        : chalk.gray('In progress');

      console.log(`  ${chalk.cyan('•')} ${chalk.white(sessionId)}`);
      console.log(`    ${chalk.gray(date)} ${chalk.gray('•')} ${duration}`);
      console.log(
        `    ${chalk.gray(`${session.metrics.totalAgents} agents, ${session.metrics.totalSkills} skills`)}`
      );
      console.log('');
    } catch (error) {
      console.log(`  ${chalk.red('✗')} ${chalk.white(sessionId)}`);
      console.log(`    ${chalk.red('Error loading session')}`);
      console.log('');
    }
  }

  if (sessionIds.length > 10) {
    console.log(
      chalk.gray(`  ... and ${sessionIds.length - 10} more session(s)`)
    );
    console.log('');
  }
}

/**
 * Show storage statistics
 */
async function showStorageStats(
  storage: OrchestrationStorage
): Promise<void> {
  const spinner = ora('Loading storage stats...').start();

  const stats = await storage.getStats();

  spinner.succeed(chalk.green('Storage statistics loaded'));

  console.log('');
  console.log(chalk.bold.cyan('💾 Storage Statistics'));
  console.log(chalk.gray('─'.repeat(60)));
  console.log(
    `  ${chalk.gray('Total Sessions:')} ${chalk.white(stats.totalSessions)}`
  );
  console.log(
    `  ${chalk.gray('Latest Session:')} ${chalk.white(stats.latestSession || 'N/A')}`
  );
  console.log(
    `  ${chalk.gray('Storage Directory:')} ${chalk.white(stats.storageDir)}`
  );
  console.log('');
}

/**
 * Format duration in human-readable format
 */
function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}
