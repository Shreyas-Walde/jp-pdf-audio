/** @type {import('next').NextConfig} */
const nextConfig = {

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
