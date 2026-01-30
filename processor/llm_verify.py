"""
LLM-based page verification module for the Japanese PDF Audio Reader.

This module uses OpenRouter API to verify and clean Japanese text
extracted from PDFs, following the LLM_VERIFICATION.md spec.

Key principles (from LLM_VERIFICATION.md):
- LLM operates on ONE page at a time
- LLM outputs structured JSON with sentences + confidence
- LLM never modifies layout, only cleans text
- LLM removes noise: O → 。, fJ → hiragana, standalone ASCII/digits

Usage:
    from processor.llm_verify import LLMVerifier
    
    verifier = LLMVerifier()
    result = verifier.verify_page(1, ["line1", "line2"])
    
    for sentence in result.sentences:
        print(f"{sentence.clean_text} (confidence: {sentence.confidence})")
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional, List

import httpx

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# OpenRouter configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.0-flash-001"

# System prompt for page-level verification (per LLM_VERIFICATION.md)
PAGE_VERIFICATION_PROMPT = """You are a Japanese text verification assistant for textbook PDFs.

Your task is to clean extracted text and identify proper Japanese sentences.

INPUT: Raw text lines from a PDF page (may contain OCR errors and artifacts)

RULES:
1. Fix obvious OCR errors:
   - O → 。 (capital O should be Japanese period)
   - 0 → 。 (digit zero should be Japanese period when between Japanese text)
   - fJ, fl → appropriate hiragana
   - Random ASCII letters between Japanese → remove
   - Standalone digits between Japanese → remove

2. Fix truncated/incomplete words at sentence start:
   - は、 → はい、 (incomplete "yes")
   - い、 → いいえ、 (incomplete "no")  
   - Other obviously incomplete words should be completed based on context

3. Fix merged sentences:
   - If two sentences are merged without proper punctuation, split them
   - Example: "です。わたしは" should stay as two sentences

4. Detect sentence boundaries (。！？)
5. Preserve all valid Japanese characters
6. Ignore page numbers, headers, and section markers like "I."
7. Do NOT translate or add new content not implied by context
8. Discard text that is too corrupted to recover

OUTPUT: Valid JSON only, in this exact format:
{
  "sentences": [
    {"clean_text": "はい、わたしはジョンです。", "confidence": 0.97},
    {"clean_text": "あなたは学生ですか？", "confidence": 0.95}
  ]
}

If no valid sentences found, return: {"sentences": []}
"""


@dataclass
class VerifiedSentence:
    """A verified sentence from LLM output."""
    clean_text: str
    confidence: float
    
    def to_dict(self) -> dict:
        return {
            "cleanText": self.clean_text,
            "confidence": self.confidence,
        }


@dataclass
class PageVerificationResult:
    """Result of LLM page verification."""
    page_number: int
    sentences: List[VerifiedSentence] = field(default_factory=list)
    raw_text: str = ""
    model_used: str = ""
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "pageNumber": self.page_number,
            "sentences": [s.to_dict() for s in self.sentences],
            "verified": self.success,
            "error": self.error,
        }


@dataclass
class VerificationResult:
    """Result of LLM text verification (legacy format)."""
    original_text: str
    verified_text: str
    model_used: str
    success: bool
    error: Optional[str] = None


class LLMVerifier:
    """
    LLM-based page verification using OpenRouter API.
    
    Uses synchronous HTTP calls for reliability.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        confidence_threshold: float = 0.9,
        timeout: float = 60.0
    ):
        """
        Initialize the LLM verifier.
        
        Args:
            api_key: OpenRouter API key (reads from OPENROUTER_API_KEY env var if not provided).
            model: Model ID to use.
            temperature: LLM temperature (lower = more deterministic).
            max_tokens: Maximum tokens in response.
            confidence_threshold: Minimum confidence for TTS eligibility.
            timeout: HTTP request timeout in seconds.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.confidence_threshold = confidence_threshold
        self.timeout = timeout
        
        logger.info(f"LLM Verifier initialized (model: {model})")
    
    def verify_page(
        self,
        page_number: int,
        lines: List[str],
    ) -> PageVerificationResult:
        """
        Verify a single page of text using LLM.
        
        Args:
            page_number: The page number.
            lines: List of text lines from the page.
            
        Returns:
            PageVerificationResult with verified sentences.
        """
        raw_text = "\n".join(lines)
        
        if not raw_text.strip():
            return PageVerificationResult(
                page_number=page_number,
                sentences=[],
                raw_text=raw_text,
                model_used=self.model,
                success=True
            )
        
        try:
            response = httpx.post(
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/jp-pdf-audio",
                    "X-Title": "Japanese PDF Audio Reader",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": PAGE_VERIFICATION_PROMPT
                        },
                        {
                            "role": "user",
                            "content": f"Verify and clean these lines from page {page_number}:\n\n{raw_text}"
                        }
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract LLM response
            llm_output = result["choices"][0]["message"]["content"].strip()
            
            # Parse JSON from LLM response
            sentences = self._parse_llm_json(llm_output)
            
            logger.info(f"Page {page_number}: LLM found {len(sentences)} sentences")
            
            return PageVerificationResult(
                page_number=page_number,
                sentences=sentences,
                raw_text=raw_text,
                model_used=self.model,
                success=True
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
            return PageVerificationResult(
                page_number=page_number,
                sentences=[],
                raw_text=raw_text,
                model_used=self.model,
                success=False,
                error=f"API error: {e.response.status_code}"
            )
        except httpx.TimeoutException:
            logger.error(f"Request timeout for page {page_number}")
            return PageVerificationResult(
                page_number=page_number,
                sentences=[],
                raw_text=raw_text,
                model_used=self.model,
                success=False,
                error="Request timeout"
            )
        except Exception as e:
            logger.error(f"LLM verification failed for page {page_number}: {e}")
            return PageVerificationResult(
                page_number=page_number,
                sentences=[],
                raw_text=raw_text,
                model_used=self.model,
                success=False,
                error=str(e)
            )
    
    def _parse_llm_json(self, llm_output: str) -> List[VerifiedSentence]:
        """Parse JSON from LLM output, handling markdown code blocks."""
        # Remove markdown code blocks if present
        llm_output = re.sub(r'^```json\s*', '', llm_output)
        llm_output = re.sub(r'^```\s*', '', llm_output)
        llm_output = re.sub(r'\s*```$', '', llm_output)
        llm_output = llm_output.strip()
        
        try:
            data = json.loads(llm_output)
            sentences = []
            
            for item in data.get("sentences", []):
                clean_text = item.get("clean_text", "").strip()
                confidence = float(item.get("confidence", 0.0))
                
                if clean_text:
                    sentences.append(VerifiedSentence(
                        clean_text=clean_text,
                        confidence=confidence
                    ))
            
            return sentences
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON: {e}")
            logger.debug(f"Raw output: {llm_output[:500]}")
            return []
    
    # Alias for backward compatibility
    def verify_page_sync(self, page_number: int, lines: List[str]) -> PageVerificationResult:
        """Alias for verify_page (already synchronous)."""
        return self.verify_page(page_number, lines)
    
    def verify_text(self, raw_text: str) -> VerificationResult:
        """
        Legacy method: Verify text and return cleaned version.
        
        For backward compatibility with existing pipeline.
        """
        if not raw_text.strip():
            return VerificationResult(
                original_text=raw_text,
                verified_text="",
                model_used=self.model,
                success=True
            )
        
        # Use page verification and concatenate sentences
        lines = raw_text.split("\n")
        result = self.verify_page(1, lines)
        
        if result.success and result.sentences:
            verified_text = "".join(s.clean_text for s in result.sentences)
        else:
            verified_text = raw_text  # Fallback
        
        return VerificationResult(
            original_text=raw_text,
            verified_text=verified_text,
            model_used=self.model,
            success=result.success,
            error=result.error
        )
    
    # Alias for backward compatibility
    def verify_text_sync(self, raw_text: str) -> VerificationResult:
        """Alias for verify_text (already synchronous)."""
        return self.verify_text(raw_text)
    
    def verify_pages(self, pages: List[dict]) -> List[dict]:
        """
        Verify multiple pages.
        
        Args:
            pages: List of page dicts with 'page_number' and 'lines' or 'raw_text'.
            
        Returns:
            List of page dicts with verification results added.
        """
        verified_pages = []
        total = len(pages)
        
        for i, page in enumerate(pages, 1):
            page_number = page.get("page_number", i)
            lines = page.get("lines", [])
            
            if not lines and "raw_text" in page:
                lines = page["raw_text"].split("\n")
            
            result = self.verify_page(page_number, lines)
            
            verified_page = {
                **page,
                "verified": result.success,
                "sentences": [s.to_dict() for s in result.sentences],
                "error": result.error,
            }
            verified_pages.append(verified_page)
            
            if i % 5 == 0 or i == total:
                logger.info(f"Verified {i}/{total} pages")
        
        return verified_pages
    
    # Alias for backward compatibility
    def verify_pages_sync(self, pages: List[dict]) -> List[dict]:
        """Alias for verify_pages (already synchronous)."""
        return self.verify_pages(pages)


if __name__ == "__main__":
    # Demo with sample text
    sample_lines = [
        "I. わたしは にほんじんです O",
        "わたしは はやしです O",
        "h あなたは がくせいですか。",
    ]
    
    print("=" * 50)
    print("LLM Page Verification Demo")
    print("=" * 50)
    print(f"\nInput lines:")
    for line in sample_lines:
        print(f"  {line}")
    
    try:
        verifier = LLMVerifier()
        result = verifier.verify_page(1, sample_lines)
        
        print(f"\n{'✅' if result.success else '❌'} Verification {'succeeded' if result.success else 'failed'}")
        print(f"Model: {result.model_used}")
        print(f"\nVerified sentences ({len(result.sentences)}):")
        for s in result.sentences:
            status = "✓" if s.confidence >= 0.9 else "?"
            print(f"  {status} [{s.confidence:.2f}] {s.clean_text}")
        
        if result.error:
            print(f"\nError: {result.error}")
            
    except ValueError as e:
        print(f"\nError: {e}")
        print("Set OPENROUTER_API_KEY environment variable to test.")
