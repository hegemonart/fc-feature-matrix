import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // D-12 prereq — exposed at build time so <HeaderBar> (plan 02-04) renders the
  // build-date span without hydration mismatch (server + client both see the
  // same ISO date slice baked into the bundle).
  env: {
    BUILD_DATE: new Date().toISOString().slice(0, 10),
  },
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
