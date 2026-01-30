'use client';

import AudioPlayer from './AudioPlayer';

interface SentenceRowProps {
    id: string;
    index: number;
    text: string;
    audioPath: string | null;
    isActive?: boolean;
    onPlay?: () => void;
}

/**
 * A single sentence row with text and audio playback
 */
export default function SentenceRow({
    id,
    index,
    text,
    audioPath,
    isActive = false,
    onPlay
}: SentenceRowProps) {
    // Convert relative audio path to full URL
    const audioUrl = audioPath ? `/audio/sentences/${audioPath}` : null;

    return (
        <div
            className={`sentence-row ${isActive ? 'sentence-row--active' : ''}`}
            data-sentence-id={id}
        >
            <span className="sentence-row__index">{index + 1}</span>

            <div className="sentence-row__content">
                <p className="sentence-row__text">{text}</p>
            </div>

            <div className="sentence-row__audio">
                <AudioPlayer
                    src={audioUrl}
                    compact
                    onEnded={onPlay}
                />
            </div>
        </div>
    );
}
