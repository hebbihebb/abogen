"""
Kokoro-82M TTS backend implementation for Abogen.

This backend wraps the Kokoro pipeline to conform to the TTSBackend protocol,
maintaining backward compatibility while enabling multi-engine support.
"""

import logging
from typing import Iterator, Optional
from .base import TTSResult, TTSBackend

logger = logging.getLogger(__name__)


class KokoroBackend:
    """
    Kokoro-82M TTS backend wrapper.

    This backend provides access to the Kokoro-82M model with 58 built-in voices
    and multi-language support. It wraps the KPipeline class to conform to the
    TTSBackend protocol.

    Features:
        - 58 pre-trained voices across multiple languages
        - Voice formula mixing (e.g., "af_heart*0.5 + am_adam*0.5")
        - Fast inference (CPU-friendly)
        - Streaming synthesis for long texts

    Example:
        >>> backend = KokoroBackend(lang_code="a", device="cpu")
        >>> for result in backend("Hello world", voice="af_heart", speed=1.0):
        ...     process_audio(result.audio, result.sample_rate)
    """

    def __init__(
        self,
        lang_code: str,
        device: str = "cpu",
        repo_id: str = "hexgrad/Kokoro-82M",
        kpipeline_class=None,  # For backward compatibility
        **kwargs
    ):
        """
        Initialize Kokoro backend.

        Args:
            lang_code: Language code (e.g., "a" for American English,
                      "b" for British English, "e" for Spanish)
            device: Device to run on ("cpu", "cuda", "mps")
            repo_id: HuggingFace repository ID for the Kokoro model
            kpipeline_class: Optional pre-imported KPipeline class
                           (for backward compatibility with existing code)
            **kwargs: Additional arguments (ignored)
        """
        self.lang_code = lang_code
        self.device = device
        self.repo_id = repo_id

        logger.info(f"Initializing Kokoro backend (lang={lang_code}, device={device})...")

        # Load KPipeline class
        if kpipeline_class is not None:
            KPipeline = kpipeline_class
        else:
            try:
                from kokoro import KPipeline
            except ImportError:
                raise ImportError(
                    "Kokoro not installed. Install with: pip install kokoro"
                )

        # Initialize the pipeline
        self.pipeline = KPipeline(
            lang_code=lang_code,
            repo_id=repo_id,
            device=device
        )

        logger.info("Kokoro pipeline loaded successfully")

    @staticmethod
    def _check_dependencies():
        """Check if Kokoro is installed."""
        import kokoro

    def __call__(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        split_pattern: Optional[str] = None,
    ) -> Iterator[TTSResult]:
        """
        Synthesize text using Kokoro pipeline.

        Args:
            text: Input text to synthesize
            voice: Voice name (e.g., "af_heart", "am_adam") or voice formula
                  (e.g., "af_heart*0.5 + am_adam*0.5")
            speed: Speech speed multiplier (1.0 = normal)
            split_pattern: Regex pattern for splitting text (optional)

        Yields:
            TTSResult objects with audio segments
        """
        logger.debug(f"Synthesizing with Kokoro: voice={voice}, speed={speed}")

        # Call the Kokoro pipeline (it's already a generator)
        for result in self.pipeline(
            text,
            voice=voice,
            speed=speed,
            split_pattern=split_pattern,
        ):
            # Kokoro results already have the right format:
            # - result.audio (numpy array)
            # - result.graphemes (list of strings)
            # - result.tokens (list)

            # Get sample rate from pipeline
            sample_rate = getattr(self.pipeline, 'sample_rate', 24000)

            yield TTSResult(
                audio=result.audio,
                sample_rate=sample_rate,
                graphemes=result.graphemes if hasattr(result, 'graphemes') else [],
                tokens=result.tokens if hasattr(result, 'tokens') else [],
            )

    def load_single_voice(self, voice_name: str):
        """
        Load a single voice embedding for mixing.

        This method is used by voice formula parsing to load individual
        voice tensors that can be blended together.

        Args:
            voice_name: Name of the voice to load (e.g., "af_heart")

        Returns:
            Voice embedding tensor
        """
        return self.pipeline.load_single_voice(voice_name)

    @property
    def supports_voice_mixing(self) -> bool:
        """Kokoro supports voice formula mixing."""
        return True

    @property
    def available_voices(self) -> list[str]:
        """
        Return list of available Kokoro voices.

        Returns:
            List of 58 built-in Kokoro voice names
        """
        # Import from constants to avoid circular dependency
        try:
            from abogen.constants import VOICES_INTERNAL
            return VOICES_INTERNAL
        except ImportError:
            # Fallback if constants not available
            return []
