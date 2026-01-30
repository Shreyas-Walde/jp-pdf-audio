import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getChaptersForBook } from '@/lib/db';

interface PageProps {
    params: { bookId: string };
}

/**
 * Book detail page - displays list of chapters
 */
export default function BookPage({ params }: PageProps) {
    const { bookId } = params;

    const data = getChaptersForBook(bookId);
    if (!data) {
        notFound();
    }

    const { book, chapters } = data;

    return (
        <main className="container">
            <nav className="breadcrumb">
                <Link href="/" className="breadcrumb__link">ホーム</Link>
                <span className="breadcrumb__separator">›</span>
                <span className="breadcrumb__current">{book.title}</span>
            </nav>

            <header className="header">
                <h1 className="header__title">{book.title}</h1>
                <p className="header__meta">
                    {chapters.length} 章
                </p>
            </header>

            {chapters.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-state__icon">📑</div>
                    <h2>章が見つかりません</h2>
                </div>
            ) : (
                <section className="chapter-list">
                    {chapters.map((chapter) => (
                        <Link
                            key={chapter.id}
                            href={`/chapters/${chapter.id}`}
                            className="chapter-card"
                        >
                            <span className="chapter-card__index">
                                第{chapter.orderIndex + 1}章
                            </span>
                            <h3 className="chapter-card__title">{chapter.title}</h3>
                            {chapter.audioPath && (
                                <span className="chapter-card__audio-badge">
                                    🔊 音声あり
                                </span>
                            )}
                        </Link>
                    ))}
                </section>
            )}
        </main>
    );
}
