/** @type {import('next').NextConfig} */
const runtimeCaching = require('next-pwa/cache');

runtimeCaching.unshift({
  urlPattern: /^https:\/\/.*\.tile\.openstreetmap\.org\/.*/i,
  handler: 'CacheFirst',
  options: {
    cacheName: 'map-tiles',
    expiration: {
      maxEntries: 1000,
      maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
    },
  },
});

// Cache GET requests for crop and recommendation API so the app is
// readable offline (StaleWhileRevalidate — shows cached, fetches fresh).
runtimeCaching.unshift({
  urlPattern: /\/api\/v1\/crops(\/.*)?(\?.*)?$/i,
  handler: 'StaleWhileRevalidate',
  method: 'GET',
  options: {
    cacheName: 'cultivax-crops-cache',
    expiration: {
      maxEntries: 50,
      maxAgeSeconds: 30 * 60, // 30 minutes
    },
    cacheableResponse: { statuses: [0, 200] },
  },
});

runtimeCaching.unshift({
  urlPattern: /\/api\/v1\/crops\/[^/]+\/recommendations(\?.*)?$/i,
  handler: 'StaleWhileRevalidate',
  method: 'GET',
  options: {
    cacheName: 'cultivax-recs-cache',
    expiration: {
      maxEntries: 30,
      maxAgeSeconds: 15 * 60, // 15 minutes
    },
    cacheableResponse: { statuses: [0, 200] },
  },
});

const withPWA = require('next-pwa')({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
  customWorkerDir: 'src/worker',
  runtimeCaching,
});

const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

module.exports = withPWA(nextConfig);
