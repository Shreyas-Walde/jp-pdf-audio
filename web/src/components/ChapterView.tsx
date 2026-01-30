'use client';

import { SentencesData } from '@/lib/db';
import SentenceInline from './SentenceInline';
import AudioPlayer from './AudioPlayer';

interface ChapterViewProps {
    data: SentencesData;
}

export default function ChapterView({ data }: ChapterViewProps) {
    const { chapter, sentences } = data;

    // Convert chapter audio path to URL
    const chapterAudioUrl = chapter.audioPath
        ? `/audio/chapters/${chapter.audioPath}`
        : null;

    return (
        <article className="chapter-view">
            <header className="chapter-view__header">
                <div className="chapter-view__title-group">
                    <span className="chapter-view__index">
                        Chapter {chapter.orderIndex + 1}
                    </span>
                    <h1 className="chapter-view__title">
                        {chapter.title}
                    </h1>
                </div>

                {chapterAudioUrl && (
                    <div className="chapter-view__audio">
                        <span className="chapter-view__audio-label">Listen to Chapter</span>
                        <AudioPlayer src={chapterAudioUrl} />
                    </div>
                )}
            </header>

            <div className="chapter-view__content">
                <div className="chapter-page">
                    {sentences.length === 0 ? (
                        <p className="chapter-page__empty">No content available.</p>
                    ) : (
                        <div className="sentence-flow">
                            {sentences.map((sentence, index) => (
                                <SentenceInline
                                    key={sentence.id}
                                    id={sentence.id}
                                    text={sentence.text}
                                    audioPath={sentence.audioPath}
                                // Simple active state logic could be added here later
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </article>
    );
}
