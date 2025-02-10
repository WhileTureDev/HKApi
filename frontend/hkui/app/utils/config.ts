// Deprecated: Keeping for potential future use
export const API_URL = '/api/proxy';

export function getApiEndpoint(path: string): string {
  // Remove leading slash from path if present, and ensure it starts with a slash
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  
  return `${API_URL}${cleanPath}`;
}
