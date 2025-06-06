import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "/selfhydro",
  images: {
    unoptimized: true,
  },
  assetPrefix: "/selfhydro/",
};

export default nextConfig;
