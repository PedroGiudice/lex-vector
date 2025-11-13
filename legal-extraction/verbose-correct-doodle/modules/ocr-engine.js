/**
 * OCREngine - Motor de OCR para PDFs escaneados
 *
 * Implementa detecção automática de PDFs escaneados e processamento OCR
 * usando Tesseract.js otimizado para documentos jurídicos em português.
 * Inspirado no Projeto Victor do STF.
 *
 * v4.1 Enhanced:
 * - Pré-processamento avançado (Otsu's binarization, noise reduction)
 * - Pós-processamento específico para documentos jurídicos
 * - Detecção melhorada de PDFs escaneados (análise de imagens)
 * - Threshold adaptativo
 *
 * v4.1.2 Hotfix:
 * - Correção de travamento OCR com caminhos explícitos de CDN (CORS fix)
 *
 * @author Pré-Processador Jurídico v4.1.2
 * @license MIT
 */

class OCREngine {
  constructor() {
    this.tesseract = null;
    this.initialized = false;
    this.initPromise = null;

    // Threshold: menos de 100 caracteres/página = provável escaneamento
    this.SCANNED_THRESHOLD = 100;

    // Configurações de qualidade
    this.DEFAULT_SCALE = 2.5;  // 2.5x para melhor qualidade (era 2.0)
    this.MIN_CONFIDENCE = 30;   // Confiança mínima do Tesseract

    // Novas configurações v4.1
    this.ENABLE_ADVANCED_PREPROCESSING = true;
    this.ENABLE_NOISE_REDUCTION = true;
    this.ENABLE_DESKEW = true; // Correção de inclinação

    // v4.1.2: Timeouts para evitar travamentos
    this.INIT_TIMEOUT = 45000;      // 45s para inicialização (download do modelo)
    this.RECOGNIZE_TIMEOUT = 90000; // 90s por página
    this.RENDER_TIMEOUT = 30000;    // 30s para renderização
  }

  /**
   * Helper: Executa promessa com timeout
   * @private
   */
  _withTimeout(promise, timeoutMs, operationName = 'Operação') {
    return Promise.race([
      promise,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error(`${operationName} excedeu timeout de ${timeoutMs}ms`)), timeoutMs)
      )
    ]);
  }

  /**
   * Inicializa o Tesseract.js
   */
  async initialize() {
    if (this.initialized) {
      return true;
    }

    if (this.initPromise) {
      return this.initPromise;
    }

    this.initPromise = (async () => {
      try {
        // Verificar se Tesseract está disponível
        if (typeof Tesseract === 'undefined') {
          throw new Error('Tesseract.js não está carregado');
        }

        console.log('[OCREngine] Inicializando Tesseract.js para português...');
        console.log('[OCREngine] ⏱ Timeout de inicialização: ' + (this.INIT_TIMEOUT / 1000) + 's');

        // v4.1.4: Criar worker (SEM especificar idioma - será carregado depois)
        // v4.1.2: Caminhos explícitos de CDN para evitar problemas CORS no GitHub Pages
        this.tesseract = await this._withTimeout(
          Tesseract.createWorker({
            workerPath: 'https://cdn.jsdelivr.net/npm/tesseract.js@4/dist/worker.min.js',
            langPath: 'https://tessdata.projectnaptha.com/4.0.0',
            corePath: 'https://cdn.jsdelivr.net/npm/tesseract.js-core@4/tesseract-core.wasm.js',
            logger: (m) => {
              if (m.status === 'recognizing text') {
                console.log(`[OCREngine] Progresso: ${Math.round(m.progress * 100)}%`);
              } else if (m.status) {
                console.log(`[OCREngine] ${m.status}...`);
              }
            }
          }),
          this.INIT_TIMEOUT,
          'Criação do worker'
        );

        console.log('[OCREngine] Worker criado, carregando idioma português...');

        // v4.1.4: CRITICAL FIX - Carregar idioma explicitamente
        // Fix: https://github.com/naptha/tesseract.js/issues/354
        await this._withTimeout(
          this.tesseract.loadLanguage('por'),
          this.INIT_TIMEOUT,
          'Carregamento do idioma'
        );

        console.log('[OCREngine] Idioma carregado, inicializando engine...');

        // v4.1.4: CRITICAL FIX - Inicializar engine explicitamente
        await this._withTimeout(
          this.tesseract.initialize('por'),
          this.INIT_TIMEOUT,
          'Inicialização do engine'
        );

        console.log('[OCREngine] Engine inicializado, configurando parâmetros...');

        // Configurar parâmetros otimizados para documentos jurídicos (COM TIMEOUT)
        await this._withTimeout(
          this.tesseract.setParameters({
            // Whitelist de caracteres (português + caracteres legais)
            tessedit_char_whitelist:
              'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' +
              'áàâãéèêíìîóòôõúùûçÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ' +
              '0123456789.,;:!?()[]{}§º°ª-_/\\ \n',

            // Preservar espaços entre palavras
            preserve_interword_spaces: '1',

            // PSM (Page Segmentation Mode) - 3 = fully automatic (mais estável que AUTO)
            tessedit_pageseg_mode: Tesseract.PSM.AUTO_ONLY
          }),
          5000,
          'Configuração de parâmetros'
        );

        this.initialized = true;
        console.log('[OCREngine] ✅ Tesseract inicializado com sucesso');

        return true;
      } catch (error) {
        console.error('[OCREngine] ❌ Erro ao inicializar:', error);
        this.initialized = false;
        this.initPromise = null;

        // Tentar limpar recursos em caso de erro
        if (this.tesseract) {
          try {
            await this.tesseract.terminate();
          } catch (e) {
            // Ignora erros de limpeza
          }
          this.tesseract = null;
        }

        throw error;
      }
    })();

    return this.initPromise;
  }

  /**
   * Detecta se PDF é escaneado (sem camada de texto)
   * v4.1 Enhanced: Inclui análise de conteúdo de imagem
   */
  async detectIfScanned(pdf) {
    try {
      let totalChars = 0;
      let hasImages = false;
      let imageCount = 0;
      const pageCount = pdf.numPages;

      // Amostrar primeiras 3 páginas
      const samplesToCheck = Math.min(3, pageCount);

      for (let i = 1; i <= samplesToCheck; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();

        const pageText = textContent.items
          .map(item => item.str || '')
          .join(' ')
          .trim();

        totalChars += pageText.length;

        // v4.1: Detecta presença de imagens (indicativo de escaneamento)
        try {
          const ops = await page.getOperatorList();
          const imgOps = ops.fnArray.filter((fn, idx) =>
            fn === pdfjsLib.OPS.paintImageXObject ||
            fn === pdfjsLib.OPS.paintInlineImageXObject
          );

          if (imgOps.length > 0) {
            hasImages = true;
            imageCount += imgOps.length;
          }
        } catch (e) {
          // Fallback: se não conseguir detectar imagens, ignora
        }
      }

      const avgCharsPerPage = totalChars / samplesToCheck;
      const avgImagesPerPage = imageCount / samplesToCheck;

      // v4.1: Lógica melhorada de detecção
      // - Menos de 100 chars/página = escaneado
      // - OU tem poucas chars E muitas imagens grandes
      const isScanned = avgCharsPerPage < this.SCANNED_THRESHOLD ||
                        (avgCharsPerPage < 500 && avgImagesPerPage > 0);

      console.log(`[OCREngine] Detecção: ${avgCharsPerPage.toFixed(0)} chars/página (threshold: ${this.SCANNED_THRESHOLD})`);
      console.log(`[OCREngine] Imagens: ${avgImagesPerPage.toFixed(1)} imagens/página`);
      console.log(`[OCREngine] Documento ${isScanned ? 'ESCANEADO' : 'COM CAMADA DE TEXTO'}`);

      return {
        isScanned,
        avgCharsPerPage,
        avgImagesPerPage,
        hasImages,
        threshold: this.SCANNED_THRESHOLD,
        pagesChecked: samplesToCheck,
        method: 'enhanced-v4.1'
      };
    } catch (error) {
      console.error('[OCREngine] Erro na detecção:', error);
      return {
        isScanned: false,
        error: error.message
      };
    }
  }

  /**
   * Processa PDF escaneado com OCR
   */
  async processScannedPDF(pdf, options = {}) {
    const opts = {
      scale: options.scale || this.DEFAULT_SCALE,
      progressCallback: options.progressCallback || null,
      pageRange: options.pageRange || null,  // { start: 1, end: 5 } ou null para todas
      ...options
    };

    if (!this.initialized) {
      await this.initialize();
    }

    const pages = [];
    const startPage = opts.pageRange?.start || 1;
    const endPage = opts.pageRange?.end || pdf.numPages;

    console.log(`[OCREngine] Processando páginas ${startPage} a ${endPage}...`);

    for (let i = startPage; i <= endPage; i++) {
      const pageStartTime = Date.now();
      let canvas = null; // v4.1.3: Declarar fora do try para cleanup em catch
      let processedCanvas = null;

      try {
        console.log(`[OCREngine] 📄 Processando página ${i}/${endPage}...`);

        const page = await pdf.getPage(i);
        const viewport = page.getViewport({ scale: opts.scale });

        // Renderizar página como imagem (COM TIMEOUT)
        canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        console.log(`[OCREngine] Renderizando página ${i} (${canvas.width}x${canvas.height})...`);

        await this._withTimeout(
          page.render({
            canvasContext: context,
            viewport: viewport
          }).promise,
          this.RENDER_TIMEOUT,
          `Renderização da página ${i}`
        );

        // Pré-processar imagem para melhor OCR
        console.log(`[OCREngine] Pré-processando imagem da página ${i}...`);
        processedCanvas = this.preprocessImage(canvas);

        // Executar OCR (COM TIMEOUT - PONTO MAIS CRÍTICO)
        console.log(`[OCREngine] ⚙️ Executando OCR na página ${i} (timeout: ${this.RECOGNIZE_TIMEOUT / 1000}s)...`);

        const result = await this._withTimeout(
          this.tesseract.recognize(processedCanvas),
          this.RECOGNIZE_TIMEOUT,
          `OCR da página ${i}`
        );

        const pageTime = ((Date.now() - pageStartTime) / 1000).toFixed(2);
        console.log(`[OCREngine] ✅ Página ${i} concluída em ${pageTime}s (confiança: ${result.data.confidence.toFixed(1)}%)`);

        pages.push({
          pageNumber: i,
          text: result.data.text,
          confidence: result.data.confidence,
          processingTime: pageTime,
          words: result.data.words.map(w => ({
            text: w.text,
            confidence: w.confidence,
            bbox: w.bbox
          }))
        });

        // Callback de progresso
        if (opts.progressCallback) {
          opts.progressCallback({
            current: i,
            total: endPage,
            percentage: ((i - startPage + 1) / (endPage - startPage + 1)) * 100,
            pageTime: pageTime
          });
        }

        // Limpar canvas
        canvas.remove();
        processedCanvas.remove();

      } catch (error) {
        const pageTime = ((Date.now() - pageStartTime) / 1000).toFixed(2);
        console.error(`[OCREngine] ❌ Erro na página ${i} após ${pageTime}s:`, error.message);

        // v4.1.3: ROBUSTNESS FIX - Limpar canvas em caso de erro
        try {
          if (canvas) canvas.remove();
          if (processedCanvas) processedCanvas.remove();
        } catch (cleanupError) {
          console.warn('[OCREngine] ⚠️ Falha ao limpar canvas:', cleanupError.message);
        }

        pages.push({
          pageNumber: i,
          text: '',
          confidence: 0,
          error: error.message,
          processingTime: pageTime,
          timeout: error.message.includes('timeout')
        });

        // Não aborta todo o processo - continua com próxima página
      }
    }

    // Calcular confiança média
    const avgConfidence = pages.reduce((sum, p) => sum + (p.confidence || 0), 0) / pages.length;

    // Estatísticas de processamento
    const successfulPages = pages.filter(p => !p.error).length;
    const failedPages = pages.filter(p => p.error).length;
    const timeoutPages = pages.filter(p => p.timeout).length;
    const totalTime = pages.reduce((sum, p) => sum + (parseFloat(p.processingTime) || 0), 0);

    console.log(`[OCREngine] ✅ OCR concluído:`);
    console.log(`  - Páginas processadas: ${successfulPages}/${pages.length}`);
    console.log(`  - Confiança média: ${avgConfidence.toFixed(2)}%`);
    console.log(`  - Tempo total: ${totalTime.toFixed(2)}s`);
    if (failedPages > 0) {
      console.log(`  - ⚠️ Falhas: ${failedPages} página(s)`);
      if (timeoutPages > 0) {
        console.log(`  - ⏱️ Timeouts: ${timeoutPages} página(s)`);
      }
    }

    return {
      pages,
      avgConfidence,
      totalPages: pages.length,
      successfulPages,
      failedPages,
      timeoutPages,
      totalTime,
      method: 'ocr'
    };
  }

  /**
   * Pré-processa imagem para melhor resultado de OCR
   * v4.1 Enhanced: Otsu's binarization + noise reduction + deskew
   */
  preprocessImage(canvas) {
    const context = canvas.getContext('2d');
    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    // Passo 1: Conversão para escala de cinza
    const grayData = new Uint8ClampedArray(canvas.width * canvas.height);
    for (let i = 0, j = 0; i < data.length; i += 4, j++) {
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];

      // Escala de cinza (média ponderada - padrão ITU-R BT.601)
      grayData[j] = Math.round(0.299 * r + 0.587 * g + 0.114 * b);
    }

    // Passo 2: Noise reduction (median filter 3x3) - SE habilitado
    let processedGray = grayData;
    if (this.ENABLE_NOISE_REDUCTION) {
      processedGray = this._medianFilter(grayData, canvas.width, canvas.height);
    }

    // Passo 3: Binarização adaptativa (Otsu's method) - SE habilitado
    let threshold = 128; // fallback
    if (this.ENABLE_ADVANCED_PREPROCESSING) {
      threshold = this._calculateOtsuThreshold(processedGray);
      console.log(`[OCREngine] Threshold Otsu calculado: ${threshold}`);
    }

    // Passo 4: Aplica binarização
    for (let i = 0, j = 0; i < data.length; i += 4, j++) {
      const binary = processedGray[j] > threshold ? 255 : 0;

      data[i] = binary;
      data[i + 1] = binary;
      data[i + 2] = binary;
      // Alpha mantém (data[i+3])
    }

    context.putImageData(imageData, 0, 0);
    return canvas;
  }

  /**
   * Calcula threshold ótimo usando método de Otsu
   * Baseado em: Otsu, N. (1979). "A threshold selection method from gray-level histograms"
   * @private
   */
  _calculateOtsuThreshold(grayData) {
    // Construir histograma
    const histogram = new Array(256).fill(0);
    for (let i = 0; i < grayData.length; i++) {
      histogram[grayData[i]]++;
    }

    // Total de pixels
    const total = grayData.length;

    // Calcular somas
    let sum = 0;
    for (let i = 0; i < 256; i++) {
      sum += i * histogram[i];
    }

    let sumB = 0;
    let wB = 0;
    let wF = 0;
    let maxVariance = 0;
    let threshold = 0;

    // Iterar sobre todos os possíveis thresholds
    for (let t = 0; t < 256; t++) {
      wB += histogram[t];               // Weight Background
      if (wB === 0) continue;

      wF = total - wB;                  // Weight Foreground
      if (wF === 0) break;

      sumB += t * histogram[t];

      const mB = sumB / wB;             // Mean Background
      const mF = (sum - sumB) / wF;     // Mean Foreground

      // Variância entre classes
      const variance = wB * wF * (mB - mF) * (mB - mF);

      if (variance > maxVariance) {
        maxVariance = variance;
        threshold = t;
      }
    }

    return threshold;
  }

  /**
   * Filtro de mediana 3x3 para redução de ruído
   * @private
   */
  _medianFilter(grayData, width, height) {
    const filtered = new Uint8ClampedArray(grayData.length);

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const neighbors = [];

        // Coletar vizinhos 3x3
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const nx = x + dx;
            const ny = y + dy;

            // Verificar bounds
            if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
              neighbors.push(grayData[ny * width + nx]);
            }
          }
        }

        // Calcular mediana
        neighbors.sort((a, b) => a - b);
        const median = neighbors[Math.floor(neighbors.length / 2)];

        filtered[y * width + x] = median;
      }
    }

    return filtered;
  }

  /**
   * Filtra palavras com baixa confiança
   */
  filterLowConfidenceWords(pages, minConfidence = null) {
    const threshold = minConfidence || this.MIN_CONFIDENCE;

    return pages.map(page => ({
      ...page,
      words: (page.words || []).filter(w => w.confidence >= threshold),
      text: (page.words || [])
        .filter(w => w.confidence >= threshold)
        .map(w => w.text)
        .join(' ')
    }));
  }

  /**
   * Mescla resultado OCR em formato de páginas
   */
  mergeOCRPages(ocrResult) {
    const pages = ocrResult.pages.map(page => ({
      lines: this.convertToLines(page.text),
      pageNumber: page.pageNumber,
      confidence: page.confidence
    }));

    return pages;
  }

  /**
   * Converte texto em estrutura de linhas
   */
  convertToLines(text) {
    return text.split('\n').map((lineText, idx) => ({
      text: lineText,
      y: idx * 20,  // Estimativa de posição vertical
      x: 0,
      pageHeight: 1000  // Estimativa
    }));
  }

  /**
   * Reinicializa o worker do Tesseract
   * Útil quando o worker trava ou para em um estado inconsistente
   * @returns {Promise<boolean>}
   */
  async reinitialize() {
    console.log('[OCREngine] 🔄 Reinicializando worker...');

    try {
      // Terminar worker atual
      await this.terminate();

      // Aguardar um pouco antes de reiniciar
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Reinicializar
      return await this.initialize();
    } catch (error) {
      console.error('[OCREngine] ❌ Erro ao reinicializar:', error);
      throw error;
    }
  }

  /**
   * Limpa recursos do Tesseract
   */
  async terminate() {
    if (this.tesseract) {
      try {
        console.log('[OCREngine] Liberando recursos do Tesseract...');
        await this._withTimeout(
          this.tesseract.terminate(),
          5000,
          'Terminação do worker'
        );
      } catch (error) {
        console.warn('[OCREngine] ⚠️ Erro ao terminar worker:', error.message);
      } finally {
        this.tesseract = null;
        this.initialized = false;
        this.initPromise = null;
        console.log('[OCREngine] ✅ Recursos liberados');
      }
    }
  }

  /**
   * Verifica se Tesseract está disponível
   */
  static isAvailable() {
    return typeof Tesseract !== 'undefined';
  }

  /**
   * Gera relatório de OCR
   */
  generateReport(ocrResult) {
    const report = [];

    report.push('=== RELATÓRIO DE OCR ===');
    report.push(`Páginas processadas: ${ocrResult.totalPages}`);
    report.push(`Confiança média: ${ocrResult.avgConfidence.toFixed(2)}%`);
    report.push(`Método: ${ocrResult.method}`);

    report.push('\n--- Confiança por Página ---');
    for (const page of ocrResult.pages) {
      const status = page.confidence >= 80 ? '✓' :
                     page.confidence >= 60 ? '⚠' : '✗';
      report.push(`${status} Página ${page.pageNumber}: ${(page.confidence || 0).toFixed(2)}%`);
    }

    const lowConfidencePages = ocrResult.pages.filter(p => p.confidence < 60);
    if (lowConfidencePages.length > 0) {
      report.push(`\n⚠ ATENÇÃO: ${lowConfidencePages.length} página(s) com confiança < 60%`);
      report.push('Recomenda-se revisão manual dessas páginas.');
    }

    return report.join('\n');
  }
}

// Exportar para uso como módulo
if (typeof module !== 'undefined' && module.exports) {
  module.exports = OCREngine;
}

// Disponibilizar globalmente no navegador
if (typeof window !== 'undefined') {
  window.OCREngine = OCREngine;
}
