import { useMutation } from '@tanstack/react-query';
import { analyzeRepository, analyzePullRequest } from '../api/client';

export const useAnalysis = () => {
  return useMutation({
    mutationFn: async ({ url, token }) => {
      // Very basic URL heuristic
      if (url.includes('/pull/')) {
        return await analyzePullRequest(url, token);
      } else {
        return await analyzeRepository(url, token);
      }
    },
  });
};
