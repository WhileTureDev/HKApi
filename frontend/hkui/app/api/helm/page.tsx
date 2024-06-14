'use client';

import React from 'react';
import Header from '@/app/lib/Header';
import styles from '@/app/styles/HelmMain.module.css';
import withAuth from '@/app/lib/withAuth';

const HelmMain: React.FC = () => {
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
                <div className={styles.welcomeCard}>
                    <h1>Welcome to the Helm Management Interface</h1>
                    <p>Use the menu on the left to navigate to the different Helm functions.</p>
                </div>
            </main>
        </div>
    );
};

export default withAuth(HelmMain);
