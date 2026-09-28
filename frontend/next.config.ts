import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a self-contained .next/standalone build for the production Docker image
  output: 'standalone',

  // Allow Server Actions from RunPod proxy
  experimental: {
    serverActions: {
      allowedOrigins: [
        'admin.ais-asu.com',
        'localhost:3000',
      ],
    },
  },
  
  async rewrites() {
    // In development, send /api calls that no Next.js route handles to the backend.
    // In production nginx does this routing. Fallback rewrites run after dynamic routes,
    // so NextAuth's /api/auth/* handlers still win.
    if (process.env.NODE_ENV === 'development') {
      return {
        beforeFiles: [],
        afterFiles: [],
        fallback: [
          {
            source: '/api/:path*',
            destination: `${process.env.BACKEND_URL || 'http://localhost:5000'}/api/:path*`,
          },
        ],
      };
    }
    return [];
  },

  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
        ],
      },
    ];
  },
  
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn.discordapp.com',
        pathname: '/avatars/**',
      },
    ],
  },
};

export default nextConfig;
