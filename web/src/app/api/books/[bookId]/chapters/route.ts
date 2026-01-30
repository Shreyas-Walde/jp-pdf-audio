import { NextResponse } from 'next/server';
import { getChaptersForBook } from '@/lib/db';

export async function GET(
    request: Request,
    { params }: { params: { bookId: string } }
) {
    const data = getChaptersForBook(params.bookId);

    if (!data) {
        return NextResponse.json({ error: 'Book not found' }, { status: 404 });
    }

    return NextResponse.json(data);
}
