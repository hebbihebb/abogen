#!/usr/bin/env python3
"""Create a custom voice mix by generating and blending multiple voice outputs."""
import sys
from pathlib import Path
import numpy as np
import soundfile as sf

def create_mixed_voice_reference():
    """Create a custom voice mix by generating each voice and blending the audio."""
    print("=" * 70)
    print("Step 1: Creating Mixed Voice Reference with Kokoro")
    print("=" * 70)

    from abogen.tts_backends import create_tts_engine

    # Create Kokoro engine
    engine = create_tts_engine("kokoro", lang_code="en-us", device="cpu")

    # Voice mix weights
    voice_weights = [
        ("af_bella", 0.6),
        ("af_nicole", 0.5),
        ("af_sarah", 0.4),
        ("am_adam", 0.3),
    ]

    print("\nVoice Mix Formula:")
    for voice, weight in voice_weights:
        print(f"  {voice:12} x {weight}")

    # Reference text for voice cloning
    ref_text = (
        "This is a custom blended voice created by mixing multiple Kokoro voices. "
        "It combines the characteristics of Bella, Nicole, Sarah, and Adam to create "
        "a unique sound that will be cloned by F5-TTS."
    )

    print(f"\nGenerating audio for each voice...")
    print(f"Text: {ref_text[:80]}...")

    # Generate audio for each voice
    voice_audio_list = []
    sample_rate = None

    for voice_name, weight in voice_weights:
        print(f"  Generating {voice_name}...")
        audio_chunks = []

        for result in engine(ref_text, voice=voice_name):
            audio_chunks.append(result.audio)
            sample_rate = result.sample_rate

        voice_audio = np.concatenate(audio_chunks)
        voice_audio_list.append((voice_audio, weight))

    # Mix the audio outputs with weights
    print("\nBlending audio outputs...")
    max_length = max(len(audio) for audio, _ in voice_audio_list)
    mixed_audio = np.zeros(max_length, dtype=np.float32)
    total_weight = sum(w for _, w in voice_weights)

    for audio, weight in voice_audio_list:
        # Pad audio if necessary
        if len(audio) < max_length:
            audio = np.pad(audio, (0, max_length - len(audio)))

        # Add weighted audio
        mixed_audio += (audio * weight)

    # Normalize by total weight
    mixed_audio = mixed_audio / total_weight

    # Ensure audio is in valid range [-1, 1]
    max_val = np.abs(mixed_audio).max()
    if max_val > 1.0:
        mixed_audio = mixed_audio / max_val

    # Save reference
    ref_output = "out/mixed_voice_reference.wav"
    Path("out").mkdir(exist_ok=True)
    sf.write(ref_output, mixed_audio, sample_rate)

    duration = len(mixed_audio) / sample_rate
    print(f"[OK] Mixed voice reference created: {ref_output} ({duration:.2f}s)")

    return ref_output, ref_text

def test_f5tts_clone_mixed(ref_audio, ref_text):
    """Clone the mixed voice with F5-TTS."""
    print("\n" + "=" * 70)
    print("Step 2: Cloning Mixed Voice with F5-TTS")
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
    test_text = (
        "Hello! I am a voice clone created from a custom Kokoro voice mix. "
        "My voice combines elements from four different speakers, creating a unique timbre. "
        "This demonstrates the power of combining Kokoro's voice mixing with F5-TTS voice cloning."
    )
    output_file = "out/test_f5tts_mixed.wav"

    print(f"\nSynthesizing with cloned mixed voice...")
    print(f"Text: {test_text[:80]}...")
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
    print("\nKokoro Voice Mix + F5-TTS Cloning Test\n")

    try:
        # Step 1: Create mixed voice reference
        ref_audio, ref_text = create_mixed_voice_reference()

        # Step 2: Clone the mixed voice with F5-TTS
        print("\n")
        choice = input("Clone this mixed voice with F5-TTS? (y/n, takes ~2-3 minutes): ").lower()
        if choice == 'y':
            test_f5tts_clone_mixed(ref_audio, ref_text)

        print("\n" + "=" * 70)
        print("Test Complete!")
        print("=" * 70)
        print("\nGenerated files:")
        print("  1. out/mixed_voice_reference.wav (Kokoro mixed voice)")
        if choice == 'y':
            print("  2. out/test_f5tts_mixed.wav (F5-TTS cloned mixed voice)")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
