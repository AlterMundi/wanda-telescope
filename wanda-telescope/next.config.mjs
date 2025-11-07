/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:5000/api/:path*",
      },
      {
        source: "/video_feed",
        destination: "http://127.0.0.1:5000/video_feed",
      },
      {
        source: "/socket.io/:path*",
        destination: "http://127.0.0.1:5000/socket.io/:path*",
      },
      {
        source: "/captures/:path*",
        destination: "http://127.0.0.1:5000/api/captures/:path*",
      },
    ]
  },
}

export default nextConfig
