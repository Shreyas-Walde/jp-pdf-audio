import { NextResponse } from 'next/server';
import { getChaptersForBook } from '@/lib/db';

interface RouteParams {
    params: { bookId: string };
}

/**
 * GET /api/books/[bookId]/chapters
 * Returns chapters for a book from chapters/{bookId}.json
 */
export async function GET(request: Request, { params }: RouteParams) {
    try {
        const { bookId } = params;

        const data = getChaptersForBook(bookId);

        if (!data) {
            return NextResponse.json(
                { success: false, error: 'Book not found' },
                { status: 404 }
            );
        }

        return NextResponse.json({
            success: true,
            data
        });
    } catch (error) {
        console.error('Failed to fetch chapters:', error);
        return NextResponse.json(
            { success: false, error: 'Failed to fetch chapters' },
            { status: 500 }
        );
    }
}
