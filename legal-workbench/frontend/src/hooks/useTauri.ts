/**
 * Hook for invoking Tauri commands from React components
 */

import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';
import { isTauri } from '@/lib/tauri';
import type { ProcessFolder, PdfFile } from '@/types/tauri';

export interface UseTauriReturn {
  // Detection
  isAvailable: boolean;

  // Filesystem commands
  selectFolder: () => Promise<string | null>;
  listProcessFolders: (rootPath: string) => Promise<ProcessFolder[]>;
  listPdfsInFolder: (folderPath: string) => Promise<PdfFile[]>;

  // Cache commands
  initCache: () => Promise<void>;
  getCachedResult: (fileHash: string) => Promise<string | null>;
  saveCachedResult: (
    fileHash: string,
    filePath: string,
    apiResponse: string,
    backendUrl: string
  ) => Promise<void>;
  hashFile: (filePath: string) => Promise<string>;
}

export function useTauri(): UseTauriReturn {
  const isAvailable = isTauri();

  /**
   * Open native folder picker dialog
   */
  const selectFolder = async (): Promise<string | null> => {
    if (!isAvailable) return null;

    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: 'Selecione a pasta de processos',
      });

      return typeof selected === 'string' ? selected : null;
    } catch (error) {
      console.error('Folder picker error:', error);
      return null;
    }
  };

  /**
   * List process folders in a directory
   */
  const listProcessFolders = async (rootPath: string): Promise<ProcessFolder[]> => {
    if (!isAvailable) return [];

    try {
      return await invoke<ProcessFolder[]>('list_process_folders', { rootPath });
    } catch (error) {
      console.error('list_process_folders error:', error);
      throw error;
    }
  };

  /**
   * List PDF files in a folder (recursive)
   */
  const listPdfsInFolder = async (folderPath: string): Promise<PdfFile[]> => {
    if (!isAvailable) return [];

    try {
      return await invoke<PdfFile[]>('list_pdfs_in_folder', { folderPath });
    } catch (error) {
      console.error('list_pdfs_in_folder error:', error);
      throw error;
    }
  };

  /**
   * Initialize the SQLite cache database
   */
  const initCache = async (): Promise<void> => {
    if (!isAvailable) return;

    try {
      await invoke('init_cache');
    } catch (error) {
      console.error('init_cache error:', error);
      throw error;
    }
  };

  /**
   * Get cached API result by file hash
   */
  const getCachedResult = async (fileHash: string): Promise<string | null> => {
    if (!isAvailable) return null;

    try {
      return await invoke<string | null>('get_cached_result', { fileHash });
    } catch (error) {
      console.error('get_cached_result error:', error);
      throw error;
    }
  };

  /**
   * Save API result to cache
   */
  const saveCachedResult = async (
    fileHash: string,
    filePath: string,
    apiResponse: string,
    backendUrl: string
  ): Promise<void> => {
    if (!isAvailable) return;

    try {
      await invoke('save_cached_result', {
        fileHash,
        filePath,
        apiResponse,
        backendUrl,
      });
    } catch (error) {
      console.error('save_cached_result error:', error);
      throw error;
    }
  };

  /**
   * Calculate SHA256 hash of a file
   */
  const hashFile = async (filePath: string): Promise<string> => {
    if (!isAvailable) return '';

    try {
      return await invoke<string>('hash_file', { filePath });
    } catch (error) {
      console.error('hash_file error:', error);
      throw error;
    }
  };

  return {
    isAvailable,
    selectFolder,
    listProcessFolders,
    listPdfsInFolder,
    initCache,
    getCachedResult,
    saveCachedResult,
    hashFile,
  };
}
