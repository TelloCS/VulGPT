import { useInfiniteQuery } from '@tanstack/react-query';
import api from '../api/api';

export const useScanResults = (scanId, isCompleted) => {
  return useInfiniteQuery({
    queryKey: ['scanResults', scanId],
    queryFn: async ({ pageParam = 0 }) => {
      const limit = 100; //initial paginate limit
      const { data } = await api.get(`/api/scans/${scanId}/?limit=${limit}&offset=${pageParam}`);
      
      const items = Array.isArray(data) ? data : (data?.items || []);
      const count = data?.count || items.length;
      
      return {
        items,
        count,
        nextOffset: pageParam + limit,
      };
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage) => {
      if (lastPage.nextOffset < lastPage.count) {
        return lastPage.nextOffset;
      }
      return undefined;
    },
    enabled: !!isCompleted, 
    refetchInterval: false, 
  });
};