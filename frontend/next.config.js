/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enable PostCSS processing
  webpack: (config) => {
    return config;
  },
};

module.exports = nextConfig;
