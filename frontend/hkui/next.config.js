/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: 'http://hkapi.dailytoolset.com',
    NEXT_PUBLIC_LOCAL_API_URL: 'http://localhost:8000'
  },
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8000/api/v1/:path*'
      }
    ]
  }
}

module.exports = nextConfig
