"""
JSON metadata export module for the Japanese PDF Audio Reader.

This module exports processed data from SQLite to static JSON files
for consumption by the Next.js frontend.

Output structure:
    data/public/
    ├── books.json
    ├── chapters/
    │   └── {book_id}.json
    └── sentences/
        └── {chapter_id}.json

Usage:
    from processor.export_json import export_all_metadata
    
    export_all_metadata()  # Exports all READY books to JSON
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from .config import DATA_DIR
from .database import Database, BookStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Output directory for JSON files
PUBLIC_DIR = DATA_DIR / "public"
CHAPTERS_JSON_DIR = PUBLIC_DIR / "chapters"
SENTENCES_JSON_DIR = PUBLIC_DIR / "sentences"


def ensure_export_directories() -> None:
    """Create export directories if they don't exist."""
    for directory in [PUBLIC_DIR, CHAPTERS_JSON_DIR, SENTENCES_JSON_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Any) -> None:
    """Write data to a JSON file with proper formatting."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.debug(f"Wrote: {path}")


def export_books(db: Database) -> List[Dict[str, Any]]:
    """
    Export all READY books to books.json.
    
    Returns:
        List of exported book data.
    """
    books = db.get_all_books(status=BookStatus.READY)
    
    export_data = []
    for book in books:
        export_data.append({
            "id": book["id"],
            "title": book["title"],
            "language": book["language"],
            "status": book["status"],
            "createdAt": book["created_at"]
        })
    
    output_path = PUBLIC_DIR / "books.json"
    write_json(output_path, export_data)
    logger.info(f"Exported {len(export_data)} books to books.json")
    
    return export_data


def export_chapters_for_book(db: Database, book_id: str) -> None:
    """
    Export chapters for a specific book to chapters/{book_id}.json.
    """
    book = db.get_book(book_id)
    if not book:
        logger.warning(f"Book not found: {book_id}")
        return
    
    chapters = db.get_chapters_for_book(book_id)
    
    export_data = {
        "book": {
            "id": book["id"],
            "title": book["title"],
            "language": book["language"]
        },
        "chapters": [
            {
                "id": ch["id"],
                "title": ch["title"],
                "orderIndex": ch["order_index"],
                "audioPath": ch["audio_path"]
            }
            for ch in chapters
        ]
    }
    
    output_path = CHAPTERS_JSON_DIR / f"{book_id}.json"
    write_json(output_path, export_data)
    logger.debug(f"Exported {len(chapters)} chapters for book {book_id}")


def export_sentences_for_chapter(db: Database, chapter_id: str) -> None:
    """
    Export sentences for a specific chapter to sentences/{chapter_id}.json.
    """
    chapter = db.get_chapter(chapter_id)
    if not chapter:
        logger.warning(f"Chapter not found: {chapter_id}")
        return
    
    book = db.get_book(chapter["book_id"])
    sentences = db.get_sentences_for_chapter(chapter_id)
    
    export_data = {
        "book": {
            "id": book["id"],
            "title": book["title"]
        } if book else None,
        "chapter": {
            "id": chapter["id"],
            "title": chapter["title"],
            "orderIndex": chapter["order_index"],
            "audioPath": chapter["audio_path"]
        },
        "sentences": [
            {
                "id": s["id"],
                "orderIndex": s["order_index"],
                "text": s["text"],
                "audioPath": s["audio_path"]
            }
            for s in sentences
        ]
    }
    
    output_path = SENTENCES_JSON_DIR / f"{chapter_id}.json"
    write_json(output_path, export_data)
    logger.debug(f"Exported {len(sentences)} sentences for chapter {chapter_id}")


def export_book_metadata(db: Database, book_id: str) -> None:
    """
    Export all metadata for a specific book (chapters and sentences).
    """
    logger.info(f"Exporting metadata for book: {book_id}")
    
    # Export chapters
    export_chapters_for_book(db, book_id)
    
    # Export sentences for each chapter
    chapters = db.get_chapters_for_book(book_id)
    for chapter in chapters:
        export_sentences_for_chapter(db, chapter["id"])
    
    logger.info(f"Completed export for book {book_id}: {len(chapters)} chapters")


def export_all_metadata(db: Database = None) -> None:
    """
    Export all metadata for all READY books to static JSON files.
    
    This is the main entry point for the export process.
    """
    if db is None:
        db = Database()
    
    ensure_export_directories()
    
    logger.info("Starting full metadata export")
    
    # Export books list
    books = export_books(db)
    
    # Export chapters and sentences for each book
    for book in books:
        export_book_metadata(db, book["id"])
    
    logger.info(f"Export complete: {len(books)} books")


if __name__ == "__main__":
    import sys
    
    logger.setLevel(logging.DEBUG)
    
    db = Database()
    
    if len(sys.argv) > 1:
        # Export specific book
        book_id = sys.argv[1]
        print(f"Exporting metadata for book: {book_id}")
        ensure_export_directories()
        export_books(db)
        export_book_metadata(db, book_id)
    else:
        # Export all
        print("Exporting all metadata to JSON...")
        export_all_metadata(db)
    
    print(f"Export directory: {PUBLIC_DIR}")
