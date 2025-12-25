import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Production optimizations
  compress: true,
  poweredByHeader: false,
  
  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [],
    minimumCacheTTL: 60, // Cache images for 60 seconds
  },
  
  // Bundle optimization
  experimental: {
    optimizePackageImports: ['lucide-react'], // Tree-shake icon library
  },
  
  // Output optimization
  output: 'standalone', // Optimize for production deployment

  // Security headers
  async headers() {
    const isProduction = process.env.NODE_ENV === 'production';
    
    // Build connect-src directive dynamically based on API URL
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const connectSrc = [
      "'self'",
      "https://api.vercel.com",
      "https://*.vercel.app",
      "https://*.railway.app", // Allow all Railway deployments
    ];
    
    // Add specific API URL if set (for additional security)
    if (apiUrl) {
      try {
        const url = new URL(apiUrl);
        // Add the origin (protocol + hostname) to connect-src
        const origin = `${url.protocol}//${url.hostname}`;
        if (!connectSrc.includes(origin)) {
          connectSrc.push(origin);
        }
      } catch (e) {
        // Invalid URL, skip
      }
    }
    
    // In development, allow localhost
    if (!isProduction) {
      connectSrc.push("http://localhost:8000", "http://localhost:3000");
    }
    
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin'
          },
          // Content Security Policy
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://vercel.live", // Next.js requires unsafe-eval in dev
              "style-src 'self' 'unsafe-inline'", // Tailwind requires unsafe-inline
              "img-src 'self' data: https: blob:",
              "font-src 'self' data:",
              `connect-src ${connectSrc.join(' ')}`,
              "frame-ancestors 'self'",
              "base-uri 'self'",
              "form-action 'self'",
            ].join('; ')
          },
          // HSTS (HTTP Strict Transport Security) - only in production
          ...(isProduction ? [{
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains; preload'
          }] : []),
          // Permissions Policy
          {
            key: 'Permissions-Policy',
            value: [
              'camera=()',
              'microphone=()',
              'geolocation=()',
              'interest-cohort=()',
            ].join(', ')
          },
        ],
      },
    ];
  },
};

export default nextConfig;
