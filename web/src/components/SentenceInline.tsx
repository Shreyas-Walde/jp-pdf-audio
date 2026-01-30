'use client';

import AudioPlayer from './AudioPlayer';

interface SentenceInlineProps {
    id: string;
    text: string;
    audioPath: string | null;
    isActive?: boolean;
    onPlay?: () => void;
}

/**
 * Inline sentence component with minimal audio button
 */
export default function SentenceInline({
    id,
    text,
    audioPath,
    isActive = false,
    onPlay
}: SentenceInlineProps) {
    // Convert relative audio path to full URL
    const audioUrl = audioPath ? `/audio/sentences/${audioPath}` : null;

    return (
        <div
            className={`sentence-inline ${isActive ? 'is-active' : ''}`}
            data-sentence-id={id}
        >
            <span className="sentence-inline__text">{text}</span>
            {audioUrl && (
                <span className="sentence-inline__audio">
                    <AudioPlayer
                        src={audioUrl}
                        compact
                        iconOnly
                        onEnded={onPlay}
                    />
                </span>
            )}
        </div>
    );
}
