import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // recharts 3.x ships as ESM; without this the SWC worker crashes in dev
  transpilePackages: ["recharts"],
  turbopack: {
    // .claude/launch.json starts this via `npm --prefix psx-fertilizer/frontend run
    // dev` from the D:/khronos repo root, not from this directory -- npm's --prefix
    // resolves *where the script runs* but doesn't chdir the spawned process, so
    // Turbopack's own root inference (which walks up from process.cwd(), not from
    // this config file's location) was landing on D:/khronos. That directory has no
    // node_modules of its own, so every request failed with a real but misleading
    // "Next.js package not found" (confirmed via the panic logs in
    // %TEMP%/next-panic-*.log -- Rust-side resolver, not an actual missing install).
    // D:/khronos also has two OTHER sibling JS projects under psx-fertilizer/
    // (.verify-frontend, "AI Investment Research Platform") with their own
    // package.json/lockfiles, which is exactly the multi-project-root scenario
    // Next's docs warn causes this. Pinning root here removes the guesswork.
    root: path.join(__dirname),
  },
};

export default nextConfig;
