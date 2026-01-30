"""
Text-to-speech generation module for the Japanese PDF Audio Reader.

This module handles:
- Generating Japanese audio from text using Coqui TTS
- Saving audio files as WAV (later converted to Opus)
- One file per sentence

The TTS model is loaded once and reused for all sentences.
Audio is generated deterministically - same input produces same output.

Usage:
    from processor.generate_tts import generate_sentence_audio, TTSEngine
    
    engine = TTSEngine()
    audio_path = engine.generate_sentence_audio(sentence, sentence_id)
"""

import logging
from pathlib import Path
from typing import Optional, List

import soundfile as sf

from .config import SENTENCES_AUDIO_DIR, AUDIO_FORMAT, AUDIO_SAMPLE_RATE, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Text-to-Speech engine using Coqui TTS.
    
    Provides a consistent interface for generating Japanese speech
    from text. The model is loaded once and reused.
    """
    
    def __init__(self, model_name: Optional[str] = None, device: str = "cpu"):
        """
        Initialize the TTS engine.
        
        Args:
            model_name: The Coqui TTS model to use. If None, uses default Japanese model.
            device: Device to run inference on ("cpu" or "cuda").
        """
        self.model_name = model_name or "tts_models/ja/kokoro/tacotron2-DDC"
        self.device = device
        self._tts = None
        
        logger.info(f"TTS Engine initialized (model: {self.model_name}, device: {device})")
    
    def _load_model(self):
        """Lazy-load the TTS model on first use."""
        if self._tts is None:
            try:
                from TTS.api import TTS
                logger.info(f"Loading TTS model: {self.model_name}")
                self._tts = TTS(model_name=self.model_name, progress_bar=False)
                if self.device == "cuda":
                    self._tts = self._tts.to(self.device)
                logger.info("TTS model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load TTS model: {e}")
                raise
    
    def generate_audio(self, text: str, output_path: Path) -> Path:
        """
        Generate audio for the given text.
        
        Args:
            text: Japanese text to synthesize.
            output_path: Path where the audio file will be saved.
            
        Returns:
            The path to the generated audio file.
        """
        self._load_model()
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate audio
        logger.debug(f"Generating audio for: {text[:50]}...")
        
        try:
            # Coqui TTS generates WAV files
            self._tts.tts_to_file(text=text, file_path=str(output_path))
            logger.debug(f"Audio saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise
    
    def generate_sentence_audio(
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
        
        # Use WAV for initial generation, will be converted to OGG later if needed
        output_path = output_dir / f"{sentence_id}.wav"
        
        return self.generate_audio(text, output_path)


def generate_all_sentence_audio(
    sentences: List,
    output_dir: Optional[Path] = None,
    device: str = "cpu"
) -> List[Path]:
    """
    Generate audio for multiple sentences.
    
    Args:
        sentences: List of Sentence objects with 'id' and 'text' attributes.
        output_dir: Directory to save audio files.
        device: Device for TTS inference.
        
    Returns:
        List of paths to generated audio files.
    """
    engine = TTSEngine(device=device)
    audio_paths = []
    
    total = len(sentences)
    logger.info(f"Generating audio for {total} sentences")
    
    for i, sentence in enumerate(sentences, 1):
        try:
            path = engine.generate_sentence_audio(
                text=sentence.text,
                sentence_id=sentence.id,
                output_dir=output_dir
            )
            audio_paths.append(path)
            
            if i % 10 == 0 or i == total:
                logger.info(f"Progress: {i}/{total} sentences")
                
        except Exception as e:
            logger.error(f"Failed to generate audio for sentence {sentence.id}: {e}")
            # Continue with other sentences
            continue
    
    logger.info(f"Audio generation complete: {len(audio_paths)}/{total} successful")
    return audio_paths


if __name__ == "__main__":
    import sys
    
    # Demo with sample text
    sample_sentences = [
        ("test-001", "こんにちは。"),
        ("test-002", "私は田中です。"),
        ("test-003", "日本語を勉強しています。"),
    ]
    
    if len(sys.argv) > 1:
        # Custom text from command line
        text = " ".join(sys.argv[1:])
        sample_sentences = [("cli-test", text)]
    
    logger.setLevel(logging.DEBUG)
    
    engine = TTSEngine()
    
    for sentence_id, text in sample_sentences:
        print(f"\nGenerating audio for: {text}")
        try:
            path = engine.generate_sentence_audio(text, sentence_id)
            print(f"  Saved to: {path}")
        except Exception as e:
            print(f"  Error: {e}")
