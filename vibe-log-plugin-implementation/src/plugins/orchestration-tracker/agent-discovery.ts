/**
 * Agent Discovery - Generic Agent Detection
 *
 * Discovers agents in Claude Code projects using configurable patterns
 */

import { readdir, readFile, stat } from 'fs/promises';
import { join, basename, extname } from 'path';
import type {
  OrchestrationConfig,
  AgentDefinition,
  AgentMetadata,
} from './types.js';

/**
 * Agent Discovery Service
 */
export class AgentDiscovery {
  constructor(private config: OrchestrationConfig) {}

  /**
   * Discover all agents in project directory
   *
   * @param projectDir - Project root directory
   * @returns Array of agent definitions
   */
  async discoverAgents(projectDir: string): Promise<AgentDefinition[]> {
    const agentsDir = join(projectDir, this.config.agentsDir);

    try {
      // Check if agents directory exists
      await stat(agentsDir);
    } catch (error) {
      // Agents directory doesn't exist - return empty array
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        this.log(`Agents directory not found: ${agentsDir}`);
        return [];
      }
      throw error;
    }

    const agents: AgentDefinition[] = [];
    const errors: string[] = [];

    try {
      // Read all files in agents directory
      const entries = await readdir(agentsDir, { withFileTypes: true });

      // Process matching files
      const processPromises = entries.map(async (entry) => {
        const filePath = join(agentsDir, entry.name);

        // Skip directories
        if (entry.isDirectory()) {
          return null;
        }

        // Check if file matches configured patterns
        const matches = this.config.agentPatterns.some((pattern) =>
          this.matchesPattern(entry.name, pattern)
        );

        if (!matches) {
          return null;
        }

        try {
          return await this.parseAgentFile(filePath);
        } catch (error) {
          errors.push(`${entry.name}: ${(error as Error).message}`);
          return null;
        }
      });

      const results = await Promise.all(processPromises);
      agents.push(...results.filter((a): a is AgentDefinition => a !== null));

      // Log errors (non-blocking)
      if (errors.length > 0 && this.config.verbose) {
        console.warn(`⚠️  ${errors.length} agent file(s) failed to parse:`);
        errors.forEach((err) => console.warn(`   - ${err}`));
      }

      this.log(
        `Discovered ${agents.length} agent(s) from ${agentsDir}`
      );

      return agents;
    } catch (error) {
      throw new Error(
        `Failed to discover agents in "${agentsDir}": ${(error as Error).message}`
      );
    }
  }

  /**
   * Parse agent file and extract metadata
   *
   * @param filePath - Path to agent file
   * @returns Agent definition
   */
  private async parseAgentFile(filePath: string): Promise<AgentDefinition> {
    const content = await readFile(filePath, 'utf-8');
    const ext = extname(filePath).toLowerCase();

    let metadata: AgentMetadata;

    // Parse based on file extension
    if (ext === '.md') {
      metadata = this.parseMarkdown(content);
    } else if (ext === '.yaml' || ext === '.yml') {
      metadata = this.parseYAML(content);
    } else if (ext === '.json') {
      metadata = this.parseJSON(content);
    } else {
      // Fallback: try all parsers
      metadata = this.parseMarkdown(content) ||
        this.parseYAML(content) ||
        this.parseJSON(content) ||
        {};
    }

    // Construct agent definition
    const name =
      metadata.name || basename(filePath, ext).replace(/[-_]/g, ' ');
    const description = metadata.description || 'No description';
    const capabilities = metadata.capabilities || [];
    const type = metadata.type || 'virtual';

    return {
      name,
      path: filePath,
      description,
      capabilities,
      type,
      metadata,
    };
  }

  /**
   * Parse Markdown file for agent metadata
   *
   * Supports:
   * - YAML frontmatter (---\nname: foo\n---)
   * - Markdown headers (# Agent Name)
   * - Custom markers ([AGENT: name])
   */
  parseMarkdown(content: string): AgentMetadata {
    const metadata: AgentMetadata = {};

    // 1. Try YAML frontmatter first
    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (frontmatterMatch) {
      const yamlContent = frontmatterMatch[1];
      Object.assign(metadata, this.parseYAML(yamlContent));
    }

    // 2. Extract from Markdown headers
    const h1Match = content.match(/^#\s+(.+)$/m);
    if (h1Match && !metadata.name) {
      metadata.name = h1Match[1].trim();
    }

    // 3. Extract description (first paragraph after title)
    const descMatch = content.match(/^#\s+.+\n\n(.+?)(?:\n\n|$)/m);
    if (descMatch && !metadata.description) {
      metadata.description = descMatch[1].trim();
    }

    // 4. Extract custom markers
    const markerMatch = content.match(/\[AGENT:\s*(.+?)\]/);
    if (markerMatch && !metadata.name) {
      metadata.name = markerMatch[1].trim();
    }

    // 5. Extract capabilities from lists
    if (!metadata.capabilities) {
      const capabilities: string[] = [];
      const listMatches = content.matchAll(/^[-*]\s+(.+)$/gm);
      for (const match of listMatches) {
        const item = match[1].trim();
        // Only include if looks like a capability (starts with verb or noun)
        if (/^[A-Z]/.test(item) && item.length < 100) {
          capabilities.push(item);
        }
      }
      if (capabilities.length > 0) {
        metadata.capabilities = capabilities.slice(0, 10); // Limit to 10
      }
    }

    return metadata;
  }

  /**
   * Parse YAML content
   */
  parseYAML(content: string): AgentMetadata {
    const metadata: AgentMetadata = {};

    try {
      // Simple YAML parser (handles basic key: value pairs)
      const lines = content.split('\n');

      for (const line of lines) {
        const match = line.match(/^(\w+):\s*(.+)$/);
        if (match) {
          const key = match[1];
          const value = match[2].trim();

          // Parse arrays (e.g., capabilities: [a, b, c])
          if (value.startsWith('[') && value.endsWith(']')) {
            metadata[key] = value
              .slice(1, -1)
              .split(',')
              .map((v) => v.trim().replace(/^["']|["']$/g, ''));
          }
          // Parse strings (remove quotes)
          else if (
            (value.startsWith('"') && value.endsWith('"')) ||
            (value.startsWith("'") && value.endsWith("'"))
          ) {
            metadata[key] = value.slice(1, -1);
          }
          // Parse booleans
          else if (value === 'true' || value === 'false') {
            metadata[key] = value === 'true';
          }
          // Parse numbers
          else if (/^\d+$/.test(value)) {
            metadata[key] = parseInt(value, 10);
          }
          // Plain string
          else {
            metadata[key] = value;
          }
        }
      }

      // Handle multi-line arrays (YAML list format)
      const capabilities: string[] = [];
      let inCapabilities = false;

      for (const line of lines) {
        if (line.match(/^capabilities:/)) {
          inCapabilities = true;
          continue;
        }

        if (inCapabilities) {
          const itemMatch = line.match(/^\s*-\s*(.+)$/);
          if (itemMatch) {
            capabilities.push(itemMatch[1].trim().replace(/^["']|["']$/g, ''));
          } else if (line.match(/^\w+:/)) {
            // New key - stop parsing capabilities
            inCapabilities = false;
          }
        }
      }

      if (capabilities.length > 0) {
        metadata.capabilities = capabilities;
      }
    } catch (error) {
      // YAML parsing failed - return partial metadata
      this.log(`YAML parse error: ${(error as Error).message}`);
    }

    return metadata;
  }

  /**
   * Parse JSON content
   */
  parseJSON(content: string): AgentMetadata {
    try {
      return JSON.parse(content) as AgentMetadata;
    } catch (error) {
      // JSON parsing failed
      this.log(`JSON parse error: ${(error as Error).message}`);
      return {};
    }
  }

  /**
   * Check if filename matches pattern
   *
   * Supports:
   * - Exact match (agent.md)
   * - Wildcard (*.md)
   * - Glob-like patterns (*-agent.md)
   */
  private matchesPattern(filename: string, pattern: string): boolean {
    // Exact match
    if (pattern === filename) {
      return true;
    }

    // Wildcard pattern
    if (pattern.includes('*')) {
      const regex = new RegExp(
        '^' + pattern.replace(/\*/g, '.*').replace(/\./g, '\\.') + '$'
      );
      return regex.test(filename);
    }

    return false;
  }

  /**
   * Log helper (respects verbose config)
   */
  private log(message: string): void {
    if (this.config.verbose) {
      console.log(`[AgentDiscovery] ${message}`);
    }
  }
}
