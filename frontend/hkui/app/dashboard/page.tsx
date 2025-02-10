'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import StatusBadge from '../components/shared/StatusBadge';
import AuthenticatedLayout from '../components/layouts/AuthenticatedLayout';
import { useAuth } from '../context/AuthContext';

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
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated, loading: authLoading, token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    console.log('Dashboard effect running:', { authLoading, isAuthenticated, token, loading });
    
    if (authLoading) {
      console.log('Auth is still loading');
      return;
    }

    if (!isAuthenticated || !token) {
      console.log('Not authenticated, redirecting to login');
      router.push('/login');
      return;
    }

    const fetchData = async () => {
      try {
        console.log('Fetching dashboard data');
        setLoading(true);
        setError(null);

        const [statsRes, activityRes] = await Promise.all([
          fetch('/api/proxy/stats', {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          }),
          fetch('/api/proxy/changelogs/', {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          })
        ]);

        console.log('API responses:', { 
          statsStatus: statsRes.status,
          activityStatus: activityRes.status 
        });

        // Handle stats response
        if (statsRes.ok) {
          const statsData = await statsRes.json();
          setStats(statsData);
        } else if (statsRes.status === 401 || statsRes.status === 403) {
          console.log('Stats unauthorized');
          setError('Failed to fetch dashboard stats: Unauthorized');
        } else {
          const statsError = await statsRes.json().catch(() => ({ error: 'Failed to fetch stats' }));
          console.error('Stats error:', statsError);
          setError('Failed to fetch dashboard stats');
        }

        // Handle activity response
        if (activityRes.ok) {
          const activityData = await activityRes.json();
          setRecentActivity(activityData);
        } else if (activityRes.status === 401 || activityRes.status === 403) {
          console.log('Activity unauthorized');
          // Don't set error if we already have stats
          if (!statsRes.ok) {
            setError('Failed to fetch activity: Unauthorized');
          }
        } else {
          const activityError = await activityRes.json().catch(() => ({ error: 'Failed to fetch activity' }));
          console.error('Activity error:', activityError);
          // Don't set error if we already have stats
          if (!statsRes.ok) {
            setError('Failed to fetch activity');
          }
        }

        // Only redirect to login if both endpoints return auth errors
        if ((statsRes.status === 401 || statsRes.status === 403) && 
            (activityRes.status === 401 || activityRes.status === 403)) {
          console.log('Both endpoints unauthorized, redirecting to login');
          router.push('/login');
          return;
        }

      } catch (error) {
        console.error('Dashboard error:', error);
        setError(error instanceof Error ? error.message : 'Failed to load dashboard data');
      } finally {
        console.log('Setting loading to false');
        setLoading(false);
      }
    };

    fetchData();
  }, [isAuthenticated, authLoading, token, router]);

  if (authLoading) {
    console.log('Rendering auth loading state');
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Checking authentication...</span>
      </div>
    );
  }

  if (!isAuthenticated || !token) {
    console.log('Rendering not authenticated state');
    return null;
  }

  if (loading) {
    console.log('Rendering data loading state');
    return (
      <AuthenticatedLayout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2">Loading dashboard data...</span>
        </div>
      </AuthenticatedLayout>
    );
  }

  return (
    <AuthenticatedLayout>
      <div className="container mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
                  <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Projects</dt>
                    <dd className="text-lg font-semibold text-gray-900">{stats.projects}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
                  <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Namespaces</dt>
                    <dd className="text-lg font-semibold text-gray-900">{stats.namespaces}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-purple-500 rounded-md p-3">
                  <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Deployments</dt>
                    <dd className="text-lg font-semibold text-gray-900">{stats.deployments}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-yellow-500 rounded-md p-3">
                  <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Helm Releases</dt>
                    <dd className="text-lg font-semibold text-gray-900">{stats.helmReleases}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Recent Activity</h3>
          </div>
          {recentActivity.length > 0 ? (
            <div className="border-t border-gray-200">
              <ul role="list" className="divide-y divide-gray-200">
                {recentActivity.map((activity) => (
                  <li key={activity.id} className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <StatusBadge status={activity.status} />
                        <p className="ml-2 text-sm text-gray-600">{activity.name}</p>
                      </div>
                      <div className="ml-2 flex-shrink-0 flex">
                        <p className="text-sm text-gray-500">
                          {new Date(activity.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No recent activity</h3>
              <p className="mt-1 text-sm text-gray-500">Your activity will show up here</p>
            </div>
          )}
        </div>
      </div>
    </AuthenticatedLayout>
  );
}
