/** @type {import('next').NextConfig} */
// Force rebuild context cache invalidation
const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:5000';

const nextConfig = {
  output: 'standalone',
  devIndicators: false,
  async rewrites() {
    return [
      { source: '/api/:path*', destination: `${backend}/api/:path*` },
      { source: '/health', destination: `${backend}/health` },
      { source: '/docs', destination: `${backend}/docs` },
      { source: '/openapi.json', destination: `${backend}/openapi.json` },
    ];
  },
};

module.exports = nextConfig;
