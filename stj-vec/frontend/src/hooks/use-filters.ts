import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client.ts';

export function useFilters() {
  return useQuery({
    queryKey: ['filters'],
    queryFn: () => api.filters(),
    staleTime: Infinity,
  });
}
