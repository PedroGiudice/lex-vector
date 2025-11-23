/**
 * Mock Agent Fixtures
 *
 * Sample agent definitions for testing agent discovery
 */

/**
 * YAML frontmatter format
 */
export const AGENT_YAML_FRONTMATTER = `---
name: desenvolvimento
type: permanent
description: Backend development specialist
capabilities:
  - TypeScript
  - Node.js
  - Express
  - Database design
triggers:
  - backend development
  - API implementation
  - database design
---

# Desenvolvimento Agent

Specialized in backend development with Node.js and TypeScript.

## Capabilities
- REST API design
- Database modeling
- Performance optimization
`;

/**
 * Markdown header format
 */
export const AGENT_MARKDOWN_HEADERS = `# Agent: qualidade-codigo

**Type:** Virtual
**Description:** Code quality assurance specialist

## Capabilities
- Code review
- Test coverage analysis
- Performance profiling
- Security audits

## Triggers
- code review
- quality check
- test coverage
`;

/**
 * Custom marker format
 */
export const AGENT_CUSTOM_MARKERS = `[AGENT: documentacao]
[TYPE: virtual]
[DESCRIPTION: Documentation specialist]

## Overview
This agent creates comprehensive documentation.

[CAPABILITIES]
- API documentation
- Architecture diagrams
- User guides

[TRIGGERS]
- write docs
- document API
- create diagrams
`;

/**
 * Invalid agent (missing required fields)
 */
export const AGENT_INVALID = `---
name: broken-agent
# Missing type and description
---

This agent is incomplete.
`;

/**
 * Minimal valid agent
 */
export const AGENT_MINIMAL = `---
name: minimal
type: virtual
description: Minimal agent definition
---
`;

/**
 * Agent with complex metadata
 */
export const AGENT_COMPLEX = `---
name: orchestrator
type: permanent
description: Multi-agent orchestration coordinator
author: PedroGiudice
version: 2.0.0
capabilities:
  - Agent spawning
  - Task delegation
  - Workflow coordination
  - Result aggregation
dependencies:
  - desenvolvimento
  - qualidade-codigo
  - documentacao
triggers:
  - orchestrate
  - multi-agent workflow
  - coordinate agents
settings:
  maxConcurrentAgents: 5
  timeout: 300000
  retryAttempts: 3
---

# Orchestrator Agent

Coordinates complex multi-agent workflows.

## Advanced Features
- Dynamic agent spawning
- Intelligent task routing
- Real-time monitoring
`;

/**
 * Mock file system structure
 */
export const MOCK_AGENTS_DIR = {
  'desenvolvimento.md': AGENT_YAML_FRONTMATTER,
  'qualidade-codigo.md': AGENT_MARKDOWN_HEADERS,
  'documentacao.md': AGENT_CUSTOM_MARKERS,
  'orchestrator.md': AGENT_COMPLEX,
  'minimal.md': AGENT_MINIMAL,
  'broken.md': AGENT_INVALID,
  'README.md': '# Agents Directory', // Should be skipped
  '.git': {}, // Should be skipped
};

/**
 * Expected parsed results
 */
export const EXPECTED_AGENTS = [
  {
    name: 'desenvolvimento',
    type: 'permanent',
    description: 'Backend development specialist',
    capabilities: ['TypeScript', 'Node.js', 'Express', 'Database design'],
  },
  {
    name: 'qualidade-codigo',
    type: 'virtual',
    description: 'Code quality assurance specialist',
    capabilities: [
      'Code review',
      'Test coverage analysis',
      'Performance profiling',
      'Security audits',
    ],
  },
  {
    name: 'documentacao',
    type: 'virtual',
    description: 'Documentation specialist',
    capabilities: ['API documentation', 'Architecture diagrams', 'User guides'],
  },
  {
    name: 'orchestrator',
    type: 'permanent',
    description: 'Multi-agent orchestration coordinator',
    capabilities: [
      'Agent spawning',
      'Task delegation',
      'Workflow coordination',
      'Result aggregation',
    ],
  },
  {
    name: 'minimal',
    type: 'virtual',
    description: 'Minimal agent definition',
    capabilities: [],
  },
];
