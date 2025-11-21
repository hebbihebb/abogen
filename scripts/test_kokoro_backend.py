#!/usr/bin/env python3
"""
Test script for Kokoro backend integration with Abogen.

This script verifies that the new TTS backend abstraction works correctly
with the existing Kokoro engine, ensuring backward compatibility.

Usage:
    # Test with default voice
    python scripts/test_kokoro_backend.py

    # Test with specific voice
    python scripts/test_kokoro_backend.py --voice am_adam

    # Test on GPU
    python scripts/test_kokoro_backend.py --device cuda
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


def test_kokoro_backend(
    text: str,
    voice: str,
    output_path: str,
    device: str = "cpu",
    speed: float = 1.0,
):
    """
    Test Kokoro backend with sample text.

    Args:
        text: Text to synthesize
        voice: Kokoro voice name
        output_path: Where to save output WAV
        device: "cpu", "cuda", or "mps"
        speed: Speech speed multiplier
    """
    logger.info("=" * 70)
    logger.info("Kokoro Backend Test")
    logger.info("=" * 70)

    # Import Abogen TTS backend
    try:
        from abogen.tts_backends import create_tts_engine
        logger.info("✓ Abogen TTS backends imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import Abogen modules: {e}")
        return False

    # Create Kokoro engine
    logger.info(f"\nInitializing Kokoro backend (device={device})...")
    try:
        engine = create_tts_engine(
            engine_name="kokoro",
            lang_code="a",  # American English
            device=device,
        )
        logger.info("✓ Kokoro backend initialized successfully")
    except ImportError as e:
        logger.error(f"✗ Kokoro not installed: {e}")
        logger.error("\nTo install Kokoro, run: pip install kokoro")
        return False
    except Exception as e:
        logger.error(f"✗ Failed to initialize Kokoro: {e}")
        return False

    # List available voices
    available_voices = engine.available_voices
    logger.info(f"\n✓ Found {len(available_voices)} available voices")
    logger.info(f"  Examples: {', '.join(available_voices[:10])}...")

    # Verify requested voice exists
    if voice not in available_voices:
        logger.error(f"✗ Voice '{voice}' not found in available voices")
        logger.error(f"  Available: {', '.join(available_voices[:20])}...")
        return False

    # Synthesize text
    logger.info(f"\nSynthesizing text with voice '{voice}'...")
    logger.info(f"Text: {text}")

    try:
        all_audio_segments = []
        sample_rate = None

        for i, result in enumerate(engine(text, voice=voice, speed=speed), 1):
            logger.info(
                f"  Chunk {i}: {len(result.audio)} samples @ {result.sample_rate}Hz "
                f"({len(result.audio)/result.sample_rate:.2f}s)"
            )
            logger.info(f"  Graphemes: {result.graphemes}")
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
        description="Test Kokoro backend integration with Abogen"
    )

    parser.add_argument(
        "--text",
        default="Hello world! This is a test of the Kokoro TTS backend with Abogen.",
        help="Text to synthesize"
    )

    parser.add_argument(
        "--voice",
        default="af_heart",
        help="Kokoro voice name (default: af_heart)"
    )

    parser.add_argument(
        "--output",
        default="out/test_kokoro.wav",
        help="Output audio file path"
    )

    parser.add_argument(
        "--device",
        choices=["cpu", "cuda", "mps"],
        default="cpu",
        help="Device to run on (default: cpu)"
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speech speed multiplier (default: 1.0)"
    )

    args = parser.parse_args()

    # Run test
    success = test_kokoro_backend(
        text=args.text,
        voice=args.voice,
        output_path=args.output,
        device=args.device,
        speed=args.speed,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
