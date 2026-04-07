import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const analyzeRepository = async (repoUrl, githubToken = null) => {
  const { data } = await api.post('/analyze-repo', {
    repo_url: repoUrl,
    github_token: githubToken || undefined,
  });
  return data;
};

export const analyzePullRequest = async (prUrl, githubToken = null) => {
  const { data } = await api.post('/analyze-pr', {
    pr_url: prUrl,
    github_token: githubToken || undefined,
  });
  return data;
};
