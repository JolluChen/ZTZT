/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL + '/:path*',
      },
    ];
  },
  images: {
    domains: ['localhost', '127.0.0.1'],
  },
  webpack: (config) => {
    config.resolve.fallback = { fs: false, net: false, tls: false };
    return config;
  },
  eslint: {
    // 在开发期间忽略ESLint错误
    ignoreDuringBuilds: true,
  },
  typescript: {
    // 在开发期间忽略TypeScript错误
    ignoreBuildErrors: true,
  },
};

module.exports = nextConfig;
