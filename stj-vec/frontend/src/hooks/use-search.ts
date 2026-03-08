import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client.ts';
import type { SearchFilters } from '@/api/types.ts';

export function useSearch(query: string, filters?: SearchFilters, limit?: number) {
  return useQuery({
    queryKey: ['search', query, filters, limit],
    queryFn: () => api.search({ query, limit, filters }),
    enabled: query.length > 2,
    staleTime: 5 * 60 * 1000,
  });
}
