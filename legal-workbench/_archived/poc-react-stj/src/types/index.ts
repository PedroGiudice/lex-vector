export type LegalDomain =
  | 'Direito Civil'
  | 'Direito Penal'
  | 'Tributário'
  | 'Administrativo';

export type TriggerWord =
  | 'Dano Moral'
  | 'Lucros Cessantes'
  | 'Habeas Corpus'
  | 'ICMS'
  | 'Responsabilidade Civil'
  | 'Prescrição'
  | 'Decadência'
  | 'Inexigibilidade';

export type Outcome = 'provido' | 'desprovido' | 'parcial';

export interface QueryTemplate {
  id: string;
  name: string;
  domain?: LegalDomain;
  triggerWords?: TriggerWord[];
  onlyAcordaos: boolean;
  description: string;
}

export interface QueryParams {
  domain: LegalDomain | null;
  triggerWords: TriggerWord[];
  onlyAcordaos: boolean;
}

export interface JurisprudenceResult {
  id: string;
  processoNumero: string;
  relator: string;
  dataJulgamento: string;
  ementa: string;
  outcome: Outcome;
  orgaoJulgador: string;
}

export interface SQLPreview {
  query: string;
  estimatedResults: number;
}
