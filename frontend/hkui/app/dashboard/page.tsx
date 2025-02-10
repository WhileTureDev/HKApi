'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import StatusBadge from '../components/shared/StatusBadge';
import AuthenticatedLayout from '../components/layouts/AuthenticatedLayout';

interface DashboardStats {
  deployments: number;
  helmReleases: number;
  projects: number;
  namespaces: number;
}

interface RecentActivity {
  id: string;
  type: string;
  name: string;
  status: 'success' | 'warning' | 'error' | 'pending' | 'running';
  timestamp: string;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    deployments: 0,
    helmReleases: 0,
    projects: 0,
    namespaces: 0,
  });
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/dashboard/stats').then(res => res.json()),
      fetch('/api/dashboard/activity').then(res => res.json())
    ])
      .then(([statsData, activityData]) => {
        setStats(statsData);
        setRecentActivity(activityData);
      })
      .finally(() => setLoading(false));
  }, []);

  const cards = [
    { name: 'Total Deployments', value: stats.deployments, href: '/deployments' },
    { name: 'Helm Releases', value: stats.helmReleases, href: '/helm/releases' },
    { name: 'Projects', value: stats.projects, href: '/projects' },
    { name: 'Namespaces', value: stats.namespaces, href: '/namespaces' },
  ];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <AuthenticatedLayout>
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        
        <div className="mt-8">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {cards.map((card) => (
              <div
                key={card.name}
                className="relative overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:px-6 sm:py-6"
              >
                <dt>
                  <div className="absolute rounded-md bg-blue-500 p-3">
                    <svg
                      className="h-6 w-6 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={1.5}
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
                      />
                    </svg>
                  </div>
                  <p className="ml-16 truncate text-sm font-medium text-gray-500">
                    {card.name}
                  </p>
                </dt>
                <dd className="ml-16 flex items-baseline pb-6 sm:pb-7">
                  <p className="text-2xl font-semibold text-gray-900">
                    {card.value}
                  </p>
                  <div className="absolute inset-x-0 bottom-0 bg-gray-50 px-4 py-4 sm:px-6">
                    <div className="text-sm">
                      <Link
                        href={card.href}
                        className="font-medium text-blue-600 hover:text-blue-500"
                      >
                        View all
                        <span className="sr-only"> {card.name}</span>
                      </Link>
                    </div>
                  </div>
                </dd>
              </div>
            ))}
          </div>
        </div>

        <h2 className="mt-8 text-lg font-medium text-gray-900">Recent Activity</h2>
        <div className="mt-4 overflow-hidden bg-white shadow sm:rounded-md">
          <ul role="list" className="divide-y divide-gray-200">
            {recentActivity.map((activity) => (
              <li key={activity.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <p className="truncate text-sm font-medium text-gray-600">
                      {activity.type}: {activity.name}
                    </p>
                    <StatusBadge status={activity.status} />
                  </div>
                  <div className="mt-2 sm:flex sm:justify-between">
                    <div className="sm:flex">
                      <p className="flex items-center text-sm text-gray-500">
                        {new Date(activity.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </AuthenticatedLayout>
  );
}
