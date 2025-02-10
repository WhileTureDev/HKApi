'use client';

import { useState, useEffect } from 'react';
import Breadcrumbs from '../components/shared/Breadcrumbs';
import DeploymentCard from '../components/deployments/DeploymentCard';
import AuthenticatedLayout from '../components/layouts/AuthenticatedLayout';

interface Deployment {
  id: string;
  name: string;
  namespace: string;
  status: 'success' | 'warning' | 'error' | 'pending' | 'running';
  replicas: number;
  availableReplicas: number;
  image: string;
  createdAt: string;
}

export default function DeploymentsPage() {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNamespace, setSelectedNamespace] = useState<string>('');
  const [namespaces, setNamespaces] = useState<string[]>([]);

  useEffect(() => {
    fetchNamespaces();
  }, []);

  useEffect(() => {
    if (selectedNamespace) {
      fetchDeployments(selectedNamespace);
    }
  }, [selectedNamespace]);

  const fetchNamespaces = async () => {
    try {
      const response = await fetch('/api/namespaces');
      if (!response.ok) {
        throw new Error('Failed to fetch namespaces');
      }
      const data = await response.json();
      setNamespaces(data);
      if (data.length > 0) {
        setSelectedNamespace(data[0]);
      }
    } catch (err) {
      setError('Failed to load namespaces');
    }
  };

  const fetchDeployments = async (namespace: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/deployments?namespace=${namespace}`);
      if (!response.ok) {
        throw new Error('Failed to fetch deployments');
      }
      const data = await response.json();
      setDeployments(data);
      setError(null);
    } catch (err) {
      setError('Failed to load deployments');
      setDeployments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleScale = async (deploymentId: string, replicas: number) => {
    try {
      const response = await fetch(`/api/deployments/${deploymentId}/scale`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ replicas }),
      });

      if (!response.ok) {
        throw new Error('Failed to scale deployment');
      }

      // Refresh deployments after scaling
      await fetchDeployments(selectedNamespace);
    } catch (err) {
      setError('Failed to scale deployment');
    }
  };

  const handleRestart = async (deploymentId: string) => {
    try {
      const response = await fetch(`/api/deployments/${deploymentId}/restart`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to restart deployment');
      }

      // Refresh deployments after restart
      await fetchDeployments(selectedNamespace);
    } catch (err) {
      setError('Failed to restart deployment');
    }
  };

  return (
    <AuthenticatedLayout>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Breadcrumbs
            items={[
              { href: '/dashboard', label: 'Dashboard' },
              { href: '/deployments', label: 'Deployments' },
            ]}
          />
        </div>

        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Deployments</h1>
          <div className="flex items-center space-x-4">
            <select
              value={selectedNamespace}
              onChange={(e) => setSelectedNamespace(e.target.value)}
              className="block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              {namespaces.map((namespace) => (
                <option key={namespace} value={namespace}>
                  {namespace}
                </option>
              ))}
            </select>
            <button
              onClick={() => window.location.href = '/deployments/new'}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              New Deployment
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : deployments.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">No deployments found</h3>
            <p className="mt-2 text-sm text-gray-500">
              Get started by creating a new deployment.
            </p>
            <div className="mt-6">
              <button
                onClick={() => window.location.href = '/deployments/new'}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-600 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Create Deployment
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {deployments.map((deployment) => (
              <DeploymentCard
                key={deployment.id}
                deployment={deployment}
                onScale={(replicas) => handleScale(deployment.id, replicas)}
                onRestart={() => handleRestart(deployment.id)}
              />
            ))}
          </div>
        )}
      </div>
    </AuthenticatedLayout>
  );
}
