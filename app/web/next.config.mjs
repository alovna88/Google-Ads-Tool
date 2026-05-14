/** @type {import('next').NextConfig} */

// In Docker Compose, the api is reachable inside the network at
// http://api:8000. In Fly.io production we set API_INTERNAL_URL to the
// API app's internal hostname. Outside any container, fall back to
// localhost:8000. Browser requests are always same-origin (/api/*).
const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://api:8000";

const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  experimental: {
    typedRoutes: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_INTERNAL_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
