import { useInfiniteQuery } from '@tanstack/react-query';
import api from '../api/api';

const fetchVulnerabilities = async ({ pageParam = 0, queryKey }) => {
  const [_key, { search, classification }] = queryKey;
  const limit = 10;
  
  // Build the URL query string
  const params = new URLSearchParams({ limit, offset: pageParam });
  if (search) params.append('search', search);
  if (classification && classification !== 'All') params.append('classification', classification);
  
  const { data } = await api.get(`/api/vulnerabilities/?${params.toString()}`);
  
  return {
    items: data?.items || [],
    count: data?.count || 0,
    nextOffset: pageParam + limit,
  };
};

export const useVulnerabilities = (search, classification) => {
  return useInfiniteQuery({
    // Include the variables in the queryKey! This is crucial.
    // It tells React Query to refetch from page 0 when these change.
    queryKey: ['vulnerabilities', { search, classification }],
    queryFn: fetchVulnerabilities,
    initialPageParam: 0,
    getNextPageParam: (lastPage) => {
      if (lastPage.nextOffset < lastPage.count) {
        return lastPage.nextOffset;
      }
      return undefined;
    },
  });
};