import type { NextConfig } from 'next';
const nextConfig: NextConfig = { distDir: process.env.MODELFORGE_BUILD_DIR || '.next', devIndicators: false, cacheComponents: true, partialPrefetching: true };
export default nextConfig;
