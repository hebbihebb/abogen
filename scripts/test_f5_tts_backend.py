#!/usr/bin/env python3
"""
Test script for F5-TTS backend integration with Abogen.

This script tests the F5-TTS backend by synthesizing a short sample text
and saving the output to a WAV file. It's useful for:
- Verifying F5-TTS installation
- Testing voice cloning with custom reference audio
- Debugging synthesis issues

Usage:
    # Test with default settings (will fail if no reference audio provided)
    python scripts/test_f5_tts_backend.py

    # Test with custom reference audio
    python scripts/test_f5_tts_backend.py --ref-audio path/to/voice.wav --ref-text "Transcript"

    # Test on GPU
    python scripts/test_f5_tts_backend.py --device cuda --ref-audio voice.wav

    # Test with longer text
    python scripts/test_f5_tts_backend.py --text "Your custom text here" --ref-audio voice.wav
"""

import argparse
import sys
import logging
from pathlib import Path

# Add parent directory to path to import abogen modules
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_f5_tts_backend(
    text: str,
    reference_audio: str,
    reference_text: str,
    output_path: str,
    device: str = "cpu",
    speed: float = 1.0,
):
    """
    Test F5-TTS backend with sample text.

    Args:
        text: Text to synthesize
        reference_audio: Path to reference audio file
        reference_text: Transcript of reference audio
        output_path: Where to save output WAV
        device: "cpu", "cuda", or "mps"
        speed: Speech speed multiplier
    """
    logger.info("=" * 70)
    logger.info("F5-TTS Backend Test")
    logger.info("=" * 70)

    # Import Abogen TTS backend
    try:
        from abogen.tts_backends import create_tts_engine
        logger.info("✓ Abogen TTS backends imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import Abogen modules: {e}")
        logger.error("Make sure you're running from the Abogen root directory")
        return False

    # Create F5-TTS engine
    logger.info(f"\nInitializing F5-TTS backend (device={device})...")
    try:
        engine = create_tts_engine(
            engine_name="f5_tts",
            lang_code="a",  # American English
            device=device,
            reference_audio=reference_audio,
            reference_text=reference_text,
        )
        logger.info("✓ F5-TTS backend initialized successfully")
    except ImportError as e:
        logger.error(f"✗ F5-TTS not installed: {e}")
        logger.error("\nTo install F5-TTS, run:")
        logger.error("  pip install f5-tts")
        logger.error("Or from source:")
        logger.error("  git clone https://github.com/SWivid/F5-TTS.git")
        logger.error("  cd F5-TTS && pip install -e .")
        return False
    except Exception as e:
        logger.error(f"✗ Failed to initialize F5-TTS: {e}")
        return False

    # Synthesize text
    logger.info(f"\nSynthesizing text ({len(text)} characters)...")
    logger.info(f"Text: {text[:100]}{'...' if len(text) > 100 else ''}")

    try:
        all_audio_segments = []
        sample_rate = None

        for i, result in enumerate(engine(text, voice=reference_audio, speed=speed), 1):
            logger.info(
                f"  Chunk {i}: {len(result.audio)} samples @ {result.sample_rate}Hz "
                f"({len(result.audio)/result.sample_rate:.2f}s)"
            )
            all_audio_segments.append(result.audio)
            sample_rate = result.sample_rate

        logger.info("✓ Synthesis complete")

    except Exception as e:
        logger.error(f"✗ Synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Concatenate and save audio
    if all_audio_segments:
        logger.info(f"\nSaving audio to {output_path}...")
        try:
            import numpy as np
            import soundfile as sf

            # Concatenate all segments
            final_audio = np.concatenate(all_audio_segments)

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Save as WAV
            sf.write(output_path, final_audio, sample_rate)

            duration = len(final_audio) / sample_rate
            logger.info(f"✓ Saved {duration:.2f}s of audio to {output_path}")

        except Exception as e:
            logger.error(f"✗ Failed to save audio: {e}")
            return False
    else:
        logger.error("✗ No audio segments generated")
        return False

    # Success!
    logger.info("\n" + "=" * 70)
    logger.info("✓ Test completed successfully!")
    logger.info("=" * 70)
    logger.info(f"\nYou can now play the audio file: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test F5-TTS backend integration with Abogen",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with custom reference audio
  %(prog)s --ref-audio my_voice.wav --ref-text "This is my voice sample"

  # Test on GPU with custom text
  %(prog)s --device cuda --ref-audio voice.wav --text "Custom synthesis text"

  # Test with faster speed
  %(prog)s --ref-audio voice.wav --speed 1.5

Note: F5-TTS requires a reference audio file (5-10 seconds of clear speech)
      and its transcript for voice cloning.
        """
    )

    parser.add_argument(
        "--text",
        default="Hello world! This is a test of the F5-TTS integration with Abogen. "
                "The quick brown fox jumps over the lazy dog. "
                "F5-TTS provides high-quality voice cloning from reference audio.",
        help="Text to synthesize (default: sample text)"
    )

    parser.add_argument(
        "--ref-audio",
        required=True,
        help="Path to reference audio file (.wav, 5-10 seconds)"
    )

    parser.add_argument(
        "--ref-text",
        default="",
        help="Transcript of reference audio (optional but recommended)"
    )

    parser.add_argument(
        "--output",
        default="out/test_f5_tts.wav",
        help="Output audio file path (default: out/test_f5_tts.wav)"
    )

    parser.add_argument(
        "--device",
        choices=["cpu", "cuda", "mps"],
        default="cpu",
        help="Device to run on (default: cpu). Note: F5-TTS is VERY slow on CPU!"
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speech speed multiplier (default: 1.0)"
    )

    args = parser.parse_args()

    # Validate reference audio exists
    if not Path(args.ref_audio).exists():
        logger.error(f"✗ Reference audio file not found: {args.ref_audio}")
        logger.error("\nF5-TTS requires a reference audio file for voice cloning.")
        logger.error("Provide a 5-10 second WAV file with clear speech using --ref-audio")
        return 1

    # Warn about CPU usage
    if args.device == "cpu":
        logger.warning("⚠ Running on CPU - F5-TTS will be VERY slow!")
        logger.warning("  Consider using --device cuda if you have a GPU")

    # Run test
    success = test_f5_tts_backend(
        text=args.text,
        reference_audio=args.ref_audio,
        reference_text=args.ref_text,
        output_path=args.output,
        device=args.device,
        speed=args.speed,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
