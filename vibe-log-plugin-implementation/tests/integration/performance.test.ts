/**
 * Integration Tests: Performance Benchmarks
 *
 * Performance tests for orchestration tracking
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mkdir, writeFile, rm } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';
import { PluginRegistry } from '../../src/plugins/core/plugin-registry.js';
import { HookTrigger } from '../../src/plugins/core/types.js';
import { createMockSession, measureTime } from '../helpers.js';

describe('Performance Benchmarks', () => {
  let testDir: string;
  let registry: PluginRegistry;
  let orchestrationTracker: any;

  beforeEach(async () => {
    testDir = join(tmpdir(), `vibe-log-perf-${Date.now()}`);
    await mkdir(testDir, { recursive: true });

    registry = PluginRegistry.getInstance();
    await registry.clear();

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
    if (testDir) {
      await rm(testDir, { recursive: true, force: true });
    }
    await registry.clear();
  });

  describe('Agent Discovery Performance', () => {
    it.skipIf(!orchestrationTracker)(
      'should discover 10 agents in <50ms',
      async () => {
        // Create test project with 10 agents
        await mkdir(join(testDir, '.claude', 'agents'), { recursive: true });

        for (let i = 0; i < 10; i++) {
          await writeFile(
            join(testDir, '.claude', 'agents', `agent-${i}.md`),
            `---
name: agent-${i}
type: virtual
description: Test agent ${i}
capabilities:
  - Capability ${i}
---`
          );
        }

        await registry.register(orchestrationTracker, {
          enabled: true,
          settings: {
            agentsDir: '.claude/agents',
            skillsDir: 'skills',
          },
        });

        const session = createMockSession({ projectDir: testDir });

        const { duration } = await measureTime(() =>
          registry.triggerHook(HookTrigger.SessionStart, session)
        );

        console.log(`Agent discovery (10 agents): ${duration}ms`);
        expect(duration).toBeLessThan(50);
      }
    );

    it.skipIf(!orchestrationTracker)(
      'should discover 50 agents in <100ms',
      async () => {
        await mkdir(join(testDir, '.claude', 'agents'), { recursive: true });

        for (let i = 0; i < 50; i++) {
          await writeFile(
            join(testDir, '.claude', 'agents', `agent-${i}.md`),
            `---
name: agent-${i}
type: virtual
description: Test agent ${i}
---`
          );
        }

        await registry.register(orchestrationTracker, {
          enabled: true,
          settings: {
            agentsDir: '.claude/agents',
            skillsDir: 'skills',
          },
        });

        const session = createMockSession({ projectDir: testDir });

        const { duration } = await measureTime(() =>
          registry.triggerHook(HookTrigger.SessionStart, session)
        );

        console.log(`Agent discovery (50 agents): ${duration}ms`);
        expect(duration).toBeLessThan(100);
      }
    );
  });

  describe('Skill Discovery Performance', () => {
    it.skipIf(!orchestrationTracker)(
      'should discover 10 skills in <50ms',
      async () => {
        await mkdir(join(testDir, 'skills'), { recursive: true });

        for (let i = 0; i < 10; i++) {
          await mkdir(join(testDir, 'skills', `skill-${i}`), {
            recursive: true,
          });
          await writeFile(
            join(testDir, 'skills', `skill-${i}`, 'SKILL.md'),
            `---
name: skill-${i}
description: Test skill ${i}
triggers:
  - trigger-${i}
---`
          );
        }

        await registry.register(orchestrationTracker, {
          enabled: true,
          settings: {
            agentsDir: '.claude/agents',
            skillsDir: 'skills',
          },
        });

        const session = createMockSession({ projectDir: testDir });

        const { duration } = await measureTime(() =>
          registry.triggerHook(HookTrigger.SessionStart, session)
        );

        console.log(`Skill discovery (10 skills): ${duration}ms`);
        expect(duration).toBeLessThan(50);
      }
    );

    it.skipIf(!orchestrationTracker)(
      'should discover 30 skills in <100ms',
      async () => {
        await mkdir(join(testDir, 'skills'), { recursive: true });

        for (let i = 0; i < 30; i++) {
          await mkdir(join(testDir, 'skills', `skill-${i}`), {
            recursive: true,
          });
          await writeFile(
            join(testDir, 'skills', `skill-${i}`, 'SKILL.md'),
            `---
name: skill-${i}
description: Test skill ${i}
triggers:
  - trigger-${i}
---`
          );
        }

        await registry.register(orchestrationTracker, {
          enabled: true,
          settings: {
            agentsDir: '.claude/agents',
            skillsDir: 'skills',
          },
        });

        const session = createMockSession({ projectDir: testDir });

        const { duration } = await measureTime(() =>
          registry.triggerHook(HookTrigger.SessionStart, session)
        );

        console.log(`Skill discovery (30 skills): ${duration}ms`);
        expect(duration).toBeLessThan(100);
      }
    );
  });

  describe('Hook Parsing Performance', () => {
    it.skipIf(!orchestrationTracker)(
      'should parse settings.json with 10 hooks in <20ms',
      async () => {
        const hooks = {
          hooks: {} as Record<string, any>,
        };

        // Create 10 different hook triggers
        const triggers = [
          'SessionStart',
          'SessionEnd',
          'UserPromptSubmit',
          'PreToolUse',
          'PostToolUse',
        ];

        triggers.forEach((trigger) => {
          hooks.hooks[trigger] = {
            hooks: [
              {
                command: `node ${trigger.toLowerCase()}-hook-1.js`,
                description: `${trigger} hook 1`,
              },
              {
                command: `node ${trigger.toLowerCase()}-hook-2.js`,
                description: `${trigger} hook 2`,
              },
            ],
          };
        });

        await mkdir(join(testDir, '.claude'), { recursive: true });
        await writeFile(
          join(testDir, '.claude', 'settings.json'),
          JSON.stringify(hooks)
        );

        await registry.register(orchestrationTracker, {
          enabled: true,
          settings: {
            agentsDir: '.claude/agents',
            skillsDir: 'skills',
          },
        });

        const session = createMockSession({ projectDir: testDir });

        const { duration } = await measureTime(() =>
          registry.triggerHook(HookTrigger.SessionStart, session)
        );

        console.log(`Hook parsing (10 hooks): ${duration}ms`);
        expect(duration).toBeLessThan(20);
      }
    );
  });

  describe('Full Plugin Cycle Performance', () => {
    it.skipIf(!orchestrationTracker)(
      'should complete full cycle in <100ms',
      async () => {
        // Setup realistic project
        await mkdir(join(testDir, '.claude', 'agents'), { recursive: true });
        await mkdir(join(testDir, 'skills'), { recursive: true });

        // 5 agents
        for (let i = 0; i < 5; i++) {
          await writeFile(
            join(testDir, '.claude', 'agents', `agent-${i}.md`),
            `---
name: agent-${i}
type: virtual
description: Test agent ${i}
---`
          );
        }

        // 10 skills
        for (let i = 0; i < 10; i++) {
          await mkdir(join(testDir, 'skills', `skill-${i}`), {
            recursive: true,
          });
          await writeFile(
            join(testDir, 'skills', `skill-${i}`, 'SKILL.md'),
            `---
name: skill-${i}
description: Test skill ${i}
triggers:
  - trigger-${i}
---`
          );
        }

        // Settings with hooks
        await writeFile(
          join(testDir, '.claude', 'settings.json'),
          JSON.stringify({
            hooks: {
              UserPromptSubmit: {
                hooks: [
                  { command: 'node hook1.js', description: 'Hook 1' },
                  { command: 'node hook2.js', description: 'Hook 2' },
                ],
              },
            },
          })
        );

        await registry.register(orchestrationTracker, {
          enabled: true,
          settings: {
            agentsDir: '.claude/agents',
            skillsDir: 'skills',
            storageDir: join(testDir, '.vibe-log'),
          },
        });

        const session = createMockSession({ projectDir: testDir });

        // Measure full cycle
        const start = Date.now();

        await registry.triggerHook(HookTrigger.SessionStart, session);
        await registry.triggerHook(HookTrigger.UserPromptSubmit, session, {
          prompt: 'Test prompt',
        });
        await registry.triggerHook(HookTrigger.SessionEnd, session);

        const duration = Date.now() - start;

        console.log(`Full cycle (5 agents, 10 skills, 2 hooks): ${duration}ms`);
        expect(duration).toBeLessThan(100);
      }
    );
  });

  describe('Skill Detection Performance', () => {
    it.skipIf(!orchestrationTracker)(
      'should detect skill in prompt in <10ms',
      async () => {
        await mkdir(join(testDir, 'skills', 'test-skill'), { recursive: true });
        await writeFile(
          join(testDir, 'skills', 'test-skill', 'SKILL.md'),
          `---
name: test-skill
description: Test skill
triggers:
  - test trigger
  - another trigger
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

        // Measure skill detection
        const { duration } = await measureTime(() =>
          registry.triggerHook(HookTrigger.UserPromptSubmit, session, {
            prompt: 'Use the test trigger for this task',
          })
        );

        console.log(`Skill detection: ${duration}ms`);
        expect(duration).toBeLessThan(10);
      }
    );
  });

  describe('Memory Usage', () => {
    it.skipIf(!orchestrationTracker)(
      'should not leak memory over 100 iterations',
      async () => {
        await mkdir(join(testDir, '.claude', 'agents'), { recursive: true });
        await writeFile(
          join(testDir, '.claude', 'agents', 'agent.md'),
          `---
name: test-agent
type: virtual
description: Test agent
---`
        );

        await registry.register(orchestrationTracker, {
          enabled: true,
          settings: {
            agentsDir: '.claude/agents',
            skillsDir: 'skills',
          },
        });

        const memBefore = process.memoryUsage().heapUsed;

        // Run 100 iterations
        for (let i = 0; i < 100; i++) {
          const session = createMockSession({
            sessionId: `session-${i}`,
            projectDir: testDir,
          });

          await registry.triggerHook(HookTrigger.SessionStart, session);
          await registry.triggerHook(HookTrigger.UserPromptSubmit, session, {
            prompt: 'Test prompt',
          });
          await registry.triggerHook(HookTrigger.SessionEnd, session);
        }

        const memAfter = process.memoryUsage().heapUsed;
        const memDelta = (memAfter - memBefore) / 1024 / 1024; // MB

        console.log(`Memory delta after 100 iterations: ${memDelta.toFixed(2)}MB`);

        // Allow reasonable memory growth (< 10MB for 100 iterations)
        expect(memDelta).toBeLessThan(10);
      }
    );
  });

  describe('Parallel Processing', () => {
    it.skipIf(!orchestrationTracker)(
      'should handle 5 concurrent sessions efficiently',
      async () => {
        await mkdir(join(testDir, '.claude', 'agents'), { recursive: true });
        await writeFile(
          join(testDir, '.claude', 'agents', 'agent.md'),
          `---
name: test-agent
type: virtual
description: Test agent
---`
        );

        await registry.register(orchestrationTracker, {
          enabled: true,
          settings: {
            agentsDir: '.claude/agents',
            skillsDir: 'skills',
          },
        });

        const sessions = Array.from({ length: 5 }, (_, i) =>
          createMockSession({
            sessionId: `concurrent-${i}`,
            projectDir: testDir,
          })
        );

        const { duration } = await measureTime(async () => {
          // Start all sessions in parallel
          await Promise.all(
            sessions.map((session) =>
              registry.triggerHook(HookTrigger.SessionStart, session)
            )
          );

          // Trigger prompts in parallel
          await Promise.all(
            sessions.map((session) =>
              registry.triggerHook(HookTrigger.UserPromptSubmit, session, {
                prompt: 'Test prompt',
              })
            )
          );

          // End all sessions in parallel
          await Promise.all(
            sessions.map((session) =>
              registry.triggerHook(HookTrigger.SessionEnd, session)
            )
          );
        });

        console.log(`5 concurrent sessions: ${duration}ms`);

        // Should be faster than 5x sequential (parallel benefit)
        expect(duration).toBeLessThan(250); // Generous limit
      }
    );
  });
});
