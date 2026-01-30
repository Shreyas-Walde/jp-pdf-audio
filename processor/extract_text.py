"""
Text extraction module for the Japanese PDF Audio Reader.

This module handles:
- Extracting text from PDF files using pdfplumber (primary method)
- Falling back to Tesseract OCR if text extraction yields insufficient content
- Preserving Japanese characters (hiragana, katakana, kanji)

Usage:
    from processor.extract_text import extract_text
    
    text = extract_text("/path/to/book.pdf")
"""

from pathlib import Path
from typing import Optional

import pdfplumber

from .config import OCR_FALLBACK_THRESHOLD, TESSERACT_LANG


def extract_text_with_pdfplumber(pdf_path: Path) -> str:
    """
    Extract text from a PDF using pdfplumber.
    
    pdfplumber is effective for text-based PDFs and preserves
    the original text encoding, which is important for Japanese text.
    
    Args:
        pdf_path: Path to the PDF file.
        
    Returns:
        Extracted text as a single string.
    """
    text_parts = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    return "\n".join(text_parts)


def extract_text_with_ocr(pdf_path: Path) -> str:
    """
    Extract text from a PDF using Tesseract OCR.
    
    This is a fallback method for scanned PDFs or PDFs where
    direct text extraction fails.
    
    Args:
        pdf_path: Path to the PDF file.
        
    Returns:
        Extracted text as a single string.
        
    Raises:
        ImportError: If pytesseract or pdf2image is not installed.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as e:
        raise ImportError(
            "OCR fallback requires pytesseract and pdf2image. "
            "Install with: pip install pytesseract pdf2image"
        ) from e
    
    text_parts = []
    
    # Convert PDF pages to images
    images = convert_from_path(pdf_path)
    
    for image in images:
        # Run OCR with Japanese language pack
        page_text = pytesseract.image_to_string(image, lang=TESSERACT_LANG)
        if page_text:
            text_parts.append(page_text)
    
    return "\n".join(text_parts)


def extract_text(
    pdf_path: str | Path,
    force_ocr: bool = False,
    ocr_threshold: Optional[int] = None
) -> str:
    """
    Extract text from a PDF file.
    
    Uses pdfplumber as the primary extraction method. If the extracted
    text is below the threshold (suggesting a scanned PDF), falls back
    to Tesseract OCR.
    
    Args:
        pdf_path: Path to the PDF file.
        force_ocr: If True, skip pdfplumber and use OCR directly.
        ocr_threshold: Minimum character count before OCR fallback.
                      Defaults to OCR_FALLBACK_THRESHOLD from config.
    
    Returns:
        Extracted Japanese text as a string.
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    threshold = ocr_threshold if ocr_threshold is not None else OCR_FALLBACK_THRESHOLD
    
    # Try pdfplumber first (unless force_ocr is set)
    if not force_ocr:
        text = extract_text_with_pdfplumber(pdf_path)
        
        # Check if we got enough text
        if len(text.strip()) >= threshold:
            return text
        
        # Text extraction yielded little content, try OCR
        print(f"Text extraction yielded {len(text)} chars, falling back to OCR...")
    
    # Use OCR
    try:
        return extract_text_with_ocr(pdf_path)
    except ImportError as e:
        if force_ocr:
            raise
        # If OCR isn't available and we have some text, return what we have
        print(f"OCR not available: {e}")
        print("Returning pdfplumber results...")
        return text


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m processor.extract_text <pdf_path> [--ocr]")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    force_ocr = "--ocr" in sys.argv
    
    try:
        extracted = extract_text(pdf_file, force_ocr=force_ocr)
        print(f"Extracted {len(extracted)} characters:")
        print("-" * 40)
        # Print first 500 chars as preview
        print(extracted[:500])
        if len(extracted) > 500:
            print(f"... ({len(extracted) - 500} more characters)")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
