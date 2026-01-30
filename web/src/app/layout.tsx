import type { Metadata } from 'next';
import './globals.css';

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
        <html lang="ja">
            <head>
                <link
                    href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap"
                    rel="stylesheet"
                />
            </head>
            <body>{children}</body>
        </html>
    );
}
