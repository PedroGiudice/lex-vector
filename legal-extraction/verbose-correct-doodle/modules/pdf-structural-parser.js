/**
 * PDFStructuralParser - Análise estrutural de PDFs processuais
 *
 * Implementa parsing de baixo nível de objetos PDF para identificar e remover
 * elementos estruturais (assinaturas digitais, annotations, incremental updates)
 * conforme ETSI TS 102 778 (PAdES) e ISO 32000-2:2020.
 *
 * @author Pré-Processador Jurídico v4.0
 * @license MIT
 */

class PDFStructuralParser {
  constructor() {
    this.debug = false;
  }

  /**
   * Analisa estrutura interna do PDF
   * @param {ArrayBuffer} pdfBytes - Bytes do arquivo PDF
   * @returns {Promise<Object>} Estrutura analisada
   */
  async analyzePDFStructure(pdfBytes) {
    try {
      // Converter para Uint8Array se necessário
      const bytes = pdfBytes instanceof Uint8Array
        ? pdfBytes
        : new Uint8Array(pdfBytes);

      // Parsing básico do PDF
      const structure = {
        hasSignatures: false,
        signatureCount: 0,
        annotations: [],
        incrementalUpdates: 0,
        objectCount: 0,
        version: this.extractPDFVersion(bytes),
        metadata: {}
      };

      // Detectar assinaturas digitais
      const sigResult = this.detectSignatures(bytes);
      structure.hasSignatures = sigResult.found;
      structure.signatureCount = sigResult.count;
      structure.signatureLocations = sigResult.locations;

      // Detectar annotations (/Annots)
      structure.annotations = this.findAnnotations(bytes);

      // Detectar incremental updates
      structure.incrementalUpdates = this.countIncrementalUpdates(bytes);

      // Extrair metadados
      structure.metadata = this.extractMetadata(bytes);

      if (this.debug) {
        console.log('[PDFStructuralParser] Análise completa:', structure);
      }

      return structure;
    } catch (error) {
      console.warn('[PDFStructuralParser] Erro na análise estrutural:', error);
      return {
        hasSignatures: false,
        signatureCount: 0,
        annotations: [],
        incrementalUpdates: 0,
        objectCount: 0,
        version: '1.4',
        metadata: {},
        error: error.message
      };
    }
  }

  /**
   * Extrai versão do PDF do header
   */
  extractPDFVersion(bytes) {
    const header = this.bytesToString(bytes.slice(0, 20));
    const match = header.match(/%PDF-(\d+\.\d+)/);
    return match ? match[1] : '1.4';
  }

  /**
   * Detecta assinaturas digitais no PDF
   * Busca por padrões ICP-Brasil e PKCS#7
   */
  detectSignatures(bytes) {
    const text = this.bytesToString(bytes);

    const patterns = [
      /\/Type\s*\/Sig/gi,           // Objeto de assinatura
      /\/SubFilter\s*\/adbe\.pkcs7/gi,  // PKCS#7
      /\/SubFilter\s*\/ETSI\.CAdES/gi,  // CAdES
      /\/ByteRange\s*\[/gi,         // ByteRange (assinatura)
      /\/Contents\s*<[0-9a-fA-F]{100,}/gi, // Conteúdo da assinatura (hex)
    ];

    let count = 0;
    const locations = [];

    for (const pattern of patterns) {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        count++;
        locations.push({
          type: pattern.source,
          position: match.index,
          length: match[0].length
        });
      }
    }

    return {
      found: count > 0,
      count: count,
      locations: locations
    };
  }

  /**
   * Encontra annotations no PDF
   */
  findAnnotations(bytes) {
    const text = this.bytesToString(bytes);
    const annotations = [];

    // Buscar objetos /Annots
    const annotPattern = /\/Annots\s*\[([^\]]+)\]/gi;
    let match;

    while ((match = annotPattern.exec(text)) !== null) {
      annotations.push({
        position: match.index,
        content: match[1].trim(),
        type: 'annotation'
      });
    }

    return annotations;
  }

  /**
   * Conta incremental updates (múltiplas seções %%EOF)
   * PDFs assinados geralmente têm incremental updates
   */
  countIncrementalUpdates(bytes) {
    const text = this.bytesToString(bytes);
    const eofPattern = /%%EOF/g;
    const matches = text.match(eofPattern);
    return matches ? matches.length : 0;
  }

  /**
   * Extrai metadados do PDF
   */
  extractMetadata(bytes) {
    const text = this.bytesToString(bytes);
    const metadata = {};

    // Padrões comuns de metadados
    const patterns = {
      title: /\/Title\s*\(([^)]+)\)/,
      author: /\/Author\s*\(([^)]+)\)/,
      subject: /\/Subject\s*\(([^)]+)\)/,
      creator: /\/Creator\s*\(([^)]+)\)/,
      producer: /\/Producer\s*\(([^)]+)\)/,
      creationDate: /\/CreationDate\s*\(([^)]+)\)/,
      modDate: /\/ModDate\s*\(([^)]+)\)/,
    };

    for (const [key, pattern] of Object.entries(patterns)) {
      const match = text.match(pattern);
      if (match) {
        metadata[key] = match[1];
      }
    }

    return metadata;
  }

  /**
   * Calcula regiões do PDF a serem removidas
   */
  computeRemovalRegions(structure) {
    const regions = [];

    // Adicionar regiões de assinaturas
    if (structure.signatureLocations) {
      for (const sig of structure.signatureLocations) {
        regions.push({
          type: 'signature',
          start: sig.position,
          end: sig.position + sig.length,
          reason: 'Digital signature object'
        });
      }
    }

    // Adicionar regiões de annotations
    if (structure.annotations) {
      for (const annot of structure.annotations) {
        regions.push({
          type: 'annotation',
          start: annot.position,
          end: annot.position + annot.content.length,
          reason: 'Annotation object'
        });
      }
    }

    return regions;
  }

  /**
   * Verifica se PDF tem camada de texto
   * (se não tiver, é provável que seja escaneado)
   */
  hasTextLayer(pdfDocument, pageNumber = 1) {
    // Esta verificação será feita via PDF.js no código principal
    // Retorna informação sobre a presença de texto
    return {
      hasText: true, // placeholder
      confidence: 0.0
    };
  }

  /**
   * Converte bytes para string (helper)
   */
  bytesToString(bytes, maxLength = 1000000) {
    const length = Math.min(bytes.length, maxLength);
    const slice = bytes.slice(0, length);

    try {
      // Tentar decodificar como Latin1 (ISO-8859-1) que é comum em PDFs
      return new TextDecoder('latin1').decode(slice);
    } catch {
      // Fallback para string simples
      let str = '';
      for (let i = 0; i < slice.length; i++) {
        str += String.fromCharCode(slice[i]);
      }
      return str;
    }
  }

  /**
   * Gera relatório de análise estrutural
   */
  generateReport(structure) {
    const report = [];

    report.push('=== ANÁLISE ESTRUTURAL DO PDF ===');
    report.push(`Versão PDF: ${structure.version}`);
    report.push(`Assinaturas digitais: ${structure.signatureCount}`);
    report.push(`Annotations encontradas: ${structure.annotations.length}`);
    report.push(`Incremental updates: ${structure.incrementalUpdates}`);

    if (structure.metadata && Object.keys(structure.metadata).length > 0) {
      report.push('\n--- Metadados ---');
      for (const [key, value] of Object.entries(structure.metadata)) {
        report.push(`${key}: ${value}`);
      }
    }

    if (structure.signatureCount > 0) {
      report.push('\n--- Assinaturas Detectadas ---');
      const sigTypes = {};
      for (const loc of structure.signatureLocations || []) {
        sigTypes[loc.type] = (sigTypes[loc.type] || 0) + 1;
      }
      for (const [type, count] of Object.entries(sigTypes)) {
        report.push(`${type}: ${count} ocorrência(s)`);
      }
    }

    return report.join('\n');
  }

  /**
   * Habilita modo debug
   */
  enableDebug() {
    this.debug = true;
  }
}

// Exportar para uso como módulo
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PDFStructuralParser;
}

// Disponibilizar globalmente no navegador
if (typeof window !== 'undefined') {
  window.PDFStructuralParser = PDFStructuralParser;
}
