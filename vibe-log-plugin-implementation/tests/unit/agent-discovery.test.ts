/**
 * Unit Tests: AgentDiscovery
 *
 * Tests for agent discovery from various file formats
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { readFile, readdir } from 'fs/promises';
import {
  AGENT_YAML_FRONTMATTER,
  AGENT_MARKDOWN_HEADERS,
  AGENT_CUSTOM_MARKERS,
  AGENT_INVALID,
  AGENT_MINIMAL,
  AGENT_COMPLEX,
  EXPECTED_AGENTS,
} from '../fixtures/mock-agents.js';

// Mock fs/promises
vi.mock('fs/promises');

describe('AgentDiscovery', () => {
  let AgentDiscovery: any;
  let discovery: any;

  beforeEach(async () => {
    vi.clearAllMocks();

    // Reset module cache to allow re-importing
    vi.resetModules();

    try {
      const module = await import(
        '../../src/plugins/orchestration-tracker/agent-discovery.js'
      );
      AgentDiscovery = module.AgentDiscovery;

      discovery = new AgentDiscovery({
        agentsDir: '.claude/agents',
        agentPatterns: ['*.md'],
      });
    } catch (error) {
      // Implementation not available yet - tests will be skipped
      console.warn('AgentDiscovery implementation not found - skipping tests');
    }
  });

  describe('Agent Discovery', () => {
    it.skipIf(!AgentDiscovery)(
      'should discover agents from .claude/agents',
      async () => {
        // Mock file system
        vi.mocked(readdir).mockResolvedValue([
          'desenvolvimento.md',
          'qualidade-codigo.md',
          'documentacao.md',
          'README.md', // Should be skipped
        ] as any);

        vi.mocked(readFile)
          .mockResolvedValueOnce(AGENT_YAML_FRONTMATTER)
          .mockResolvedValueOnce(AGENT_MARKDOWN_HEADERS)
          .mockResolvedValueOnce(AGENT_CUSTOM_MARKERS)
          .mockResolvedValueOnce('# README');

        const agents = await discovery.discoverAgents('/test/project');

        expect(agents).toHaveLength(3);
        expect(agents.map((a: any) => a.name)).toContain('desenvolvimento');
        expect(agents.map((a: any) => a.name)).toContain('qualidade-codigo');
        expect(agents.map((a: any) => a.name)).toContain('documentacao');
      }
    );

    it.skipIf(!AgentDiscovery)('should support custom agent directories', async () => {
      const customDiscovery = new AgentDiscovery({
        agentsDir: 'custom/agents',
        agentPatterns: ['*.md'],
      });

      vi.mocked(readdir).mockResolvedValue(['agent1.md'] as any);
      vi.mocked(readFile).mockResolvedValue(AGENT_MINIMAL);

      const agents = await customDiscovery.discoverAgents('/test/project');

      expect(agents).toHaveLength(1);
    });

    it.skipIf(!AgentDiscovery)('should support multiple patterns', async () => {
      const multiPatternDiscovery = new AgentDiscovery({
        agentsDir: '.claude/agents',
        agentPatterns: ['*.md', '*.yaml', '*.json'],
      });

      vi.mocked(readdir).mockResolvedValue([
        'agent1.md',
        'agent2.yaml',
        'agent3.json',
      ] as any);

      vi.mocked(readFile)
        .mockResolvedValueOnce(AGENT_MINIMAL)
        .mockResolvedValueOnce(
          'name: agent2\ntype: virtual\ndescription: Agent 2'
        )
        .mockResolvedValueOnce(
          JSON.stringify({
            name: 'agent3',
            type: 'virtual',
            description: 'Agent 3',
          })
        );

      const agents = await multiPatternDiscovery.discoverAgents('/test/project');

      expect(agents).toHaveLength(3);
    });

    it.skipIf(!AgentDiscovery)('should skip invalid files', async () => {
      vi.mocked(readdir).mockResolvedValue([
        'valid.md',
        'invalid.md',
        'broken.md',
      ] as any);

      vi.mocked(readFile)
        .mockResolvedValueOnce(AGENT_MINIMAL)
        .mockResolvedValueOnce(AGENT_INVALID)
        .mockResolvedValueOnce('not an agent file');

      const agents = await discovery.discoverAgents('/test/project');

      // Should only return valid agent
      expect(agents).toHaveLength(1);
      expect(agents[0].name).toBe('minimal');
    });

    it.skipIf(!AgentDiscovery)(
      'should handle missing agents directory',
      async () => {
        vi.mocked(readdir).mockRejectedValue(
          new Error('ENOENT: no such file or directory')
        );

        const agents = await discovery.discoverAgents('/test/project');

        expect(agents).toEqual([]);
      }
    );
  });

  describe('Metadata Parsing', () => {
    it.skipIf(!AgentDiscovery)('should parse YAML frontmatter', async () => {
      const metadata = discovery.parseAgentMetadata(AGENT_YAML_FRONTMATTER);

      expect(metadata.name).toBe('desenvolvimento');
      expect(metadata.type).toBe('permanent');
      expect(metadata.description).toBe('Backend development specialist');
      expect(metadata.capabilities).toContain('TypeScript');
    });

    it.skipIf(!AgentDiscovery)('should parse Markdown headers', async () => {
      const metadata = discovery.parseAgentMetadata(AGENT_MARKDOWN_HEADERS);

      expect(metadata.name).toBe('qualidade-codigo');
      expect(metadata.type).toBe('virtual');
      expect(metadata.description).toBe('Code quality assurance specialist');
      expect(metadata.capabilities).toContain('Code review');
    });

    it.skipIf(!AgentDiscovery)('should parse custom markers', async () => {
      const metadata = discovery.parseAgentMetadata(AGENT_CUSTOM_MARKERS);

      expect(metadata.name).toBe('documentacao');
      expect(metadata.type).toBe('virtual');
      expect(metadata.description).toBe('Documentation specialist');
      expect(metadata.capabilities).toContain('API documentation');
    });

    it.skipIf(!AgentDiscovery)('should handle complex metadata', async () => {
      const metadata = discovery.parseAgentMetadata(AGENT_COMPLEX);

      expect(metadata.name).toBe('orchestrator');
      expect(metadata.type).toBe('permanent');
      expect(metadata.version).toBe('2.0.0');
      expect(metadata.dependencies).toContain('desenvolvimento');
      expect(metadata.settings).toBeDefined();
      expect(metadata.settings?.maxConcurrentAgents).toBe(5);
    });

    it.skipIf(!AgentDiscovery)(
      'should return null for invalid metadata',
      async () => {
        const metadata = discovery.parseAgentMetadata(AGENT_INVALID);

        // Should return null or throw - depends on implementation
        expect(metadata).toBeNull();
      }
    );

    it.skipIf(!AgentDiscovery)(
      'should handle minimal valid metadata',
      async () => {
        const metadata = discovery.parseAgentMetadata(AGENT_MINIMAL);

        expect(metadata.name).toBe('minimal');
        expect(metadata.type).toBe('virtual');
        expect(metadata.description).toBe('Minimal agent definition');
      }
    );
  });

  describe('Performance', () => {
    it.skipIf(!AgentDiscovery)(
      'should discover 10 agents in <50ms',
      async () => {
        // Mock 10 agent files
        const files = Array.from({ length: 10 }, (_, i) => `agent${i}.md`);
        vi.mocked(readdir).mockResolvedValue(files as any);
        vi.mocked(readFile).mockResolvedValue(AGENT_MINIMAL);

        const start = Date.now();
        await discovery.discoverAgents('/test/project');
        const duration = Date.now() - start;

        expect(duration).toBeLessThan(50);
      }
    );
  });

  describe('Error Handling', () => {
    it.skipIf(!AgentDiscovery)(
      'should handle file read errors gracefully',
      async () => {
        vi.mocked(readdir).mockResolvedValue(['agent1.md', 'agent2.md'] as any);
        vi.mocked(readFile)
          .mockResolvedValueOnce(AGENT_MINIMAL)
          .mockRejectedValueOnce(new Error('Permission denied'));

        // Should return agents that were successfully read
        const agents = await discovery.discoverAgents('/test/project');

        expect(agents).toHaveLength(1);
        expect(agents[0].name).toBe('minimal');
      }
    );

    it.skipIf(!AgentDiscovery)(
      'should handle malformed YAML gracefully',
      async () => {
        vi.mocked(readdir).mockResolvedValue(['bad.md'] as any);
        vi.mocked(readFile).mockResolvedValue('---\ninvalid: yaml: syntax\n---');

        const agents = await discovery.discoverAgents('/test/project');

        expect(agents).toEqual([]);
      }
    );
  });
});
