import { useQuery } from '@tanstack/react-query';
import type { QueryParams, JurisprudenceResult, SQLPreview } from '@/types';
import {
  MOCK_RESULTS,
  generateSQLPreview,
  estimateResultCount,
} from '@/utils/mockData';

/**
 * Simulates API delay for realistic testing
 */
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Mock API call to fetch jurisprudence results
 */
async function fetchJurisprudence(
  params: QueryParams
): Promise<JurisprudenceResult[]> {
  await delay(800); // Simulate network delay

  let results = [...MOCK_RESULTS];

  // Filter by domain
  if (params.domain) {
    results = results.filter((r) =>
      r.ementa.toLowerCase().includes(params.domain!.toLowerCase().split(' ')[1])
    );
  }

  // Filter by trigger words
  if (params.triggerWords.length > 0) {
    results = results.filter((r) =>
      params.triggerWords.some((word) =>
        r.ementa.toLowerCase().includes(word.toLowerCase())
      )
    );
  }

  // Filter by document type (only acórdãos)
  // In a real scenario, this would filter by document type
  // For mock, we keep all results

  return results;
}

/**
 * Hook to fetch jurisprudence results with TanStack Query
 */
export function useJurisprudenceQuery(params: QueryParams) {
  return useQuery({
    queryKey: ['jurisprudence', params],
    queryFn: () => fetchJurisprudence(params),
    enabled: params.domain !== null || params.triggerWords.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to generate SQL preview (synchronous, no API call needed)
 */
export function useSQLPreview(params: QueryParams): SQLPreview {
  const query = generateSQLPreview(
    params.domain,
    params.triggerWords,
    params.onlyAcordaos
  );

  const estimatedResults = estimateResultCount(
    params.domain,
    params.triggerWords,
    params.onlyAcordaos
  );

  return {
    query,
    estimatedResults,
  };
}
