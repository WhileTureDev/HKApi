'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import withAuth from '@/app/lib/withAuth'; // Adjust the import path as necessary
import styles from '@/app/styles/Dashboard.module.css';

const Dashboard: React.FC = () => {
    const router = useRouter();
    const [showDropdown, setShowDropdown] = useState(false);

    const handleLogout = () => {
        localStorage.removeItem('token');
        router.push('/');
    };

    const toggleDropdown = () => {
        setShowDropdown((prev) => !prev);
    };

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div className={styles.logo}>HKUI</div>
                <div className={styles.userProfile} onClick={toggleDropdown}>
                    <img src="/profile.png" alt="User Profile" />
                    {showDropdown && (
                        <div className={styles.dropdownMenu}>
                            <a href="/profile">Profile</a>
                            <a href="/settings">User Settings</a>
                            <button onClick={handleLogout}>Logout</button>
                        </div>
                    )}
                </div>
            </header>

            <aside className={styles.sidebar}>
                <nav>
                    <a href="#">Projects</a>
                    <a href="#">Settings</a>
                    <a href="#">Logs</a>
                    <a href="#">Alerts</a>
                </nav>
            </aside>

            <main className={styles.main}>
                <section className={styles.metrics}>
                    <div className={styles.metricCard}>
                        <h3>Active Environments</h3>
                        <p>35</p>
                    </div>
                    <div className={styles.metricCard}>
                        <h3>Nodes</h3>
                        <p>120</p>
                    </div>
                    <div className={styles.metricCard}>
                        <h3>CPU Usage</h3>
                        <p>45%</p>
                    </div>
                    <div className={styles.metricCard}>
                        <h3>Memory Usage</h3>
                        <p>60%</p>
                    </div>
                </section>

                <section className={styles.charts}>
                    <div className={styles.chartCard}>
                        <h3>CPU Usage</h3>
                        <img src="/cpu-chart.png" alt="CPU Usage Chart" />
                    </div>
                    <div className={styles.chartCard}>
                        <h3>Memory Usage</h3>
                        <img src="/memory-chart.png" alt="Memory Usage Chart" />
                    </div>
                </section>

                <section className={styles.activity}>
                    <h3>Recent Activity</h3>
                    <ul>
                        <li>Environment created - June 10, 2024</li>
                        <li>Node added to cluster - June 9, 2024</li>
                        <li>Resource usage updated - June 8, 2024</li>
                    </ul>
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

export default withAuth(Dashboard);
