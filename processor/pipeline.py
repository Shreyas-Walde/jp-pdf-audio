"""
Main processing pipeline for the Japanese PDF Audio Reader.

This module orchestrates the entire processing flow:
1. PDF ingestion
2. Text extraction
3. LLM verification (cleans text using OpenRouter/Gemini)
4. Text normalization
5. Chapter detection
6. Sentence segmentation
7. Sentence validation (quality gate - filters invalid sentences)
8. TTS generation (optional, requires edge-tts)
9. Audio stitching (optional)
10. Database persistence
11. JSON export for frontend

Pipeline Flow:
    extract → LLM verify → normalize → segment → validate → TTS
                                                    ↓
                                              (invalid filtered)

Usage:
    # Process a PDF with all steps
    python -m processor.pipeline path/to/book.pdf --title "My Book"
    
    # Skip TTS (text-only processing)
    python -m processor.pipeline path/to/book.pdf --title "My Book" --skip-tts
    
    # Skip LLM verification (use regex-only cleaning)
    python -m processor.pipeline path/to/book.pdf --title "My Book" --skip-llm
    
    # Export existing book to JSON
    python -m processor.pipeline --export-only --book-id <book_id>
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .config import ensure_directories
from .database import Database, BookStatus
from .ingest_pdf import ingest_pdf
from .extract_text import extract_text
from .normalize_text import normalize_text
from .detect_chapters import detect_chapters
from .segment_sentences import segment_sentences, validate_sentence_for_tts
from .export_json import export_all_metadata, export_book_metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def process_pdf(
    pdf_path: str,
    title: str,
    language: str = "ja",
    skip_tts: bool = False,
    skip_llm: bool = False,
    force_ocr: bool = False
) -> Optional[str]:
    """
    Process a PDF through the entire pipeline.
    
    Args:
        pdf_path: Path to the PDF file.
        title: Title of the book.
        language: Language code (default: 'ja').
        skip_tts: If True, skip TTS generation.
        force_ocr: If True, force OCR even if text extraction succeeds.
        
    Returns:
        The book_id if successful, None otherwise.
    """
    ensure_directories()
    db = Database()
    db.create_tables()
    
    book_id = None
    
    try:
        # Step 1: Ingest PDF
        logger.info("=" * 50)
        logger.info("Step 1: Ingesting PDF")
        logger.info("=" * 50)
        book_id, stored_path = ingest_pdf(pdf_path)
        logger.info(f"Book ID: {book_id}")
        logger.info(f"Stored at: {stored_path}")
        
        # Create book record
        db.insert_book(
            book_id=book_id,
            title=title,
            language=language,
            pdf_path=str(stored_path),
            status=BookStatus.PROCESSING
        )
        
        # Step 2: Extract text
        logger.info("=" * 50)
        logger.info("Step 2: Extracting text")
        logger.info("=" * 50)
        raw_text = extract_text(stored_path, force_ocr=force_ocr)
        logger.info(f"Extracted {len(raw_text)} characters")
        
        if not raw_text.strip():
            raise ValueError("No text extracted from PDF")
        
        # Step 3: LLM Verification (optional)
        if not skip_llm:
            logger.info("=" * 50)
            logger.info("Step 3: LLM Verification (OpenRouter)")
            logger.info("=" * 50)
            try:
                from .llm_verify import LLMVerifier
                
                verifier = LLMVerifier()
                result = verifier.verify_text_sync(raw_text)
                
                if result.success:
                    verified_text = result.verified_text
                    logger.info(f"LLM verified text: {len(raw_text)} → {len(verified_text)} characters")
                    raw_text = verified_text
                else:
                    logger.warning(f"LLM verification failed: {result.error}")
                    logger.warning("Continuing with raw text")
                    
            except ImportError as e:
                logger.warning(f"LLM module not available: {e}")
                logger.warning("Skipping LLM verification")
            except ValueError as e:
                logger.warning(f"LLM API key not configured: {e}")
                logger.warning("Skipping LLM verification. Set OPENROUTER_API_KEY in .env file.")
            except Exception as e:
                logger.error(f"LLM verification error: {e}")
                logger.warning("Continuing with raw text")
        else:
            logger.info("Skipping LLM verification (--skip-llm flag)")
        
        # Step 4: Normalize text
        logger.info("=" * 50)
        logger.info("Step 4: Normalizing text")
        logger.info("=" * 50)
        normalized_text = normalize_text(raw_text)
        logger.info(f"Normalized to {len(normalized_text)} characters")
        
        # Step 5: Detect chapters
        logger.info("=" * 50)
        logger.info("Step 5: Detecting chapters")
        logger.info("=" * 50)
        chapters = detect_chapters(normalized_text, book_id)
        logger.info(f"Found {len(chapters)} chapters")
        
        for chapter in chapters:
            logger.info(f"  - {chapter.title}")
        
        # Step 6: Segment sentences for each chapter
        logger.info("=" * 50)
        logger.info("Step 6: Segmenting sentences")
        logger.info("=" * 50)
        
        all_sentences = []
        for chapter in chapters:
            sentences = segment_sentences(chapter.text, chapter.id)
            all_sentences.extend(sentences)
            logger.info(f"  {chapter.title}: {len(sentences)} sentences")
        
        logger.info(f"Total sentences: {len(all_sentences)}")
        
        # Step 7: Validate sentences (quality gate)
        logger.info("=" * 50)
        logger.info("Step 7: Validating sentences")
        logger.info("=" * 50)
        
        valid_sentences = []
        invalid_count = 0
        
        for sentence in all_sentences:
            validation = validate_sentence_for_tts(sentence.text)
            if validation.is_valid:
                valid_sentences.append(sentence)
            else:
                invalid_count += 1
                logger.debug(
                    f"Filtered invalid sentence [{sentence.id}]: {validation.reason} "
                    f"| '{sentence.text[:30]}...'"
                )
        
        logger.info(f"Valid sentences: {len(valid_sentences)} (filtered {invalid_count} invalid)")
        
        # Use only valid sentences for TTS and persistence
        all_sentences = valid_sentences
        
        # Step 8 & 9: TTS and stitching (optional)
        if not skip_tts:
            logger.info("=" * 50)
            logger.info("Step 8: Generating TTS audio")
            logger.info("=" * 50)
            try:
                from .generate_tts import generate_all_sentence_audio_sync
                from .stitch_audio import stitch_chapter_audio, get_sentence_audio_paths
                
                # Generate audio for all sentences using edge-tts
                # Note: Validation already done above, so all sentences here are valid
                audio_paths = generate_all_sentence_audio_sync(all_sentences)
                
                # Map audio paths back to sentences
                audio_path_map = {p.stem: p.name for p in audio_paths}
                for sentence in all_sentences:
                    if sentence.id in audio_path_map:
                        sentence.audio_path = audio_path_map[sentence.id]
                
                logger.info(f"Generated audio for {len(audio_paths)} sentences")
                
                logger.info("=" * 50)
                logger.info("Step 9: Stitching chapter audio")
                logger.info("=" * 50)
                
                for chapter in chapters:
                    chapter_sentences = [s for s in all_sentences if s.chapter_id == chapter.id]
                    sentence_ids = [s.id for s in chapter_sentences]
                    chapter_audio_paths = get_sentence_audio_paths(sentence_ids)
                    
                    if chapter_audio_paths:
                        chapter_audio = stitch_chapter_audio(chapter_audio_paths, chapter.id)
                        if chapter_audio:
                            chapter.audio_path = str(chapter_audio.name)
                            logger.info(f"  Created audio for: {chapter.title}")
                
            except ImportError as e:
                logger.warning(f"TTS not available: {e}")
                logger.warning("Skipping audio generation. Install edge-tts: pip install edge-tts")
            except Exception as e:
                logger.error(f"TTS failed: {e}")
                logger.warning("Continuing without audio")
        else:
            logger.info("Skipping TTS generation (--skip-tts flag)")
        
        # Step 10: Persist to database
        logger.info("=" * 50)
        logger.info("Step 10: Persisting to database")
        logger.info("=" * 50)
        
        for i, chapter in enumerate(chapters):
            db.insert_chapter(
                chapter_id=chapter.id,
                book_id=book_id,
                title=chapter.title,
                order_index=i,
                audio_path=getattr(chapter, 'audio_path', None)
            )
        
        for sentence in all_sentences:
            db.insert_sentence(
                sentence_id=sentence.id,
                chapter_id=sentence.chapter_id,
                order_index=sentence.order_index,
                text=sentence.text,
                audio_path=getattr(sentence, 'audio_path', None)
            )
        
        # Mark book as ready
        db.update_book_status(book_id, BookStatus.READY)
        logger.info(f"Persisted {len(chapters)} chapters, {len(all_sentences)} sentences")
        
        # Step 11: Export to JSON
        logger.info("=" * 50)
        logger.info("Step 11: Exporting to JSON")
        logger.info("=" * 50)
        export_all_metadata(db)
        logger.info("JSON export complete")
        
        # Done!
        logger.info("=" * 50)
        logger.info("✅ PROCESSING COMPLETE")
        logger.info("=" * 50)
        logger.info(f"Book ID: {book_id}")
        logger.info(f"Title: {title}")
        logger.info(f"Chapters: {len(chapters)}")
        logger.info(f"Sentences: {len(all_sentences)}")
        
        return book_id
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        if book_id:
            try:
                db.update_book_status(book_id, BookStatus.FAILED)
            except:
                pass
        raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Japanese PDF Audio Reader - Processing Pipeline"
    )
    
    parser.add_argument(
        "pdf_path",
        nargs="?",
        help="Path to the PDF file to process"
    )
    
    parser.add_argument(
        "--title", "-t",
        required=False,
        help="Title of the book"
    )
    
    parser.add_argument(
        "--language", "-l",
        default="ja",
        help="Language code (default: ja)"
    )
    
    parser.add_argument(
        "--skip-tts",
        action="store_true",
        help="Skip TTS audio generation"
    )
    
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip LLM text verification (use regex-only cleaning)"
    )
    
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Force OCR even if text extraction works"
    )
    
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Only export existing data to JSON"
    )
    
    parser.add_argument(
        "--book-id",
        help="Book ID for export-only mode"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Export-only mode
    if args.export_only:
        db = Database()
        if args.book_id:
            logger.info(f"Exporting book: {args.book_id}")
            export_book_metadata(db, args.book_id)
        else:
            logger.info("Exporting all books")
            export_all_metadata(db)
        logger.info("Export complete!")
        return 0
    
    # Normal processing mode
    if not args.pdf_path:
        parser.error("PDF path is required (unless using --export-only)")
    
    if not args.title:
        # Use filename as title if not provided
        args.title = Path(args.pdf_path).stem
    
    try:
        book_id = process_pdf(
            pdf_path=args.pdf_path,
            title=args.title,
            language=args.language,
            skip_tts=args.skip_tts,
            skip_llm=args.skip_llm,
            force_ocr=args.force_ocr
        )
        
        print(f"\n✅ Success! Book ID: {book_id}")
        print(f"\nTo view the book, start the web server:")
        print(f"  cd web && npm run dev")
        print(f"\nThen open: http://localhost:3000")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
