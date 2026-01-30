import Link from 'next/link';
import { getAllBooks } from '@/lib/db';

/**
 * Home page - displays list of available books
 */
export default function HomePage() {
    let books = getAllBooks();
    let error: string | null = null;

    if (!books || books.length === 0) {
        // Check if it's a missing file vs empty list
        try {
            books = getAllBooks();
        } catch (e) {
            error = 'データベースに接続できませんでした。';
            console.error('Failed to load books:', e);
        }
    }

    return (
        <main className="container">
            <header className="header">
                <h1 className="header__title">📚 日本語PDF音声リーダー</h1>
                <p className="header__subtitle">Japanese PDF Audio Reader</p>
            </header>

            {error ? (
                <div className="error-message">
                    <p>{error}</p>
                    <p className="error-message__hint">
                        処理パイプラインでPDFを処理してください。
                    </p>
                </div>
            ) : books.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-state__icon">📖</div>
                    <h2>まだ本がありません</h2>
                    <p>処理パイプラインでPDFを追加してください。</p>
                </div>
            ) : (
                <section className="book-list">
                    <h2 className="section-title">利用可能な本</h2>
                    <div className="book-grid">
                        {books.map((book) => (
                            <Link
                                key={book.id}
                                href={`/books/${book.id}`}
                                className="book-card"
                            >
                                <div className="book-card__icon">📕</div>
                                <h3 className="book-card__title">{book.title}</h3>
                                <div className="book-card__meta">
                                    <span className="book-card__language">
                                        {book.language === 'ja' ? '日本語' : book.language}
                                    </span>
                                </div>
                            </Link>
                        ))}
                    </div>
                </section>
            )}
        </main>
    );
}
