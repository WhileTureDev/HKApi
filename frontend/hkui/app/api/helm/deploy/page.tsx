'use client';

import React, { useState, useEffect } from 'react';
import withAuth from '@/app/lib/withAuth';
import Header from '@/app/lib/Header';
import styles from '@/app/styles/HelmDeploy.module.css';
import createHelmRelease from '@/app/lib/api/createHelmRelease';
import LoginModal from '@/app/lib/LoginModal';

const HelmDeploy: React.FC = () => {
    const [formData, setFormData] = useState({
        name: '',
        namespace: '',
        chart_name: '',
        chart_repo_url: '',
        provider: '',
    });
    const [jsonPayload, setJsonPayload] = useState('');
    const [response, setResponse] = useState('');
    const [isDeploying, setIsDeploying] = useState(false);
    const [showLoginModal, setShowLoginModal] = useState(false);

    useEffect(() => {
        setJsonPayload(JSON.stringify(formData, null, 2));
    }, [formData]);

    const handleChange = (e: { target: { name: string; value: string } }) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleJsonChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setJsonPayload(e.target.value);
        try {
            const updatedFormData = JSON.parse(e.target.value);
            setFormData(updatedFormData);
        } catch (error) {
            // Invalid JSON, do not update formData
        }
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setResponse('');
        setIsDeploying(true);
        let payload;
        if (jsonPayload) {
            try {
                payload = JSON.parse(jsonPayload);
            } catch (error) {
                setResponse('Invalid JSON payload');
                setIsDeploying(false);
                return;
            }
        } else {
            payload = formData;
        }

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setResponse('No authentication token found');
                setShowLoginModal(true);
                setIsDeploying(false);
                return;
            }

            const data = await createHelmRelease(payload, token);
            setResponse(JSON.stringify(data, null, 2));
            setIsDeploying(false);
        } catch (error: unknown) {
            if (error instanceof Error) {
                setResponse('Error: ' + error.message);
            } else {
                setResponse('An unknown error occurred');
            }
            setIsDeploying(false);
        }
    };

    const handleLoginSuccess = () => {
        window.location.reload();
    };

    return (
        <div className={styles.container}>
            <Header />
            <aside className={styles.sidebar}>
                <nav>
                    <a href="/api/helm/deploy">Helm Deploy</a>
                    <a href="/api/helm/releases">Helm Releases</a>
                    <a href="/api/helm/status">Helm Status</a>
                    <div className={styles.bottomNav}>
                        <a href="/dashboard">Dashboard</a>
                    </div>
                </nav>
            </aside>
            <main className={styles.main}>
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
                        <button type="submit" className={styles.submitButton} disabled={isDeploying}>
                            {isDeploying ? (
                                <>
                                    <span>Deploying</span>
                                    <span className={styles.spinner}></span>
                                </>
                            ) : (
                                'Deploy'
                            )}
                        </button>
                    </form>
                    <div className={styles.jsonInput}>
                        <label>Or provide JSON payload</label>
                        <textarea value={jsonPayload} onChange={handleJsonChange} />
                    </div>
                </div>
                <div className={styles.card}>
                    <h1>Response of the Helm Deploy</h1>
                    <div className={styles.console}>
                        <pre>{response}</pre>
                    </div>
                </div>
            </main>

            {showLoginModal && (
                <LoginModal
                    onClose={() => setShowLoginModal(false)}
                    onLoginSuccess={handleLoginSuccess}
                />
            )}
        </div>
    );
};

export default withAuth(HelmDeploy);
