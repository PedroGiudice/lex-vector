import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';
import { useState, useCallback } from 'react';

export interface ProcessFolder {
  path: string;
  name: string;
  pdf_count: number;
  total_size_bytes: number;
  last_modified: string;
}

export interface PdfFile {
  path: string;
  name: string;
  size_bytes: number;
  last_modified: string;
  extracted_text: string | null;
  extraction_status: 'Pending' | 'InProgress' | 'Completed' | { Failed: string };
}

export function useTauri() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectFolder = useCallback(async (): Promise<string | null> => {
    const selected = await open({
      directory: true,
      multiple: false,
      title: 'Selecione a pasta de processos',
    });
    return selected as string | null;
  }, []);

  const listProcessFolders = useCallback(async (rootPath: string): Promise<ProcessFolder[]> => {
    setLoading(true);
    setError(null);
    try {
      return await invoke<ProcessFolder[]>('list_process_folders', { rootPath });
    } catch (e) {
      setError(String(e));
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const listPdfs = useCallback(async (folderPath: string): Promise<PdfFile[]> => {
    setLoading(true);
    setError(null);
    try {
      return await invoke<PdfFile[]>('list_pdfs_in_folder', { folderPath });
    } catch (e) {
      setError(String(e));
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const getCachedExtraction = useCallback(async (pdfPath: string): Promise<string | null> => {
    return await invoke<string | null>('get_cached_extraction', { pdfPath });
  }, []);

  const saveExtraction = useCallback(async (pdfPath: string, text: string): Promise<void> => {
    await invoke('save_extraction', { pdfPath, text });
  }, []);

  return {
    loading,
    error,
    selectFolder,
    listProcessFolders,
    listPdfs,
    getCachedExtraction,
    saveExtraction,
  };
}
