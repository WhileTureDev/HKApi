'use client';

import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/navigation';
import styles from './styles/Home.module.css';

const Home = () => {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    // This ensures any client-side only code runs after the component is mounted
  }, []);

  const handleLogin = async (e: { preventDefault: () => void; }) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/token`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: email,
          password,
        }),
      });

      if (!response.ok) {
        setError('Login failed: Invalid email or password')
      }

      const data = await response.json();
      localStorage.setItem('token', data.token);
      router.push('/dashboard');
    } catch (error) {
      setError('Invalid email or password');
    }
  };

  return (
      <div className={styles.container}>
        <Head>
          <title>Kubernetes API Platform</title>
          <meta name="description" content="Create and manage temporary Kubernetes environments." />
          <link rel="icon" href="/favicon.ico" />
        </Head>

        <header className={styles.header}>
          <div className={styles.logo}>HKUI</div>
          <nav>
            <ul className={styles.navLinks}>
              <li><a href="#">Home</a></li>
              <li><a href="#">API Docs</a></li>
              <li><a href="#">Support</a></li>
              <li><a href="#">Login</a></li>
              <li><a href="#">Sign Up</a></li>
            </ul>
          </nav>
        </header>

        <main className={styles.main}>
          <section className={styles.formSection}>
            <div className={styles.formCard}>
              <h2>Login</h2>
              {error && <p className={styles.error}>{error}</p>}
              <form onSubmit={handleLogin}>
                <input
                    type="User"
                    placeholder="User"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                <button type="submit" className={styles.loginButton}>Login</button>
              </form>
              <div className={styles.socialLogin}>
                <div className={styles.socialIcons}>
                  <a href="#" className={styles.socialIcon}><i className="fab fa-facebook-f"></i></a>
                  <a href="#" className={styles.socialIcon}><i className="fab fa-twitter"></i></a>
                  <a href="#" className={styles.socialIcon}><i className="fab fa-google"></i></a>
                </div>
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

export default Home;
