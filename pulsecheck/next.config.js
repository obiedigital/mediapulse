/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Keep the participant bundle lean: no experimental heavy features,
  // no image optimization service dependency (we don't ship photos in-app).
  images: {
    unoptimized: true,
  },
  // pdfkit/fontkit read font metric (.afm) files off disk relative to their
  // own package directory at runtime. Webpack-bundling them into the route's
  // server chunk breaks that lookup, so keep them external (loaded via plain
  // require() from node_modules instead) for the PDF export route.
  experimental: {
    serverComponentsExternalPackages: ["pdfkit", "fontkit"],
  },
};

module.exports = nextConfig;
