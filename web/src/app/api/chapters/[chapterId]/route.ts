import { NextResponse } from 'next/server';
import { getSentencesForChapter } from '@/lib/db';

interface RouteParams {
    params: { chapterId: string };
}

/**
 * GET /api/chapters/[chapterId]
 * Returns sentences for a chapter from sentences/{chapterId}.json
 */
export async function GET(request: Request, { params }: RouteParams) {
    try {
        const { chapterId } = params;

        const data = getSentencesForChapter(chapterId);

        if (!data) {
            return NextResponse.json(
                { success: false, error: 'Chapter not found' },
                { status: 404 }
            );
        }

        return NextResponse.json({
            success: true,
            data
        });
    } catch (error) {
        console.error('Failed to fetch chapter:', error);
        return NextResponse.json(
            { success: false, error: 'Failed to fetch chapter' },
            { status: 500 }
        );
    }
}
