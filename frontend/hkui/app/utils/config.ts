export const getApiUrl = () => {
  return process.env.NEXT_PUBLIC_API_URL || 'https://hkapi.dailytoolset.com';
};

export const getApiEndpoint = (path: string) => {
  return `${getApiUrl()}${path}`;
};
