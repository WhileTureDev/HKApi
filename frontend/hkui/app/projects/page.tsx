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
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/projects`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch projects');
      }

      const data = await response.json();
      setProjects(data);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
    }
  };

  const handleDeleteProject = async (projectId: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/projects/${projectId}`, {
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

  const handleCreateProject = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Generate a unique namespace name
      const namespaceName = `${formData.name.toLowerCase().replace(/\s+/g, '-')}-${Math.random().toString(36).substring(2, 8)}`;
      
      // First, create the project
      const projectResponse = await fetch(`${API_URL}/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description
        })
      });

      if (!projectResponse.ok) {
        const errorData = await projectResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to create project');
      }

      const newProject = await projectResponse.json();
      
      // Then, create the namespace
      const namespaceResponse = await fetch(`${API_URL}/namespaces`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: namespaceName,
          project_id: newProject.id
        })
      });

      if (!namespaceResponse.ok) {
        const errorData = await namespaceResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to create namespace');
      }

      const newNamespace = await namespaceResponse.json();
      
      // Update the project list with the new project and its namespace
      setProjects(prevProjects => [
        ...prevProjects, 
        { 
          ...newProject, 
          namespace: {
            id: newNamespace.id,
            name: newNamespace.name
          }
        }
      ]);

      // Reset form and close modal
      setFormData({ name: '', description: '' });
      setShowNewProjectForm(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred while creating the project';
      setError(errorMessage);
    }
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

    setIsSubmitting(true);
    setFormError('');

    try {
      const response = await fetch(`${API_URL}/projects`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name.trim(),
          description: formData.description.trim()
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to create project');
      }

      // Reset form and close dialog
      setFormData({ name: '', description: '' });
      setShowNewProjectForm(false);
      
      // Refresh projects list
      await fetchProjects();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Failed to create project');
    } finally {
      setIsSubmitting(false);
    }
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
                    onClick={() => handleDeleteProject(project.id)}
                    className="text-red-500 hover:text-red-700 transition-colors"
                    title="Delete Project"
                  >
                    <svg 
                      xmlns="http://www.w3.org/2000/svg" 
                      className="h-6 w-6" 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" 
                      />
                    </svg>
                  </button>
                </div>
                
                {project.description && (
                  <p className="text-gray-600 mb-4">{project.description}</p>
                )}
                
                {project.namespace && (
                  <p className="text-gray-600 mb-4">Namespace: {project.namespace.name}</p>
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
