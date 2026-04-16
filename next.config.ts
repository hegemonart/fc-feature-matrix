import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: '/analytics',
        destination: '/admin/analytics',
        permanent: true, // 308
      },
    ];
  },
};

export default nextConfig;
