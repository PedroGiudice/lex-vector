import React, { useState, useEffect } from 'react';
import { Check, X } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAnnotations } from '@/hooks/useAnnotations';
import { useDocumentStore } from '@/store/documentStore';
import type { TextSelection as TextSelectionType } from '@/types';

interface TextSelectionPopupProps {
  selection: TextSelectionType;
  onClose: () => void;
}

export function TextSelectionPopup({ selection, onClose }: TextSelectionPopupProps) {
  const [fieldName, setFieldName] = useState('');
  const [error, setError] = useState('');
  const [position, setPosition] = useState({ top: 0, left: 0 });

  const { validateFieldName, addAnnotation } = useAnnotations();
  const setSelectedText = useDocumentStore(state => state.setSelectedText);

  useEffect(() => {
    // Position the popup near the selection
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0) {
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();

      setPosition({
        top: rect.bottom + window.scrollY + 10,
        left: rect.left + window.scrollX,
      });
    }
  }, []);

  const handleCreate = () => {
    const validation = validateFieldName(fieldName);

    if (!validation.valid) {
      setError(validation.error || 'Invalid field name');
      return;
    }

    addAnnotation({
      fieldName,
      text: selection.text,
      start: selection.start,
      end: selection.end,
      paragraphIndex: selection.paragraphIndex,
    });

    // Clear selection and close popup
    window.getSelection()?.removeAllRanges();
    setSelectedText(null);
    onClose();
  };

  const handleCancel = () => {
    window.getSelection()?.removeAllRanges();
    setSelectedText(null);
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCreate();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  return (
    <div
      className="fixed z-40 bg-gh-bg-secondary border border-gh-border-default rounded-lg shadow-xl p-4 min-w-[320px]"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
      }}
    >
      <div className="mb-3">
        <p className="text-xs text-gh-text-secondary mb-2">Selected text:</p>
        <p className="text-sm text-gh-text-primary bg-gh-bg-tertiary px-3 py-2 rounded border border-gh-border-default max-h-20 overflow-y-auto">
          {selection.text}
        </p>
      </div>

      <Input
        autoFocus
        placeholder="field_name"
        value={fieldName}
        onChange={e => {
          setFieldName(e.target.value);
          setError('');
        }}
        onKeyDown={handleKeyDown}
        error={error}
        helperText="Use snake_case (e.g., nome_autor, data_assinatura)"
      />

      <div className="flex items-center gap-2 mt-4">
        <Button
          variant="primary"
          size="sm"
          onClick={handleCreate}
          className="flex-1"
        >
          <Check className="w-4 h-4 mr-2" />
          Create Field
        </Button>
        <Button variant="ghost" size="sm" onClick={handleCancel}>
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
