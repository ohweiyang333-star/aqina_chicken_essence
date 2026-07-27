import type { NextConfig } from "next";
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin(
  './src/i18n/request.ts'
);

const nextConfig: NextConfig = {
  output: 'standalone',
  async redirects() {
    // The v2/v3/v4 landing experiments are retired. They were still publicly
    // reachable and /v2 was quoting the old price scheme (SGD 75 / 149 / 219 and a
    // "free shipping over SGD 70" threshold) to anyone who landed on it. Send that
    // traffic to the live offer instead of leaving stale prices in the wild.
    const retiredLandings = ['v2', 'v3', 'v4', 'V4'].flatMap((v) => [
      { source: `/${v}`, destination: '/', permanent: true },
      { source: `/${v}/:path*`, destination: '/', permanent: true },
    ]);

    return [
      ...retiredLandings,
      // Locale-prefixed variants of the retired v3 route.
      { source: '/:locale(en|zh)/v3', destination: '/:locale', permanent: true },
      { source: '/:locale(en|zh)/v3/:path*', destination: '/:locale', permanent: true },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'firebasestorage.googleapis.com',
      },
    ],
  },
};

export default withNextIntl(nextConfig);
