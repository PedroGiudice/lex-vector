import { useState, useEffect } from 'react';
import { FileOutput, Download, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useDocumentStore } from '@/store/documentStore';
import { api } from '@/services/api';

interface AssemblePanelProps {
  templateId: string;
  fields: string[];
  onClose: () => void;
}

export function AssemblePanel({ templateId, fields, onClose }: AssemblePanelProps) {
  const addToast = useDocumentStore((state) => state.addToast);
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  // Initialize field values
  useEffect(() => {
    const initial: Record<string, string> = {};
    fields.forEach((f) => (initial[f] = ''));
    setFieldValues(initial);
  }, [fields]);

  const handleFieldChange = (fieldName: string, value: string) => {
    setFieldValues((prev) => ({ ...prev, [fieldName]: value }));
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const response = await api.assembleDocument({
        template_path: `/templates/builder/${templateId}.docx`,
        data: fieldValues,
        auto_normalize: true,
      });

      setDownloadUrl(response.download_url);
      addToast('Documento gerado com sucesso!', 'success');
    } catch (error) {
      console.error('Assembly failed:', error);
      addToast('Falha ao gerar documento', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const allFieldsFilled = Object.values(fieldValues).every((v) => v.trim() !== '');

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border-default">
        <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wide flex items-center gap-2">
          <FileOutput className="w-4 h-4" />
          Montar Documento
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {fields.map((field) => (
          <Input
            key={field}
            label={field.replace(/_/g, ' ')}
            placeholder={`Digite ${field.replace(/_/g, ' ')}`}
            value={fieldValues[field] || ''}
            onChange={(e) => handleFieldChange(field, e.target.value)}
          />
        ))}
      </div>

      <div className="p-4 border-t border-border-default space-y-2">
        {downloadUrl ? (
          <a
            href={`/api/doc${downloadUrl}`}
            download
            className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Baixar Documento
          </a>
        ) : (
          <Button
            variant="primary"
            className="w-full"
            onClick={handleGenerate}
            disabled={!allFieldsFilled || isGenerating}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Gerando...
              </>
            ) : (
              <>
                <FileOutput className="w-4 h-4 mr-2" />
                Gerar Documento
              </>
            )}
          </Button>
        )}
        <Button variant="ghost" className="w-full" onClick={onClose}>
          Voltar
        </Button>
      </div>
    </div>
  );
}
