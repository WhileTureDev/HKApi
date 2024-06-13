// API page
'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link'; // Import Link component
import withAuth from '@/app/lib/withAuth'; // Adjust the import path as necessary
import styles from '@/app/styles/Api.module.css';

const APIPage: React.FC = () => {
    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div className={styles.logo}>HKUI</div>
                <div className={styles.userProfile}>
                    <img src="/profile.png" alt="User Profile" />
                    {/* User dropdown logic can be reused here */}
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
                {/* Content will be based on the selected link */}
                <section className={styles.content}>
                    <h1>Welcome to the API page</h1>
                    {/* Placeholder content */}
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

export default withAuth(APIPage);
