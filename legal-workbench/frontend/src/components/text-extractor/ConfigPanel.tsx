import React from 'react';
import { useTextExtractorStore } from '@/store/textExtractorStore';
import { MarginPreview } from './MarginPreview';
import { IgnoreTermsList } from './IgnoreTermsList';
import { Play, Loader2 } from 'lucide-react';

export function ConfigPanel() {
  const { engine, setEngine, cleanupMode, setCleanupMode, status, file, submitJob } =
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

        <div className="te-divider" />

        {/* Cleanup Mode Selection */}
        <div className="te-section">
          <div className="te-subsection-header">
            <span className="te-command">&gt; CLEANUP_MODE</span>
          </div>
          <div className="te-engine-options">
            <label className="te-radio-label">
              <input
                type="radio"
                name="cleanup"
                value="script"
                checked={cleanupMode === 'script'}
                onChange={() => setCleanupMode('script')}
                disabled={isDisabled}
                className="te-radio"
              />
              <span className="te-radio-text">Script (fast)</span>
            </label>
            <label className="te-radio-label">
              <input
                type="radio"
                name="cleanup"
                value="gemini"
                checked={cleanupMode === 'gemini'}
                onChange={() => setCleanupMode('gemini')}
                disabled={isDisabled}
                className="te-radio"
              />
              <span className="te-radio-text">Gemini Polish (~12 min)</span>
            </label>
          </div>
        </div>

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
