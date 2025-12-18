import { create } from 'zustand';
import { stjApi, SearchParams, AcordaoSummary, AcordaoDetail, StatsResponse } from '@/services/stjApi';

interface STJState {
  // Search state
  searchTerm: string;
  results: AcordaoSummary[];
  total: number;
  loading: boolean;
  error: string | null;

  // Filters
  filters: {
    orgao: string;
    dias: number;
    campo: 'ementa' | 'texto_integral';
  };

  // Pagination
  page: number;
  pageSize: number;

  // Selected case
  selectedCase: AcordaoDetail | null;
  loadingCase: boolean;

  // Stats
  stats: StatsResponse | null;

  // Actions
  setSearchTerm: (term: string) => void;
  setFilters: (filters: Partial<STJState['filters']>) => void;
  search: () => Promise<void>;
  loadCase: (id: string) => Promise<void>;
  loadStats: () => Promise<void>;
  setPage: (page: number) => void;
  clearResults: () => void;
}

export const useSTJStore = create<STJState>((set, get) => ({
  searchTerm: '',
  results: [],
  total: 0,
  loading: false,
  error: null,

  filters: {
    orgao: '',
    dias: 365,
    campo: 'ementa',
  },

  page: 0,
  pageSize: 20,

  selectedCase: null,
  loadingCase: false,

  stats: null,

  setSearchTerm: (term) => set({ searchTerm: term }),

  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters },
    page: 0, // Reset pagination on filter change
  })),

  search: async () => {
    const { searchTerm, filters, page, pageSize } = get();
    if (searchTerm.length < 3) {
      set({ error: 'Termo de busca deve ter ao menos 3 caracteres' });
      return;
    }

    set({ loading: true, error: null });

    try {
      const params: SearchParams = {
        termo: searchTerm,
        dias: filters.dias,
        campo: filters.campo,
        limit: pageSize,
        offset: page * pageSize,
      };

      if (filters.orgao) {
        params.orgao = filters.orgao;
      }

      const { data } = await stjApi.search(params);
      set({
        results: data.resultados,
        total: data.total,
        loading: false
      });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erro ao buscar jurisprudência',
        loading: false
      });
    }
  },

  loadCase: async (id) => {
    set({ loadingCase: true });
    try {
      const { data } = await stjApi.getCase(id);
      set({ selectedCase: data, loadingCase: false });
    } catch (err: any) {
      set({ loadingCase: false });
    }
  },

  loadStats: async () => {
    try {
      const { data } = await stjApi.getStats();
      set({ stats: data });
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  },

  setPage: (page) => {
    set({ page });
    get().search();
  },

  clearResults: () => set({
    results: [],
    total: 0,
    searchTerm: '',
    selectedCase: null,
    page: 0
  }),
}));

export default useSTJStore;
