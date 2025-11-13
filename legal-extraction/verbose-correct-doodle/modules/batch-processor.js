/**
 * BatchProcessor - Processamento em lote de múltiplos PDFs
 *
 * Permite processar múltiplos documentos processuais simultaneamente,
 * com controle de concorrência e organização automática.
 *
 * @author Pré-Processador Jurídico v4.1
 * @license MIT
 */

class BatchProcessor {
  constructor(options = {}) {
    this.maxConcurrency = options.maxConcurrency || 2; // 2 PDFs simultâneos (OCR é pesado)
    this.queue = [];
    this.active = 0;
    this.results = [];
    this.errors = [];
    this.progressCallback = options.progressCallback || null;
    this.itemCompleteCallback = options.itemCompleteCallback || null;

    // v4.1.3: Timeout global para prevenir loops infinitos
    this.GLOBAL_TIMEOUT = options.globalTimeout || 600000; // 10 minutos default
    this.MAX_RETRIES_PER_FILE = options.maxRetries || 1; // Tentar 1x (sem retry por default)
  }

  /**
   * Adiciona arquivos à fila de processamento
   */
  addFiles(files) {
    for (const file of files) {
      this.queue.push({
        file,
        status: 'pending',
        result: null,
        error: null
      });
    }
  }

  /**
   * Processa todos os arquivos na fila
   */
  async processAll(processingFunction) {
    const total = this.queue.length;
    let completed = 0;
    let failed = 0;

    // v4.1.3: Timeout global para prevenir travamentos
    const startTime = Date.now();

    console.log(`[BatchProcessor] Iniciando processamento de ${total} arquivo(s)...`);
    console.log(`[BatchProcessor] ⏱ Timeout global: ${this.GLOBAL_TIMEOUT / 1000}s`);

    // Atualizar status inicial
    this.updateProgress(0, total, 'Iniciando processamento em lote...');

    // Processar em lotes com concorrência controlada
    while (this.queue.length > 0 || this.active > 0) {
      // v4.1.3: Verificar timeout global
      const elapsed = Date.now() - startTime;
      if (elapsed > this.GLOBAL_TIMEOUT) {
        const remaining = this.queue.length;
        console.error(`[BatchProcessor] ⏱ TIMEOUT GLOBAL após ${elapsed / 1000}s. Abortando ${remaining} arquivo(s) restante(s).`);

        // Marcar arquivos restantes como erro
        while (this.queue.length > 0) {
          const item = this.queue.shift();
          failed++;
          this.errors.push({
            file: item.file.name,
            error: 'Timeout global do processamento em lote'
          });
        }

        break;
      }
      // Iniciar novos processamentos se há espaço
      while (this.active < this.maxConcurrency && this.queue.length > 0) {
        const item = this.queue.shift();
        this.active++;

        // Processar de forma assíncrona
        this.processItem(item, processingFunction)
          .then(result => {
            completed++;
            this.results.push({ file: item.file.name, result });

            if (this.itemCompleteCallback) {
              this.itemCompleteCallback({
                file: item.file.name,
                status: 'success',
                result,
                progress: (completed + failed) / total
              });
            }

            this.updateProgress(completed + failed, total,
              `Processado: ${item.file.name} (${completed}/${total})`);
          })
          .catch(error => {
            failed++;
            this.errors.push({ file: item.file.name, error: error.message });

            if (this.itemCompleteCallback) {
              this.itemCompleteCallback({
                file: item.file.name,
                status: 'error',
                error: error.message,
                progress: (completed + failed) / total
              });
            }

            this.updateProgress(completed + failed, total,
              `Erro: ${item.file.name} (${failed} falhas)`);
          })
          .finally(() => {
            this.active--;
            // v4.1.3: Log de segurança para debug
            console.log(`[BatchProcessor] Active workers: ${this.active}, Queue: ${this.queue.length}`);
          });
      }

      // Aguardar um pouco antes de verificar novamente
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    console.log(`[BatchProcessor] Concluído: ${completed} sucesso, ${failed} falhas`);

    return {
      total,
      completed,
      failed,
      results: this.results,
      errors: this.errors
    };
  }

  /**
   * Processa um item individual
   */
  async processItem(item, processingFunction) {
    try {
      item.status = 'processing';
      const result = await processingFunction(item.file);
      item.status = 'completed';
      item.result = result;
      return result;
    } catch (error) {
      item.status = 'error';
      item.error = error;
      throw error;
    }
  }

  /**
   * Atualiza progresso
   */
  updateProgress(current, total, message) {
    if (this.progressCallback) {
      this.progressCallback({
        current,
        total,
        percentage: (current / total) * 100,
        message
      });
    }
  }

  /**
   * Exporta resultados em lote (ZIP)
   */
  async exportBatchResults(results, format = 'txt') {
    // Requer JSZip (adicionar ao HTML)
    if (typeof JSZip === 'undefined') {
      throw new Error('JSZip não está carregado. Adicione a biblioteca para usar esta funcionalidade.');
    }

    const zip = new JSZip();
    const folder = zip.folder('documentos_processados');

    for (const item of results) {
      const filename = this.generateFilename(item.file, format);
      const content = this.formatContent(item.result, format);
      folder.file(filename, content);
    }

    // Adicionar relatório
    const report = this.generateBatchReport(results);
    folder.file('_RELATORIO.txt', report);

    // Gerar ZIP
    const blob = await zip.generateAsync({ type: 'blob' });
    return blob;
  }

  /**
   * Gera nome de arquivo para exportação
   */
  generateFilename(originalFilename, format) {
    const base = originalFilename.replace(/\.pdf$/i, '');
    const ext = {
      'txt': 'txt',
      'md': 'md',
      'html': 'html',
      'docx': 'docx'
    }[format] || 'txt';

    return `${base}_processado.${ext}`;
  }

  /**
   * Formata conteúdo para exportação
   */
  formatContent(result, format) {
    switch (format) {
      case 'txt':
        return result.cleanText || result.text || '';
      case 'md':
        return result.markdown || result.text || '';
      case 'html':
        return result.html || result.text || '';
      default:
        return result.text || '';
    }
  }

  /**
   * Gera relatório do processamento em lote
   */
  generateBatchReport(results) {
    const report = [];

    report.push('=== RELATÓRIO DE PROCESSAMENTO EM LOTE ===');
    report.push(`Data: ${new Date().toLocaleString('pt-BR')}`);
    report.push(`Total de arquivos: ${results.total}`);
    report.push(`Processados com sucesso: ${results.completed}`);
    report.push(`Falhas: ${results.failed}`);
    report.push('');

    report.push('--- ARQUIVOS PROCESSADOS ---');
    for (const item of results.results) {
      const confidence = item.result.confidenceScore?.percentage || 'N/A';
      const method = item.result.method || 'estrutural';
      report.push(`✓ ${item.file} (${confidence}% confiança, método: ${method})`);
    }

    if (results.errors.length > 0) {
      report.push('');
      report.push('--- ERROS ---');
      for (const error of results.errors) {
        report.push(`✗ ${error.file}: ${error.error}`);
      }
    }

    report.push('');
    report.push('--- ESTATÍSTICAS AGREGADAS ---');
    const avgConfidence = this.calculateAverageConfidence(results.results);
    const methodCounts = this.countMethods(results.results);

    report.push(`Confiança média: ${avgConfidence.toFixed(2)}%`);
    report.push(`Extração estrutural: ${methodCounts.structural}`);
    report.push(`OCR: ${methodCounts.ocr}`);

    return report.join('\n');
  }

  /**
   * Calcula confiança média
   */
  calculateAverageConfidence(results) {
    if (results.length === 0) return 0;

    const sum = results.reduce((acc, item) => {
      const confidence = item.result?.confidenceScore?.percentage || 0;
      return acc + confidence;
    }, 0);

    return sum / results.length;
  }

  /**
   * Conta métodos de extração usados
   */
  countMethods(results) {
    const counts = { structural: 0, ocr: 0 };

    for (const item of results) {
      const method = item.result?.method || 'structural';
      if (method === 'ocr') {
        counts.ocr++;
      } else {
        counts.structural++;
      }
    }

    return counts;
  }

  /**
   * Limpa estado do processador
   */
  reset() {
    this.queue = [];
    this.active = 0;
    this.results = [];
    this.errors = [];
  }
}

// Exportar
if (typeof module !== 'undefined' && module.exports) {
  module.exports = BatchProcessor;
}

if (typeof window !== 'undefined') {
  window.BatchProcessor = BatchProcessor;
}
