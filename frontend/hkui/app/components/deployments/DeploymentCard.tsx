'use client';

import { useState } from 'react';
import Link from 'next/link';
import StatusBadge from '../shared/StatusBadge';

interface DeploymentCardProps {
  deployment: {
    id: string;
    name: string;
    namespace: string;
    status: 'success' | 'warning' | 'error' | 'pending' | 'running';
    replicas: number;
    availableReplicas: number;
    image: string;
    createdAt: string;
  };
  onScale?: (replicas: number) => void;
  onRestart?: () => void;
}

export default function DeploymentCard({ deployment, onScale, onRestart }: DeploymentCardProps) {
  const [isScaling, setIsScaling] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const handleScale = async (newReplicas: number) => {
    if (onScale) {
      setIsScaling(true);
      try {
        await onScale(newReplicas);
      } finally {
        setIsScaling(false);
      }
    }
  };

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
              <Link href={`/deployments/${deployment.id}`} className="hover:text-blue-600">
                {deployment.name}
              </Link>
            </h3>
            <p className="text-sm text-gray-500">Namespace: {deployment.namespace}</p>
          </div>
          <StatusBadge status={deployment.status} />
        </div>

        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Replicas</span>
            <span className="font-medium">
              {deployment.availableReplicas}/{deployment.replicas}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Image</span>
            <span className="font-mono text-xs">{deployment.image}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Created</span>
            <span>{new Date(deployment.createdAt).toLocaleDateString()}</span>
          </div>
        </div>

        <div className={`flex space-x-2 transition-opacity ${showActions ? 'opacity-100' : 'opacity-0'}`}>
          <button
            onClick={() => handleScale(deployment.replicas + 1)}
            disabled={isScaling}
            className="px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Scale Up
          </button>
          <button
            onClick={() => handleScale(Math.max(0, deployment.replicas - 1))}
            disabled={isScaling || deployment.replicas <= 1}
            className="px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Scale Down
          </button>
          <button
            onClick={onRestart}
            className="px-3 py-1 text-sm font-medium text-gray-600 bg-gray-50 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Restart
          </button>
        </div>
      </div>
    </div>
  );
}
