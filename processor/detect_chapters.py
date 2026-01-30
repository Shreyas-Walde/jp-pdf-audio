"""
Chapter detection module for the Japanese PDF Audio Reader.

This module handles:
- Detecting chapter boundaries using regex heuristics
- Splitting text into chapters with titles and content
- Generating unique chapter IDs

Supported chapter patterns:
- 第1課, 第2課, etc. (Lesson 1, 2, etc.)
- 第一章, 第二章, etc. (Chapter 1, 2, etc.)
- Lesson 1, Lesson 2, etc.
- Chapter 1, Chapter 2, etc.
- Unit 1, Unit 2, etc.

Usage:
    from processor.detect_chapters import detect_chapters
    
    chapters = detect_chapters(normalized_text, book_id="abc123")
"""

import logging
import re
import uuid
from dataclasses import dataclass
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    """Represents a detected chapter."""
    id: str
    book_id: str
    title: str
    text: str
    order_index: int


# Japanese number characters for chapter detection
JAPANESE_NUMBERS = "一二三四五六七八九十百"

# Chapter detection patterns (ordered by priority)
CHAPTER_PATTERNS = [
    # Japanese lesson format: 第1課, 第12課
    re.compile(r"^(第\s*\d+\s*課.*)$", re.MULTILINE),
    
    # Japanese chapter with kanji numbers: 第一章, 第二章
    re.compile(rf"^(第\s*[{JAPANESE_NUMBERS}]+\s*章.*)$", re.MULTILINE),
    
    # Japanese chapter with arabic numbers: 第1章, 第2章
    re.compile(r"^(第\s*\d+\s*章.*)$", re.MULTILINE),
    
    # Japanese lesson with kanji numbers: 第一課, 第二課
    re.compile(rf"^(第\s*[{JAPANESE_NUMBERS}]+\s*課.*)$", re.MULTILINE),
    
    # English lesson format: Lesson 1, LESSON 2
    re.compile(r"^(Lesson\s+\d+.*)$", re.MULTILINE | re.IGNORECASE),
    
    # English chapter format: Chapter 1, CHAPTER 2
    re.compile(r"^(Chapter\s+\d+.*)$", re.MULTILINE | re.IGNORECASE),
    
    # English unit format: Unit 1, UNIT 2
    re.compile(r"^(Unit\s+\d+.*)$", re.MULTILINE | re.IGNORECASE),
]


def generate_chapter_id() -> str:
    """Generate a unique chapter identifier."""
    return str(uuid.uuid4())


def find_chapter_markers(text: str) -> List[tuple]:
    """
    Find all chapter markers in text with their positions.
    
    Args:
        text: The full normalized text.
        
    Returns:
        List of tuples: (start_position, title_line)
    """
    markers = []
    
    for pattern in CHAPTER_PATTERNS:
        for match in pattern.finditer(text):
            title = match.group(1).strip()
            start = match.start()
            markers.append((start, title))
            logger.debug(f"Found chapter marker at pos {start}: {title[:50]}")
    
    # Sort by position and remove duplicates (keep first occurrence)
    markers.sort(key=lambda x: x[0])
    
    # Remove overlapping markers (within 10 chars of each other)
    filtered = []
    for marker in markers:
        if not filtered or marker[0] - filtered[-1][0] > 10:
            filtered.append(marker)
    
    logger.info(f"Found {len(filtered)} chapter markers")
    return filtered


def split_into_chapters(
    text: str,
    markers: List[tuple],
    book_id: str
) -> List[Chapter]:
    """
    Split text into chapters based on detected markers.
    
    Args:
        text: The full normalized text.
        markers: List of (position, title) tuples.
        book_id: The book ID for chapter association.
        
    Returns:
        List of Chapter objects.
    """
    if not markers:
        # No chapters detected, treat entire text as one chapter
        logger.warning("No chapter markers found, creating single chapter")
        return [
            Chapter(
                id=generate_chapter_id(),
                book_id=book_id,
                title="Chapter 1",
                text=text.strip(),
                order_index=0
            )
        ]
    
    chapters = []
    
    for i, (start_pos, title) in enumerate(markers):
        # Determine end position (start of next chapter or end of text)
        if i + 1 < len(markers):
            end_pos = markers[i + 1][0]
        else:
            end_pos = len(text)
        
        # Extract chapter content (skip the title line itself)
        chapter_text = text[start_pos:end_pos]
        
        # Remove the title from the content (it's stored separately)
        lines = chapter_text.split("\n")
        if lines and title in lines[0]:
            lines = lines[1:]
        content = "\n".join(lines).strip()
        
        chapter = Chapter(
            id=generate_chapter_id(),
            book_id=book_id,
            title=title,
            text=content,
            order_index=i
        )
        chapters.append(chapter)
        
        logger.info(
            f"Chapter {i + 1}: '{title[:40]}...' - {len(content)} chars"
        )
    
    return chapters


def detect_chapters(
    text: str,
    book_id: str,
    include_preamble: bool = True
) -> List[Chapter]:
    """
    Detect and extract chapters from normalized text.
    
    Uses regex-based heuristics to find chapter boundaries.
    This is a deterministic process with no LLM involvement.
    
    Args:
        text: Normalized Japanese text.
        book_id: The book ID to associate chapters with.
        include_preamble: If True, include text before first chapter
                         as "Introduction".
                         
    Returns:
        List of Chapter objects in order.
    """
    logger.info(f"Starting chapter detection for book {book_id}")
    logger.info(f"Input text length: {len(text)} characters")
    
    # Find all chapter markers
    markers = find_chapter_markers(text)
    
    # Handle text before first chapter (preamble)
    if include_preamble and markers and markers[0][0] > 100:
        preamble_text = text[:markers[0][0]].strip()
        if len(preamble_text) > 50:  # Only include if substantial
            logger.info(f"Including preamble: {len(preamble_text)} chars")
            # Insert a synthetic marker at the start
            markers.insert(0, (0, "はじめに"))  # "Introduction" in Japanese
    
    # Split into chapters
    chapters = split_into_chapters(text, markers, book_id)
    
    logger.info(f"Chapter detection complete: {len(chapters)} chapters found")
    
    return chapters


if __name__ == "__main__":
    import sys
    
    # Demo with sample text
    sample_text = """
はじめに

この本は日本語を勉強する人のための教科書です。

第1課　あいさつ

こんにちは。
はじめまして。
私は田中です。
よろしくお願いします。

第2課　自己紹介

私の名前は山田花子です。
東京から来ました。
趣味は読書です。

第3課　日常会話

今日はいい天気ですね。
そうですね。
どこへ行きますか。
"""
    
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            sample_text = f.read()
    
    logger.setLevel(logging.DEBUG)
    
    chapters = detect_chapters(sample_text, book_id="test-book-123")
    
    print("\n" + "=" * 50)
    print(f"Detected {len(chapters)} chapters:")
    print("=" * 50)
    
    for ch in chapters:
        print(f"\n[{ch.order_index}] {ch.title}")
        print(f"    ID: {ch.id}")
        print(f"    Length: {len(ch.text)} chars")
        print(f"    Preview: {ch.text[:100]}...")
