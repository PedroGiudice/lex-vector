/**
 * LegalDocumentAnalyzer - Identificação e classificação de peças processuais
 *
 * Analisa documentos jurídicos e identifica o tipo de peça processual:
 * - Petição Inicial
 * - Contestação
 * - Despacho
 * - Decisão Interlocutória
 * - Sentença
 * - Acórdão
 * - Parecer
 * - etc.
 *
 * @author Pré-Processador Jurídico v4.1
 * @license MIT
 */

class LegalDocumentAnalyzer {
  constructor() {
    // Padrões para identificação de cada tipo de peça
    this.patterns = {
      peticao_inicial: {
        name: 'Petição Inicial',
        order: 1,
        patterns: [
          /excelent[íi]ssimo\s+senhor\s+(?:doutor\s+)?juiz(?:\s+de\s+direito)?/gi,
          /\bpeti[çc][ãa]o\s+inicial\b/gi,
          /vem,?\s+(?:por\s+seu\s+advogado|respeitosamente),?\s+(?:à|a)\s+presen[çc]a\s+de\s+vossa\s+excel[êe]ncia/gi,
          /requer(?:er)?[:\s]+(?:.*?)(?:cita[çc][ãa]o|intima[çc][ãa]o)/gis,
          /\bdos\s+fatos\b.*?\bdo\s+direito\b.*?\bdos\s+pedidos\b/gis,
          /termos\s+em\s+que[,\s]+pede\s+deferimento/gi
        ],
        exclusions: [
          /\bcontesta[çc][ãa]o\b/gi,
          /\br[ée]plica\b/gi
        ]
      },

      contestacao: {
        name: 'Contestação',
        order: 2,
        patterns: [
          /\bcontesta[çc][ãa]o\b/gi,
          /vem,?\s+(?:respeitosamente,?\s+)?apresentar\s+(?:sua\s+)?contesta[çc][ãa]o/gi,
          /(?:r[ée]u|contestante|requerido).*?vem\s+(?:à|a)\s+presen[çc]a/gi,
          /impugna[çc][ãa]o\s+(?:aos\s+)?fatos/gi,
          /preliminar(?:es)?\s+de/gi
        ],
        exclusions: []
      },

      replica: {
        name: 'Réplica',
        order: 3,
        patterns: [
          /\br[ée]plica\b/gi,
          /vem.*?apresentar.*?r[ée]plica/gi,
          /impugnar\s+a\s+contesta[çc][ãa]o/gi
        ],
        exclusions: []
      },

      despacho: {
        name: 'Despacho',
        order: 10,
        patterns: [
          /^despacho\b/gim,
          /\bdespacho\s*:\s*$/gim,
          /(?:intime[mn]-se|cite[mn]-se|cumpra-se|arquive[mn]-se)/gi,
          /vista\s+(?:à|ao)\s+(?:autor|r[ée]u|minist[ée]rio\s+p[úu]blico)/gi,
          /^(?:fl\.|fls\.?)\s*\d+/gim
        ],
        exclusions: [
          /\bdecis[ãa]o\s+interlocut[óo]ria\b/gi,
          /\bsenten[çc]a\b/gi,
          /\bac[óo]rd[ãa]o\b/gi
        ]
      },

      decisao_interlocutoria: {
        name: 'Decisão Interlocutória',
        order: 11,
        patterns: [
          /\bdecis[ãa]o\s+interlocut[óo]ria\b/gi,
          /(?:defiro|indefiro).*?(?:tutela|liminar|medida)/gi,
          /\btutela\s+(?:antecipada|provis[óo]ria|de\s+urg[êe]ncia)\b/gi,
          /\bliminar\b.*?\b(?:concedida|deferida|indeferida)\b/gi,
          /decido\s*:/gi
        ],
        exclusions: [
          /\bsenten[çc]a\b/gi,
          /\bjulgo\s+(?:procedente|improcedente)\b/gi
        ]
      },

      sentenca: {
        name: 'Sentença',
        order: 20,
        patterns: [
          /\bsenten[çc]a\b/gi,
          /\bjulgo\s+(?:procedente|improcedente|parcialmente\s+procedente)/gi,
          /\brelatório\b.*?\bfundamenta[çc][ãa]o\b.*?\bdispositivo\b/gis,
          /pelo\s+exposto.*?julgo/gi,
          /ante\s+o\s+exposto.*?(?:julgo|decido)/gi,
          /(?:condeno|absolvo)\s+(?:o\s+)?(?:r[ée]u|autor)/gi,
          /custas\s+(?:processuais\s+)?(?:pelo\s+)?(?:autor|r[ée]u|vencido)/gi,
          /honor[áa]rios\s+advocat[íi]cios/gi
        ],
        exclusions: [
          /\bac[óo]rd[ãa]o\b/gi,
          /\b(?:tribunal|turma|c[âa]mara)\b/gi
        ]
      },

      acordao: {
        name: 'Acórdão',
        order: 30,
        patterns: [
          /\bac[óo]rd[ãa]o\b/gi,
          /\b(?:tribunal|turma|c[âa]mara)\b.*?\b(?:vistos|relatados|discutidos)\b/gis,
          /\b(?:relator|revisor)\s*:\s*(?:des\.|desembargador|ministro)/gi,
          /\bementa\b/gi,
          /(?:vistos|relatados|discutidos)\s+e\s+(?:relatados|discutidos)\s+(?:estes|os\s+presentes)\s+autos/gi,
          /acordam\s+(?:os\s+)?(?:desembargadores|ministros)/gi,
          /(?:dar|negar|dar\s+parcial)\s+provimento\s+ao\s+recurso/gi
        ],
        exclusions: []
      },

      parecer_mp: {
        name: 'Parecer do Ministério Público',
        order: 15,
        patterns: [
          /\bparecer\b.*?\bminist[ée]rio\s+p[úu]blico\b/gis,
          /\bpromotor(?:ia)?\s+de\s+justi[çc]a\b/gi,
          /\bprocurador(?:ia)?\s+(?:de\s+)?justi[çc]a\b/gi,
          /\bórgão\s+ministerial\b/gi,
          /(?:é|[ée])\s+o\s+parecer/gi,
          /opina\s+(?:pelo\s+)?(?:provimento|desprovimento|acolhimento|rejei[çc][ãa]o)/gi
        ],
        exclusions: []
      },

      agravo: {
        name: 'Agravo de Instrumento',
        order: 25,
        patterns: [
          /\bagravo\s+de\s+instrumento\b/gi,
          /\bagravo\s+interno\b/gi,
          /interpõe\s+(?:o\s+presente\s+)?agravo/gi,
          /insurge-se\s+contra\s+a\s+decis[ãa]o/gi
        ],
        exclusions: []
      },

      apelacao: {
        name: 'Apelação',
        order: 26,
        patterns: [
          /\bapela[çc][ãa]o\b(?!\s+c[íi]vel)/gi,
          /interpõe\s+(?:a\s+presente\s+)?apela[çc][ãa]o/gi,
          /inconformado\s+com\s+a\s+senten[çc]a/gi,
          /razões\s+(?:de\s+)?apela[çc][ãa]o/gi
        ],
        exclusions: []
      },

      embargos_declaracao: {
        name: 'Embargos de Declaração',
        order: 27,
        patterns: [
          /\bembargos\s+de\s+declara[çc][ãa]o\b/gi,
          /opõe\s+embargos\s+declaratórios/gi,
          /(?:omiss[ãa]o|contradi[çc][ãa]o|obscuridade)/gi
        ],
        exclusions: []
      },

      mandado: {
        name: 'Mandado',
        order: 40,
        patterns: [
          /^mandado\s+de\s+(?:cita[çc][ãa]o|intima[çc][ãa]o|pris[ãa]o|busca|penhora)/gim,
          /\boficial\s+de\s+justi[çc]a\b/gi,
          /cumprimento\s+de\s+mandado/gi
        ],
        exclusions: []
      },

      ata_audiencia: {
        name: 'Ata de Audiência',
        order: 45,
        patterns: [
          /\bata\s+de\s+audi[êe]ncia\b/gi,
          /audi[êe]ncia\s+de\s+(?:concilia[çc][ãa]o|instru[çc][ãa]o|justifica[çc][ãa]o)/gi,
          /aos?\s+\d{1,2}\s+dias?\s+do\s+m[êe]s\s+de/gi,
          /\btermo\s+de\s+audi[êe]ncia\b/gi,
          /presente(?:s)?:.*?(?:autor|r[ée]u|advogado)/gis
        ],
        exclusions: []
      }
    };
  }

  /**
   * Analisa um documento e identifica o tipo
   */
  analyzeDocument(text) {
    const scores = {};

    // Calcular score para cada tipo
    for (const [type, config] of Object.entries(this.patterns)) {
      scores[type] = this.calculateTypeScore(text, config);
    }

    // Ordenar por score
    const sorted = Object.entries(scores)
      .sort((a, b) => b[1].score - a[1].score);

    const topMatch = sorted[0];

    // Considerar apenas se score > 0
    if (topMatch && topMatch[1].score > 0) {
      return {
        type: topMatch[0],
        name: this.patterns[topMatch[0]].name,
        order: this.patterns[topMatch[0]].order,
        confidence: this.normalizeConfidence(topMatch[1].score),
        matches: topMatch[1].matches,
        allScores: Object.fromEntries(sorted.map(([k, v]) => [k, v.score]))
      };
    }

    // Documento não identificado
    return {
      type: 'unknown',
      name: 'Documento Não Identificado',
      order: 999,
      confidence: 0,
      matches: [],
      allScores: scores
    };
  }

  /**
   * Calcula score de um tipo específico
   */
  calculateTypeScore(text, config) {
    let score = 0;
    const matches = [];

    // Verificar padrões positivos
    for (const pattern of config.patterns) {
      const found = text.match(pattern);
      if (found) {
        score += found.length;
        matches.push(...found);
      }
    }

    // Penalizar por padrões de exclusão
    if (config.exclusions) {
      for (const pattern of config.exclusions) {
        const found = text.match(pattern);
        if (found) {
          score -= found.length * 2; // Penalidade maior
        }
      }
    }

    return { score: Math.max(0, score), matches };
  }

  /**
   * Normaliza score para percentual de confiança
   */
  normalizeConfidence(score) {
    // Função sigmoid adaptada
    // Score 1-2: ~50-70%
    // Score 3-5: ~70-90%
    // Score 6+: ~90-99%

    if (score === 0) return 0;
    if (score === 1) return 50;

    const normalized = 1 / (1 + Math.exp(-0.5 * (score - 3)));
    return Math.round(normalized * 100);
  }

  /**
   * Detecta início de uma peça processual no texto
   */
  detectDocumentStart(text, windowSize = 500) {
    // Analisar início do documento (primeiros N caracteres)
    const header = text.substring(0, windowSize);

    const startPatterns = [
      /^(?:excelent[íi]ssimo|il(?:ustr[íi]ssimo)?)/im,
      /^(?:poder\s+judici[áa]rio|tribunal)/im,
      /^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}/m, // Número CNJ
      /^(?:processo|autos)\s+n[úu]mero/im,
      /^despacho\s*:/im,
      /^senten[çc]a\b/im,
      /^ac[óo]rd[ãa]o\b/im
    ];

    for (let i = 0; i < startPatterns.length; i++) {
      const match = header.match(startPatterns[i]);
      if (match) {
        return {
          found: true,
          position: match.index,
          pattern: startPatterns[i].source
        };
      }
    }

    return { found: false, position: -1 };
  }

  /**
   * Detecta fim de uma peça processual
   */
  detectDocumentEnd(text, windowSize = 500) {
    // Analisar final do documento (últimos N caracteres)
    const footer = text.substring(Math.max(0, text.length - windowSize));

    const endPatterns = [
      /(?:é|[ée])\s+o\s+(?:relatório|parecer)\s*\.?\s*$/im,
      /nestes\s+termos,?\s+pede\s+deferimento\s*\.?\s*$/im,
      /(?:local|cidade).*?,?\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\s*\.?\s*$/im,
      /(?:assinado\s+)?(?:eletronicamente|digitalmente)\s*\.?\s*$/im,
      /\b(?:nada\s+mais|sendo\s+s[óo])\b.*?$/im
    ];

    for (const pattern of endPatterns) {
      const match = footer.match(pattern);
      if (match) {
        return {
          found: true,
          position: text.length - windowSize + match.index,
          pattern: pattern.source
        };
      }
    }

    return { found: false, position: text.length };
  }

  /**
   * Separa múltiplas peças em um único texto
   */
  separateDocuments(fullText) {
    const documents = [];
    let currentPos = 0;

    // Padrões que indicam início de nova peça
    const separatorPatterns = [
      /(?:^|\n\n)(?:excelent[íi]ssimo|il(?:ustr[íi]ssimo)?)\s+senhor/gim,
      /(?:^|\n\n)(?:despacho|decis[ãa]o|senten[çc]a|ac[óo]rd[ãa]o)\s*:/gim,
      /(?:^|\n\n)poder\s+judici[áa]rio/gim,
      /(?:^|\n\n)\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}/gm // Número CNJ
    ];

    // Encontrar todas as posições de separação
    const separators = [];

    for (const pattern of separatorPatterns) {
      let match;
      while ((match = pattern.exec(fullText)) !== null) {
        separators.push({
          position: match.index,
          text: match[0].trim()
        });
      }
    }

    // Ordenar por posição
    separators.sort((a, b) => a.position - b.position);

    // Remover duplicatas (mesma posição)
    const uniqueSeparators = [];
    let lastPos = -1;
    for (const sep of separators) {
      if (sep.position - lastPos > 50) { // Tolerância de 50 chars
        uniqueSeparators.push(sep);
        lastPos = sep.position;
      }
    }

    // Se não encontrou separadores, retornar texto inteiro
    if (uniqueSeparators.length === 0) {
      const analysis = this.analyzeDocument(fullText);
      return [{
        text: fullText,
        type: analysis.type,
        name: analysis.name,
        order: analysis.order,
        confidence: analysis.confidence,
        start: 0,
        end: fullText.length
      }];
    }

    // Criar documentos separados
    for (let i = 0; i < uniqueSeparators.length; i++) {
      const start = uniqueSeparators[i].position;
      const end = i < uniqueSeparators.length - 1
        ? uniqueSeparators[i + 1].position
        : fullText.length;

      const docText = fullText.substring(start, end).trim();

      if (docText.length > 100) { // Mínimo de 100 chars
        const analysis = this.analyzeDocument(docText);

        documents.push({
          text: docText,
          type: analysis.type,
          name: analysis.name,
          order: analysis.order,
          confidence: analysis.confidence,
          start,
          end
        });
      }
    }

    return documents;
  }

  /**
   * Gera relatório de análise
   */
  generateAnalysisReport(analysis) {
    const report = [];

    report.push('=== ANÁLISE DE PEÇA PROCESSUAL ===');
    report.push(`Tipo: ${analysis.name}`);
    report.push(`Confiança: ${analysis.confidence}%`);
    report.push(`Ordem cronológica sugerida: ${analysis.order}`);

    if (analysis.matches && analysis.matches.length > 0) {
      report.push('');
      report.push('--- Padrões Encontrados ---');
      const uniqueMatches = [...new Set(analysis.matches)].slice(0, 5);
      for (const match of uniqueMatches) {
        report.push(`- "${match.substring(0, 80)}..."`);
      }
    }

    return report.join('\n');
  }
}

// Exportar
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LegalDocumentAnalyzer;
}

if (typeof window !== 'undefined') {
  window.LegalDocumentAnalyzer = LegalDocumentAnalyzer;
}
