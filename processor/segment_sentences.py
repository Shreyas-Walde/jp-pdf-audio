"""
Sentence segmentation module for the Japanese PDF Audio Reader.

This module handles:
- Splitting chapter text into individual sentences
- Rule-based segmentation on Japanese punctuation (PRIMARY)
- spaCy with Japanese model as optional fallback
- Generating unique sentence IDs

Japanese sentence boundaries are detected using:
- Full-width period (。) - primary sentence terminator
- Question marks (？) - interrogative terminator
- Exclamation marks (！) - exclamatory terminator

Rule-based segmentation is preferred for Japanese textbooks because:
1. Textbooks use consistent, standard punctuation
2. NLP models like spaCy may over-merge short conversational sentences
3. Deterministic behavior is more predictable for TTS

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


def segment_with_rules(text: str) -> List[str]:
    """
    Segment text into sentences using rule-based Japanese punctuation splitting.
    
    This is the PRIMARY segmentation method for Japanese textbooks.
    
    Splits on:
    - 。 (full-width period) - standard sentence terminator
    - ？ (full-width question mark) - interrogative
    - ！ (full-width exclamation mark) - exclamatory
    
    Args:
        text: Japanese text to segment.
        
    Returns:
        List of sentence strings in order.
    """
    logger.info("Using rule-based Japanese sentence segmentation")
    
    # Japanese sentence-ending punctuation
    # We focus on full-width variants as these are standard in Japanese text
    # Half-width ?, ! are rare but included for robustness
    
    # Split on sentence-ending punctuation, keeping the punctuation attached
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
    
    logger.debug(f"Rule-based segmented into {len(sentences)} sentences")
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


@dataclass
class ValidationResult:
    """Result of sentence validation for TTS."""
    is_valid: bool
    reason: str
    sentence: str


def validate_sentence_for_tts(sentence: str, min_length: int = 2) -> ValidationResult:
    """
    Validate a sentence for TTS quality.
    
    This is a quality gate to prevent malformed text from being
    sent to the TTS engine, which would produce incorrect audio.
    
    A sentence is VALID only if:
    - Length > min_length characters
    - Contains at least one Japanese character (hiragana, katakana, or kanji)
    - Does NOT contain standalone ASCII digits mixed with Japanese
    - Does NOT contain random ASCII letters mixed with Japanese
    - Does NOT contain control characters
    
    Args:
        sentence: The sentence text to validate.
        min_length: Minimum character length (default: 2).
        
    Returns:
        ValidationResult with is_valid, reason, and original sentence.
    """
    # Check minimum length
    if len(sentence) < min_length:
        return ValidationResult(
            is_valid=False,
            reason=f"Too short ({len(sentence)} chars, min: {min_length})",
            sentence=sentence
        )
    
    # Must contain at least one Japanese character
    japanese_pattern = re.compile(
        r"[\u3040-\u309F"   # Hiragana
        r"\u30A0-\u30FF"    # Katakana
        r"\u4E00-\u9FFF"    # CJK Unified Ideographs (kanji)
        r"\u3400-\u4DBF]"   # CJK Extension A
    )
    
    if not japanese_pattern.search(sentence):
        return ValidationResult(
            is_valid=False,
            reason="No Japanese characters (hiragana, katakana, or kanji)",
            sentence=sentence
        )
    
    # Check for control characters (except newlines/tabs which should be stripped anyway)
    control_pattern = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
    if control_pattern.search(sentence):
        return ValidationResult(
            is_valid=False,
            reason="Contains control characters",
            sentence=sentence
        )
    
    # Check for standalone ASCII digits between Japanese characters
    # Pattern: Japanese char + digit(s) + Japanese char
    ascii_digit_junk = re.compile(
        r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]"  # Japanese char
        r"[0-9]+"                                      # ASCII digits
        r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]"  # Japanese char
    )
    if ascii_digit_junk.search(sentence):
        return ValidationResult(
            is_valid=False,
            reason="Contains standalone ASCII digits mixed with Japanese",
            sentence=sentence
        )
    
    # Check for standalone ASCII letters between Japanese characters
    # Pattern: Japanese char + letter(s) + Japanese char
    ascii_letter_junk = re.compile(
        r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]"  # Japanese char
        r"[a-zA-Z]+"                                   # ASCII letters
        r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]"  # Japanese char
    )
    if ascii_letter_junk.search(sentence):
        return ValidationResult(
            is_valid=False,
            reason="Contains random ASCII letters mixed with Japanese",
            sentence=sentence
        )
    
    # Check for backslashes (common PDF extraction artifact)
    if "\\" in sentence:
        return ValidationResult(
            is_valid=False,
            reason="Contains backslash (likely extraction artifact)",
            sentence=sentence
        )
    
    # All checks passed
    return ValidationResult(
        is_valid=True,
        reason="Valid",
        sentence=sentence
    )


def is_valid_sentence(sentence: str, min_length: int = 2) -> bool:
    """
    Check if a sentence is valid for TTS processing.
    
    This is a simplified wrapper around validate_sentence_for_tts.
    Use validate_sentence_for_tts() for detailed validation results.
    
    Args:
        sentence: The sentence to validate.
        min_length: Minimum character length.
        
    Returns:
        True if the sentence is valid for TTS.
    """
    result = validate_sentence_for_tts(sentence, min_length)
    return result.is_valid


def segment_sentences(
    text: str,
    chapter_id: str,
    use_spacy_fallback: bool = False,
    min_length: int = 2
) -> List[Sentence]:
    """
    Segment chapter text into individual sentences.
    
    Uses rule-based Japanese punctuation splitting as the PRIMARY method.
    This works best for textbooks with clear, consistent punctuation.
    
    spaCy can be used as an optional fallback for edge cases, but is
    NOT recommended for typical textbook content as it tends to over-merge.
    
    This is a deterministic process with no LLM involvement.
    
    Args:
        text: Chapter text to segment.
        chapter_id: The chapter ID to associate sentences with.
        use_spacy_fallback: If True, use spaCy for segmentation instead of
            rule-based. NOT recommended for typical Japanese textbooks.
        min_length: Minimum sentence length to include.
        
    Returns:
        List of Sentence objects in order.
    """
    logger.info(f"Starting sentence segmentation for chapter {chapter_id}")
    logger.info(f"Input text length: {len(text)} characters")
    
    if not text.strip():
        logger.warning("Empty text provided, returning empty list")
        return []
    
    # Use rule-based segmentation as PRIMARY method
    # spaCy is only used if explicitly requested (not recommended for textbooks)
    if use_spacy_fallback:
        nlp = load_spacy_model()
        if nlp is not None:
            raw_sentences = segment_with_spacy(text, nlp)
        else:
            logger.warning("spaCy not available, falling back to rule-based")
            raw_sentences = segment_with_rules(text)
    else:
        raw_sentences = segment_with_rules(text)
    
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
