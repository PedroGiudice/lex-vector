/**
 * QualityMetrics - Sistema de pontuação de confiança para extração de PDFs
 *
 * Implementa métricas de qualidade conforme pesquisa acadêmica:
 * - Confidence scoring com thresholds
 * - CER (Character Error Rate) estimado
 * - WER (Word Error Rate) estimado
 * - Completude estrutural
 *
 * @author Pré-Processador Jurídico v4.0
 * @license MIT
 */

class QualityMetrics {
  constructor() {
    // Thresholds conforme pesquisa
    this.THRESHOLDS = {
      AUTO_ACCEPT: 0.90,        // > 90% = aprovação automática
      AUTOMATED_VALIDATION: 0.70, // 70-90% = validação automatizada
      HUMAN_REVIEW: 0.70         // < 70% = revisão humana
    };

    this.weights = {
      mlConfidence: 0.4,
      structuralCompleteness: 0.3,
      qualityMetrics: 0.3
    };
  }

  /**
   * Calcula score de confiança geral
   * @param {Object} extractionResult - Resultado da extração
   * @returns {Object} Score e recomendação
   */
  computeConfidenceScore(extractionResult) {
    const mlConfidence = this.computeMLConfidence(extractionResult);
    const structuralCompleteness = this.computeStructuralCompleteness(extractionResult);
    const qualityMetrics = this.computeQualityMetrics(extractionResult);

    // Fórmula ponderada
    const score = (
      this.weights.mlConfidence * mlConfidence +
      this.weights.structuralCompleteness * structuralCompleteness +
      this.weights.qualityMetrics * qualityMetrics
    );

    const recommendation = this.getRecommendation(score);

    return {
      score: parseFloat(score.toFixed(4)),
      percentage: parseFloat((score * 100).toFixed(2)),
      components: {
        mlConfidence: parseFloat(mlConfidence.toFixed(4)),
        structuralCompleteness: parseFloat(structuralCompleteness.toFixed(4)),
        qualityMetrics: parseFloat(qualityMetrics.toFixed(4))
      },
      recommendation,
      thresholds: this.THRESHOLDS
    };
  }

  /**
   * Calcula confiança do método de extração/ML
   */
  computeMLConfidence(result) {
    const text = result.text || '';
    const method = result.method || 'structural';

    if (method === 'ocr') {
      // Se for OCR, usar confidence do Tesseract
      if (result.ocrConfidence !== undefined) {
        return result.ocrConfidence / 100;
      }

      // Estimativa baseada em características do texto
      const estimatedConfidence = this.estimateOCRQuality(text);
      return estimatedConfidence;
    }

    // Para extração estrutural
    const expectedElements = ['text', 'pages', 'system'];
    const foundElements = expectedElements.filter(elem => {
      if (elem === 'text') return text.length > 0;
      if (elem === 'pages') return result.pages && result.pages > 0;
      if (elem === 'system') return result.system && result.system !== 'auto';
      return false;
    });

    const baseScore = foundElements.length / expectedElements.length;

    // Bonus se tiver estrutura de PDF analisada
    const structureBonus = result.pdfStructure ? 0.1 : 0;

    return Math.min(1.0, baseScore + structureBonus);
  }

  /**
   * Estima qualidade do OCR baseado em características do texto
   */
  estimateOCRQuality(text) {
    let score = 1.0;

    // Penalizar por caracteres inválidos/ruído
    const invalidCharRatio = (text.match(/[^\x20-\x7E\u00C0-\u00FF\s]/g) || []).length / text.length;
    score -= invalidCharRatio * 0.5;

    // Penalizar por excesso de caracteres especiais
    const specialCharRatio = (text.match(/[^a-zA-Z0-9\u00C0-\u00FFáàâãéèêíìîóòôõúùûçÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ\s.,;:!?()\[\]{}\-]/g) || []).length / text.length;
    score -= Math.max(0, specialCharRatio - 0.05) * 0.3;

    // Bonificar por presença de palavras comuns em português jurídico
    const legalWords = ['lei', 'artigo', 'processo', 'juiz', 'tribunal', 'parte', 'réu', 'autor'];
    const legalWordCount = legalWords.filter(word =>
      new RegExp(`\\b${word}\\b`, 'i').test(text)
    ).length;
    score += Math.min(0.2, legalWordCount * 0.025);

    return Math.max(0, Math.min(1, score));
  }

  /**
   * Calcula completude estrutural do documento
   */
  computeStructuralCompleteness(result) {
    const text = result.text || '';

    const elements = {
      // Verificar presença de cabeçalho/identificação
      hasHeader: this.detectHeader(text),

      // Corpo do documento (tamanho razoável)
      hasBody: text.length > 500 && text.length < 10000000,

      // Citações legais (Lei, Artigo, Parágrafo)
      hasLegalCitations: /\b(?:Lei\s+n[ºo°]?\s*\d+|Art\.?\s*\d+|§\s*\d+)/i.test(text),

      // Número de processo (CNJ)
      hasProcessNumber: /\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}/.test(text),

      // Datas
      hasDates: /\d{2}\/\d{2}\/\d{4}/.test(text),

      // Partes processuais
      hasParties: /\b(?:autor|réu|recorrente|recorrido|impetrante|impetrado)/i.test(text),

      // Dispositivo/conclusão
      hasDispositive: /\b(?:defiro|indefiro|julgo|determino|homologo|sentença|acórdão)/i.test(text)
    };

    const present = Object.values(elements).filter(Boolean).length;
    const total = Object.keys(elements).length;

    return present / total;
  }

  /**
   * Detecta presença de cabeçalho
   */
  detectHeader(text) {
    const headerPatterns = [
      /poder\s+judici[aá]rio/i,
      /tribunal/i,
      /justi[cç]a\s+(?:federal|estadual)/i,
      /comarca/i,
      /vara/i
    ];

    // Verificar nos primeiros 1000 caracteres
    const header = text.substring(0, 1000);

    return headerPatterns.some(pattern => pattern.test(header));
  }

  /**
   * Calcula métricas de qualidade do texto
   */
  computeQualityMetrics(result) {
    const text = result.text || '';

    const metrics = {
      // Tamanho razoável
      hasReasonableLength: text.length > 200 && text.length < 10000000,

      // Encoding correto (sem caracteres de erro)
      hasProperEncoding: !/�|�/.test(text),

      // Baixo ruído (estimativa)
      hasLowNoise: this.computeNoiseRatio(result) < 0.15,

      // Estrutura coerente (múltiplos parágrafos)
      hasCoherentStructure: this.detectParagraphs(text).length > 1,

      // Densidade lexical razoável
      hasReasonableDensity: this.computeLexicalDensity(text) > 0.3,

      // Sem excesso de repetição
      hasNoExcessiveRepetition: this.detectExcessiveRepetition(text) < 0.2
    };

    const passed = Object.values(metrics).filter(Boolean).length;
    const total = Object.keys(metrics).length;

    return passed / total;
  }

  /**
   * Calcula razão de ruído no texto
   */
  computeNoiseRatio(result) {
    const text = result.text || '';
    const totalChars = text.length;

    if (totalChars === 0) return 1.0;

    const noisePatterns = [
      /[0-9A-F]{32,}/g,                    // Hashes longos
      /\b[0-9A-F]{4}(?:-[0-9A-F]{4}){3,}\b/g, // Serial numbers
      /SHA-?(?:1|224|256|384|512)/gi,      // Referências a hash
      /MD5/gi,
      /ICP-?Brasil/gi,
      /\b[A-Z0-9]{20,}\b/g                 // Códigos longos
    ];

    let noiseChars = 0;
    for (const pattern of noisePatterns) {
      const matches = text.match(pattern) || [];
      noiseChars += matches.join('').length;
    }

    return noiseChars / totalChars;
  }

  /**
   * Detecta parágrafos no texto
   */
  detectParagraphs(text) {
    // Dividir por múltiplas quebras de linha
    return text.split(/\n\s*\n/).filter(p => p.trim().length > 50);
  }

  /**
   * Calcula densidade lexical (razão de palavras únicas)
   */
  computeLexicalDensity(text) {
    const words = text.toLowerCase()
      .replace(/[^\wáàâãéèêíìîóòôõúùûç\s]/gi, ' ')
      .split(/\s+/)
      .filter(w => w.length > 2);

    if (words.length === 0) return 0;

    const uniqueWords = new Set(words);
    return uniqueWords.size / words.length;
  }

  /**
   * Detecta repetição excessiva de blocos
   */
  detectExcessiveRepetition(text) {
    const lines = text.split('\n');
    const lineCount = new Map();

    for (const line of lines) {
      const normalized = line.trim().toLowerCase();
      if (normalized.length > 20) {
        lineCount.set(normalized, (lineCount.get(normalized) || 0) + 1);
      }
    }

    let repeatedLines = 0;
    for (const count of lineCount.values()) {
      if (count > 3) {
        repeatedLines += count;
      }
    }

    return lines.length > 0 ? repeatedLines / lines.length : 0;
  }

  /**
   * Retorna recomendação baseada no score
   */
  getRecommendation(score) {
    if (score >= this.THRESHOLDS.AUTO_ACCEPT) {
      return {
        code: 'AUTO_ACCEPT',
        label: 'Aprovação Automática',
        description: 'Alta confiança - documento processado com sucesso',
        color: '#28a745'
      };
    }

    if (score >= this.THRESHOLDS.AUTOMATED_VALIDATION) {
      return {
        code: 'AUTOMATED_VALIDATION',
        label: 'Validação Automatizada',
        description: 'Confiança moderada - recomenda-se verificação',
        color: '#ffc107'
      };
    }

    return {
      code: 'HUMAN_REVIEW',
      label: 'Revisão Humana',
      description: 'Baixa confiança - revisão manual necessária',
      color: '#dc3545'
    };
  }

  /**
   * Estima CER (Character Error Rate) - para uso futuro com ground truth
   */
  estimateCER(predicted, groundTruth) {
    if (!groundTruth) {
      return {
        cer: null,
        note: 'Ground truth não disponível'
      };
    }

    const distance = this.levenshteinDistance(predicted, groundTruth);
    const cer = distance / groundTruth.length;

    return {
      cer: parseFloat(cer.toFixed(4)),
      distance: distance,
      length: groundTruth.length,
      target: 0.005 // < 0.5% conforme pesquisa
    };
  }

  /**
   * Estima WER (Word Error Rate) - para uso futuro com ground truth
   */
  estimateWER(predicted, groundTruth) {
    if (!groundTruth) {
      return {
        wer: null,
        note: 'Ground truth não disponível'
      };
    }

    const predictedWords = predicted.split(/\s+/);
    const groundTruthWords = groundTruth.split(/\s+/);

    const distance = this.levenshteinDistance(
      predictedWords.join(' '),
      groundTruthWords.join(' ')
    );
    const wer = distance / groundTruthWords.length;

    return {
      wer: parseFloat(wer.toFixed(4)),
      distance: distance,
      wordCount: groundTruthWords.length,
      target: 0.025 // < 2.5% conforme pesquisa
    };
  }

  /**
   * Calcula distância de Levenshtein
   */
  levenshteinDistance(str1, str2) {
    const m = str1.length;
    const n = str2.length;
    const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;

    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        if (str1[i - 1] === str2[j - 1]) {
          dp[i][j] = dp[i - 1][j - 1];
        } else {
          dp[i][j] = 1 + Math.min(
            dp[i - 1][j],     // deletion
            dp[i][j - 1],     // insertion
            dp[i - 1][j - 1]  // substitution
          );
        }
      }
    }

    return dp[m][n];
  }

  /**
   * Gera relatório de qualidade
   */
  generateQualityReport(confidenceResult) {
    const report = [];

    report.push('=== RELATÓRIO DE QUALIDADE ===');
    report.push(`Score de Confiança: ${confidenceResult.percentage}%`);
    report.push(`Recomendação: ${confidenceResult.recommendation.label}`);
    report.push(`Descrição: ${confidenceResult.recommendation.description}`);

    report.push('\n--- Componentes do Score ---');
    report.push(`Confiança ML: ${(confidenceResult.components.mlConfidence * 100).toFixed(2)}%`);
    report.push(`Completude Estrutural: ${(confidenceResult.components.structuralCompleteness * 100).toFixed(2)}%`);
    report.push(`Métricas de Qualidade: ${(confidenceResult.components.qualityMetrics * 100).toFixed(2)}%`);

    report.push('\n--- Thresholds ---');
    report.push(`Aprovação Automática: > ${(this.THRESHOLDS.AUTO_ACCEPT * 100).toFixed(0)}%`);
    report.push(`Validação Automatizada: > ${(this.THRESHOLDS.AUTOMATED_VALIDATION * 100).toFixed(0)}%`);
    report.push(`Revisão Humana: < ${(this.THRESHOLDS.HUMAN_REVIEW * 100).toFixed(0)}%`);

    return report.join('\n');
  }
}

// Exportar para uso como módulo
if (typeof module !== 'undefined' && module.exports) {
  module.exports = QualityMetrics;
}

// Disponibilizar globalmente no navegador
if (typeof window !== 'undefined') {
  window.QualityMetrics = QualityMetrics;
}
