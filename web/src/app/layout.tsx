import type { Metadata } from 'next';
import { Noto_Sans_JP } from 'next/font/google';
import './globals.css';

const notojp = Noto_Sans_JP({
    subsets: ['latin'],
    weight: ['400', '500', '700'],
    variable: '--font-sans',
    display: 'swap',
});

export const metadata: Metadata = {
    title: '日本語PDF音声リーダー | Japanese PDF Audio Reader',
    description: 'Listen to Japanese textbooks with sentence-level audio playback',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="ja" className={notojp.variable}>
            <body>{children}</body>
        </html>
    );
}
