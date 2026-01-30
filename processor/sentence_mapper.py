"""
Sentence-to-span mapping for the Japanese PDF Audio Reader.

This module maps segmented sentences back to their source text spans,
enabling the UI to highlight exact positions when playing audio.

Usage:
    from processor.sentence_mapper import map_sentences_to_spans
    
    mappings = map_sentences_to_spans(sentences, spans)
    for m in mappings:
        print(f"Sentence: {m.sentence_text}")
        print(f"Spans: {m.span_ids}")
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from .page_extractor import TextSpan
from .segment_sentences import Sentence

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SentenceSpanMapping:
    """Maps a sentence to its source spans in the page layout."""
    sentence_id: str
    sentence_text: str
    span_ids: List[str] = field(default_factory=list)
    page_number: Optional[int] = None
    audio_path: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "sentenceId": self.sentence_id,
            "text": self.sentence_text,
            "spanIds": self.span_ids,
            "pageNumber": self.page_number,
            "audioPath": self.audio_path,
        }


def _normalize_for_matching(text: str) -> str:
    """Normalize text for fuzzy matching."""
    # Remove whitespace and common variations
    import re
    text = re.sub(r'\s+', '', text)
    text = text.replace('　', '')  # Full-width space
    return text


def map_sentences_to_spans(
    sentences: List[Sentence],
    spans: List[TextSpan],
) -> List[SentenceSpanMapping]:
    """
    Map sentences to their source text spans.
    
    Uses fuzzy text matching to find which spans compose each sentence.
    
    Args:
        sentences: List of segmented sentences.
        spans: List of text spans from page extraction.
        
    Returns:
        List of SentenceSpanMapping objects.
    """
    logger.info(f"Mapping {len(sentences)} sentences to {len(spans)} spans")
    
    mappings = []
    
    # Build a map of normalized span text to span objects
    span_map = {}
    for span in spans:
        normalized = _normalize_for_matching(span.text)
        if normalized:
            if normalized not in span_map:
                span_map[normalized] = []
            span_map[normalized].append(span)
    
    # Concatenate all spans to create a searchable text
    all_span_text = "".join(s.text for s in spans)
    all_span_text_normalized = _normalize_for_matching(all_span_text)
    
    # Track which spans have been assigned
    used_span_positions = set()
    
    for sentence in sentences:
        sentence_normalized = _normalize_for_matching(sentence.text)
        
        # Find spans that contribute to this sentence
        matched_span_ids = []
        current_page = None
        
        # Strategy 1: Direct substring matching
        # Find where this sentence appears in the concatenated span text
        pos = all_span_text_normalized.find(sentence_normalized)
        
        if pos != -1:
            # Walk through spans to find which ones cover this position
            char_count = 0
            for span in spans:
                span_normalized = _normalize_for_matching(span.text)
                span_start = char_count
                span_end = char_count + len(span_normalized)
                
                # Check if this span overlaps with the sentence position
                sentence_end = pos + len(sentence_normalized)
                
                if span_end > pos and span_start < sentence_end:
                    matched_span_ids.append(span.id)
                    if current_page is None:
                        current_page = span.page_number
                
                char_count = span_end
        
        # Strategy 2: If no direct match, try individual span matching
        if not matched_span_ids:
            for span in spans:
                span_normalized = _normalize_for_matching(span.text)
                # Check if span text is contained in sentence or vice versa
                if span_normalized and (
                    span_normalized in sentence_normalized or
                    sentence_normalized in span_normalized
                ):
                    matched_span_ids.append(span.id)
                    if current_page is None:
                        current_page = span.page_number
        
        mapping = SentenceSpanMapping(
            sentence_id=sentence.id,
            sentence_text=sentence.text,
            span_ids=matched_span_ids,
            page_number=current_page,
            audio_path=getattr(sentence, 'audio_path', None),
        )
        
        mappings.append(mapping)
    
    # Log mapping statistics
    mapped_count = sum(1 for m in mappings if m.span_ids)
    logger.info(f"Mapped {mapped_count}/{len(sentences)} sentences to spans")
    
    return mappings


def update_spans_with_sentence_ids(
    spans: List[TextSpan],
    mappings: List[SentenceSpanMapping]
) -> List[dict]:
    """
    Create span dicts with sentence IDs attached.
    
    Returns enriched span data for JSON export.
    """
    # Build reverse mapping: span_id -> sentence_id
    span_to_sentence = {}
    for mapping in mappings:
        for span_id in mapping.span_ids:
            span_to_sentence[span_id] = mapping.sentence_id
    
    enriched_spans = []
    for span in spans:
        span_dict = span.to_dict()
        span_dict["sentenceId"] = span_to_sentence.get(span.id)
        enriched_spans.append(span_dict)
    
    return enriched_spans


if __name__ == "__main__":
    # Demo with mock data
    print("Sentence Mapper Demo")
    print("=" * 50)
    
    # Create mock spans
    mock_spans = [
        TextSpan(id="s1", page_number=1, text="わたしは", x0=10, y0=10, x1=50, y1=20),
        TextSpan(id="s2", page_number=1, text="日本人", x0=55, y0=10, x1=90, y1=20),
        TextSpan(id="s3", page_number=1, text="です。", x0=95, y0=10, x1=120, y1=20),
        TextSpan(id="s4", page_number=1, text="東京に", x0=10, y0=30, x1=50, y1=40),
        TextSpan(id="s5", page_number=1, text="住んでいます。", x0=55, y0=30, x1=120, y1=40),
    ]
    
    # Create mock sentences
    mock_sentences = [
        Sentence(id="sent1", chapter_id="ch1", order_index=0, text="わたしは日本人です。"),
        Sentence(id="sent2", chapter_id="ch1", order_index=1, text="東京に住んでいます。"),
    ]
    
    mappings = map_sentences_to_spans(mock_sentences, mock_spans)
    
    for m in mappings:
        print(f"\nSentence: {m.sentence_text}")
        print(f"  Mapped to spans: {m.span_ids}")
        print(f"  Page: {m.page_number}")
