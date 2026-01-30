import { NextResponse } from 'next/server';
import { getAllBooks } from '@/lib/db';

/**
 * GET /api/books
 * Returns list of available books from books.json
 */
export async function GET() {
    try {
        const books = getAllBooks();

        return NextResponse.json({
            success: true,
            data: books
        });
    } catch (error) {
        console.error('Failed to fetch books:', error);
        return NextResponse.json(
            { success: false, error: 'Failed to fetch books' },
            { status: 500 }
        );
    }
}
