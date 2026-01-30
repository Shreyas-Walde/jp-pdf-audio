"""
Audio stitching module for the Japanese PDF Audio Reader.

This module handles:
- Concatenating sentence audio files into chapter audio
- Converting WAV to compressed format (OGG/Opus)
- Managing audio file paths

Usage:
    from processor.stitch_audio import stitch_chapter_audio
    
    chapter_audio_path = stitch_chapter_audio(sentence_audio_paths, chapter_id)
"""

import logging
from pathlib import Path
from typing import List, Optional

from pydub import AudioSegment

from .config import CHAPTERS_AUDIO_DIR, SENTENCES_AUDIO_DIR, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Silence gap between sentences (milliseconds)
SENTENCE_GAP_MS = 500


def load_audio_file(audio_path: Path) -> Optional[AudioSegment]:
    """
    Load an audio file using pydub.
    
    Args:
        audio_path: Path to the audio file.
        
    Returns:
        AudioSegment if successful, None otherwise.
    """
    try:
        return AudioSegment.from_file(str(audio_path))
    except Exception as e:
        logger.error(f"Failed to load audio file {audio_path}: {e}")
        return None


def create_silence(duration_ms: int = SENTENCE_GAP_MS) -> AudioSegment:
    """
    Create a silent audio segment.
    
    Args:
        duration_ms: Duration of silence in milliseconds.
        
    Returns:
        Silent AudioSegment.
    """
    return AudioSegment.silent(duration=duration_ms)


def stitch_audio_files(
    audio_paths: List[Path],
    gap_ms: int = SENTENCE_GAP_MS
) -> Optional[AudioSegment]:
    """
    Concatenate multiple audio files with gaps between them.
    
    Args:
        audio_paths: List of paths to audio files in order.
        gap_ms: Gap between audio segments in milliseconds.
        
    Returns:
        Combined AudioSegment, or None if no valid audio files.
    """
    if not audio_paths:
        logger.warning("No audio paths provided for stitching")
        return None
    
    combined = None
    silence = create_silence(gap_ms)
    successful_count = 0
    
    for i, path in enumerate(audio_paths):
        segment = load_audio_file(path)
        
        if segment is None:
            logger.warning(f"Skipping missing/invalid audio: {path}")
            continue
        
        if combined is None:
            combined = segment
        else:
            combined = combined + silence + segment
        
        successful_count += 1
    
    logger.info(f"Stitched {successful_count}/{len(audio_paths)} audio files")
    return combined


def export_audio(
    audio: AudioSegment,
    output_path: Path,
    format: str = "ogg",
    bitrate: str = "64k"
) -> Path:
    """
    Export audio segment to file.
    
    Args:
        audio: AudioSegment to export.
        output_path: Destination path.
        format: Output format (ogg, mp3, wav, etc.)
        bitrate: Bitrate for compressed formats.
        
    Returns:
        Path to the exported file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    export_params = {}
    if format in ("ogg", "mp3"):
        export_params["bitrate"] = bitrate
    if format == "ogg":
        export_params["codec"] = "libopus"
    
    try:
        audio.export(str(output_path), format=format, **export_params)
        logger.info(f"Exported audio to: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to export audio: {e}")
        raise


def stitch_chapter_audio(
    sentence_audio_paths: List[Path],
    chapter_id: str,
    output_dir: Optional[Path] = None,
    gap_ms: int = SENTENCE_GAP_MS,
    output_format: str = "ogg"
) -> Optional[Path]:
    """
    Create chapter-level audio by stitching sentence audio files.
    
    Args:
        sentence_audio_paths: List of sentence audio file paths in order.
        chapter_id: Unique ID for the chapter.
        output_dir: Directory for chapter audio. Defaults to CHAPTERS_AUDIO_DIR.
        gap_ms: Gap between sentences in milliseconds.
        output_format: Output audio format.
        
    Returns:
        Path to the chapter audio file, or None if stitching failed.
    """
    logger.info(f"Stitching chapter audio: {chapter_id}")
    logger.info(f"  Input files: {len(sentence_audio_paths)}")
    
    if output_dir is None:
        output_dir = CHAPTERS_AUDIO_DIR
    
    ensure_directories()
    
    # Stitch audio files
    combined = stitch_audio_files(sentence_audio_paths, gap_ms)
    
    if combined is None:
        logger.error(f"Failed to stitch chapter {chapter_id}: no valid audio")
        return None
    
    # Export to compressed format
    output_path = output_dir / f"{chapter_id}.{output_format}"
    
    try:
        return export_audio(combined, output_path, format=output_format)
    except Exception as e:
        logger.error(f"Failed to export chapter audio: {e}")
        return None


def get_sentence_audio_paths(
    sentence_ids: List[str],
    audio_dir: Optional[Path] = None,
    extension: str = "mp3"
) -> List[Path]:
    """
    Get paths to sentence audio files by their IDs.
    
    Args:
        sentence_ids: List of sentence IDs.
        audio_dir: Directory containing sentence audio.
        extension: Audio file extension (default: mp3 for edge-tts).
        
    Returns:
        List of paths (only existing files).
    """
    if audio_dir is None:
        audio_dir = SENTENCES_AUDIO_DIR
    
    paths = []
    for sid in sentence_ids:
        path = audio_dir / f"{sid}.{extension}"
        if path.exists():
            paths.append(path)
        else:
            logger.warning(f"Sentence audio not found: {path}")
    
    return paths


if __name__ == "__main__":
    import sys
    
    logger.setLevel(logging.DEBUG)
    
    if len(sys.argv) < 3:
        print("Usage: python -m processor.stitch_audio <chapter_id> <audio_file1> [audio_file2] ...")
        print("\nExample:")
        print("  python -m processor.stitch_audio ch-001 sent-001.wav sent-002.wav sent-003.wav")
        sys.exit(1)
    
    chapter_id = sys.argv[1]
    audio_files = [Path(f) for f in sys.argv[2:]]
    
    # Validate files exist
    valid_files = [f for f in audio_files if f.exists()]
    if not valid_files:
        print("Error: No valid audio files found")
        sys.exit(1)
    
    print(f"Stitching {len(valid_files)} audio files for chapter: {chapter_id}")
    
    result = stitch_chapter_audio(valid_files, chapter_id)
    
    if result:
        print(f"Chapter audio created: {result}")
    else:
        print("Failed to create chapter audio")
        sys.exit(1)
