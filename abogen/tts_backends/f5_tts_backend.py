"""
F5-TTS backend implementation for Abogen.

This backend provides high-quality TTS synthesis using the F5-TTS diffusion model
with zero-shot voice cloning capabilities from reference audio.
"""

import re
import logging
import numpy as np
from pathlib import Path
from typing import Iterator, Optional
from .base import TTSResult, TTSBackend

logger = logging.getLogger(__name__)


class F5TTSBackend:
    """
    F5-TTS backend for Abogen.

    F5-TTS is a diffusion-based TTS model that supports zero-shot voice cloning
    from reference audio. Unlike Kokoro, it doesn't have built-in voices - instead,
    you provide a short reference audio clip (5-10 seconds) and the model clones
    that voice.

    Features:
        - High-quality, natural-sounding synthesis
        - Zero-shot voice cloning from reference audio
        - Multi-lingual support
        - Controllable speed and prosody

    Limitations:
        - Requires GPU for reasonable speed (very slow on CPU)
        - No built-in voice library (user must provide reference audio)
        - Longer inference time than Kokoro
        - Requires reference audio + transcript for each voice

    Example:
        >>> backend = F5TTSBackend(
        ...     lang_code="a",
        ...     device="cuda",
        ...     reference_audio="my_voice.wav",
        ...     reference_text="This is a sample of my voice."
        ... )
        >>> for result in backend("Hello world", voice="my_voice.wav", speed=1.0):
        ...     process_audio(result.audio, result.sample_rate)
    """

    def __init__(
        self,
        lang_code: str,
        device: str = "cpu",
        model_name: str = "F5-TTS",
        ckpt_file: str = "",
        vocab_file: str = "",
        reference_audio: Optional[str] = None,
        reference_text: Optional[str] = None,
        vocoder_name: str = "vocos",
        target_rms: float = 0.1,
        cross_fade_duration: float = 0.15,
        nfe_step: int = 32,
        cfg_strength: float = 2.0,
        sway_sampling_coef: float = -1.0,
        speed: float = 1.0,
        fix_duration: Optional[float] = None,
        **kwargs
    ):
        """
        Initialize F5-TTS backend.

        Args:
            lang_code: Language code (currently mainly supports English)
            device: Device to run on ("cpu", "cuda", "mps")
            model_name: Model name ("F5-TTS" or "E2-TTS")
            ckpt_file: Path to model checkpoint (empty string for auto-download)
            vocab_file: Path to vocab file (empty string for auto-download)
            reference_audio: Default reference audio file path
            reference_text: Transcript of default reference audio
            vocoder_name: Vocoder to use ("vocos" recommended)
            target_rms: Target RMS for audio normalization
            cross_fade_duration: Cross-fade duration between segments (seconds)
            nfe_step: Number of function evaluations (32 is good balance)
            cfg_strength: Classifier-free guidance strength
            sway_sampling_coef: Sway sampling coefficient (-1 = disabled)
            speed: Global speed multiplier
            fix_duration: Fix duration for generated audio (None = auto)
            **kwargs: Additional arguments (ignored)
        """
        self.lang_code = lang_code
        self.device = device
        self.model_name = model_name
        self.reference_audio = reference_audio
        self.reference_text = reference_text
        self.vocoder_name = vocoder_name

        # Synthesis parameters
        self.target_rms = target_rms
        self.cross_fade_duration = cross_fade_duration
        self.nfe_step = nfe_step
        self.cfg_strength = cfg_strength
        self.sway_sampling_coef = sway_sampling_coef
        self.default_speed = speed
        self.fix_duration = fix_duration

        logger.info(f"Initializing F5-TTS backend on {device}...")

        # Import F5-TTS API
        try:
            from f5_tts.api import F5TTS
        except ImportError as e:
            raise ImportError(
                "F5-TTS not installed. Install with:\n"
                "  pip install f5-tts\n"
                "Or from source:\n"
                "  git clone https://github.com/SWivid/F5-TTS.git\n"
                "  cd F5-TTS && pip install -e .\n"
                f"Error: {e}"
            )

        # Map model names to F5-TTS API model names
        model_name_mapping = {
            "F5-TTS": "F5TTS_v1_Base",
            "E2-TTS": "E2TTS_Base",
        }
        api_model_name = model_name_mapping.get(model_name, model_name)

        # Load F5-TTS model using high-level API
        try:
            logger.info("Loading F5-TTS model (this may take a few moments)...")

            # Suppress download messages during model loading
            import sys
            import os
            from contextlib import redirect_stdout, redirect_stderr

            with open(os.devnull, 'w') as devnull:
                with redirect_stdout(devnull), redirect_stderr(devnull):
                    self.f5tts = F5TTS(
                        model=api_model_name,
                        ckpt_file=ckpt_file,
                        vocab_file=vocab_file,
                        ode_method="euler",
                        use_ema=True,
                        device=device,
                    )

            logger.info("F5-TTS model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load F5-TTS model: {e}")
            raise RuntimeError(
                f"Failed to initialize F5-TTS. This could be due to:\n"
                f"  - Missing model files (will auto-download on first run)\n"
                f"  - Insufficient GPU memory (try device='cpu' or reduce batch size)\n"
                f"  - Missing dependencies (ensure torch and torchaudio installed)\n"
                f"Error: {e}"
            )

        # Store default reference audio path
        self.default_ref_audio_path = reference_audio
        self.default_ref_text = reference_text or ""

    @staticmethod
    def _check_dependencies():
        """Check if F5-TTS is installed."""
        import f5_tts

    def __call__(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        split_pattern: Optional[str] = None,
    ) -> Iterator[TTSResult]:
        """
        Synthesize text using F5-TTS.

        For F5-TTS, the 'voice' parameter should be:
        - Path to a reference audio file (.wav), OR
        - Empty string to use the default reference audio from initialization

        Args:
            text: Input text to synthesize (can be long, will be chunked)
            voice: Path to reference audio file, or "" for default
            speed: Speech speed multiplier (1.0 = normal)
            split_pattern: Regex pattern for splitting text (optional)

        Yields:
            TTSResult objects with audio segments

        Raises:
            ValueError: If no reference audio provided
            RuntimeError: If synthesis fails
        """
        # Determine which reference audio to use
        if voice and Path(voice).exists():
            logger.info(f"Using custom reference audio: {voice}")
            ref_audio_path = voice
            ref_text = ""  # Transcript is optional with new API
        elif self.default_ref_audio_path and Path(self.default_ref_audio_path).exists():
            logger.debug("Using default reference audio")
            ref_audio_path = self.default_ref_audio_path
            ref_text = self.default_ref_text
        else:
            raise ValueError(
                "F5-TTS requires reference audio. Please provide:\n"
                "  1. 'voice' parameter as path to reference audio file, OR\n"
                "  2. 'reference_audio' in backend initialization\n"
                "\n"
                "Reference audio should be:\n"
                "  - WAV format, 5-10 seconds long\n"
                "  - Clear voice sample without background noise\n"
                "  - Representative of desired voice characteristics"
            )

        # Split text into manageable chunks
        chunks = self._split_text(text, split_pattern)

        logger.info(
            f"Synthesizing {len(chunks)} text chunks with F5-TTS "
            f"(speed={speed:.2f})..."
        )

        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks, 1):
            if not chunk.strip():
                continue

            logger.debug(f"Processing chunk {i}/{total_chunks}: {chunk[:50]}...")

            try:
                # Suppress F5-TTS stdout/stderr during inference
                import sys
                import os
                from contextlib import redirect_stdout, redirect_stderr

                # Redirect stdout and stderr to devnull to suppress F5-TTS internal messages
                with open(os.devnull, 'w') as devnull:
                    with redirect_stdout(devnull), redirect_stderr(devnull):
                        # Run F5-TTS inference using high-level API
                        audio, sample_rate, spectrogram = self.f5tts.infer(
                            ref_file=ref_audio_path,
                            ref_text=ref_text,
                            gen_text=chunk,
                            show_info=lambda x: None,  # Suppress F5-TTS logging
                            progress=None,  # Disable progress bar
                            target_rms=self.target_rms,
                            cross_fade_duration=self.cross_fade_duration,
                            nfe_step=self.nfe_step,
                            cfg_strength=self.cfg_strength,
                            sway_sampling_coef=self.sway_sampling_coef,
                            speed=speed,
                            fix_duration=self.fix_duration,
                            remove_silence=False,
                            seed=None,  # Random seed for each chunk
                        )

                # Convert to numpy array if needed
                if not isinstance(audio, np.ndarray):
                    audio = np.array(audio)

                # Ensure audio is 1D (mono)
                if audio.ndim > 1:
                    audio = audio.flatten()

                # Use chunk characters as graphemes for progress tracking
                # This allows the GUI to track progress based on text length
                graphemes = list(chunk)

                yield TTSResult(
                    audio=audio,
                    sample_rate=sample_rate,
                    graphemes=graphemes,
                    tokens=[],
                )

                logger.debug(
                    f"  → Generated {len(audio)} samples @ {sample_rate}Hz "
                    f"({len(audio)/sample_rate:.2f}s)"
                )

            except Exception as e:
                logger.error(f"Failed to synthesize chunk {i}: {e}")
                raise RuntimeError(
                    f"F5-TTS synthesis failed on chunk {i}/{total_chunks}:\n"
                    f"  Text: {chunk[:100]}...\n"
                    f"  Error: {e}"
                )

        logger.info("F5-TTS synthesis complete")

    def _split_text(
        self,
        text: str,
        split_pattern: Optional[str]
    ) -> list[str]:
        """
        Split text into chunks for processing.

        F5-TTS works best with chunks of ~100-200 words. This method splits
        long texts intelligently to maintain sentence boundaries.

        Args:
            text: Input text to split
            split_pattern: Optional regex pattern for custom splitting

        Returns:
            List of text chunks
        """
        if split_pattern:
            # Use custom split pattern if provided
            chunks = re.split(split_pattern, text)
            return [c.strip() for c in chunks if c.strip()]

        # Default: split on sentence boundaries with max ~200 words per chunk
        # This helps maintain natural prosody and avoids memory issues

        # First, split into sentences
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = []
        current_word_count = 0
        max_words_per_chunk = 200

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Count words in this sentence
            words = sentence.split()
            word_count = len(words)

            # If adding this sentence exceeds limit and we have content, start new chunk
            if current_word_count + word_count > max_words_per_chunk and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_word_count = word_count
            else:
                current_chunk.append(sentence)
                current_word_count += word_count

        # Add remaining content
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        logger.debug(f"Split text into {len(chunks)} chunks (max {max_words_per_chunk} words each)")
        return chunks

    @property
    def supports_voice_mixing(self) -> bool:
        """F5-TTS doesn't support Kokoro-style voice formula mixing."""
        return False

    @property
    def available_voices(self) -> list[str]:
        """
        F5-TTS uses reference audio for voices, so there are no "built-in" voices.

        Users must provide their own reference audio files. In the future, we
        could bundle some high-quality reference voices with Abogen.

        Returns:
            Empty list (no built-in voices)
        """
        return []
