import type {
  QueryTemplate,
  JurisprudenceResult,
  LegalDomain,
  TriggerWord,
} from '@/types';

export const LEGAL_DOMAINS: LegalDomain[] = [
  'Direito Civil',
  'Direito Penal',
  'Tributário',
  'Administrativo',
];

export const TRIGGER_WORDS: TriggerWord[] = [
  'Dano Moral',
  'Lucros Cessantes',
  'Habeas Corpus',
  'ICMS',
  'Responsabilidade Civil',
  'Prescrição',
  'Decadência',
  'Inexigibilidade',
];

export const QUERY_TEMPLATES: QueryTemplate[] = [
  {
    id: 'divergencia-turmas',
    name: 'Divergência entre Turmas',
    description: 'Identifica divergências jurisprudenciais entre diferentes turmas',
    onlyAcordaos: true,
  },
  {
    id: 'recursos-repetitivos',
    name: 'Recursos Repetitivos',
    description: 'Busca por recursos sob rito de repetitivos (Art. 1.036 CPC)',
    onlyAcordaos: true,
  },
  {
    id: 'sumulas-recentes',
    name: 'Súmulas Recentes',
    description: 'Jurisprudência relacionada a súmulas dos últimos 24 meses',
    onlyAcordaos: false,
  },
];

export const MOCK_RESULTS: JurisprudenceResult[] = [
  {
    id: '1',
    processoNumero: 'REsp 1.234.567/SP',
    relator: 'Min. Nancy Andrighi',
    dataJulgamento: '2024-11-15',
    ementa:
      'RECURSO ESPECIAL. RESPONSABILIDADE CIVIL. DANO MORAL. CONFIGURAÇÃO. Caracterizado dano moral decorrente de ofensa à honra objetiva da vítima. Quantum indenizatório mantido. RECURSO PROVIDO.',
    outcome: 'provido',
    orgaoJulgador: '3ª Turma',
  },
  {
    id: '2',
    processoNumero: 'REsp 1.345.678/RJ',
    relator: 'Min. Marco Buzzi',
    dataJulgamento: '2024-10-22',
    ementa:
      'TRIBUTÁRIO. ICMS. BASE DE CÁLCULO. INCLUSÃO DE VALORES. Impossibilidade de inclusão de encargos na base de cálculo do ICMS. Precedentes. RECURSO DESPROVIDO.',
    outcome: 'desprovido',
    orgaoJulgador: '2ª Turma',
  },
  {
    id: '3',
    processoNumero: 'REsp 1.456.789/MG',
    relator: 'Min. Ricardo Villas Bôas Cueva',
    dataJulgamento: '2024-09-18',
    ementa:
      'CIVIL. LUCROS CESSANTES. COMPROVAÇÃO. NEXO CAUSAL. Necessária a demonstração efetiva do prejuízo e do nexo de causalidade. Prova insuficiente nos autos. RECURSO PARCIALMENTE PROVIDO.',
    outcome: 'parcial',
    orgaoJulgador: '3ª Turma',
  },
  {
    id: '4',
    processoNumero: 'HC 987.654/BA',
    relator: 'Min. Sebastião Reis Júnior',
    dataJulgamento: '2024-08-30',
    ementa:
      'HABEAS CORPUS. PRISÃO PREVENTIVA. FUNDAMENTAÇÃO INSUFICIENTE. Ausência de motivação concreta para manutenção da custódia cautelar. ORDEM CONCEDIDA.',
    outcome: 'provido',
    orgaoJulgador: '6ª Turma',
  },
  {
    id: '5',
    processoNumero: 'REsp 1.567.890/RS',
    relator: 'Min. Maria Isabel Gallotti',
    dataJulgamento: '2024-07-12',
    ementa:
      'RESPONSABILIDADE CIVIL. PRESCRIÇÃO. TERMO INICIAL. Contagem do prazo prescricional a partir da ciência inequívoca do dano. Prescrição não configurada. RECURSO DESPROVIDO.',
    outcome: 'desprovido',
    orgaoJulgador: '4ª Turma',
  },
];

/**
 * Generates SQL preview based on query parameters
 */
export function generateSQLPreview(
  domain: LegalDomain | null,
  triggerWords: TriggerWord[],
  onlyAcordaos: boolean
): string {
  const clauses: string[] = ['SELECT *', 'FROM stj_jurisprudencia'];
  const whereClauses: string[] = [];

  if (domain) {
    whereClauses.push(`  domain = '${domain}'`);
  }

  if (triggerWords.length > 0) {
    const wordList = triggerWords.map((w) => `'${w}'`).join(', ');
    whereClauses.push(`  ementa ILIKE ANY(ARRAY[${wordList}])`);
  }

  if (onlyAcordaos) {
    whereClauses.push(`  tipo_documento = 'ACORDAO'`);
  }

  if (whereClauses.length > 0) {
    clauses.push('WHERE');
    clauses.push(whereClauses.join('\n  AND\n'));
  }

  clauses.push('ORDER BY data_julgamento DESC');
  clauses.push('LIMIT 100;');

  return clauses.join('\n');
}

/**
 * Estimates result count based on filters
 */
export function estimateResultCount(
  domain: LegalDomain | null,
  triggerWords: TriggerWord[],
  onlyAcordaos: boolean
): number {
  let baseCount = 15000;

  if (domain) baseCount *= 0.4;
  if (triggerWords.length > 0) {
    baseCount *= 0.3 * Math.max(0.5, 1 / triggerWords.length);
  }
  if (onlyAcordaos) baseCount *= 0.6;

  return Math.floor(baseCount);
}
