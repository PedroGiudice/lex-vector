/**
 * ProcessFileOrganizer - Organização de autos processuais
 *
 * Organiza documentos extraídos na ordem cronológica correta
 * como se fossem autos processuais físicos, facilitando leitura
 * sequencial e compreensão do processo.
 *
 * @author Pré-Processador Jurídico v4.1
 * @license MIT
 */

class ProcessFileOrganizer {
  constructor() {
    this.analyzer = new LegalDocumentAnalyzer();
  }

  /**
   * Organiza múltiplos documentos como autos processuais
   */
  organizeAsProcessFile(documents) {
    console.log(`[ProcessFileOrganizer] Organizando ${documents.length} documento(s)...`);

    // Analisar cada documento
    const analyzed = documents.map(doc => {
      const analysis = this.analyzer.analyzeDocument(doc.text || doc.cleanText || '');
      return {
        ...doc,
        analysis
      };
    });

    // Ordenar por ordem processual
    const sorted = this.sortByProcessOrder(analyzed);

    // Gerar estrutura de autos
    const processFile = this.buildProcessStructure(sorted);

    console.log(`[ProcessFileOrganizer] ${processFile.sections.length} seção(ões) criada(s)`);

    return processFile;
  }

  /**
   * Ordena documentos pela ordem processual cronológica
   */
  sortByProcessOrder(documents) {
    // Ordem processual típica:
    // 1. Petição Inicial
    // 2. Contestação
    // 3. Réplica
    // 10-19. Despachos e Decisões Interlocutórias (ordem de criação)
    // 20. Sentença
    // 25-29. Recursos (Agravo, Apelação, Embargos)
    // 30. Acórdão
    // 40+. Mandados, Atas

    return documents.sort((a, b) => {
      const orderA = a.analysis.order;
      const orderB = b.analysis.order;

      // Se mesma ordem, manter ordem original (cronológica)
      if (orderA === orderB) {
        return 0;
      }

      return orderA - orderB;
    });
  }

  /**
   * Constrói estrutura organizada de autos
   */
  buildProcessStructure(sortedDocuments) {
    const structure = {
      metadata: this.extractProcessMetadata(sortedDocuments),
      sections: [],
      summary: {
        totalDocuments: sortedDocuments.length,
        documentTypes: this.countDocumentTypes(sortedDocuments),
        chronology: this.buildChronology(sortedDocuments)
      }
    };

    // Agrupar por tipo de peça
    const groups = this.groupByType(sortedDocuments);

    // Criar seções
    for (const [type, docs] of Object.entries(groups)) {
      const section = {
        type,
        name: docs[0].analysis.name,
        order: docs[0].analysis.order,
        documents: docs.map((doc, idx) => ({
          index: idx + 1,
          title: this.generateDocumentTitle(doc, idx),
          text: doc.text || doc.cleanText || '',
          filename: doc.filename || doc.file?.name || `documento_${idx + 1}.txt`,
          confidence: doc.analysis.confidence,
          metadata: doc.metadata || {}
        }))
      };

      structure.sections.push(section);
    }

    // Ordenar seções pela ordem processual
    structure.sections.sort((a, b) => a.order - b.order);

    return structure;
  }

  /**
   * Agrupa documentos por tipo
   */
  groupByType(documents) {
    const groups = {};

    for (const doc of documents) {
      const type = doc.analysis.type;
      if (!groups[type]) {
        groups[type] = [];
      }
      groups[type].push(doc);
    }

    return groups;
  }

  /**
   * Extrai metadados do processo
   */
  extractProcessMetadata(documents) {
    // Buscar número do processo em todos os documentos
    let processNumber = null;
    let court = null;
    let parties = { plaintiff: null, defendant: null };

    for (const doc of documents) {
      const text = doc.text || doc.cleanText || '';

      // Número do processo (padrão CNJ)
      if (!processNumber) {
        const numberMatch = text.match(/\b(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})\b/);
        if (numberMatch) {
          processNumber = numberMatch[1];
        }
      }

      // Tribunal/Comarca
      if (!court) {
        const courtMatch = text.match(/(?:tribunal|comarca|juízo)\s+(?:de\s+)?([^\n]{10,80})/i);
        if (courtMatch) {
          court = courtMatch[0].trim();
        }
      }

      // Partes (simplificado)
      if (!parties.plaintiff) {
        const plaintiffMatch = text.match(/(?:autor|requerente|impetrante)[:\s]+([^\n]{5,80})/i);
        if (plaintiffMatch) {
          parties.plaintiff = plaintiffMatch[1].trim();
        }
      }

      if (!parties.defendant) {
        const defendantMatch = text.match(/(?:réu|requerido|impetrado)[:\s]+([^\n]{5,80})/i);
        if (defendantMatch) {
          parties.defendant = defendantMatch[1].trim();
        }
      }
    }

    return {
      processNumber,
      court,
      parties,
      extractedAt: new Date().toISOString()
    };
  }

  /**
   * Conta tipos de documentos
   */
  countDocumentTypes(documents) {
    const counts = {};

    for (const doc of documents) {
      const name = doc.analysis.name;
      counts[name] = (counts[name] || 0) + 1;
    }

    return counts;
  }

  /**
   * Constrói cronologia do processo
   */
  buildChronology(documents) {
    return documents.map((doc, idx) => ({
      order: idx + 1,
      type: doc.analysis.name,
      confidence: doc.analysis.confidence,
      filename: doc.filename || doc.file?.name || `documento_${idx + 1}`
    }));
  }

  /**
   * Gera título para documento
   */
  generateDocumentTitle(doc, index) {
    const baseName = doc.analysis.name;

    // Se há múltiplos do mesmo tipo, numerar
    if (index > 0) {
      return `${baseName} (${index + 1})`;
    }

    return baseName;
  }

  /**
   * Exporta autos organizados em Markdown
   */
  exportToMarkdown(processFile) {
    const md = [];

    md.push('# AUTOS DO PROCESSO');
    md.push('');

    // Metadados
    if (processFile.metadata.processNumber) {
      md.push(`**Processo nº:** ${processFile.metadata.processNumber}`);
    }
    if (processFile.metadata.court) {
      md.push(`**Juízo:** ${processFile.metadata.court}`);
    }
    if (processFile.metadata.parties.plaintiff) {
      md.push(`**Autor:** ${processFile.metadata.parties.plaintiff}`);
    }
    if (processFile.metadata.parties.defendant) {
      md.push(`**Réu:** ${processFile.metadata.parties.defendant}`);
    }

    md.push('');
    md.push('---');
    md.push('');

    // Índice
    md.push('## ÍNDICE');
    md.push('');

    for (const section of processFile.sections) {
      md.push(`- **${section.name}**`);
      for (const doc of section.documents) {
        md.push(`  - ${doc.title}`);
      }
    }

    md.push('');
    md.push('---');
    md.push('');

    // Documentos
    for (const section of processFile.sections) {
      md.push(`## ${section.name.toUpperCase()}`);
      md.push('');

      for (const doc of section.documents) {
        md.push(`### ${doc.title}`);
        md.push('');
        md.push(`_Confiança na identificação: ${doc.confidence}%_`);
        md.push('');
        md.push(doc.text);
        md.push('');
        md.push('---');
        md.push('');
      }
    }

    // Resumo
    md.push('## RESUMO DO PROCESSO');
    md.push('');
    md.push(`**Total de documentos:** ${processFile.summary.totalDocuments}`);
    md.push('');
    md.push('**Composição:**');
    for (const [type, count] of Object.entries(processFile.summary.documentTypes)) {
      md.push(`- ${type}: ${count}`);
    }

    md.push('');
    md.push('**Cronologia:**');
    for (const item of processFile.summary.chronology) {
      md.push(`${item.order}. ${item.type} (${item.confidence}% confiança) - _${item.filename}_`);
    }

    md.push('');
    md.push('---');
    md.push('');
    md.push(`_Autos organizados automaticamente em ${new Date().toLocaleString('pt-BR')}_`);

    return md.join('\n');
  }

  /**
   * Exporta autos em formato texto simples
   */
  exportToText(processFile) {
    const lines = [];

    lines.push('═══════════════════════════════════════════════════');
    lines.push('              AUTOS DO PROCESSO                    ');
    lines.push('═══════════════════════════════════════════════════');
    lines.push('');

    // Metadados
    if (processFile.metadata.processNumber) {
      lines.push(`Processo nº: ${processFile.metadata.processNumber}`);
    }
    if (processFile.metadata.court) {
      lines.push(`Juízo: ${processFile.metadata.court}`);
    }
    if (processFile.metadata.parties.plaintiff) {
      lines.push(`Autor: ${processFile.metadata.parties.plaintiff}`);
    }
    if (processFile.metadata.parties.defendant) {
      lines.push(`Réu: ${processFile.metadata.parties.defendant}`);
    }

    lines.push('');
    lines.push('───────────────────────────────────────────────────');
    lines.push('');

    // Documentos
    let docNumber = 1;
    for (const section of processFile.sections) {
      lines.push('');
      lines.push(`╔═══ ${section.name.toUpperCase()} ═══╗`);
      lines.push('');

      for (const doc of section.documents) {
        lines.push(`[${docNumber}] ${doc.title}`);
        lines.push(`Confiança: ${doc.confidence}%`);
        lines.push('');
        lines.push(doc.text);
        lines.push('');
        lines.push('───────────────────────────────────────────────────');
        lines.push('');
        docNumber++;
      }
    }

    // Resumo
    lines.push('');
    lines.push('═══════════════════════════════════════════════════');
    lines.push('                   RESUMO                          ');
    lines.push('═══════════════════════════════════════════════════');
    lines.push('');
    lines.push(`Total de documentos: ${processFile.summary.totalDocuments}`);
    lines.push('');
    lines.push('Composição:');
    for (const [type, count] of Object.entries(processFile.summary.documentTypes)) {
      lines.push(`  - ${type}: ${count}`);
    }

    lines.push('');
    lines.push(`Organizado automaticamente em ${new Date().toLocaleString('pt-BR')}`);
    lines.push('');

    return lines.join('\n');
  }

  /**
   * Gera relatório de organização
   */
  generateOrganizationReport(processFile) {
    const report = [];

    report.push('=== RELATÓRIO DE ORGANIZAÇÃO DE AUTOS ===');
    report.push('');

    if (processFile.metadata.processNumber) {
      report.push(`Processo: ${processFile.metadata.processNumber}`);
    }

    report.push(`Documentos processados: ${processFile.summary.totalDocuments}`);
    report.push(`Seções criadas: ${processFile.sections.length}`);
    report.push('');

    report.push('--- Estrutura Criada ---');
    for (const section of processFile.sections) {
      report.push(`${section.order}. ${section.name} (${section.documents.length} documento(s))`);
      for (const doc of section.documents) {
        report.push(`   - ${doc.title} (${doc.confidence}% confiança)`);
      }
    }

    report.push('');
    report.push('--- Tipos de Documento ---');
    for (const [type, count] of Object.entries(processFile.summary.documentTypes)) {
      report.push(`${type}: ${count}`);
    }

    return report.join('\n');
  }
}

// Exportar
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ProcessFileOrganizer;
}

if (typeof window !== 'undefined') {
  window.ProcessFileOrganizer = ProcessFileOrganizer;
}
