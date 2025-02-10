'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Header from '@/app/lib/Header';
import styles from '@/app/styles/shared.module.css';

interface Project {
    id: number;
    name: string;
    description: string;
    owner_id: number;
    created_at: string;
    updated_at: string;
}

const Dashboard: React.FC = () => {
    const [activeTab, setActiveTab] = useState('projects');
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            const response = await fetch('/api/projects');
            if (!response.ok) {
                throw new Error('Failed to fetch projects');
            }
            const data = await response.json();
            setProjects(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch projects');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateProject = async (name: string, description: string) => {
        try {
            const response = await fetch('/api/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, description }),
            });

            if (!response.ok) {
                throw new Error('Failed to create project');
            }

            const newProject = await response.json();
            setProjects([...projects, newProject]);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create project');
        }
    };

    return (
        <div className={styles.container}>
            <Header />
            <div className="flex h-screen">
                {/* Sidebar */}
                <aside className="w-64 bg-gray-800 text-white p-6">
                    <nav className="space-y-4">
                        <div className="pb-4 border-b border-gray-700">
                            <button 
                                onClick={() => setActiveTab('projects')}
                                className={`w-full text-left py-2 px-4 rounded ${activeTab === 'projects' ? 'bg-blue-600' : 'hover:bg-gray-700'}`}
                            >
                                Projects
                            </button>
                            <button 
                                onClick={() => setActiveTab('deployments')}
                                className={`w-full text-left py-2 px-4 rounded ${activeTab === 'deployments' ? 'bg-blue-600' : 'hover:bg-gray-700'}`}
                            >
                                Deployments
                            </button>
                            <button 
                                onClick={() => setActiveTab('monitoring')}
                                className={`w-full text-left py-2 px-4 rounded ${activeTab === 'monitoring' ? 'bg-blue-600' : 'hover:bg-gray-700'}`}
                            >
                                Monitoring
                            </button>
                            <button 
                                onClick={() => setActiveTab('config')}
                                className={`w-full text-left py-2 px-4 rounded ${activeTab === 'config' ? 'bg-blue-600' : 'hover:bg-gray-700'}`}
                            >
                                Configuration
                            </button>
                        </div>
                        <div className="pt-4">
                            <Link href="/" className="block py-2 px-4 hover:bg-gray-700 rounded">
                                Settings
                            </Link>
                            <Link href="/" className="block py-2 px-4 hover:bg-gray-700 rounded">
                                Documentation
                            </Link>
                        </div>
                    </nav>
                </aside>

                {/* Main Content */}
                <main className="flex-1 p-8 bg-gray-100">
                    {activeTab === 'projects' && (
                        <div>
                            <div className="flex justify-between items-center mb-6">
                                <h1 className="text-2xl font-bold">My Projects</h1>
                                <button 
                                    onClick={() => handleCreateProject('New Project', 'Description')}
                                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                                >
                                    New Project
                                </button>
                            </div>

                            {loading && <div>Loading projects...</div>}
                            {error && <div className="text-red-600">Error: {error}</div>}
                            
                            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                                {projects.map(project => (
                                    <div key={project.id} className="bg-white p-6 rounded-lg shadow-sm">
                                        <div className="flex justify-between items-start mb-4">
                                            <h3 className="font-semibold text-lg">{project.name}</h3>
                                        </div>
                                        <p className="text-sm text-gray-600 mb-4">
                                            {project.description}
                                        </p>
                                        <p className="text-xs text-gray-500 mb-4">
                                            Created: {new Date(project.created_at).toLocaleDateString()}
                                        </p>
                                        <div className="flex space-x-3">
                                            <button className="bg-blue-50 text-blue-600 px-3 py-1 rounded hover:bg-blue-100">
                                                Deploy
                                            </button>
                                            <button className="bg-gray-50 text-gray-600 px-3 py-1 rounded hover:bg-gray-100">
                                                Configure
                                            </button>
                                            <button className="bg-gray-50 text-gray-600 px-3 py-1 rounded hover:bg-gray-100">
                                                Logs
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {activeTab === 'deployments' && (
                        <div>
                            <h1 className="text-2xl font-bold mb-6">Deployments</h1>
                            <div className="bg-white rounded-lg shadow-sm p-6">
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between p-4 border-b">
                                        <div>
                                            <h3 className="font-semibold">Frontend Service v1.2.0</h3>
                                            <p className="text-sm text-gray-600">Deployed 2 hours ago</p>
                                        </div>
                                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
                                            Successful
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'monitoring' && (
                        <div>
                            <h1 className="text-2xl font-bold mb-6">Resource Monitoring</h1>
                            <div className="grid gap-6 md:grid-cols-2">
                                <div className="bg-white p-6 rounded-lg shadow-sm">
                                    <h3 className="font-semibold mb-4">CPU Usage</h3>
                                    <div className="h-40 bg-gray-50 rounded flex items-center justify-center">
                                        [CPU Usage Graph Placeholder]
                                    </div>
                                </div>
                                <div className="bg-white p-6 rounded-lg shadow-sm">
                                    <h3 className="font-semibold mb-4">Memory Usage</h3>
                                    <div className="h-40 bg-gray-50 rounded flex items-center justify-center">
                                        [Memory Usage Graph Placeholder]
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'config' && (
                        <div>
                            <h1 className="text-2xl font-bold mb-6">Configuration</h1>
                            <div className="bg-white rounded-lg shadow-sm p-6">
                                <div className="space-y-6">
                                    <div>
                                        <h3 className="font-semibold mb-2">Environment Variables</h3>
                                        <div className="bg-gray-50 p-4 rounded">
                                            <pre className="text-sm">[Environment Variables Configuration]</pre>
                                        </div>
                                    </div>
                                    <div>
                                        <h3 className="font-semibold mb-2">Service Configuration</h3>
                                        <div className="bg-gray-50 p-4 rounded">
                                            <pre className="text-sm">[Service Configuration]</pre>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

export default Dashboard;
