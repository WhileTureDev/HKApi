'use client';

import React, { useState } from 'react';
import styles from '@/app/styles/LoginModal.module.css';

interface LoginModalProps {
    onClose: () => void;
    onLoginSuccess: () => void;
}

const LoginModal: React.FC<LoginModalProps> = ({ onClose, onLoginSuccess }) => {
    const [loginForm, setLoginForm] = useState({ username: '', password: '' });
    const [loginError, setLoginError] = useState('');

    const handleLoginChange = (e: { target: { name: any; value: any; }; }) => {
        setLoginForm({
            ...loginForm,
            [e.target.name]: e.target.value,
        });
    };

    const handleLogin = async (e: { preventDefault: () => void; }) => {
        e.preventDefault();
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json',
                },
                body: new URLSearchParams({
                    username: loginForm.username,
                    password: loginForm.password,
                }),
            });

            if (!res.ok) {
                setLoginError('Login failed');
                return;
            }

            const data = await res.json();
            localStorage.setItem('token', data.access_token);
            setLoginError('');
            onLoginSuccess();
            onClose();
        } catch (error: unknown) {
            if (error instanceof Error) {
                setLoginError('Error: ' + error.message);
                console.error('Error message:', error.message);
            } else {
                setLoginError('An unknown error occurred');
                console.error('Unknown error:', error);
            }
        }
    };

    return (
        <div className={styles.loginModalOverlay}>
            <div className={styles.loginModal}>
                <h2>Login</h2>
                <form onSubmit={handleLogin}>
                    <input
                        type="text"
                        name="username"
                        value={loginForm.username}
                        onChange={handleLoginChange}
                        placeholder="User"
                        required
                        className={styles.loginInput}
                    />
                    <input
                        type="password"
                        name="password"
                        value={loginForm.password}
                        onChange={handleLoginChange}
                        placeholder="Password"
                        required
                        className={styles.loginInput}
                    />
                    {loginError && <p className={styles.error}>{loginError}</p>}
                    <button type="submit" className={styles.loginButton}>Login</button>
                </form>
            </div>
        </div>
    );
};

export default LoginModal;
