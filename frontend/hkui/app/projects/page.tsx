'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Breadcrumbs from '../components/shared/Breadcrumbs';
import LoadingSpinner from '@/app/components/LoadingSpinner';

interface Project {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  owner: {
    id: number;
    username: string;
  };
  namespaces?: {
    id: number;
    name: string;
    project_id: number;
  }[];
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showDeployForm, setShowDeployForm] = useState(false);
  const [projectDeployments, setProjectDeployments] = useState<{ [key: number]: { [key: string]: any[] } }>({});
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [deploymentForm, setDeploymentForm] = useState({
    releaseName: '',
    chartName: '',
    chartRepoUrl: '',
    values: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState<number | null>(null);
  const [deleteReleaseConfirmation, setDeleteReleaseConfirmation] = useState<{name: string, namespace: string} | null>(null);
  const router = useRouter();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching projects...');
      
      const response = await fetch(`/api/proxy/projects`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include'
      });

      console.log('Projects response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        console.log('Error data:', errorData);
        
        if (response.status === 401) {
          console.log('Token invalid or expired, redirecting to login...');
          setError(null);
          setLoading(false);
          router.push('/login');
          return;
        }

        if (response.status === 422) {
          console.log('Validation error:', errorData);
          const errorMessage = errorData.detail?.[0]?.msg || errorData.detail || 'Validation error';
          setError(errorMessage);
          setLoading(false);
          return;
        }
        
        setError(typeof errorData.error === 'string' ? errorData.error : 'Failed to fetch projects');
        setLoading(false);
        return;
      }

      const projectsData = await response.json();
      console.log('Projects data received:', projectsData);
      
      // Always treat as array, empty if no projects
      setProjects(Array.isArray(projectsData) ? projectsData : []);
      
    } catch (error) {
      console.error('Error fetching projects:', error);
      setError('Failed to fetch projects. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjectNamespaces = async (projectId: number) => {
    try {
      const response = await fetch(`/api/proxy/projects/${projectId}/namespaces/`, {
        credentials: 'include'
      });
      if (!response.ok) {
        throw new Error('Failed to fetch namespaces');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching namespaces:', error);
      return [];
    }
  };

  const fetchProjectDeployments = async (namespace: string) => {
    try {
      const response = await fetch(`/api/proxy/helm/releases/${namespace}`, {
        credentials: 'include'
      });
      if (!response.ok) {
        throw new Error('Failed to fetch deployments');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching deployments:', error);
      return [];
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Breadcrumbs items={[{ label: 'Projects', href: '/projects' }]} />
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {error}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-semibold text-gray-900">Projects</h1>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Create Project
            </button>
          </div>

          {projects.length === 0 ? (
            <div className="text-center py-12">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No projects</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by creating a new project.</p>
              <div className="mt-6">
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg
                    className="-ml-1 mr-2 h-5 w-5"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Create Project
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul role="list" className="divide-y divide-gray-200">
                {projects.map((project) => (
                  <li key={project.id}>
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-blue-600 truncate">
                          {project.name}
                        </p>
                        <div className="ml-2 flex-shrink-0 flex">
                          <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            {project.owner.username}
                          </p>
                        </div>
                      </div>
                      <div className="mt-2 sm:flex sm:justify-between">
                        <div className="sm:flex">
                          <p className="flex items-center text-sm text-gray-500">
                            {project.description || 'No description'}
                          </p>
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                          <p>
                            Created on {new Date(project.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {/* Create Project Modal */}
      {showCreateForm && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          {/* Modal content */}
        </div>
      )}
    </div>
  );
}
