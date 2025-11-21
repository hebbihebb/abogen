#!/usr/bin/env python3
"""Test F5-TTS with custom reference audio."""
from pathlib import Path
import numpy as np
import soundfile as sf
from abogen.tts_backends import create_tts_engine

# Your custom reference audio
ref_audio = "out/abogen_3s2bay39.wav"
ref_text = ""  # F5-TTS will auto-transcribe if empty

# Text to generate with the cloned voice
test_text = (
    "Hello! This is a test of voice cloning using F5-TTS. "
    "I am speaking with a voice that was cloned from the reference audio. "
    "The technology analyzes the reference to replicate vocal characteristics."
)

print("=" * 70)
print("F5-TTS Voice Cloning Test with Custom Reference")
print("=" * 70)
print(f"\nReference audio: {ref_audio}")
print(f"Text to generate: {test_text}\n")

# Create F5-TTS engine
print("Initializing F5-TTS (loading model, ~30 seconds)...")
engine = create_tts_engine(
    "f5_tts",
    lang_code="en-us",
    device="cpu",  # Change to "cuda" if you want to use GPU
    reference_audio=ref_audio,
    reference_text=ref_text
)

print("\nSynthesizing audio with cloned voice...")

# Generate audio
audio_chunks = []
sample_rate = None

for result in engine(test_text, voice=ref_audio):
    audio_chunks.append(result.audio)
    sample_rate = result.sample_rate

# Save
audio = np.concatenate(audio_chunks)
output_file = "out/test_custom_clone.wav"
sf.write(output_file, audio, sample_rate)

duration = len(audio) / sample_rate
print(f"\n[OK] Success! Saved {duration:.2f}s to {output_file}")
print("\n" + "=" * 70)
print("Done! You can now play the cloned voice audio.")
print("=" * 70)
