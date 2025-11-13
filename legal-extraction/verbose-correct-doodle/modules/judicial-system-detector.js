/**
 * JUDICIAL SYSTEM DETECTOR v1.0
 *
 * Detecta automaticamente qual sistema de processo judicial eletrônico brasileiro
 * gerou o PDF, baseado em padrões textuais específicos de cada sistema.
 *
 * Sistemas suportados:
 * - PJE (Processo Judicial Eletrônico - CNJ)
 * - ESAJ (Sistema de Automação da Justiça - Softplan)
 * - EPROC (Sistema de Processo Eletrônico - TRF4)
 * - PROJUDI (Processo Judicial Digital)
 * - STF (Sistema e-STF - Supremo Tribunal Federal)
 * - STJ (Sistema e-STJ - Superior Tribunal de Justiça)
 *
 * Baseado em: Pesquisa "Sistemas de processo judicial eletrônico no Brasil:
 * desafios técnicos de extração" (2025)
 */

class JudicialSystemDetector {
  constructor() {
    // Padrões de detecção por sistema (ordenados por especificidade)
    this.patterns = {
      STF: {
        name: 'STF (Supremo Tribunal Federal)',
        code: 'STF',
        priority: 1, // Alta prioridade (padrões muito específicos)
        signatures: [
          /supremo\s+tribunal\s+federal/i,
          /e-stf/i,
          /portal\.stf\.jus\.br/i,
          /peticionamento\s+eletr[oô]nico\s+stf/i,
          /resolu[cç][aã]o\s+stf\s+693/i,
          /pkcs\s*[#]?\s*7/i, // Assinatura PKCS7 específica do STF
          /projeto\s+victor/i
        ],
        minMatches: 2,
        description: 'PDF gerado pelo sistema e-STF com assinatura PKCS7 e marca d\'água com CPF'
      },

      STJ: {
        name: 'STJ (Superior Tribunal de Justiça)',
        code: 'STJ',
        priority: 1,
        signatures: [
          /superior\s+tribunal\s+de\s+justi[cç]a/i,
          /e-stj/i,
          /www\.stj\.jus\.br/i,
          /central\s+do\s+processo\s+eletr[oô]nico/i,
          /resolu[cç][aã]o\s+stj\/gp\s+10/i,
          /autentique\s+em:\s*https?:\/\/www\.stj\.jus\.br\/validar/i
        ],
        minMatches: 2,
        description: 'PDF gerado pelo sistema e-STJ com múltiplos elementos de validação'
      },

      PJE: {
        name: 'PJE (Processo Judicial Eletrônico)',
        code: 'PJE',
        priority: 2,
        signatures: [
          /processo\s+judicial\s+eletr[oô]nico/i,
          /\bpje\b/i,
          /resolu[cç][aã]o\s+cnj\s+281/i,
          /documento\s+assinado\s+por.*e\s+certificado\s+digitalmente\s+por/i,
          /c[oó]digo\s+de\s+verifica[cç][aã]o:\s*[A-Z0-9]{4}\.[0-9]{4}\.[0-9]X{2}[0-9]\.[X0-9]{4}/i,
          /este\s+documento\s+foi\s+gerado\s+pelo\s+usu[aá]rio\s+\d{3}\.\d{3}\.\d{3}-\d{2}/i,
          /trt\d+\.jus\.br\/pje/i,
          /trf\d+\.jus\.br\/pje/i
        ],
        minMatches: 2,
        description: 'PDF gerado pelo PJE com códigos alfanuméricos e timestamps repetitivos'
      },

      ESAJ: {
        name: 'ESAJ (Sistema de Automação da Justiça)',
        code: 'ESAJ',
        priority: 2,
        signatures: [
          /e-saj/i,
          /\besaj\b/i,
          /softplan/i,
          /portal\s+e-saj/i,
          /confer[eê]ncia\s+de\s+documento\s+digital/i,
          /tjsp\.jus\.br.*esaj/i,
          /tjce\.jus\.br.*esaj/i,
          /tjam\.jus\.br.*esaj/i,
          /tjms\.jus\.br.*esaj/i,
          /resolu[cç][aã]o\s+.*552\/11/i // Resolução do brasão TJSP
        ],
        minMatches: 2,
        description: 'PDF gerado pelo ESAJ com selo lateral vertical e QR codes'
      },

      EPROC: {
        name: 'EPROC (Sistema de Processo Eletrônico)',
        code: 'EPROC',
        priority: 2,
        signatures: [
          /\beproc\b/i,
          /sistema\s+de\s+processo\s+eletr[oô]nico/i,
          /trf4\.jus\.br.*eproc/i,
          /trf2\.jus\.br.*eproc/i,
          /trf6\.jus\.br.*eproc/i,
          /tjrs\.jus\.br.*eproc/i,
          /tjsc\.jus\.br.*eproc/i,
          /\.p7s/i, // Referência a arquivo de assinatura destacada
          /cades/i, // Padrão CAdES específico
          /assinatura\s+destacada/i
        ],
        minMatches: 2,
        description: 'PDF gerado pelo EPROC com assinatura destacada (arquivo .p7s separado)'
      },

      PROJUDI: {
        name: 'PROJUDI (Processo Judicial Digital)',
        code: 'PROJUDI',
        priority: 3, // Menor prioridade (padrões menos específicos devido a variações regionais)
        signatures: [
          /projudi/i,
          /processo\s+judicial\s+digital/i,
          /tjba\.jus\.br.*projudi/i,
          /tjce\.jus\.br.*projudi/i,
          /tjpr\.jus\.br.*projudi/i,
          /tjmg\.jus\.br.*projudi/i,
          /vers[aã]o\s+1\.\d+/i, // Versões variadas (1.08, 1.9, 1.14, 2.x, 4.14.2)
          /assinador\s+livre/i,
          /universidade\s+federal\s+de\s+campina\s+grande/i // Origem do PROJUDI
        ],
        minMatches: 2,
        description: 'PDF gerado pelo PROJUDI com variações regionais significativas'
      }
    };

    // Padrões gerais de assinatura ICP-Brasil (não identificam sistema específico)
    this.icpBrasilPatterns = [
      /icp-brasil/i,
      /certificado\s+digital/i,
      /assinado\s+digitalmente/i,
      /pades|cades|xades/i,
      /ac\s+[a-z]+/i, // Autoridade Certificadora
      /iti\s+-\s+instituto\s+nacional\s+de\s+tecnologia\s+da\s+informa[cç][aã]o/i
    ];
  }

  /**
   * Detecta qual sistema judicial gerou o PDF
   * @param {string} text - Texto extraído do PDF
   * @param {object} metadata - Metadados do PDF (opcional)
   * @returns {object} - {system: 'PJE'|'ESAJ'|..., confidence: 0-100, details: {...}}
   */
  detectSystem(text, metadata = {}) {
    if (!text || text.length < 100) {
      return {
        system: 'UNKNOWN',
        confidence: 0,
        details: { reason: 'Texto muito curto para análise' }
      };
    }

    const results = [];

    // Testa cada sistema
    for (const [systemCode, config] of Object.entries(this.patterns)) {
      const matches = this._countMatches(text, config.signatures);
      const matchRatio = matches / config.signatures.length;

      // Calcula confiança baseada em matches e prioridade
      let confidence = 0;
      if (matches >= config.minMatches) {
        // Base: 40-100% dependendo do ratio de matches
        confidence = 40 + (matchRatio * 60);

        // Bônus por prioridade (sistemas mais específicos têm bônus)
        if (config.priority === 1) {
          confidence = Math.min(100, confidence + 10);
        }

        // Bônus por matches acima do mínimo
        if (matches > config.minMatches) {
          confidence = Math.min(100, confidence + ((matches - config.minMatches) * 5));
        }
      }

      results.push({
        system: systemCode,
        name: config.name,
        confidence: Math.round(confidence),
        matches: matches,
        totalPatterns: config.signatures.length,
        description: config.description
      });
    }

    // Ordena por confiança
    results.sort((a, b) => b.confidence - a.confidence);

    const topResult = results[0];

    // Se nenhum sistema específico foi detectado com confiança razoável
    if (topResult.confidence < 40) {
      // Verifica se tem padrões ICP-Brasil gerais
      const icpMatches = this._countMatches(text, this.icpBrasilPatterns);
      if (icpMatches >= 2) {
        return {
          system: 'GENERIC_JUDICIAL',
          name: 'Sistema Judicial Genérico (ICP-Brasil)',
          confidence: 50,
          details: {
            reason: 'Detectado certificação ICP-Brasil mas sistema específico não identificado',
            icpMatches: icpMatches,
            allResults: results
          }
        };
      }

      return {
        system: 'UNKNOWN',
        name: 'Sistema Desconhecido',
        confidence: 0,
        details: {
          reason: 'Nenhum padrão de sistema judicial brasileiro detectado',
          allResults: results
        }
      };
    }

    return {
      system: topResult.system,
      name: topResult.name,
      confidence: topResult.confidence,
      details: {
        matches: topResult.matches,
        totalPatterns: topResult.totalPatterns,
        description: topResult.description,
        allResults: results.slice(0, 3) // Top 3 resultados para debugging
      }
    };
  }

  /**
   * Conta quantos padrões regex fazem match no texto
   * @private
   */
  _countMatches(text, patterns) {
    let count = 0;
    for (const pattern of patterns) {
      if (pattern.test(text)) {
        count++;
      }
    }
    return count;
  }

  /**
   * Retorna informações detalhadas sobre um sistema específico
   * @param {string} systemCode - Código do sistema (PJE, ESAJ, etc)
   * @returns {object|null}
   */
  getSystemInfo(systemCode) {
    return this.patterns[systemCode] || null;
  }

  /**
   * Lista todos os sistemas suportados
   * @returns {array}
   */
  listSupportedSystems() {
    return Object.entries(this.patterns).map(([code, config]) => ({
      code: code,
      name: config.name,
      description: config.description
    }));
  }
}

// Export para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
  module.exports = JudicialSystemDetector;
}

// Disponibiliza globalmente no browser
if (typeof window !== 'undefined') {
  window.JudicialSystemDetector = JudicialSystemDetector;
  console.log('✓ JudicialSystemDetector v1.0 carregado');
}
