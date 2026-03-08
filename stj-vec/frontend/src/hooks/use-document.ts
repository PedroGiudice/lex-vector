import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client.ts';

export function useDocument(docId: string | null) {
  return useQuery({
    queryKey: ['document', docId],
    queryFn: () => api.document(docId!),
    enabled: !!docId,
    staleTime: 10 * 60 * 1000,
  });
}
