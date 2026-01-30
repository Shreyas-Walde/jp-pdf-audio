"""
Text-to-speech generation module for the Japanese PDF Audio Reader.

This module handles:
- Generating Japanese audio from text using Microsoft Edge TTS
- Saving audio files as MP3
- One file per sentence

Uses edge-tts which is a pure Python library with no native dependencies.

Usage:
    from processor.generate_tts import TTSEngine
    
    engine = TTSEngine()
    audio_path = await engine.generate_sentence_audio(sentence, sentence_id)
    
    # Or synchronous version:
    audio_path = engine.generate_sentence_audio_sync(sentence, sentence_id)
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

from .config import SENTENCES_AUDIO_DIR, ensure_directories
from .segment_sentences import validate_sentence_for_tts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Japanese voices available in Edge TTS
JAPANESE_VOICES = [
    "ja-JP-NanamiNeural",  # Female, default
    "ja-JP-KeitaNeural",   # Male
]

DEFAULT_VOICE = "ja-JP-NanamiNeural"


@dataclass
class Sentence:
    """Simple sentence dataclass for type hints."""
    id: str
    text: str


class TTSEngine:
    """
    Text-to-Speech engine using Microsoft Edge TTS.
    
    Provides a consistent interface for generating Japanese speech
    from text. Uses edge-tts which is free and requires no API keys.
    """
    
    def __init__(self, voice: str = DEFAULT_VOICE, rate: str = "+0%", pitch: str = "+0Hz"):
        """
        Initialize the TTS engine.
        
        Args:
            voice: The Edge TTS voice to use. Defaults to Japanese female voice.
            rate: Speech rate adjustment (e.g., "+10%", "-20%").
            pitch: Pitch adjustment (e.g., "+5Hz", "-10Hz").
        """
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        
        logger.info(f"TTS Engine initialized (voice: {voice}, rate: {rate}, pitch: {pitch})")
    
    async def generate_audio(self, text: str, output_path: Path) -> Path:
        """
        Generate audio for the given text.
        
        Args:
            text: Japanese text to synthesize.
            output_path: Path where the audio file will be saved.
            
        Returns:
            The path to the generated audio file.
        """
        import edge_tts
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate audio using edge-tts
        logger.debug(f"Generating audio for: {text[:50]}...")
        
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch
            )
            await communicate.save(str(output_path))
            logger.debug(f"Audio saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise
    
    def generate_audio_sync(self, text: str, output_path: Path) -> Path:
        """Synchronous wrapper for generate_audio."""
        return asyncio.run(self.generate_audio(text, output_path))
    
    async def generate_sentence_audio(
        self,
        text: str,
        sentence_id: str,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Generate audio for a single sentence.
        
        Args:
            text: The sentence text to synthesize.
            sentence_id: Unique ID for the sentence.
            output_dir: Directory to save audio. Defaults to SENTENCES_AUDIO_DIR.
            
        Returns:
            Path to the generated audio file.
        """
        if output_dir is None:
            output_dir = SENTENCES_AUDIO_DIR
        
        ensure_directories()
        
        # Use MP3 format (edge-tts default)
        output_path = output_dir / f"{sentence_id}.mp3"
        
        return await self.generate_audio(text, output_path)
    
    def generate_sentence_audio_sync(
        self,
        text: str,
        sentence_id: str,
        output_dir: Optional[Path] = None
    ) -> Path:
        """Synchronous wrapper for generate_sentence_audio."""
        return asyncio.run(self.generate_sentence_audio(text, sentence_id, output_dir))


async def generate_all_sentence_audio(
    sentences: List,
    output_dir: Optional[Path] = None,
    voice: str = DEFAULT_VOICE,
    batch_size: int = 10
) -> List[Path]:
    """
    Generate audio for multiple sentences.
    
    Args:
        sentences: List of Sentence objects with 'id' and 'text' attributes.
        output_dir: Directory to save audio files.
        voice: Edge TTS voice to use.
        batch_size: Number of concurrent requests (to avoid rate limiting).
        
    Returns:
        List of paths to generated audio files.
    """
    import edge_tts
    
    if output_dir is None:
        output_dir = SENTENCES_AUDIO_DIR
    
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    audio_paths = []
    skipped_count = 0
    total = len(sentences)
    logger.info(f"Generating audio for {total} sentences using {voice}")
    
    engine = TTSEngine(voice=voice)
    
    for i, sentence in enumerate(sentences, 1):
        try:
            # Get text from sentence (handle both dict and object)
            if hasattr(sentence, 'text'):
                text = sentence.text
                sid = sentence.id
            else:
                text = sentence['text']
                sid = sentence['id']
            
            # QUALITY GATE: Validate sentence before TTS generation
            validation = validate_sentence_for_tts(text)
            if not validation.is_valid:
                logger.warning(
                    f"Skipping invalid sentence [{sid}]: {validation.reason} "
                    f"| Text: '{text[:50]}{'...' if len(text) > 50 else ''}'"
                )
                skipped_count += 1
                continue
            
            output_path = output_dir / f"{sid}.mp3"
            
            # Skip if already exists
            if output_path.exists():
                audio_paths.append(output_path)
                continue
            
            await engine.generate_audio(text, output_path)
            audio_paths.append(output_path)
            
            if i % 50 == 0 or i == total:
                logger.info(f"Progress: {i}/{total} sentences ({i*100//total}%)")
                
        except Exception as e:
            logger.error(f"Failed to generate audio for sentence {sid}: {e}")
            # Continue with other sentences
            continue
    
    logger.info(
        f"Audio generation complete: {len(audio_paths)}/{total} successful, "
        f"{skipped_count} skipped (invalid)"
    )
    return audio_paths


def generate_all_sentence_audio_sync(
    sentences: List,
    output_dir: Optional[Path] = None,
    voice: str = DEFAULT_VOICE
) -> List[Path]:
    """Synchronous wrapper for generate_all_sentence_audio."""
    return asyncio.run(generate_all_sentence_audio(sentences, output_dir, voice))


if __name__ == "__main__":
    import sys
    
    # Demo with sample text
    sample_sentences = [
        Sentence("test-001", "こんにちは。"),
        Sentence("test-002", "私は田中です。"),
        Sentence("test-003", "日本語を勉強しています。"),
    ]
    
    if len(sys.argv) > 1:
        # Custom text from command line
        text = " ".join(sys.argv[1:])
        sample_sentences = [Sentence("cli-test", text)]
    
    logging.getLogger().setLevel(logging.DEBUG)
    
    engine = TTSEngine()
    
    async def main():
        for sentence in sample_sentences:
            print(f"\nGenerating audio for: {sentence.text}")
            try:
                path = await engine.generate_sentence_audio(sentence.text, sentence.id)
                print(f"  Saved to: {path}")
            except Exception as e:
                print(f"  Error: {e}")
    
    asyncio.run(main())
