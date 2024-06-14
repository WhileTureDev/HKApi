// Home page

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Head from 'next/head';
import styles from '@/app/styles/Home.module.css';

const Home = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

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
        setError('Invalid email or password');
        return;
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token); // Ensure this matches the key used in the backend
      console.log('Token stored in localStorage:', data.access_token); // Debug log for stored token
      router.push('/dashboard');
    } catch (error) {
      setError('An unexpected error occurred. Please try again.');
      console.error('Login error:', error); // Debug log for login error
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
              {error && <p className={styles.error}>{error}</p>}
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
