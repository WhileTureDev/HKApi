// api/dashboard/page.tsx

'use client';

import React from 'react';
import Link from 'next/link';
import Header from '@/app/lib/Header'; // Import the shared Header component
import styles from '@/app/styles/shared.module.css'; // Import shared CSS

const Dashboard: React.FC = () => {
    return (
        <div className={styles.container}>
            <Header />
            <aside className={styles.sidebar}>
                <nav>
                    <Link href="/dashboard">Dashboard</Link>
                    <Link href="/api/helm">Helm</Link>
                    <Link href="/api/deployment">Deployments</Link>
                    <div className={styles.bottomNav}>
                        <Link href="/">Home</Link>
                    </div>
                </nav>
            </aside>
            <main className={styles.main}>
                <section className={styles.content}>
                    <div className={styles.card}>
                        <h1>Dashboard</h1>
                        <p>Welcome to the Kubernetes API Platform Dashboard.</p>
                        {/* Add dashboard content here */}
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

export default Dashboard;
