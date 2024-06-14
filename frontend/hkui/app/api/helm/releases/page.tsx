'use client';

import React, { useState, useEffect } from 'react';
import withAuth from '@/app/lib/withAuth';
import Header from '@/app/lib/Header';
import styles from '@/app/styles/HelmReleases.module.css';
import listHelmReleases from '@/app/lib/api/listHelmReleases';
import deleteHelmRelease from '@/app/lib/api/deleteHelmRelease';
import LoginModal from '@/app/lib/LoginModal';

interface HelmRelease {
    Name: string;
    Namespace: string;
    Status: string;
    Revision: string;
    Updated: string;
}

const HelmReleases: React.FC = () => {
    const [namespace, setNamespace] = useState('');
    const [releases, setReleases] = useState<HelmRelease[]>([]);
    const [releaseError, setReleaseError] = useState('');
    const [selectedReleases, setSelectedReleases] = useState<HelmRelease[]>([]);
    const [showConfirmDialog, setShowConfirmDialog] = useState(false);
    const [showDeleteAllConfirmDialog, setShowDeleteAllConfirmDialog] = useState(false);
    const [releaseToDelete, setReleaseToDelete] = useState<HelmRelease | null>(null);
    const [showLoginModal, setShowLoginModal] = useState(false);

    const handleNamespaceChange = (e: { target: { value: string } }) => {
        setNamespace(e.target.value);
    };

    const fetchReleases = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setReleaseError('No authentication token found');
                setShowLoginModal(true);
                return;
            }

            const data = await listHelmReleases(namespace, token);
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
            } else {
                setReleaseError('An unknown error occurred');
            }
        }
    };

    const handleSelectRelease = (release: HelmRelease) => {
        const newSelectedReleases = selectedReleases.includes(release)
            ? selectedReleases.filter((r) => r !== release)
            : [...selectedReleases, release];
        setSelectedReleases(newSelectedReleases);
    };

    const handleDeleteRelease = (release: HelmRelease) => {
        setReleaseToDelete(release);
        setShowConfirmDialog(true);
    };

    const confirmDeleteRelease = async () => {
        if (!releaseToDelete) return;

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setReleaseError('No authentication token found');
                setShowLoginModal(true);
                return;
            }

            await deleteHelmRelease(releaseToDelete.Name, releaseToDelete.Namespace, token);
            setReleases((prevReleases) => prevReleases.filter((r) => r !== releaseToDelete));
            setSelectedReleases((prevSelected) => prevSelected.filter((r) => r !== releaseToDelete));
        } catch (error: unknown) {
            if (error instanceof Error) {
                setReleaseError('Error: ' + error.message);
            } else {
                setReleaseError('An unknown error occurred');
            }
        } finally {
            setShowConfirmDialog(false);
            setReleaseToDelete(null);
        }
    };

    const handleDeleteSelectedReleases = () => {
        setShowDeleteAllConfirmDialog(true);
    };

    const confirmDeleteAllReleases = async () => {
        for (const release of selectedReleases) {
            await deleteRelease(release);
        }
        setShowDeleteAllConfirmDialog(false);
    };

    const deleteRelease = async (release: HelmRelease) => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                setReleaseError('No authentication token found');
                setShowLoginModal(true);
                return;
            }

            await deleteHelmRelease(release.Name, release.Namespace, token);
            setReleases((prevReleases) => prevReleases.filter((r) => r !== release));
            setSelectedReleases((prevSelected) => prevSelected.filter((r) => r !== release));
        } catch (error: unknown) {
            if (error instanceof Error) {
                setReleaseError('Error: ' + error.message);
            } else {
                setReleaseError('An unknown error occurred');
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
                        {selectedReleases.length > 1 && (
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
                                            {selectedReleases.length <= 1 && selectedReleases.includes(release) && (
                                                <button onClick={() => handleDeleteRelease(release)} className={styles.deleteButton}>
                                                    Delete
                                                </button>
                                            )}
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
            </main>

            {showConfirmDialog && (
                <div className={styles.confirmDialogOverlay}>
                    <div className={styles.confirmDialog}>
                        <h2>Confirm Deletion</h2>
                        <p>Are you sure you want to delete the release "{releaseToDelete?.Name}" in namespace "{releaseToDelete?.Namespace}"?</p>
                        <div className={styles.confirmDialogActions}>
                            <button onClick={confirmDeleteRelease} className={styles.confirmButton}>Yes</button>
                            <button onClick={() => setShowConfirmDialog(false)} className={styles.cancelButton}>No</button>
                        </div>
                    </div>
                </div>
            )}

            {showDeleteAllConfirmDialog && (
                <div className={styles.confirmDialogOverlay}>
                    <div className={styles.confirmDialog}>
                        <h2>Confirm Deletion</h2>
                        <p>Are you sure you want to delete all selected releases?</p>
                        <div className={styles.confirmDialogActions}>
                            <button onClick={confirmDeleteAllReleases} className={styles.confirmButton}>Yes</button>
                            <button onClick={() => setShowDeleteAllConfirmDialog(false)} className={styles.cancelButton}>No</button>
                        </div>
                    </div>
                </div>
            )}

            {showLoginModal && (
                <LoginModal
                    onClose={() => setShowLoginModal(false)}
                    onLoginSuccess={handleLoginSuccess}
                />
            )}
        </div>
    );
};

export default withAuth(HelmReleases);
