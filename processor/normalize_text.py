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


def remove_pdf_extraction_junk(text: str) -> str:
    """
    Remove non-linguistic junk characters introduced by PDF text extraction.
    
    PDF extraction often introduces artifacts like:
    - Standalone ASCII letters (e.g., 'h', 'a') between Japanese text
    - Standalone digits (e.g., '0', '1') not part of Japanese words
    - Backslashes and escape sequences
    - Other non-Japanese layout artifacts
    
    Preserves:
    - Hiragana (U+3040-U+309F)
    - Katakana (U+30A0-U+30FF)
    - Kanji (CJK Unified Ideographs)
    - Japanese punctuation (。！？、「」『』（）・ー〜々)
    - Full-width numbers and letters (when used in context)
    - Newlines and basic whitespace (for sentence structure)
    
    Args:
        text: Text with potential PDF extraction junk.
        
    Returns:
        Cleaned text with junk characters removed.
    """
    # Pattern to match Japanese characters and allowed symbols
    japanese_pattern = re.compile(
        r"[\u3040-\u309F"   # Hiragana
        r"\u30A0-\u30FF"    # Katakana  
        r"\u4E00-\u9FFF"    # CJK Unified Ideographs (common kanji)
        r"\u3400-\u4DBF"    # CJK Extension A
        r"\uF900-\uFAFF"    # CJK Compatibility Ideographs
        r"\u31F0-\u31FF"    # Katakana Phonetic Extensions
        r"\uFF65-\uFF9F"    # Half-width Katakana
        r"\u3000-\u303F"    # CJK Symbols and Punctuation
        r"\uFF01-\uFF60"    # Full-width ASCII variants
        r"。、！？「」『』（）・ー〜々…‥]"  # Explicit Japanese punctuation
    )
    
    # Pattern to match junk characters that should be removed
    junk_pattern = re.compile(r"[a-zA-Z0-9\\\/]+")
    
    def is_japanese(char: str) -> bool:
        """Check if a character is Japanese (hiragana, katakana, kanji, or JP punctuation)."""
        return bool(japanese_pattern.match(char))
    
    def process_line(line: str) -> str:
        """Process a single line, removing junk characters between Japanese text."""
        if not line.strip():
            return line
        
        # Find all runs of junk characters and their positions
        result = []
        i = 0
        chars = list(line)
        
        while i < len(chars):
            char = chars[i]
            
            # If it's a Japanese character or whitespace, keep it
            if is_japanese(char) or char in " \t":
                result.append(char)
                i += 1
                continue
            
            # Check for junk characters (ASCII letters, digits, backslashes)
            if char in "\\/" or (char.isascii() and char.isalnum()):
                # Collect the entire run of potential junk
                junk_start = i
                junk_run = ""
                while i < len(chars):
                    c = chars[i]
                    if c in "\\/" or (c.isascii() and c.isalnum()):
                        junk_run += c
                        i += 1
                    else:
                        break
                
                # Check context: what comes before and after this junk run?
                prev_char = chars[junk_start - 1] if junk_start > 0 else ""
                next_char = chars[i] if i < len(chars) else ""
                
                prev_is_japanese = is_japanese(prev_char) if prev_char else False
                next_is_japanese = is_japanese(next_char) if next_char else False
                
                # If junk is between Japanese characters, it's extraction noise - remove it
                # Also remove if it's short (1-2 chars) and at least one neighbor is Japanese
                if prev_is_japanese and next_is_japanese:
                    # Definitely junk - skip it
                    continue
                elif len(junk_run) <= 2 and (prev_is_japanese or next_is_japanese):
                    # Short junk adjacent to Japanese text - likely noise
                    continue
                else:
                    # Might be intentional (longer sequences, or at line edges)
                    result.append(junk_run)
                continue
            
            # Keep other characters (punctuation, etc. that isn't specifically junk)
            result.append(char)
            i += 1
        
        return "".join(result)
    
    # Process each line
    lines = text.split("\n")
    return "\n".join(process_line(line) for line in lines)


def normalize_text(
    text: str,
    remove_artifacts: bool = True,
    normalize_punctuation: bool = True,
    remove_extraction_junk: bool = True
) -> str:
    """
    Normalize Japanese text extracted from a PDF.
    
    Applies a series of normalization steps:
    1. Unicode NFKC normalization
    2. Control character removal
    3. PDF extraction junk removal (optional)
    4. Layout artifact removal (optional)
    5. Japanese punctuation normalization (optional)
    6. Whitespace normalization
    
    Args:
        text: Raw text to normalize.
        remove_artifacts: Whether to remove layout artifacts (page numbers, etc.)
        normalize_punctuation: Whether to normalize Japanese punctuation.
        remove_extraction_junk: Whether to remove PDF extraction junk (standalone
            ASCII letters/digits, backslashes between Japanese text).
        
    Returns:
        Clean, normalized Japanese text.
    """
    if not text:
        return ""
    
    # Step 1: Unicode normalization
    text = normalize_unicode(text)
    
    # Step 2: Remove control characters
    text = remove_control_characters(text)
    
    # Step 3: Remove PDF extraction junk (standalone ASCII chars, backslashes)
    if remove_extraction_junk:
        text = remove_pdf_extraction_junk(text)
    
    # Step 4: Remove layout artifacts
    if remove_artifacts:
        text = remove_layout_artifacts(text)
    
    # Step 5: Normalize Japanese punctuation
    if normalize_punctuation:
        text = normalize_japanese_punctuation(text)
    
    # Step 6: Normalize whitespace (always do this last)
    text = normalize_whitespace(text)
    
    return text.strip()


if __name__ == "__main__":
    import sys
    
    # Demo with sample Japanese text containing PDF extraction junk
    sample_text = """
    第1課　はじめまして
    
    1
    
    こんにちは｡私h0は田中\\です｡
    よろしくaお願いします。
    
    ---
    
    2
    
    日本語0を勉強hしています。
    これはテ\\ストです。
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
