import { readFileSync, existsSync } from 'fs';
import path from 'path';

// Path to the public JSON data directory
const PUBLIC_DIR = path.join(process.cwd(), '..', 'data', 'public');

/**
 * Read and parse a JSON file
 */
function readJsonFile<T>(filePath: string): T | null {
    try {
        if (!existsSync(filePath)) {
            return null;
        }
        const content = readFileSync(filePath, 'utf-8');
        return JSON.parse(content) as T;
    } catch (error) {
        console.error(`Failed to read JSON file: ${filePath}`, error);
        return null;
    }
}

// Type definitions
export interface Book {
    id: string;
    title: string;
    language: string;
    status: string;
    createdAt: string;
}

export interface Chapter {
    id: string;
    title: string;
    orderIndex: number;
    audioPath: string | null;
}

export interface Sentence {
    id: string;
    orderIndex: number;
    text: string;
    audioPath: string | null;
}

export interface BookInfo {
    id: string;
    title: string;
    language?: string;
}

export interface ChaptersData {
    book: BookInfo;
    chapters: Chapter[];
}

export interface SentencesData {
    book: BookInfo | null;
    chapter: Chapter;
    sentences: Sentence[];
}

/**
 * Get all books from books.json
 */
export function getAllBooks(): Book[] {
    const filePath = path.join(PUBLIC_DIR, 'books.json');
    return readJsonFile<Book[]>(filePath) || [];
}

/**
 * Get chapters for a book from chapters/{bookId}.json
 */
export function getChaptersForBook(bookId: string): ChaptersData | null {
    const filePath = path.join(PUBLIC_DIR, 'chapters', `${bookId}.json`);
    return readJsonFile<ChaptersData>(filePath);
}

/**
 * Get sentences for a chapter from sentences/{chapterId}.json
 */
export function getSentencesForChapter(chapterId: string): SentencesData | null {
    const filePath = path.join(PUBLIC_DIR, 'sentences', `${chapterId}.json`);
    return readJsonFile<SentencesData>(filePath);
}
