'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/navigation';
import Breadcrumbs from '../components/shared/Breadcrumbs';
import AuthenticatedLayout from '../components/layouts/AuthenticatedLayout';
import LoadingSpinner from '@/app/components/LoadingSpinner';

const API_URL = 'http://hkapi.dailytoolset.com';

interface Project {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  owner_id: number;
  updated_at: string;
  namespace?: {
    id: number;
    name: string;
  };
  namespaces?: any[];
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewProjectForm, setShowNewProjectForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    fetchProjects();
  }, [user, router]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/v1/projects/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch projects');
      }

      const projectsData = await response.json();
      
      // Fetch namespaces for each project
      const projectsWithNamespaces = await Promise.all(
        projectsData.map(async (project: any) => ({
          ...project,
          namespaces: await fetchProjectNamespaces(project.id)
        }))
      );

      setProjects(projectsWithNamespaces);
    } catch (error) {
      console.error('Error fetching projects:', error);
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjectNamespaces = async (projectId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/v1/namespaces/list`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch namespaces');
      }

      const allNamespaces = await response.json();
      return allNamespaces.filter((ns: any) => ns.project_id === projectId);
    } catch (error) {
      console.error('Error fetching project namespaces:', error);
      return [];
    }
  };

  const handleDeleteProject = async (projectId: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/v1/projects/${projectId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete project');
      }

      // Remove the deleted project from the list
      setProjects(projects.filter(project => project.id !== projectId));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred while deleting the project';
      setError(errorMessage);
    }
  };

  const handleDeleteNamespace = async (namespaceId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/v1/namespaces/delete/${namespaceId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete namespace');
      }

      // Refresh namespaces list
      await fetchNamespaces();
    } catch (error) {
      console.error('Error deleting namespace:', error);
    }
  };

  const fetchNamespaces = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/namespaces/list`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch namespaces');
      }

      const namespaces = await response.json();
      setNamespaces(namespaces);
    } catch (error) {
      console.error('Error fetching namespaces:', error);
    }
  };

  const createProjectWithNamespace = async (formData: {
    name: string;
    description: string;
  }) => {
    try {
      // Fetch current user's information
      const userResponse = await fetch(`${API_URL}/api/v1/users/me`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!userResponse.ok) {
        throw new Error('Failed to fetch user information');
      }

      const user = await userResponse.json();
      
      // Generate unique namespace name
      const namespaceName = `${user.username.toLowerCase()}-${formData.name.toLowerCase().replace(/\s+/g, '-')}-${Math.random().toString(36).substring(2, 8)}`;
      
      // First, create the project
      const projectResponse = await fetch(`${API_URL}/api/v1/projects/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description
        })
      });

      if (!projectResponse.ok) {
        throw new Error('Failed to create project');
      }

      const newProject = await projectResponse.json();
      
      // Then, create the namespace
      const namespaceResponse = await fetch(`${API_URL}/api/v1/namespaces/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          name: namespaceName,
          project_id: newProject.id
        })
      });

      if (!namespaceResponse.ok) {
        throw new Error('Failed to create namespace');
      }

      // Refresh projects list
      await fetchProjects();
      
      // Reset form and close modal
      setShowNewProjectForm(false);
      setFormData({ name: '', description: '' });
      
      // Show success message
      setSuccessMessage(`Project ${formData.name} and namespace ${namespaceName} created successfully`);
    } catch (error) {
      console.error('Error creating project and namespace:', error);
      setFormError(error instanceof Error ? error.message : 'An error occurred');
    }
  };

  const handleCreateProject = async () => {
    setIsSubmitting(true);
    setFormError('');
    await createProjectWithNamespace(formData);
    setIsSubmitting(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear form error when user starts typing
    if (formError) setFormError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    if (!formData.name.trim()) {
      setFormError('Project name is required');
      return;
    }

    await handleCreateProject();
  };

  return (
    <AuthenticatedLayout>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Breadcrumbs
            items={[
              { href: '/dashboard', label: 'Dashboard' },
              { href: '/projects', label: 'Projects' },
            ]}
          />
        </div>

        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <button
            onClick={() => setShowNewProjectForm(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            New Project
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {successMessage && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-600">{successMessage}</p>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <LoadingSpinner />
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">No projects found</h3>
            <p className="mt-2 text-sm text-gray-500">
              Get started by creating a new project.
            </p>
            <div className="mt-6">
              <button
                onClick={() => setShowNewProjectForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-600 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Create Project
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map(project => (
              <div 
                key={project.id} 
                className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold text-gray-900">{project.name}</h2>
                  <button 
                    className="text-red-500 hover:text-red-700 transition-colors" 
                    title="Delete Project"
                    onClick={() => handleDeleteProject(project.id)}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </button>
                </div>
                {project.description && (
                  <p className="text-gray-600 mb-4">{project.description}</p>
                )}
                
                {project.namespaces && project.namespaces.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Namespace:</h3>
                    <div className="flex flex-wrap gap-2">
                      {project.namespaces.map((namespace) => (
                        <span 
                          key={namespace.id} 
                          className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded"
                        >
                          {namespace.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="text-sm text-gray-500">
                  Created: {new Date(project.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* New Project Form Modal */}
      {showNewProjectForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Create New Project</h2>
              <button
                onClick={() => {
                  setShowNewProjectForm(false);
                  setFormData({ name: '', description: '' });
                  setFormError('');
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Project Name *
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter project name"
                />
              </div>

              <div className="mb-4">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter project description"
                />
              </div>

              {formError && (
                <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
                  {formError}
                </div>
              )}

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowNewProjectForm(false);
                    setFormData({ name: '', description: '' });
                    setFormError('');
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AuthenticatedLayout>
  );
}
