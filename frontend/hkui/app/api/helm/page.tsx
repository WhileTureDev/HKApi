// app/api/helm/page.tsx

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import withAuth from '@/app/lib/withAuth'; // Adjust the import path as necessary
import styles from '@/app/styles/Api.module.css';

const HelmPage: React.FC = () => {
    const router = useRouter();
    const [formData, setFormData] = useState({
        name: '',
        namespace: '',
        chart_name: '',
        chart_repo_url: '',
        provider: '',
    });
    const [jsonPayload, setJsonPayload] = useState('');
    const [response, setResponse] = useState('');
    const [namespace, setNamespace] = useState('');
    const [releases, setReleases] = useState([]);
    const [releaseError, setReleaseError] = useState('');
    const [selectedReleases, setSelectedReleases] = useState([]);

    useEffect(() => {
        const generatedPayload = JSON.stringify(formData, null, 2);
        setJsonPayload(generatedPayload);
    }, [formData]);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleJsonChange = (e) => {
        setJsonPayload(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        let payload;
        if (jsonPayload) {
            try {
                payload = JSON.parse(jsonPayload);
            } catch (error) {
                setResponse('Invalid JSON payload');
                return;
            }
        } else {
            payload = formData;
        }

        try {
            const token = localStorage.getItem('token');
            console.log('Token from localStorage:', token);

            if (!token) {
                setResponse('No authentication token found');
                return;
            }

            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/helm/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            console.log('Request payload:', payload);
            console.log('Response status:', res.status);

            if (res.status === 401) {
                setResponse('Unauthorized: Invalid token or session expired');
                return;
            }

            const data = await res.json();
            setResponse(JSON.stringify(data, null, 2));
        } catch (error: unknown) {
            if (error instanceof Error) {
                setResponse('Error: ' + error.message);
                console.error('Error message:', error.message);
            } else {
                setResponse('An unknown error occurred');
                console.error('Unknown error:', error);
            }
        }
    };

    const handleNamespaceChange = (e) => {
        setNamespace(e.target.value);
    };

    const fetchReleases = async () => {
        try {
            const token = localStorage.getItem('token');
            console.log('Token from localStorage:', token);

            if (!token) {
                setReleaseError('No authentication token found');
                return;
            }

            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/helm/list?namespace=${namespace}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            console.log('Namespace:', namespace);
            console.log('Response status:', res.status);

            if (res.status === 401) {
                setReleaseError('Unauthorized: Invalid token or session expired');
                return;
            }

            const data = await res.json();
            if (Array.isArray(data.releases)) {
                setReleases(data.releases);
            } else {
                setReleases([]);
                setReleaseError('Unexpected response format');
            }
            setReleaseError('');
        } catch (error: unknown) {
            if (error instanceof Error) {
                setReleaseError('Error: ' + error.message);
                console.error('Error message:', error.message);
            } else {
                setReleaseError('An unknown error occurred');
                console.error('Unknown error:', error);
            }
        }
    };

    const handleSelectRelease = (release) => {
        const newSelectedReleases = selectedReleases.includes(release)
            ? selectedReleases.filter((r) => r !== release)
            : [...selectedReleases, release];
        setSelectedReleases(newSelectedReleases);
    };

    const handleDeleteRelease = async (release) => {
        try {
            const token = localStorage.getItem('token');
            console.log('Token from localStorage:', token);

            if (!token) {
                setReleaseError('No authentication token found');
                return;
            }

            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/helm/delete`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    name: release.Name,
                    namespace: release.Namespace,
                }),
            });

            console.log('Delete request payload:', {
                name: release.Name,
                namespace: release.Namespace,
            });
            console.log('Response status:', res.status);

            if (res.status === 401) {
                setReleaseError('Unauthorized: Invalid token or session expired');
                return;
            }

            if (res.ok) {
                setReleases((prevReleases) => prevReleases.filter((r) => r !== release));
                setSelectedReleases((prevSelected) => prevSelected.filter((r) => r !== release));
            } else {
                setReleaseError('Failed to delete release');
            }
        } catch (error: unknown) {
            if (error instanceof Error) {
                setReleaseError('Error: ' + error.message);
                console.error('Error message:', error.message);
            } else {
                setReleaseError('An unknown error occurred');
                console.error('Unknown error:', error);
            }
        }
    };

    const handleDeleteSelectedReleases = async () => {
        for (const release of selectedReleases) {
            await handleDeleteRelease(release);
        }
    };

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div className={styles.logo}>HKUI</div>
                <div className={styles.userProfile}>
                    <img src="/profile.png" alt="User Profile" />
                </div>
            </header>

            <aside className={styles.sidebar}>
                <nav>
                    <Link href="/api/helm">Helm</Link>
                    <Link href="/api/deployment">Deployments</Link>
                    <div className={styles.bottomNav}>
                        <Link href="/dashboard">Dashboard</Link>
                    </div>
                </nav>
            </aside>

            <main className={styles.main}>
                <section className={styles.content}>
                    <div className={styles.card}>
                        <h1>Deploy a Helm Chart</h1>
                        <form onSubmit={handleSubmit} className={styles.form}>
                            <div className={styles.formGroup}>
                                <label>Name</label>
                                <input
                                    type="text"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleChange}
                                    placeholder="Enter the name"
                                    required
                                />
                            </div>
                            <div className={styles.formGroup}>
                                <label>Namespace</label>
                                <input
                                    type="text"
                                    name="namespace"
                                    value={formData.namespace}
                                    onChange={handleChange}
                                    placeholder="Enter the namespace"
                                    required
                                />
                            </div>
                            <div className={styles.formGroup}>
                                <label>Chart Name</label>
                                <input
                                    type="text"
                                    name="chart_name"
                                    value={formData.chart_name}
                                    onChange={handleChange}
                                    placeholder="Enter the chart name"
                                    required
                                />
                            </div>
                            <div className={styles.formGroup}>
                                <label>Chart Repo URL</label>
                                <input
                                    type="text"
                                    name="chart_repo_url"
                                    value={formData.chart_repo_url}
                                    onChange={handleChange}
                                    placeholder="Enter the chart repo URL"
                                    required
                                />
                            </div>
                            <div className={styles.formGroup}>
                                <label>Provider</label>
                                <input
                                    type="text"
                                    name="provider"
                                    value={formData.provider}
                                    onChange={handleChange}
                                    placeholder="Enter the provider"
                                    required
                                />
                            </div>
                            <button type="submit" className={styles.submitButton}>Deploy</button>
                        </form>
                        <div className={styles.jsonInput}>
                            <label>Or provide JSON payload</label>
                            <textarea value={jsonPayload} onChange={handleJsonChange} />
                        </div>
                        <div className={styles.response}>
                            <h2>Response</h2>
                            <pre>{response}</pre>
                        </div>
                    </div>

                    <div className={styles.card}>
                        <h1>Helm Releases</h1>
                        <div className={styles.formGroup}>
                            <label>Namespace</label>
                            <input
                                type="text"
                                value={namespace}
                                onChange={handleNamespaceChange}
                                placeholder="Enter the namespace"
                                required
                            />
                            <button onClick={fetchReleases} className={styles.refreshButton}>Refresh</button>
                            {selectedReleases.length > 0 && (
                                <button onClick={handleDeleteSelectedReleases} className={styles.deleteButton}>Delete All</button>
                            )}
                        </div>
                        {releaseError && <p className={styles.error}>{releaseError}</p>}
                        <div className={styles.releaseList}>
                            {Array.isArray(releases) && releases.length > 0 ? (
                                <table className={styles.table}>
                                    <thead>
                                    <tr>
                                        <th>Select</th>
                                        <th>Name</th>
                                        <th>Namespace</th>
                                        <th>Status</th>
                                        <th>Revision</th>
                                        <th>Updated</th>
                                        <th>Action</th>
                                    </tr>
                                    </thead>
                                    <tbody>
                                    {releases.map((release, index) => (
                                        <tr key={index}>
                                            <td>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedReleases.includes(release)}
                                                    onChange={() => handleSelectRelease(release)}
                                                />
                                            </td>
                                            <td>{release.Name}</td>
                                            <td>{release.Namespace}</td>
                                            <td>{release.Status}</td>
                                            <td>{release.Revision}</td>
                                            <td>{release.Updated}</td>
                                            <td>
                                                <button onClick={() => handleDeleteRelease(release)} className={styles.deleteButton}>Delete</button>
                                            </td>
                                        </tr>
                                    ))}
                                    </tbody>
                                </table>
                            ) : (
                                <p>No releases found</p>
                            )}
                        </div>
                    </div>
                </section>
            </main>

            <footer className={styles.footer}>
                <p>&copy; 2024 HKUI. All rights reserved.</p>
                <div className={styles.footerLinks}>
                    <a href="#">Privacy Policy</a>
                    <a href="#">Terms of Service</a>
                    <a href="#">Contact Us</a>
                </div>
            </footer>
        </div>
    );
};

export default withAuth(HelmPage);
