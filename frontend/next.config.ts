import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow Server Actions from RunPod proxy
  experimental: {
    serverActions: {
      allowedOrigins: [
        '8bzhwve1ri5cw2-80.proxy.runpod.net',
        'admin.ais-asu.com',
        'localhost:3000',
      ],
    },
  },
  
  async rewrites() {
    // Only use rewrites in development (docker-compose)
    // In production, nginx handles the routing
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://backend:5000/api/:path*', // Proxy to Backend
        },
      ];
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
