'use client';

import { useRef, useState, useEffect } from 'react';

interface AudioPlayerProps {
    src: string | null;
    onEnded?: () => void;
    autoPlay?: boolean;
    compact?: boolean;
    iconOnly?: boolean;
}

/**
 * Reusable audio player component with play/pause controls
 */
export default function AudioPlayer({
    src,
    onEnded,
    autoPlay = false,
    compact = false,
    iconOnly = false
}: AudioPlayerProps) {
    const audioRef = useRef<HTMLAudioElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [progress, setProgress] = useState(0);
    const [duration, setDuration] = useState(0);

    useEffect(() => {
        const audio = audioRef.current;
        if (!audio) return;

        const handleTimeUpdate = () => {
            if (audio.duration) {
                setProgress((audio.currentTime / audio.duration) * 100);
            }
        };

        const handleLoadedMetadata = () => {
            setDuration(audio.duration);
        };

        const handleEnded = () => {
            setIsPlaying(false);
            setProgress(0);
            onEnded?.();
        };

        audio.addEventListener('timeupdate', handleTimeUpdate);
        audio.addEventListener('loadedmetadata', handleLoadedMetadata);
        audio.addEventListener('ended', handleEnded);

        return () => {
            audio.removeEventListener('timeupdate', handleTimeUpdate);
            audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
            audio.removeEventListener('ended', handleEnded);
        };
    }, [onEnded]);

    useEffect(() => {
        if (autoPlay && src && audioRef.current) {
            audioRef.current.play();
            setIsPlaying(true);
        }
    }, [autoPlay, src]);

    const togglePlay = () => {
        const audio = audioRef.current;
        if (!audio || !src) return;

        if (isPlaying) {
            audio.pause();
        } else {
            audio.play();
        }
        setIsPlaying(!isPlaying);
    };

    const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
        const audio = audioRef.current;
        if (!audio || !src) return;

        const rect = e.currentTarget.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        audio.currentTime = percent * audio.duration;
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    if (!src) {
        return (
            <div className={`audio-player audio-player--disabled ${compact ? 'audio-player--compact' : ''} ${iconOnly ? 'audio-player--icon-only' : ''}`}>
                <span className="audio-player__no-audio">{iconOnly ? '🔇' : '音声なし'}</span>
            </div>
        );
    }

    return (
        <div className={`audio-player ${compact ? 'audio-player--compact' : ''} ${iconOnly ? 'audio-player--icon-only' : ''}`}>
            <audio ref={audioRef} src={src} preload="metadata" />

            <button
                className="audio-player__button"
                onClick={togglePlay}
                aria-label={isPlaying ? '一時停止' : '再生'}
                title={isPlaying ? 'Pause' : 'Play'}
            >
                {isPlaying ? (
                    <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                        <rect x="6" y="4" width="4" height="16" />
                        <rect x="14" y="4" width="4" height="16" />
                    </svg>
                ) : (
                    <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                        <polygon points="5,3 19,12 5,21" />
                    </svg>
                )}
            </button>

            {!iconOnly && !compact && (
                <>
                    <div
                        className="audio-player__progress"
                        onClick={handleProgressClick}
                    >
                        <div
                            className="audio-player__progress-bar"
                            style={{ width: `${progress}%` }}
                        />
                    </div>

                    <span className="audio-player__time">
                        {formatTime(duration)}
                    </span>
                </>
            )}
        </div>
    );
}
