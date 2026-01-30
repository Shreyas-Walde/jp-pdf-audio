"""
SQLite database module for the Japanese PDF Audio Reader.

This module handles:
- Database schema creation with foreign keys
- Insert operations for books, chapters, and sentences
- Read queries with proper ordering

Uses standard library sqlite3 for maximum portability.

Usage:
    from processor.database import Database
    
    db = Database()
    db.create_tables()
    
    # Insert data
    db.insert_book(book_id, title, language, pdf_path)
    db.insert_chapter(chapter_id, book_id, title, order_index)
    db.insert_sentence(sentence_id, chapter_id, order_index, text, audio_path)
    
    # Query data
    books = db.get_all_books()
    chapters = db.get_chapters_for_book(book_id)
    sentences = db.get_sentences_for_chapter(chapter_id)
"""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import DATA_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database file path
DEFAULT_DB_PATH = DATA_DIR / "metadata.db"

# Book status constants
class BookStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


# SQL Schema
SCHEMA_SQL = """
-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- Books table
CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    language TEXT DEFAULT 'ja',
    pdf_path TEXT,
    status TEXT DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chapters table
CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL,
    title TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    audio_path TEXT,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
);

-- Sentences table
CREATE TABLE IF NOT EXISTS sentences (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    audio_path TEXT,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_chapters_book_id ON chapters(book_id);
CREATE INDEX IF NOT EXISTS idx_sentences_chapter_id ON sentences(chapter_id);
CREATE INDEX IF NOT EXISTS idx_chapters_order ON chapters(book_id, order_index);
CREATE INDEX IF NOT EXISTS idx_sentences_order ON sentences(chapter_id, order_index);
"""


class Database:
    """
    SQLite database interface for the Japanese PDF Audio Reader.
    
    Provides methods for schema creation, data insertion, and queries.
    Uses context managers for safe connection handling.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. Defaults to data/metadata.db.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database initialized: {self.db_path}")
    
    @contextmanager
    def connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like row access
        conn.execute("PRAGMA foreign_keys = ON")  # Enable FK enforcement
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def create_tables(self) -> None:
        """Create all tables if they don't exist."""
        with self.connection() as conn:
            conn.executescript(SCHEMA_SQL)
            logger.info("Database tables created/verified")
    
    # =========================================================================
    # INSERT OPERATIONS
    # =========================================================================
    
    def insert_book(
        self,
        book_id: str,
        title: str,
        language: str = "ja",
        pdf_path: Optional[str] = None,
        status: str = BookStatus.PENDING
    ) -> str:
        """
        Insert a new book record.
        
        Args:
            book_id: Unique book identifier.
            title: Book title.
            language: Language code (default: 'ja').
            pdf_path: Path to stored PDF file.
            status: Processing status.
            
        Returns:
            The book_id.
        """
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO books (id, title, language, pdf_path, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (book_id, title, language, pdf_path, status)
            )
            logger.debug(f"Inserted book: {book_id}")
        return book_id
    
    def insert_chapter(
        self,
        chapter_id: str,
        book_id: str,
        title: str,
        order_index: int,
        audio_path: Optional[str] = None
    ) -> str:
        """
        Insert a new chapter record.
        
        Args:
            chapter_id: Unique chapter identifier.
            book_id: Parent book ID.
            title: Chapter title.
            order_index: Order within the book (0-indexed).
            audio_path: Path to chapter audio file.
            
        Returns:
            The chapter_id.
        """
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO chapters (id, book_id, title, order_index, audio_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chapter_id, book_id, title, order_index, audio_path)
            )
            logger.debug(f"Inserted chapter: {chapter_id}")
        return chapter_id
    
    def insert_sentence(
        self,
        sentence_id: str,
        chapter_id: str,
        order_index: int,
        text: str,
        audio_path: Optional[str] = None
    ) -> str:
        """
        Insert a new sentence record.
        
        Args:
            sentence_id: Unique sentence identifier.
            chapter_id: Parent chapter ID.
            order_index: Order within the chapter (0-indexed).
            text: Sentence text content.
            audio_path: Path to sentence audio file.
            
        Returns:
            The sentence_id.
        """
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO sentences (id, chapter_id, order_index, text, audio_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sentence_id, chapter_id, order_index, text, audio_path)
            )
            logger.debug(f"Inserted sentence: {sentence_id}")
        return sentence_id
    
    def insert_chapters_batch(self, chapters: List[Dict[str, Any]]) -> int:
        """
        Insert multiple chapters in a single transaction.
        
        Args:
            chapters: List of chapter dicts with keys:
                      id, book_id, title, order_index, audio_path (optional)
        
        Returns:
            Number of chapters inserted.
        """
        with self.connection() as conn:
            conn.executemany(
                """
                INSERT INTO chapters (id, book_id, title, order_index, audio_path)
                VALUES (:id, :book_id, :title, :order_index, :audio_path)
                """,
                [{**ch, 'audio_path': ch.get('audio_path')} for ch in chapters]
            )
            logger.info(f"Batch inserted {len(chapters)} chapters")
        return len(chapters)
    
    def insert_sentences_batch(self, sentences: List[Dict[str, Any]]) -> int:
        """
        Insert multiple sentences in a single transaction.
        
        Args:
            sentences: List of sentence dicts with keys:
                       id, chapter_id, order_index, text, audio_path (optional)
        
        Returns:
            Number of sentences inserted.
        """
        with self.connection() as conn:
            conn.executemany(
                """
                INSERT INTO sentences (id, chapter_id, order_index, text, audio_path)
                VALUES (:id, :chapter_id, :order_index, :text, :audio_path)
                """,
                [{**s, 'audio_path': s.get('audio_path')} for s in sentences]
            )
            logger.info(f"Batch inserted {len(sentences)} sentences")
        return len(sentences)
    
    # =========================================================================
    # UPDATE OPERATIONS
    # =========================================================================
    
    def update_book_status(self, book_id: str, status: str) -> None:
        """Update the processing status of a book."""
        with self.connection() as conn:
            conn.execute(
                "UPDATE books SET status = ? WHERE id = ?",
                (status, book_id)
            )
            logger.info(f"Updated book {book_id} status to {status}")
    
    def update_chapter_audio_path(self, chapter_id: str, audio_path: str) -> None:
        """Update the audio path for a chapter."""
        with self.connection() as conn:
            conn.execute(
                "UPDATE chapters SET audio_path = ? WHERE id = ?",
                (audio_path, chapter_id)
            )
            logger.debug(f"Updated chapter {chapter_id} audio path")
    
    def update_sentence_audio_path(self, sentence_id: str, audio_path: str) -> None:
        """Update the audio path for a sentence."""
        with self.connection() as conn:
            conn.execute(
                "UPDATE sentences SET audio_path = ? WHERE id = ?",
                (audio_path, sentence_id)
            )
            logger.debug(f"Updated sentence {sentence_id} audio path")
    
    # =========================================================================
    # READ OPERATIONS
    # =========================================================================
    
    def get_all_books(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all books, optionally filtered by status.
        
        Args:
            status: Filter by status (e.g., 'READY'). None for all.
            
        Returns:
            List of book dicts ordered by created_at descending.
        """
        with self.connection() as conn:
            if status:
                cursor = conn.execute(
                    """
                    SELECT id, title, language, pdf_path, status, created_at
                    FROM books
                    WHERE status = ?
                    ORDER BY created_at DESC
                    """,
                    (status,)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT id, title, language, pdf_path, status, created_at
                    FROM books
                    ORDER BY created_at DESC
                    """
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_book(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get a single book by ID."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, title, language, pdf_path, status, created_at
                FROM books
                WHERE id = ?
                """,
                (book_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_chapters_for_book(self, book_id: str) -> List[Dict[str, Any]]:
        """
        Get all chapters for a book, ordered by order_index.
        
        Args:
            book_id: The parent book ID.
            
        Returns:
            List of chapter dicts in order.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, book_id, title, order_index, audio_path
                FROM chapters
                WHERE book_id = ?
                ORDER BY order_index ASC
                """,
                (book_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_chapter(self, chapter_id: str) -> Optional[Dict[str, Any]]:
        """Get a single chapter by ID."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, book_id, title, order_index, audio_path
                FROM chapters
                WHERE id = ?
                """,
                (chapter_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_sentences_for_chapter(self, chapter_id: str) -> List[Dict[str, Any]]:
        """
        Get all sentences for a chapter, ordered by order_index.
        
        Args:
            chapter_id: The parent chapter ID.
            
        Returns:
            List of sentence dicts in order.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, chapter_id, order_index, text, audio_path
                FROM sentences
                WHERE chapter_id = ?
                ORDER BY order_index ASC
                """,
                (chapter_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_sentence(self, sentence_id: str) -> Optional[Dict[str, Any]]:
        """Get a single sentence by ID."""
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, chapter_id, order_index, text, audio_path
                FROM sentences
                WHERE id = ?
                """,
                (sentence_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # =========================================================================
    # UTILITY OPERATIONS
    # =========================================================================
    
    def book_exists(self, book_id: str) -> bool:
        """Check if a book exists."""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM books WHERE id = ?",
                (book_id,)
            )
            return cursor.fetchone() is not None
    
    def get_book_stats(self, book_id: str) -> Dict[str, int]:
        """Get statistics for a book (chapter count, sentence count)."""
        with self.connection() as conn:
            # Chapter count
            cursor = conn.execute(
                "SELECT COUNT(*) FROM chapters WHERE book_id = ?",
                (book_id,)
            )
            chapter_count = cursor.fetchone()[0]
            
            # Sentence count (through chapters)
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM sentences s
                JOIN chapters c ON s.chapter_id = c.id
                WHERE c.book_id = ?
                """,
                (book_id,)
            )
            sentence_count = cursor.fetchone()[0]
            
            return {
                "chapters": chapter_count,
                "sentences": sentence_count
            }
    
    def delete_book(self, book_id: str) -> bool:
        """
        Delete a book and all related data (cascading).
        
        Returns:
            True if book was deleted, False if not found.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM books WHERE id = ?",
                (book_id,)
            )
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted book: {book_id}")
            return deleted


# Convenience function for quick database access
def get_database(db_path: Optional[Path] = None) -> Database:
    """Get a Database instance."""
    return Database(db_path)


if __name__ == "__main__":
    import sys
    
    logger.setLevel(logging.DEBUG)
    
    # Demo usage
    db = Database()
    db.create_tables()
    
    print("Database tables created successfully!")
    print(f"Database path: {db.db_path}")
    
    # List existing books
    books = db.get_all_books()
    print(f"\nExisting books: {len(books)}")
    for book in books:
        stats = db.get_book_stats(book['id'])
        print(f"  - {book['title']} ({book['status']}): "
              f"{stats['chapters']} chapters, {stats['sentences']} sentences")
