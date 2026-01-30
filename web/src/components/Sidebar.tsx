'use client';

import Link from 'next/link';
import { Chapter } from '@/lib/db';

interface SidebarProps {
    chapters: Chapter[];
    activeChapterId?: string;
    bookId: string;
    bookTitle: string;
    isOpen: boolean;
    onClose?: () => void;
}

export default function Sidebar({
    chapters,
    activeChapterId,
    bookId,
    bookTitle,
    isOpen,
    onClose
}: SidebarProps) {
    return (
        <>
            {/* Mobile overlay */}
            <div
                className={`sidebar-overlay ${isOpen ? 'is-open' : ''}`}
                onClick={onClose}
                aria-hidden="true"
            />

            <aside className={`sidebar ${isOpen ? 'is-open' : ''}`}>
                <div className="sidebar__header">
                    <Link href="/" className="sidebar__home-link">
                        ← Home
                    </Link>
                    <h2 className="sidebar__title" title={bookTitle}>
                        {bookTitle}
                    </h2>
                </div>

                <div className="sidebar__content">
                    <h3 className="sidebar__section-title">目次 (Index)</h3>
                    <nav className="chapter-nav">
                        {chapters.map((chapter) => (
                            <Link
                                key={chapter.id}
                                href={`/read/${bookId}/${chapter.id}`}
                                className={`chapter-nav__item ${chapter.id === activeChapterId ? 'is-active' : ''
                                    }`}
                                onClick={onClose} // Close sidebar on mobile select
                            >
                                <span className="chapter-nav__index">
                                    {chapter.orderIndex + 1}.
                                </span>
                                <span className="chapter-nav__title">
                                    {chapter.title}
                                </span>
                                {chapter.audioPath && (
                                    <span className="chapter-nav__icon" title="Audio available">
                                        🔊
                                    </span>
                                )}
                            </Link>
                        ))}
                    </nav>
                </div>
            </aside>
        </>
    );
}
