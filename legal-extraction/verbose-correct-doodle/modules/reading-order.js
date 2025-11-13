/**
 * ReadingOrderDetector - Determina ordem de leitura correta em PDFs
 *
 * Implementa algoritmos de spatial sorting, column detection e
 * bounding box analysis para corrigir ordem de leitura em documentos
 * com múltiplas colunas, texto rotacionado, e elementos sobrepostos.
 *
 * @author Pré-Processador Jurídico v4.0
 * @license MIT
 */

class ReadingOrderDetector {
  constructor() {
    this.TOLERANCE = 5;  // pixels de tolerância para mesma linha
    this.COLUMN_GAP_THRESHOLD_RATIO = 0.1; // 10% da largura
    this.debug = false;
  }

  /**
   * Determina ordem de leitura de itens de texto
   * @param {Array} textItems - Items de texto com coordenadas
   * @param {Object} pageGeometry - Dimensões da página
   * @returns {Array} Items ordenados
   */
  determineReadingOrder(textItems, pageGeometry) {
    if (!textItems || textItems.length === 0) {
      return [];
    }

    // Etapa 1: Spatial Sorting básico (top-to-bottom, left-to-right)
    let sorted = this.spatialSort(textItems);

    // Etapa 2: Column Detection
    const columns = this.detectColumns(sorted, pageGeometry);

    // Se houver múltiplas colunas, reordenar por coluna
    if (columns.length > 1) {
      sorted = this.sortByColumns(columns);
    }

    // Etapa 3: Bounding Box Analysis (resolver sobreposições)
    sorted = this.resolveBoundingBoxOverlaps(sorted);

    // Etapa 4: Hierarchy Preservation (títulos e seções)
    sorted = this.preserveHierarchy(sorted);

    // Etapa 5: Detect rotated text (selos laterais)
    sorted = this.handleRotatedText(sorted, pageGeometry);

    if (this.debug) {
      console.log('[ReadingOrderDetector] Items ordenados:', sorted.length);
    }

    return sorted;
  }

  /**
   * Ordenação espacial básica: top-to-bottom, left-to-right
   */
  spatialSort(items) {
    return [...items].sort((a, b) => {
      const yDiff = Math.abs((a.y || 0) - (b.y || 0));

      // Se estão na mesma linha (diferença Y < tolerância)
      if (yDiff < this.TOLERANCE) {
        return (a.x || 0) - (b.x || 0);  // ordenar por X
      }

      // Diferentes linhas: ordenar por Y (decrescente, pois PDF usa bottom-up)
      return (b.y || 0) - (a.y || 0);
    });
  }

  /**
   * Detecta colunas no documento através de análise de whitespace
   */
  detectColumns(items, geometry) {
    if (!geometry || !geometry.width) {
      return [items];  // Single column
    }

    const WIDTH = geometry.width;
    const COLUMN_GAP_THRESHOLD = WIDTH * this.COLUMN_GAP_THRESHOLD_RATIO;

    // Criar histogram de posições X
    const histogram = new Map();

    for (const item of items) {
      const x = Math.floor(item.x || 0);
      histogram.set(x, (histogram.get(x) || 0) + 1);
    }

    // Encontrar gaps (regiões sem texto)
    const gaps = this.findGaps(histogram, WIDTH, COLUMN_GAP_THRESHOLD);

    // Se não há gaps significativos, é single-column
    if (gaps.length === 0) {
      return [items];
    }

    // Agrupar items por coluna baseado nos gaps
    return this.groupItemsByColumns(items, gaps, WIDTH);
  }

  /**
   * Encontra gaps verticais (whitespace) no histogram
   */
  findGaps(histogram, width, threshold) {
    const gaps = [];
    let inGap = false;
    let gapStart = 0;

    for (let x = 0; x < width; x++) {
      const count = histogram.get(x) || 0;

      if (count === 0 && !inGap) {
        // Início de um gap
        inGap = true;
        gapStart = x;
      } else if (count > 0 && inGap) {
        // Fim de um gap
        const gapWidth = x - gapStart;
        if (gapWidth > threshold) {
          gaps.push({ start: gapStart, end: x, width: gapWidth });
        }
        inGap = false;
      }
    }

    return gaps;
  }

  /**
   * Agrupa items por coluna baseado nos gaps
   */
  groupItemsByColumns(items, gaps, pageWidth) {
    const columns = [];

    // Determinar limites de cada coluna
    const columnBounds = [];
    let start = 0;

    for (const gap of gaps) {
      columnBounds.push({ start, end: gap.start });
      start = gap.end;
    }
    columnBounds.push({ start, end: pageWidth });

    // Agrupar items em colunas
    for (const bounds of columnBounds) {
      const columnItems = items.filter(item => {
        const x = item.x || 0;
        return x >= bounds.start && x < bounds.end;
      });

      if (columnItems.length > 0) {
        columns.push(columnItems);
      }
    }

    return columns.length > 0 ? columns : [items];
  }

  /**
   * Ordena items respeitando estrutura de colunas
   */
  sortByColumns(columns) {
    const sorted = [];

    // Ordenar cada coluna individualmente por Y
    for (const column of columns) {
      const sortedColumn = this.spatialSort(column);
      sorted.push(...sortedColumn);
    }

    return sorted;
  }

  /**
   * Resolve sobreposições de bounding boxes (marcas d'água, selos)
   */
  resolveBoundingBoxOverlaps(items) {
    const resolved = [];
    const processed = new Set();

    for (let i = 0; i < items.length; i++) {
      if (processed.has(i)) continue;

      const item = items[i];
      const overlapping = [];

      // Encontrar items sobrepostos
      for (let j = i + 1; j < items.length; j++) {
        if (processed.has(j)) continue;

        if (this.boundingBoxesOverlap(item, items[j])) {
          overlapping.push({ index: j, item: items[j] });
        }
      }

      if (overlapping.length === 0) {
        // Não há sobreposição
        resolved.push(item);
        processed.add(i);
      } else {
        // Escolher elemento primário (maior área, conteúdo substantivo)
        const allItems = [item, ...overlapping.map(o => o.item)];
        const primary = this.selectPrimaryElement(allItems);

        resolved.push(primary);
        processed.add(i);
        overlapping.forEach(o => processed.add(o.index));
      }
    }

    return resolved;
  }

  /**
   * Verifica se dois bounding boxes se sobrepõem
   */
  boundingBoxesOverlap(a, b) {
    const boxA = this.getBoundingBox(a);
    const boxB = this.getBoundingBox(b);

    return !(
      boxA.right < boxB.left ||
      boxA.left > boxB.right ||
      boxA.bottom < boxB.top ||
      boxA.top > boxB.bottom
    );
  }

  /**
   * Calcula bounding box de um item
   */
  getBoundingBox(item) {
    const x = item.x || 0;
    const y = item.y || 0;
    const width = item.width || (item.text || '').length * 6; // estimativa
    const height = item.height || 12; // estimativa

    return {
      left: x,
      right: x + width,
      top: y,
      bottom: y - height  // PDF usa bottom-up
    };
  }

  /**
   * Seleciona elemento primário entre elementos sobrepostos
   */
  selectPrimaryElement(elements) {
    return elements.reduce((primary, current) => {
      const primaryArea = (primary.width || 0) * (primary.height || 0);
      const currentArea = (current.width || 0) * (current.height || 0);

      const primaryText = (primary.text || '').trim();
      const currentText = (current.text || '').trim();

      // Preferir:
      // 1. Maior área
      // 2. Conteúdo não-vazio
      // 3. Sem caracteres especiais excessivos

      if (currentArea > primaryArea && currentText.length > 0) {
        return current;
      }

      if (primaryText.length === 0 && currentText.length > 0) {
        return current;
      }

      return primary;
    });
  }

  /**
   * Preserva hierarquia de títulos e seções
   */
  preserveHierarchy(items) {
    const hierarchy = [];
    let currentSection = null;

    for (const item of items) {
      const text = (item.text || '').trim();
      const isTitle = this.isTitle(item, text);

      if (isTitle) {
        // Finalizar seção anterior
        if (currentSection) {
          hierarchy.push(currentSection);
        }

        // Iniciar nova seção
        currentSection = {
          title: item,
          content: []
        };
      } else {
        // Adicionar ao conteúdo
        if (currentSection) {
          currentSection.content.push(item);
        } else {
          // Conteúdo antes do primeiro título
          if (hierarchy.length === 0 || hierarchy[0].title) {
            hierarchy.unshift({ title: null, content: [] });
          }
          hierarchy[0].content.push(item);
        }
      }
    }

    // Finalizar última seção
    if (currentSection) {
      hierarchy.push(currentSection);
    }

    // Flatten mantendo hierarquia
    return hierarchy.flatMap(section =>
      section.title ? [section.title, ...section.content] : section.content
    );
  }

  /**
   * Detecta se um item é um título
   */
  isTitle(item, text) {
    // Heurísticas para detectar títulos
    const criteria = {
      // CAIXA ALTA
      isUpperCase: /^[A-ZÇÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛ\s]{5,}$/.test(text),

      // Marcadores legais
      isLegalMarker: /^(?:CAPÍTULO|SEÇÃO|TÍTULO|PARTE|Art\.|§)\s+[IVXLCDM0-9]+/i.test(text),

      // Fonte maior (se disponível)
      isLargeFont: (item.fontSize && item.fontSize > 12),

      // Negrito (se disponível)
      isBold: (item.fontWeight && item.fontWeight > 400)
    };

    // É título se atender pelo menos 1 critério
    return Object.values(criteria).some(Boolean);
  }

  /**
   * Trata texto rotacionado (selos laterais ESAJ)
   */
  handleRotatedText(items, geometry) {
    const rotated = [];
    const normal = [];

    for (const item of items) {
      const isRotated = this.isRotatedText(item, geometry);

      if (isRotated) {
        rotated.push({ ...item, _rotated: true });
      } else {
        normal.push(item);
      }
    }

    if (this.debug && rotated.length > 0) {
      console.log('[ReadingOrderDetector] Texto rotacionado detectado:', rotated.length);
    }

    // Elementos rotacionados vão para o final (geralmente são selos/marcas d'água)
    return [...normal, ...rotated];
  }

  /**
   * Detecta se texto está rotacionado
   */
  isRotatedText(item, geometry) {
    // Verificar se há transformação de rotação
    if (item.transform) {
      const [a, b, c, d] = item.transform;

      // Rotação ~90° ou ~270°: |b| ≈ 1 e |a| ≈ 0
      if (Math.abs(b) > 0.8 && Math.abs(a) < 0.2) {
        return true;
      }
    }

    // Verificar se está na margem direita (típico de selos verticais ESAJ)
    if (geometry && geometry.width) {
      const x = item.x || 0;
      const rightMargin = geometry.width * 0.9; // 90% da largura

      if (x > rightMargin) {
        return true;
      }
    }

    return false;
  }

  /**
   * Detecta parágrafos no conjunto ordenado de items
   */
  detectParagraphs(orderedItems) {
    const paragraphs = [];
    let currentParagraph = [];

    for (let i = 0; i < orderedItems.length; i++) {
      const item = orderedItems[i];
      const text = (item.text || '').trim();

      if (!text) {
        // Linha vazia = quebra de parágrafo
        if (currentParagraph.length > 0) {
          paragraphs.push([...currentParagraph]);
          currentParagraph = [];
        }
        continue;
      }

      // Detectar início de novo parágrafo
      const isNewParagraph = this.isNewParagraph(item, text);

      if (isNewParagraph && currentParagraph.length > 0) {
        paragraphs.push([...currentParagraph]);
        currentParagraph = [];
      }

      currentParagraph.push(item);
    }

    // Finalizar último parágrafo
    if (currentParagraph.length > 0) {
      paragraphs.push(currentParagraph);
    }

    return paragraphs;
  }

  /**
   * Detecta se item inicia novo parágrafo
   */
  isNewParagraph(item, text) {
    return (
      /^\s{2,}/.test(item.text || '') ||  // recuo
      /^[0-9]+\./.test(text) ||            // numeração
      /^[A-Z][).]/.test(text) ||           // letras
      /^[IVX]+\./.test(text) ||            // romanos
      /^[-•*]/.test(text)                  // bullets
    );
  }

  /**
   * Habilita modo debug
   */
  enableDebug() {
    this.debug = true;
  }

  /**
   * Gera relatório de análise de ordem de leitura
   */
  generateReport(items, columns, rotatedCount) {
    const report = [];

    report.push('=== ANÁLISE DE ORDEM DE LEITURA ===');
    report.push(`Total de items: ${items.length}`);
    report.push(`Colunas detectadas: ${columns.length}`);
    report.push(`Elementos rotacionados: ${rotatedCount || 0}`);

    if (columns.length > 1) {
      report.push('\n--- Distribuição por Coluna ---');
      columns.forEach((col, idx) => {
        report.push(`Coluna ${idx + 1}: ${col.length} items`);
      });
    }

    return report.join('\n');
  }
}

// Exportar para uso como módulo
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ReadingOrderDetector;
}

// Disponibilizar globalmente no navegador
if (typeof window !== 'undefined') {
  window.ReadingOrderDetector = ReadingOrderDetector;
}
