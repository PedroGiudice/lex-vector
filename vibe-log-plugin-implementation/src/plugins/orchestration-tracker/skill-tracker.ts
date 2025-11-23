/**
 * Skill Tracker - Skill Discovery and Usage Tracking
 *
 * Tracks Claude Code skill usage and effectiveness
 */

import { readdir, readFile, stat } from 'fs/promises';
import { join, basename } from 'path';
import type {
  OrchestrationConfig,
  SkillDefinition,
  SkillInvocation,
} from './types.js';

/**
 * Skill usage record (internal)
 */
interface SkillUsage {
  invocations: SkillInvocation[];
  usageCount: number;
}

/**
 * Skill Tracker Service
 */
export class SkillTracker {
  private usage: Map<string, SkillUsage> = new Map();
  private skills: SkillDefinition[] = [];

  constructor(private config: OrchestrationConfig) {}

  /**
   * Discover skills in project directory
   *
   * @param projectDir - Project root directory
   * @returns Array of skill definitions
   */
  async discoverSkills(projectDir: string): Promise<SkillDefinition[]> {
    const skillsDir = join(projectDir, this.config.skillsDir);

    try {
      await stat(skillsDir);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        this.log(`Skills directory not found: ${skillsDir}`);
        return [];
      }
      throw error;
    }

    const skills: SkillDefinition[] = [];
    const errors: string[] = [];

    try {
      // Read skill directories
      const entries = await readdir(skillsDir, { withFileTypes: true });

      const processPromises = entries.map(async (entry) => {
        if (!entry.isDirectory() || entry.name.startsWith('.')) {
          return null;
        }

        const skillDir = join(skillsDir, entry.name);

        try {
          return await this.parseSkillDirectory(skillDir, entry.name);
        } catch (error) {
          errors.push(`${entry.name}: ${(error as Error).message}`);
          return null;
        }
      });

      const results = await Promise.all(processPromises);
      skills.push(...results.filter((s): s is SkillDefinition => s !== null));

      if (errors.length > 0 && this.config.verbose) {
        console.warn(`⚠️  ${errors.length} skill(s) failed to parse:`);
        errors.forEach((err) => console.warn(`   - ${err}`));
      }

      this.skills = skills;
      this.log(`Discovered ${skills.length} skill(s) from ${skillsDir}`);

      return skills;
    } catch (error) {
      throw new Error(
        `Failed to discover skills in "${skillsDir}": ${(error as Error).message}`
      );
    }
  }

  /**
   * Parse skill directory for metadata
   *
   * @param skillDir - Path to skill directory
   * @param skillName - Skill name (directory name)
   * @returns Skill definition
   */
  private async parseSkillDirectory(
    skillDir: string,
    skillName: string
  ): Promise<SkillDefinition> {
    // Try each supported format
    for (const format of this.config.skillFormats) {
      const filePath = join(skillDir, format);

      try {
        await stat(filePath);
        const content = await readFile(filePath, 'utf-8');

        // Parse based on format
        const metadata = this.parseSkillContent(content, format);

        return {
          name: metadata.name || skillName,
          path: skillDir,
          triggers: metadata.triggers || [],
          description: metadata.description || 'No description',
          metadata,
        };
      } catch (error) {
        // File doesn't exist, try next format
        if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
          continue;
        }
        throw error;
      }
    }

    // No valid skill file found
    throw new Error(
      `No skill file found (tried: ${this.config.skillFormats.join(', ')})`
    );
  }

  /**
   * Parse skill file content
   *
   * @param content - File content
   * @param format - File format (SKILL.md, skill.yaml, skill.json)
   * @returns Parsed metadata
   */
  private parseSkillContent(
    content: string,
    format: string
  ): Record<string, unknown> {
    if (format.endsWith('.md')) {
      return this.parseMarkdownSkill(content);
    } else if (format.endsWith('.yaml') || format.endsWith('.yml')) {
      return this.parseYAMLSkill(content);
    } else if (format.endsWith('.json')) {
      return this.parseJSONSkill(content);
    }

    return {};
  }

  /**
   * Parse Markdown skill file
   */
  private parseMarkdownSkill(content: string): Record<string, unknown> {
    const metadata: Record<string, unknown> = {};

    // Extract YAML frontmatter
    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (frontmatterMatch) {
      const yaml = this.parseSimpleYAML(frontmatterMatch[1]);
      Object.assign(metadata, yaml);
    }

    // Extract name from H1
    const h1Match = content.match(/^#\s+(.+)$/m);
    if (h1Match && !metadata.name) {
      metadata.name = h1Match[1].trim();
    }

    // Extract description (first paragraph)
    const descMatch = content.match(/^#\s+.+\n\n(.+?)(?:\n\n|$)/m);
    if (descMatch && !metadata.description) {
      metadata.description = descMatch[1].trim();
    }

    // Extract triggers (keywords, patterns)
    if (!metadata.triggers) {
      const triggers: string[] = [];

      // Look for triggers section
      const triggersMatch = content.match(
        /##\s+Triggers?[\s\S]*?(?:^-\s+(.+)$)+/gim
      );
      if (triggersMatch) {
        const listMatches = triggersMatch[0].matchAll(/^-\s+(.+)$/gm);
        for (const match of listMatches) {
          triggers.push(match[1].trim());
        }
      }

      // Look for keywords section
      const keywordsMatch = content.match(
        /##\s+Keywords?[\s\S]*?(?:^-\s+(.+)$)+/gim
      );
      if (keywordsMatch) {
        const listMatches = keywordsMatch[0].matchAll(/^-\s+(.+)$/gm);
        for (const match of listMatches) {
          triggers.push(match[1].trim());
        }
      }

      if (triggers.length > 0) {
        metadata.triggers = triggers;
      }
    }

    return metadata;
  }

  /**
   * Parse YAML skill file
   */
  private parseYAMLSkill(content: string): Record<string, unknown> {
    return this.parseSimpleYAML(content);
  }

  /**
   * Parse JSON skill file
   */
  private parseJSONSkill(content: string): Record<string, unknown> {
    try {
      return JSON.parse(content) as Record<string, unknown>;
    } catch (error) {
      this.log(`JSON parse error: ${(error as Error).message}`);
      return {};
    }
  }

  /**
   * Simple YAML parser (handles basic key: value pairs and lists)
   */
  private parseSimpleYAML(content: string): Record<string, unknown> {
    const result: Record<string, unknown> = {};
    const lines = content.split('\n');

    let currentKey: string | null = null;
    const currentArray: string[] = [];

    for (const line of lines) {
      // Array items
      if (line.match(/^\s*-\s+(.+)$/)) {
        const match = line.match(/^\s*-\s+(.+)$/);
        if (match && currentKey) {
          currentArray.push(match[1].trim().replace(/^["']|["']$/g, ''));
        }
        continue;
      }

      // Save previous array
      if (currentKey && currentArray.length > 0) {
        result[currentKey] = [...currentArray];
        currentArray.length = 0;
        currentKey = null;
      }

      // Key-value pairs
      const kvMatch = line.match(/^(\w+):\s*(.*)$/);
      if (kvMatch) {
        const key = kvMatch[1];
        const value = kvMatch[2].trim();

        if (!value) {
          // Array start
          currentKey = key;
        } else if (value.startsWith('[') && value.endsWith(']')) {
          // Inline array
          result[key] = value
            .slice(1, -1)
            .split(',')
            .map((v) => v.trim().replace(/^["']|["']$/g, ''));
        } else {
          // Simple value
          result[key] = value.replace(/^["']|["']$/g, '');
        }
      }
    }

    // Save last array
    if (currentKey && currentArray.length > 0) {
      result[currentKey] = currentArray;
    }

    return result;
  }

  /**
   * Detect skill invocation in prompt
   *
   * @param prompt - User prompt text
   * @returns Skill invocation record (or null if no match)
   */
  detectSkillInvocation(prompt: string): SkillInvocation | null {
    const lowerPrompt = prompt.toLowerCase();

    // Check each skill's triggers
    for (const skill of this.skills) {
      for (const trigger of skill.triggers) {
        const lowerTrigger = trigger.toLowerCase();

        // Exact match or word boundary match
        if (
          lowerPrompt.includes(lowerTrigger) ||
          new RegExp(`\\b${this.escapeRegex(lowerTrigger)}\\b`).test(
            lowerPrompt
          )
        ) {
          return {
            skill: skill.name,
            timestamp: Date.now(),
            context: prompt.slice(0, 200), // First 200 chars
          };
        }
      }
    }

    return null;
  }

  /**
   * Track skill usage
   *
   * @param skillName - Skill name
   * @param context - Context (prompt)
   * @param outcome - Success or failure
   */
  trackUsage(
    skillName: string,
    context: string,
    outcome: 'success' | 'failure' = 'success'
  ): void {
    const invocation: SkillInvocation = {
      skill: skillName,
      timestamp: Date.now(),
      context: context.slice(0, 200),
      outcome,
    };

    const existing = this.usage.get(skillName) || {
      invocations: [],
      usageCount: 0,
    };

    existing.invocations.push(invocation);
    existing.usageCount++;

    // Keep only last 50 invocations
    if (existing.invocations.length > 50) {
      existing.invocations.shift();
    }

    this.usage.set(skillName, existing);

    this.log(`Tracked usage for skill "${skillName}" (${outcome})`);
  }

  /**
   * Get usage statistics for a skill
   *
   * @param skillName - Skill name
   * @returns Usage data
   */
  getUsage(skillName: string): SkillUsage {
    return (
      this.usage.get(skillName) || {
        invocations: [],
        usageCount: 0,
      }
    );
  }

  /**
   * Get all skills with usage data
   *
   * @returns Map of skill name to usage
   */
  getAllUsage(): Map<string, SkillUsage> {
    return new Map(this.usage);
  }

  /**
   * Export usage data (for storage)
   */
  exportData(): Record<string, SkillUsage> {
    return Object.fromEntries(this.usage);
  }

  /**
   * Import usage data (from storage)
   */
  importData(data: Record<string, SkillUsage>): void {
    this.usage = new Map(Object.entries(data));
    this.log(`Imported data for ${this.usage.size} skill(s)`);
  }

  /**
   * Escape regex special characters
   */
  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  /**
   * Log helper (respects verbose config)
   */
  private log(message: string): void {
    if (this.config.verbose) {
      console.log(`[SkillTracker] ${message}`);
    }
  }
}
