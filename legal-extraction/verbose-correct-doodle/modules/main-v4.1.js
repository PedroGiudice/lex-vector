/**
 * Main v4.1 Script - Pré-Processador Jurídico v4.1 Professional
 *
 * Extends v4.0 Enhanced with:
 * - Batch processing (multiple PDFs)
 * - Legal document analysis and identification
 * - Process file organization (autos)
 * - Standalone Markdown editor
 *
 * @author Pré-Processador Jurídico v4.1
 * @license MIT
 */

(function() {
  'use strict';

  console.log('[Main v4.1] Inicializando funcionalidades Professional...');

  // ===== VERIFICAR MÓDULOS V4.1 =====
  const modules = {
    legalAnalyzer: typeof LegalDocumentAnalyzer !== 'undefined' ? new LegalDocumentAnalyzer() : null,
    processOrganizer: typeof ProcessFileOrganizer !== 'undefined' ? new ProcessFileOrganizer() : null,
    batchProcessor: typeof BatchProcessor !== 'undefined' ? new BatchProcessor() : null,
    systemDetector: typeof JudicialSystemDetector !== 'undefined' ? new JudicialSystemDetector() : null,
    advancedCleaner: typeof AdvancedSignatureCleaner !== 'undefined' ? new AdvancedSignatureCleaner() : null
  };

  if (!modules.legalAnalyzer || !modules.processOrganizer || !modules.batchProcessor) {
    console.warn('[Main v4.1] Alguns módulos v4.1 não disponíveis. Funcionalidades limitadas.');
  }

  if (modules.systemDetector) {
    console.log('[Main v4.1] ✓ Detecção de sistema judicial habilitada');
  }

  if (modules.advancedCleaner) {
    console.log('[Main v4.1] ✓ Limpeza avançada de assinaturas habilitada');
  }

  // ===== HELPER FUNCTIONS =====

  /**
   * Sanitiza string HTML para prevenir XSS
   * @param {string} str - String a ser sanitizada
   * @returns {string} String sanitizada
   */
  function sanitizeHTML(str) {
    if (typeof str !== 'string') return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /**
   * Lê blacklist do campo de texto (v4.1)
   * @returns {array} Array de strings a serem removidas
   */
  function getBlacklist() {
    const blacklistField = $('#blacklist');
    if (!blacklistField || !blacklistField.value) {
      return [];
    }

    // Dividir por linhas, remover vazias e trim
    const MAX_LINES = 500; // Limite de linhas
    const MAX_LINE_LENGTH = 500; // Limite de caracteres por linha

    return blacklistField.value
      .split('\n')
      .slice(0, MAX_LINES) // Limita número de linhas
      .map(line => line.trim().substring(0, MAX_LINE_LENGTH)) // Limita tamanho de cada linha
      .filter(line => line.length > 0);
  }

  /**
   * Detecta sistema judicial usando novo módulo (v4.1)
   * @param {string} text - Texto extraído do PDF
   * @returns {string} Código do sistema (PJE, ESAJ, STF, etc)
   */
  function detectSystemEnhanced(text) {
    if (!modules.systemDetector) {
      // Fallback para detecção antiga (main-enhanced.js)
      return detectSystem(text);
    }

    const detection = modules.systemDetector.detectSystem(text);
    console.log(`[Main v4.1] Sistema detectado: ${detection.name} (${detection.confidence}% confiança)`);

    return detection.system;
  }

  /**
   * Aplica limpeza avançada de assinaturas (v4.1)
   * @param {string} text - Texto pré-limpo
   * @param {string} detectedSystem - Sistema detectado
   * @returns {string} Texto com assinaturas removidas
   */
  function applyAdvancedCleaning(text, detectedSystem) {
    if (!modules.advancedCleaner) {
      return text;
    }

    // Atualizar blacklist no cleaner
    const blacklist = getBlacklist();
    modules.advancedCleaner.setCustomBlacklist(blacklist);

    // Aplicar limpeza específica do sistema
    updateProgress(88, 'Removendo assinaturas e selos...');
    const cleanResult = modules.advancedCleaner.clean(text, detectedSystem);

    // Log estatísticas
    console.log(`[Main v4.1] Limpeza avançada concluída:`);
    console.log(`  - Texto original: ${cleanResult.stats.originalLength} chars`);
    console.log(`  - Texto final: ${cleanResult.stats.finalLength} chars`);
    console.log(`  - Redução: ${cleanResult.stats.reductionPercentage}%`);
    console.log(`  - Padrões removidos: ${cleanResult.stats.removedPatterns.length}`);

    if (cleanResult.stats.removedPatterns.length > 0) {
      console.log('  - Categorias:', [...new Set(cleanResult.stats.removedPatterns.map(p => p.category))]);
    }

    return cleanResult.text;
  }

  // ===== STATE MANAGEMENT =====
  const state = {
    batchResults: [],
    currentBatchFile: null,
    documentAnalysis: null,
    detectedSystem: null // v4.1: armazena sistema detectado
  };

  // ===== EXTEND PROCESSING PIPELINE =====
  // Interceptar o processamento original para adicionar análise de documentos

  const originalProcessBtn = $('#processBtn');
  if (originalProcessBtn && originalProcessBtn.__v41_patched !== true) {
    const originalClickHandler = originalProcessBtn.onclick;

    // Remover listener original
    const newProcessBtn = originalProcessBtn.cloneNode(true);
    originalProcessBtn.parentNode.replaceChild(newProcessBtn, originalProcessBtn);

    // Adicionar novo handler que integra análise de documentos
    newProcessBtn.addEventListener('click', async () => {
      const file = $('#pdfFile').files?.[0];
      if (!file) {
        showError('Selecione um arquivo PDF');
        return;
      }

      newProcessBtn.disabled = true;
      newProcessBtn.innerHTML = '<span class="loading"></span> Processando...';

      try {
        updateProgress(0, 'Inicializando...');

        // Extrair com métodos enhanced (v4.0)
        const extractResult = await extractFromPDF(file, {
          enableOCR: $('#enableOCR').checked
        });

        const { pages, pdfStructure, method } = extractResult;

        updateProgress(85, 'Limpando texto...');

        const fullText = pages.map(p => p.lines.map(l => l.text).join('\n')).join('\n\n');

        // ===== v4.1: DETECÇÃO APRIMORADA DE SISTEMA =====
        let selectedSystem = getSelectedSystem();
        if (selectedSystem === 'auto') {
          selectedSystem = detectSystemEnhanced(fullText);
          state.detectedSystem = selectedSystem;
        }

        const selectedMode = getSelectedMode();

        // Limpeza básica (v4.0)
        const result = Cleaner.clean(pages, {
          system: selectedSystem,
          mode: selectedMode,
          removeHash: $('#rmHash').checked,
          removeSignature: $('#rmAssinatura').checked,
          removeProtocol: $('#rmProtocolo').checked,
          removePageNum: $('#rmPageNum').checked,
          removeHeader: $('#rmHeader').checked,
          normalizeBreaks: $('#normalizeBreaks').checked,
          whitelist: getWhitelist()
        });

        let cleanText = Cleaner.joinPages(result.pages);

        // ===== v4.1: LIMPEZA AVANÇADA DE ASSINATURAS =====
        if (modules.advancedCleaner && selectedSystem) {
          cleanText = applyAdvancedCleaning(cleanText, selectedSystem);
        }

        // ===== v4.1: ANÁLISE DE DOCUMENTO JURÍDICO =====
        if (modules.legalAnalyzer) {
          updateProgress(90, 'Analisando tipo de documento jurídico...');

          state.documentAnalysis = modules.legalAnalyzer.analyzeDocument(cleanText);
          console.log('[Main v4.1] Análise do documento:', state.documentAnalysis);

          // Verificar se há múltiplos documentos
          const separated = modules.legalAnalyzer.separateDocuments(cleanText);
          if (separated.length > 1) {
            console.log(`[Main v4.1] Múltiplos documentos detectados: ${separated.length}`);
            // Mostrar informação ao usuário
            showSuccess(`${separated.length} documentos detectados neste PDF`);
          }
        }

        updateProgress(90, 'Calculando métricas de qualidade...');

        // Calcular métricas de qualidade (v4.0)
        const qualityMetrics = new QualityMetrics();
        const confidenceScore = qualityMetrics.computeConfidenceScore({
          text: cleanText,
          pages: result.stats.pages,
          system: selectedSystem,
          method: method,
          pdfStructure: pdfStructure
        });

        console.log('[Main] Métricas de qualidade:', confidenceScore);

        updateProgress(95, 'Gerando outputs...');

        const markdown = MarkdownConverter.addMetadata(
          MarkdownConverter.convert(cleanText),
          {
            ...result.stats,
            system: SYSTEM_PATTERNS[selectedSystem]?.name || selectedSystem.toUpperCase(),
            mode: selectedMode.toUpperCase(),
            method: method,
            confidence: confidenceScore.percentage,
            // NOVO: Adicionar tipo de documento se disponível
            ...(state.documentAnalysis ? {
              documentType: state.documentAnalysis.name,
              documentConfidence: state.documentAnalysis.confidence
            } : {})
          }
        );
        const html = HtmlConverter.convert(cleanText);

        $('#outputText').value = cleanText;
        $('#outputMarkdown').value = markdown;
        $('#outputHtml').value = html;

        window.lastResult = {
          cleanText,
          markdown,
          html,
          stats: result.stats,
          system: selectedSystem,
          mode: selectedMode,
          method,
          confidenceScore,
          // NOVO: Análise do documento
          documentAnalysis: state.documentAnalysis,
          filename: file.name
        };

        // Atualizar UI com métricas (v4.0)
        $('#statPages').textContent = result.stats.pages;
        $('#statRemoved').textContent = result.stats.removed;
        $('#statSystem').textContent = SYSTEM_PATTERNS[selectedSystem]?.name || selectedSystem.toUpperCase();
        $('#statMode').textContent = selectedMode.toUpperCase();
        $('#statMethod').textContent = method === 'ocr' ? 'OCR' : 'Estrutural';

        // NOVO: Adicionar tipo de documento às estatísticas
        if (state.documentAnalysis) {
          const docTypeRow = document.createElement('div');
          docTypeRow.className = 'stats-row';
          docTypeRow.innerHTML = `
            <span class="stats-label">Tipo de documento:</span>
            <span class="stats-value">${sanitizeHTML(state.documentAnalysis.name)} (${state.documentAnalysis.confidence}%)</span>
          `;

          const statsBox = $('#statsBox');
          if (statsBox && !$('#statDocType')) {
            statsBox.appendChild(docTypeRow);
          }
        }

        $('#statsBox').style.display = 'block';

        // Exibir Quality Badge (v4.0)
        const qualityBadgeContainer = $('#qualityBadgeContainer');
        const qualityBadge = $('#qualityBadge');
        const qualityScore = $('#qualityScore');
        const qualityStatus = $('#qualityStatus');

        qualityScore.textContent = `${confidenceScore.percentage}%`;
        qualityStatus.textContent = confidenceScore.recommendation.label;

        qualityBadge.className = 'quality-badge';
        if (confidenceScore.recommendation.code === 'AUTO_ACCEPT') {
          qualityBadge.classList.add('auto-accept');
        } else if (confidenceScore.recommendation.code === 'AUTOMATED_VALIDATION') {
          qualityBadge.classList.add('automated-validation');
        } else {
          qualityBadge.classList.add('human-review');
        }

        // Atualizar métricas detalhadas
        $('#metricML').value = confidenceScore.components.mlConfidence;
        $('#metricMLValue').textContent = `${(confidenceScore.components.mlConfidence * 100).toFixed(0)}%`;

        $('#metricStructure').value = confidenceScore.components.structuralCompleteness;
        $('#metricStructureValue').textContent = `${(confidenceScore.components.structuralCompleteness * 100).toFixed(0)}%`;

        $('#metricQuality').value = confidenceScore.components.qualityMetrics;
        $('#metricQualityValue').textContent = `${(confidenceScore.components.qualityMetrics * 100).toFixed(0)}%`;

        qualityBadgeContainer.style.display = 'block';

        $('#downloadTxtBtn').disabled = false;
        $('#downloadMdBtn').disabled = false;
        $('#downloadDocxBtn').disabled = false;
        $('#downloadHtmlBtn').disabled = false;

        updateProgress(100, 'Processamento concluído!');
        showSuccess('Documento processado com sucesso!');

      } catch (err) {
        console.error(err);
        showError('Falha ao processar PDF: ' + err.message);
      } finally {
        newProcessBtn.disabled = false;
        newProcessBtn.textContent = 'Processar';
      }
    });

    newProcessBtn.__v41_patched = true;
  }

  // ===== BATCH PROCESSING UI =====
  const batchFilesInput = $('#pdfBatchFiles');
  const batchFileInfo = $('#batchFileInfo');
  const batchActions = $('#batchActions');
  const processBatchBtn = $('#processBatchBtn');
  const batchProgressContainer = $('#batchProgressContainer');
  const batchProgressList = $('#batchProgressList');
  const batchExportSection = $('#batchExportSection');
  const downloadBatchZipBtn = $('#downloadBatchZipBtn');
  const organizeAsAutosBtn = $('#organizeAsAutosBtn');

  if (batchFilesInput) {
    batchFilesInput.addEventListener('change', () => {
      const files = Array.from(batchFilesInput.files || []);
      if (files.length > 0) {
        batchFileInfo.innerHTML = `<span class="file-name">${files.length} arquivo(s) selecionado(s)</span>`;
        batchActions.style.display = 'block';
        state.batchResults = []; // Reset results
        batchExportSection.style.display = 'none';
      } else {
        batchFileInfo.innerHTML = `<span class="file-name">Nenhum arquivo selecionado</span>`;
        batchActions.style.display = 'none';
      }
    });
  }

  if (processBatchBtn && modules.batchProcessor) {
    processBatchBtn.addEventListener('click', async () => {
      const files = Array.from(batchFilesInput.files || []);
      if (files.length === 0) {
        showError('Selecione pelo menos um arquivo PDF');
        return;
      }

      processBatchBtn.disabled = true;
      processBatchBtn.innerHTML = '<span class="loading"></span> Processando...';
      batchProgressContainer.style.display = 'block';
      batchProgressList.innerHTML = '';

      // Criar elementos de progresso para cada arquivo
      const progressElements = {};
      files.forEach(file => {
        const div = document.createElement('div');
        div.style.padding = '0.5rem 0';
        div.style.borderBottom = '1px solid var(--border)';
        const safeFileName = sanitizeHTML(file.name);
        const safeFileId = file.name.replace(/[^a-zA-Z0-9]/g, '_');
        div.innerHTML = `
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
            <span>${safeFileName}</span>
            <span id="status-${safeFileId}">Aguardando...</span>
          </div>
        `;
        batchProgressList.appendChild(div);
        progressElements[file.name] = div;
      });

      try {
        // Adicionar arquivos ao batch processor
        modules.batchProcessor.reset();
        modules.batchProcessor.addFiles(files);

        // Processar com callback de progresso
        const results = await modules.batchProcessor.processAll(async (file) => {
          const safeId = file.name.replace(/[^a-zA-Z0-9]/g, '_');
          const statusEl = $(`#status-${safeId}`);

          if (statusEl) statusEl.textContent = 'Processando...';

          // Processar usando a mesma lógica do processamento único
          const extractResult = await extractFromPDF(file, {
            enableOCR: $('#enableOCR').checked
          });

          const { pages } = extractResult;
          const fullText = pages.map(p => p.lines.map(l => l.text).join('\n')).join('\n\n');

          let selectedSystem = getSelectedSystem();
          if (selectedSystem === 'auto') {
            selectedSystem = detectSystem(fullText);
          }

          const result = Cleaner.clean(pages, {
            system: selectedSystem,
            mode: getSelectedMode(),
            removeHash: $('#rmHash').checked,
            removeSignature: $('#rmAssinatura').checked,
            removeProtocol: $('#rmProtocolo').checked,
            removePageNum: $('#rmPageNum').checked,
            removeHeader: $('#rmHeader').checked,
            normalizeBreaks: $('#normalizeBreaks').checked,
            whitelist: getWhitelist()
          });

          const cleanText = Cleaner.joinPages(result.pages);

          // Analisar documento
          let documentAnalysis = null;
          if (modules.legalAnalyzer) {
            documentAnalysis = modules.legalAnalyzer.analyzeDocument(cleanText);
          }

          if (statusEl) statusEl.textContent = '✓ Concluído';

          return {
            filename: file.name,
            cleanText,
            text: cleanText,
            documentAnalysis,
            file
          };
        });

        state.batchResults = results;

        showSuccess(`${results.length} documento(s) processado(s) com sucesso!`);
        batchExportSection.style.display = 'block';

      } catch (err) {
        console.error(err);
        showError('Falha no processamento em lote: ' + err.message);
      } finally {
        processBatchBtn.disabled = false;
        processBatchBtn.textContent = 'Processar Lote';
      }
    });
  }

  // Download batch as ZIP
  if (downloadBatchZipBtn) {
    downloadBatchZipBtn.addEventListener('click', async () => {
      if (state.batchResults.length === 0) {
        showError('Nenhum resultado de lote disponível');
        return;
      }

      if (typeof JSZip === 'undefined') {
        showError('JSZip não disponível. Exportação ZIP desabilitada.');
        return;
      }

      try {
        downloadBatchZipBtn.disabled = true;
        downloadBatchZipBtn.innerHTML = '<span class="loading"></span> Criando ZIP...';

        const format = 'txt'; // Pode ser configurável
        const result = await modules.batchProcessor.exportBatchResults(state.batchResults, format);

        downloadBatchZipBtn.disabled = false;
        downloadBatchZipBtn.textContent = 'ZIP (Todos)';
        showSuccess('ZIP criado com sucesso!');
      } catch (err) {
        console.error(err);
        showError('Falha ao criar ZIP: ' + err.message);
        downloadBatchZipBtn.disabled = false;
        downloadBatchZipBtn.textContent = 'ZIP (Todos)';
      }
    });
  }

  // Organize as Autos
  if (organizeAsAutosBtn && modules.processOrganizer) {
    organizeAsAutosBtn.addEventListener('click', () => {
      if (state.batchResults.length === 0) {
        showError('Nenhum resultado de lote disponível');
        return;
      }

      try {
        organizeAsAutosBtn.disabled = true;
        organizeAsAutosBtn.innerHTML = '<span class="loading"></span> Organizando...';

        // Organizar documentos
        const processFile = modules.processOrganizer.organizeAsProcessFile(state.batchResults);

        // Exportar como Markdown
        const markdown = modules.processOrganizer.exportToMarkdown(processFile);
        const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
        saveAs(blob, 'autos_organizados.md');

        // Também exportar como TXT
        const txt = modules.processOrganizer.exportToText(processFile);
        const blobTxt = new Blob([txt], { type: 'text/plain;charset=utf-8' });
        saveAs(blobTxt, 'autos_organizados.txt');

        showSuccess('Autos organizados e exportados!');

        organizeAsAutosBtn.disabled = false;
        organizeAsAutosBtn.textContent = 'Organizar Autos';
      } catch (err) {
        console.error(err);
        showError('Falha ao organizar autos: ' + err.message);
        organizeAsAutosBtn.disabled = false;
        organizeAsAutosBtn.textContent = 'Organizar Autos';
      }
    });
  }

  // ===== MARKDOWN EDITOR =====
  const editorText = $('#editorText');
  const editorExportTxt = $('#editorExportTxt');
  const editorExportMd = $('#editorExportMd');
  const editorExportDocx = $('#editorExportDocx');
  const editorExportHtml = $('#editorExportHtml');

  if (editorExportTxt) {
    editorExportTxt.addEventListener('click', () => {
      const text = editorText.value;
      if (!text) {
        showError('Editor vazio. Escreva ou cole texto primeiro.');
        return;
      }
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
      saveAs(blob, 'editor_export.txt');
      showSuccess('TXT exportado!');
    });
  }

  if (editorExportMd) {
    editorExportMd.addEventListener('click', () => {
      const text = editorText.value;
      if (!text) {
        showError('Editor vazio. Escreva ou cole texto primeiro.');
        return;
      }
      const markdown = MarkdownConverter.convert(text);
      const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
      saveAs(blob, 'editor_export.md');
      showSuccess('Markdown exportado!');
    });
  }

  if (editorExportDocx) {
    editorExportDocx.addEventListener('click', async () => {
      const text = editorText.value;
      if (!text) {
        showError('Editor vazio. Escreva ou cole texto primeiro.');
        return;
      }
      try {
        await exportToDocx(text, 'editor_export.docx');
        showSuccess('DOCX exportado!');
      } catch (err) {
        console.error(err);
        showError('Falha ao exportar DOCX: ' + err.message);
      }
    });
  }

  if (editorExportHtml) {
    editorExportHtml.addEventListener('click', () => {
      const text = editorText.value;
      if (!text) {
        showError('Editor vazio. Escreva ou cole texto primeiro.');
        return;
      }
      const html = HtmlConverter.convert(text);
      const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
      saveAs(blob, 'editor_export.html');
      showSuccess('HTML exportado!');
    });
  }

  console.log('[Main v4.1] ✓ Funcionalidades Professional carregadas');
  console.log('[Main v4.1] ✓ Análise de documentos jurídicos: ' + (modules.legalAnalyzer ? 'ATIVA' : 'DESABILITADA'));
  console.log('[Main v4.1] ✓ Organização de autos: ' + (modules.processOrganizer ? 'DISPONÍVEL' : 'DESABILITADA'));
  console.log('[Main v4.1] ✓ Processamento em lote: ' + (modules.batchProcessor ? 'DISPONÍVEL' : 'DESABILITADO'));

})();
