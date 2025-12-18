import { useCallback } from 'react';
import { useDocumentStore } from '@/store/documentStore';

export function useDocumentUpload() {
  const uploadDocument = useDocumentStore(state => state.uploadDocument);
  const isUploading = useDocumentStore(state => state.isUploading);
  const uploadProgress = useDocumentStore(state => state.uploadProgress);
  const clearDocument = useDocumentStore(state => state.clearDocument);

  const handleUpload = useCallback(
    async (file: File) => {
      // Validate file type
      if (!file.name.endsWith('.docx')) {
        throw new Error('Only .docx files are supported');
      }

      // Validate file size (max 10MB)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        throw new Error('File size exceeds 10MB limit');
      }

      await uploadDocument(file);
    },
    [uploadDocument]
  );

  return {
    uploadDocument: handleUpload,
    isUploading,
    uploadProgress,
    clearDocument,
  };
}
