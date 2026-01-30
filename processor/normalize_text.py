"""
Text normalization module for the Japanese PDF Audio Reader.

This module handles:
- Unicode normalization (NFKC)
- Removing layout artifacts and control characters
- Preserving Japanese text (hiragana, katakana, kanji)
- Cleaning up whitespace and formatting

Usage:
    from processor.normalize_text import normalize_text
    
    clean_text = normalize_text(raw_text)
"""

import re
import unicodedata
from typing import Optional


def normalize_unicode(text: str) -> str:
    """
    Apply Unicode NFKC normalization to text.
    
    NFKC normalization:
    - Converts full-width ASCII to half-width
    - Normalizes compatibility characters
    - Preserves Japanese characters (hiragana, katakana, kanji)
    
    Args:
        text: Raw text to normalize.
        
    Returns:
        Unicode-normalized text.
    """
    return unicodedata.normalize("NFKC", text)


def remove_control_characters(text: str) -> str:
    """
    Remove control characters except newlines and tabs.
    
    Preserves:
    - Newlines (\\n)
    - Carriage returns (\\r) - will be normalized later
    - Tabs (\\t)
    
    Args:
        text: Text with potential control characters.
        
    Returns:
        Text with control characters removed.
    """
    # Remove control characters (categories Cc, Cf) except whitespace
    cleaned = []
    for char in text:
        category = unicodedata.category(char)
        # Keep if not a control character, or if it's a common whitespace
        if category not in ("Cc", "Cf") or char in "\n\r\t ":
            cleaned.append(char)
    return "".join(cleaned)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    - Converts Windows line endings (\\r\\n) to Unix (\\n)
    - Removes trailing whitespace from lines
    - Collapses multiple blank lines into one
    - Preserves single newlines between content
    
    Args:
        text: Text with inconsistent whitespace.
        
    Returns:
        Text with normalized whitespace.
    """
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]
    
    # Collapse multiple blank lines into one
    result_lines = []
    prev_blank = False
    for line in lines:
        is_blank = len(line.strip()) == 0
        if is_blank:
            if not prev_blank:
                result_lines.append("")
            prev_blank = True
        else:
            result_lines.append(line)
            prev_blank = False
    
    return "\n".join(result_lines)


def remove_layout_artifacts(text: str) -> str:
    """
    Remove common PDF layout artifacts.
    
    This includes:
    - Page numbers (standalone numbers on lines)
    - Header/footer markers
    - Excessive punctuation from formatting
    
    Args:
        text: Text with potential layout artifacts.
        
    Returns:
        Text with artifacts removed.
    """
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip lines that are just page numbers
        if re.match(r"^[\d\s\-–—\.]+$", stripped) and len(stripped) < 10:
            continue
        
        # Skip lines that are just punctuation/symbols
        if re.match(r"^[\s\-–—\.•●○◆◇★☆※]+$", stripped):
            continue
        
        cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)


def normalize_japanese_punctuation(text: str) -> str:
    """
    Normalize Japanese punctuation marks.
    
    Ensures consistent use of:
    - Full-width periods (。)
    - Full-width commas (、)
    - Full-width question marks (？)
    - Full-width exclamation marks (！)
    
    Args:
        text: Text with potentially mixed punctuation.
        
    Returns:
        Text with normalized punctuation.
    """
    # These conversions happen naturally with NFKC, but we ensure consistency
    replacements = {
        "｡": "。",  # Half-width period to full-width
        "､": "、",  # Half-width comma to full-width
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def normalize_text(
    text: str,
    remove_artifacts: bool = True,
    normalize_punctuation: bool = True
) -> str:
    """
    Normalize Japanese text extracted from a PDF.
    
    Applies a series of normalization steps:
    1. Unicode NFKC normalization
    2. Control character removal
    3. Layout artifact removal (optional)
    4. Japanese punctuation normalization (optional)
    5. Whitespace normalization
    
    Args:
        text: Raw text to normalize.
        remove_artifacts: Whether to remove layout artifacts (page numbers, etc.)
        normalize_punctuation: Whether to normalize Japanese punctuation.
        
    Returns:
        Clean, normalized Japanese text.
    """
    if not text:
        return ""
    
    # Step 1: Unicode normalization
    text = normalize_unicode(text)
    
    # Step 2: Remove control characters
    text = remove_control_characters(text)
    
    # Step 3: Remove layout artifacts
    if remove_artifacts:
        text = remove_layout_artifacts(text)
    
    # Step 4: Normalize Japanese punctuation
    if normalize_punctuation:
        text = normalize_japanese_punctuation(text)
    
    # Step 5: Normalize whitespace (always do this last)
    text = normalize_whitespace(text)
    
    return text.strip()


if __name__ == "__main__":
    import sys
    
    # Demo with sample Japanese text
    sample_text = """
    第1課　はじめまして
    
    1
    
    こんにちは｡私は田中です｡
    よろしくお願いします。
    
    ---
    
    2
    
    日本語を勉強しています。
    """
    
    if len(sys.argv) > 1:
        # Read from file if provided
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            sample_text = f.read()
    
    print("Original text:")
    print("-" * 40)
    print(sample_text[:300])
    print("-" * 40)
    
    normalized = normalize_text(sample_text)
    
    print("\nNormalized text:")
    print("-" * 40)
    print(normalized[:300])
    print("-" * 40)
    print(f"\nOriginal length: {len(sample_text)}")
    print(f"Normalized length: {len(normalized)}")
