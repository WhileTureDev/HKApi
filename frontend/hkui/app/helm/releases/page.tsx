'use client';

import { useState, useEffect } from 'react';
import Breadcrumbs from '../../components/shared/Breadcrumbs';
import HelmReleaseCard from '../../components/helm/HelmReleaseCard';
import AuthenticatedLayout from '../../components/layouts/AuthenticatedLayout';

interface HelmRelease {
  id: string;
  name: string;
  namespace: string;
  chart: string;
  version: string;
  status: 'success' | 'warning' | 'error' | 'pending' | 'running';
  lastDeployed: string;
  description?: string;
}

export default function HelmReleasesPage() {
  const [releases, setReleases] = useState<HelmRelease[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNamespace, setSelectedNamespace] = useState<string>('');
  const [namespaces, setNamespaces] = useState<string[]>([]);

  useEffect(() => {
    fetchNamespaces();
  }, []);

  useEffect(() => {
    if (selectedNamespace) {
      fetchReleases(selectedNamespace);
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

  const fetchReleases = async (namespace: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/helm/releases?namespace=${namespace}`);
      if (!response.ok) {
        throw new Error('Failed to fetch Helm releases');
      }
      const data = await response.json();
      setReleases(data);
      setError(null);
    } catch (err) {
      setError('Failed to load Helm releases');
      setReleases([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (releaseId: string, version: string) => {
    try {
      const response = await fetch(`/api/helm/releases/${releaseId}/rollback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ version }),
      });

      if (!response.ok) {
        throw new Error('Failed to rollback release');
      }

      // Refresh releases after rollback
      await fetchReleases(selectedNamespace);
    } catch (err) {
      setError('Failed to rollback release');
    }
  };

  const handleUninstall = async (releaseId: string) => {
    if (!confirm('Are you sure you want to uninstall this release?')) {
      return;
    }

    try {
      const response = await fetch(`/api/helm/releases/${releaseId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to uninstall release');
      }

      // Refresh releases after uninstall
      await fetchReleases(selectedNamespace);
    } catch (err) {
      setError('Failed to uninstall release');
    }
  };

  return (
    <AuthenticatedLayout>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Breadcrumbs
            items={[
              { href: '/dashboard', label: 'Dashboard' },
              { href: '/helm/releases', label: 'Helm Releases' },
            ]}
          />
        </div>

        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Helm Releases</h1>
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
              onClick={() => window.location.href = '/helm/releases/new'}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Install Chart
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
        ) : releases.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">No Helm releases found</h3>
            <p className="mt-2 text-sm text-gray-500">
              Get started by installing a new Helm chart.
            </p>
            <div className="mt-6">
              <button
                onClick={() => window.location.href = '/helm/releases/new'}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-600 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Install Chart
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {releases.map((release) => (
              <HelmReleaseCard
                key={release.id}
                release={release}
                onRollback={(version) => handleRollback(release.id, version)}
                onUninstall={() => handleUninstall(release.id)}
              />
            ))}
          </div>
        )}
      </div>
    </AuthenticatedLayout>
  );
}
