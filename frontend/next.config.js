/** @type {import('next').NextConfig} */
const nextConfig = {
  skipTrailingSlashRedirect: true,
  // Default proxy body limit is 10MB which truncates video uploads.
  // Backend enforces its own 500MB cap in content.py (MAX_UPLOAD_BYTES).
  experimental: {
    proxyClientMaxBodySize: "500mb",
  },
  async rewrites() {
    return [
      // Preserve trailing slash variants first so the proxy doesn't strip them
      // (FastAPI redirects /courses → /courses/ which drops the Authorization header).
      { source: "/api/:path*/", destination: "http://localhost:8000/api/:path*/" },
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
      { source: "/ws/:path*", destination: "http://localhost:8000/ws/:path*" },
      { source: "/uploads/:path*", destination: "http://localhost:8000/uploads/:path*" },
    ];
  },
};

module.exports = nextConfig;
