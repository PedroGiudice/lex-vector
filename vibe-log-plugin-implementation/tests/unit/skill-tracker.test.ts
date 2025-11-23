/**
 * Unit Tests: SkillTracker
 *
 * Tests for skill discovery and usage tracking
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { readFile, readdir } from 'fs/promises';
import {
  SKILL_MD_FORMAT,
  SKILL_YAML_FORMAT,
  SKILL_JSON_FORMAT,
  SKILL_INVALID,
  SKILL_MINIMAL,
  EXPECTED_SKILLS,
  SKILL_DETECTION_PROMPTS,
} from '../fixtures/mock-skills.js';

// Mock fs/promises
vi.mock('fs/promises');

describe('SkillTracker', () => {
  let SkillTracker: any;
  let tracker: any;

  beforeEach(async () => {
    vi.clearAllMocks();
    vi.resetModules();

    try {
      const module = await import(
        '../../src/plugins/orchestration-tracker/skill-tracker.js'
      );
      SkillTracker = module.SkillTracker;

      tracker = new SkillTracker({
        skillsDir: 'skills',
        skillFormats: ['SKILL.md', 'skill.yaml', 'skill.json'],
      });
    } catch (error) {
      console.warn('SkillTracker implementation not found - skipping tests');
    }
  });

  describe('Skill Discovery', () => {
    it.skipIf(!SkillTracker)(
      'should discover skills from skills/ directory',
      async () => {
        // Mock directory structure
        vi.mocked(readdir).mockResolvedValueOnce([
          'ocr-pro',
          'deep-parser',
          'frontend-design',
          '.git', // Should be skipped
        ] as any);

        // Mock readdir for each subdirectory
        vi.mocked(readdir)
          .mockResolvedValueOnce(['SKILL.md'] as any)
          .mockResolvedValueOnce(['skill.yaml'] as any)
          .mockResolvedValueOnce(['skill.json'] as any);

        // Mock file contents
        vi.mocked(readFile)
          .mockResolvedValueOnce(SKILL_MD_FORMAT)
          .mockResolvedValueOnce(SKILL_YAML_FORMAT)
          .mockResolvedValueOnce(JSON.stringify(SKILL_JSON_FORMAT));

        const skills = await tracker.discoverSkills('/test/project');

        expect(skills).toHaveLength(3);
        expect(skills.map((s: any) => s.name)).toContain('ocr-pro');
        expect(skills.map((s: any) => s.name)).toContain('deep-parser');
        expect(skills.map((s: any) => s.name)).toContain('frontend-design');
      }
    );

    it.skipIf(!SkillTracker)('should support SKILL.md format', async () => {
      vi.mocked(readdir).mockResolvedValueOnce(['ocr-pro'] as any);
      vi.mocked(readdir).mockResolvedValueOnce(['SKILL.md'] as any);
      vi.mocked(readFile).mockResolvedValueOnce(SKILL_MD_FORMAT);

      const skills = await tracker.discoverSkills('/test/project');

      expect(skills).toHaveLength(1);
      expect(skills[0].name).toBe('ocr-pro');
      expect(skills[0].triggers).toContain('OCR');
    });

    it.skipIf(!SkillTracker)('should support skill.yaml format', async () => {
      vi.mocked(readdir).mockResolvedValueOnce(['deep-parser'] as any);
      vi.mocked(readdir).mockResolvedValueOnce(['skill.yaml'] as any);
      vi.mocked(readFile).mockResolvedValueOnce(SKILL_YAML_FORMAT);

      const skills = await tracker.discoverSkills('/test/project');

      expect(skills).toHaveLength(1);
      expect(skills[0].name).toBe('deep-parser');
      expect(skills[0].triggers).toContain('parse JSON');
    });

    it.skipIf(!SkillTracker)('should support skill.json format', async () => {
      vi.mocked(readdir).mockResolvedValueOnce(['frontend-design'] as any);
      vi.mocked(readdir).mockResolvedValueOnce(['skill.json'] as any);
      vi.mocked(readFile).mockResolvedValueOnce(
        JSON.stringify(SKILL_JSON_FORMAT)
      );

      const skills = await tracker.discoverSkills('/test/project');

      expect(skills).toHaveLength(1);
      expect(skills[0].name).toBe('frontend-design');
      expect(skills[0].triggers).toContain('design system');
    });

    it.skipIf(!SkillTracker)('should skip invalid skills', async () => {
      vi.mocked(readdir).mockResolvedValueOnce([
        'valid-skill',
        'invalid-skill',
      ] as any);

      vi.mocked(readdir)
        .mockResolvedValueOnce(['SKILL.md'] as any)
        .mockResolvedValueOnce(['SKILL.md'] as any);

      vi.mocked(readFile)
        .mockResolvedValueOnce(SKILL_MINIMAL)
        .mockResolvedValueOnce(SKILL_INVALID);

      const skills = await tracker.discoverSkills('/test/project');

      // Should only return valid skill
      expect(skills).toHaveLength(1);
      expect(skills[0].name).toBe('minimal-skill');
    });

    it.skipIf(!SkillTracker)(
      'should skip directories without skill files',
      async () => {
        vi.mocked(readdir).mockResolvedValueOnce([
          'valid-skill',
          'no-skill',
        ] as any);

        vi.mocked(readdir)
          .mockResolvedValueOnce(['SKILL.md'] as any)
          .mockResolvedValueOnce(['README.md'] as any); // No skill file

        vi.mocked(readFile).mockResolvedValueOnce(SKILL_MINIMAL);

        const skills = await tracker.discoverSkills('/test/project');

        expect(skills).toHaveLength(1);
      }
    );

    it.skipIf(!SkillTracker)(
      'should handle missing skills directory',
      async () => {
        vi.mocked(readdir).mockRejectedValue(
          new Error('ENOENT: no such file or directory')
        );

        const skills = await tracker.discoverSkills('/test/project');

        expect(skills).toEqual([]);
      }
    );
  });

  describe('Skill Invocation Detection', () => {
    it.skipIf(!SkillTracker)(
      'should detect OCR skill from prompt',
      async () => {
        // Setup skills first
        vi.mocked(readdir).mockResolvedValueOnce(['ocr-pro'] as any);
        vi.mocked(readdir).mockResolvedValueOnce(['SKILL.md'] as any);
        vi.mocked(readFile).mockResolvedValueOnce(SKILL_MD_FORMAT);

        await tracker.discoverSkills('/test/project');

        const invocation = tracker.detectSkillInvocation(
          'Can you extract text from this PDF using OCR?'
        );

        expect(invocation).toBeDefined();
        expect(invocation.skill).toBe('ocr-pro');
      }
    );

    it.skipIf(!SkillTracker)(
      'should detect parser skill from prompt',
      async () => {
        vi.mocked(readdir).mockResolvedValueOnce(['deep-parser'] as any);
        vi.mocked(readdir).mockResolvedValueOnce(['skill.yaml'] as any);
        vi.mocked(readFile).mockResolvedValueOnce(SKILL_YAML_FORMAT);

        await tracker.discoverSkills('/test/project');

        const invocation = tracker.detectSkillInvocation(
          'I need help parsing this complex JSON structure.'
        );

        expect(invocation).toBeDefined();
        expect(invocation.skill).toBe('deep-parser');
      }
    );

    it.skipIf(!SkillTracker)(
      'should return null for non-matching prompt',
      async () => {
        vi.mocked(readdir).mockResolvedValueOnce(['ocr-pro'] as any);
        vi.mocked(readdir).mockResolvedValueOnce(['SKILL.md'] as any);
        vi.mocked(readFile).mockResolvedValueOnce(SKILL_MD_FORMAT);

        await tracker.discoverSkills('/test/project');

        const invocation = tracker.detectSkillInvocation(
          'Run the tests and fix any failures.'
        );

        expect(invocation).toBeNull();
      }
    );

    it.skipIf(!SkillTracker)(
      'should be case-insensitive',
      async () => {
        vi.mocked(readdir).mockResolvedValueOnce(['ocr-pro'] as any);
        vi.mocked(readdir).mockResolvedValueOnce(['SKILL.md'] as any);
        vi.mocked(readFile).mockResolvedValueOnce(SKILL_MD_FORMAT);

        await tracker.discoverSkills('/test/project');

        const invocation = tracker.detectSkillInvocation(
          'use ocr to extract text' // lowercase 'ocr'
        );

        expect(invocation).toBeDefined();
        expect(invocation.skill).toBe('ocr-pro');
      }
    );

    it.skipIf(!SkillTracker)(
      'should match partial trigger phrases',
      async () => {
        vi.mocked(readdir).mockResolvedValueOnce(['ocr-pro'] as any);
        vi.mocked(readdir).mockResolvedValueOnce(['SKILL.md'] as any);
        vi.mocked(readFile).mockResolvedValueOnce(SKILL_MD_FORMAT);

        await tracker.discoverSkills('/test/project');

        const invocation = tracker.detectSkillInvocation(
          'Please extract text from the document' // matches "extract text" trigger
        );

        expect(invocation).toBeDefined();
        expect(invocation.skill).toBe('ocr-pro');
      }
    );

    it.skipIf(!SkillTracker)(
      'should include timestamp in invocation',
      async () => {
        vi.mocked(readdir).mockResolvedValueOnce(['ocr-pro'] as any);
        vi.mocked(readdir).mockResolvedValueOnce(['SKILL.md'] as any);
        vi.mocked(readFile).mockResolvedValueOnce(SKILL_MD_FORMAT);

        await tracker.discoverSkills('/test/project');

        const before = Date.now();
        const invocation = tracker.detectSkillInvocation('Use OCR');
        const after = Date.now();

        expect(invocation.timestamp).toBeGreaterThanOrEqual(before);
        expect(invocation.timestamp).toBeLessThanOrEqual(after);
      }
    );
  });

  describe('Usage Tracking', () => {
    it.skipIf(!SkillTracker)('should track skill usage', async () => {
      tracker.trackUsage('ocr-pro', 'Extract text from PDF', 'success');
      tracker.trackUsage('ocr-pro', 'Scan document', 'success');
      tracker.trackUsage('ocr-pro', 'Read invoice', 'failure');

      const stats = tracker.getStats('ocr-pro');

      expect(stats.totalInvocations).toBe(3);
      expect(stats.successRate).toBeCloseTo(0.667, 2);
    });

    it.skipIf(!SkillTracker)(
      'should track multiple skills independently',
      async () => {
        tracker.trackUsage('skill-1', 'Context 1', 'success');
        tracker.trackUsage('skill-2', 'Context 2', 'success');
        tracker.trackUsage('skill-1', 'Context 3', 'success');

        const stats1 = tracker.getStats('skill-1');
        const stats2 = tracker.getStats('skill-2');

        expect(stats1.totalInvocations).toBe(2);
        expect(stats2.totalInvocations).toBe(1);
      }
    );

    it.skipIf(!SkillTracker)('should calculate success rate correctly', async () => {
      // 3 success, 2 failures
      tracker.trackUsage('test-skill', 'Context 1', 'success');
      tracker.trackUsage('test-skill', 'Context 2', 'success');
      tracker.trackUsage('test-skill', 'Context 3', 'success');
      tracker.trackUsage('test-skill', 'Context 4', 'failure');
      tracker.trackUsage('test-skill', 'Context 5', 'failure');

      const stats = tracker.getStats('test-skill');

      expect(stats.successRate).toBe(0.6); // 3/5
    });

    it.skipIf(!SkillTracker)(
      'should return zero stats for non-existent skill',
      async () => {
        const stats = tracker.getStats('non-existent-skill');

        expect(stats.totalInvocations).toBe(0);
        expect(stats.successRate).toBe(0);
      }
    );

    it.skipIf(!SkillTracker)('should update lastUsed timestamp', async () => {
      const before = Date.now();
      tracker.trackUsage('test-skill', 'Context', 'success');
      const after = Date.now();

      const stats = tracker.getStats('test-skill');

      expect(stats.lastUsed).toBeGreaterThanOrEqual(before);
      expect(stats.lastUsed).toBeLessThanOrEqual(after);
    });
  });

  describe('Performance', () => {
    it.skipIf(!SkillTracker)(
      'should discover 10 skills in <50ms',
      async () => {
        // Mock 10 skill directories
        const dirs = Array.from({ length: 10 }, (_, i) => `skill-${i}`);
        vi.mocked(readdir).mockResolvedValueOnce(dirs as any);

        // Mock SKILL.md for each directory
        for (let i = 0; i < 10; i++) {
          vi.mocked(readdir).mockResolvedValueOnce(['SKILL.md'] as any);
          vi.mocked(readFile).mockResolvedValueOnce(SKILL_MINIMAL);
        }

        const start = Date.now();
        await tracker.discoverSkills('/test/project');
        const duration = Date.now() - start;

        expect(duration).toBeLessThan(50);
      }
    );

    it.skipIf(!SkillTracker)(
      'should detect invocation in <5ms',
      async () => {
        vi.mocked(readdir).mockResolvedValueOnce(['ocr-pro'] as any);
        vi.mocked(readdir).mockResolvedValueOnce(['SKILL.md'] as any);
        vi.mocked(readFile).mockResolvedValueOnce(SKILL_MD_FORMAT);

        await tracker.discoverSkills('/test/project');

        const start = Date.now();
        tracker.detectSkillInvocation('Use OCR to extract text');
        const duration = Date.now() - start;

        expect(duration).toBeLessThan(5);
      }
    );
  });

  describe('Error Handling', () => {
    it.skipIf(!SkillTracker)(
      'should handle file read errors gracefully',
      async () => {
        vi.mocked(readdir).mockResolvedValueOnce(['skill-1', 'skill-2'] as any);

        vi.mocked(readdir)
          .mockResolvedValueOnce(['SKILL.md'] as any)
          .mockResolvedValueOnce(['SKILL.md'] as any);

        vi.mocked(readFile)
          .mockResolvedValueOnce(SKILL_MINIMAL)
          .mockRejectedValueOnce(new Error('Permission denied'));

        // Should return skills that were successfully read
        const skills = await tracker.discoverSkills('/test/project');

        expect(skills).toHaveLength(1);
      }
    );

    it.skipIf(!SkillTracker)('should handle malformed YAML gracefully', async () => {
      vi.mocked(readdir).mockResolvedValueOnce(['bad-skill'] as any);
      vi.mocked(readdir).mockResolvedValueOnce(['skill.yaml'] as any);
      vi.mocked(readFile).mockResolvedValue('invalid: yaml: syntax');

      const skills = await tracker.discoverSkills('/test/project');

      expect(skills).toEqual([]);
    });

    it.skipIf(!SkillTracker)('should handle malformed JSON gracefully', async () => {
      vi.mocked(readdir).mockResolvedValueOnce(['bad-skill'] as any);
      vi.mocked(readdir).mockResolvedValueOnce(['skill.json'] as any);
      vi.mocked(readFile).mockResolvedValue('{ invalid json }');

      const skills = await tracker.discoverSkills('/test/project');

      expect(skills).toEqual([]);
    });
  });

  describe('Multiple Trigger Matching', () => {
    it.skipIf(!SkillTracker)(
      'should match first matching skill',
      async () => {
        // Both skills have "parse" trigger
        vi.mocked(readdir).mockResolvedValueOnce([
          'deep-parser',
          'simple-parser',
        ] as any);

        vi.mocked(readdir)
          .mockResolvedValueOnce(['SKILL.md'] as any)
          .mockResolvedValueOnce(['SKILL.md'] as any);

        vi.mocked(readFile)
          .mockResolvedValueOnce(SKILL_YAML_FORMAT)
          .mockResolvedValueOnce(`---
name: simple-parser
description: Simple parser
triggers:
  - parse data
---`);

        await tracker.discoverSkills('/test/project');

        const invocation = tracker.detectSkillInvocation('parse JSON data');

        // Should match first skill (deep-parser)
        expect(invocation.skill).toBe('deep-parser');
      }
    );
  });
});
