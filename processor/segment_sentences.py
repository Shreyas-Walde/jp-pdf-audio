"""
Sentence segmentation module for the Japanese PDF Audio Reader.

This module handles:
- Splitting chapter text into individual sentences
- Using spaCy with Japanese model (ja_core_news_sm)
- Generating unique sentence IDs

Japanese sentence boundaries are detected using:
- Full-width period (。)
- Question marks (？ and ?)
- Exclamation marks (！ and !)
- End of quoted speech patterns

Usage:
    from processor.segment_sentences import segment_sentences
    
    sentences = segment_sentences(chapter_text, chapter_id="xyz789")
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
class Sentence:
    """Represents a segmented sentence."""
    id: str
    chapter_id: str
    text: str
    order_index: int


def generate_sentence_id() -> str:
    """Generate a unique sentence identifier."""
    return str(uuid.uuid4())


def load_spacy_model():
    """
    Load the spaCy Japanese model.
    
    Returns:
        The loaded spaCy model, or None if not available.
    """
    try:
        import spacy
        nlp = spacy.load("ja_core_news_sm")
        logger.info("Loaded spaCy model: ja_core_news_sm")
        return nlp
    except OSError:
        logger.warning(
            "spaCy model 'ja_core_news_sm' not found. "
            "Install with: python -m spacy download ja_core_news_sm"
        )
        return None
    except ImportError:
        logger.warning("spaCy not installed. Using regex fallback.")
        return None


def segment_with_spacy(text: str, nlp) -> List[str]:
    """
    Segment text into sentences using spaCy.
    
    Args:
        text: Japanese text to segment.
        nlp: Loaded spaCy model.
        
    Returns:
        List of sentence strings.
    """
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    logger.debug(f"spaCy segmented into {len(sentences)} sentences")
    return sentences


def segment_with_regex(text: str) -> List[str]:
    """
    Segment text into sentences using regex (fallback method).
    
    This is a deterministic rule-based approach for Japanese text.
    
    Args:
        text: Japanese text to segment.
        
    Returns:
        List of sentence strings.
    """
    logger.info("Using regex-based sentence segmentation")
    
    # Japanese sentence-ending patterns
    # - 。 (full-width period)
    # - ？ or ? (question marks)
    # - ！ or ! (exclamation marks)
    # - 」 (closing quotation when followed by certain patterns)
    
    # Split on sentence-ending punctuation, keeping the punctuation
    pattern = r'([。？！?!]+(?:」)?)'
    
    # Split and keep delimiters
    parts = re.split(pattern, text)
    
    sentences = []
    current = ""
    
    for part in parts:
        if not part:
            continue
        
        current += part
        
        # If this part is a sentence-ending punctuation, finalize sentence
        if re.match(pattern, part):
            sentence = current.strip()
            if sentence:
                sentences.append(sentence)
            current = ""
    
    # Handle any remaining text
    if current.strip():
        sentences.append(current.strip())
    
    logger.debug(f"Regex segmented into {len(sentences)} sentences")
    return sentences


def clean_sentence(sentence: str) -> str:
    """
    Clean a sentence for processing.
    
    Args:
        sentence: Raw sentence text.
        
    Returns:
        Cleaned sentence text.
    """
    # Remove excess whitespace
    sentence = " ".join(sentence.split())
    
    # Remove leading/trailing whitespace
    sentence = sentence.strip()
    
    return sentence


def is_valid_sentence(sentence: str, min_length: int = 2) -> bool:
    """
    Check if a sentence is valid for TTS processing.
    
    Args:
        sentence: The sentence to validate.
        min_length: Minimum character length.
        
    Returns:
        True if the sentence is valid.
    """
    if len(sentence) < min_length:
        return False
    
    # Must contain at least some Japanese characters or alphanumeric
    has_content = bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\w]', sentence))
    
    return has_content


def segment_sentences(
    text: str,
    chapter_id: str,
    use_spacy: bool = True,
    min_length: int = 2
) -> List[Sentence]:
    """
    Segment chapter text into individual sentences.
    
    Uses spaCy with ja_core_news_sm model for accurate Japanese
    sentence segmentation. Falls back to regex-based segmentation
    if spaCy is not available.
    
    This is a deterministic process with no LLM involvement.
    
    Args:
        text: Chapter text to segment.
        chapter_id: The chapter ID to associate sentences with.
        use_spacy: Whether to attempt using spaCy (True by default).
        min_length: Minimum sentence length to include.
        
    Returns:
        List of Sentence objects in order.
    """
    logger.info(f"Starting sentence segmentation for chapter {chapter_id}")
    logger.info(f"Input text length: {len(text)} characters")
    
    if not text.strip():
        logger.warning("Empty text provided, returning empty list")
        return []
    
    # Try spaCy first
    nlp = None
    if use_spacy:
        nlp = load_spacy_model()
    
    # Segment the text
    if nlp is not None:
        raw_sentences = segment_with_spacy(text, nlp)
    else:
        raw_sentences = segment_with_regex(text)
    
    # Clean and validate sentences
    sentences = []
    for i, raw_sent in enumerate(raw_sentences):
        cleaned = clean_sentence(raw_sent)
        
        if not is_valid_sentence(cleaned, min_length):
            logger.debug(f"Skipping invalid sentence: '{cleaned[:30]}...'")
            continue
        
        sentence = Sentence(
            id=generate_sentence_id(),
            chapter_id=chapter_id,
            text=cleaned,
            order_index=len(sentences)  # Use filtered index
        )
        sentences.append(sentence)
    
    logger.info(
        f"Segmentation complete: {len(sentences)} valid sentences "
        f"(filtered from {len(raw_sentences)} raw)"
    )
    
    return sentences


if __name__ == "__main__":
    import sys
    
    # Demo with sample Japanese text
    sample_text = """
こんにちは。私は田中です。はじめまして。
今日はいい天気ですね？そうですね！
明日、東京へ行きます。電車で行きますか、それともバスで行きますか？
バスで行きます。
「おはようございます」と言いました。彼女は「おはよう」と返事しました。
日本語を勉強しています。とても面白いです。
"""
    
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            sample_text = f.read()
    
    logger.setLevel(logging.DEBUG)
    
    sentences = segment_sentences(sample_text, chapter_id="test-chapter-456")
    
    print("\n" + "=" * 50)
    print(f"Segmented into {len(sentences)} sentences:")
    print("=" * 50)
    
    for sent in sentences:
        print(f"\n[{sent.order_index}] {sent.text}")
        print(f"    ID: {sent.id}")
