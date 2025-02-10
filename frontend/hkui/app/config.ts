// Environment variables with defaults
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/proxy';

// Other configuration variables can be added here
export const config = {
    apiBaseUrl: API_BASE_URL,
    // Add other configuration variables as needed
};
