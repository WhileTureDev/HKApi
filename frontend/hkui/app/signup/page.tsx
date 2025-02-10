'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { validatePassword, validateEmail, validateUsername } from '@/app/utils/validation';
import styles from '@/app/styles/Auth.module.css';
import LoadingSpinner from '@/app/components/LoadingSpinner';

interface FormData {
  username: string;
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

interface ValidationErrors {
  username?: string;
  email?: string;
  password?: string[];
  confirm_password?: string;
  submit?: string;
}

export default function SignUp() {
  const router = useRouter();
  const [formData, setFormData] = useState<FormData>({
    username: '',
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
  });
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};
    let isValid = true;

    // Username validation
    const usernameValidation = validateUsername(formData.username);
    if (!usernameValidation.isValid) {
      newErrors.username = usernameValidation.error;
      isValid = false;
    }

    // Email validation
    if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
      isValid = false;
    }

    // Password validation
    const passwordValidation = validatePassword(formData.password);
    if (!passwordValidation.isValid) {
      newErrors.password = passwordValidation.errors;
      isValid = false;
    }

    // Confirm password validation
    if (formData.password !== formData.confirm_password) {
      newErrors.confirm_password = 'Passwords do not match';
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear specific error when user starts typing
    setErrors(prev => ({
      ...prev,
      [name]: undefined
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          full_name: formData.full_name,
          email: formData.email,
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to create account');
      }

      // Redirect to login page on success
      router.push('/login?registered=true');
    } catch (err) {
      setErrors(prev => ({
        ...prev,
        submit: err instanceof Error ? err.message : 'An error occurred'
      }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.formCard}>
        <h1>Create an Account</h1>
        <form onSubmit={handleSubmit} className={styles.form} autoComplete="on">
          {errors.submit && (
            <div className={styles.errorMessage}>
              <svg className={styles.errorIcon} viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span>{errors.submit}</span>
            </div>
          )}

          <div className={styles.formGroup}>
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              autoComplete="username"
              value={formData.username}
              onChange={handleChange}
              required
              className={`${errors.username ? styles.inputError : ''} text-gray-900`}
              placeholder="Choose a username"
              style={{ color: '#1f2937' }}
            />
            {errors.username && (
              <p className={styles.errorText}>{errors.username}</p>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="full_name">Full Name</label>
            <input
              type="text"
              id="full_name"
              name="full_name"
              autoComplete="name"
              value={formData.full_name}
              onChange={handleChange}
              required
              className={`${errors.full_name ? styles.inputError : ''} text-gray-900`}
              placeholder="Enter your full name"
              style={{ color: '#1f2937' }}
            />
            {errors.full_name && (
              <p className={styles.errorText}>{errors.full_name}</p>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              autoComplete="email"
              value={formData.email}
              onChange={handleChange}
              required
              className={`${errors.email ? styles.inputError : ''} text-gray-900`}
              placeholder="Enter your email"
              style={{ color: '#1f2937' }}
            />
            {errors.email && (
              <p className={styles.errorText}>{errors.email}</p>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              autoComplete="new-password"
              value={formData.password}
              onChange={handleChange}
              required
              className={`${errors.password ? styles.inputError : ''} text-gray-900`}
              placeholder="Create a password"
              style={{ color: '#1f2937' }}
            />
            {errors.password && (
              <div className={styles.errorList}>
                {errors.password.map((error, index) => (
                  <p key={index} className={styles.errorText}>{error}</p>
                ))}
              </div>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="confirm_password">Confirm Password</label>
            <input
              type="password"
              id="confirm_password"
              name="confirm_password"
              autoComplete="new-password"
              value={formData.confirm_password}
              onChange={handleChange}
              required
              className={`${errors.confirm_password ? styles.inputError : ''} text-gray-900`}
              placeholder="Confirm your password"
              style={{ color: '#1f2937' }}
            />
            {errors.confirm_password && (
              <p className={styles.errorText}>{errors.confirm_password}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`${styles.submitButton} ${loading ? styles.loading : ''}`}
          >
            {loading ? (
              <span className={styles.loadingWrapper}>
                <LoadingSpinner size="small" />
                <span>Creating Account...</span>
              </span>
            ) : (
              'Create Account'
            )}
          </button>

          <p className={styles.switchAuthMode}>
            Already have an account?{' '}
            <Link href="/login">
              Sign in here
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
