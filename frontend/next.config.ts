import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // recharts 3.x ships as ESM; without this the SWC worker crashes in dev
  transpilePackages: ["recharts"],
};

export default nextConfig;
