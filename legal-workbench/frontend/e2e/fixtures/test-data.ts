/**
 * E2E Test Fixtures and Data
 *
 * This file contains test data and fixtures for E2E tests.
 * Use these constants to keep tests consistent and maintainable.
 */

export const MODULES = {
  TRELLO: {
    id: 'trello',
    name: 'Trello Command Center',
    path: '/trello',
    description: 'Gerencie boards, listas e cards do Trello',
  },
  DOC_ASSEMBLER: {
    id: 'doc-assembler',
    name: 'Doc Assembler',
    path: '/doc-assembler',
    description: 'Monte documentos a partir de templates',
  },
  STJ: {
    id: 'stj',
    name: 'STJ Dados Abertos',
    path: '/stj',
    description: 'Pesquise jurisprudencia do STJ',
  },
  TEXT_EXTRACTOR: {
    id: 'text-extractor',
    name: 'Text Extractor',
    path: '/text-extractor',
    description: 'Extraia texto de PDFs com OCR',
  },
  LEDES: {
    id: 'ledes-converter',
    name: 'LEDES Converter',
    path: '/ledes-converter',
    description: 'Converta faturas DOCX para formato LEDES',
  },
  CCUI_ASSISTANT: {
    id: 'ccui-assistant',
    name: 'Claude Code',
    path: '/ccui-assistant',
    description: 'Interface do Claude Code',
  },
  CCUI_V2: {
    id: 'ccui-v2',
    name: 'CCui V2',
    path: '/ccui-v2',
    description: 'CCui versao 2',
  },
} as const

export const ALL_MODULE_PATHS = Object.values(MODULES).map((m) => m.path)

export const SELECTORS = {
  // Layout selectors
  MAIN_HEADER: 'header',
  MODULE_CARD: '[class*="group"]',

  // Text selectors
  WELCOME_HEADING: 'Bem-vindo ao Legal Workbench',
  SUBTITLE: 'Selecione um modulo abaixo para comecar',
} as const

export const TIMEOUTS = {
  SHORT: 5000,
  MEDIUM: 10000,
  LONG: 30000,
  NETWORK_IDLE: 60000,
} as const
