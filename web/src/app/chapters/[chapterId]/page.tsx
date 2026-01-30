import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getSentencesForChapter } from '@/lib/db';
import SentenceRow from '@/components/SentenceRow';
import AudioPlayer from '@/components/AudioPlayer';

interface PageProps {
    params: { chapterId: string };
}

/**
 * Chapter reader page - displays sentences with audio playback
 */
export default function ChapterPage({ params }: PageProps) {
    const { chapterId } = params;

    const data = getSentencesForChapter(chapterId);
    if (!data) {
        notFound();
    }

    const { book, chapter, sentences } = data;

    // Convert chapter audio path to URL
    const chapterAudioUrl = chapter.audioPath
        ? `/audio/chapters/${chapter.audioPath}`
        : null;

    return (
        <main className="container">
            <nav className="breadcrumb">
                <Link href="/" className="breadcrumb__link">ホーム</Link>
                <span className="breadcrumb__separator">›</span>
                {book && (
                    <>
                        <Link href={`/books/${book.id}`} className="breadcrumb__link">
                            {book.title}
                        </Link>
                        <span className="breadcrumb__separator">›</span>
                    </>
                )}
                <span className="breadcrumb__current">{chapter.title}</span>
            </nav>

            <header className="chapter-header">
                <div className="chapter-header__info">
                    <span className="chapter-header__index">
                        第{chapter.orderIndex + 1}章
                    </span>
                    <h1 className="chapter-header__title">{chapter.title}</h1>
                </div>

                {chapterAudioUrl && (
                    <div className="chapter-header__audio">
                        <span className="chapter-header__audio-label">章全体を再生:</span>
                        <AudioPlayer src={chapterAudioUrl} />
                    </div>
                )}
            </header>

            <section className="sentences">
                <h2 className="visually-hidden">文章</h2>

                {sentences.length === 0 ? (
                    <div className="empty-state">
                        <p>この章には文章がありません。</p>
                    </div>
                ) : (
                    <div className="sentence-list">
                        {sentences.map((sentence) => (
                            <SentenceRow
                                key={sentence.id}
                                id={sentence.id}
                                index={sentence.orderIndex}
                                text={sentence.text}
                                audioPath={sentence.audioPath}
                            />
                        ))}
                    </div>
                )}
            </section>

            <footer className="chapter-footer">
                <p className="chapter-footer__count">
                    {sentences.length} 文
                </p>
            </footer>
        </main>
    );
}
