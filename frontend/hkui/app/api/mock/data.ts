// Mock data for development

export const mockStats = {
  deployments: 12,
  helmReleases: 8,
  projects: 5,
  namespaces: 3,
};

export const mockActivity = [
  {
    id: '1',
    type: 'Deployment',
    name: 'frontend-service',
    status: 'success',
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 minutes ago
  },
  {
    id: '2',
    type: 'Helm Release',
    name: 'redis-cache',
    status: 'running',
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(), // 15 minutes ago
  },
  {
    id: '3',
    type: 'Project',
    name: 'e-commerce-platform',
    status: 'success',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
  },
  {
    id: '4',
    type: 'Deployment',
    name: 'auth-service',
    status: 'error',
    timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(), // 45 minutes ago
  },
];

export const mockDeployments = [
  {
    id: '1',
    name: 'frontend-service',
    namespace: 'production',
    status: 'success',
    replicas: 3,
    availableReplicas: 3,
    image: 'nginx:1.21',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(), // 3 days ago
  },
  {
    id: '2',
    name: 'auth-service',
    namespace: 'production',
    status: 'error',
    replicas: 2,
    availableReplicas: 1,
    image: 'auth-service:v1.2.3',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(), // 2 days ago
  },
  {
    id: '3',
    name: 'redis-cache',
    namespace: 'staging',
    status: 'running',
    replicas: 1,
    availableReplicas: 1,
    image: 'redis:6.2',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
  },
];

export const mockNamespaces = ['production', 'staging', 'development'];
