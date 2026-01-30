import { NextResponse } from 'next/server';
import { getSentencesForChapter } from '@/lib/db';

export async function GET(
    request: Request,
    { params }: { params: { chapterId: string } }
) {
    const data = getSentencesForChapter(params.chapterId);

    if (!data) {
        return NextResponse.json({ error: 'Chapter not found' }, { status: 404 });
    }

    return NextResponse.json(data);
}
