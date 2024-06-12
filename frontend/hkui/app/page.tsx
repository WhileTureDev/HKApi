import React from 'react';
import Head from 'next/head';
import styles from './styles/Home.module.css';

const Home = () => {
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
              <li><a href="#">Dashboard</a></li>
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
              <form>
                <input type="email" placeholder="Email" required />
                <input type="password" placeholder="Password" required />
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
