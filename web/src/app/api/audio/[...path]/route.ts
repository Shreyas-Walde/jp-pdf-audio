import { NextRequest, NextResponse } from 'next/server';
import { readFileSync, existsSync } from 'fs';
import path from 'path';

interface RouteParams {
    params: { path: string[] };
}

/**
 * GET /api/audio/[...path]
 * Serves audio files from the data/audio directory
 */
export async function GET(request: NextRequest, { params }: RouteParams) {
    try {
        const audioPath = params.path.join('/');
        const fullPath = path.join(process.cwd(), '..', 'data', 'audio', audioPath);

        // Security: ensure path doesn't escape audio directory
        const resolvedPath = path.resolve(fullPath);
        const audioDir = path.resolve(path.join(process.cwd(), '..', 'data', 'audio'));

        if (!resolvedPath.startsWith(audioDir)) {
            return NextResponse.json(
                { error: 'Invalid path' },
                { status: 403 }
            );
        }

        if (!existsSync(resolvedPath)) {
            return NextResponse.json(
                { error: 'Audio file not found' },
                { status: 404 }
            );
        }

        const fileBuffer = readFileSync(resolvedPath);

        // Determine content type based on extension
        const ext = path.extname(resolvedPath).toLowerCase();
        const contentTypes: Record<string, string> = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.ogg': 'audio/ogg',
            '.webm': 'audio/webm',
        };

        const contentType = contentTypes[ext] || 'application/octet-stream';

        return new NextResponse(fileBuffer, {
            headers: {
                'Content-Type': contentType,
                'Content-Length': fileBuffer.length.toString(),
                'Cache-Control': 'public, max-age=31536000, immutable',
            },
        });
    } catch (error) {
        console.error('Failed to serve audio:', error);
        return NextResponse.json(
            { error: 'Failed to serve audio file' },
            { status: 500 }
        );
    }
}
