import React from 'react';
import { useTextExtractorStore } from '@/store/textExtractorStore';
import { MarginPreview } from './MarginPreview';
import { IgnoreTermsList } from './IgnoreTermsList';
import { Play, Loader2 } from 'lucide-react';

export function ConfigPanel() {
  const { engine, setEngine, gpuMode, setGpuMode, status, file, submitJob } =
    useTextExtractorStore();

  const isDisabled = status === 'processing';
  const canSubmit = file && (status === 'configuring' || status === 'preflight');

  const handleSubmit = () => {
    if (canSubmit) {
      submitJob();
    }
  };

  return (
    <div className="te-panel">
      <div className="te-panel-header">
        <span className="te-panel-label">[CONFIG]</span>
        <span className="te-panel-step">#STEP-2</span>
      </div>
      <div className="te-panel-content">
        {/* Engine Selection */}
        <div className="te-section">
          <div className="te-subsection-header">
            <span className="te-command">&gt; ENGINE_SELECT</span>
          </div>
          <div className="te-engine-options">
            <label className="te-radio-label">
              <input
                type="radio"
                name="engine"
                value="marker"
                checked={engine === 'marker'}
                onChange={() => setEngine('marker')}
                disabled={isDisabled}
                className="te-radio"
              />
              <span className="te-radio-text">Marker (recommended)</span>
            </label>
            <label className="te-radio-label">
              <input
                type="radio"
                name="engine"
                value="pdfplumber"
                checked={engine === 'pdfplumber'}
                onChange={() => setEngine('pdfplumber')}
                disabled={isDisabled}
                className="te-radio"
              />
              <span className="te-radio-text">PDFPlumber (fallback)</span>
            </label>
          </div>
          <label className="te-checkbox-label te-checkbox-indent">
            <input type="checkbox" checked={true} disabled={true} className="te-checkbox" />
            <span>Auto-detect OCR</span>
          </label>
        </div>

        {/* GPU Mode Selection - only show when engine is marker */}
        {engine === 'marker' && (
          <>
            <div className="te-divider" />
            <div className="te-section">
              <div className="te-subsection-header">
                <span className="te-command">&gt; GPU_MODE</span>
              </div>
              <div className="te-gpu-options">
                <label className="te-radio-label">
                  <input
                    type="radio"
                    name="gpuMode"
                    value="auto"
                    checked={gpuMode === 'auto'}
                    onChange={() => setGpuMode('auto')}
                    disabled={isDisabled}
                    className="te-radio"
                  />
                  <span className="te-radio-text">Automatico</span>
                </label>
                <p className="te-radio-description">
                  Seleciona o melhor modo baseado no tamanho do PDF
                </p>

                <label className="te-radio-label">
                  <input
                    type="radio"
                    name="gpuMode"
                    value="economy"
                    checked={gpuMode === 'economy'}
                    onChange={() => setGpuMode('economy')}
                    disabled={isDisabled}
                    className="te-radio"
                  />
                  <span className="te-radio-text">Economia</span>
                </label>
                <p className="te-radio-description">
                  Multi-T4 paralelo - mais barato para PDFs grandes
                </p>

                <label className="te-radio-label">
                  <input
                    type="radio"
                    name="gpuMode"
                    value="performance"
                    checked={gpuMode === 'performance'}
                    onChange={() => setGpuMode('performance')}
                    disabled={isDisabled}
                    className="te-radio"
                  />
                  <span className="te-radio-text">Performance</span>
                </label>
                <p className="te-radio-description">
                  A100 dedicada - mais rapido para PDFs pequenos
                </p>
              </div>
            </div>
          </>
        )}

        <div className="te-divider" />

        {/* Margin Preview */}
        <MarginPreview />

        <div className="te-divider" />

        {/* Ignore Terms */}
        <IgnoreTermsList />

        {/* Submit Button */}
        <div className="te-submit-section">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit || isDisabled}
            className="te-btn-submit"
            aria-label="Start extraction"
          >
            {status === 'processing' ? (
              <>
                <Loader2 size={18} className="te-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Play size={18} />
                <span>EXTRACT</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfigPanel;
