/**
 * Mock Hook Fixtures
 *
 * Sample hook definitions and settings.json structures
 */

/**
 * Sample settings.json with hooks configuration
 */
export const MOCK_SETTINGS_JSON = {
  hooks: {
    UserPromptSubmit: {
      hooks: [
        {
          command: 'node .claude/hooks/invoke-legal-braniac-hybrid.js',
          description: 'Legal-Braniac agent detection',
        },
        {
          command: 'node .claude/hooks/session-context-hybrid.js',
          description: 'Session context collection',
        },
        {
          command: 'npx vibe-log-cli analyze-prompt --stdin',
          description: 'Gordon Co-pilot analysis',
        },
      ],
    },
    SessionStart: {
      hooks: [
        {
          command: 'bash .claude/hooks/session-init.sh',
          description: 'Initialize session data',
        },
      ],
    },
    PreToolUse: {
      hooks: [
        {
          command: 'node .claude/hooks/tool-validator.js',
          description: 'Validate tool parameters',
        },
      ],
    },
  },
  statusLine: {
    enabled: true,
    format: 'Legal-Braniac | {agents}ag {skills}sk {hooks}h',
  },
};

/**
 * Minimal settings.json (no hooks)
 */
export const MOCK_SETTINGS_MINIMAL = {
  version: '1.0.0',
};

/**
 * Settings with malformed hooks
 */
export const MOCK_SETTINGS_MALFORMED = {
  hooks: {
    UserPromptSubmit: {
      // Missing 'hooks' array
      command: 'node something.js',
    },
  },
};

/**
 * Expected parsed hook definitions
 */
export const EXPECTED_HOOKS = [
  {
    name: 'invoke-legal-braniac-hybrid',
    triggers: ['UserPromptSubmit'],
    command: 'node .claude/hooks/invoke-legal-braniac-hybrid.js',
    description: 'Legal-Braniac agent detection',
  },
  {
    name: 'session-context-hybrid',
    triggers: ['UserPromptSubmit'],
    command: 'node .claude/hooks/session-context-hybrid.js',
    description: 'Session context collection',
  },
  {
    name: 'vibe-log-cli',
    triggers: ['UserPromptSubmit'],
    command: 'npx vibe-log-cli analyze-prompt --stdin',
    description: 'Gordon Co-pilot analysis',
  },
  {
    name: 'session-init',
    triggers: ['SessionStart'],
    command: 'bash .claude/hooks/session-init.sh',
    description: 'Initialize session data',
  },
  {
    name: 'tool-validator',
    triggers: ['PreToolUse'],
    command: 'node .claude/hooks/tool-validator.js',
    description: 'Validate tool parameters',
  },
];

/**
 * Mock hook execution stats
 */
export const MOCK_HOOK_STATS = {
  'invoke-legal-braniac-hybrid': {
    totalExecutions: 15,
    avgDuration: 25.3,
    failureRate: 0.0,
    lastRun: Date.now() - 3600000, // 1 hour ago
  },
  'session-context-hybrid': {
    totalExecutions: 15,
    avgDuration: 18.7,
    failureRate: 0.067, // 1 failure out of 15
    lastRun: Date.now() - 3600000,
  },
  'vibe-log-cli': {
    totalExecutions: 15,
    avgDuration: 1200.5,
    failureRate: 0.0,
    lastRun: Date.now() - 3600000,
  },
};
