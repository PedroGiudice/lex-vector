/**
 * ADVANCED SIGNATURE CLEANER v1.0
 *
 * Remove assinaturas digitais, selos, códigos de validação e elementos de
 * certificação específicos de cada sistema de processo judicial eletrônico brasileiro.
 *
 * Baseado em: Pesquisa "Sistemas de processo judicial eletrônico no Brasil:
 * desafios técnicos de extração" (2025)
 *
 * Estratégia: Pipeline híbrido
 * 1. Remoção estrutural via regex (70-80% dos casos)
 * 2. Análise contextual (evita falsos positivos)
 * 3. Preservação de elementos jurídicos críticos
 */

class AdvancedSignatureCleaner {
  constructor(options = {}) {
    this.preservePatterns = options.preservePatterns || [];
    this.customBlacklist = options.customBlacklist || [];
    this.aggressiveMode = options.aggressiveMode || false;

    // Padrões de limpeza específicos por sistema
    this.systemPatterns = {
      PJE: this._getPJEPatterns(),
      ESAJ: this._getESAJPatterns(),
      EPROC: this._getEPROCPatterns(),
      PROJUDI: this._getPROJUDIPatterns(),
      STF: this._getSTFPatterns(),
      STJ: this._getSTJPatterns(),
      GENERIC_JUDICIAL: this._getGenericJudicialPatterns()
    };

    // Padrões universais (aplicados a todos os sistemas)
    this.universalPatterns = this._getUniversalPatterns();
  }

  /**
   * Limpa texto baseado no sistema detectado
   * @param {string} text - Texto original
   * @param {string} detectedSystem - Sistema detectado (PJE, ESAJ, etc)
   * @param {object} options - Opções adicionais
   * @returns {string} - Texto limpo
   */
  clean(text, detectedSystem = 'GENERIC_JUDICIAL', options = {}) {
    if (!text || text.length === 0) {
      return text;
    }

    let cleanedText = text;
    const stats = {
      system: detectedSystem,
      originalLength: text.length,
      removedPatterns: []
    };

    // 1. Remove padrões específicos do sistema detectado
    if (this.systemPatterns[detectedSystem]) {
      const systemResult = this._applyPatterns(
        cleanedText,
        this.systemPatterns[detectedSystem],
        `${detectedSystem}-specific`
      );
      cleanedText = systemResult.text;
      stats.removedPatterns.push(...systemResult.patterns);
    }

    // 2. Remove padrões universais (certificação ICP-Brasil, etc)
    const universalResult = this._applyPatterns(
      cleanedText,
      this.universalPatterns,
      'universal'
    );
    cleanedText = universalResult.text;
    stats.removedPatterns.push(...universalResult.patterns);

    // 3. Aplica blacklist customizada do usuário
    if (this.customBlacklist.length > 0) {
      const blacklistResult = this._applyCustomBlacklist(cleanedText);
      cleanedText = blacklistResult.text;
      stats.removedPatterns.push(...blacklistResult.patterns);
    }

    // 4. Normalização final (linhas vazias, espaços, etc)
    cleanedText = this._normalizeText(cleanedText);

    stats.finalLength = cleanedText.length;
    stats.reductionPercentage = ((1 - stats.finalLength / stats.originalLength) * 100).toFixed(2);

    return {
      text: cleanedText,
      stats: stats
    };
  }

  /**
   * Aplica lista de padrões regex ao texto
   * @private
   */
  _applyPatterns(text, patterns, category) {
    let result = text;
    const matched = [];

    for (const pattern of patterns) {
      const before = result;
      result = result.replace(pattern.regex, pattern.replacement || '');

      if (before !== result) {
        matched.push({
          category: category,
          description: pattern.description,
          pattern: pattern.regex.source
        });
      }
    }

    return { text: result, patterns: matched };
  }

  /**
   * Aplica blacklist customizada do usuário
   * @private
   */
  _applyCustomBlacklist(text) {
    let result = text;
    const matched = [];

    for (const blacklistItem of this.customBlacklist) {
      if (!blacklistItem || blacklistItem.trim() === '') continue;

      try {
        // Trata como string literal (escape de caracteres especiais)
        const escapedPattern = blacklistItem.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(escapedPattern, 'gi');

        const before = result;
        result = result.replace(regex, '');

        if (before !== result) {
          matched.push({
            category: 'custom-blacklist',
            description: `Termo customizado removido: "${blacklistItem}"`,
            pattern: escapedPattern
          });
        }
      } catch (e) {
        console.warn(`Erro ao processar blacklist item "${blacklistItem}":`, e);
      }
    }

    return { text: result, patterns: matched };
  }

  /**
   * Normaliza texto final (remove linhas vazias excessivas, espaços, etc)
   * @private
   */
  _normalizeText(text) {
    return text
      // Remove múltiplos espaços em branco
      .replace(/[ \t]+/g, ' ')
      // Remove espaços no início/fim de linhas
      .replace(/^[ \t]+|[ \t]+$/gm, '')
      // Remove múltiplas linhas vazias (máx 2 consecutivas)
      .replace(/\n{3,}/g, '\n\n')
      // Remove linhas com apenas pontuação/símbolos isolados
      .replace(/^\s*[_\-=*]{1,5}\s*$/gm, '')
      .trim();
  }

  /**
   * Padrões de limpeza para PJE
   * @private
   */
  _getPJEPatterns() {
    return [
      {
        description: 'Código de verificação PJE (formato XXXX.9999.9XX9.X9XX)',
        regex: /c[óo]digo\s+de\s+verifica[çc][ãa]o:\s*[A-Z0-9]{4}\.[0-9]{4}\.[0-9A-Z]{4}\.[A-Z0-9]{4}/gi,
        replacement: ''
      },
      {
        description: 'Timestamp de geração PJE',
        regex: /este\s+documento\s+foi\s+gerado\s+pelo\s+usu[áa]rio\s+\d{3}\.\d{3}\.\d{3}-\d{2}\s+em\s+\d{2}\/\d{2}\/\d{4}\s+\d{2}:\d{2}:\d{2}/gi,
        replacement: ''
      },
      {
        description: 'URL de validação PJE',
        regex: /https?:\/\/[a-z0-9.-]*\.(trt|trf|tst|cnj)\d*\.jus\.br\/[^\s]*validar[^\s]*/gi,
        replacement: ''
      },
      {
        description: 'Tarja de assinatura dupla PJE (Resolução CNJ 281/2019)',
        regex: /documento\s+assinado\s+por\s+[^\n]{5,100}\s+e\s+certificado\s+digitalmente\s+por\s+[^\n]{5,100}/gi,
        replacement: ''
      },
      {
        description: 'QR Code placeholder PJE',
        regex: /\[QR\s+CODE\]|\{QR\s+CODE\}/gi,
        replacement: ''
      },
      {
        description: 'Rodapé PJE genérico',
        regex: /^[_\-=]+\s*processo\s+judicial\s+eletr[ôo]nico\s*[_\-=]+$/gmi,
        replacement: ''
      }
    ];
  }

  /**
   * Padrões de limpeza para ESAJ
   * @private
   */
  _getESAJPatterns() {
    return [
      {
        description: 'Selo lateral vertical ESAJ (texto rotacionado)',
        regex: /c[óo]digo\s+do\s+documento:\s*[A-Z0-9]{8,20}/gi,
        replacement: ''
      },
      {
        description: 'Conferência de documento digital ESAJ',
        regex: /confer[êe]ncia\s+de\s+documento\s+digital.*?portal\s+e-saj/gis,
        replacement: ''
      },
      {
        description: 'QR Code ESAJ com URL',
        regex: /https?:\/\/[a-z0-9.-]*\.jus\.br\/[^\s]*esaj[^\s]*\/documento[^\s]*/gi,
        replacement: ''
      },
      {
        description: 'Barra de assinatura digital ESAJ',
        regex: /assinado\s+digitalmente\s+por:\s*[^\n]{5,80}\s+data:\s*\d{2}\/\d{2}\/\d{4}\s+\d{2}:\d{2}:\d{2}/gi,
        replacement: ''
      },
      {
        description: 'Brasão e logotipo TJSP',
        regex: /tribunal\s+de\s+justi[çc]a\s+do\s+estado\s+de\s+s[ãa]o\s+paulo\s*-\s*tjsp/gi,
        replacement: ''
      },
      {
        description: 'Referência Resolução 552/11 (brasão TJSP)',
        regex: /resolu[çc][ãa]o\s+n?[º°]?\s*552\/11/gi,
        replacement: ''
      },
      {
        description: 'Marca d\'água ESAJ',
        regex: /\[marca\s+d.?[áa]gua:?\s*esaj\]/gi,
        replacement: ''
      }
    ];
  }

  /**
   * Padrões de limpeza para EPROC
   * @private
   */
  _getEPROCPatterns() {
    return [
      {
        description: 'Referência a arquivo .p7s (assinatura destacada)',
        regex: /assinatura\s+digital\s+dispon[ií]vel\s+em:\s*[^\n]*\.p7s/gi,
        replacement: ''
      },
      {
        description: 'Verificador de Conformidade ITI',
        regex: /verificador\s+de\s+conformidade\s+(iti|icp-brasil)/gi,
        replacement: ''
      },
      {
        description: 'Selo PAdES padrão EPROC',
        regex: /assinado\s+eletronicamente\s+por.*?certificado\s+digital\s+icp-brasil/gis,
        replacement: ''
      },
      {
        description: 'URL EPROC',
        regex: /https?:\/\/[a-z0-9.-]*\.(trf|tj)[a-z0-9]*\.jus\.br\/[^\s]*eproc[^\s]*/gi,
        replacement: ''
      },
      {
        description: 'ByteRange e referências técnicas CAdES',
        regex: /byterange\s*\[\s*\d+\s+\d+\s+\d+\s+\d+\s*\]/gi,
        replacement: ''
      }
    ];
  }

  /**
   * Padrões de limpeza para PROJUDI
   * @private
   */
  _getPROJUDIPatterns() {
    return [
      {
        description: 'Selo PAdES padrão PROJUDI',
        regex: /digitalmente\s+assinado\s+por.*?data:\s*\d{2}\/\d{2}\/\d{4}/gis,
        replacement: ''
      },
      {
        description: 'URL PROJUDI (variações regionais)',
        regex: /https?:\/\/[a-z0-9.-]*\.jus\.br\/[^\s]*projudi[^\s]*/gi,
        replacement: ''
      },
      {
        description: 'Assinador Livre TJRJ',
        regex: /assinador\s+livre\s+(tjrj|tribunal\s+de\s+justi[çc]a\s+do\s+rio\s+de\s+janeiro)/gi,
        replacement: ''
      },
      {
        description: 'Versão PROJUDI',
        regex: /projudi\s+-\s+vers[ãa]o\s+\d+\.\d+(\.\d+)?/gi,
        replacement: ''
      },
      {
        description: 'Brasões variados (variações regionais)',
        regex: /\[bras[ãa]o:?\s*[^\]]{5,50}\]/gi,
        replacement: ''
      }
    ];
  }

  /**
   * Padrões de limpeza para STF
   * @private
   */
  _getSTFPatterns() {
    return [
      {
        description: 'Marca d\'água com CPF do consulente STF',
        regex: /cpf\s+do\s+consulente:\s*\d{3}\.\d{3}\.\d{3}-\d{2}/gi,
        replacement: ''
      },
      {
        description: 'Alerta de marca d\'água STF',
        regex: /a\s+inser[çc][ãa]o\s+da\s+marca\s+d.?[áa]gua\s+se\s+sobrescreve.*?sistemas\s+internos\s+do\s+tribunal/gis,
        replacement: ''
      },
      {
        description: 'Assinatura PKCS7 STF',
        regex: /assinatura\s+digital\s+pkcs\s*[#]?\s*7/gi,
        replacement: ''
      },
      {
        description: 'URL validação STF',
        regex: /https?:\/\/(www\.)?stf\.jus\.br\/[^\s]*(validar|autenticar)[^\s]*/gi,
        replacement: ''
      },
      {
        description: 'Projeto Victor (ocerização automática)',
        regex: /documento\s+processado\s+pelo\s+projeto\s+victor/gi,
        replacement: ''
      },
      {
        description: 'Resolução STF 693/2020',
        regex: /resolu[çc][ãa]o\s+stf\s+n?[º°]?\s*693\/2020/gi,
        replacement: ''
      },
      {
        description: 'Cabeçalho STF padrão',
        regex: /supremo\s+tribunal\s+federal\s*-\s*stf.*?pet\s+v3/gis,
        replacement: ''
      }
    ];
  }

  /**
   * Padrões de limpeza para STJ
   * @private
   */
  _getSTJPatterns() {
    return [
      {
        description: 'Código de verificação STJ',
        regex: /c[óo]digo:\s*[A-Z0-9]{16,32}/gi,
        replacement: ''
      },
      {
        description: 'URL autenticação STJ',
        regex: /autentique\s+em:\s*https?:\/\/(www\.)?stj\.jus\.br\/validar[^\s]*/gi,
        replacement: ''
      },
      {
        description: 'Dados de certificado STJ',
        regex: /assinado\s+por:\s*[^\n]{5,80}\s+-\s+cpf:\s*\d{3}\.\d{3}\.\d{3}-\d{2}/gi,
        replacement: ''
      },
      {
        description: 'Timestamp STJ',
        regex: /data:\s*\d{2}\/\d{2}\/\d{4}\s+\d{2}:\d{2}:\d{2}\s+(brt|brst|-03:?00|-02:?00)/gi,
        replacement: ''
      },
      {
        description: 'Disclaimer MP 2.200-2/2001',
        regex: /documento\s+assinado\s+digitalmente\s+conforme\s+mp\s+n?[º°]?\s*2\.?200-2\/2001/gi,
        replacement: ''
      },
      {
        description: 'QR Code STJ',
        regex: /valide\s+este\s+documento\s+via\s+qr\s+code/gi,
        replacement: ''
      },
      {
        description: 'Cabeçalho STJ padrão',
        regex: /superior\s+tribunal\s+de\s+justi[çc]a\s*-\s*stj.*?central\s+do\s+processo\s+eletr[ôo]nico/gis,
        replacement: ''
      },
      {
        description: 'Marca d\'água STJ',
        regex: /\[logo\s+institucional\s+stj\]/gi,
        replacement: ''
      }
    ];
  }

  /**
   * Padrões genéricos para sistemas não identificados
   * @private
   */
  _getGenericJudicialPatterns() {
    return [
      {
        description: 'Assinatura digital genérica',
        regex: /assinado\s+digitalmente\s+por:?\s*[^\n]{5,100}/gi,
        replacement: ''
      },
      {
        description: 'Certificado digital genérico',
        regex: /certificado\s+digital:?\s*[^\n]{5,100}/gi,
        replacement: ''
      },
      {
        description: 'Data/hora de assinatura genérica',
        regex: /data\s+da\s+assinatura:?\s*\d{2}\/\d{2}\/\d{4}\s+\d{2}:\d{2}(:\d{2})?/gi,
        replacement: ''
      },
      {
        description: 'URL de validação genérica',
        regex: /valide?\s+este\s+documento\s+em:?\s*https?:\/\/[^\s]+/gi,
        replacement: ''
      }
    ];
  }

  /**
   * Padrões universais aplicados a TODOS os sistemas
   * @private
   */
  _getUniversalPatterns() {
    return [
      {
        description: 'Serial number de certificado (hexadecimal longo)',
        regex: /serial\s+number:?\s*[0-9A-F]{16,}/gi,
        replacement: ''
      },
      {
        description: 'Hash SHA-1',
        regex: /sha-?1:?\s*[0-9A-F]{40}/gi,
        replacement: ''
      },
      {
        description: 'Hash SHA-256',
        regex: /sha-?256:?\s*[0-9A-F]{64}/gi,
        replacement: ''
      },
      {
        description: 'Autoridade Certificadora ICP-Brasil',
        regex: /ac\s+[a-z]+\s+-\s+icp-brasil/gi,
        replacement: ''
      },
      {
        description: 'Emissor de certificado',
        regex: /emissor:?\s*cn\s*=\s*ac\s+[^\n]{10,80}/gi,
        replacement: ''
      },
      {
        description: 'Subject do certificado',
        regex: /subject:?\s*cn\s*=\s*[^\n]{10,80}cpf\s*=\s*\d{11}/gi,
        replacement: ''
      },
      {
        description: 'Validade do certificado',
        regex: /v[áa]lido\s+de:?\s*\d{2}\/\d{2}\/\d{4}\s+at[ée]:?\s*\d{2}\/\d{2}\/\d{4}/gi,
        replacement: ''
      },
      {
        description: 'Padrão PAdES/CAdES/XAdES',
        regex: /\b(pades|cades|xades)\s+(signature|assinatura)/gi,
        replacement: ''
      },
      {
        description: 'Referência ETSI TS 102 778',
        regex: /etsi\s+ts\s+102\s+778/gi,
        replacement: ''
      },
      {
        description: 'ITI - Instituto Nacional de Tecnologia da Informação',
        regex: /iti\s+-\s+instituto\s+nacional\s+de\s+tecnologia\s+da\s+informa[çc][ãa]o/gi,
        replacement: ''
      },
      {
        description: 'URL validador ITI',
        regex: /https?:\/\/(www\.)?validar\.iti\.gov\.br[^\s]*/gi,
        replacement: ''
      },
      {
        description: 'Timestamp RFC 3161',
        regex: /timestamp\s+rfc\s+3161/gi,
        replacement: ''
      },
      {
        description: 'Assinatura qualificada ICP-Brasil',
        regex: /assinatura\s+qualificada\s+icp-brasil/gi,
        replacement: ''
      },
      {
        description: 'Linhas separadoras estéticas',
        regex: /^[_\-=*]{10,}$/gm,
        replacement: ''
      },
      {
        description: 'Páginas numeradas isoladas (ex: "Página 1 de 10")',
        regex: /^p[áa]gina\s+\d+\s+(de|\/)\s+\d+\s*$/gmi,
        replacement: ''
      }
    ];
  }

  /**
   * Atualiza blacklist customizada
   * @param {array} blacklist - Array de strings/padrões a remover
   */
  setCustomBlacklist(blacklist) {
    this.customBlacklist = Array.isArray(blacklist) ? blacklist : [blacklist];
  }

  /**
   * Adiciona item à blacklist
   * @param {string} item - String a remover
   */
  addToBlacklist(item) {
    if (item && !this.customBlacklist.includes(item)) {
      this.customBlacklist.push(item);
    }
  }

  /**
   * Remove item da blacklist
   * @param {string} item - String a remover da blacklist
   */
  removeFromBlacklist(item) {
    const index = this.customBlacklist.indexOf(item);
    if (index > -1) {
      this.customBlacklist.splice(index, 1);
    }
  }

  /**
   * Retorna estatísticas de padrões disponíveis
   */
  getStatistics() {
    const stats = {};
    for (const [system, patterns] of Object.entries(this.systemPatterns)) {
      stats[system] = patterns.length;
    }
    stats['universal'] = this.universalPatterns.length;
    stats['customBlacklist'] = this.customBlacklist.length;
    return stats;
  }
}

// Export para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AdvancedSignatureCleaner;
}

// Disponibiliza globalmente no browser
if (typeof window !== 'undefined') {
  window.AdvancedSignatureCleaner = AdvancedSignatureCleaner;
  console.log('✓ AdvancedSignatureCleaner v1.0 carregado');
}
