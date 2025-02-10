'use client';

import { useState } from 'react';
import Link from 'next/link';
import StatusBadge from '../shared/StatusBadge';

interface HelmReleaseCardProps {
  release: {
    id: string;
    name: string;
    namespace: string;
    chart: string;
    version: string;
    status: 'success' | 'warning' | 'error' | 'pending' | 'running';
    lastDeployed: string;
    description?: string;
  };
  onRollback?: (version: string) => void;
  onUninstall?: () => void;
}

export default function HelmReleaseCard({ release, onRollback, onUninstall }: HelmReleaseCardProps) {
  const [showActions, setShowActions] = useState(false);

  return (
    <div 
      className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="p-4">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              <Link href={`/helm/releases/${release.id}`} className="hover:text-blue-600">
                {release.name}
              </Link>
            </h3>
            <p className="text-sm text-gray-500">Namespace: {release.namespace}</p>
          </div>
          <StatusBadge status={release.status} />
        </div>

        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Chart</span>
            <span className="font-medium">{release.chart}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Version</span>
            <span className="font-mono text-xs">{release.version}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Last Deployed</span>
            <span>{new Date(release.lastDeployed).toLocaleString()}</span>
          </div>
          {release.description && (
            <div className="text-sm text-gray-600">
              <p className="truncate">{release.description}</p>
            </div>
          )}
        </div>

        <div className={`flex space-x-2 transition-opacity ${showActions ? 'opacity-100' : 'opacity-0'}`}>
          <Link
            href={`/helm/releases/${release.id}/values`}
            className="px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Values
          </Link>
          <button
            onClick={() => onRollback?.(release.version)}
            className="px-3 py-1 text-sm font-medium text-yellow-600 bg-yellow-50 rounded-md hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-yellow-500"
          >
            Rollback
          </button>
          <button
            onClick={onUninstall}
            className="px-3 py-1 text-sm font-medium text-red-600 bg-red-50 rounded-md hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            Uninstall
          </button>
        </div>
      </div>
    </div>
  );
}
