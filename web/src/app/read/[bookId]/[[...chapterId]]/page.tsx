'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Book, Chapter, SentencesData } from '@/lib/db';
import Sidebar from '@/components/Sidebar';
import ChapterView from '@/components/ChapterView';

interface ReaderPageProps {
    params: {
        bookId: string;
        chapterId?: string[]; // Optional catch-all for chapter
    };
}

export default function ReaderPage({ params }: ReaderPageProps) {
    const router = useRouter();
    const { bookId } = params;
    const chapterId = params.chapterId ? params.chapterId[0] : null;

    const [book, setBook] = useState<Book | null>(null);
    const [chapters, setChapters] = useState<Chapter[]>([]);
    const [currentChapterData, setCurrentChapterData] = useState<SentencesData | null>(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    // Fetch initial book data (chapters list)
    useEffect(() => {
        async function fetchBookData() {
            try {
                // Fetch chapters for the book
                const res = await fetch(`/api/books/${bookId}/chapters`);
                if (!res.ok) throw new Error('Failed to load book');
                const data = await res.json();

                setBook(data.book);
                setChapters(data.chapters);

                // If no chapter selected, redirect to first chapter
                if (!chapterId && data.chapters.length > 0) {
                    router.replace(`/read/${bookId}/${data.chapters[0].id}`);
                }
            } catch (error) {
                console.error(error);
            } finally {
                setIsLoading(false);
            }
        }
        fetchBookData();
    }, [bookId, chapterId, router]);

    // Fetch specific chapter content when chapterId changes
    useEffect(() => {
        if (!chapterId) return;

        async function fetchChapterContent() {
            try {
                setIsLoading(true);
                const res = await fetch(`/api/chapters/${chapterId}`);
                if (!res.ok) throw new Error('Failed to load chapter');
                const data = await res.json();
                setCurrentChapterData(data);
            } catch (error) {
                console.error(error);
            } finally {
                setIsLoading(false);
            }
        }
        fetchChapterContent();
    }, [chapterId]);

    const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

    if (!book) return <div className="loading-screen">Loading book...</div>;

    return (
        <div className="reader-layout">
            {/* Header/Nav for mobile toggle */}
            <header className="reader-header">
                <button
                    className="sidebar-toggle"
                    onClick={toggleSidebar}
                    aria-label="Toggle sidebar"
                >
                    ☰
                </button>
                <h1 className="reader-header__title">{book.title}</h1>
            </header>

            <div className="reader-container">
                <Sidebar
                    chapters={chapters}
                    activeChapterId={chapterId || undefined}
                    bookId={bookId}
                    bookTitle={book.title}
                    isOpen={isSidebarOpen}
                    onClose={() => setIsSidebarOpen(false)}
                />

                <main className="reader-content">
                    {isLoading ? (
                        <div className="loading-spinner">Loading chapter...</div>
                    ) : currentChapterData ? (
                        <ChapterView data={currentChapterData} />
                    ) : (
                        <div className="empty-state">Select a chapter</div>
                    )}
                </main>
            </div>
        </div>
    );
}
