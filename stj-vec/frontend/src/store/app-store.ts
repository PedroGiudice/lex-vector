import { create } from 'zustand';
import type { SearchFilters } from '@/api/types.ts';

interface AppState {
  query: string;
  submittedQuery: string;
  filters: SearchFilters;
  selectedChunkId: string | null;
  selectedDocId: string | null;
  limit: number;
  setQuery: (q: string) => void;
  submitQuery: () => void;
  setFilter: (key: keyof SearchFilters, value: string | undefined) => void;
  clearFilters: () => void;
  selectResult: (chunkId: string, docId: string) => void;
  clearSelection: () => void;
  setLimit: (limit: number) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  query: '',
  submittedQuery: '',
  filters: {},
  selectedChunkId: null,
  selectedDocId: null,
  limit: 20,

  setQuery: (q) => set({ query: q }),

  submitQuery: () => {
    const { query } = get();
    if (query.trim().length > 2) {
      set({
        submittedQuery: query.trim(),
        selectedChunkId: null,
        selectedDocId: null,
      });
    }
  },

  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value || undefined },
    })),

  clearFilters: () => set({ filters: {} }),

  selectResult: (chunkId, docId) =>
    set({ selectedChunkId: chunkId, selectedDocId: docId }),

  clearSelection: () =>
    set({ selectedChunkId: null, selectedDocId: null }),

  setLimit: (limit) => set({ limit }),
}));
