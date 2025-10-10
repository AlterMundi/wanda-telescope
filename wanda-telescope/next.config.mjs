/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:5000/api/:path*",
      },
      {
        source: "/video_feed",
        destination: "http://localhost:5000/video_feed",
      },
      {
        source: "/socket.io/:path*",
        destination: "http://localhost:5000/socket.io/:path*",
      },
    ]
  },
}

export default nextConfig
