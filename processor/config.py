"""
Configuration constants for the Japanese PDF Audio Reader processing pipeline.

This module centralizes all configuration settings including paths, thresholds,
and external service URLs.
"""

from pathlib import Path
import os

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"

# Book storage
BOOKS_DIR = DATA_DIR / "books"

# Audio storage
AUDIO_DIR = DATA_DIR / "audio"
SENTENCES_AUDIO_DIR = AUDIO_DIR / "sentences"
CHAPTERS_AUDIO_DIR = AUDIO_DIR / "chapters"

# Database
DATABASE_PATH = DATA_DIR / "metadata.db"

# Text extraction settings
OCR_FALLBACK_THRESHOLD = 100  # Minimum characters before considering OCR fallback
TESSERACT_LANG = "jpn"  # Japanese language pack for Tesseract

# Voicevox TTS settings
VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://localhost:50021")
VOICEVOX_SPEAKER_ID = int(os.getenv("VOICEVOX_SPEAKER_ID", "1"))  # Default speaker

# Audio settings
AUDIO_FORMAT = "ogg"  # Opus codec in Ogg container
AUDIO_SAMPLE_RATE = 24000


def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    for directory in [BOOKS_DIR, SENTENCES_AUDIO_DIR, CHAPTERS_AUDIO_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # Print configuration for debugging
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"BOOKS_DIR: {BOOKS_DIR}")
    print(f"DATABASE_PATH: {DATABASE_PATH}")
    print(f"VOICEVOX_URL: {VOICEVOX_URL}")
    ensure_directories()
    print("Directories created successfully.")
