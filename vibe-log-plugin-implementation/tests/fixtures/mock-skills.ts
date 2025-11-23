/**
 * Mock Skill Fixtures
 *
 * Sample skill definitions in various formats
 */

/**
 * SKILL.md format (standard)
 */
export const SKILL_MD_FORMAT = `---
name: ocr-pro
description: Advanced OCR for documents
author: PedroGiudice
version: 1.0.0
triggers:
  - OCR
  - extract text
  - read PDF
  - scan document
keywords:
  - optical character recognition
  - document processing
  - text extraction
---

# OCR Pro Skill

Advanced optical character recognition for documents.

## Usage
Automatically triggered when user mentions OCR or document scanning.

## Capabilities
- PDF text extraction
- Image OCR
- Multi-language support
`;

/**
 * skill.yaml format
 */
export const SKILL_YAML_FORMAT = `name: deep-parser
description: Deep parsing of complex structures
author: PedroGiudice
version: 1.2.0
triggers:
  - parse JSON
  - parse XML
  - parse YAML
  - analyze structure
keywords:
  - parsing
  - data structures
  - syntax analysis
capabilities:
  - JSON parsing with schema validation
  - XML/HTML parsing
  - YAML parsing
  - Custom DSL parsing
`;

/**
 * skill.json format
 */
export const SKILL_JSON_FORMAT = {
  name: 'frontend-design',
  description: 'Frontend design system skill',
  author: 'PedroGiudice',
  version: '2.0.0',
  triggers: [
    'design system',
    'UI components',
    'React components',
    'frontend design',
  ],
  keywords: ['React', 'TypeScript', 'MUI', 'design system'],
  capabilities: [
    'React component creation',
    'MUI v7 theming',
    'Responsive design',
    'Accessibility',
  ],
};

/**
 * Invalid skill (missing required fields)
 */
export const SKILL_INVALID = `---
name: broken-skill
# Missing description and triggers
---
`;

/**
 * Minimal valid skill
 */
export const SKILL_MINIMAL = `---
name: minimal-skill
description: Minimal skill definition
triggers:
  - minimal
---
`;

/**
 * Mock file system structure for skills
 */
export const MOCK_SKILLS_DIR = {
  'ocr-pro': {
    'SKILL.md': SKILL_MD_FORMAT,
  },
  'deep-parser': {
    'skill.yaml': SKILL_YAML_FORMAT,
  },
  'frontend-design': {
    'skill.json': JSON.stringify(SKILL_JSON_FORMAT, null, 2),
  },
  'minimal-skill': {
    'SKILL.md': SKILL_MINIMAL,
  },
  'broken-skill': {
    'SKILL.md': SKILL_INVALID,
  },
  'no-skill-file': {
    'README.md': 'This directory has no skill file',
  },
};

/**
 * Expected parsed skills
 */
export const EXPECTED_SKILLS = [
  {
    name: 'ocr-pro',
    description: 'Advanced OCR for documents',
    triggers: ['OCR', 'extract text', 'read PDF', 'scan document'],
  },
  {
    name: 'deep-parser',
    description: 'Deep parsing of complex structures',
    triggers: ['parse JSON', 'parse XML', 'parse YAML', 'analyze structure'],
  },
  {
    name: 'frontend-design',
    description: 'Frontend design system skill',
    triggers: [
      'design system',
      'UI components',
      'React components',
      'frontend design',
    ],
  },
  {
    name: 'minimal-skill',
    description: 'Minimal skill definition',
    triggers: ['minimal'],
  },
];

/**
 * Sample user prompts for skill detection
 */
export const SKILL_DETECTION_PROMPTS = [
  {
    prompt: 'Can you extract text from this PDF using OCR?',
    expectedSkill: 'ocr-pro',
  },
  {
    prompt: 'I need help parsing this complex JSON structure.',
    expectedSkill: 'deep-parser',
  },
  {
    prompt: 'Create a React component following our design system.',
    expectedSkill: 'frontend-design',
  },
  {
    prompt: 'Run the tests and fix any failures.',
    expectedSkill: null, // No skill match
  },
];

/**
 * Mock skill usage statistics
 */
export const MOCK_SKILL_STATS = {
  'ocr-pro': {
    totalInvocations: 25,
    successRate: 0.96,
    avgDuration: 3500,
    lastUsed: Date.now() - 7200000, // 2 hours ago
  },
  'deep-parser': {
    totalInvocations: 42,
    successRate: 0.98,
    avgDuration: 150,
    lastUsed: Date.now() - 1800000, // 30 minutes ago
  },
  'frontend-design': {
    totalInvocations: 18,
    successRate: 1.0,
    avgDuration: 2200,
    lastUsed: Date.now() - 600000, // 10 minutes ago
  },
};
