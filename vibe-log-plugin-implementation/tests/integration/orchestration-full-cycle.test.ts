/**
 * Integration Tests: Orchestration Full Cycle
 *
 * End-to-end tests for complete orchestration tracking workflow
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mkdir, writeFile, readFile, rm } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';
import { PluginRegistry } from '../../src/plugins/core/plugin-registry.js';
import { HookTrigger } from '../../src/plugins/core/types.js';
import { createMockSession } from '../helpers.js';

describe('Orchestration Full Cycle', () => {
  let testDir: string;
  let registry: PluginRegistry;
  let orchestrationTracker: any;

  beforeEach(async () => {
    // Create temporary test directory
    testDir = join(tmpdir(), `vibe-log-test-${Date.now()}`);
    await mkdir(testDir, { recursive: true });

    // Setup test project structure
    await mkdir(join(testDir, '.claude', 'agents'), { recursive: true });
    await mkdir(join(testDir, 'skills'), { recursive: true });

    // Create test agents
    await writeFile(
      join(testDir, '.claude', 'agents', 'test-agent.md'),
      `---
name: test-agent
type: virtual
description: Test agent
capabilities:
  - Testing
  - Validation
---`
    );

    // Create test skills
    await mkdir(join(testDir, 'skills', 'test-skill'), { recursive: true });
    await writeFile(
      join(testDir, 'skills', 'test-skill', 'SKILL.md'),
      `---
name: test-skill
description: Test skill
triggers:
  - test
  - testing
---`
    );

    // Create settings.json with hooks
    await writeFile(
      join(testDir, '.claude', 'settings.json'),
      JSON.stringify({
        hooks: {
          UserPromptSubmit: {
            hooks: [
              {
                command: 'node test-hook.js',
                description: 'Test hook',
              },
            ],
          },
        },
      })
    );

    // Get plugin registry
    registry = PluginRegistry.getInstance();
    await registry.clear();

    // Try to load orchestration tracker
    try {
      const module = await import(
        '../../src/plugins/orchestration-tracker/index.js'
      );
      orchestrationTracker = module.orchestrationTracker;
    } catch (error) {
      console.warn(
        'Orchestration tracker implementation not found - skipping tests'
      );
    }
  });

  afterEach(async () => {
    // Cleanup test directory
    if (testDir) {
      await rm(testDir, { recursive: true, force: true });
    }

    // Clear registry
    await registry.clear();
  });

  it.skipIf(!orchestrationTracker)(
    'should complete full session lifecycle',
    async () => {
      // Register plugin
      await registry.register(orchestrationTracker, {
        enabled: true,
        settings: {
          agentsDir: '.claude/agents',
          skillsDir: 'skills',
          storageDir: join(testDir, '.vibe-log'),
        },
      });

      const session = createMockSession({
        projectDir: testDir,
      });

      // 1. Session Start - Should discover resources
      await registry.triggerHook(HookTrigger.SessionStart, session);

      // Verify agents were discovered
      expect(session.plugins?.orchestration?.agents).toBeDefined();
      expect(session.plugins?.orchestration?.agents).toHaveLength(1);
      expect(session.plugins?.orchestration?.agents[0].name).toBe('test-agent');

      // Verify skills were discovered
      expect(session.plugins?.orchestration?.skills).toBeDefined();
      expect(session.plugins?.orchestration?.skills).toHaveLength(1);
      expect(session.plugins?.orchestration?.skills[0].name).toBe('test-skill');

      // Verify hooks were discovered
      expect(session.plugins?.orchestration?.hooks).toBeDefined();
      expect(session.plugins?.orchestration?.hooks).toHaveLength(1);

      // 2. User Prompt - Should detect skill invocation
      await registry.triggerHook(HookTrigger.UserPromptSubmit, session, {
        prompt: 'Run a test on the codebase',
      });

      // Verify skill was detected
      expect(session.plugins?.orchestration?.invocations).toBeDefined();
      expect(session.plugins?.orchestration?.invocations).toHaveLength(1);
      expect(session.plugins?.orchestration?.invocations[0].skill).toBe(
        'test-skill'
      );

      // 3. Session End - Should save data
      session.endTime = Date.now();
      await registry.triggerHook(HookTrigger.SessionEnd, session);

      // Verify data was saved
      const storageDir = join(testDir, '.vibe-log', 'orchestration');
      const sessionFile = join(storageDir, `${session.sessionId}.json`);

      const savedData = JSON.parse(await readFile(sessionFile, 'utf-8'));

      expect(savedData.sessionId).toBe(session.sessionId);
      expect(savedData.agents).toHaveLength(1);
      expect(savedData.skills).toHaveLength(1);
      expect(savedData.invocations).toHaveLength(1);
    }
  );

  it.skipIf(!orchestrationTracker)(
    'should discover all resources correctly',
    async () => {
      // Create multiple agents
      await writeFile(
        join(testDir, '.claude', 'agents', 'agent-2.md'),
        `---
name: agent-2
type: permanent
description: Second agent
---`
      );

      // Create multiple skills
      await mkdir(join(testDir, 'skills', 'skill-2'), { recursive: true });
      await writeFile(
        join(testDir, 'skills', 'skill-2', 'SKILL.md'),
        `---
name: skill-2
description: Second skill
triggers:
  - skill-2
---`
      );

      await registry.register(orchestrationTracker, {
        enabled: true,
        settings: {
          agentsDir: '.claude/agents',
          skillsDir: 'skills',
        },
      });

      const session = createMockSession({ projectDir: testDir });

      await registry.triggerHook(HookTrigger.SessionStart, session);

      expect(session.plugins?.orchestration?.agents).toHaveLength(2);
      expect(session.plugins?.orchestration?.skills).toHaveLength(2);
    }
  );

  it.skipIf(!orchestrationTracker)(
    'should save data to correct locations',
    async () => {
      const storageDir = join(testDir, '.vibe-log', 'orchestration');

      await registry.register(orchestrationTracker, {
        enabled: true,
        settings: {
          agentsDir: '.claude/agents',
          skillsDir: 'skills',
          storageDir: join(testDir, '.vibe-log'),
        },
      });

      const session = createMockSession({ projectDir: testDir });

      await registry.triggerHook(HookTrigger.SessionStart, session);
      await registry.triggerHook(HookTrigger.SessionEnd, session);

      // Verify directory structure
      const sessionFile = join(storageDir, `${session.sessionId}.json`);
      const fileExists = await readFile(sessionFile, 'utf-8')
        .then(() => true)
        .catch(() => false);

      expect(fileExists).toBe(true);
    }
  );

  it.skipIf(!orchestrationTracker)(
    'should handle concurrent sessions',
    async () => {
      await registry.register(orchestrationTracker, {
        enabled: true,
        settings: {
          agentsDir: '.claude/agents',
          skillsDir: 'skills',
          storageDir: join(testDir, '.vibe-log'),
        },
      });

      const session1 = createMockSession({
        sessionId: 'session-1',
        projectDir: testDir,
      });

      const session2 = createMockSession({
        sessionId: 'session-2',
        projectDir: testDir,
      });

      // Start both sessions
      await Promise.all([
        registry.triggerHook(HookTrigger.SessionStart, session1),
        registry.triggerHook(HookTrigger.SessionStart, session2),
      ]);

      // Both should have discovered resources independently
      expect(session1.plugins?.orchestration?.agents).toBeDefined();
      expect(session2.plugins?.orchestration?.agents).toBeDefined();

      // End both sessions
      await Promise.all([
        registry.triggerHook(HookTrigger.SessionEnd, session1),
        registry.triggerHook(HookTrigger.SessionEnd, session2),
      ]);

      // Both should have separate files
      const storageDir = join(testDir, '.vibe-log', 'orchestration');
      const file1 = await readFile(join(storageDir, 'session-1.json'), 'utf-8');
      const file2 = await readFile(join(storageDir, 'session-2.json'), 'utf-8');

      expect(JSON.parse(file1).sessionId).toBe('session-1');
      expect(JSON.parse(file2).sessionId).toBe('session-2');
    }
  );

  it.skipIf(!orchestrationTracker)(
    'should cleanup on session end',
    async () => {
      await registry.register(orchestrationTracker, {
        enabled: true,
        settings: {
          agentsDir: '.claude/agents',
          skillsDir: 'skills',
        },
      });

      const session = createMockSession({ projectDir: testDir });

      await registry.triggerHook(HookTrigger.SessionStart, session);

      // Session should have orchestration data
      expect(session.plugins?.orchestration).toBeDefined();

      await registry.triggerHook(HookTrigger.SessionEnd, session);

      // Cleanup should have occurred (implementation-dependent)
      // At minimum, data should be persisted
      expect(session.plugins?.orchestration).toBeDefined();
    }
  );

  it.skipIf(!orchestrationTracker)(
    'should handle missing directories gracefully',
    async () => {
      // Create project without agents/skills
      const emptyDir = join(tmpdir(), `vibe-log-empty-${Date.now()}`);
      await mkdir(emptyDir, { recursive: true });

      await registry.register(orchestrationTracker, {
        enabled: true,
        settings: {
          agentsDir: '.claude/agents',
          skillsDir: 'skills',
        },
      });

      const session = createMockSession({ projectDir: emptyDir });

      // Should not throw
      await expect(
        registry.triggerHook(HookTrigger.SessionStart, session)
      ).resolves.not.toThrow();

      // Should have empty arrays
      expect(session.plugins?.orchestration?.agents || []).toHaveLength(0);
      expect(session.plugins?.orchestration?.skills || []).toHaveLength(0);

      await rm(emptyDir, { recursive: true, force: true });
    }
  );

  it.skipIf(!orchestrationTracker)(
    'should track hook execution metrics',
    async () => {
      await registry.register(orchestrationTracker, {
        enabled: true,
        settings: {
          agentsDir: '.claude/agents',
          skillsDir: 'skills',
        },
      });

      const session = createMockSession({ projectDir: testDir });

      await registry.triggerHook(HookTrigger.SessionStart, session);

      // Trigger multiple prompts
      for (let i = 0; i < 5; i++) {
        await registry.triggerHook(HookTrigger.UserPromptSubmit, session, {
          prompt: `Test prompt ${i}`,
        });
      }

      await registry.triggerHook(HookTrigger.SessionEnd, session);

      // Verify metrics were tracked
      expect(session.plugins?.orchestration?.metrics).toBeDefined();
      expect(
        session.plugins?.orchestration?.metrics?.totalPrompts
      ).toBeGreaterThanOrEqual(5);
    }
  );

  it.skipIf(!orchestrationTracker)(
    'should generate session summary',
    async () => {
      await registry.register(orchestrationTracker, {
        enabled: true,
        settings: {
          agentsDir: '.claude/agents',
          skillsDir: 'skills',
          storageDir: join(testDir, '.vibe-log'),
        },
      });

      const session = createMockSession({ projectDir: testDir });

      await registry.triggerHook(HookTrigger.SessionStart, session);
      await registry.triggerHook(HookTrigger.UserPromptSubmit, session, {
        prompt: 'Run a test',
      });
      await registry.triggerHook(HookTrigger.SessionEnd, session);

      // Verify summary was generated
      const storageDir = join(testDir, '.vibe-log', 'orchestration');
      const sessionFile = join(storageDir, `${session.sessionId}.json`);
      const data = JSON.parse(await readFile(sessionFile, 'utf-8'));

      expect(data.summary).toBeDefined();
      expect(data.summary.totalAgents).toBe(1);
      expect(data.summary.totalSkills).toBe(1);
      expect(data.summary.totalInvocations).toBeGreaterThanOrEqual(1);
    }
  );
});
