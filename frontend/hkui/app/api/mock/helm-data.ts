export const mockHelmReleases = [
  {
    id: '1',
    name: 'redis-cache',
    namespace: 'production',
    chart: 'bitnami/redis',
    version: '17.3.14',
    status: 'success',
    lastDeployed: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(), // 2 days ago
    description: 'Redis cache for production environment',
  },
  {
    id: '2',
    name: 'mongodb',
    namespace: 'production',
    chart: 'bitnami/mongodb',
    version: '13.9.1',
    status: 'warning',
    lastDeployed: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
    description: 'MongoDB database cluster',
  },
  {
    id: '3',
    name: 'rabbitmq',
    namespace: 'staging',
    chart: 'bitnami/rabbitmq',
    version: '11.2.0',
    status: 'running',
    lastDeployed: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(), // 12 hours ago
    description: 'RabbitMQ message broker',
  },
  {
    id: '4',
    name: 'elasticsearch',
    namespace: 'staging',
    chart: 'elastic/elasticsearch',
    version: '7.17.3',
    status: 'error',
    lastDeployed: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(), // 6 hours ago
    description: 'Elasticsearch cluster for log aggregation',
  },
];
