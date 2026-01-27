# Doc Assembler UX Improvements & Core Assemble Feature

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix text selection UX issues, improve field annotation visuals, and implement the core "Assemble" functionality that generates documents from templates.

**Architecture:** Frontend improvements to TipTap editor configuration and styling, plus new UI components for the document assembly workflow. Backend endpoints already exist (`/api/v1/assemble`).

**Tech Stack:** React, TipTap, TypeScript, Zustand, FastAPI (existing)

---

## Task 1: Fix Text Selection Difficulty

**Problem:** With `editable: false`, TipTap makes text selection difficult (picks up letter-by-letter instead of smooth selection).

**Files:**
- Modify: `frontend/src/components/document/TipTapDocumentViewer.tsx:104-120`

**Step 1: Write a test comment documenting expected behavior**

Add a comment block documenting the fix:

```typescript
// TipTap selection fix: editable:true allows smooth selection
// We use contentEditable CSS to prevent actual editing while keeping selection UX
```

**Step 2: Change TipTap configuration**

Replace `editable: false` with `editable: true` and add CSS to prevent editing:

```typescript
const editor = useEditor({
  extensions: [Document, Paragraph, Text, FieldAnnotationMark],
  content: paragraphsToTipTapContent(paragraphs),
  editable: true, // Enable for better selection UX
  editorProps: {
    attributes: {
      class: 'prose prose-invert prose-sm max-w-none focus:outline-none select-text',
      // Prevent actual text input while allowing selection
      contenteditable: 'true',
    },
    handleKeyDown: () => true, // Block all keyboard input
    handlePaste: () => true,   // Block paste
    handleDrop: () => true,    // Block drag-drop
  },
  // ... rest of config
});
```

**Step 3: Verify selection works smoothly**

Run: `cd legal-workbench/frontend && bun run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/components/document/TipTapDocumentViewer.tsx
git commit -m "fix(lw-doc-assembler): Enable smooth text selection in TipTap"
```

---

## Task 2: Make Field Annotations More Visible (Highlight Style)

**Problem:** Current style uses subtle `border-bottom` which is hard to see. Need bold highlight/grifo style.

**Files:**
- Modify: `frontend/src/extensions/FieldAnnotationMark.ts:36-44`
- Modify: `frontend/src/index.css` (add selection style)

**Step 1: Update FieldAnnotationMark renderHTML**

Change from subtle border to bold highlight:

```typescript
addAttributes() {
  return {
    fieldName: {
      default: null,
      parseHTML: (element) => element.getAttribute('data-field-name'),
      renderHTML: (attributes) => ({
        'data-field-name': attributes.fieldName,
      }),
    },
    color: {
      default: '#3b82f6',
      parseHTML: (element) => element.getAttribute('data-color'),
      renderHTML: (attributes) => ({
        'data-color': attributes.color,
        // Bold highlight style - impossible to miss
        style: `
          background-color: ${attributes.color};
          color: white;
          padding: 2px 4px;
          border-radius: 3px;
          font-weight: 500;
          box-shadow: 0 1px 2px rgba(0,0,0,0.3);
        `.replace(/\s+/g, ' ').trim(),
      }),
    },
  };
},
```

**Step 2: Add CSS for text selection highlight**

Add to `frontend/src/index.css`:

```css
/* TipTap text selection - bright yellow highlight */
.ProseMirror ::selection {
  background-color: #fef08a !important; /* yellow-200 */
  color: #1a1a1a !important;
}

.ProseMirror::-moz-selection {
  background-color: #fef08a !important;
  color: #1a1a1a !important;
}

/* Field annotation hover effect */
.field-annotation:hover {
  filter: brightness(1.1);
  cursor: pointer;
}
```

**Step 3: Verify visually**

Run: `bun run build`
Deploy and verify fields are now bold colored boxes, not subtle underlines.

**Step 4: Commit**

```bash
git add frontend/src/extensions/FieldAnnotationMark.ts frontend/src/index.css
git commit -m "style(lw-doc-assembler): Bold highlight style for field annotations"
```

---

## Task 3: Create AssemblePanel Component

**Problem:** No UI exists to use templates and generate documents.

**Files:**
- Create: `frontend/src/components/document/AssemblePanel.tsx`
- Modify: `frontend/src/types/index.ts` (add types)

**Step 1: Add types for assembly**

Add to `frontend/src/types/index.ts`:

```typescript
export interface AssembleRequest {
  template_path: string;
  data: Record<string, string>;
  output_filename?: string;
  auto_normalize?: boolean;
}

export interface AssembleResponse {
  success: boolean;
  output_path: string;
  download_url: string;
  filename: string;
  message: string;
}

export interface TemplateField {
  name: string;
  value: string;
  category?: string;
}
```

**Step 2: Create AssemblePanel component**

Create `frontend/src/components/document/AssemblePanel.tsx`:

```typescript
import { useState, useEffect } from 'react';
import { FileOutput, Download, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useDocumentStore } from '@/store/documentStore';
import { api } from '@/services/api';
import type { TemplateField } from '@/types';

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
```

**Step 3: Verify build**

Run: `bun run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/components/document/AssemblePanel.tsx frontend/src/types/index.ts
git commit -m "feat(lw-doc-assembler): Add AssemblePanel component for document generation"
```

---

## Task 4: Add Assembly API Method

**Files:**
- Modify: `frontend/src/services/api.ts`

**Step 1: Add assembleDocument method**

Add to `ApiService` class:

```typescript
async assembleDocument(data: {
  template_path: string;
  data: Record<string, string>;
  output_filename?: string;
  auto_normalize?: boolean;
}): Promise<{
  success: boolean;
  output_path: string;
  download_url: string;
  filename: string;
  message: string;
}> {
  // Use main API endpoint, not builder
  const response = await axios.post('/api/doc/api/v1/assemble', data);
  return response.data;
}
```

**Step 2: Verify build**

Run: `bun run build`

**Step 3: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat(lw-doc-assembler): Add assembleDocument API method"
```

---

## Task 5: Integrate AssemblePanel into TemplateList

**Files:**
- Modify: `frontend/src/components/templates/TemplateList.tsx`
- Modify: `frontend/src/components/templates/TemplateCard.tsx`

**Step 1: Add "Use Template" button to TemplateCard**

Modify TemplateCard to accept onUse callback:

```typescript
interface TemplateCardProps {
  template: Template;
  onLoad: () => void;
  onUse?: () => void; // Add this
}

export function TemplateCard({ template, onLoad, onUse }: TemplateCardProps) {
  return (
    <div className="...">
      {/* existing content */}
      <div className="flex gap-2 mt-2">
        <Button size="sm" variant="ghost" onClick={onLoad}>
          Carregar
        </Button>
        {onUse && (
          <Button size="sm" variant="primary" onClick={onUse}>
            Usar
          </Button>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Add state for selected template in TemplateList**

Modify TemplateList to manage assembly mode:

```typescript
const [assembleTemplate, setAssembleTemplate] = useState<Template | null>(null);

// In render:
{assembleTemplate ? (
  <AssemblePanel
    templateId={assembleTemplate.id}
    fields={assembleTemplate.fields || []}
    onClose={() => setAssembleTemplate(null)}
  />
) : (
  // existing template list
)}
```

**Step 3: Commit**

```bash
git add frontend/src/components/templates/TemplateList.tsx frontend/src/components/templates/TemplateCard.tsx
git commit -m "feat(lw-doc-assembler): Integrate AssemblePanel with template list"
```

---

## Task 6: Deploy and Test E2E

**Files:** None (deployment only)

**Step 1: Build**

```bash
cd legal-workbench/frontend
bun run build
```

**Step 2: Sync source to OCI**

```bash
rsync -avz --exclude 'node_modules' --exclude 'dist' \
  legal-workbench/frontend/ \
  opc@137.131.201.119:/home/opc/lex-vector/legal-workbench/frontend/
```

**Step 3: Docker rebuild with CACHEBUST**

```bash
ssh opc@137.131.201.119 "cd /home/opc/lex-vector/legal-workbench && \
  docker compose build --build-arg CACHEBUST=\$(date +%s) frontend-react && \
  docker compose up -d frontend-react"
```

**Step 4: Test E2E**

1. Upload a DOCX document
2. Create field annotations (should be bold colored highlights)
3. Save as template
4. Click "Usar" on the template
5. Fill in field values
6. Click "Gerar Documento"
7. Download the generated document
8. Open and verify fields were replaced

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat(lw-doc-assembler): Complete UX improvements and Assemble feature"
git push origin feat/tiptap-integration
```

---

## Summary

| Task | Description | Estimated Time |
|------|-------------|----------------|
| 1 | Fix text selection UX | 15 min |
| 2 | Bold highlight style | 20 min |
| 3 | AssemblePanel component | 30 min |
| 4 | Assembly API method | 10 min |
| 5 | Integrate with templates | 20 min |
| 6 | Deploy and test | 30 min |
| **Total** | | **~2 hours** |

---

## Dependencies

- Backend `/api/v1/assemble` endpoint already exists
- Backend `/api/v1/builder/templates` endpoint already exists
- TipTap packages already installed

## Risks

| Risk | Mitigation |
|------|------------|
| TipTap `editable: true` may cause issues | Use keyboard/paste/drop handlers to block input |
| Download URL routing | Use `/api/doc${downloadUrl}` prefix for Traefik |
| Template fields not loaded | Ensure `getTemplateDetails` returns `fields` array |
