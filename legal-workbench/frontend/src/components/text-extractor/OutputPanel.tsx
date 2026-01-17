import React, { useState, useCallback } from 'react';
import { useTextExtractorStore } from '@/store/textExtractorStore';
import {
  Copy,
  Download,
  RefreshCw,
  ChevronDown,
  Check,
  User,
  FileText,
  Calendar,
  DollarSign,
  Clock,
  Hash,
  Zap,
} from 'lucide-react';

type DownloadFormat = 'txt' | 'md' | 'json';

export function OutputPanel() {
  const { result, status, reset, progress } = useTextExtractorStore();
  const [copied, setCopied] = useState(false);
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);

  const handleCopy = useCallback(async () => {
    if (result?.text) {
      try {
        await navigator.clipboard.writeText(result.text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('Failed to copy text:', err);
      }
    }
  }, [result]);

  const handleDownload = useCallback(
    (format: DownloadFormat) => {
      if (!result) return;

      let content: string;
      let mimeType: string;
      let extension: string;

      switch (format) {
        case 'txt':
          content = result.text;
          mimeType = 'text/plain';
          extension = 'txt';
          break;
        case 'md':
          content = `# Extracted Text\n\n${result.text}\n\n---\n\n## Metadata\n\n- Pages: ${result.pages_processed}\n- Time: ${result.execution_time_seconds}s\n- Engine: ${result.engine_used}\n- Characters: ${result.text.length}\n`;
          mimeType = 'text/markdown';
          extension = 'md';
          break;
        case 'json':
          content = JSON.stringify(result, null, 2);
          mimeType = 'application/json';
          extension = 'json';
          break;
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `extracted-text.${extension}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setShowDownloadMenu(false);
    },
    [result]
  );

  const getEntityIcon = (type: string) => {
    switch (type) {
      case 'pessoa':
        return <User size={14} />;
      case 'cpf':
      case 'cnpj':
        return <FileText size={14} />;
      case 'data':
        return <Calendar size={14} />;
      case 'valor':
        return <DollarSign size={14} />;
      default:
        return <Hash size={14} />;
    }
  };

  const formatEntityType = (type: string): string => {
    const types: Record<string, string> = {
      pessoa: 'PESSOAS',
      cpf: 'CPF',
      cnpj: 'CNPJ',
      data: 'DATAS',
      valor: 'VALORES',
      email: 'E-MAILS',
      telefone: 'TELEFONES',
    };
    return types[type] || type.toUpperCase();
  };

  const isProcessing = status === 'processing';
  const hasResult = status === 'success' && result;

  return (
    <div className="te-panel te-panel--output">
      <div className="te-panel-header">
        <span className="te-panel-label">[OUTPUT]</span>
        <span className="te-panel-step">#STEP-3</span>
      </div>
      <div className="te-panel-content">
        {/* Processing State */}
        {isProcessing && (
          <div className="te-processing">
            <div className="te-processing-icon">
              <Zap size={32} className="te-icon-accent te-pulse" />
            </div>
            <div className="te-processing-text">
              <span className="te-command">&gt; PROCESSING...</span>
              <span className="te-progress-text">{progress}% complete</span>
            </div>
            <div className="te-progress-bar">
              <div className="te-progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}

        {/* Idle State */}
        {status === 'idle' && (
          <div className="te-empty-state">
            <span className="te-comment">// Awaiting extraction job...</span>
            <span className="te-hint">Upload a PDF to get started</span>
          </div>
        )}

        {/* Configuring State */}
        {(status === 'configuring' || status === 'preflight') && (
          <div className="te-empty-state">
            <span className="te-comment">// Configure and click EXTRACT</span>
            <span className="te-hint">Results will appear here</span>
          </div>
        )}

        {/* Error State */}
        {status === 'error' && (
          <div className="te-error-state">
            <span className="te-error-text">Extraction failed</span>
            <button type="button" onClick={reset} className="te-btn-retry">
              <RefreshCw size={14} />
              <span>Try Again</span>
            </button>
          </div>
        )}

        {/* Success State with Results */}
        {hasResult && (
          <>
            {/* Header with actions */}
            <div className="te-output-header">
              <span className="te-command">&gt; EXTRACTED_TEXT</span>
              <div className="te-output-actions">
                <button
                  type="button"
                  onClick={handleCopy}
                  className="te-btn-action"
                  aria-label="Copy to clipboard"
                >
                  {copied ? <Check size={14} /> : <Copy size={14} />}
                  <span>{copied ? 'Copied!' : 'COPY'}</span>
                </button>

                <div className="te-dropdown">
                  <button
                    type="button"
                    onClick={() => setShowDownloadMenu(!showDownloadMenu)}
                    className="te-btn-action"
                    aria-expanded={showDownloadMenu}
                    aria-haspopup="listbox"
                  >
                    <Download size={14} />
                    <span>DOWNLOAD</span>
                    <ChevronDown size={12} />
                  </button>
                  {showDownloadMenu && (
                    <div className="te-dropdown-menu" role="listbox">
                      <button
                        type="button"
                        onClick={() => handleDownload('txt')}
                        className="te-dropdown-item"
                        role="option"
                      >
                        .txt (Plain text)
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDownload('md')}
                        className="te-dropdown-item"
                        role="option"
                      >
                        .md (Markdown)
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDownload('json')}
                        className="te-dropdown-item"
                        role="option"
                      >
                        .json (Full data)
                      </button>
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  onClick={reset}
                  className="te-btn-action"
                  aria-label="Reset and start over"
                >
                  <RefreshCw size={14} />
                </button>
              </div>
            </div>

            {/* Extracted Text */}
            <div className="te-text-output">
              <pre className="te-text-content">{result.text}</pre>
            </div>

            {/* Bottom Section: Entities + Metadata */}
            <div className="te-output-footer">
              {/* Entities */}
              {result.entities && result.entities.length > 0 && (
                <div className="te-entities">
                  <span className="te-command">&gt; ENTITIES</span>
                  <div className="te-entities-list">
                    {result.entities.map((entity, index) => (
                      <div key={`${entity.type}-${index}`} className="te-entity-group">
                        <div className="te-entity-header">
                          {getEntityIcon(entity.type)}
                          <span>
                            {formatEntityType(entity.type)} ({entity.count})
                          </span>
                        </div>
                        <div className="te-entity-value">{entity.value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="te-metadata">
                <span className="te-command">&gt; METADATA</span>
                <div className="te-metadata-list">
                  <div className="te-metadata-item">
                    <FileText size={12} />
                    <span>Pages: {result.pages_processed}</span>
                  </div>
                  <div className="te-metadata-item">
                    <Clock size={12} />
                    <span>Time: {result.execution_time_seconds.toFixed(1)}s</span>
                  </div>
                  <div className="te-metadata-item">
                    <Zap size={12} />
                    <span>Engine: {result.engine_used}</span>
                  </div>
                  <div className="te-metadata-item">
                    <Hash size={12} />
                    <span>Chars: {result.text.length.toLocaleString()}</span>
                  </div>
                  {result.metadata?.extraction_mode && (
                    <div className="te-metadata-item">
                      <span>Mode: {result.metadata.extraction_mode}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default OutputPanel;
