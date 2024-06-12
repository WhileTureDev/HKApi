import React from 'react';
import Head from 'next/head';
import styles from '../styles/Dashboard.module.css';

const Dashboard = () => {
    return (
        <div className={styles.container}>
            <Head>
                <title>Dashboard - Kubernetes API Platform</title>
                <meta name="description" content="Monitor and manage your Kubernetes environments." />
                <link rel="icon" href="/favicon.ico" />
            </Head>

            <header className={styles.header}>
                <div className={styles.logo}>KubeEnv</div>
                <nav className={styles.nav}>
                    <a href="#">Dashboard</a>
                    <a href="#">Projects</a>
                    <a href="#">Settings</a>
                </nav>
                <div className={styles.userProfile}>
                    <img src="/profile.png" alt="User Profile" />
                </div>
            </header>

            <aside className={styles.sidebar}>
                <nav>
                    <a href="#">Dashboard</a>
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
                <p>&copy; 2024 KubeEnv. All rights reserved.</p>
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
