import React, { useState, useEffect } from 'react';
import { Check, X, Type } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAnnotations } from '@/hooks/useAnnotations';
import { useDocumentStore } from '@/store/documentStore';

export function FieldEditorPanel() {
  const selectedText = useDocumentStore((state) => state.selectedText);
  const setSelectedText = useDocumentStore((state) => state.setSelectedText);
  const { validateFieldName, addAnnotation } = useAnnotations();

  const [fieldName, setFieldName] = useState('');
  const [error, setError] = useState('');

  // Reset quando selecao muda
  useEffect(() => {
    setFieldName('');
    setError('');
  }, [selectedText]);

  const handleCreate = () => {
    if (!selectedText) return;

    const validation = validateFieldName(fieldName);
    if (!validation.valid) {
      setError(validation.error || 'Invalid field name');
      return;
    }

    addAnnotation({
      fieldName,
      text: selectedText.text,
      start: selectedText.start,
      end: selectedText.end,
      paragraphIndex: selectedText.paragraphIndex,
    });

    window.getSelection()?.removeAllRanges();
    setSelectedText(null);
  };

  const handleCancel = () => {
    window.getSelection()?.removeAllRanges();
    setSelectedText(null);
  };

  // Estado vazio - nenhuma selecao
  if (!selectedText) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center">
        <Type className="w-12 h-12 text-[#a1a1aa] mb-4 opacity-50" />
        <h3 className="text-sm font-medium text-[#e4e4e7] mb-2">Nenhum texto selecionado</h3>
        <p className="text-xs text-[#a1a1aa]">Selecione texto no documento para criar um campo</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-[#3f3f46]">
        <h2 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wide">
          Criar Campo
        </h2>
      </div>

      <div className="p-4 flex-1">
        {/* Texto selecionado */}
        <div className="mb-4">
          <label className="text-xs text-[#a1a1aa] mb-2 block">Texto selecionado:</label>
          <div className="bg-[#1e1e2e] border border-[#3f3f46] rounded-lg p-3 max-h-32 overflow-y-auto">
            <p className="text-sm text-[#e4e4e7]">&quot;{selectedText.text}&quot;</p>
          </div>
        </div>

        {/* Campo de nome */}
        <Input
          autoFocus
          label="Nome do campo"
          placeholder="ex: nome_autor"
          value={fieldName}
          onChange={(e) => {
            setFieldName(e.target.value);
            setError('');
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleCreate();
            if (e.key === 'Escape') handleCancel();
          }}
          error={error}
          helperText="Use snake_case (ex: data_assinatura)"
        />
      </div>

      {/* Botoes de acao */}
      <div className="p-4 border-t border-[#3f3f46] flex gap-2">
        <Button
          variant="primary"
          className="flex-1"
          onClick={handleCreate}
          disabled={!fieldName.trim()}
        >
          <Check className="w-4 h-4 mr-2" />
          Criar Campo
        </Button>
        <Button variant="ghost" onClick={handleCancel}>
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
