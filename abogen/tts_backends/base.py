"""
Base protocol and types for TTS backend implementations in Abogen.

This module defines the interface that all TTS engines must implement
to be compatible with Abogen's synthesis pipeline.
"""

from typing import Protocol, Iterator, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class TTSResult:
    """
    Normalized result format for TTS synthesis across all engines.

    Attributes:
        audio: Audio samples as numpy array (mono or stereo)
        sample_rate: Sample rate in Hz (e.g., 24000, 22050)
        graphemes: Optional list of graphemes/phonemes for subtitle generation
        tokens: Optional list of token representations
    """
    audio: np.ndarray
    sample_rate: int
    graphemes: list[str] = None
    tokens: list = None

    def __post_init__(self):
        """Initialize optional fields to empty lists if None."""
        if self.graphemes is None:
            self.graphemes = []
        if self.tokens is None:
            self.tokens = []


class TTSBackend(Protocol):
    """
    Protocol defining the interface for TTS engine implementations.

    All TTS backends must implement this protocol to be compatible with
    Abogen's conversion pipeline. This enables swapping between different
    TTS engines (Kokoro, F5-TTS, future engines) without changing core logic.

    Example:
        >>> engine = create_tts_engine("f5_tts", lang_code="a", device="cuda")
        >>> for result in engine(text="Hello world", voice="default", speed=1.0):
        ...     process_audio(result.audio, result.sample_rate)
    """

    def __init__(
        self,
        lang_code: str,
        device: str = "cpu",
        **engine_specific_kwargs
    ):
        """
        Initialize the TTS engine.

        Args:
            lang_code: Language code (e.g., "a" for American English,
                      "b" for British, "e" for Spanish). See constants.py
                      for full language mapping.
            device: Device to run inference on ("cpu", "cuda", "mps")
            **engine_specific_kwargs: Engine-specific configuration options
        """
        ...

    def __call__(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        split_pattern: Optional[str] = None,
    ) -> Iterator[TTSResult]:
        """
        Synthesize text to audio, yielding segments incrementally.

        This is the main synthesis method. It should yield audio segments
        as they are generated to enable memory-efficient streaming for
        long texts (e.g., full book chapters).

        Args:
            text: Input text to synthesize (can be multiple paragraphs)
            voice: Voice identifier (format is engine-specific):
                  - Kokoro: voice name like "af_heart", "am_adam"
                  - F5-TTS: path to reference audio file
            speed: Speech speed multiplier (1.0 = normal, 0.5 = half speed,
                  2.0 = double speed)
            split_pattern: Optional regex pattern for splitting text into
                         chunks before synthesis (e.g., r"\n+" for paragraphs)

        Yields:
            TTSResult objects containing audio segments and metadata

        Raises:
            ValueError: If voice not found or parameters invalid
            RuntimeError: If synthesis fails
        """
        ...

    def load_single_voice(self, voice_name: str) -> any:
        """
        Load a voice embedding/model for voice mixing (optional feature).

        This method is only required for engines that support voice formula
        blending (like Kokoro's "voice1*0.5 + voice2*0.3" feature).

        Args:
            voice_name: Name of the voice to load

        Returns:
            Voice embedding tensor or model object (engine-specific format)

        Raises:
            NotImplementedError: If engine doesn't support voice mixing
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} doesn't support voice mixing"
        )

    @property
    def supports_voice_mixing(self) -> bool:
        """
        Whether this engine supports voice formula blending.

        Returns:
            True if engine supports Kokoro-style voice formulas,
            False otherwise
        """
        return False

    @property
    def available_voices(self) -> list[str]:
        """
        List of voice identifiers available for this engine.

        Returns:
            List of voice names/identifiers that can be passed to __call__
            Empty list if voices are user-provided (e.g., F5-TTS reference audio)
        """
        return []
