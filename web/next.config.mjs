/** @type {import('next').NextConfig} */
const nextConfig = {
    // Enable static export for cheap hosting
    output: 'standalone',

    // Configure static file serving for audio files
    async rewrites() {
        return [
            {
                source: '/audio/:path*',
                destination: '/api/audio/:path*',
            },
        ];
    },
};

export default nextConfig;
