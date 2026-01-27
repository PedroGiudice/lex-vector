/**
 * TanStack Query hooks for Tauri commands
 * Provides caching, loading states, and automatic refetch
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTauri } from '@/hooks/useTauri';
import type { ProcessFolder, PdfFile } from '@/types/tauri';

// Query keys for cache management
export const tauriQueryKeys = {
  all: ['tauri'] as const,
  processFolders: (rootPath: string) => [...tauriQueryKeys.all, 'folders', rootPath] as const,
  pdfFiles: (folderPath: string) => [...tauriQueryKeys.all, 'pdfs', folderPath] as const,
  fileHash: (filePath: string) => [...tauriQueryKeys.all, 'hash', filePath] as const,
  cachedResult: (fileHash: string) => [...tauriQueryKeys.all, 'cache', fileHash] as const,
};

/**
 * Hook for listing process folders with caching
 */
export function useProcessFolders(rootPath: string | null) {
  const { listProcessFolders, isAvailable } = useTauri();

  return useQuery<ProcessFolder[], Error>({
    queryKey: tauriQueryKeys.processFolders(rootPath ?? ''),
    queryFn: () => listProcessFolders(rootPath!),
    enabled: isAvailable && !!rootPath,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes
  });
}

/**
 * Hook for listing PDF files in a folder
 */
export function usePdfFiles(folderPath: string | null) {
  const { listPdfsInFolder, isAvailable } = useTauri();

  return useQuery<PdfFile[], Error>({
    queryKey: tauriQueryKeys.pdfFiles(folderPath ?? ''),
    queryFn: () => listPdfsInFolder(folderPath!),
    enabled: isAvailable && !!folderPath,
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
}

/**
 * Hook for calculating file hash
 */
export function useFileHash(filePath: string | null) {
  const { hashFile, isAvailable } = useTauri();

  return useQuery<string, Error>({
    queryKey: tauriQueryKeys.fileHash(filePath ?? ''),
    queryFn: () => hashFile(filePath!),
    enabled: isAvailable && !!filePath,
    staleTime: Infinity, // Hash doesn't change for same file
    gcTime: 1000 * 60 * 60, // 1 hour
  });
}

/**
 * Hook for getting cached API result
 */
export function useCachedResult(fileHash: string | null) {
  const { getCachedResult, isAvailable } = useTauri();

  return useQuery<string | null, Error>({
    queryKey: tauriQueryKeys.cachedResult(fileHash ?? ''),
    queryFn: () => getCachedResult(fileHash!),
    enabled: isAvailable && !!fileHash,
    staleTime: Infinity, // Cache is permanent
    gcTime: 1000 * 60 * 60, // 1 hour
  });
}

/**
 * Hook for saving cached result (mutation)
 */
export function useSaveCachedResult() {
  const queryClient = useQueryClient();
  const { saveCachedResult, isAvailable } = useTauri();

  return useMutation({
    mutationFn: async (params: {
      fileHash: string;
      filePath: string;
      apiResponse: string;
      backendUrl: string;
    }) => {
      if (!isAvailable) return;
      await saveCachedResult(
        params.fileHash,
        params.filePath,
        params.apiResponse,
        params.backendUrl
      );
    },
    onSuccess: (_, variables) => {
      // Update cache query after saving
      queryClient.setQueryData(
        tauriQueryKeys.cachedResult(variables.fileHash),
        variables.apiResponse
      );
    },
  });
}

/**
 * Hook for initializing cache (one-time)
 */
export function useInitCache() {
  const { initCache, isAvailable } = useTauri();

  return useMutation({
    mutationFn: async () => {
      if (!isAvailable) return;
      await initCache();
    },
  });
}

/**
 * Combined hook for common Tauri query operations
 */
export function useTauriQueries() {
  const queryClient = useQueryClient();
  const { isAvailable } = useTauri();

  const invalidateFolders = (rootPath: string) => {
    queryClient.invalidateQueries({ queryKey: tauriQueryKeys.processFolders(rootPath) });
  };

  const invalidatePdfs = (folderPath: string) => {
    queryClient.invalidateQueries({ queryKey: tauriQueryKeys.pdfFiles(folderPath) });
  };

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: tauriQueryKeys.all });
  };

  return {
    isAvailable,
    invalidateFolders,
    invalidatePdfs,
    invalidateAll,
  };
}
