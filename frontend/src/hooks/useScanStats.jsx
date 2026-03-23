import { useQuery } from '@tanstack/react-query';
import api from '../api/api';

export const useScanStats = (scanId) => {
  return useQuery({
    queryKey: ['scanStats', scanId],
    queryFn: async () => {
      const { data } = await api.get(`/api/scans/${scanId}/stats/`);
      return data;
    },
    refetchInterval: (query) => {
      // Keep polling every 3 seconds until the backend explicitly says we are done
      const data = query.state.data;
      if (!data || data.status !== 'COMPLETED') {
        return 3000; 
      }
      return false; // Kill the polling
    },
  });
};