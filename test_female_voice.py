#!/usr/bin/env python3
"""Test F5-TTS with a female voice by creating reference audio from Kokoro."""
import sys
from pathlib import Path
import numpy as np
import soundfile as sf

def create_female_reference():
    """Create a female voice reference using Kokoro."""
    print("=" * 70)
    print("Step 1: Creating Female Reference Audio with Kokoro")
    print("=" * 70)

    from abogen.tts_backends import create_tts_engine

    # Create Kokoro engine
    engine = create_tts_engine("kokoro", lang_code="en-us", device="cpu")

    # Reference text for voice cloning
    ref_text = "The quick brown fox jumps over the lazy dog. This voice will be cloned by F5-TTS."
    ref_output = "out/female_reference.wav"

    print(f"\nGenerating reference with Kokoro voice 'af_bella' (female)")
    print(f"Text: {ref_text}")

    # Synthesize
    audio_chunks = []
    sample_rate = None

    for result in engine(ref_text, voice="af_bella"):
        audio_chunks.append(result.audio)
        sample_rate = result.sample_rate

    # Save reference
    audio = np.concatenate(audio_chunks)
    Path("out").mkdir(exist_ok=True)
    sf.write(ref_output, audio, sample_rate)

    duration = len(audio) / sample_rate
    print(f"[OK] Reference audio created: {ref_output} ({duration:.2f}s)")

    return ref_output, ref_text

def test_f5tts_female(ref_audio, ref_text):
    """Test F5-TTS with the female reference."""
    print("\n" + "=" * 70)
    print("Step 2: Voice Cloning with F5-TTS")
    print("=" * 70)

    from abogen.tts_backends import create_tts_engine

    # Create F5-TTS engine
    print("\nInitializing F5-TTS (loading model, ~30 seconds)...")
    engine = create_tts_engine(
        "f5_tts",
        lang_code="en-us",
        device="cpu",
        reference_audio=ref_audio,
        reference_text=ref_text
    )

    # Test text
    test_text = "Hello! This is F5-TTS cloning a female voice. The technology uses the reference audio to replicate the voice characteristics."
    output_file = "out/test_f5tts_female.wav"

    print(f"\nSynthesizing with cloned voice...")
    print(f"Text: {test_text}")
    print(f"Output: {output_file}")

    # Synthesize
    audio_chunks = []
    sample_rate = None

    for result in engine(test_text, voice=ref_audio):
        audio_chunks.append(result.audio)
        sample_rate = result.sample_rate

    # Save
    audio = np.concatenate(audio_chunks)
    sf.write(output_file, audio, sample_rate)

    duration = len(audio) / sample_rate
    print(f"\n[OK] Success! Saved {duration:.2f}s to {output_file}")

if __name__ == "__main__":
    print("\nF5-TTS Female Voice Cloning Test\n")

    try:
        # Step 1: Create female reference audio
        ref_audio, ref_text = create_female_reference()

        # Step 2: Clone the voice with F5-TTS
        test_f5tts_female(ref_audio, ref_text)

        print("\n" + "=" * 70)
        print("Test Complete!")
        print("=" * 70)
        print("\nGenerated files:")
        print("  1. out/female_reference.wav (Kokoro female voice)")
        print("  2. out/test_f5tts_female.wav (F5-TTS cloned voice)")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
