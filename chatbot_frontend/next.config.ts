import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/static/**',
      },
      {
        protocol: 'https',
        hostname: '*.fal.media',
      },
      {
        protocol: 'https',
        hostname: 'fal.media',
      },
      {
        protocol: 'https',
        hostname: 'pbxt.replicate.delivery',
      },
      {
        protocol: 'https',
        hostname: 'replicate.delivery',
      }
    ],
    unoptimized: false,
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY' // or SAMEORIGIN
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: http://localhost:8000; connect-src 'self' http://localhost:8000 ws://localhost:8000; font-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none';"
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), browsing-topics=()'
          }
        ]
      }
    ];
  }
};

export default nextConfig;
