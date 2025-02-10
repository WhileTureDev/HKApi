/**
 * Validation utilities for the authentication system.
 * Contains functions for validating user input in forms.
 */

/**
 * Validates a password against security requirements.
 * Requirements:
 * - Minimum 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one number
 * - At least one special character (!@#$%^&*)
 *
 * @param password - The password to validate
 * @returns Object containing validation result and any error messages
 */
export const validatePassword = (password: string): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];
    
    if (password.length < 8) {
        errors.push('Password must be at least 8 characters long');
    }
    if (!/[A-Z]/.test(password)) {
        errors.push('Password must contain at least one uppercase letter');
    }
    if (!/[a-z]/.test(password)) {
        errors.push('Password must contain at least one lowercase letter');
    }
    if (!/[0-9]/.test(password)) {
        errors.push('Password must contain at least one number');
    }
    if (!/[!@#$%^&*]/.test(password)) {
        errors.push('Password must contain at least one special character (!@#$%^&*)');
    }

    return {
        isValid: errors.length === 0,
        errors
    };
};

/**
 * Validates an email address format.
 * Uses a simple regex pattern to check for basic email format:
 * - Must contain @ symbol
 * - Must have text before and after @
 * - Must have a domain extension
 *
 * @param email - The email address to validate
 * @returns boolean indicating if the email format is valid
 */
export const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

/**
 * Validates a username against the following rules:
 * - Minimum 3 characters
 * - Only allows letters, numbers, underscores, and hyphens
 * - No spaces or special characters
 *
 * @param username - The username to validate
 * @returns Object containing validation result and any error message
 */
export const validateUsername = (username: string): { isValid: boolean; error?: string } => {
    if (username.length < 3) {
        return { isValid: false, error: 'Username must be at least 3 characters long' };
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
        return { isValid: false, error: 'Username can only contain letters, numbers, underscores, and hyphens' };
    }
    return { isValid: true };
};
