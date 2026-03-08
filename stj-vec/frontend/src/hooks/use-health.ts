import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client.ts';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.health(),
    refetchInterval: 30_000,
    staleTime: 10_000,
  });
}
