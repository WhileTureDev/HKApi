'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Head from 'next/head';
import Link from 'next/link';
import styles from '@/app/styles/Home.module.css';
import LoadingSpinner from '@/app/components/LoadingSpinner';

const Home = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogin = async (e: { preventDefault: () => void; }) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          password,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Invalid username or password');
      }

      router.push('/dashboard');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (!mounted) {
    return null; // Prevent flash of unstyled content
  }

  return (
    <div className={styles.container}>
      <Head>
        <title>Kubernetes API Platform</title>
        <meta name="description" content="Create and manage temporary Kubernetes environments." />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header className={styles.header}>
        <div className={styles.logo}>HKUI</div>
        
        {/* Mobile menu button */}
        <button 
          className={styles.mobileMenuButton}
          onClick={() => setShowMobileMenu(!showMobileMenu)}
          aria-label="Toggle menu"
        >
          <div className={`${styles.hamburger} ${showMobileMenu ? styles.open : ''}`}>
            <span></span>
            <span></span>
            <span></span>
          </div>
        </button>

        {/* Navigation */}
        <nav className={`${styles.nav} ${showMobileMenu ? styles.showMobileMenu : ''}`}>
          <ul className={styles.navLinks}>
            <li><Link href="/" className={styles.activeLink}>Home</Link></li>
            <li><Link href="/docs">API Docs</Link></li>
            <li><Link href="/support">Support</Link></li>
            <li><Link href="/login">Login</Link></li>
            <li><Link href="/signup" className={styles.signupButton}>Sign Up</Link></li>
          </ul>
        </nav>
      </header>

      <main className={styles.main}>
        <section className={styles.hero}>
          <h1 className={styles.title}>Welcome to HKUI</h1>
          <p className={styles.description}>Create and manage temporary Kubernetes environments with ease.</p>
          <div className={styles.heroButtons}>
            <Link href="/signup" className={styles.primaryButton}>
              Get Started
            </Link>
            <Link href="/docs" className={styles.secondaryButton}>
              Learn More
            </Link>
          </div>
        </section>

        <section className={styles.formSection}>
          <div className={styles.formCard}>
            <h2>Login to Your Account</h2>
            <form onSubmit={handleLogin} className={styles.form}>
              <div className={styles.formGroup}>
                <label htmlFor="username">Username</label>
                <input
                  id="username"
                  type="text"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={loading}
                  className={error ? styles.inputError : ''}
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="password">Password</label>
                <div className={styles.passwordInput}>
                  <input
                    id="password"
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={loading}
                    className={error ? styles.inputError : ''}
                  />
                </div>
              </div>

              {error && (
                <div className={styles.errorMessage}>
                  <svg className={styles.errorIcon} viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className={`${styles.loginButton} ${loading ? styles.loading : ''}`}
              >
                {loading ? (
                  <span className={styles.loadingWrapper}>
                    <LoadingSpinner size="small" />
                    <span>Logging in...</span>
                  </span>
                ) : (
                  'Login'
                )}
              </button>

              <div className={styles.formDivider}>
                <span>or</span>
              </div>

              <p className={styles.signupPrompt}>
                Don't have an account?{' '}
                <Link href="/signup" className={styles.signupLink}>
                  Sign up now
                </Link>
              </p>
            </form>
          </div>
        </section>

        <section className={styles.features}>
          <h2>Why Choose HKUI?</h2>
          <div className={styles.featureGrid}>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>🚀</div>
              <h3>Quick Setup</h3>
              <p>Deploy your applications in minutes, not hours.</p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>🛡️</div>
              <h3>Secure by Default</h3>
              <p>Enterprise-grade security out of the box.</p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>📊</div>
              <h3>Real-time Monitoring</h3>
              <p>Monitor your deployments in real-time.</p>
            </div>
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <p>&copy; 2025 HKUI. All rights reserved.</p>
          <div className={styles.footerLinks}>
            <Link href="/privacy">Privacy Policy</Link>
            <Link href="/terms">Terms of Service</Link>
            <Link href="/contact">Contact Us</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
