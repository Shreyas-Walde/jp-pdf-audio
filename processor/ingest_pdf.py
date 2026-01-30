"""
PDF ingestion module for the Japanese PDF Audio Reader.

This module handles:
- Accepting a PDF file path
- Generating a unique book_id (UUID)
- Copying the PDF to the data/books directory

Usage:
    from processor.ingest_pdf import ingest_pdf
    
    book_id, stored_path = ingest_pdf("/path/to/textbook.pdf")
"""

import shutil
import uuid
from pathlib import Path
from typing import Tuple

from .config import BOOKS_DIR, ensure_directories


def generate_book_id() -> str:
    """
    Generate a unique book identifier using UUID4.
    
    Returns:
        A unique string identifier for the book.
    """
    return str(uuid.uuid4())


def ingest_pdf(pdf_path: str | Path, book_id: str | None = None) -> Tuple[str, Path]:
    """
    Ingest a PDF file into the system.
    
    This function:
    1. Validates that the PDF file exists
    2. Generates a unique book_id (or uses provided one)
    3. Copies the PDF to data/books/{book_id}.pdf
    
    Args:
        pdf_path: Path to the source PDF file.
        book_id: Optional pre-generated book ID. If None, generates a new one.
        
    Returns:
        A tuple of (book_id, stored_path) where:
        - book_id: The unique identifier for this book
        - stored_path: The path where the PDF was stored
        
    Raises:
        FileNotFoundError: If the source PDF doesn't exist.
        ValueError: If the file is not a PDF.
    """
    pdf_path = Path(pdf_path)
    
    # Validate file exists
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Validate file extension
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"File must be a PDF, got: {pdf_path.suffix}")
    
    # Ensure storage directory exists
    ensure_directories()
    
    # Generate book ID if not provided
    if book_id is None:
        book_id = generate_book_id()
    
    # Define destination path
    stored_path = BOOKS_DIR / f"{book_id}.pdf"
    
    # Copy PDF to storage location
    shutil.copy2(pdf_path, stored_path)
    
    return book_id, stored_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m processor.ingest_pdf <pdf_path>")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    try:
        book_id, stored = ingest_pdf(pdf_file)
        print(f"Book ingested successfully!")
        print(f"  Book ID: {book_id}")
        print(f"  Stored at: {stored}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
