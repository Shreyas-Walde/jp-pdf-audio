"""
Page-level layout extraction for the Japanese PDF Audio Reader.

This module extracts positioned text spans from PDF pages, preserving
the visual layout for accurate UI rendering.

Each text span includes:
- Position (x0, y0, x1, y1)
- Text content
- Font information
- Unique ID for mapping

Usage:
    from processor.page_extractor import extract_page_layouts
    
    pages = extract_page_layouts(pdf_path)
    for page in pages:
        print(f"Page {page.page_number}: {len(page.spans)} spans")
"""

import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import pdfplumber

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class TextSpan:
    """A positioned text element from the PDF."""
    id: str
    page_number: int
    text: str
    x0: float  # left position
    y0: float  # top position
    x1: float  # right position
    y1: float  # bottom position
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    
    @property
    def width(self) -> float:
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        return self.y1 - self.y0
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "pageNumber": self.page_number,
            "text": self.text,
            "x": round(self.x0, 2),
            "y": round(self.y0, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2),
            "fontSize": round(self.font_size, 2) if self.font_size else None,
        }


@dataclass
class PageLayout:
    """Layout data for a single PDF page."""
    page_number: int
    width: float
    height: float
    spans: List[TextSpan] = field(default_factory=list)
    raw_text: str = ""
    verified_text: str = ""  # After LLM cleaning
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "pageNumber": self.page_number,
            "width": round(self.width, 2),
            "height": round(self.height, 2),
            "spans": [s.to_dict() for s in self.spans],
            "rawText": self.raw_text,
            "verifiedText": self.verified_text,
        }


def _group_chars_to_words(chars: List[dict], page_number: int) -> List[TextSpan]:
    """
    Group individual characters into word/phrase spans.
    
    pdfplumber extracts individual characters. We group them into
    logical spans based on proximity and line breaks.
    """
    if not chars:
        return []
    
    spans = []
    current_span_chars = []
    current_y = None
    current_x_end = None
    
    # Threshold for considering chars on same line (in points)
    Y_TOLERANCE = 3.0
    # Threshold for word spacing (in points)
    SPACE_THRESHOLD = 5.0
    
    for char in chars:
        char_text = char.get("text", "")
        if not char_text.strip() and not current_span_chars:
            continue
        
        x0 = char.get("x0", 0)
        y0 = char.get("top", 0)
        x1 = char.get("x1", 0)
        y1 = char.get("bottom", 0)
        
        # Check if this char continues the current span
        same_line = current_y is None or abs(y0 - current_y) < Y_TOLERANCE
        close_enough = current_x_end is None or (x0 - current_x_end) < SPACE_THRESHOLD
        
        if same_line and close_enough:
            # Continue current span
            current_span_chars.append(char)
            current_y = y0
            current_x_end = x1
        else:
            # Start new span, save current
            if current_span_chars:
                span = _create_span_from_chars(current_span_chars, page_number)
                if span and span.text.strip():
                    spans.append(span)
            
            current_span_chars = [char]
            current_y = y0
            current_x_end = x1
    
    # Don't forget the last span
    if current_span_chars:
        span = _create_span_from_chars(current_span_chars, page_number)
        if span and span.text.strip():
            spans.append(span)
    
    return spans


def _create_span_from_chars(chars: List[dict], page_number: int) -> Optional[TextSpan]:
    """Create a TextSpan from a list of character dicts."""
    if not chars:
        return None
    
    text = "".join(c.get("text", "") for c in chars)
    
    # Calculate bounding box
    x0 = min(c.get("x0", 0) for c in chars)
    y0 = min(c.get("top", 0) for c in chars)
    x1 = max(c.get("x1", 0) for c in chars)
    y1 = max(c.get("bottom", 0) for c in chars)
    
    # Get font info from first char
    font_name = chars[0].get("fontname")
    font_size = chars[0].get("size")
    
    return TextSpan(
        id=f"span-{uuid.uuid4().hex[:8]}",
        page_number=page_number,
        text=text,
        x0=x0,
        y0=y0,
        x1=x1,
        y1=y1,
        font_name=font_name,
        font_size=font_size,
    )


def extract_page_layouts(pdf_path: Path) -> List[PageLayout]:
    """
    Extract positioned text spans from each page of a PDF.
    
    Args:
        pdf_path: Path to the PDF file.
        
    Returns:
        List of PageLayout objects, one per page.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    logger.info(f"Extracting page layouts from: {pdf_path}")
    
    pages = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        logger.info(f"PDF has {total_pages} pages")
        
        for page_num, page in enumerate(pdf.pages, 1):
            # Extract individual characters with positions
            chars = page.chars or []
            
            # Group characters into spans
            spans = _group_chars_to_words(chars, page_num)
            
            # Build raw text from spans (in reading order)
            # Sort by y position (top to bottom), then x (left to right)
            sorted_spans = sorted(spans, key=lambda s: (s.y0, s.x0))
            raw_text = " ".join(s.text for s in sorted_spans)
            
            page_layout = PageLayout(
                page_number=page_num,
                width=page.width,
                height=page.height,
                spans=spans,
                raw_text=raw_text,
            )
            
            pages.append(page_layout)
            
            if page_num % 10 == 0 or page_num == total_pages:
                logger.info(f"Extracted {page_num}/{total_pages} pages")
    
    total_spans = sum(len(p.spans) for p in pages)
    logger.info(f"Extraction complete: {len(pages)} pages, {total_spans} spans")
    
    return pages


def extract_page_layouts_sync(pdf_path: Path) -> List[PageLayout]:
    """Synchronous alias for extract_page_layouts."""
    return extract_page_layouts(pdf_path)


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python page_extractor.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    pages = extract_page_layouts(pdf_path)
    
    print("\n" + "=" * 50)
    print("Page Layout Extraction Results")
    print("=" * 50)
    
    for page in pages[:3]:  # Show first 3 pages
        print(f"\nPage {page.page_number}:")
        print(f"  Size: {page.width} x {page.height}")
        print(f"  Spans: {len(page.spans)}")
        print(f"  Raw text preview: {page.raw_text[:100]}...")
        
        if page.spans:
            print(f"\n  First 5 spans:")
            for span in page.spans[:5]:
                print(f"    [{span.id}] '{span.text}' at ({span.x0:.1f}, {span.y0:.1f})")
    
    # Export first page as JSON sample
    if pages:
        sample = pages[0].to_dict()
        print(f"\n\nJSON sample (page 1):")
        print(json.dumps(sample, indent=2, ensure_ascii=False)[:500] + "...")
