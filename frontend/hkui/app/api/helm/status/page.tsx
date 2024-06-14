'use client';

import React, { useState } from 'react';
import withAuth from '@/app/lib/withAuth';
import Header from '@/app/lib/Header';
import styles from '@/app/styles/HelmStatus.module.css';
import getHelmStatus from '@/app/lib/api/getHelmStatus';
import LoginModal from '@/app/lib/LoginModal';

interface HelmStatusInfo {
    [key: string]: string;
}

interface HelmStatusResponse {
    Name: string;
    Namespace: string;
    Info: HelmStatusInfo;
}

const HelmStatus: React.FC = () => {
    const [statusFormData, setStatusFormData] = useState({
        name: '',
        namespace: '',
    });
    const [helmStatus, setHelmStatus] = useState<HelmStatusResponse | null>(null);
    const [statusError, setStatusError] = useState('');
    const [showLoginModal, setShowLoginModal] = useState(false);

    const handleStatusChange = (e: { target: { name: string; value: string } }) => {
        setStatusFormData({
            ...statusFormData,
            [e.target.name]: e.target.value,
        });
    };

    const fetchHelmStatus = async (name: string, namespace: string) => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setStatusError('No authentication token found');
                setShowLoginModal(true);
                return;
            }

            const data = await getHelmStatus(name, namespace, token);
            setHelmStatus(data);
            setStatusError('');
        } catch (error: unknown) {
            if (error instanceof Error) {
                setStatusError('Error: ' + error.message);
            } else {
                setStatusError('An unknown error occurred');
            }
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
                    <h1>Query Helm Status</h1>
                    <div className={styles.formGroup}>
                        <label>Name</label>
                        <input
                            type="text"
                            name="name"
                            value={statusFormData.name}
                            onChange={handleStatusChange}
                            placeholder="Enter the name"
                            required
                        />
                    </div>
                    <div className={styles.formGroup}>
                        <label>Namespace</label>
                        <input
                            type="text"
                            name="namespace"
                            value={statusFormData.namespace}
                            onChange={handleStatusChange}
                            placeholder="Enter the namespace"
                            required
                        />
                    </div>
                    <button onClick={() => fetchHelmStatus(statusFormData.name, statusFormData.namespace)} className={styles.submitButton}>
                        Get Status
                    </button>
                    {statusError && <p className={styles.error}>{statusError}</p>}
                    {helmStatus && (
                        <div className={styles.statusCard}>
                            <h2>Helm Status</h2>
                            <table className={styles.statusTable}>
                                <tbody>
                                {Object.entries(helmStatus.Info).map(([key, value]) => (
                                    <tr key={key}>
                                        <td><strong>{key}</strong></td>
                                        <td>{value}</td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    )}
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

export default withAuth(HelmStatus);
