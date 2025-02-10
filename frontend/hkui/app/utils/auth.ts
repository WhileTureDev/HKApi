import Cookies from 'js-cookie';

/**
 * Get the authentication token from cookies
 * @returns The JWT token or null if not found
 */
export function getAuthToken(): string | null {
    return Cookies.get('token') || null;
}

/**
 * Set the authentication token in cookies
 * @param token The JWT token to store
 */
export function setAuthToken(token: string): void {
    Cookies.set('token', token, { 
        expires: 7, // 7 days
        sameSite: 'strict',
        secure: process.env.NODE_ENV === 'production'
    });
}

/**
 * Remove the authentication token from cookies
 */
export function removeAuthToken(): void {
    Cookies.remove('token');
}
